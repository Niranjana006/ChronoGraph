import asyncio
import logging
logging.basicConfig(level=logging.INFO)
from evaluation.chronos_runner import setup_chronos_workspace
from app.database import AsyncSessionLocal
from app.graph.neo4j_client import neo4j_client

async def run():
    await neo4j_client.connect()
    async with AsyncSessionLocal() as db:
        ws_id = await setup_chronos_workspace(db, 'doc1', 'doc2')
        print('Workspace ID:', ws_id)
        
asyncio.run(run())
