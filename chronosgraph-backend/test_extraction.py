import asyncio
import logging
logging.basicConfig(level=logging.INFO)
from app.llm.extractor import extract_graph_from_chunk

async def run():
    doc1 = 'Alice became CEO of Acme Corp in 2020.'
    ext = await extract_graph_from_chunk(doc1)
    print('Entities:', ext.entities)
    print('Facts:', ext.facts)
        
asyncio.run(run())
