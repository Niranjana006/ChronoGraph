FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for psycopg2, asyncpg, etc.
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# We'll rely on docker-compose volume mounting to map our local code into /app
# CMD will also be provided in docker-compose.yml for hot reloading
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
