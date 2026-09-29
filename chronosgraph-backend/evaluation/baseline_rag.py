# evaluation/baseline_rag.py
import os
import httpx
from openai import AsyncOpenAI
from app.config import settings

async def run_baseline_rag(query: str, doc1: str, doc2: str) -> str:
    """
    Simulates a query-time-only standard RAG.
    Assumes perfect retrieval (top_k=2 pulls both documents), 
    and feeds them to the LLM as context.
    """
    client = AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url="https://api.groq.com/openai/v1",
        http_client=httpx.AsyncClient(verify=False)
    )

    system_prompt = (
        "You are a helpful AI assistant. Answer the user's question based ONLY on the provided context.\n"
        "If the context does not contain the answer, say 'I don't know'."
    )
    
    user_prompt = f"Context:\n[Document A]\n{doc1}\n\n[Document B]\n{doc2}\n\nQuestion: {query}"
    
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0
    )
    
    return response.choices[0].message.content
