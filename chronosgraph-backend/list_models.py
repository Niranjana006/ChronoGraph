import os
import httpx

api_key = os.environ.get("LLM_API_KEY")
if not api_key:
    print("NO API KEY")
    exit(1)
    
try:
    resp = httpx.get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    if resp.status_code == 200:
        data = resp.json().get("data", [])
        models = [m["id"] for m in data]
        print("AVAILABLE MODELS:", models)
    else:
        print("ERROR:", resp.status_code, resp.text)
except Exception as e:
    print("EXCEPTION:", e)
