import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000"
WORKSPACE_ID = 16 # E2E workspace ID from test_e2e.py

from app.auth.jwt_handler import create_access_token
async def test_chat():
    logger.info("Testing Chat API...")
    
    token = create_access_token({"sub": "test_user"})
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(headers=headers) as client:
        # 1. Create a chat session
        logger.info(f"Creating chat session in workspace {WORKSPACE_ID}...")
        resp = await client.post(f"{API_URL}/workspaces/{WORKSPACE_ID}/chats", json={"title": "Test Chat"})
        
        if resp.status_code not in (200, 201):
            logger.error(f"Failed to create chat: {resp.text}")
            return
            
        chat_data = resp.json()
        chat_id = chat_data["id"]
        logger.info(f"Created Chat ID: {chat_id}")
        
        # 2. Send a message
        query = "Who was the CEO of Acme Corp?"
        logger.info(f"Sending message: '{query}'")
        
        resp = await client.post(
            f"{API_URL}/workspaces/{WORKSPACE_ID}/chats/{chat_id}/messages", 
            json={"content": query},
            timeout=60.0
        )
        
        if resp.status_code != 200:
            logger.error(f"Failed to send message: {resp.text}")
            return
            
        msg_data = resp.json()
        
        logger.info("====================================")
        logger.info(f"LLM Answer:\n{msg_data['content']}")
        logger.info("====================================")
        logger.info(f"Citations:\n{msg_data.get('citations')}")
        logger.info(f"Conflicts:\n{msg_data.get('conflicts')}")
        logger.info("====================================")
        logger.info("Test Complete.")

if __name__ == "__main__":
    asyncio.run(test_chat())
