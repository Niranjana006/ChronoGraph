import asyncio
from app.database import AsyncSessionLocal
from app.ingestion.models import Document
from app.graph.neo4j_client import neo4j_client
from sqlalchemy.future import select

async def main():
    await neo4j_client.connect()
    
    # 1. Inspect Postgres Documents
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Document).order_by(Document.id.desc()))
        docs = res.scalars().all()[:15]
        print("=== RECENT POSTGRES DOCUMENTS ===")
        for d in docs:
            print(f"Doc ID: {d.id} | Workspace ID: {d.workspace_id} | Name: {d.filename} | Status: {d.status} | Stage: {d.current_stage}")

    # 2. Inspect Neo4j Conflicts across workspaces
    print("\n=== NEO4J CONFLICTS PER WORKSPACE ===")
    query = """
    MATCH (f1:Fact)-[c:CONTRADICTS]-(f2:Fact)
    WHERE f1.id < f2.id
    RETURN f1.workspace_id AS ws_id, count(c) AS conflict_count
    """
    async with neo4j_client.driver.session() as session:
        res = await session.run(query)
        records = await res.data()
        for r in records:
            print(f"Workspace ID: {r['ws_id']} | Total Conflicts: {r['conflict_count']}")

    # 3. Detailed conflicts in recent workspaces
    query_details = """
    MATCH (f1:Fact)-[c:CONTRADICTS]-(f2:Fact)
    MATCH (f1)-[:SUBJECT]->(s:Entity)
    WHERE f1.id < f2.id
    RETURN f1.workspace_id AS ws_id, c.id AS c_id, s.name AS entity, c.status AS status, c.explanation AS explanation
    LIMIT 10
    """
    async with neo4j_client.driver.session() as session:
        res = await session.run(query_details)
        records = await res.data()
        print("\n=== SAMPLE CONFLICT DETAILS ===")
        for r in records:
            print(f"WS: {r['ws_id']} | Entity: {r['entity']} | Status: {r['status']} | Expl: {r['explanation']}")

    await neo4j_client.close()

if __name__ == "__main__":
    asyncio.run(main())
