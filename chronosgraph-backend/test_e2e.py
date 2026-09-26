import asyncio
import httpx
import logging
import time
from reportlab.pdfgen import canvas
import os

from app.database import AsyncSessionLocal, engine
from app.graph.neo4j_client import neo4j_client
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000"

def create_pdf(filename: str, content: str):
    c = canvas.Canvas(filename)
    c.drawString(100, 750, content)
    c.save()
    return filename

async def main():
    logger.info("Initializing E2E test for Phase 4...")
    
    # 1. Create test PDFs
    pdf1 = create_pdf("test_doc1.pdf", "Alice became CEO of Acme Corp in 2020.")
    pdf2 = create_pdf("test_doc2.pdf", "Bob became CEO of Acme Corp in 2021.")
    from app.auth.jwt_handler import create_access_token, get_password_hash
    token = create_access_token({"sub": "test_user"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Setup DB and Workspace
    workspace_id = 998
    async with AsyncSessionLocal() as db:
        await db.execute(text("INSERT INTO users (email, password_hash, name, role) VALUES ('test_user', 'hash', 'Test', 'analyst') ON CONFLICT DO NOTHING"))
        await db.commit()
    async with httpx.AsyncClient(headers=headers) as client:
        # Create workspace via API
        res = await client.post(f"{API_URL}/workspaces", json={"name": "Test E2E Workspace"})
        if res.status_code not in (200, 201):
            logger.error(f"Failed to create workspace: {res.text}")
            return
        workspace_id = res.json()["id"]
        logger.info(f"Created workspace {workspace_id}")

    # 3. Upload PDFs
    async with httpx.AsyncClient(headers=headers) as client:
        # Upload doc 1
        with open(pdf1, "rb") as f:
            res1 = await client.post(f"{API_URL}/workspaces/{workspace_id}/documents", files={"file": ("test_doc1.pdf", f, "application/pdf")})
        doc1_id = res1.json()["id"]
        logger.info(f"Uploaded doc1: {doc1_id}")
        
        # Upload doc 2
        with open(pdf2, "rb") as f:
            res2 = await client.post(f"{API_URL}/workspaces/{workspace_id}/documents", files={"file": ("test_doc2.pdf", f, "application/pdf")})
        doc2_id = res2.json()["id"]
        logger.info(f"Uploaded doc2: {doc2_id}")
        
        # 4. Wait for processing and auto-chaining
        logger.info("Waiting for ingestion pipeline, resolution, and audit to finish (giving it 30s)...")
        await asyncio.sleep(30)
        
        # 5. Check Neo4j for CONTRADICTS edges
        logger.info("Querying Neo4j for CONTRADICTS edges...")
        await neo4j_client.connect()
        query = f"""
        MATCH (f1:Fact {{workspace_id: {workspace_id}}})-[c:CONTRADICTS]-(f2:Fact {{workspace_id: {workspace_id}}})
        MATCH (f1)-[:SUBJECT]->(s:Entity)
        MATCH (f1)-[:OBJECT]->(o1:Entity)
        MATCH (f2)-[:OBJECT]->(o2:Entity)
        WHERE f1.id < f2.id
        RETURN f1.evidence AS ev1, f2.evidence AS ev2, o1.name AS obj1, o2.name AS obj2,
               c.status AS status, c.confidence AS confidence, c.explanation AS explanation
        """
        async with neo4j_client.driver.session() as session:
            result = await session.run(query)
            edges = await result.data()
            
        logger.info(f"Found {len(edges)} CONTRADICTS edges.")
        for edge in edges:
            logger.info("====================================")
            logger.info(f"Fact 1 (-> {edge['obj1']}): {edge['ev1']}")
            logger.info(f"Fact 2 (-> {edge['obj2']}): {edge['ev2']}")
            logger.info(f"Status: {edge['status']}")
            logger.info(f"Confidence: {edge['confidence']}")
            logger.info(f"Explanation: {edge['explanation']}")
            logger.info("====================================")
            
        if len(edges) == 1:
            logger.info("E2E Test PASSED!")
        else:
            logger.error("E2E Test FAILED!")
            
    # Cleanup
    os.remove(pdf1)
    os.remove(pdf2)
    await engine.dispose()
    await neo4j_client.close()

if __name__ == "__main__":
    asyncio.run(main())
