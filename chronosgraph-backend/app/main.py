import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import engine, Base
from app.graph.neo4j_client import neo4j_client
from app.graph.schema import apply_schema

from app.auth.router import router as auth_router
from app.workspaces.router import router as workspaces_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Database Setup
    logger.info("Initializing Postgres tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    logger.info("Connecting to Neo4j...")
    await neo4j_client.connect()
    
    logger.info("Applying Neo4j schema constraints...")
    await apply_schema()
    
    yield
    
    # Shutdown
    logger.info("Disconnecting from Neo4j...")
    await neo4j_client.close()
    
    logger.info("Closing Postgres engine...")
    await engine.dispose()


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ChronosGraph API",
    description="Multi-agent temporal RAG system with explicit conflict detection.",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware to allow requests from the Lovable frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

from app.ingestion.router import router as ingestion_router
from app.resolution.router import router as resolution_router
from app.conflicts.router import router as conflicts_router
from app.chat.router import router as chat_router

app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(ingestion_router)
app.include_router(resolution_router)
app.include_router(conflicts_router)
app.include_router(chat_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
