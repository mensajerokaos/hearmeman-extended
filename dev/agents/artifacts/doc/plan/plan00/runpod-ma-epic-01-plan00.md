---
task: runpod-ma-epic-01 (PostgreSQL + File System Support)
agent: hc (headless claude)
model: claude-opus-4-5-20251101
timestamp: 2026-01-20T15:30:00Z
status: completed
version: 2.0-minimal
---

# runpod-ma-epic-01: PostgreSQL + File System Support

## Overview

Add persistent storage to media-analysis-api using existing PostgreSQL (af-postgres-1) and simple file system directories. Five tasks: schema creation, database models, file storage directories, API integration, and Docker network configuration.

---

## Child Tasks

### ma-21: Create Database Schema

**Execute on devmaster:**

```bash
ssh devmaster 'docker exec af-postgres-1 psql -U n8n -d af-memory' << 'EOF'
CREATE TABLE IF NOT EXISTS media_analysis_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    media_url TEXT NOT NULL,
    prompt TEXT NOT NULL,
    media_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    model_used VARCHAR(100),
    latency_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS media_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES media_analysis_requests(id) ON DELETE CASCADE,
    result_text TEXT NOT NULL,
    model_used VARCHAR(100) NOT NULL,
    prompt_used TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    latency_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS media_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_path TEXT,
    storage_path TEXT NOT NULL,
    size_bytes BIGINT,
    mime_type VARCHAR(100),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS contact_sheets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES media_analysis_requests(id) ON DELETE CASCADE,
    storage_path TEXT NOT NULL,
    frames_count INTEGER NOT NULL,
    grid_layout VARCHAR(20) DEFAULT '2x3',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_requests_status ON media_analysis_requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_created ON media_analysis_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_results_request ON media_analysis_results(request_id);
CREATE INDEX IF NOT EXISTS idx_files_uploaded ON media_files(uploaded_at DESC);
EOF
```

**Verify:**
```bash
ssh devmaster 'docker exec af-postgres-1 psql -U n8n -d af-memory -c "\dt media_*"'
```

---

### ma-22: Create Database Models

**Create directory:**
```bash
ssh devmaster 'mkdir -p /opt/services/media-analysis/api/models'
```

**File 1: api/models/__init__.py**
```python
from .database import get_db_pool, close_db_pool
from .schemas import AnalysisRequest, AnalysisResult, MediaFile, ContactSheet
```

**File 2: api/models/database.py**
```python
import asyncpg
import os
from contextlib import asynccontextmanager

_pool = None

async def get_db_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=os.getenv("DB_HOST", "af-postgres-1"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME", "af-memory"),
            user=os.getenv("DB_USER", "n8n"),
            password=os.getenv("DB_PASSWORD"),
            min_size=2,
            max_size=10
        )
    return _pool

async def close_db_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

@asynccontextmanager
async def get_connection():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        yield conn
```

**File 3: api/models/schemas.py**
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class AnalysisRequestCreate(BaseModel):
    media_url: str
    prompt: str
    media_type: str  # audio, video, document

class AnalysisRequest(BaseModel):
    id: UUID
    media_url: str
    prompt: str
    media_type: str
    status: str
    model_used: Optional[str] = None
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class AnalysisResult(BaseModel):
    id: UUID
    request_id: UUID
    result_text: str
    model_used: str
    prompt_used: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    latency_ms: Optional[int] = None
    created_at: datetime

class MediaFile(BaseModel):
    id: UUID
    filename: str
    storage_path: str
    size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_at: datetime

class ContactSheet(BaseModel):
    id: UUID
    request_id: UUID
    storage_path: str
    frames_count: int
    grid_layout: str
    created_at: datetime
```

**Add asyncpg to requirements.txt:**
```bash
ssh devmaster 'echo "asyncpg>=0.29.0" >> /opt/services/media-analysis/requirements.txt'
```

---

### ma-23: File Storage

**Execute on devmaster:**
```bash
ssh devmaster 'mkdir -p /opt/services/media-analysis/storage/{uploads,outputs,temp} && chmod 755 /opt/services/media-analysis/storage/*'
```

**Verify:**
```bash
ssh devmaster 'ls -la /opt/services/media-analysis/storage/'
```

---

### ma-24: API Integration

**Add to main.py (startup/shutdown hooks):**
```python
from api.models.database import get_db_pool, close_db_pool

@app.on_event("startup")
async def startup():
    await get_db_pool()

@app.on_event("shutdown")
async def shutdown():
    await close_db_pool()
```

**Add to analyze endpoint (before processing):**
```python
from api.models.database import get_connection

async with get_connection() as conn:
    request_id = await conn.fetchval('''
        INSERT INTO media_analysis_requests (media_url, prompt, media_type, status)
        VALUES ($1, $2, $3, 'processing')
        RETURNING id
    ''', media_url, prompt, media_type)
```

**Add after processing completes:**
```python
async with get_connection() as conn:
    await conn.execute('''
        UPDATE media_analysis_requests
        SET status = 'completed', model_used = $1, latency_ms = $2, completed_at = NOW()
        WHERE id = $3
    ''', model_used, latency_ms, request_id)

    await conn.execute('''
        INSERT INTO media_analysis_results (request_id, result_text, model_used, latency_ms)
        VALUES ($1, $2, $3, $4)
    ''', request_id, result_text, model_used, latency_ms)
```

---

### ma-25: Docker Network

**Update /opt/services/media-analysis/docker-compose.yml:**
```yaml
networks:
  default:
    name: af-network
    external: true
```

**Add DB_PASSWORD to config/.env:**
```bash
ssh devmaster 'echo "DB_PASSWORD=89wdPtUBK4pn6kDPQcaM" >> /opt/services/media-analysis/config/.env'
```

**Rebuild and restart:**
```bash
ssh devmaster 'cd /opt/services/media-analysis && docker compose down && docker compose up -d --build'
```

---

## Verification

```bash
# 1. Check tables exist
ssh devmaster 'docker exec af-postgres-1 psql -U n8n -d af-memory -c "\dt media_*"'

# 2. Check container healthy
ssh devmaster 'docker ps --filter name=media-analysis'

# 3. Test health endpoint
ssh devmaster 'curl -s http://localhost:8050/health | jq .'

# 4. Test analysis with DB write
ssh devmaster 'curl -s -X POST http://localhost:8050/api/media/analyze \
  -H "Content-Type: application/json" \
  -d "{\"media_type\": \"document\", \"media_url\": \"https://example.com/test.jpg\", \"prompt\": \"describe\"}"'

# 5. Check DB for record
ssh devmaster 'docker exec af-postgres-1 psql -U n8n -d af-memory -c "SELECT id, status, model_used FROM media_analysis_requests ORDER BY created_at DESC LIMIT 1"'
```

---

## Summary

| Task | Action | Files |
|------|--------|-------|
| ma-21 | Execute SQL | None (direct psql) |
| ma-22 | Create models | 3 Python files |
| ma-23 | Create dirs | 3 directories |
| ma-24 | Integrate DB | 2 files modified |
| ma-25 | Network config | docker-compose.yml, .env |

**Total new files:** 3
**Total modified files:** 4
**Estimated time:** 30-45 minutes
