from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.auth.models import User
from app.auth.dependencies import get_current_user
from app.workspaces.schemas import WorkspaceCreate, WorkspaceResponse, ChatCreate, ChatResponse
import app.workspaces.service as ws_service
from app.graph.neo4j_client import neo4j_client

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

class AuditEntryResponse(BaseModel):
    id: str
    workspaceId: str
    timestamp: str
    entityName: str
    summary: str
    resolution: str  # "auto" | "human"
    resolvedBy: str
    status: str      # "resolved" | "escalated" | "pending"

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return await ws_service.create_workspace(db, data.name, current_user)


@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return await ws_service.get_user_workspaces(db, current_user.id)


@router.post("/{workspace_id}/chats", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    workspace_id: int, 
    data: ChatCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return await ws_service.create_chat(db, workspace_id, data.title, current_user)


@router.get("/{workspace_id}/chats", response_model=List[ChatResponse])
async def list_chats(
    workspace_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return await ws_service.get_workspace_chats(db, workspace_id, current_user)


@router.get("/{workspace_id}/audit-log", response_model=List[AuditEntryResponse])
async def get_audit_log(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit log of all contradiction resolutions (auto or human) for a workspace.
    """
    query = """
    MATCH (f1:Fact {workspace_id: $workspace_id})-[c:CONTRADICTS]-(f2:Fact {workspace_id: $workspace_id})
    OPTIONAL MATCH (f1)-[:SUBJECT]->(s:Entity)
    WHERE f1.id < f2.id
    RETURN c.id AS id,
           c.status AS status,
           c.confidence AS confidence,
           c.explanation AS explanation,
           c.resolved_by AS resolved_by,
           toString(coalesce(c.resolved_at, datetime())) AS timestamp,
           coalesce(s.name, "Unknown Entity") AS entityName,
           f1.evidence AS fact1_evidence,
           f2.evidence AS fact2_evidence,
           f1.relation AS relation
    ORDER BY timestamp DESC
    """
    try:
        async with neo4j_client.driver.session() as session:
            result = await session.run(query, workspace_id=workspace_id)
            records = await result.data()
            
            entries = []
            for r in records:
                exp = r["explanation"] or f"{r['relation']}: {r['fact1_evidence']} vs {r['fact2_evidence']}"
                res_by = r["resolved_by"] or ("system" if r["status"] == "auto_resolved" else "pending")
                res_type = "auto" if (r["resolved_by"] and r["resolved_by"].lower() in ["system", "auto"]) or r["status"] == "auto_resolved" else "human"
                
                raw_st = (r["status"] or "pending").lower()
                if raw_st in ["resolved", "auto_resolved", "accepted", "overridden"]:
                    st = "resolved"
                elif raw_st == "escalated":
                    st = "escalated"
                else:
                    st = "pending"

                entries.append(AuditEntryResponse(
                    id=str(r["id"]),
                    workspaceId=str(workspace_id),
                    timestamp=str(r["timestamp"]),
                    entityName=str(r["entityName"]),
                    summary=str(exp),
                    resolution=res_type,
                    resolvedBy=str(res_by),
                    status=st
                ))
            return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

