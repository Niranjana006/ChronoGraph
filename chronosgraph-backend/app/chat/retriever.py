import logging
import json
from sentence_transformers import SentenceTransformer, util
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from httpx import HTTPError

from app.graph.neo4j_client import neo4j_client
from app.llm.client import generate_completion
from app.config import settings
from app.resolution.entities import get_embedder

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a query analysis AI for a Knowledge Graph.
Extract the core entities from the user's question. These are typically proper nouns, companies, people, or locations.
Return a JSON object containing an array of strings called 'entities'.
If no clear entities are present, return an empty array.
"""

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(HTTPError)
)
async def extract_query_entities(query: str) -> list[str]:
    prompt = f"User Question: {query}"
    response_json = await generate_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt,
        response_format={"type": "json_object"}
    )
    data = json.loads(response_json)
    return data.get("entities", [])

async def retrieve_context(workspace_id: int, query: str):
    """
    1. Extracts entities from query.
    2. Uses vector similarity to find matching Entity nodes in Neo4j.
    3. Traverses graph to get facts and [:CONTRADICTS] edges.
    """
    # 1. Extract entities from query
    query_entities = await extract_query_entities(query)
    logger.info(f"Extracted entities from query: {query_entities}")
    
    if not query_entities:
        return []
        
    # 2. Vector match against workspace entities
    query_fetch = """
    MATCH (e:Entity {workspace_id: $workspace_id})
    RETURN e.id AS name
    """
    async with neo4j_client.driver.session() as session:
        result = await session.run(query_fetch, workspace_id=workspace_id)
        records = await result.data()
        
    if not records:
        return []
        
    workspace_entity_names = [record["name"] for record in records]
    
    # Embed both as tensors for sentence_transformers.util.cos_sim
    emb = get_embedder()
    query_embs = emb.encode(query_entities, convert_to_tensor=True)
    workspace_embs = emb.encode(workspace_entity_names, convert_to_tensor=True)
    
    sim_matrix = util.cos_sim(query_embs, workspace_embs)
    
    matched_entity_names = set()
    for i in range(len(query_entities)):
        for j in range(len(workspace_entity_names)):
            if sim_matrix[i][j].item() >= 0.70: # Threshold for matching query entity to graph entity
                matched_entity_names.add(workspace_entity_names[j])
                
    if not matched_entity_names:
        logger.info("No matching entities found in the graph.")
        return []
        
    logger.info(f"Matched graph entities: {matched_entity_names}")
    
    # 3. Cypher Traversal for 1-hop facts and conflicts
    # We want to pull any Fact connected to these matched entities, 
    # AND optionally any CONTRADICTS edge bridging that Fact to another Fact.
    traversal_query = """
    MATCH (e:Entity {workspace_id: $workspace_id})
    WHERE e.id IN $matched_names
    MATCH (e)-[r]-(f:Fact {workspace_id: $workspace_id})
    // Get the other entity involved in this fact
    MATCH (f)-[r2]-(e2:Entity)
    WHERE e2.id <> e.id
    OPTIONAL MATCH (f)-[:SOURCED_FROM]->(d:Document)
    OPTIONAL MATCH (f)-[c:CONTRADICTS]-(f2:Fact {workspace_id: $workspace_id})
    RETURN e.id AS matched_entity, 
           type(r) AS relation_to_fact,
           f.id AS fact_id,
           f.relation AS fact_relation,
           f.valid_from AS valid_from,
           f.valid_to AS valid_to,
           f.evidence AS evidence,
           e2.id AS other_entity,
           type(r2) AS other_relation,
           d.filename AS document_name,
           c.status AS conflict_status,
           c.explanation AS conflict_explanation,
           f2.id AS conflicting_fact_id,
           f2.evidence AS conflicting_evidence
    """
    
    async with neo4j_client.driver.session() as session:
        result = await session.run(traversal_query, workspace_id=workspace_id, matched_names=list(matched_entity_names))
        retrieved_data = await result.data()
        
    return retrieved_data
