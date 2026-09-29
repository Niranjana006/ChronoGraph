import asyncio
from app.chat.retriever import extract_query_entities
from app.llm.client import generate_completion

async def run():
    query = 'What is the budget for Q3 marketing?'
    prompt = f'User Question: {query}'
    SYSTEM_PROMPT = """You are a query analysis AI for a Knowledge Graph.
Extract the core entities from the user's question. These are typically proper nouns, companies, people, or locations.
Return a JSON object containing an array of strings called 'entities'.
If no clear entities are present, return an empty array.
"""
    response_json = await generate_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt,
        response_format={"type": "json_object"}
    )
    print('RAW LLM RESPONSE:')
    print(response_json)
    
    # Try the real function too
    res = await extract_query_entities(query)
    print('PARSED RESULT:', res)

if __name__ == "__main__":
    asyncio.run(run())
