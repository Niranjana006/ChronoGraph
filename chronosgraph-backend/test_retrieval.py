import asyncio
import logging
logging.basicConfig(level=logging.INFO)
from app.chat.retriever import retrieve_context
from app.graph.neo4j_client import neo4j_client
from evaluation.chronos_runner import setup_chronos_workspace
from app.database import AsyncSessionLocal

async def run():
    await neo4j_client.connect()
    async with AsyncSessionLocal() as db:
        ws_id = await setup_chronos_workspace(db, 'The approved budget for Q3 marketing is ,000.', 'The Q3 marketing budget has been slashed to ,000 due to budget cuts.')
        print('Workspace ID:', ws_id)
        context = await retrieve_context(ws_id, 'What is the budget for Q3 marketing?')
        print('Context:', context)
        
asyncio.run(run())
