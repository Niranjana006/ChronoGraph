from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.workspaces.models import Workspace, WorkspaceMember, Chat
from app.auth.models import User

async def check_workspace_access(db: AsyncSession, workspace_id: int, user_id: int, required_roles: list[str] = None):
    """Verify user is a member of the workspace, optionally with a specific role."""
    result = await db.execute(
        select(WorkspaceMember)
        .filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id)
    )
    member = result.scalars().first()
    
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found or access denied")
        
    if required_roles and member.role_in_workspace not in required_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient workspace role")
        
    return member

async def create_workspace(db: AsyncSession, name: str, current_user: User):
    new_workspace = Workspace(name=name, created_by=current_user.id)
    db.add(new_workspace)
    await db.flush() # get the ID
    
    # Creator is admin of the workspace
    member = WorkspaceMember(
        workspace_id=new_workspace.id,
        user_id=current_user.id,
        role_in_workspace="admin"
    )
    db.add(member)
    await db.commit()
    await db.refresh(new_workspace)
    return new_workspace

async def get_user_workspaces(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .filter(WorkspaceMember.user_id == user_id)
    )
    return result.scalars().all()

async def create_chat(db: AsyncSession, workspace_id: int, title: str, current_user: User):
    # Ensure they have access to the workspace
    await check_workspace_access(db, workspace_id, current_user.id)
    
    new_chat = Chat(
        workspace_id=workspace_id,
        title=title,
        created_by=current_user.id
    )
    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)
    return new_chat

async def get_workspace_chats(db: AsyncSession, workspace_id: int, current_user: User):
    # Ensure access
    await check_workspace_access(db, workspace_id, current_user.id)
    
    result = await db.execute(
        select(Chat).filter(Chat.workspace_id == workspace_id)
    )
    return result.scalars().all()
