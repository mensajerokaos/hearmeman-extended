# MA-22 Discovery Findings

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-20 | $USER | Initial findings from PRD analysis |

---

## PRD Analysis Summary

### Target System
- **Service**: media-analysis-api
- **Database**: af-postgres-1:5432/af-memory
- **User**: n8n
- **Network**: af-network

### Existing State
- Current persistence: File-based (JSON)
- No SQLAlchemy models defined
- No repository pattern implemented
- No connection pooling configured

### Required Components

#### 1. Database Schema
| Table | Purpose | Relationships |
|-------|---------|---------------|
| jobs | Media analysis job tracking | Parent to assets, transcriptions, results |
| media_assets | Processed media files | Child of jobs |
| transcriptions | Audio/video transcripts | Child of jobs |
| analysis_results | LLM analysis outputs | Child of jobs |

#### 2. File Structure
```
/opt/services/media-analysis/api/models/
├── __init__.py
├── base.py                    # SQLAlchemy Base class
├── database.py                # Async engine and session factory
├── job.py                     # Job model
├── media_asset.py             # MediaAsset model
├── transcription.py           # Transcription model
├── analysis_result.py         # AnalysisResult model
├── repositories/
│   ├── __init__.py
│   └── job_repository.py      # Job CRUD operations
└── schemas.py                 # Pydantic validation schemas
```

#### 3. Key Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| sqlalchemy | 2.0+ | ORM framework |
| asyncpg | 0.29+ | Async PostgreSQL driver |
| psycopg2-binary | 2.9+ | Sync driver (migrations) |
| pydantic | 2.x | Data validation |

---

## Database Configuration Details

### Connection Parameters
- **Host**: af-postgres-1
- **Port**: 5432
- **Database**: af-memory
- **User**: n8n
- **Password**: 89wdPtUBK4pn6kDPQcaM
- **Async Driver**: postgresql+asyncpg

### Pool Configuration
```python
pool_size=10
max_overflow=20
pool_pre_ping=True
pool_recycle=3600
```

### Table Specifications

#### jobs
- **Columns**: id (UUID PK), job_type, status, media_url, prompt, parameters (JSONB), result (JSONB), error, created_at, updated_at, started_at, completed_at, processing_time_ms
- **Indexes**: status, created_at DESC, job_type

#### media_assets
- **Columns**: id (UUID PK), job_id (FK), asset_type, file_path, file_size_bytes, mime_type, metadata (JSONB), created_at
- **Indexes**: job_id, asset_type

#### transcriptions
- **Columns**: id (UUID PK), job_id (FK), provider, text_content, language, confidence_score, word_timestamps (JSONB), metadata (JSONB), created_at
- **Indexes**: job_id, provider

#### analysis_results
- **Columns**: id (UUID PK), job_id (FK), analysis_type, summary, detailed_analysis (JSONB), confidence_score, model_used, prompt_used, input_tokens, output_tokens, created_at
- **Indexes**: job_id, analysis_type

---

## Integration Requirements

### API Endpoints to Update
- POST /api/media/video - Create job, store in DB
- POST /api/media/audio - Create job, store in DB
- POST /api/media/document - Create job, store in DB
- GET /api/media/status/{job_id} - Query jobs table

### Migration Strategy
1. Create SQL migration script (run once)
2. Apply migration via psql or alembic
3. Update API code to use repositories
4. Keep file-based fallback during transition

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Connection pool exhaustion | High | Monitor pool_size, implement proper cleanup |
| Migration conflicts | Medium | Run during low-traffic window |
| Model changes post-migration | High | Use alembic for future changes |
| Data loss during rollback | High | Backup before migration |

---

*Generated: 2026-01-20*
