# Database Integration with API Endpoints - Implementation Plan

## Executive Summary
Integrate PostgreSQL database operations with API endpoints for media analysis workflows. Create CRUD operations for media items, analysis results, and job management.

## Phase 1: API Endpoint Implementation

### Step 1.1: Create Media Items Endpoints
- File: /opt/services/media-analysis/src/api/endpoints/media.py
- Code:
```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.connection import get_pool, Pool
from db.models import MediaItem

router = APIRouter(prefix="/media", tags=["media"])

@router.get("/")
async def list_media(limit: int = 100, pool: Pool = Depends(get_pool)):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM media_items ORDER BY created_at DESC LIMIT $1", limit)
        return [dict(row) for row in rows]

@router.post("/")
async def create_media(item: dict, pool: Pool = Depends(get_pool)):
    async with pool.acquire() as conn:
        result = await conn.fetchrow("""
            INSERT INTO media_items (source_url, source_type, local_path, file_size, mime_type)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
        """, item["source_url"], item["source_type"], item.get("local_path"), item.get("file_size"), item.get("mime_type"))
        return dict(result)
```

### Step 1.2: Create Analysis Endpoints
- File: /opt/services/media-analysis/src/api/endpoints/analysis.py
- Code:
```python
from fastapi import APIRouter, HTTPException
from datetime import datetime

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.get("/results/{media_item_id}")
async def get_analysis_results(media_item_id: str):
    # Query analysis_results table
    pass

@router.post("/transcribe")
async def transcribe_media(media_item_id: str, provider: str = "groq"):
    # Insert into analysis_results with type='transcription'
    pass

@router.post("/vision")
async def analyze_vision(media_item_id: str, provider: str = "qwen3-vl"):
    # Insert into analysis_results with type='vision'
    pass
```

## Phase 2: Service Layer

### Step 2.1: Create Analysis Service
- File: /opt/services/media-analysis/src/services/analysis_service.py
- Code:
```python
class AnalysisService:
    async def submit_transcription(self, media_id: str, provider: str) -> str:
        job_id = await self._create_job(media_id, "transcription", provider)
        # Queue job for async processing
        return job_id
    
    async def get_result(self, job_id: str) -> dict:
        # Query analysis_results table
        pass
```

## Phase 3: Job Queue Integration

### Step 3.1: Create Job Worker
- File: /opt/services/media-analysis/src/workers/analysis_worker.py
- Code:
```python
import asyncio
from db.connection import get_pool

class AnalysisWorker:
    async def process_queue(self):
        pool = await get_pool()
        while True:
            async with pool.acquire() as conn:
                jobs = await conn.fetch("""
                    SELECT * FROM processing_jobs 
                    WHERE status = 'queued' 
                    ORDER BY priority DESC 
                    LIMIT 1
                """)
                for job in jobs:
                    await self._process_job(job)
            await asyncio.sleep(5)
```

## Phase 4: Testing

### Step 4.1: Test API Endpoints
- Bash: `cd /opt/services/media-analysis && python -m pytest tests/api/test_media.py -v`
- Expected: All tests pass

### Step 4.2: Integration Test
- Bash: `curl -X POST http://localhost:8050/media/ -H "Content-Type: application/json" -d '{"source_url": "https://youtube.com/watch?v=abc", "source_type": "youtube"}'`
- Expected: JSON response with media item ID

## Rollback
- Bash: `psql -h af-postgres-1 -U n8n -d af-memory -c "DELETE FROM media_items WHERE source_url LIKE '%test%'"`
- Verification: Test data removed

## Bead Structure
| Phase | Bead Title | Parallel With | Blocked By |
|-------|------------|---------------|------------|
| 1 | [PRD] ma-24 - API Endpoints | - | - |
| 2 | [PRD] ma-24 - Service Layer | p1 | - |
| 3 | [PRD] ma-24 - Job Queue | p2 | - |
| 4 | [PRD] ma-24 - Testing | p3 | - |
