import logging
import json
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from httpx import HTTPError

from app.llm.client import generate_completion

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an intelligent knowledge assistant connected to a Knowledge Graph.
Your task is to answer the user's question based ONLY on the retrieved graph context provided.

The context contains facts extracted from documents. It may also contain explicitly flagged CONTRADICTIONS between facts.
You MUST handle contradictions as follows:
1. If a contradiction has status 'pending_review', present BOTH facts to the user as unresolved and explicitly note that a human review is pending.
2. If a contradiction has status 'auto_resolved', state the system's high-confidence answer clearly, but transparently mention that conflicting information was found and briefly explain why the other version was deprioritized.

You MUST cite your sources. Return a structured JSON object containing:
- "answer": A natural language string answering the question, incorporating the conflict logic above.
- "citations": An array of citation objects, each containing:
  - "fact_id": The ID of the fact cited.
  - "evidence": The exact string evidence from the document.
  - "document_name": The name of the source document.
  - "valid_from": The valid from date string if it exists in context, else null.
  - "valid_to": The valid to date string if it exists in context, else null.
  - "entity_name": The name of the core subject entity involved in this fact.
- "conflicts": An array of conflict objects if any were present in the context, each containing:
  - "status": The status of the conflict.
  - "explanation": The system's explanation of the conflict.

Only output valid JSON.
"""

def format_context(retrieved_data: list[dict]) -> str:
    """
    Takes the raw Cypher results and formats them into a readable string for the LLM.
    """
    if not retrieved_data:
        return "No relevant facts found in the knowledge graph."
        
    context_blocks = []
    processed_facts = set()
    
    for record in retrieved_data:
        fact_id = record["fact_id"]
        if fact_id in processed_facts:
            continue
            
        processed_facts.add(fact_id)
        
        # Build basic fact string
        subject = record["matched_entity"] if record["relation_to_fact"] == "SUBJECT" else record["other_entity"]
        obj = record["matched_entity"] if record["relation_to_fact"] == "OBJECT" else record["other_entity"]
        relation = record["fact_relation"]
        
        fact_str = f"Fact [{fact_id}]: {subject} -> {relation} -> {obj}"
        if record["valid_from"]:
            fact_str += f" (Valid From: {record['valid_from']})"
        if record["valid_to"]:
            fact_str += f" (Valid To: {record['valid_to']})"
            
        fact_str += f"\nSource Document: {record.get('document_name', 'Unknown')}"
        fact_str += f"\nEvidence: \"{record['evidence']}\""
        
        # Add conflict info if present
        if record["conflict_status"]:
            fact_str += f"\n!!! CONFLICT DETECTED ({record['conflict_status']}) !!!"
            fact_str += f"\nSystem Explanation: {record['conflict_explanation']}"
            fact_str += f"\nConflicts with Fact [{record['conflicting_fact_id']}]: \"{record['conflicting_evidence']}\""
            
        context_blocks.append(fact_str)
        
    return "\n\n".join(context_blocks)

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(HTTPError)
)
async def generate_response(query: str, retrieved_data: list[dict]) -> dict:
    context_str = format_context(retrieved_data)
    
    prompt = f"""
Context from Knowledge Graph:
=============================
{context_str}
=============================

User Question: {query}
"""
    
    logger.info(f"Generating LLM response with {len(retrieved_data)} context records.")
    
    response_json = await generate_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt,
        response_format={"type": "json_object"}
    )
    
    try:
        return json.loads(response_json)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}")
        return {
            "answer": "Sorry, I encountered an error generating the response.",
            "citations": [],
            "conflicts": []
        }
