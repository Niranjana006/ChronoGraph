import asyncio
from app.graph.neo4j_client import neo4j_client

async def main():
    ws_id = 112
    await neo4j_client.connect()
    
    print(f"=== MERGE CANDIDATES IN WORKSPACE {ws_id} ===")
    query = """
    MATCH (mc:MergeCandidate {workspace_id: $workspace_id})
    RETURN mc.entity_a AS entity_a, mc.entity_b AS entity_b, mc.score AS score, mc.status AS status
    """
    async with neo4j_client.driver.session() as session:
        res = await session.run(query, workspace_id=ws_id)
        records = await res.data()
        print(f"Total Pending Merge Candidates: {len(records)}")
        for r in records:
            print(f"  Candidate: '{r['entity_a']}' <--> '{r['entity_b']}' | Score: {r['score']:.4f} | Status: {r['status']}")

    await neo4j_client.close()

if __name__ == "__main__":
    asyncio.run(main())
