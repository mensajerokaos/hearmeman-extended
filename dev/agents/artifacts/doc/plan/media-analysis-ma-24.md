---
author: $USER
model: claude-opus-4-5-20251101
date: 2026-01-20
task: Database Integration PRD for Media Analysis API
version: 1.0
---

# PRD: Media Analysis API Database Integration

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-20 | $USER | Initial PRD for database integration |

## Approvals

| Role | Name | Status | Date |
|------|------|--------|------|
| Technical Lead | [Pending] | Pending | TBD |
| Security Review | [Pending] | Pending | TBD |
| DBA Review | [Pending] | Pending | TBD |

---

# 1. Executive Summary

## Project Overview

This document specifies the database integration for the Media Analysis API at `/opt/services/media-analysis/`. The integration adds persistent storage for analysis requests using PostgreSQL with async task queue support via Celery and Redis.

## Business Value

| Value | Description |
|-------|-------------|
| **Request Tracking** | Track analysis requests across sessions and restarts |
| **Status Polling** | Enable clients to poll for long-running analysis status |
| **Audit Trail** | Maintain complete history of all analysis requests |
| **Async Processing** | Support background processing without blocking |
| **Results Persistence** | Store analysis results for later retrieval |

## Key Metrics

| Metric | Current State | Target State |
|--------|---------------|--------------|
| Endpoints | 4 (in design) | 4 (with persistence) |
| Database Tables | 0 | 1 (analysis_request) |
| New Dependencies | 0 | 5 (SQLAlchemy, Celery, Redis, Alembic, psycopg2) |
| Migration Complexity | N/A | MEDIUM |
| Test Coverage Target | 0% | 90% |
| API Latency Target | N/A | <500ms p95 |

## Scope

### In Scope

1. **Database Schema Design**
   - Create `analysis_request` table
   - Define indexes for query performance
   - Implement soft delete pattern

2. **Model Layer**
   - SQLAlchemy ORM model
   - Pydantic request/response schemas
   - Repository pattern implementation

3. **Endpoint Integration**
   - `POST /api/media/analyze` - Create request with persistence
   - `GET /api/media/status/{id}` - Query status from database
   - `DELETE /api/media/{id}` - Soft delete with timestamp
   - `GET /api/media/history` - Paginated list with filters

4. **Async Processing**
   - Celery task queue setup
   - Redis broker configuration
   - Background worker implementation

5. **Testing**
   - Unit tests (90% coverage)
   - Integration tests
   - Load testing (100 RPS)

### Out of Scope

1. Multi-tenant user authentication (re-use existing patterns)
2. Data archival/retention policy (future phase)
3. Real-time WebSocket updates (future phase)
4. Analytics/reporting dashboard (future phase)

---

# 2. Current State Analysis

## System Context

The Media Analysis API is being cloned from `cotizador-api` on devmaster to `/opt/services/media-analysis/` for isolated media analysis operations.

### Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│               media-services-network (NEW)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            media-analysis-api:8000                        │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │  │
│  │  │   Audio     │ │   Video     │ │     Document        │ │  │
│  │  │   Branch    │ │   Branch    │ │     Branch          │ │  │
│  │  │ /api/media/ │ │ /api/media/ │ │ /api/media/documents│ │  │
│  │  │   audio     │ │   video     │ │                     │ │  │
│  │  │             │ │             │ │                     │ │  │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘ │  │
│  │                        │                                   │  │
│  │              ┌─────────┴─────────┐                        │  │
│  │              │   Aggregator      │◄── NEW ENDPOINT        │  │
│  │              │ /api/media/analyze│                        │  │
│  │              └───────────────────┘                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                    │
│           ┌───────────────┼───────────────┐                   │
│           ▼               ▼               ▼                   │
│    ┌────────────┐  ┌────────────┐  ┌────────────────────┐    │
│    │  Deepgram  │  │   FFmpeg   │  │     MiniMax API    │    │
│    │   (TTS)    │  │ (Video)    │  │ (Vision + Text)    │    │
│    └────────────┘  └────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Current Database State

| Component | Status | Details |
|-----------|--------|---------|
| **Database Layer** | NONE | No persistent storage |
| **SQLAlchemy Models** | NONE | No ORM models |
| **Migration Tool** | NONE | No Alembic setup |
| **Connection Pool** | NONE | No database configuration |

### Endpoints to Implement

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/api/media/analyze` | POST | Create analysis request | NEW (with persistence) |
| `/api/media/status/{id}` | GET | Query analysis status | NEW |
| `/api/media/{id}` | DELETE | Soft delete analysis | NEW |
| `/api/media/history` | GET | List analysis history | NEW |

### File Structure to Create

```
/opt/services/media-analysis/
├── database/
│   ├── __init__.py
│   └── config.py              # Database connection settings
├── models/
│   ├── __init__.py
│   └── analysis_request.py    # SQLAlchemy model
├── schemas/
│   ├── __init__.py
│   └── analysis.py            # Pydantic schemas
├── repositories/
│   ├── __init__.py
│   └── analysis_repository.py # CRUD operations
├── routes/
│   ├── __init__.py
│   ├── analyze.py             # POST /api/media/analyze
│   ├── status.py              # GET /api/media/status/{id}
│   ├── delete.py              # DELETE /api/media/{id}
│   └── history.py             # GET /api/media/history
├── tasks/
│   ├── __init__.py
│   └── process_analysis.py    # Celery task
├── alembic/
│   └── versions/
│       └── xxx_create_analysis_request.py  # Migration script
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_analyze_endpoint.py
│   ├── test_status_endpoint.py
│   ├── test_delete_endpoint.py
│   └── test_history_endpoint.py
└── requirements.txt           # Add dependencies
```

---

# 3. System Architecture

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    API Client / Frontend                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS Requests
┌────────────────────────▼────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Endpoints  │  │  Services   │  │   Database Layer    │  │
│  │  /analyze   │  │  Business   │  │   PostgreSQL        │  │
│  │  /status    │  │  Logic      │  │   (analysis_request)│  │
│  │  /delete    │  │             │  │                     │  │
│  │  /history   │  │             │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ Async Task Queue
┌────────────────────────▼────────────────────────────────────┐
│                   Celery Worker (Redis)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  1. Fetch pending analysis requests                 │   │
│  │  2. Update status to 'processing'                   │   │
│  │  3. Process media (FFmpeg/Deepgram/etc)             │   │
│  │  4. Store results in JSONB column                   │   │
│  │  5. Update status to 'completed' or 'failed'        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### POST /api/media/analyze Flow

```
1. Client → POST /api/media/analyze
   { "prompt": "...", "media_url": "...", "media_type": "video" }

2. API validates request

3. API → INSERT INTO analysis_request
   status='pending', media_type='video', source_url='...'

4. API returns
   { "analysis_id": "uuid", "status": "pending", "estimated_time": 30 }

5. API → Celery.process_analysis.delay(analysis_id)

6. Celery Worker picks up task

7. Celery → UPDATE analysis_request
   status='processing', progress=10

8. Celery processes media (FFmpeg, LLM, etc.)

9. Celery → UPDATE analysis_request
   status='completed', progress=100, results={...}

10. Client → GET /api/media/status/{id}
    Receives status='completed', results={...}
```

---

# 4. Database Design

## Table Schema

### analysis_request

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| id | UUID | PRIMARY KEY | `gen_random_uuid()` | Unique analysis identifier |
| status | VARCHAR(20) | NOT NULL, CHECK | `'pending'` | Request status (pending/processing/completed/failed/deleted) |
| media_type | VARCHAR(50) | NOT NULL, CHECK | - | Media type (video/audio/document/image/unknown) |
| source_url | TEXT | NOT NULL | - | Original media URL |
| filename | VARCHAR(500) | NULL | - | Original filename if uploaded |
| analysis_config | JSONB | NOT NULL | `{}` | Configuration parameters |
| analysis_options | JSONB | NOT NULL | `{}` | Processing options |
| results | JSONB | NOT NULL | `{}` | Analysis results |
| progress | INTEGER | NOT NULL, CHECK | `0` | Progress percentage (0-100) |
| error_message | TEXT | NULL | - | Error details if failed |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL | `NOW()` | Request creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL | `NOW()` | Last update timestamp |
| completed_at | TIMESTAMP WITH TIME ZONE | NULL | - | Completion timestamp |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULL | - | Soft delete timestamp |
| created_by | UUID | NULL | - | User ID (for multi-tenant) |
| celery_task_id | VARCHAR(255) | NULL | - | Celery task reference |

### Status Values

| Status | Description |
|--------|-------------|
| `pending` | Request received, waiting to start |
| `processing` | Currently being processed |
| `completed` | Analysis finished successfully |
| `failed` | Analysis failed with error |
| `deleted` | Soft deleted (filtered from queries) |

### Media Type Values

| Type | Description |
|------|-------------|
| `video` | Video files (mp4, mov, avi) |
| `audio` | Audio files (mp3, wav, ogg) |
| `document` | Documents (pdf, doc, txt) |
| `image` | Images (jpg, png, gif) |
| `unknown` | Auto-detect or unknown type |

## Complete SQL

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create analysis_request table
CREATE TABLE analysis_request (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'processing', 'completed', 'failed', 'deleted')
    ),
    media_type VARCHAR(50) NOT NULL CHECK (
        media_type IN ('video', 'audio', 'document', 'image', 'unknown')
    ),
    source_url TEXT NOT NULL,
    filename VARCHAR(500),
    analysis_config JSONB DEFAULT '{}',
    analysis_options JSONB DEFAULT '{}',
    results JSONB DEFAULT '{}',
    progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    celery_task_id VARCHAR(255)
);

-- Indexes for query optimization
CREATE INDEX idx_analysis_request_status_active
    ON analysis_request(status)
    WHERE status != 'deleted';

CREATE INDEX idx_analysis_request_created_at
    ON analysis_request(created_at DESC);

CREATE INDEX idx_analysis_request_status_created
    ON analysis_request(status, created_at DESC)
    WHERE status != 'deleted';

CREATE INDEX idx_analysis_request_created_by
    ON analysis_request(created_by, created_at DESC)
    WHERE created_by IS NOT NULL;

CREATE INDEX idx_analysis_request_celery_task
    ON analysis_request(celery_task_id)
    WHERE celery_task_id IS NOT NULL;

CREATE INDEX idx_analysis_request_media_type
    ON analysis_request(media_type)
    WHERE status != 'deleted';
```

## Index Strategy

| Index | Columns | Purpose | Query Pattern |
|-------|---------|---------|---------------|
| idx_analysis_request_status_active | status | Filter active requests | `WHERE status != 'deleted'` |
| idx_analysis_request_created_at | created_at DESC | Sort by date | `ORDER BY created_at DESC` |
| idx_analysis_request_status_created | status, created_at DESC | Filter + sort | `WHERE status != 'deleted' ORDER BY created_at DESC` |
| idx_analysis_request_created_by | created_by, created_at DESC | User queries | `WHERE created_by = ? ORDER BY created_at DESC` |
| idx_analysis_request_celery_task | celery_task_id | Task lookup | `WHERE celery_task_id = ?` |
| idx_analysis_request_media_type | media_type | Type filter | `WHERE media_type = ? AND status != 'deleted'` |

---

# 5. Endpoint Integration

## 5.1 POST /api/media/analyze

### Request Schema

```json
{
  "prompt": "What is happening in this video?",
  "media_url": "https://example.com/video.mp4",
  "media_type": "video",
  "config": {
    "model": "gpt-4o",
    "max_tokens": 2000,
    "temperature": 0.7
  },
  "options": {
    "extract_frames": true,
    "generate_contact_sheet": false,
    "transcribe_audio": true
  }
}
```

### Response Schema (202 Accepted)

```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "estimated_time": 30,
  "message": "Analysis queued. Check status with /api/media/status/{id}"
}
```

### Error Responses

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | Invalid request | Missing required fields |
| 422 | Validation error | Invalid field format |
| 500 | Internal error | Database or processing error |

### Implementation

```python
@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_media(
    request: AnalyzeRequest,
    repository: AnalysisRepository = Depends(get_repository),
) -> AnalysisResponse:
    """Create a new media analysis request."""
    # Create database record
    analysis_id = uuid4()
    analysis = await repository.create(
        request=request,
        celery_task_id=None,
    )

    # Queue async task
    celery_task = process_analysis.delay(str(analysis_id))

    # Update with Celery task ID
    await repository.update_celery_task_id(analysis_id, celery_task.id)

    # Return response
    return AnalysisResponse(
        analysis_id=analysis_id,
        status='pending',
        estimated_time=estimate_processing_time(request.media_type),
    )
```

---

## 5.2 GET /api/media/status/{id}

### Response Schema (200 OK)

```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "media_type": "video",
  "source_url": "https://example.com/video.mp4",
  "created_at": "2026-01-20T10:00:00Z",
  "updated_at": "2026-01-20T10:00:30Z",
  "completed_at": "2026-01-20T10:00:30Z",
  "result_summary": {
    "summary": "Video shows a person speaking about AI",
    "topics": ["AI", "Technology", "Future"]
  },
  "error_message": null
}
```

### Error Responses

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | Invalid UUID | Invalid analysis_id format |
| 404 | Not found | Analysis does not exist |
| 410 | Gone | Analysis was deleted |

---

## 5.3 DELETE /api/media/{id}

### Response (204 No Content)

On successful soft deletion, returns 204 No Content.

### Error Responses

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | Invalid UUID | Invalid analysis_id format |
| 404 | Not found | Analysis does not exist |
| 410 | Gone | Analysis already deleted |

### Implementation

```python
@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_analysis(
    analysis_id: str,
    repository: AnalysisRepository = Depends(get_repository),
) -> Response:
    """Soft delete an analysis request."""
    uuid_id = UUID(analysis_id)

    # Verify exists
    analysis = await repository.get_by_id(uuid_id)
    if not analysis:
        deleted = await repository.is_deleted(uuid_id)
        if deleted:
            raise HTTPException(status_code=410, detail="Already deleted")
        else:
            raise HTTPException(status_code=404, detail="Not found")

    # Soft delete
    await repository.soft_delete(uuid_id)
    return Response(status_code=204)
```

---

## 5.4 GET /api/media/history

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number (1-indexed) |
| per_page | integer | 20 | Items per page (max 100) |
| status | string | all | Filter by status |
| media_type | string | all | Filter by media type |
| date_from | datetime | - | Filter from date |
| date_to | datetime | - | Filter to date |
| sort_by | string | created_at | Sort field |
| order | string | desc | Sort order (asc/desc) |

### Response Schema (200 OK)

```json
{
  "data": [
    {
      "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "media_type": "video",
      "prompt": "What is happening in this video?",
      "created_at": "2026-01-20T10:00:00Z",
      "completed_at": "2026-01-20T10:00:30Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

---

# 6. Implementation Phases

## Phase 1: Database Setup (Week 1, Days 1-5)

**Objective**: Create database schema and verify connection

### Tasks

| Task | Description | Owner | Duration |
|------|-------------|-------|----------|
| 1.1 | Create Alembic migration script | Backend | 1 day |
| 1.2 | Apply migration to database | DevOps | 0.5 day |
| 1.3 | Verify connection and indexes | Backend | 0.5 day |
| 1.4 | Test rollback procedure | DevOps | 0.5 day |
| 1.5 | Document connection configuration | Backend | 0.5 day |

### Commands

```bash
# Navigate to project directory
cd /opt/services/media-analysis

# Initialize Alembic (if not done)
alembic init alembic

# Configure alembic.ini
# Set sqlalchemy.url = postgresql+asyncpg://user:pass@host:5432/media_analysis

# Create migration script
alembic revision --autogenerate -m "Create analysis_request table"

# Review generated migration
cat alembic/versions/xxx_create_analysis_request.py

# Apply migration
alembic upgrade head

# Verify table exists
psql -d media_analysis -c "\d analysis_request"

# Verify indexes
psql -d media_analysis -c "\di analysis_request*"

# Test rollback
alembic downgrade -1
psql -d media_analysis -c "SELECT COUNT(*) FROM analysis_request;"
# Expected: 0 rows (empty table)

# Re-apply migration
alembic upgrade head
```

### Verification

```bash
# Check migration status
alembic current
# Expected: abc123 (or migration hash)

# Check table structure
psql -d media_analysis -c "\d analysis_request"
# Expected: All columns, constraints, indexes defined

# Check indexes
psql -d media_analysis -c "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'analysis_request';"
# Expected: 6 indexes defined
```

### Rollback

```bash
# Rollback one migration
alembic downgrade -1

# Verify table removed
psql -d media_analysis -c "SELECT COUNT(*) FROM analysis_request;"
# Expected: ERROR: relation "analysis_request" does not exist
```

---

## Phase 2: Model Layer (Week 1, Days 6-10)

**Objective**: Implement data access layer

### Tasks

| Task | Description | Owner | Duration |
|------|-------------|-------|----------|
| 2.1 | Create SQLAlchemy model | Backend | 1 day |
| 2.2 | Implement repository pattern | Backend | 2 days |
| 2.3 | Add Pydantic schemas | Backend | 1 day |
| 2.4 | Write unit tests | QA | 2 days |

### Commands

```bash
# Create model file
touch /opt/services/media-analysis/models/analysis_request.py
touch /opt/services/media-analysis/repositories/analysis_repository.py
touch /opt/services/media-analysis/schemas/analysis.py

# Verify model import
python -c "from app.models.analysis_request import AnalysisRequest; print('Model OK')"
# Expected: Model OK

# Verify repository import
python -c "from app.repositories.analysis_repository import AnalysisRepository; print('Repository OK')"
# Expected: Repository OK

# Verify schemas import
python -c "from app.schemas.analysis import AnalyzeRequest, AnalysisResponse; print('Schemas OK')"
# Expected: Schemas OK

# Run unit tests
pytest tests/unit/models/ -v
# Expected: All tests pass (target: 90% coverage)

pytest tests/unit/schemas/ -v
# Expected: All tests pass

pytest tests/unit/repositories/ -v
# Expected: All tests pass
```

### Verification

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Model coverage | 100% | pytest --cov app/models |
| Repository coverage | 100% | pytest --cov app/repositories |
| Schema validation | 100% | All Pydantic models tested |
| Type hints | 100% | mypy checking |

### Rollback

```bash
# Revert model files
git checkout HEAD -- app/models/ app/repositories/ app/schemas/

# Migration remains (no-op)
alembic current
# Expected: Still at latest migration
```

---

## Phase 3: Service Layer (Week 2, Days 1-5)

**Objective**: Implement business logic

### Tasks

| Task | Description | Owner | Duration |
|------|-------------|-------|----------|
| 3.1 | Implement CRUD operations | Backend | 2 days |
| 3.2 | Add business logic validation | Backend | 1 day |
| 3.3 | Implement error handling | Backend | 1 day |
| 3.4 | Write integration tests | QA | 1 day |

### Commands

```bash
# Test service layer
pytest tests/integration/ -v
# Expected: All integration tests pass

# Test database connection
python -c "
import asyncio
from app.core.database import get_session
from app.repositories.analysis_repository import AnalysisRepository

async def test_connection():
    async for session in get_session():
        repository = AnalysisRepository(session)
        # Test basic query
        result = await repository.get_pending_count()
        print(f'Connection OK, pending count: {result}')

asyncio.run(test_connection())
"
# Expected: Connection OK, pending count: 0
```

### Verification

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Integration tests | 100% pass | pytest tests/integration/ |
| Async operations | All tested | pytest tests/integration/ -k async |
| Error scenarios | 100% coverage | pytest tests/integration/ -k error |

### Rollback

```bash
# Revert service files
git checkout HEAD -- app/services/

# Migration and models remain
alembic current
# Expected: Still at latest migration
```

---

## Phase 4: API Integration (Week 2, Days 6-10)

**Objective**: Update API endpoints

### Tasks

| Task | Description | Owner | Duration |
|------|-------------|-------|----------|
| 4.1 | Update POST /api/media/analyze | Backend | 1 day |
| 4.2 | Implement GET /api/media/status/{id} | Backend | 1 day |
| 4.3 | Implement DELETE /api/media/{id} | Backend | 1 day |
| 4.4 | Implement GET /api/media/history | Backend | 1 day |
| 4.5 | Add endpoint integration tests | QA | 1 day |

### Commands

```bash
# Test all endpoints
pytest tests/api/ -v
# Expected: All endpoint tests pass

# Manual endpoint testing
# Start API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Test POST /api/media/analyze
curl -X POST http://localhost:8000/api/media/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is happening in this video?",
    "media_url": "https://example.com/video.mp4",
    "media_type": "video"
  }'
# Expected: 202 status, JSON with analysis_id

# Test GET /api/media/status/{id}
curl http://localhost:8000/api/media/status/{analysis_id}
# Expected: 200 status, JSON with status and progress

# Test GET /api/media/history
curl http://localhost:8000/api/media/history?page=1&per_page=10
# Expected: 200 status, JSON with pagination

# Test DELETE /api/media/{id}
curl -X DELETE http://localhost:8000/api/media/{analysis_id}
# Expected: 204 No Content
```

### Verification

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Endpoint tests | 100% pass | pytest tests/api/ |
| Status codes | All correct | Manual testing |
| Response schemas | Valid | Pydantic validation |
| Error handling | All scenarios | pytest tests/api/ -k error |

### Rollback

```bash
# Revert endpoint files
git checkout HEAD -- app/routes/

# Migration and models remain
alembic current
# Expected: Still at latest migration
```

---

## Phase 5: Testing & Verification (Week 3, Days 1-5)

**Objective**: Full system testing

### Tasks

| Task | Description | Owner | Duration |
|------|-------------|-------|----------|
| 5.1 | Unit tests (90%+ coverage) | QA | 2 days |
| 5.2 | Integration tests | QA | 1 day |
| 5.3 | Load testing (100 RPS) | QA | 1 day |
| 5.4 | Manual end-to-end testing | QA | 1 day |

### Commands

```bash
# Full test suite
pytest tests/ -v --cov --cov-report=html --cov-report=term-missing
# Expected: 90% coverage minimum

# Generate coverage report
open htmlcov/index.html

# Load test
locust -f tests/locustfile.py --host=http://localhost:8000 -u 100 -r 10 --run-time=5m
# Expected: 100 RPS with <500ms p95 latency

# Smoke tests
./scripts/smoke-tests.sh
# Expected: All smoke tests pass
```

### Load Test Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Requests per second | 100 RPS | locust statistics |
| API latency p95 | <500ms | locust statistics |
| Error rate | <0.1% | locust statistics |
| Database CPU | <70% | monitoring dashboard |

### Verification

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Unit test coverage | ≥90% | pytest --cov |
| Integration tests | 100% pass | pytest tests/integration/ |
| Load test RPS | 100 | locust |
| Load test latency | <500ms p95 | locust |
| Manual tests | 100% pass | TestRail |

### Rollback

```bash
# Previous phase rollback
git checkout HEAD -- app/routes/ app/services/

# If needed, full rollback
git checkout HEAD~5 -- .

# Restore from database backup
psql -d media_analysis < backup_pre_migration.sql

# Re-apply migrations
alembic upgrade head
```

---

# 7. Risk Management

## Risk Summary

| Risk | Impact | Likelihood | Priority |
|------|--------|------------|----------|
| Database Migration | HIGH | MEDIUM | P1 |
| Data Consistency | MEDIUM | MEDIUM | P2 |
| Performance | MEDIUM | HIGH | P2 |
| API Compatibility | HIGH | LOW | P3 |
| Soft Delete Complexity | LOW | MEDIUM | P4 |

### Key Mitigations

1. **Database Migration**: Backup, staging validation, zero-downtime pattern
2. **Data Consistency**: Optimistic locking, idempotent operations, transactions
3. **Performance**: Proper indexing, connection pooling, pagination
4. **API Compatibility**: Backward compatibility, feature flags, versioning
5. **Soft Delete**: Repository pattern, default filters, automatic archival

### Monitoring

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| API latency p95 | <500ms | 500ms-1s | >1s |
| Error rate | <0.1% | 0.1-1% | >1% |
| DB CPU | <60% | 60-80% | >80% |
| Connection pool | <70% | 70-90% | >90% |

---

# 8. Dependencies

## New Python Dependencies

```txt
# requirements.txt
sqlalchemy[asyncio]>=2.0.0
psycopg2-binary>=2.9.0
alembic>=1.12.0
celery[redis]>=5.3.0
redis>=5.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
locust>=2.18.0
```

## Infrastructure Dependencies

| Component | Version | Purpose |
|-----------|---------|---------|
| PostgreSQL | 14+ | Primary database |
| Redis | 6+ | Celery broker/backend |
| Alembic | 1.12+ | Migration tool |

## Environment Variables

```bash
# .env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/media_analysis
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=1800

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

# 9. Testing Strategy

## Test Pyramid

```
        ┌─────────────┐
        │   Load      │  ← Locust (100 RPS)
       ┌┴─────────────┴┐
       │  Integration  │  ← API tests
      ┌┴───────────────┴┐
      │     Unit        │  ← Model, Schema, Repository tests
     ┌┴─────────────────┴┐
     │   Component        │  ← SQLAlchemy, Pydantic
    ┌┴───────────────────┴┐
    │      Database        │  ← PostgreSQL
    └─────────────────────┘
```

## Test Coverage Targets

| Layer | Target | Tool |
|-------|--------|------|
| Models | 100% | pytest-cov |
| Schemas | 100% | pytest-cov |
| Repositories | 100% | pytest-cov |
| Services | 90% | pytest-cov |
| Endpoints | 90% | pytest-cov |
| Overall | 90% | pytest-cov |

## Test Categories

### Unit Tests

```bash
# Run unit tests
pytest tests/unit/ -v --cov

# Target: 90% coverage
```

### Integration Tests

```bash
# Run integration tests
pytest tests/integration/ -v

# Tests database operations, API contracts
```

### Load Tests

```bash
# Run load test
locust -f tests/locustfile.py --host=http://localhost:8000 -u 200 -r 20 --run-time=10m

# Target: 100 RPS, <500ms p95 latency
```

### Smoke Tests

```bash
# Run smoke tests
./scripts/smoke-tests.sh

# Tests basic API functionality
```

---

# 10. Deployment Plan

## Pre-Deployment Checklist

- [ ] Database backup created and verified
- [ ] Migration tested on staging
- [ ] Rollback procedure documented
- [ ] Monitoring alerts configured
- [ ] Team notified of maintenance window
- [ ] All tests passing (≥90% coverage)
- [ ] Load test passed (100 RPS)
- [ ] Documentation updated

## Deployment Steps

```bash
# 1. Create database backup
pg_dump -d media_analysis > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Apply migration (zero-downtime)
alembic upgrade head

# 3. Deploy application
docker compose up -d --build api

# 4. Start Celery workers
docker compose up -d celery-worker

# 5. Verify endpoints
./scripts/verify-endpoints.sh

# 6. Monitor logs
docker compose logs -f api

# 7. Verify no new alerts
kubectl get alerts
```

## Verification Commands

```bash
# Check migration status
alembic current

# Check table exists
psql -d media_analysis -c "\d analysis_request"

# Test POST /api/media/analyze
curl -X POST http://localhost:8000/api/media/analyze \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test", "media_url": "https://example.com/video.mp4", "media_type": "video"}'

# Test GET /api/media/status/{id}
curl http://localhost:8000/api/media/status/{analysis_id}

# Test GET /api/media/history
curl http://localhost:8000/api/media/history?page=1&per_page=20

# Test DELETE /api/media/{id}
curl -X DELETE http://localhost:8000/api/media/{analysis_id}
```

---

# 11. Rollback Procedures

## Quick Rollback (Application Only)

```bash
# Revert to previous image
docker compose pull api:previous
docker compose up -d api
```

## Database Rollback

```bash
# Rollback one migration
alembic downgrade -1

# Verify table removed
psql -d media_analysis -c "SELECT COUNT(*) FROM analysis_request;"
# Expected: ERROR: relation does not exist
```

## Full Rollback (Emergency)

```bash
# 1. Stop application
docker compose down api

# 2. Restore from backup
psql -d media_analysis < backup_20260120_120000.sql

# 3. Revert application code
git checkout <previous-commit>

# 4. Rebuild and start
docker compose up -d --build api

# 5. Verify
./scripts/smoke-tests.sh
```

---

# 12. Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Test Coverage | ≥90% | pytest --cov |
| API Latency | <500ms p95 | locust statistics |
| Migration Time | <30s | timed execution |
| Rollback Time | <5min | timed execution |
| Error Rate | <0.1% | monitoring dashboard |
| Load Test | 100 RPS | locust |

---

# 13. Timeline

| Phase | Duration | Start | End | Owner |
|-------|----------|-------|-----|-------|
| Phase 1: Database Setup | 1 week | Week 1, Day 1 | Week 1, Day 5 | DevOps/Backend |
| Phase 2: Model Layer | 1 week | Week 1, Day 6 | Week 2, Day 5 | Backend |
| Phase 3: Service Layer | 1 week | Week 2, Day 6 | Week 3, Day 5 | Backend |
| Phase 4: API Integration | 1 week | Week 3, Day 6 | Week 4, Day 5 | Backend |
| Phase 5: Testing & Verification | 1 week | Week 4, Day 6 | Week 5, Day 5 | QA |

**Total Estimated Time**: 5 weeks

---

# 14. Open Questions

1. [ ] What is the expected volume of analysis requests per day?
   - Impacts: Index strategy, connection pool size, archival policy

2. [ ] Should we implement data retention/archival policy?
   - Impacts: Storage costs, query performance, compliance

3. [ ] Do we need multi-tenant support (user_id field)?
   - Impacts: Schema design, repository pattern, API authentication

4. [ ] What is the max acceptable latency for status checks?
   - Impacts: Caching strategy, connection pool size

5. [ ] Should we implement caching for frequently accessed status?
   - Impacts: Redis configuration, cache invalidation logic

---

# 15. Appendix

## A. Database Schema Reference

### Complete CREATE TABLE Statement

```sql
CREATE TABLE analysis_request (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'processing', 'completed', 'failed', 'deleted')
    ),
    media_type VARCHAR(50) NOT NULL CHECK (
        media_type IN ('video', 'audio', 'document', 'image', 'unknown')
    ),
    source_url TEXT NOT NULL,
    filename VARCHAR(500),
    analysis_config JSONB DEFAULT '{}',
    analysis_options JSONB DEFAULT '{}',
    results JSONB DEFAULT '{}',
    progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    celery_task_id VARCHAR(255)
);
```

## B. API Response Codes

| Endpoint | Method | Success | Client Error | Server Error |
|----------|--------|---------|--------------|--------------|
| /analyze | POST | 202 | 400, 422 | 500 |
| /status/{id} | GET | 200 | 400, 404, 410 | 500 |
| /{id} | DELETE | 204 | 400, 404, 410 | 500 |
| /history | GET | 200 | 400 | 500 |

## C. Glossary

| Term | Definition |
|------|------------|
| **Analysis Request** | A single media analysis task with unique UUID |
| **Soft Delete** | Marking record as deleted without physical removal (status='deleted') |
| **Repository Pattern** | Abstraction for data access layer |
| **Idempotent** | Operation that produces same result when repeated |
| **Celery Task** | Async background job for long-running processing |
| **Zero-Downtime Migration** | Migration that doesn't interrupt service availability |

---

*Generated: 2026-01-20*
*Version: 1.0*
*Output: /home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-24.md*
