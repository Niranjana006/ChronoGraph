from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.auth.models import User
from app.auth.dependencies import get_current_user
from app.workspaces.schemas import WorkspaceCreate, WorkspaceResponse, ChatCreate, ChatResponse
import app.workspaces.service as ws_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

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
