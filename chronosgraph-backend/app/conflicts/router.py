from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

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
    subject_name: str
    relation: str
    fact1_evidence: str
    fact2_evidence: str
    fact1_valid_from: Optional[str] = None
    fact2_valid_from: Optional[str] = None
    fact1_valid_to: Optional[str] = None
    fact2_valid_to: Optional[str] = None
    fact1_document_name: Optional[str] = None
    fact2_document_name: Optional[str] = None

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
           d1.filename AS fact1_document_name, d2.filename AS fact2_document_name
    ORDER BY c.resolved_at DESC
    """
    
    try:
        async with neo4j_client.driver.session() as session:
            result = await session.run(query, workspace_id=workspace_id)
            records = await result.data()
            
            return [ConflictResponse(**record) for record in records]
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
