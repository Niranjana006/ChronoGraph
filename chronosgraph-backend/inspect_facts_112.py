import asyncio
from app.graph.neo4j_client import neo4j_client

async def main():
    ws_id = 112
    await neo4j_client.connect()
    
    print(f"=== ALL ENTITIES IN WORKSPACE {ws_id} ===")
    query_ent = """
    MATCH (e:Entity {workspace_id: $workspace_id})
    RETURN e.id AS id, e.name AS name, e.type AS type
    """
    async with neo4j_client.driver.session() as session:
        res = await session.run(query_ent, workspace_id=ws_id)
        records = await res.data()
        for r in records:
            print(f"  Entity: {r['name']} ({r['type']})")

    print(f"\n=== ALL FACTS IN WORKSPACE {ws_id} ===")
    query_facts = """
    MATCH (f:Fact {workspace_id: $workspace_id})
    MATCH (f)-[:SUBJECT]->(s:Entity)
    MATCH (f)-[:OBJECT]->(o:Entity)
    OPTIONAL MATCH (f)-[:SOURCED_FROM]->(d:Document)
    RETURN f.id AS id, s.name AS sub, f.relation AS rel, o.name AS obj, 
           f.valid_from AS valid_from, f.valid_to AS valid_to, 
           f.evidence AS evidence, d.filename AS doc
    """
    async with neo4j_client.driver.session() as session:
        res = await session.run(query_facts, workspace_id=ws_id)
        records = await res.data()
        print(f"Total Facts in Workspace {ws_id}: {len(records)}")
        for r in records:
            print(f"  [{r['doc']}] {r['sub']} --({r['rel']})--> {r['obj']} | Valid: {r['valid_from']} to {r['valid_to']}")
            print(f"    Evidence: \"{r['evidence']}\"")

    await neo4j_client.close()

if __name__ == "__main__":
    asyncio.run(main())
