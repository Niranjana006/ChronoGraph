import asyncio
import logging
from celery import Celery
from openai import RateLimitError

from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Celery app
# Note: we use redis as both the broker and result backend
celery_app = Celery(
    "chronosgraph_worker",
    broker=settings.redis_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Standard configuration to prevent workers from picking up too many tasks at once
    worker_prefetch_multiplier=1,
)

# Example base task structure demonstrating how we handle persistent 429s
@celery_app.task(bind=True, max_retries=10)
def process_extraction(self, document_chunk: str):
    """
    Example extraction task. In Phase 2, this will call the async LLM client.
    Because Celery tasks are synchronous by default in this setup, we use asyncio.run
    to call the async LLM client.
    """
    try:
        # In a real scenario, this imports the LLM client and runs it:
        # from app.llm.client import generate_completion
        # result = asyncio.run(generate_completion("System prompt", document_chunk))
        
        logger.info("Processing document chunk...")
        return {"status": "success"}

    except RateLimitError as exc:
        # If tenacity exhausted all its internal retries and we still got a 429,
        # we fall back to Celery's task requeueing with a longer countdown (e.g., 60 seconds).
        logger.error(f"Persistent RateLimitError encountered. Requeuing task in 60s.")
        raise self.retry(exc=exc, countdown=60)
        
    except Exception as exc:
        logger.error(f"Unexpected error in extraction: {exc}")
        # Could mark document as failed here in Phase 2
        raise
