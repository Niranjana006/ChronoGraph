from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Union

from app.graph.neo4j_client import neo4j_client

router = APIRouter(prefix="/workspaces/{workspace_id}/conflicts", tags=["conflicts"])

class ConflictResponse(BaseModel):
    id: str
    status: str
    confidence: float
    explanation: str
    resolved_by: str
    resolved_at: str
    fact1_id: str
    fact2_id: str
    subject_name: Union[str, List[str]]
    relation: str
    fact1_evidence: str
    fact2_evidence: str
    fact1_valid_from: Optional[str] = None
    fact2_valid_from: Optional[str] = None
    fact1_valid_to: Optional[str] = None
    fact2_valid_to: Optional[str] = None
    fact1_document_name: Optional[str] = None
    fact2_document_name: Optional[str] = None
    fact1_value: Optional[Union[str, List[str]]] = None
    fact2_value: Optional[Union[str, List[str]]] = None

class ResolveConflictRequest(BaseModel):
    status: str
    resolved_by: str

@router.get("", response_model=List[ConflictResponse])
async def get_conflicts(workspace_id: int):
    """
    Get all conflicts for a workspace.
    """
    query = """
    MATCH (f1:Fact {workspace_id: $workspace_id})-[c:CONTRADICTS]-(f2:Fact {workspace_id: $workspace_id})
    MATCH (f1)-[:SUBJECT]->(s:Entity)
    OPTIONAL MATCH (f1)-[:SOURCED_FROM]->(d1:Document)
    OPTIONAL MATCH (f2)-[:SOURCED_FROM]->(d2:Document)
    OPTIONAL MATCH (f1)-[:OBJECT]->(o1:Entity)
    OPTIONAL MATCH (f2)-[:OBJECT]->(o2:Entity)
    // To avoid duplicates since it's an undirected edge in the query, enforce f1.id < f2.id
    WHERE f1.id < f2.id
    RETURN c.id AS id, c.status AS status, c.confidence AS confidence, 
           c.explanation AS explanation, c.resolved_by AS resolved_by, 
           toString(c.resolved_at) AS resolved_at,
           f1.id AS fact1_id, f2.id AS fact2_id,
           s.name AS subject_name, f1.relation AS relation,
           f1.evidence AS fact1_evidence, f2.evidence AS fact2_evidence,
           f1.valid_from AS fact1_valid_from, f2.valid_from AS fact2_valid_from,
           f1.valid_to AS fact1_valid_to, f2.valid_to AS fact2_valid_to,
           d1.filename AS fact1_document_name, d2.filename AS fact2_document_name,
           o1.name AS fact1_value, o2.name AS fact2_value
    ORDER BY c.resolved_at DESC
    """
    
    try:
        async with neo4j_client.driver.session() as session:
            result = await session.run(query, workspace_id=workspace_id)
            records = await result.data()
            
            return [ConflictResponse(**record) for record in records]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{conflict_id}")
async def get_conflict_graph(workspace_id: int, conflict_id: str):
    """
    Get a specific conflict and its surrounding fact graph.
    """
    query = """
    MATCH (f1:Fact {workspace_id: $workspace_id})-[c:CONTRADICTS {id: $conflict_id}]-(f2:Fact {workspace_id: $workspace_id})
    MATCH (f1)-[:SUBJECT]->(s:Entity)
    OPTIONAL MATCH (f1)-[:SOURCED_FROM]->(d1:Document)
    OPTIONAL MATCH (f2)-[:SOURCED_FROM]->(d2:Document)
    
    // Find all facts associated with this entity to build the timeline
    MATCH (all_f:Fact {workspace_id: $workspace_id})-[:SUBJECT]->(s)
    OPTIONAL MATCH (all_f)-[:SOURCED_FROM]->(all_d:Document)
    
    WITH c, f1, f2, s, d1, d2, collect(all_f {
        .id, 
        .valid_from, 
        .valid_to, 
        .evidence, 
        .relation,
        value: [(all_f)-[:OBJECT]->(o:Entity) | o.name][0],
        document_name: all_d.filename
    }) as entity_facts
    
    RETURN c.id AS id, c.status AS status, c.confidence AS confidence, 
           c.explanation AS explanation, c.resolved_by AS resolved_by, 
           toString(c.resolved_at) AS resolved_at,
           f1.id AS fact1_id, f2.id AS fact2_id,
           s.name AS subject_name,
           entity_facts
    """
    
    try:
        async with neo4j_client.driver.session() as session:
            result = await session.run(query, workspace_id=workspace_id, conflict_id=conflict_id)
            record = await result.single()
            
            if not record:
                raise HTTPException(status_code=404, detail="Conflict not found")
                
            return record.data()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{conflict_id}/resolve")
async def resolve_conflict(workspace_id: int, conflict_id: str, req: ResolveConflictRequest):
    """
    Update the status of a conflict (e.g. human reviewed).
    """
    query = """
    MATCH (f1:Fact {workspace_id: $workspace_id})-[c:CONTRADICTS {id: $conflict_id}]-(f2:Fact {workspace_id: $workspace_id})
    SET c.status = $status,
        c.resolved_by = $resolved_by,
        c.resolved_at = datetime()
    RETURN c.id AS id, c.status AS status
    """
    
    try:
        async with neo4j_client.driver.session() as session:
            result = await session.run(query, workspace_id=workspace_id, conflict_id=conflict_id, 
                                       status=req.status, resolved_by=req.resolved_by)
            record = await result.single()
            
            if not record:
                raise HTTPException(status_code=404, detail="Conflict not found")
                
            return {"message": "Conflict resolved", "id": record["id"], "status": record["status"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
