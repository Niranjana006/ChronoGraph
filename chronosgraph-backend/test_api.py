import httpx
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(base_url=base_url) as client:
        # 1. Check health/docs
        resp = await client.get("/health")
        logger.info(f"Health check: {resp.status_code} {resp.text}")
        assert resp.status_code == 200

        # 2. Signup
        signup_data = {
            "email": "test@example.com",
            "password": "testpassword",
            "name": "Test User"
        }
        resp = await client.post("/auth/signup", json=signup_data)
        logger.info(f"Signup: {resp.status_code} {resp.text}")
        assert resp.status_code == 201
        
        # 3. Login
        login_data = {
            "username": "test@example.com",
            "password": "testpassword"
        }
        resp = await client.post("/auth/login", data=login_data)
        logger.info(f"Login: {resp.status_code} {resp.text}")
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        
        # 4. Create Workspace (Positive)
        headers = {"Authorization": f"Bearer {token}"}
        ws_data = {"name": "Test Workspace"}
        resp = await client.post("/workspaces", json=ws_data, headers=headers)
        logger.info(f"Create Workspace: {resp.status_code} {resp.text}")
        assert resp.status_code == 201

        # 5. Create Workspace (Negative - No Token)
        resp = await client.post("/workspaces", json=ws_data)
        logger.info(f"Create Workspace (No Token): {resp.status_code} {resp.text}")
        assert resp.status_code == 401

        # 6. Create Workspace (Negative - Malformed Token)
        bad_headers = {"Authorization": "Bearer not.a.valid.token"}
        resp = await client.post("/workspaces", json=ws_data, headers=bad_headers)
        logger.info(f"Create Workspace (Bad Token): {resp.status_code} {resp.text}")
        assert resp.status_code == 401
        
        logger.info("All tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
