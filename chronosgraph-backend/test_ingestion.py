import asyncio
import httpx
import os

async def test_ingestion():
    # 1. Login to get token (using the test user created in Phase 1)
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Assuming the user already exists, let's login (OAuth2 needs form data)
        login_resp = await client.post("/auth/login", data={"username": "test@example.com", "password": "testpassword"})
        if login_resp.status_code != 200:
            print(f"Failed to login: {login_resp.status_code} {login_resp.text}")
            return
            
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get workspace ID
        ws_resp = await client.get("/workspaces", headers=headers)
        workspaces = ws_resp.json()
        if not workspaces:
            print("No workspaces found.")
            return
        workspace_id = workspaces[0]["id"]
        
        # 3. Create a dummy PDF
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "John F. Kennedy was president of the United States from 1961 until 1963.", fontsize=11)
        doc.save("test_history.pdf")
        doc.close()
        
        # 4. Upload PDF
        with open("test_history.pdf", "rb") as f:
            files = {"file": ("test_history.pdf", f, "application/pdf")}
            upload_resp = await client.post(f"/workspaces/{workspace_id}/documents", headers=headers, files=files)
            
        print("Upload Response:", upload_resp.status_code, upload_resp.json())
        
        # Cleanup
        os.remove("test_history.pdf")

if __name__ == "__main__":
    asyncio.run(test_ingestion())
