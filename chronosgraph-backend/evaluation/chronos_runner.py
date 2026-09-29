# evaluation/chronos_runner.py
import asyncio
import uuid
from sqlalchemy.future import select

from app.database import AsyncSessionLocal
from app.workspaces.models import Workspace
from app.ingestion.models import Document
from app.graph.writer import write_extraction_to_graph
from app.llm.extractor import extract_graph_from_chunk
from app.worker.tasks import resolve_workspace_task, audit_workspace_task
from app.chat.retriever import retrieve_context
from app.chat.generator import generate_response
from app.graph.neo4j_client import neo4j_client
from app.auth.models import User

async def setup_chronos_workspace(db, doc1: str, doc2: str) -> int:
    """Creates a new workspace, parses both docs, and runs conflict detection."""
    # 1. Create Workspace
    ws = Workspace(name=f"Eval Workspace {uuid.uuid4().hex[:6]}")
    db.add(ws)
    await db.commit()
    await db.refresh(ws)
    workspace_id = ws.id
    
    # 2. Insert Documents
    d1 = Document(workspace_id=workspace_id, filename="doc1.txt", content_hash="1", status="completed")
    d2 = Document(workspace_id=workspace_id, filename="doc2.txt", content_hash="2", status="completed")
    db.add_all([d1, d2])
    await db.commit()
    await db.refresh(d1)
    await db.refresh(d2)
    
    # 3. Extract Graphs
    ext1 = await extract_graph_from_chunk(doc1)
    await write_extraction_to_graph(ext1, workspace_id, d1.id, "doc1.txt")
    
    ext2 = await extract_graph_from_chunk(doc2)
    await write_extraction_to_graph(ext2, workspace_id, d2.id, "doc2.txt")
    
    # 4. Resolve & Audit (Synchronous wrapper around Celery tasks logic for eval)
    from app.resolution.entities import resolve_entities
    from app.resolution.temporal import resolve_temporal
    from app.conflicts.auditor import audit_workspace
    
    # Manually run the pipeline parts that the celery workers would run
    await resolve_entities(workspace_id)
    await resolve_temporal(workspace_id)
    await audit_workspace(workspace_id)
    
    return workspace_id

async def run_chronos_rag(query: str, doc1: str, doc2: str) -> str:
    """
    Simulates the ChronosGraph flow: ingests documents, resolves entities, 
    finds conflicts, and answers the query using the conflict-aware chat endpoint.
    """
    async with AsyncSessionLocal() as db:
        workspace_id = await setup_chronos_workspace(db, doc1, doc2)
        
        # 5. Query
        retrieved_data = await retrieve_context(workspace_id, query)
        llm_response = await generate_response(query, retrieved_data)
        
        return llm_response.get("answer", "")
