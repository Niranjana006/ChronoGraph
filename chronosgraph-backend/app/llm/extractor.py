import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field

from app.llm.client import generate_completion

logger = logging.getLogger(__name__)

class EntitySchema(BaseModel):
    id: str = Field(description="Unique identifier for the entity within this extraction (e.g., e1, e2).")
    name: str = Field(description="The exact name of the entity as it appears in the text.")
    type: str = Field(description="The type of the entity (e.g., Person, Organization, Location, Event, Concept).")

class FactSchema(BaseModel):
    source: str = Field(description="The ID of the source (subject) entity.")
    target: str = Field(description="The ID of the target (object) entity.")
    relation: str = Field(description="The relationship between the source and target (e.g., MEMBER_OF, BORN_IN). Must be UPPERCASE_SNAKE_CASE.")
    valid_from: Optional[str] = Field(description="The starting date or time context for this fact, if mentioned (ISO 8601 or raw string). null if not applicable.")
    valid_to: Optional[str] = Field(description="The ending date or time context for this fact, if mentioned. null if not applicable.")
    evidence: str = Field(description="The exact quote or excerpt from the text that proves this fact.")

class ExtractionSchema(BaseModel):
    entities: List[EntitySchema]
    facts: List[FactSchema]

SYSTEM_PROMPT = """You are an expert knowledge graph extractor. 
Your task is to extract entities and facts from the provided text snippet.
You MUST output valid JSON conforming exactly to the requested schema.

Extract all relevant entities. Then, extract the relationships (facts) between them using a Subject-Relation-Object triple model.
Crucially, look for temporal bounds. If a fact is only true during a specific time, capture it in `valid_from` and `valid_to`.

CRITICAL INSTRUCTION: DO NOT extract pronouns (e.g., "He", "She", "It", "They", "This", "That") as entities. Only extract concrete named entities (e.g., "John F. Kennedy", "Apple", "United States"). Resolve pronouns to their referents if possible, otherwise ignore them.

Schema Requirement:
{
  "entities": [
    {"id": "e1", "name": "...", "type": "..."}
  ],
  "facts": [
    {
      "source": "e1",
      "target": "e2",
      "relation": "RELATION_NAME",
      "valid_from": "YYYY-MM-DD or context",
      "valid_to": "YYYY-MM-DD or context",
      "evidence": "Exact quote from text"
    }
  ]
}

Return ONLY the JSON object. Do not wrap it in markdown block quotes (```json ... ```).
"""

PRONOUNS = {
    "he", "she", "it", "they", "him", "her", "them", 
    "his", "hers", "its", "their", "theirs",
    "i", "me", "my", "mine", "we", "us", "our", "ours",
    "you", "your", "yours", "this", "that", "these", "those"
}

async def extract_graph_from_chunk(text_chunk: str) -> ExtractionSchema:
    """
    Calls the LLM to extract entities and facts from a chunk of text.
    Returns a validated Pydantic model.
    """
    logger.info("Extracting graph from chunk...")
    response_json_str = await generate_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=text_chunk,
        response_format={"type": "json_object"}
    )
    
    try:
        # Pydantic will validate the structure
        parsed_data = json.loads(response_json_str)
        extraction = ExtractionSchema(**parsed_data)
        
        # 2nd line of defense: filter out pronoun entities
        filtered_entities = []
        rejected_entity_ids = set()
        for e in extraction.entities:
            if e.name.strip().lower() in PRONOUNS:
                rejected_entity_ids.add(e.id)
                logger.warning(f"Filtered out pronoun entity: {e.name}")
            else:
                filtered_entities.append(e)
                
        # Filter facts that rely on rejected entities
        filtered_facts = []
        for f in extraction.facts:
            if f.source in rejected_entity_ids or f.target in rejected_entity_ids:
                logger.warning(f"Filtered out fact dependent on pronoun entity: {f.source} -> {f.target}")
            else:
                filtered_facts.append(f)
                
        extraction.entities = filtered_entities
        extraction.facts = filtered_facts
        
        return extraction
    except Exception as e:
        logger.error(f"Failed to parse LLM output: {e}\nRaw output: {response_json_str}")
        # Return empty rather than failing the whole pipeline, though this could be handled differently
        return ExtractionSchema(entities=[], facts=[])
