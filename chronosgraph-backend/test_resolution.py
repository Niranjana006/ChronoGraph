import httpx
import os
import time

BASE_URL = "http://localhost:8000"

# Using static filenames so tests are repeatable
FILES = [
    ("test_doc_1.pdf", "John F. Kennedy was president of the United States from 1961 until 1963."),
    ("test_doc_2.pdf", "JFK negotiated with the USSR during the Cuban Missile Crisis."),
    ("test_doc_3.pdf", "Apple the company released a new phone recently."),
    ("test_doc_4.pdf", "He ate a green apple for lunch yesterday.")
]

def create_dummy_pdf(filename, text):
    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), text)
        doc.save(filename)
        doc.close()
    except Exception as e:
        print(f"PyMuPDF not available to generate PDF: {e}")

def main():
    print("Generating test PDFs...")
    for filename, text in FILES:
        create_dummy_pdf(filename, text)

    with httpx.Client(base_url=BASE_URL, timeout=120) as client:
        email = f"tester_{int(time.time())}@test.com"
        # Register user
        resp_signup = client.post("/auth/signup", json={"email": email, "password": "password", "name": "Tester"})
        if resp_signup.status_code != 201:
            print("Signup failed!", resp_signup.status_code, resp_signup.text)
            return
        
        # Login
        resp = client.post("/auth/login", data={"username": email, "password": "password"})
        if resp.status_code != 200:
            print("Login failed!", resp.status_code, resp.text)
            return
            
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create workspace
        resp = client.post("/workspaces", json={"name": "Resolution Test Workspace"}, headers=headers)
        if resp.status_code != 200 and resp.status_code != 201:
            print("Workspace creation failed!", resp.status_code, resp.text)
            return
        workspace_id = resp.json()["id"]
        
        print(f"Workspace created: {workspace_id}")
        
        # Upload all docs
        doc_ids = []
        for filename, _ in FILES:
            with open(filename, "rb") as f:
                print(f"Uploading {filename}...")
                resp = client.post(f"/workspaces/{workspace_id}/documents", files={"file": f}, headers=headers)
                if resp.status_code == 201:
                    doc_ids.append(resp.json()["id"])
                elif resp.status_code == 200:
                    print(f"Document {filename} already exists (deduplicated).")
                else:
                    print("Upload Failed:", resp.status_code, resp.text)
                    
        print(f"Uploaded {len(doc_ids)} documents. Waiting for ingestion pipeline to finish...")
        
        # Simple polling logic to wait for extraction
        while True:
            resp = client.get(f"/workspaces/{workspace_id}/documents", headers=headers)
            if resp.status_code != 200:
                print("GET /documents failed:", resp.status_code, resp.text)
                break
                
            docs = resp.json()
            if not isinstance(docs, list):
                print("Expected a list, got:", docs)
                break
                
            all_done = True
            for doc in docs:
                if doc["id"] in doc_ids and doc["status"] != "completed":
                    all_done = False
            
            if all_done:
                break
            print("Still processing... waiting 5 seconds.", flush=True)
            time.sleep(5)
            
        print("Ingestion complete. Triggering Entity Resolution and Temporal Normalization...")
        
        resp = client.post(f"/workspaces/{workspace_id}/resolve", headers=headers)
        print("Resolve Response:", resp.status_code, resp.json())
        
        print("\n\nVerify via Neo4j Browser or worker logs!")

if __name__ == "__main__":
    main()
