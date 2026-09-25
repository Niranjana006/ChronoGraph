from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    filename = Column(String, nullable=False)
    content_hash = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="processing")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
