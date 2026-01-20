# Plan: runpod-ma-epic-01 - PostgreSQL + File System Support (REFINED)

## Objective
Add persistent storage to media-analysis-api for tracking analysis history, storing media files, and enabling querying of past results.

## Version History
- **v1.0**: Initial draft
- **v1.1**: Enhanced with MiniMax feedback (error handling, security)
- **v2.0 (current)**: Production-ready with all plan02 refinements

## Scope
- Create PostgreSQL database schema in af-memory database
- Implement database models and connection layer with retry logic
- Implement file storage organization system with cleanup policies
- Integrate database with API endpoints with graceful degradation
- Update Docker Compose with PostgreSQL network configuration

## Dependencies
- **External**: af-postgres-1 service (af-memory database) must be accessible
- **Network**: media-analysis-api must join af-network for PostgreSQL connectivity
- **Secrets**: Database credentials from RunPod secrets or environment
- **Redis**: af-redis-1 for caching and rate limiting (NEW)

---

## Technical Requirements

### Database Schema (PostgreSQL - af-memory database)

```sql
-- Connection: af-postgres-1:5432, database=af-memory, user=n8n
-- Execute via Alembic migration: alembic upgrade head

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ENUM types for constrained values
CREATE TYPE media_analysis_status AS ENUM (
    'pending',
    'processing',
    'completed',
    'failed',
    'cancelled',
    'deleted'
);

CREATE TYPE media_type_enum AS ENUM (
    'video',
    'audio',
    'document',
    'image',
    'unknown'
);

-- Main requests table
CREATE TABLE media_analysis_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correlation_id UUID DEFAULT gen_random_uuid(),  -- For tracing across services
    media_url TEXT NOT NULL,
    original_filename TEXT,
    prompt TEXT NOT NULL,
    media_type media_type_enum NOT NULL DEFAULT 'unknown',
    status media_analysis_status NOT NULL DEFAULT 'pending',
    model_used VARCHAR(100),
    prompt_hash CHAR(64),  -- SHA-256 for idempotency
    latency_ms INTEGER,
    error_message TEXT,
    error_code VARCHAR(50),
    retry_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Results table with token/cost tracking
CREATE TABLE media_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES media_analysis_requests(id) ON DELETE CASCADE,
    result_text TEXT NOT NULL,
    model_used VARCHAR(100) NOT NULL,
    prompt_used TEXT,
    provider VARCHAR(50),  -- e.g., 'novita', 'google-vertex', 'openrouter'
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    latency_ms INTEGER,
    confidence_score DECIMAL(4, 3),  -- 0.000-1.000
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Media files tracking
CREATE TABLE media_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES media_analysis_requests(id) ON DELETE SET NULL,
    filename VARCHAR(255) NOT NULL,
    original_path TEXT,
    storage_path TEXT NOT NULL,
    relative_path TEXT,  -- For portability across hosts
    size_bytes BIGINT,
    mime_type VARCHAR(100),
    checksum VARCHAR(64),  -- SHA-256 hash
    retention_days INTEGER DEFAULT 30,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Contact sheets (video analysis)
CREATE TABLE contact_sheets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES media_analysis_requests(id) ON DELETE CASCADE,
    storage_path TEXT NOT NULL,
    relative_path TEXT,
    frames_count INTEGER NOT NULL,
    grid_layout VARCHAR(20) DEFAULT '2x3',
    resolution VARCHAR(20) DEFAULT '1920x1080',
    file_size_bytes BIGINT,
    checksum VARCHAR(64),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit log for tracking all changes
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL,  -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    performed_by VARCHAR(100),
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_requests_status ON media_analysis_requests(status);
CREATE INDEX idx_requests_created ON media_analysis_requests(created_at DESC);
CREATE INDEX idx_requests_correlation ON media_analysis_requests(correlation_id);
CREATE INDEX idx_requests_prompt_hash ON media_analysis_requests(prompt_hash);
CREATE INDEX idx_requests_deleted ON media_analysis_requests(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_results_request ON media_analysis_results(request_id);
CREATE INDEX idx_results_model ON media_analysis_results(model_used);
CREATE INDEX idx_files_request ON media_files(request_id);
CREATE INDEX idx_files_uploaded ON media_files(uploaded_at DESC);
CREATE INDEX idx_files_expires ON media_files(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_contact_request ON contact_sheets(request_id);
CREATE INDEX idx_audit_table ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_created ON audit_log(created_at DESC);

-- Constraints
ALTER TABLE media_analysis_requests ADD CONSTRAINT chk_retry_count CHECK (retry_count >= 0 AND retry_count <= 10);
ALTER TABLE media_analysis_results ADD CONSTRAINT chk_tokens CHECK (input_tokens >= 0 AND output_tokens >= 0);
```

### Database Connection Pool (Production-Ready)

```python
DATABASE_CONFIG = {
    # Connection pool sizing
    'min_size': 5,              # Always maintain 5 connections
    'max_size': 50,             # Scale to 50 for burst capacity
    'max_overflow': 30,         # Additional connections beyond max_size

    # Timeouts
    'pool_timeout': 30,         # Wait up to 30s for connection
    'pool_recycle': 3600,       # Recycle connections hourly
    'idle_timeout': 600,        # Close idle connections after 10min
    'command_timeout': 60,      # Query timeout

    # Retry logic
    'max_retries': 3,
    'retry_delay': 0.5,
    'retry_backoff': 2.0,

    # Health checks
    'connect_timeout': 10,
    'pool_pre_ping': True,      # Health check before use
}

# Graceful degradation modes
class DatabaseHealth:
    AVAILABLE = "available"
    DEGRADED = "degraded"  # Reads only, cache fallback
    OFFLINE = "offline"    # No DB access, use memory cache
```

### Redis Caching Layer (NEW - plan02 refinement)

```python
REDIS_CONFIG = {
    'host': 'af-redis-1',  # In af-network
    'port': 6379,
    'db': 0,
    'password': '{{RUNPOD_SECRET_redis_password}}',
    'max_connections': 50,
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
}

CACHE_TTL = {
    'request_status': 300,      # 5 minutes for status checks
    'request_result': 3600,     # 1 hour for completed results
    'history_list': 60,         # 1 minute for paginated lists
}

# Circuit breaker pattern
CIRCUIT_BREAKER = {
    'failure_threshold': 5,     # Failures before opening circuit
    'recovery_timeout': 30,     # Seconds before half-open
    'half_open_requests': 3,    # Test requests in half-open state
}
```

### File Storage Structure

```
/opt/services/media-analysis/storage/
├── uploads/                    # User-uploaded media (7d retention)
│   ├── {YYYY-MM-DD}/
│   │   ├── {request_id}/
│   │   │   ├── original.ext
│   │   │   └── metadata.json
│   └── .gitkeep
├── frames/                     # Extracted video frames (30d retention)
│   ├── {YYYY-MM-DD}/
│   │   └── {request_id}/
│   │       ├── frame_001.jpg
│   │       └── ...
│   └── .gitkeep
├── contact-sheets/             # Generated contact sheets (30d retention)
│   ├── {YYYY-MM-DD}/
│   │   └── {request_id}/
│   │       └── contact_sheet.jpg
│   └── .gitkeep
├── outputs/                    # Final analysis outputs (indefinite)
│   ├── {YYYY-MM-DD}/
│   │   └── {request_id}/
│   │       ├── result.json
│   │       └── summary.txt
│   └── .gitkeep
├── temp/                       # Temporary files (24h retention)
│   └── {request_id}/
│       ├── processing_*.tmp
│       └── ...
└── .cleanup.lock               # Prevent concurrent cleanup runs
```

---

## Implementation Strategy (5 Phases + Observability)

### Phase 1: Database Foundation
**Parallel Work Items**:
1. Execute SQL schema via Alembic migration
2. Create `api/models/database.py` with async connection pool
3. Define SQLAlchemy models with Pydantic schemas
4. Set up Redis client and circuit breaker

**NEW - Migration Setup**:
```bash
# Initialize Alembic
cd /opt/services/media-analysis
alembic init alembic
# Create initial migration: alembic revision --autogenerate -m "Initial schema"
# Apply: alembic upgrade head
```

### Phase 2: Storage System
**Independent of Phase 1**:
1. Create directory structure with proper permissions
2. Implement `storage_manager.py` with:
   - Path generation and validation
   - Retention policy enforcement
   - Cleanup job (daily cron)
3. Add disk space monitoring (warn at 80%, critical at 90%)

### Phase 3: API Integration
**Requires Phase 1 + Phase 2**:
1. Add database session to request context
2. Implement middleware for:
   - Request ID generation/forwarding
   - Database + Redis health check
   - Circuit breaker state management
   - Graceful degradation handling
3. Update endpoints:
   - `POST /api/media/analyze`: Log to DB, return correlation_id
   - `GET /api/media/status/{id}`: Query DB with cache
   - `DELETE /api/media/{id}`: Soft delete
   - `GET /api/media/history`: Paginated list with filters
   - `POST /api/media/{id}/retry`: Reset failed request

### Phase 4: Docker & Network
1. Update docker-compose.yml:
   - Add `af-network` network configuration
   - Add database health check
   - Configure volume mounts for storage
   - Set environment variables for DB + Redis connection
2. Test container health and DB connectivity

### Phase 5: Testing & Validation
1. Integration tests:
   - End-to-end request flow with DB persistence
   - Graceful degradation when DB unavailable
   - File storage and cleanup
   - Cache hit/miss behavior
   - Circuit breaker activation
2. Load tests:
   - 100 concurrent requests
   - Connection pool saturation
   - Cache effectiveness under load
3. Security tests:
   - Path traversal attempts
   - SQL injection attempts
   - Circuit breaker under DoS

### Phase 6: Observability (NEW - plan02 refinement)
**Add comprehensive monitoring**:
1. Metrics endpoints (`/metrics` for Prometheus)
2. Structured logging with correlation IDs
3. Health check endpoints (`/health`, `/health/ready`)
4. Backup procedures documentation

---

## Success Criteria

### Functional Requirements
- [ ] Database tables created via Alembic migration
- [ ] Async connection pool configured (min=5, max=50, overflow=30)
- [ ] Redis caching layer active with TTL policies
- [ ] Circuit breaker prevents cascade failures
- [ ] Storage directories created with proper permissions (755)
- [ ] All API endpoints tracking requests in database
- [ ] History endpoint returns paginated results (default 20, max 100)
- [ ] Soft delete working (records not purged, just hidden)

### Performance Requirements
- [ ] Cache hit rate > 60% for status checks
- [ ] Circuit breaker activates within 5 failures
- [ ] Recovery from circuit open within 30 seconds
- [ ] Connection pool handles 100 concurrent requests

### Reliability Requirements
- [ ] Container health check passes (database + Redis connectivity verified)
- [ ] File cleanup policies working (daily cron job)
- [ ] Disk space monitoring (alert at 80%, critical at 90%)
- [ ] Graceful degradation (cache fallback when DB unavailable)
- [ ] Backup procedures documented and tested

### Security Requirements
- [ ] Path traversal blocked
- [ ] SQL injection prevented
- [ ] Audit logging active for all mutations
- [ ] Credentials via environment variables only

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| af-network connectivity issues | High | Medium | Circuit breaker, cache fallback |
| Connection pool exhaustion | Critical | Medium | Increase max_size to 50, async driver |
| Missing migrations | Critical | High | Use Alembic with version control |
| No caching causes DB overload | High | High | Redis layer for read-heavy endpoints |
| Sync I/O blocks API | High | Medium | Migrate to async/await with asyncpg |
| File storage fills disk | High | Medium | Monitoring + automatic cleanup + alerts |
| Redis dependency failure | Medium | Low | Cache-aside with fallthrough to DB |
| Credential exposure | Critical | Low | Secrets via environment, audit logging |

---

**Created:** 2026-01-20
**Version:** 2.0
**Previous Versions:** 0.1 (Draft), 1.0 (Enhanced)
**plan02 Refinements Applied:**
- Added Alembic migration strategy
- Added async SQLAlchemy configuration
- Added Redis caching layer with TTL
- Added circuit breaker pattern
- Increased connection pool for burst capacity (50 max)
- Added comprehensive observability requirements
- Added transaction management guidance
- Enhanced risk matrix with severity ratings
