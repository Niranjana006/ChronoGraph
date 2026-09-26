from pydantic import BaseModel
from datetime import datetime

class DocumentResponse(BaseModel):
    id: int
    workspace_id: int
    filename: str
    content_hash: str
    status: str
    current_stage: str
    created_at: datetime

    class Config:
        from_attributes = True
