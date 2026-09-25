from pydantic import BaseModel
from datetime import datetime
from typing import List

class WorkspaceCreate(BaseModel):
    name: str

class WorkspaceResponse(BaseModel):
    id: int
    name: str
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True

class ChatCreate(BaseModel):
    title: str

class ChatResponse(BaseModel):
    id: int
    workspace_id: int
    title: str
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True
