import requests
import time
import json
import uuid
import subprocess

API_URL = "http://localhost:8000"

def print_header(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

print_header("Layer 1 - Infrastructure")
print("1. docker-compose ps")
print(run_cmd("docker ps --format 'table {{.Names}}\t{{.Status}}'"))

print("2. docker-compose logs api")
print(run_cmd("docker logs --tail 20 chronosgraph-backend-api-1"))

print("3. docker-compose logs worker")
print(run_cmd("docker logs --tail 20 chronosgraph-backend-worker-1"))

print("5. GET /health")
try:
    r = requests.get(f"{API_URL}/health")
    print(f"Status: {r.status_code}, Body: {r.text}")
except Exception as e:
    print(f"Failed: {e}")

print("6. GET /docs")
try:
    r = requests.get(f"{API_URL}/openapi.json")
    print(f"Status: {r.status_code}, Keys: {list(r.json().get('paths', {}).keys())[:5]}...")
except Exception as e:
    print(f"Failed: {e}")

print_header("Layer 2 - Auth")
test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
test_pwd = "Password123!"

print("7. POST /auth/signup (new)")
r = requests.post(f"{API_URL}/auth/signup", json={"email": test_email, "password": test_pwd, "name": "Test User"})
print(f"Status: {r.status_code}")

print("8. POST /auth/signup (duplicate)")
r = requests.post(f"{API_URL}/auth/signup", json={"email": test_email, "password": test_pwd, "name": "Test User"})
print(f"Status: {r.status_code}")

print("9. POST /auth/login (correct)")
r = requests.post(f"{API_URL}/auth/login", data={"username": test_email, "password": test_pwd})
print(f"Status: {r.status_code}")
token = r.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

print("10. POST /auth/login (wrong)")
r = requests.post(f"{API_URL}/auth/login", data={"username": test_email, "password": "wrongpassword"})
print(f"Status: {r.status_code}")

print_header("Layer 2 - Workspaces")
print("12. POST /workspaces")
r = requests.post(f"{API_URL}/workspaces", json={"name": "Test Workspace"}, headers=headers)
print(f"Status: {r.status_code}")
workspace_id = r.json().get("id")
print(f"Workspace ID: {workspace_id}")

print("13. GET /workspaces")
r = requests.get(f"{API_URL}/workspaces", headers=headers)
print(f"Status: {r.status_code}, Count: {len(r.json())}")

print("14. Wrong workspace ID")
r = requests.get(f"{API_URL}/workspaces/999999/documents", headers=headers)
print(f"Status: {r.status_code}")

print_header("Layer 2 - Ingestion")
print("15. POST /workspaces/{id}/documents")

minimal_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n5 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(Apple makes iphones) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000219 00000 n \n0000000307 00000 n \ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n402\n%%EOF"
with open("test_upload.pdf", "wb") as f:
    f.write(minimal_pdf)
files = {'file': ('test_upload.pdf', open('test_upload.pdf', 'rb'), 'application/pdf')}
r = requests.post(f"{API_URL}/workspaces/{workspace_id}/documents", files=files, headers=headers)
print(f"Status: {r.status_code}, Response: {r.json()}")

print("16. GET /workspaces/{id}/documents (polling)")
for i in range(3):
    time.sleep(2)
    r = requests.get(f"{API_URL}/workspaces/{workspace_id}/documents", headers=headers)
    docs = r.json()
    if docs:
        print(f"Poll {i+1}: Status={docs[0].get('status')}, Stage={docs[0].get('current_stage')}")

print("17. Upload exact same file (dedup)")
files = {'file': ('test_upload.pdf', open('test_upload.pdf', 'rb'), 'application/pdf')}
r = requests.post(f"{API_URL}/workspaces/{workspace_id}/documents", files=files, headers=headers)
print(f"Status: {r.status_code}, Response: {r.json()}")

print_header("Layer 2 - Graph state")
print("We can't easily query neo4j directly from python without installing drivers, but we can check the graph endpoint we just built!")
r = requests.get(f"{API_URL}/workspaces/{workspace_id}/graph", headers=headers)
if r.status_code == 200:
    print(f"Status: {r.status_code}, Nodes: {len(r.json().get('nodes', []))}")
else:
    print(f"Status: {r.status_code}, Error: {r.text}")

print_header("Layer 2 - Chat")
print("24. POST /workspaces/{id}/chats")
r = requests.post(f"{API_URL}/workspaces/{workspace_id}/chats", json={"title": "Test Chat"}, headers=headers)
print(f"Status: {r.status_code}")
chat_id = r.json().get("id")

if chat_id:
    print("25. POST /workspaces/{id}/chats/{chat_id}/messages")
    r = requests.post(f"{API_URL}/workspaces/{workspace_id}/chats/{chat_id}/messages", json={"content": "What does Apple make?"}, headers=headers)
    print(f"Status: {r.status_code}, Response contains answer: {'answer' in r.json()}")
    
    print("27. GET /workspaces/{id}/chats")
    r = requests.get(f"{API_URL}/workspaces/{workspace_id}/chats", headers=headers)
    print(f"Status: {r.status_code}, Count: {len(r.json())}")

print_header("Layer 2 - Auth enforcement")
print("29. No auth header")
r = requests.get(f"{API_URL}/workspaces")
print(f"Status: {r.status_code}")

print("30. Garbage token")
r = requests.get(f"{API_URL}/workspaces", headers={"Authorization": "Bearer GARBAGE"})
print(f"Status: {r.status_code}")
