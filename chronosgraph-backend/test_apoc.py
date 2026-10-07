import asyncio
from app.graph.neo4j_client import neo4j_client

async def main():
    await neo4j_client.connect()
    
    # Try merging '30 days' and '30 calendar days' in Workspace 112
    ws_id = 112
    name_a = "30 days"
    name_b = "30 calendar days"
    
    query = """
    MATCH (ea:Entity {id: $name_a, workspace_id: $workspace_id})
    MATCH (eb:Entity {id: $name_b, workspace_id: $workspace_id})
    CALL apoc.refactor.mergeNodes([ea, eb], {
        properties: "overwrite",
        mergeRels: true
    }) YIELD node
    RETURN node.id AS id
    """
    try:
        res = await neo4j_client.execute_write(query, {"workspace_id": ws_id, "name_a": name_a, "name_b": name_b})
        print("APOC Merge Success:", res)
    except Exception as e:
        print("APOC Merge Error:", e)

    await neo4j_client.close()

if __name__ == "__main__":
    asyncio.run(main())
