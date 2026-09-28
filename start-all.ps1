Write-Host "Starting ChronoGraph Services..." -ForegroundColor Cyan

# 1. Start Database Infrastructure
Write-Host "1. Starting Docker Database Infrastructure (Neo4j, Postgres, Redis)..." -ForegroundColor Yellow
Set-Location chronosgraph-backend
docker-compose up -d
Set-Location ..

# 2. Start Celery Worker
Write-Host "2. Starting Celery Worker (New Window)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd chronosgraph-backend; .\venv\Scripts\activate; celery -A app.worker.tasks worker --pool=solo --loglevel=info"

# 3. Start FastAPI Backend
Write-Host "3. Starting FastAPI Backend (New Window)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd chronosgraph-backend; .\venv\Scripts\activate; uvicorn app.main:app --reload --port 8000"

# 4. Start Vite Frontend
Write-Host "4. Starting Vite Frontend (New Window)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"

Write-Host "All services started! Check the new windows for their respective logs." -ForegroundColor Green
Write-Host "API will be at http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend will be at http://localhost:5173" -ForegroundColor Green
