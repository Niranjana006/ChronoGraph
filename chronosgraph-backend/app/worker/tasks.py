import asyncio
import logging
from celery import shared_task
from openai import RateLimitError
from sqlalchemy.future import select

from app.worker.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.workspaces.models import Workspace # Import for foreign key resolution
from app.ingestion.models import Document
from app.ingestion.parser import extract_text_from_pdf, chunk_text
from app.llm.extractor import extract_graph_from_chunk
from app.graph.writer import write_extraction_to_graph

logger = logging.getLogger(__name__)

from app.database import AsyncSessionLocal, engine

async def run_pipeline(document_id: int, workspace_id: int, file_path: str):
    """
    Async implementation of the document processing pipeline.
    """
    await engine.dispose()
    try:
        async with AsyncSessionLocal() as db:
            # 1. Update status
            doc_result = await db.execute(select(Document).where(Document.id == document_id))
            document = doc_result.scalar_one_or_none()
            if not document:
                logger.error(f"Document {document_id} not found.")
                return
    
            # 2. Parse PDF
            try:
                raw_text = extract_text_from_pdf(file_path)
                chunks = chunk_text(raw_text)
                logger.info(f"Extracted {len(chunks)} chunks from {document.filename}")
            except Exception as e:
                logger.error(f"Failed to parse document: {e}")
                document.status = "failed"
                await db.commit()
                return
    
            # 3. Extract and Write Graph per chunk
            for chunk in chunks:
                try:
                    extraction = await extract_graph_from_chunk(chunk)
                    await write_extraction_to_graph(extraction, workspace_id, document_id, document.filename)
                except RateLimitError as e:
                    # Let this bubble up to Celery for requeue
                    raise e
                except Exception as e:
                    # Other errors shouldn't crash the whole pipeline, log and continue
                    logger.error(f"Failed to process chunk: {e}")
    
            # 4. Mark complete
            document.status = "completed"
            await db.commit()
            logger.info(f"Successfully processed document {document_id}")
            
            # Auto-chain resolution and then audit
            resolve_workspace_task.delay(workspace_id)
    finally:
        from app.graph.neo4j_client import neo4j_client
        await neo4j_client.close()
        neo4j_client.driver = None


@celery_app.task(bind=True, max_retries=10, name="app.worker.tasks.process_document")
def process_document(self, document_id: int, workspace_id: int, file_path: str):
    """
    Celery task that acts as the entrypoint for the ingestion pipeline.
    """
    logger.info(f"Starting ingestion pipeline for document {document_id}")
    
    try:
        # Run the async pipeline synchronously for Celery
        asyncio.run(run_pipeline(document_id, workspace_id, file_path))
    except RateLimitError as exc:
        logger.warning("Rate limit completely exhausted. Requeuing task in 60s.")
        # Document status remains 'processing', task gets delayed
        raise self.retry(exc=exc, countdown=60)
    except Exception as exc:
        logger.error(f"Unexpected error in process_document task: {exc}")
        # Could mark as failed here by re-running async db update if needed

@celery_app.task(bind=True, max_retries=3, name="app.worker.tasks.resolve_workspace_task")
def resolve_workspace_task(self, workspace_id: int):
    """
    Celery task to run entity resolution and temporal normalization 
    on all facts and entities in a workspace.
    """
    import asyncio
    from app.resolution.entities import resolve_entities
    from app.resolution.temporal import resolve_temporal
    
    logger.info(f"Task resolve_workspace_task received for workspace {workspace_id}")
    try:
        # Run resolution sequentially
        async def _run_resolution():
            from app.graph.neo4j_client import neo4j_client
            await engine.dispose()
            if neo4j_client.driver is None:
                await neo4j_client.connect()
            try:
                m = await resolve_entities(workspace_id)
                t = await resolve_temporal(workspace_id)
                return m, t
            finally:
                await neo4j_client.close()
                neo4j_client.driver = None
            
        merged_pairs, temporal_processed = asyncio.run(_run_resolution())
        
        # Auto-chain Consistency Swarm audit
        audit_workspace_task.delay(workspace_id)
        
        return {
            "workspace_id": workspace_id,
            "merged_pairs": len(merged_pairs),
            "temporal_processed": temporal_processed
        }
    except Exception as exc:
        logger.error(f"Error in resolve_workspace_task: {exc}")
        raise self.retry(exc=exc, countdown=10)

@celery_app.task(bind=True, max_retries=3, name="app.worker.tasks.audit_workspace_task")
def audit_workspace_task(self, workspace_id: int):
    """
    Celery task to run the Consistency Swarm (Conflict Detection).
    """
    import asyncio
    from app.conflicts.auditor import audit_workspace
    
    logger.info(f"Task audit_workspace_task received for workspace {workspace_id}")
    try:
        async def _run_audit():
            from app.graph.neo4j_client import neo4j_client
            await engine.dispose()
            if neo4j_client.driver is None:
                await neo4j_client.connect()
            try:
                c = await audit_workspace(workspace_id)
                return c
            finally:
                await neo4j_client.close()
                neo4j_client.driver = None
            
        conflicts = asyncio.run(_run_audit())
        
        return {
            "workspace_id": workspace_id,
            "conflicts_found": conflicts
        }
    except RateLimitError as exc:
        logger.warning("Rate limit completely exhausted. Requeuing task in 60s.")
        raise self.retry(exc=exc, countdown=60)
    except Exception as exc:
        logger.error(f"Error in audit_workspace_task: {exc}")
        raise self.retry(exc=exc, countdown=10)
