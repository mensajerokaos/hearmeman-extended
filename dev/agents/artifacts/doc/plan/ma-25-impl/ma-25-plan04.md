# Docker Compose Update - Implementation Plan

## Executive Summary
Update docker-compose.yml to include PostgreSQL service and configure media-analysis-api to use the external database. Target: af-postgres-1:5432.

## Phase 1: Docker Compose Configuration

### Step 1.1: Add PostgreSQL Service
- File: /opt/services/media-analysis/docker-compose.yml (update)
- Code:
```yaml
services:
  media-analysis-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8050:8050"
    environment:
      - POSTGRES_HOST=af-postgres-1
      - POSTGRES_PORT=5432
      - POSTGRES_DB=af-memory
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    depends_on:
      - redis
    volumes:
      - ./data:/opt/services/media-analysis/data
      - ./uploads:/opt/services/media-analysis/uploads

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### Step 1.2: Create Environment Template
- File: /opt/services/media-analysis/.env.example
- Code:
```bash
# Database Configuration
POSTGRES_HOST=af-postgres-1
POSTGRES_PORT=5432
POSTGRES_DB=af-memory
POSTGRES_USER=n8n
POSTGRES_PASSWORD=your_password_here

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Application Configuration
MEDIA_OUTPUT_BASE=/opt/services/media-analysis/data/outputs
```

## Phase 2: Database Initialization

### Step 2.1: Create Initialization Script
- File: /opt/services/media-analysis/scripts/init_db.sh
- Code:
```bash
#!/bin/bash
set -e

echo "Initializing database schema..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f database/migrations/001_initial_schema.sql

echo "Database schema initialized successfully"
```

## Phase 3: Health Checks

### Step 3.1: Add Health Check to API
- File: /opt/services/media-analysis/src/api/health.py
- Code:
```python
from fastapi import APIRouter
import asyncpg

router = APIRouter()

@router.get("/health")
async def health_check():
    try:
        pool = await asyncpg.connect(
            host="af-postgres-1",
            port=5432,
            database="af-memory",
            user="n8n",
            password="secret"
        )
        await pool.fetch("SELECT 1")
        await pool.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
```

## Phase 4: Testing

### Step 4.1: Build and Test Containers
- Bash: `cd /opt/services/media-analysis && docker compose build`
- Expected: Build completes without errors

### Step 4.2: Verify Database Connection
- Bash: `docker compose up -d && sleep 10 && curl http://localhost:8050/health`
- Expected: {"status": "healthy", "database": "connected"}

## Rollback
- Bash: `docker compose down && docker volume rm media-analysis_redis_data`
- Verification: Containers stopped and removed

## Bead Structure
| Phase | Bead Title | Parallel With | Blocked By |
|-------|------------|---------------|------------|
| 1 | [PRD] ma-25 - Docker Compose | - | - |
| 2 | [PRD] ma-25 - Environment Config | p1 | - |
| 3 | [PRD] ma-25 - Health Checks | p2 | - |
| 4 | [PRD] ma-25 - Testing | p3 | - |
