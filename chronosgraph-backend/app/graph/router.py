from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.graph.neo4j_client import neo4j_client

router = APIRouter(prefix="/workspaces", tags=["graph"])

@router.get("/{workspace_id}/graph")
async def get_workspace_graph(workspace_id: int) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetches the Knowledge Graph for a specific workspace to be rendered in the UI.
    Returns nodes (Entities) and links (Facts connecting them).
    """
    try:
        query = """
        MATCH (f:Fact {workspace_id: $workspace_id})
        MATCH (f)-[:SUBJECT]->(sub:Entity)
        MATCH (f)-[:OBJECT]->(obj:Entity)
        RETURN sub.id AS source, sub.name AS source_name, sub.type AS source_type,
               obj.id AS target, obj.name AS target_name, obj.type AS target_type,
               f.relation AS relation, f.id AS fact_id, f.evidence AS evidence
        """
        
        records = await neo4j_client.execute_write(query, {"workspace_id": workspace_id})
        
        nodes_map = {}
        links = []
        
        for record in records:
            source_id = record["source"]
            target_id = record["target"]
            
            # Add source node if not exists
            if source_id not in nodes_map:
                nodes_map[source_id] = {
                    "id": source_id,
                    "name": record["source_name"],
                    "type": record["source_type"]
                }
                
            # Add target node if not exists
            if target_id not in nodes_map:
                nodes_map[target_id] = {
                    "id": target_id,
                    "name": record["target_name"],
                    "type": record["target_type"]
                }
                
            # Add link
            links.append({
                "source": source_id,
                "target": target_id,
                "label": record["relation"],
                "fact_id": record["fact_id"],
                "evidence": record["evidence"]
            })
            
        return {
            "nodes": list(nodes_map.values()),
            "links": links
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
