import logging
import json
from pydantic import BaseModel, Field
from typing import Dict
from app.graph.neo4j_client import neo4j_client
from app.llm.client import generate_completion

logger = logging.getLogger(__name__)

class TemporalResolution(BaseModel):
    fact_id: str = Field(description="The original fact_id from the input.")
    parsed_valid_from: str | None = Field(description="ISO-8601 date string (e.g. 1961-01-01), or null if unable to resolve.")
    parsed_valid_to: str | None = Field(description="ISO-8601 date string (e.g. 1963-12-31), or null if unable to resolve.")
    temporal_confidence: str = Field(description="Must be 'high' if you confidently resolved a date, or 'low' if the text is ambiguous.")

class TemporalNormalizationResponse(BaseModel):
    results: list[TemporalResolution] = Field(description="A list of normalized temporal resolutions.")

async def resolve_temporal(workspace_id: int):
    """
    Finds Facts in a workspace that have raw valid_from/valid_to strings but no 
    parsed native Date types. Uses the LLM to normalize them.
    """
    logger.info(f"Starting temporal normalization for workspace {workspace_id}...")
    
    # 1. Fetch facts that need normalization
    query_fetch = """
    MATCH (f:Fact {workspace_id: $workspace_id})-[:SOURCED_FROM]->(d:Document)
    WHERE f.parsed_valid_from IS NULL AND f.temporal_confidence IS NULL
    RETURN f.id AS fact_id, f.valid_from AS valid_from, f.valid_to AS valid_to, f.evidence AS evidence
    """
    
    records = await neo4j_client.execute_write(query_fetch, {"workspace_id": workspace_id})
    
    if not records:
        logger.info("No facts require temporal normalization.")
        return 0
        
    logger.info(f"Found {len(records)} facts needing temporal normalization.")
    
    # Process in batches of 10 to avoid huge LLM context windows
    batch_size = 10
    total_processed = 0
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        
        prompt_data = {
            "instructions": "You are a temporal normalization engine. Convert relative or fuzzy temporal phrases into concrete ISO-8601 dates (YYYY-MM-DD). If a fact says someone 'became CEO in 2020' or started something in 2020, set valid_from to '2020-01-01' and leave valid_to as null (meaning ongoing). If they 'were CEO from 2020 to 2022', set valid_from='2020-01-01', valid_to='2022-12-31'. If the fact is ambiguous (like 'recently', 'later') and you cannot confidently provide a date, set temporal_confidence to 'low' and leave the dates null. DO NOT GUESS DATES.",
            "expected_output_schema": TemporalNormalizationResponse.model_json_schema(),
            "facts_to_normalize": batch
        }
        
        try:
            response_text = await generate_completion(
                system_prompt="You are a strict JSON data extractor. Output ONLY valid JSON matching the schema.",
                user_prompt=json.dumps(prompt_data),
                response_format={"type": "json_object"}
            )
            
            parsed_json = json.loads(response_text)
            # Validate schema
            response = TemporalNormalizationResponse(**parsed_json)
            
            # 2. Update the graph with the parsed dates
            for resolution in response.results:
                update_query = """
                MATCH (f:Fact {id: $fact_id})
                SET f.temporal_confidence = $confidence
                """
                params = {
                    "fact_id": resolution.fact_id,
                    "confidence": resolution.temporal_confidence
                }
                
                # If high confidence and we have dates, parse them as native Neo4j dates
                if resolution.temporal_confidence == "high":
                    if resolution.parsed_valid_from:
                        update_query += ", f.parsed_valid_from = date($valid_from)"
                        params["valid_from"] = resolution.parsed_valid_from
                    if resolution.parsed_valid_to:
                        update_query += ", f.parsed_valid_to = date($valid_to)"
                        params["valid_to"] = resolution.parsed_valid_to
                        
                await neo4j_client.execute_write(update_query, params)
                total_processed += 1
                
        except Exception as e:
            logger.error(f"Failed to normalize batch: {e}")
            
    logger.info(f"Temporal normalization complete. Processed {total_processed} facts.")
    return total_processed
