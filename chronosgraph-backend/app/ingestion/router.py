import os
import hashlib
from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.auth.models import User
from app.auth.dependencies import get_current_user
from app.workspaces.models import WorkspaceMember
from app.ingestion.models import Document
from app.ingestion.schemas import DocumentResponse

# We will import the Celery task later, using a string name for now or direct import if ready
# from app.worker.tasks import process_document

router = APIRouter(prefix="/workspaces/{workspace_id}/documents", tags=["ingestion"])

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    workspace_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    # 1. Workspace access check
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
        
    # 2. Read and hash file for deduplication
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Check if this exact file already exists in this workspace
    doc_result = await db.execute(
        select(Document).where(
            Document.workspace_id == workspace_id,
            Document.content_hash == file_hash
        )
    )
    existing_doc = doc_result.scalar_one_or_none()
    
    if existing_doc:
        # If it's already there, just return it. 
        # (Could optionally check status and restart if failed)
        return existing_doc
        
    # 3. Save file locally (for the worker to pick up)
    file_path = os.path.join(UPLOAD_DIR, f"{file_hash}.pdf")
    with open(file_path, "wb") as f:
        f.write(content)
        
    # 4. Create Postgres Document Record
    new_doc = Document(
        workspace_id=workspace_id,
        filename=file.filename,
        content_hash=file_hash,
        status="processing"
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    # 5. Kick off Celery Task
    from app.worker.tasks import process_document
    # Pass the local file path and IDs to the worker
    process_document.delay(new_doc.id, workspace_id, file_path)
    
    return new_doc

from typing import List

@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Workspace access check
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
        
    doc_result = await db.execute(
        select(Document).where(Document.workspace_id == workspace_id)
    )
    return doc_result.scalars().all()
