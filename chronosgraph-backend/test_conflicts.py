import asyncio
import uuid
import logging
from unittest.mock import patch
from datetime import date

from app.database import engine
from app.graph.neo4j_client import neo4j_client
from app.conflicts.auditor import audit_workspace
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data setup query
SEED_QUERY = """
// Clean up workspace 999
MATCH (n {workspace_id: 999}) DETACH DELETE n;

// Subject A
CREATE (s:Entity {id: 'Subject A', workspace_id: 999, name: 'Subject A', type: 'Person'})
// Objects X, Y, Z
CREATE (x:Entity {id: 'Object X', workspace_id: 999, name: 'Object X', type: 'Organization'})
CREATE (y:Entity {id: 'Object Y', workspace_id: 999, name: 'Object Y', type: 'Organization'})
CREATE (z:Entity {id: 'Object Z', workspace_id: 999, name: 'Object Z', type: 'Organization'})

// Fact 1: Subject A -> Role -> Object X (2020-01-01 to 2023-01-01)
CREATE (f1:Fact {
    id: 'f1', workspace_id: 999, relation: 'CEO_OF', 
    evidence: 'Fact 1 Evidence', temporal_confidence: 'high',
    parsed_valid_from: date('2020-01-01'), parsed_valid_to: date('2023-01-01')
})
CREATE (f1)-[:SUBJECT]->(s)
CREATE (f1)-[:OBJECT]->(x)

// Fact 2: Subject A -> Role -> Object Y (2022-01-01 to 2024-01-01) - OVERLAPS FACT 1
CREATE (f2:Fact {
    id: 'f2', workspace_id: 999, relation: 'CEO_OF', 
    evidence: 'Fact 2 Evidence', temporal_confidence: 'high',
    parsed_valid_from: date('2022-01-01'), parsed_valid_to: date('2024-01-01')
})
CREATE (f2)-[:SUBJECT]->(s)
CREATE (f2)-[:OBJECT]->(y)

// Fact 3: Subject A -> Role -> Object Z (2025-01-01 to 2026-01-01) - NO OVERLAP
CREATE (f3:Fact {
    id: 'f3', workspace_id: 999, relation: 'CEO_OF', 
    evidence: 'Fact 3 Evidence', temporal_confidence: 'high',
    parsed_valid_from: date('2025-01-01'), parsed_valid_to: date('2026-01-01')
})
CREATE (f3)-[:SUBJECT]->(s)
CREATE (f3)-[:OBJECT]->(z)

// Fact 4: Overlaps Fact 2, but low confidence (2023-01-01 to null)
CREATE (f4:Fact {
    id: 'f4', workspace_id: 999, relation: 'CEO_OF', 
    evidence: 'Fact 4 Evidence', temporal_confidence: 'low',
    parsed_valid_from: date('2023-01-01')
})
CREATE (f4)-[:SUBJECT]->(s)
CREATE (f4)-[:OBJECT]->(z)

// Fact 5: Ongoing (null valid_to), overlaps Fact 3 (2024-06-01 to null)
CREATE (f5:Fact {
    id: 'f5', workspace_id: 999, relation: 'CEO_OF', 
    evidence: 'Fact 5 Evidence', temporal_confidence: 'high',
    parsed_valid_from: date('2024-06-01')
})
CREATE (f5)-[:SUBJECT]->(s)
CREATE (f5)-[:OBJECT]->(x)
"""

VERIFY_QUERY = """
MATCH (f1:Fact {workspace_id: 999})-[c:CONTRADICTS]-(f2:Fact {workspace_id: 999})
WHERE f1.id < f2.id
RETURN f1.id AS f1, f2.id AS f2, c.status AS status, c.confidence AS confidence
"""

# Mock LLM behavior
async def mock_generate_completion(system_prompt, user_prompt, response_format):
    import json
    logger.info(f"MOCK CALLED WITH: {user_prompt}")
    
    # Check which facts are being compared based on evidence
    if '"Fact 1 Evidence"' in user_prompt and '"Fact 2 Evidence"' in user_prompt:
        # High confidence conflict -> Test Case A
        return json.dumps({
            "is_conflict": True,
            "confidence": 0.95,
            "explanation": "High confidence contradiction"
        })
    elif '"Fact 3 Evidence"' in user_prompt and '"Fact 5 Evidence"' in user_prompt:
        # Low confidence conflict -> Test Case B
        return json.dumps({
            "is_conflict": True,
            "confidence": 0.50,
            "explanation": "Ambiguous contradiction"
        })
    else:
        # Default to false
        return json.dumps({
            "is_conflict": False,
            "confidence": 0.0,
            "explanation": "No conflict"
        })


async def main():
    await neo4j_client.connect()
    try:
        logger.info("Seeding test data...")
        async with neo4j_client.driver.session() as session:
            for q in SEED_QUERY.split(';'):
                if q.strip():
                    await session.run(q.strip())
            
        logger.info("Running audit workspace task...")
        
        # Patch the generate_completion function in app.conflicts.auditor
        with patch('app.conflicts.auditor.generate_completion', side_effect=mock_generate_completion):
            conflicts_found = await audit_workspace(999)
            
        logger.info(f"Audit complete. Reported {conflicts_found} conflicts.")
        
        # Verify results
        async with neo4j_client.driver.session() as session:
            res = await session.run(VERIFY_QUERY)
            edges = await res.data()
            
        logger.info("--- TEST RESULTS ---")
        for edge in edges:
            logger.info(f"Edge: {edge['f1']} <-> {edge['f2']} | Status: {edge['status']} | Confidence: {edge['confidence']}")
            
        # Assertions
        assert len(edges) == 2, f"Expected 2 conflicts, got {len(edges)}"
        
        f1_f2 = next((e for e in edges if e['f1'] == 'f1' and e['f2'] == 'f2'), None)
        assert f1_f2 is not None, "Missing f1 <-> f2 edge"
        assert f1_f2['status'] == 'auto_resolved', f"f1-f2 status should be 'auto_resolved', got {f1_f2['status']}"
        
        f3_f5 = next((e for e in edges if e['f1'] == 'f3' and e['f2'] == 'f5'), None)
        assert f3_f5 is not None, "Missing f3 <-> f5 edge"
        assert f3_f5['status'] == 'pending_review', f"f3-f5 status should be 'pending_review', got {f3_f5['status']}"
        
        logger.info("All assertions passed! The two-tier resolution logic works perfectly.")
        
    finally:
        await neo4j_client.close()
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
