import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
load_dotenv()
models = ['llama3-70b-8192', 'mixtral-8x7b-32768', 'gemma2-9b-it', 'llama-3.3-70b-versatile']
for m in models:
    try:
        llm = ChatOpenAI(model=m, api_key=os.getenv('LLM_API_KEY'), base_url='https://api.groq.com/openai/v1', max_retries=1)
        res = llm.invoke('hello')
        print(f'{m}: SUCCESS')
    except Exception as e:
        print(f'{m}: FAILED ({e})')
