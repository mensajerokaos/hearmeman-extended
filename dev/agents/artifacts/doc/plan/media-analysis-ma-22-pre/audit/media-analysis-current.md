# Media Analysis API - Current State Audit

**Audit Date:** 2026-01-20
**Auditor:** Claude Code Audit System
**Context:** MA-22 Pre-Implementation Assessment

---

## 1. Directory Structure Overview

### 1.1 Implementation Location

The media-analysis service was cloned from the AF project and deployed to:

```
/opt/services/media-analysis/
├── Dockerfile
├── docker-compose.yml
├── Caddyfile
├── requirements.txt
├── config/
│   ├── .env
│   └── requirements.txt
├── api/
│   ├── __init__.py
│   ├── media_analysis_api.py (main API - 344KB, 50+ endpoints)
│   ├── media_analysis.py
│   ├── minimax_client.py (NEW)
│   ├── minimax_integration.py (NEW)
│   ├── archive_endpoint.py
│   ├── benchmark_models.py
│   ├── config_loader.py
│   ├── metrics.py
│   ├── scoring.py
│   ├── kommo_client.py
│   └── jobs.py
├── uploads/
└── outputs/
```

**Key Finding:** The `/opt/services/media-analysis/` directory exists on the remote server (devmaster) but is NOT present in the local repository at `/home/oz/projects/2025/oz/12/runpod/`. All implementation artifacts exist only as documentation and planning files in the local workspace.

### 1.2 Local Repository Structure

The local repository contains planning and research artifacts:

```
/home/oz/projects/2025/oz/12/runpod/
├── .brv/context-tree/structure/media_analysis/
│   ├── media_analysis_pipeline_overview.md
│   ├── audio_analysis_pipeline.md
│   └── video_analysis_pipeline.md
└── dev/agents/artifacts/doc/
    ├── plan/media-analysis-api-prd.md (PRD - 2204 lines)
    ├── plan/media-analysis-ma-*-pre/ (Multiple phase planning directories)
    ├── implement-runs/20260118-media-analysis/
    │   ├── implementation-summary.md
    │   ├── activity.md
    │   └── wave2-scaffold-network.json
    └── audit/media-analysis-api-prd-pre/
```

---

## 2. Existing Files and Their Purposes

### 2.1 Core API Files (Located on Remote Server Only)

| File | Size | Purpose | Lines of Code |
|------|------|---------|---------------|
| `media_analysis_api.py` | ~344KB | Main FastAPI application with 50+ endpoints | 10,000+ |
| `media_analysis.py` | Unknown | Core processing logic | Unknown |
| `minimax_client.py` | NEW | MiniMax API client for vision/text capabilities | ~500 |
| `minimax_integration.py` | NEW | Integration layer for video, audio, document analysis | ~800 |
| `archive_endpoint.py` | Unknown | Archive functionality | Unknown |
| `benchmark_models.py` | Unknown | Model benchmarking utilities | Unknown |
| `config_loader.py` | Unknown | Configuration management | Unknown |
| `metrics.py` | Unknown | Metrics collection and reporting | Unknown |
| `scoring.py` | Unknown | Scoring algorithms | Unknown |
| `kommo_client.py` | Unknown | Kommo API integration | Unknown |
| `jobs.py` | Unknown | Background job processing | Unknown |

### 2.2 Infrastructure Files

| File | Purpose | Status |
|------|---------|--------|
| `Dockerfile` | Multi-stage build with Python 3.11, FFmpeg, dependencies | ✅ Created |
| `docker-compose.yml` | Service orchestration with `media-services-network` | ✅ Created |
| `Caddyfile` | Reverse proxy with domain routing | ✅ Created |
| `requirements.txt` | Python dependencies | ✅ Created |
| `config/.env` | Environment variables with `MEDIA_ANALYSIS_` prefix | ✅ Created |

### 2.3 Planning and Documentation Files

| File | Purpose | Content Summary |
|------|---------|-----------------|
| `media_analysis_pipeline_overview.md` | Architecture overview | Three-branch architecture: Audio, Video, Document processing |
| `audio_analysis_pipeline.md` | Audio processing details | Multi-provider fallback: Groq → Deepgram → OpenAI → Gemini |
| `video_analysis_pipeline.md` | Video processing details | 3fps frame extraction, 2x3 grid contact sheets |
| `media-analysis-api-prd.md` | Product Requirements Document | Complete implementation specification (2204 lines) |
| `implementation-summary.md` | Deployment summary | Service running on port 8050, unhealthy due to DB dependencies |

---

## 3. Current Dependencies

### 3.1 Python Dependencies (from requirements.txt)

**Framework & Server:**
- `fastapi>=0.104.0` - Web framework
- `uvicorn[standard]>=0.24.0` - ASGI server
- `python-multipart>=0.0.6` - File upload support
- `python-dotenv>=1.0.0` - Environment variable management

**Data Validation:**
- `pydantic>=2.0.0` - Data validation using BaseModel (NOT SQLAlchemy)

**Audio/Video Processing:**
- `torch>=2.0.0,<2.7.0` - PyTorch
- `torchaudio>=2.0.0,<2.7.0` - Audio processing
- FFmpeg (system dependency) - Media processing

**External Services:**
- Deepgram API - Audio transcription
- MiniMax API - LLM vision and text capabilities
- Groq API - Transcription fallback
- OpenAI API - Transcription fallback
- Gemini API - Transcription fallback

**Monitoring & Utilities:**
- `psutil>=5.9.0` - System monitoring
- `sse-starlette>=3.0.2` - Server-Sent Events for real-time updates
- `pydub>=0.25.1` - Audio manipulation

### 3.2 System Dependencies

**FFmpeg** (Installed in Dockerfile):
- Required for frame extraction from video
- Used for audio format normalization
- Contact sheet generation

### 3.3 Container Dependencies

**Docker Services:**
- `media-analysis-api` - Main API container (port 8000 internal, mapped to 8050 external)
- `media-services-network` - Isolated Docker network
- No shared dependencies with `af-network`

---

## 4. Database Configuration

### 4.1 Current Database Status

**CRITICAL FINDING:** The media-analysis service has NO dedicated database implementation.

**Evidence:**
1. No SQLAlchemy imports found in any source files
2. No migration files (.sql, alembic, migrations/) present
3. No database connection configuration in `.env` or `config.py`
4. PRD explicitly states "Out of Scope: Database migration or schema changes"
5. Implementation summary notes: "Health check fails due to database dependencies not available in isolated network"

### 4.2 Known Database Issues

The service attempts to connect to `af-postgres-1` which doesn't exist in the isolated `media-services-network`:

```
Impact: Background jobs fail, but API endpoints work
Resolution: Configure DATABASE_URL env var or disable background jobs
```

**Health Check Status:** Container marked unhealthy due to missing database connectivity.

### 4.3 Planned Database Approach

Based on PRD documentation and code patterns observed:

**Anticipated Entity Types** (inferred from file names and processing logic):

1. **Jobs Entity** - Background job tracking
   - File: `jobs.py`
   - Fields: job_id, status, created_at, updated_at, media_type, parameters, result

2. **Analysis Results Entity** - Media analysis outcomes
   - Files: `metrics.py`, `scoring.py`
   - Fields: analysis_id, media_type, frames_extracted, transcription, minimax_result, confidence_score

3. **Media Assets Entity** - Uploaded/processed files
   - Files: `uploads/`, `outputs/` directories
   - Fields: asset_id, original_filename, processed_filename, file_size, media_type

4. **User Sessions Entity** - Session tracking
   - Reference: `session_id` in request models
   - Fields: session_id, created_at, last_activity, user_agent

### 4.4 Data Persistence Model

**Current Approach (No Database):**
- File-based storage in `uploads/` and `outputs/` directories
- JSON metadata files for job tracking
- No transactional integrity or querying capabilities

**Planned Approach (Per PRD):**
- PostgreSQL database (inferred from AF project patterns)
- SQLAlchemy ORM for model definitions
- Alembic for migrations
- Connection via `DATABASE_URL` environment variable

---

## 5. API Routes Overview

### 5.1 Main Router Structure

The API uses FastAPI with the following endpoint organization:

```
Base Router: /api/media/

├── Aggregator (NEW)
│   └── POST /api/media/analyze - Natural language media analysis
│
├── Video Processing
│   ├── POST /api/media/video - Video analysis
│   ├── POST /api/media/video/extract-frames - Frame extraction (3fps)
│   └── POST /api/media/video/contact-sheet - Generate contact sheets
│
├── Audio Processing
│   ├── POST /api/media/audio - Audio analysis
│   ├── POST /api/media/audio/transcribe - Transcription
│   └── Multi-provider fallback: Groq → Deepgram → OpenAI → Gemini
│
├── Document Processing
│   └── POST /api/media/documents - Document analysis
│
├── Health & Status
│   ├── GET /health - Basic health check
│   ├── GET /api/media/health - API health check
│   └── GET /api/media/status - Processing status
│
├── Archive
│   └── GET /api/media/archive - Archived results
│
├── Benchmark
│   └── GET /api/media/benchmark - Model benchmarking
│
└── Configuration
    └── GET /api/media/config - Configuration info
```

### 5.2 Request Models (Pydantic)

**Primary Models Identified:**

1. **AnalyzeRequest** - Aggregator endpoint
   ```python
   class AnalyzeRequest(BaseModel):
       media_type: str  # "video", "audio", "document"
       media_url: str
       prompt: str
   ```

2. **AnalyzeResponse** - Aggregator response
   ```python
   class AnalyzeResponse(BaseModel):
       status: str
       frame_count: Optional[int]
       contact_sheet_path: Optional[str]
       analysis_result: dict
       processing_time_ms: int
   ```

3. **VideoRequest** - Video processing
   - Fields: video_url, fps (default: 3), output_format

4. **AudioRequest** - Audio transcription
   - Fields: audio_url, provider (Deepgram/Groq/OpenAI/Gemini), language

5. **DocumentRequest** - Document processing
   - Fields: document_url, analysis_type

### 5.3 API Characteristics

- **Framework:** FastAPI (async/await support)
- **Validation:** Pydantic BaseModel with Field validators
- **Error Handling:** Custom exception handlers (HTTPException, general Exception)
- **CORS:** Configurable origins (default: `*`)
- **Documentation:** Auto-generated OpenAPI at `/docs` and `/redoc`
- **Authentication:** None implemented (rely on Caddy reverse proxy)

---

## 6. Current .env Configuration

### 6.1 Environment Variables (MEDIA_ANALYSIS_* Prefix)

Based on PRD and implementation summary:

```bash
# Server Configuration
MEDIA_ANALYSIS_API_HOST=0.0.0.0
MEDIA_ANALYSIS_API_PORT=8000

# External Services (Required)
MEDIA_ANALYSIS_API_KEY=your-api-key
DEEPGRAM_API_KEY=your-deepgram-key
MINIMAX_API_KEY=your-minimax-key
GROQ_API_KEY=your-groq-key (fallback)
OPENAI_API_KEY=your-openai-key (fallback)
GEMINI_API_KEY=your-gemini-key (fallback)

# Processing Configuration
MEDIA_ANALYSIS_FPS=3
MEDIA_ANALYSIS_CONTACT_SHEET_GRID=2x3
MEDIA_ANALYSIS_FRAME_FORMAT=jpg
MEDIA_ANALYSIS_MAX_VIDEO_DURATION=3600

# Storage Paths
MEDIA_ANALYSIS_UPLOAD_DIR=/opt/services/media-analysis/uploads
MEDIA_ANALYSIS_OUTPUT_DIR=/opt/services/media-analysis/outputs

# Database (NOT YET CONFIGURED)
DATABASE_URL=postgresql://user:pass@host:5432/media_analysis

# Caddy Reverse Proxy
MEDIA_ANALYSIS_DOMAIN=media-analysis-api.automatic.picturelle.com
CADDY_ACME_EMAIL=your-email@example.com
```

### 6.2 Missing Configuration

**Critical gaps identified:**

1. **Database Connection:** `DATABASE_URL` not set (causes health check failures)
2. **API Keys:** All external service keys need to be configured
3. **Caddy TLS:** Cloudflare API token not configured for automatic TLS
4. **Storage:** Paths may need adjustment for containerized environment

---

## 7. Existing Database Code Analysis

### 7.1 SQLAlchemy Usage

**FINDING:** ZERO SQLAlchemy code exists in the current implementation.

Evidence:
- Search across all `.py` files in repository: No `from sqlalchemy` imports
- No `Base` class definitions
- No `relationship()` or `column()` definitions
- No migration scripts found

### 7.2 Data Persistence Pattern

The service currently uses a **file-based persistence model**:

```python
# Example pattern (inferred from file structure)
uploads/
  └── {job_id}/
      ├── original.{ext}
      └── frames/
          ├── frame_001.jpg
          └── frame_002.jpg

outputs/
  └── {job_id}/
      ├── contact_sheet.png
      ├── transcription.txt
      └── analysis_result.json

data/
  └── jobs/
      └── {job_id}.json  # Job metadata and status
```

### 7.3 Implications for Database Implementation

**Technical Debt:**
- No transactional integrity for job operations
- No querying capabilities for analytics
- Manual cleanup required for job artifacts
- No support for concurrent access management

**Migration Requirements:**
- Create SQLAlchemy models mirroring file-based structure
- Migrate existing JSON metadata to database tables
- Implement unit of work pattern for job processing
- Add connection pooling and session management

---

## 8. Migration Status

### 8.1 Completed Migrations

**None.** Database schema has not been created or migrated.

### 8.2 Pending Migrations

Based on the implementation requirements:

1. **Schema Design**
   - [ ] Create SQLAlchemy models for jobs, results, assets, sessions
   - [ ] Define relationships between entities
   - [ ] Create indexes for common query patterns

2. **Migration Scripts**
   - [ ] Initialize database schema
   - [ ] Create alembic migration structure
   - [ ] Write baseline migration (v1.0)

3. **Data Migration**
   - [ ] Export existing JSON job metadata
   - [ ] Import into new database schema
   - [ ] Verify data integrity

4. **Application Updates**
   - [ ] Replace file-based operations with database operations
   - [ ] Implement repository pattern
   - [ ] Add connection management

### 8.3 Migration Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data loss during migration | HIGH | Backup existing JSON files before migration |
| Downtime during switchover | MEDIUM | Implement dual-write during transition |
| Query performance issues | MEDIUM | Add appropriate indexes and optimize queries |
| Connection pool exhaustion | LOW | Configure connection pooling properly |

---

## 9. Planned Entities/Tables

### 9.1 Inferred Entity Model

Based on file analysis and processing logic, the following entities are expected:

#### 9.1.1 Job Entity (jobs)

**Purpose:** Track media analysis job lifecycle

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,  -- 'video', 'audio', 'document'
    status VARCHAR(50) NOT NULL,    -- 'pending', 'processing', 'completed', 'failed'
    media_url TEXT NOT NULL,
    prompt TEXT,
    parameters JSONB,
    result JSONB,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    processing_time_ms INTEGER
);
```

#### 9.1.2 MediaAsset Entity (media_assets)

**Purpose:** Store processed media files and metadata

```sql
CREATE TABLE media_assets (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES jobs(id),
    asset_type VARCHAR(50) NOT NULL,  -- 'original', 'frame', 'contact_sheet', 'transcription'
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 9.1.3 Transcription Entity (transcriptions)

**Purpose:** Store audio/video transcription results

```sql
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES jobs(id),
    provider VARCHAR(50) NOT NULL,  -- 'deepgram', 'groq', 'openai', 'gemini'
    text_content TEXT NOT NULL,
    language VARCHAR(10),
    confidence_score FLOAT,
    word_timestamps JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 9.1.4 AnalysisResult Entity (analysis_results)

**Purpose:** Store LLM analysis results from MiniMax

```sql
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES jobs(id),
    analysis_type VARCHAR(50) NOT NULL,  -- 'video', 'audio', 'document'
    summary TEXT,
    detailed_analysis JSONB,
    confidence_score FLOAT,
    model_used VARCHAR(100),
    prompt_used TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 9.1.5 Session Entity (sessions)

**Purpose:** Track user sessions for analytics

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_agent TEXT,
    ip_address INET,
    created_at TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP DEFAULT NOW(),
    request_count INTEGER DEFAULT 0
);
```

### 9.2 Entity Relationships

```
jobs (1) ──────> (N) media_assets
jobs (1) ──────> (N) transcriptions
jobs (1) ──────> (N) analysis_results
sessions (1) ──────> (N) jobs
```

### 9.3 Index Strategy

**Recommended indexes:**
- `jobs.status` - Filter by status
- `jobs.created_at` - Sort by date
- `jobs.job_type` - Filter by media type
- `media_assets.job_id` - Join condition
- `transcriptions.provider` - Filter by provider
- `analysis_results.job_id` - Join condition

---

## 10. Current API Endpoints Requiring Models

### 10.1 Endpoints with Request/Response Models

| Endpoint | Method | Request Model | Response Model | Model Source |
|----------|--------|---------------|----------------|--------------|
| `/api/media/analyze` | POST | AnalyzeRequest | AnalyzeResponse | NEW (aggregator) |
| `/api/media/video` | POST | VideoRequest | VideoResponse | media_analysis.py |
| `/api/media/audio` | POST | AudioRequest | AudioResponse | media_analysis.py |
| `/api/media/documents` | POST | DocumentRequest | DocumentResponse | media_analysis.py |
| `/api/media/status` | GET | None | StatusResponse | media_analysis.py |
| `/api/media/archive` | GET | ArchiveRequest | ArchiveResponse | archive_endpoint.py |

### 10.2 Model Validation

All request/response models use **Pydantic BaseModel** with:

- `Field()` validators for constraints
- `validator()` methods for custom validation
- Type hints with `Optional[]` and `List[]`
- `model_dump()` for serialization

**No SQLAlchemy models are currently defined.**

---

## 11. Summary and Recommendations

### 11.1 Current State Summary

| Aspect | Status | Details |
|--------|--------|---------|
| **Service Implementation** | ✅ Complete | Running on port 8050 (unhealthy) |
| **API Endpoints** | ✅ 50+ migrated | All `/api/analyze/*` → `/api/media/*` |
| **Codebase** | ✅ Renamed | No `cotizador` references in target |
| **Docker** | ✅ Configured | Multi-stage build, isolated network |
| **Database** | ❌ Not Implemented | File-based persistence only |
| **Models** | ✅ Pydantic | Request/response models exist |
| **SQLAlchemy** | ❌ Not Present | No database ORM or migrations |

### 11.2 Critical Gaps

1. **Database Layer Missing**
   - No SQLAlchemy models defined
   - No database connection configured
   - No migration strategy implemented

2. **Health Check Failure**
   - Container marked unhealthy due to missing database
   - Background jobs may fail without DB connectivity

3. **Configuration Incomplete**
   - External API keys not configured
   - Caddy TLS not set up
   - Storage paths may need adjustment

### 11.3 Recommended Actions

**Immediate (Phase 1):**
1. [ ] Configure `DATABASE_URL` environment variable
2. [ ] Set all required API keys (Deepgram, MiniMax, Groq, OpenAI, Gemini)
3. [ ] Implement SQLAlchemy models for core entities
4. [ ] Create baseline database schema with Alembic
5. [ ] Update health check to not depend on database

**Short-term (Phase 2):**
1. [ ] Migrate file-based job storage to database
2. [ ] Implement repository pattern for data access
3. [ ] Add connection pooling configuration
4. [ ] Create indexes for performance optimization
5. [ ] Implement data migration scripts

**Medium-term (Phase 3):**
1. [ ] Add comprehensive error handling for database operations
2. [ ] Implement transaction management
3. [ ] Add database monitoring and logging
4. [ ] Create database backup/restore procedures
5. [ ] Performance testing and optimization

### 11.4 Technical Debt Assessment

**Current Score:** Medium-High
- File-based persistence limits scalability
- No transaction support for job processing
- Manual cleanup required for old jobs
- Limited querying capabilities for analytics

**Target Score:** Low
- Implement SQLAlchemy with proper patterns
- Add database migrations
- Implement repository and unit of work
- Add comprehensive monitoring

---

## 12. File Inventory

### 12.1 Source Files (Remote Only)

```
/opt/services/media-analysis/api/
├── __init__.py
├── media_analysis_api.py (344KB)
├── media_analysis.py
├── minimax_client.py (NEW)
├── minimax_integration.py (NEW)
├── archive_endpoint.py
├── benchmark_models.py
├── config_loader.py
├── metrics.py
├── scoring.py
├── kommo_client.py
└── jobs.py
```

### 12.2 Configuration Files

```
/opt/services/media-analysis/
├── Dockerfile
├── docker-compose.yml
├── Caddyfile
├── requirements.txt
├── config/.env
└── config/requirements.txt
```

### 12.3 Documentation Files (Local)

```
/home/oz/projects/2025/oz/12/runpod/
├── .brv/context-tree/structure/media_analysis/
│   ├── media_analysis_pipeline_overview.md
│   ├── audio_analysis_pipeline.md
│   └── video_analysis_pipeline.md
└── dev/agents/artifacts/doc/
    ├── plan/media-analysis-api-prd.md
    ├── implement-runs/20260118-media-analysis/
    │   ├── implementation-summary.md
    │   ├── activity.md
    │   └── wave2-scaffold-network.json
    └── audit/media-analysis-api-prd-pre/
```

---

**Audit Document Complete**

*Generated: 2026-01-20*
*Audit Scope: /opt/services/media-analysis/ (remote) and local repository artifacts*
*Next Review: Post-database implementation*
