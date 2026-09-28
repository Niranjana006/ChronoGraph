import urllib.parse
from fastapi import APIRouter, HTTPException
from typing import List

from app.graph.neo4j_client import neo4j_client

router = APIRouter(prefix="/workspaces/{workspace_id}/entities", tags=["entities"])

@router.get("/{entity_id}")
async def get_entity(workspace_id: int, entity_id: str):
    """
    Get a specific entity and all its facts to build the timeline view.
    """
    # entity_id might be URL encoded (e.g. "Sick Leave Policy" -> "Sick%20Leave%20Policy")
    decoded_entity_id = urllib.parse.unquote(entity_id)
    
    query = """
    MATCH (s:Entity {name: $entity_id, workspace_id: $workspace_id})
    
    // Find all facts associated with this entity
    MATCH (f:Fact {workspace_id: $workspace_id})-[:SUBJECT]->(s)
    OPTIONAL MATCH (f)-[:SOURCED_FROM]->(d:Document)
    OPTIONAL MATCH (f)-[:OBJECT]->(o:Entity)
    
    WITH s, collect(f {
        .id, 
        .valid_from, 
        .valid_to, 
        .evidence, 
        .relation,
        value: o.name,
        document_name: d.filename
    }) as facts
    
    RETURN s.name AS id, s.name AS name, s.type AS type, facts
    """
    
    try:
        async with neo4j_client.driver.session() as session:
            result = await session.run(query, workspace_id=workspace_id, entity_id=decoded_entity_id)
            record = await result.single()
            
            if not record:
                raise HTTPException(status_code=404, detail="Entity not found")
                
            return record.data()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
