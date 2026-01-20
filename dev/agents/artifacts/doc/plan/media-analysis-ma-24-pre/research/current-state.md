# Current State Analysis: Media Analysis API

**Date**: 2026-01-20
**Task**: Database Integration PRD Research - Phase 1
**Output**: /home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-24-pre/research/current-state.md

---

## 1. Directory Structure

### Source System (devmaster)
```
/opt/clients/af/dev/services/cotizador-api/
├── cotizador_api.py           # Main FastAPI service (~344KB, 50+ endpoints)
├── cotizador.py               # Core analysis logic
├── docker-compose.yml         # Service orchestration
├── Dockerfile                 # Container build
├── .env                       # Environment configuration
├── Caddyfile                  # Web server routing
├── hitl_push.py               # Human-in-the-loop push
├── archive_endpoint.py        # Archival operations
├── benchmark_models.py        # Model benchmarking
└── requirements.txt           # Python dependencies
```

### Target System (local)
```
/opt/services/media-analysis/
├── media_analysis_api.py      # Main FastAPI service (cloned)
├── docker-compose.yml         # Service orchestration (new network)
├── Dockerfile                 # Container build
├── .env                       # Environment configuration
├── Caddyfile                  # Web server routing (new)
├── requirements.txt           # Python dependencies
├── routes/                    # API route handlers
├── services/                  # Business logic
├── models/                    # Data models (to be created)
└── database/                  # Database config (to be created)
```

---

## 2. API Endpoint Implementations

### 2.1 POST /api/media/analyze

**Status**: NEW ENDPOINT (Aggregator)
- **File**: `/opt/services/media-analysis/media_analysis_api.py`
- **Lines**: ~100-150 (estimated)
- **Current behavior**: Accepts natural language prompt + media URL, orchestrates full analysis pipeline
- **Request schema**:
  ```python
  {
    "prompt": "string",           # Natural language instruction
    "media_url": "string",        # Video/audio/document URL
    "media_type": "video|audio|document|auto",
    "options": {
      "extract_frames": boolean,
      "generate_contact_sheet": boolean,
      "transcribe_audio": boolean,
      "ocr_document": boolean
    }
  }
  ```
- **Response schema**:
  ```python
  {
    "analysis_id": "uuid",
    "status": "pending|processing|completed|failed",
    "estimated_time": "seconds",
    "result_url": "string|null"
  }
  ```
- **Current data flow**:
  1. Receive request with media URL and prompt
  2. Route to appropriate branch (audio/video/document)
  3. Process media using FFmpeg/Deepgram/OCR
  4. Return immediate response (no persistence)

**Missing**: No database persistence, no status tracking, no async processing

---

### 2.2 GET /api/media/status/{id}

**Status**: NEW ENDPOINT (to be implemented)
- **File**: `/opt/services/media-analysis/routes/status.py` (to be created)
- **Lines**: N/A (new)
- **Current behavior**: Does not exist
- **Required behavior**: Query analysis status from database, return progress and results
- **Request schema**: Path parameter `id` (UUID)
- **Response schema**:
  ```python
  {
    "analysis_id": "uuid",
    "status": "pending|processing|completed|failed|deleted",
    "progress": 0-100,
    "created_at": "timestamp",
    "completed_at": "timestamp|null",
    "result_summary": "object|null",
    "error_message": "string|null"
  }
  ```
- **Current data flow**: N/A (endpoint does not exist)

**Blocking**: Requires database schema for `analysis_request` table

---

### 2.3 DELETE /api/media/{id}

**Status**: NEW ENDPOINT (to be implemented)
- **File**: `/opt/services/media-analysis/routes/delete.py` (to be created)
- **Lines**: N/A (new)
- **Current behavior**: Does not exist
- **Required behavior**: Soft delete analysis request (status='deleted')
- **Request schema**: Path parameter `id` (UUID)
- **Response schema**: 204 No Content
- **Current data flow**: N/A (endpoint does not exist)

**Blocking**: Requires database schema and soft delete logic

---

### 2.4 GET /api/media/history

**Status**: NEW ENDPOINT (to be implemented)
- **File**: `/opt/services/media-analysis/routes/history.py` (to be created)
- **Lines**: N/A (new)
- **Current behavior**: Does not exist
- **Required behavior**: List analysis requests with pagination and filtering
- **Request schema**:
  ```python
  {
    "page": 1,
    "per_page": 20,
    "status": "pending|processing|completed|failed|all",
    "media_type": "video|audio|document|all",
    "date_from": "timestamp|null",
    "date_to": "timestamp|null",
    "sort_by": "created_at|status|media_type",
    "order": "asc|desc"
  }
  ```
- **Response schema**:
  ```python
  {
    "data": [
      {
        "analysis_id": "uuid",
        "status": "string",
        "media_type": "string",
        "created_at": "timestamp",
        "prompt": "string"
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
- **Current data flow**: N/A (endpoint does not exist)

**Blocking**: Requires database table and query optimization

---

## 3. Existing Database Models

### Current State: NO DATABASE LAYER

| Component | Status | Details |
|-----------|--------|---------|
| **SQLAlchemy Models** | None | No ORM models defined |
| **Database Tables** | None | No persistent storage |
| **Migration Tool** | None | No Alembic/Flyway setup |
| **Connection Pool** | None | No database connection |
| **Seed Data** | None | Not required |

### Files to Create for Database Layer

| File | Purpose |
|------|---------|
| `/opt/services/media-analysis/database/config.py` | Database connection settings |
| `/opt/services/media-analysis/models/analysis_request.py` | SQLAlchemy model for analysis_request table |
| `/opt/services/media-analysis/schemas/analysis.py` | Pydantic request/response schemas |
| `/opt/services/media-analysis/repositories/analysis_repository.py` | Repository pattern implementation |
| `/opt/services/media-analysis/alembic/versions/` | Migration scripts |

---

## 4. Database Configuration

### Required Configuration

**Connection Settings** (from .env):
```
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/media_analysis
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=1800
```

**Redis Configuration** (for Celery):
```
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**Migration Tool Choice**: Alembic
- Standard for FastAPI projects
- Async support via SQLAlchemy 2.0
- Auto-generation support

---

## 5. Key Findings Summary

### Critical Discoveries

1. **No Database Layer Exists**
   - The Media Analysis API currently has NO database integration
   - All processing is in-memory, no persistence
   - Status endpoints (status, history, delete) do not exist

2. **Four New Endpoints Required**
   - Status tracking: `GET /api/media/status/{id}`
   - History listing: `GET /api/media/history`
   - Deletion: `DELETE /api/media/{id}`
   - All require database persistence

3. **Architecture Ready for Integration**
   - FastAPI framework supports async SQLAlchemy
   - Clean separation of routes/services/models
   - Ready for repository pattern implementation

4. **Async Processing Pattern Needed**
   - Media analysis is long-running (seconds to minutes)
   - Current implementation is synchronous
   - Need Celery/Redis for async task queue

5. **File Paths for Implementation**
   - Model file: `/opt/services/media-analysis/models/analysis_request.py`
   - Schema file: `/opt/services/media-analysis/schemas/analysis.py`
   - Repository: `/opt/services/media-analysis/repositories/analysis_repository.py`
   - Database config: `/opt/services/media-analysis/database/config.py`
   - Migration directory: `/opt/services/media-analysis/alembic/versions/`

### Data Flow After Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    API Client / Frontend                     │
└────────────────────────┬────────────────────────────────────┘
                         │ POST /api/media/analyze
┌────────────────────────▼────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  1. Validate request                                │   │
│  │  2. Create AnalysisRequest record (status='pending')│   │
│  │  3. Queue async task (Celery)                       │   │
│  │  4. Return analysis_id, status='pending'            │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ INSERT INTO analysis_request
┌────────────────────────▼────────────────────────────────────┐
│                   PostgreSQL Database                        │
│                    (analysis_request table)                  │
└─────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Celery Worker (Redis)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  1. Pick up task                                    │   │
│  │  2. Update status='processing'                      │   │
│  │  3. Process media (FFmpeg/Deepgram/etc)             │   │
│  │  4. Store results in JSONB column                   │   │
│  │  5. Update status='completed'                       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Priority

1. **Phase 1**: Database schema and migration
2. **Phase 2**: SQLAlchemy model and Pydantic schemas
3. **Phase 3**: Repository pattern implementation
4. **Phase 4**: Update POST /api/media/analyze with persistence
5. **Phase 5**: Implement GET /api/media/status/{id}
6. **Phase 6**: Implement DELETE /api/media/{id}
7. **Phase 7**: Implement GET /api/media/history
8. **Phase 8**: Celery integration for async processing

---

## 6. Next Steps for Phases 2-5

Based on Phase 1 findings, Phase 2 should design:

1. **analysis_request table** with:
   - UUID primary key
   - Status field with enum constraints
   - Media metadata (type, source, filename)
   - Analysis parameters (JSONB for flexibility)
   - Results storage (JSONB)
   - Timestamps (created, updated, completed, deleted)
   - Soft delete support

2. **Index strategy** optimized for:
   - Status queries (most common)
   - Date range queries for history
   - User filtering (if multi-tenant)

3. **Migration approach**:
   - Alembic for version control
   - Zero-downtime deployment
   - Rollback capability

---

*Research completed: 2026-01-20*
*Output: /home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-24-pre/research/current-state.md*
