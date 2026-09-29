import asyncio
import os
from langchain_openai import ChatOpenAI

async def test():
    llm = ChatOpenAI(model='llama-3.1-8b-instant', max_retries=5, base_url='https://api.groq.com/openai/v1', api_key=os.getenv('GROQ_API_KEY'))
    print(await llm.ainvoke('hello'))

asyncio.run(test())
