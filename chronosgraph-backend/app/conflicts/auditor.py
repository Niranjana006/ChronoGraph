import logging
import json
from datetime import datetime
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from httpx import HTTPError

from app.graph.neo4j_client import neo4j_client
from app.llm.client import generate_completion
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a precise conflict-detection AI. You are given two overlapping facts extracted from a knowledge graph. They share either the same subject or the same object, and have the same relationship. They overlap in time.
Your job is to determine if these two facts represent a genuine contradiction (e.g. two different people being CEO of the same company at the same time, or one person being born in two different cities) or if they can logically co-exist (e.g. two people both being Board Members at the same time).

Respond with a JSON object containing:
- "is_conflict": boolean (true if it's a genuine contradiction, false if they can co-exist)
- "confidence": float between 0.0 and 1.0
- "explanation": a short string explaining your reasoning

Only output valid JSON.
"""

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(HTTPError)
)
async def validate_conflict_llm(sub1: str, obj1: str, ev1: str, sub2: str, obj2: str, ev2: str, relation: str) -> dict:
    prompt = f"""
Relation: {relation}

Fact 1:
Subject: {sub1}
Object: {obj1}
Evidence: "{ev1}"

Fact 2:
Subject: {sub2}
Object: {obj2}
Evidence: "{ev2}"

Do these two facts contradict each other given they overlap in time?
"""
    response_json = await generate_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt,
        response_format={"type": "json_object"}
    )
    return json.loads(response_json)

async def audit_workspace(workspace_id: int):
    """
    Scans a workspace for structural overlaps and uses the LLM to validate conflicts.
    """
    logger.info(f"Starting Consistency Swarm audit for workspace {workspace_id}")
    
    # Cypher query to find overlapping facts
    overlap_query = """
    MATCH (f1:Fact {workspace_id: $workspace_id})-[:SUBJECT]->(s1:Entity),
          (f1)-[:OBJECT]->(o1:Entity),
          (f2:Fact {workspace_id: $workspace_id})-[:SUBJECT]->(s2:Entity),
          (f2)-[:OBJECT]->(o2:Entity)
    WHERE f1.relation = f2.relation
      AND f1.id < f2.id
      AND (
          (s1.id = s2.id AND o1.id <> o2.id) OR
          (o1.id = o2.id AND s1.id <> s2.id)
      )
      AND f1.temporal_confidence <> 'low'
      AND f2.temporal_confidence <> 'low'
      // Temporal overlap check (null valid_to means valid until present)
      AND coalesce(f1.parsed_valid_from, date('1000-01-01')) <= coalesce(f2.parsed_valid_to, date())
      AND coalesce(f2.parsed_valid_from, date('1000-01-01')) <= coalesce(f1.parsed_valid_to, date())
      // Ensure we haven't already audited this pair
      AND NOT (f1)-[:CONTRADICTS]-(f2)
      AND NOT (f1)-[:NON_CONFLICT]-(f2)
    RETURN f1.id AS f1_id, f1.evidence AS f1_evidence, o1.id AS o1_name, s1.id AS s1_name,
           f2.id AS f2_id, f2.evidence AS f2_evidence, o2.id AS o2_name, s2.id AS s2_name,
           f1.relation AS relation
    """
    
    async with neo4j_client.driver.session() as session:
        result = await session.run(overlap_query, workspace_id=workspace_id)
        overlaps = [record.data() async for record in result]
        
    if not overlaps:
        logger.info("No new overlaps found.")
        return 0
        
    logger.info(f"Found {len(overlaps)} overlapping fact pairs. Starting LLM validation...")
    
    conflicts_found = 0
    
    for overlap in overlaps:
        f1_id = overlap['f1_id']
        f2_id = overlap['f2_id']
        
        try:
            llm_result = await validate_conflict_llm(
                sub1=overlap['s1_name'],
                obj1=overlap['o1_name'],
                ev1=overlap['f1_evidence'],
                sub2=overlap['s2_name'],
                obj2=overlap['o2_name'],
                ev2=overlap['f2_evidence'],
                relation=overlap['relation']
            )
            
            is_conflict = llm_result.get('is_conflict', False)
            confidence = llm_result.get('confidence', 0.0)
            explanation = llm_result.get('explanation', '')
            
            if is_conflict:
                status = "auto_resolved" if confidence >= settings.conflict_auto_resolve_threshold else "pending_review"
                import uuid
                edge_id = str(uuid.uuid4())
                
                mark_query = """
                MATCH (f1:Fact {id: $f1_id, workspace_id: $workspace_id})
                MATCH (f2:Fact {id: $f2_id, workspace_id: $workspace_id})
                MERGE (f1)-[c:CONTRADICTS]-(f2)
                SET c.id = coalesce(c.id, $edge_id),
                    c.status = $status,
                    c.confidence = $confidence,
                    c.explanation = $explanation,
                    c.resolved_by = 'system',
                    c.resolved_at = datetime()
                """
                async with neo4j_client.driver.session() as session:
                    await session.run(mark_query, 
                                      f1_id=f1_id, f2_id=f2_id, 
                                      workspace_id=workspace_id,
                                      edge_id=edge_id,
                                      status=status,
                                      confidence=confidence,
                                      explanation=explanation)
                
                logger.info(f"Logged CONTRADICTS edge between {f1_id} and {f2_id} (status: {status})")
                conflicts_found += 1
            else:
                # To prevent re-auditing false positives indefinitely, we could mark a NON_CONFLICT edge,
                # but for now we only mark CONTRADICTS. If we don't mark anything, the query will hit it again.
                # Actually, the user's spec didn't mention this. I will mark it as [:NON_CONFLICT] so we skip it next time.
                skip_query = """
                MATCH (f1:Fact {id: $f1_id, workspace_id: $workspace_id})
                MATCH (f2:Fact {id: $f2_id, workspace_id: $workspace_id})
                MERGE (f1)-[c:NON_CONFLICT]-(f2)
                """
                async with neo4j_client.driver.session() as session:
                    await session.run(skip_query, f1_id=f1_id, f2_id=f2_id, workspace_id=workspace_id)
                logger.info(f"Marked NON_CONFLICT between {f1_id} and {f2_id}")

        except Exception as e:
            logger.error(f"Failed to validate overlap pair {f1_id} vs {f2_id}: {e}")
            
    return conflicts_found
