from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.future import select

from app.database import get_db, AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from app.workspaces.models import Chat, ChatMessage, Workspace
from app.chat.retriever import retrieve_context
from app.chat.generator import generate_response
from app.auth.dependencies import get_current_user
from app.auth.models import User

router = APIRouter(prefix="/workspaces/{workspace_id}/chats", tags=["chat"])

class MessageCreateRequest(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    citations: Optional[List[Dict[str, Any]]] = None
    conflicts: Optional[List[Dict[str, Any]]] = None
    created_at: str

@router.post("/{chat_id}/messages", response_model=MessageResponse)
async def send_message(
    workspace_id: int, 
    chat_id: int, 
    req: MessageCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify chat belongs to workspace
    result = await db.execute(select(Chat).where(Chat.id == chat_id, Chat.workspace_id == workspace_id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    # 1. Save User Message
    user_msg = ChatMessage(chat_id=chat_id, role="user", content=req.content)
    db.add(user_msg)
    await db.commit()
    
    # 2. RAG Pipeline
    try:
        retrieved_data = await retrieve_context(workspace_id, req.content)
        llm_response = await generate_response(req.content, retrieved_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {e}")
        
    # 3. Save Assistant Message
    assistant_msg = ChatMessage(
        chat_id=chat_id, 
        role="assistant", 
        content=llm_response.get("answer", ""),
        citations_json=llm_response.get("citations", []),
        conflict_flags_json=llm_response.get("conflicts", [])
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)
    
    return {
        "id": assistant_msg.id,
        "role": assistant_msg.role,
        "content": assistant_msg.content,
        "citations": assistant_msg.citations_json,
        "conflicts": assistant_msg.conflict_flags_json,
        "created_at": str(assistant_msg.created_at)
    }


