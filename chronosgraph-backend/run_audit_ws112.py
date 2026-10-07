import asyncio
import logging
logging.basicConfig(level=logging.INFO)
from app.graph.neo4j_client import neo4j_client
from app.resolution.entities import resolve_entities
from app.resolution.temporal import resolve_temporal
from app.conflicts.auditor import audit_workspace

async def main():
    ws_id = 112
    await neo4j_client.connect()
    
    print(f"\n==========================================")
    print(f"--- 1. ENTITY RESOLUTION FOR WORKSPACE {ws_id} ---")
    print(f"==========================================")
    merged_entities = await resolve_entities(ws_id)
    print("Merged Entities Total:", len(merged_entities))
    for m in merged_entities:
        print(f"  Merged: '{m[0]}' --> '{m[1]}' (score: {m[2]:.4f})")
    
    print(f"\n==========================================")
    print(f"--- 2. TEMPORAL NORMALIZATION FOR WORKSPACE {ws_id} ---")
    print(f"==========================================")
    timeline_updates = await resolve_temporal(ws_id)
    print("Timeline Updates Total:", timeline_updates)
    
    print(f"\n==========================================")
    print(f"--- 3. CONFLICT AUDIT SWARM FOR WORKSPACE {ws_id} ---")
    print(f"==========================================")
    conflict_count = await audit_workspace(ws_id)
    print(f"TOTAL NEW CONFLICTS LOGGED: {conflict_count}")

    # Fetch and display logged conflicts from Neo4j
    query = """
    MATCH (f1:Fact {workspace_id: $workspace_id})-[c:CONTRADICTS]-(f2:Fact {workspace_id: $workspace_id})
    MATCH (f1)-[:SUBJECT]->(s:Entity)
    WHERE f1.id < f2.id
    RETURN c.id AS id, s.name AS subject_name, c.status AS status, c.confidence AS confidence, c.explanation AS explanation
    """
    async with neo4j_client.driver.session() as session:
        res = await session.run(query, workspace_id=ws_id)
        records = await res.data()
        print(f"\nFetched {len(records)} CONTRADICTS edges from Neo4j for Workspace {ws_id}:")
        for i, r in enumerate(records, 1):
            print(f"\nConflict #{i}:")
            print(f"  ID: {r.get('id')}")
            print(f"  Subject: {r.get('subject_name')}")
            print(f"  Status: {r.get('status')}")
            print(f"  Confidence: {r.get('confidence')}")
            print(f"  Explanation: {r.get('explanation')}")

    await neo4j_client.close()

if __name__ == "__main__":
    asyncio.run(main())
