# Database Architecture Design for Media-Analysis-API

**Design Date:** 2026-01-20
**Based on:** Phase 1 (cotizador-patterns.md) + Phase 2 (media-analysis-current.md)
**Database:** PostgreSQL af-memory (n8n user)

---

## 1. Architecture Overview

### 1.1 Recommended Stack

```
Layer 1: Connection Pool
  └── asyncpg (async PostgreSQL driver)
      └── Configuration: min_size=5, max_size=20, timeout=60s

Layer 2: ORM
  └── SQLAlchemy 2.0+ with async support
      └── Core + Declarative ORM
      └── Alembic for migrations

Layer 3: Schema Validation
  └── Pydantic v2 (Input/Output/Update models)

Layer 4: Dependency Injection
  └── FastAPI Depends() for session management
```

### 1.2 Design Principles

1. **Async-First:** All database operations use async/await
2. **Connection Pooling:** Reuse connections across requests
3. **Type Safety:** SQLAlchemy ORM + Pydantic for validation
4. **Audit Trails:** Timestamps on all records
5. **Soft Deletes:** Preserve data with `deleted_at` field
6. **Transactions:** Explicit transaction boundaries
7. **Indexes:** Strategic indexes for common queries

---

## 2. asyncpg Connection Pool Configuration

### 2.1 Pool Settings

```python
# /opt/services/media-analysis/api/models/database.py

from typing import AsyncGenerator
from contextlib import asynccontextmanager
import asyncpg
import os

# Pool configuration
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "af-postgres-1"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "af-memory"),
    "user": os.getenv("DB_USER", "n8n"),
    "password": os.getenv("DB_PASSWORD", ""),
    "min_size": 5,                    # Warm connections (default: 5)
    "max_size": 20,                   # Max connections (default: 20)
    "max_inactive_connection_lifetime": 300.0,  # 5 minutes
    "command_timeout": 60.0,          # Query timeout (seconds)
    "statement_cache_size": 100,      # Prepared statements cache
    "connect_timeout": 10.0,          # Connection timeout (seconds)
}

# Global connection pool
_pool: asyncpg.Pool | None = None

async def get_pool() -> asyncpg.Pool:
    """Get or create the connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(**DATABASE_CONFIG)
    return _pool

async def close_pool() -> None:
    """Close the connection pool on shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
```

### 2.2 Connection Health Checks

```python
async def check_connection_health() -> dict:
    """Verify database connectivity and pool status."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Test query
        await conn.fetchval("SELECT 1")
        
        # Get pool status
        pool_status = {
            "size": pool.get_size(),
            "available": pool.get_idle_size(),
            "busy": pool.get_size() - pool.get_idle_size(),
        }
        
        # Get database version
        db_version = await conn.fetchval("SELECT version()")
        
        return {
            "status": "healthy",
            "pool": pool_status,
            "database": db_version,
        }
```

### 2.3 Retry Logic

```python
import asyncio
from asyncpg import PoolAcquireTimeoutError, ConnectionFailureError

async def execute_with_retry(
    query: str,
    params: tuple,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> asyncpg.Record:
    """Execute query with exponential backoff retry."""
    pool = await get_pool()
    
    for attempt in range(max_retries):
        try:
            async with pool.acquire() as conn:
                return await conn.fetchrow(query, *params)
                
        except (PoolAcquireTimeoutError, ConnectionFailureError) as e:
            if attempt == max_retries - 1:
                raise e
            
            # Exponential backoff
            wait_time = retry_delay * (2 ** attempt)
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            # Don't retry on other errors (syntax, constraint violations, etc.)
            raise e
```

---

## 3. SQLAlchemy Models

### 3.1 Base Model and Mixins

```python
# /opt/services/media-analysis/api/models/base.py

from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime, Integer, event
from sqlalchemy.orm import declarative_base, declared_attr

Base = declarative_base()

class TimestampMixin:
    """Add created_at and updated_at timestamps."""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class SoftDeleteMixin:
    """Add soft delete capability."""
    
    deleted_at = Column(DateTime, nullable=True)
    
    @declared_attr
    def is_deleted(cls) -> bool:
        """Property to check if record is soft-deleted."""
        return deferred(
            Column(Boolean, default=False, nullable=False)
        )


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """Abstract base model with common fields."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name (snake_case, plural)."""
        import re
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        return f"{name}s"  # Plural form
```

### 3.2 Media Analysis Models

```python
# /opt/services/media-analysis/api/models/media_analysis.py

from sqlalchemy import Column, String, Integer, Text, Float, JSON, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel, TimestampMixin
import uuid


class MediaType(enum.Enum):
    """Types of media that can be analyzed."""
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    IMAGE = "image"


class ProcessingStatus(enum.Enum):
    """Status of media processing jobs."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MediaFile(BaseModel, TimestampMixin):
    """
    Stores metadata about uploaded/processed media files.
    
    Replaces file-based storage in uploads/ and outputs/ directories.
    """
    
    # File identification
    session_id = Column(String(36), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    processed_filename = Column(String(255), nullable=True)
    file_path = Column(String(512), nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes
    
    # Media information
    media_type = Column(SQLEnum(MediaType), nullable=False)
    mime_type = Column(String(100), nullable=True)
    duration_seconds = Column(Float, nullable=True)  # For audio/video
    
    # Processing metadata
    extraction_method = Column(String(50), nullable=True)  # e.g., "3fps", "uniform"
    frame_count = Column(Integer, nullable=True)
    contact_sheet_path = Column(String(512), nullable=True)
    
    # Storage location
    storage_backend = Column(String(50), default="local")  # local, r2, s3
    storage_path = Column(String(512), nullable=True)
    
    # Relationships
    analysis_jobs = relationship("AnalysisJob", back_populates="media_file")
    analysis_results = relationship("AnalysisResult", back_populates="media_file")
    
    # Indexes
    __table_args__ = (
        Index("idx_media_file_session", "session_id"),
        Index("idx_media_file_type", "media_type"),
        Index("idx_media_file_created", "created_at"),
    )


class AnalysisJob(BaseModel, TimestampMixin):
    """
    Tracks background jobs for media processing.
    
    Replaces JSON-based job tracking in jobs.py.
    """
    
    # Job identification
    session_id = Column(String(36), nullable=False, index=True)
    job_type = Column(String(50), nullable=False)  # "video_analysis", "transcription", etc.
    
    # Processing status
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False)
    progress = Column(Float, default=0.0)  # 0.0 - 1.0
    
    # Job parameters (JSON)
    parameters = Column(JSON, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    media_file_id = Column(Integer, ForeignKey("media_files.id"), nullable=True)
    media_file = relationship("MediaFile", back_populates="analysis_jobs")
    results = relationship("AnalysisResult", back_populates="job")
    
    # Indexes
    __table_args__ = (
        Index("idx_job_status", "status"),
        Index("idx_job_session_type", "session_id", "job_type"),
        Index("idx_job_created", "created_at"),
    )


class AnalysisResult(BaseModel, TimestampMixin):
    """
    Stores analysis results from LLM/vision models.
    
    Replaces file-based results from metrics.py and scoring.py.
    """
    
    # Job reference
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False)
    media_file_id = Column(Integer, ForeignKey("media_files.id"), nullable=True)
    
    # Analysis metadata
    analysis_type = Column(String(50), nullable=False)  # "video", "audio", "document"
    model_used = Column(String(100), nullable=True)
    
    # Results (JSON)
    result_data = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Text outputs
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)
    
    # Frame/segment information
    frames_extracted = Column(Integer, nullable=True)
    segments = Column(JSON, nullable=True)  # Timestamps for key segments
    
    # Relationships
    job = relationship("AnalysisJob", back_populates="results")
    media_file = relationship("MediaFile", back_populates="analysis_results")
    
    # Indexes
    __table_args__ = (
        Index("idx_result_type", "analysis_type"),
        Index("idx_result_model", "model_used"),
        Index("idx_result_job", "job_id"),
    )


class UserSession(BaseModel, TimestampMixin):
    """
    Tracks user sessions for analytics and correlation.
    
    Replaces in-memory session tracking.
    """
    
    session_id = Column(String(36), unique=True, nullable=False, index=True)
    user_agent = Column(String(512), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    
    # Session lifecycle
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    
    # Usage metrics
    request_count = Column(Integer, default=0)
    media_processed_count = Column(Integer, default=0)
    
    # Relationships
    jobs = relationship("AnalysisJob", back_populates="session")
    
    # Indexes
    __table_args__ = (
        Index("idx_session_activity", "last_activity"),
        Index("idx_session_started", "started_at"),
    )


# Add relationships to TimestampMixin models
AnalysisJob.session = relationship("UserSession", back_populates="jobs")
```

### 3.3 HITL Review Models (Optional - Future)

```python
# /opt/services/media-analysis/api/models/hitl_review.py

class HITLReview(BaseModel, TimestampMixin):
    """
    Human-in-the-loop review tracking.
    
    Optional: Add if HITL workflow is implemented.
    """
    
    analysis_result_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=False)
    
    # Review status
    status = Column(String(50), default="pending")  # pending, claimed, reviewing, completed
    priority = Column(Integer, default=0)
    
    # Claim tracking
    claimed_by = Column(String(100), nullable=True)
    claimed_at = Column(DateTime, nullable=True)
    claim_expires_at = Column(DateTime, nullable=True)
    
    # Review content
    reviewer_notes = Column(Text, nullable=True)
    corrections = Column(JSON, nullable=True)
    
    # Outcome
    approved = Column(String(10), nullable=True)  # "yes", "no", "needs_changes"
    reviewed_at = Column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_hitl_status", "status"),
        Index("idx_hitl_result", "analysis_result_id"),
        Index("idx_hitl_claim", "claimed_by", "claim_expires_at"),
    )
```

---

## 4. Pydantic Schemas

### 4.1 Base Schemas

```python
# /opt/services/media-analysis/api/schemas/base.py

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field
import uuid


class TimestampSchema(BaseModel):
    """Base schema with timestamp fields."""
    created_at: datetime
    updated_at: datetime


class SoftDeleteSchema(BaseModel):
    """Schema with soft delete fields."""
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class PaginationResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int
```

### 4.2 Media File Schemas

```python
# /opt/services/media-analysis/api/schemas/media_file.py

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl
import enum


class MediaType(str, enum.Enum):
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    IMAGE = "image"


class MediaFileCreate(BaseModel):
    """Schema for creating a media file record."""
    session_id: str = Field(..., description="Session correlation ID")
    original_filename: str = Field(..., max_length=255)
    media_type: MediaType
    mime_type: Optional[str] = Field(None, max_length=100)
    file_size: Optional[int] = Field(None, ge=0)
    storage_backend: str = Field(default="local", max_length=50)


class MediaFileUpdate(BaseModel):
    """Schema for updating a media file record."""
    processed_filename: Optional[str] = Field(None, max_length=255)
    file_path: Optional[str] = Field(None, max_length=512)
    duration_seconds: Optional[float] = Field(None, ge=0)
    frame_count: Optional[int] = Field(None, ge=0)
    contact_sheet_path: Optional[str] = Field(None, max_length=512)
    storage_path: Optional[str] = Field(None, max_length=512)


class MediaFileResponse(BaseModel):
    """Schema for media file response."""
    id: int
    session_id: str
    original_filename: str
    processed_filename: Optional[str]
    file_path: Optional[str]
    file_size: Optional[int]
    media_type: MediaType
    mime_type: Optional[str]
    duration_seconds: Optional[float]
    frame_count: Optional[int]
    contact_sheet_path: Optional[str]
    storage_backend: str
    storage_path: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MediaFileListResponse(BaseModel):
    """Schema for paginated media file list."""
    items: List[MediaFileResponse]
    total: int
    page: int
    per_page: int
    pages: int
```

### 4.3 Analysis Job Schemas

```python
# /opt/services/media-analysis/api/schemas/analysis_job.py

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import enum


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisJobCreate(BaseModel):
    """Schema for creating an analysis job."""
    session_id: str = Field(..., description="Session correlation ID")
    job_type: str = Field(..., max_length=50, description="Type of analysis")
    media_file_id: Optional[int] = Field(None, description="Associated media file")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Job parameters")
    max_retries: int = Field(default=3, ge=0, le=10)


class AnalysisJobUpdate(BaseModel):
    """Schema for updating an analysis job."""
    status: Optional[ProcessingStatus] = None
    progress: Optional[float] = Field(None, ge=0.0, le=1.0)
    error_message: Optional[str] = None
    retry_count: Optional[int] = Field(None, ge=0)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AnalysisJobResponse(BaseModel):
    """Schema for analysis job response."""
    id: int
    session_id: str
    job_type: str
    status: ProcessingStatus
    progress: float
    parameters: Optional[Dict[str, Any]]
    error_message: Optional[str]
    retry_count: int
    max_retries: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    media_file_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisJobListResponse(BaseModel):
    """Schema for paginated job list."""
    items: List[AnalysisJobResponse]
    total: int
    page: int
    per_page: int
    pages: int


class JobProgressResponse(BaseModel):
    """Schema for job progress updates (SSE)."""
    job_id: int
    status: ProcessingStatus
    progress: float
    message: Optional[str] = None
```

### 4.4 Analysis Result Schemas

```python
# /opt/services/media-analysis/api/schemas/analysis_result.py

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AnalysisResultResponse(BaseModel):
    """Schema for analysis result response."""
    id: int
    job_id: int
    media_file_id: Optional[int]
    analysis_type: str
    model_used: Optional[str]
    result_data: Optional[Dict[str, Any]]
    confidence_score: Optional[float]
    transcript: Optional[str]
    summary: Optional[str]
    extracted_text: Optional[str]
    frames_extracted: Optional[int]
    segments: Optional[List[Dict[str, Any]]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisResultCreate(BaseModel):
    """Schema for creating an analysis result."""
    job_id: int
    media_file_id: Optional[int] = None
    analysis_type: str = Field(..., max_length=50)
    model_used: Optional[str] = Field(None, max_length=100)
    result_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    transcript: Optional[str] = None
    summary: Optional[str] = None
    extracted_text: Optional[str] = None
    frames_extracted: Optional[int] = None
    segments: Optional[List[Dict[str, Any]]] = None


class AnalysisResultUpdate(BaseModel):
    """Schema for updating an analysis result."""
    result_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    transcript: Optional[str] = None
    summary: Optional[str] = None
    extracted_text: Optional[str] = None
```

### 4.5 User Session Schemas

```python
# /opt/services/media-analysis/api/schemas/session.py

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class UserSessionCreate(BaseModel):
    """Schema for creating a user session."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_agent: Optional[str] = Field(None, max_length=512)
    ip_address: Optional[str] = Field(None, max_length=45)


class UserSessionUpdate(BaseModel):
    """Schema for updating a user session."""
    last_activity: Optional[datetime] = None
    request_count: Optional[int] = Field(None, ge=0)
    media_processed_count: Optional[int] = Field(None, ge=0)
    ended_at: Optional[datetime] = None


class UserSessionResponse(BaseModel):
    """Schema for user session response."""
    session_id: str
    user_agent: Optional[str]
    ip_address: Optional[str]
    started_at: datetime
    last_activity: datetime
    ended_at: Optional[datetime]
    request_count: int
    media_processed_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

---

## 5. Table Index Strategy

### 5.1 Primary Indexes (Critical)

```sql
-- Analysis jobs: Fast lookup by session and status
CREATE INDEX idx_analysis_jobs_session_status 
ON analysis_jobs(session_id, status);

-- Media files: Fast lookup by session
CREATE INDEX idx_media_files_session 
ON media_files(session_id);

-- Analysis results: Fast lookup by job
CREATE INDEX idx_analysis_results_job 
ON analysis_results(job_id);
```

### 5.2 Secondary Indexes (Common Queries)

```sql
-- Sessions: Active session cleanup
CREATE INDEX idx_user_sessions_activity 
ON user_sessions(last_activity);

-- Jobs: Queue processing order
CREATE INDEX idx_analysis_jobs_created 
ON analysis_jobs(created_at);

-- Results: Model performance analysis
CREATE INDEX idx_analysis_results_type_model 
ON analysis_results(analysis_type, model_used);
```

### 5.3 Composite Indexes (Complex Queries)

```sql
-- Dashboard: Jobs by session and time
CREATE INDEX idx_analysis_jobs_session_time 
ON analysis_jobs(session_id, created_at DESC);

-- Analytics: Results by type and confidence
CREATE INDEX idx_analysis_results_type_confidence 
ON analysis_results(analysis_type, confidence_score DESC);
```

---

## 6. Migration Strategy (Alembic)

### 6.1 Migration Directory Structure

```
/opt/services/media-analysis/
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 001_initial_schema.py
│       ├── 002_add_hitl_reviews.py
│       └── 003_add_indexes.py
```

### 6.2 Initial Migration

```python
# alembic/versions/001_initial_schema.py

"""Initial schema for media-analysis-api

Revision ID: 001
Revises: 
Create Date: 2026-01-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    op.execute("CREATE TYPE mediatype AS ENUM ('video', 'audio', 'document', 'image')")
    op.execute("CREATE TYPE processingstatus AS ENUM ('pending', 'processing', 'completed', 'failed')")
    
    # Create media_files table
    op.create_table(
        'media_files',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('processed_filename', sa.String(255), nullable=True),
        sa.Column('file_path', sa.String(512), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('media_type', sa.Enum('video', 'audio', 'document', 'image', name='mediatype'), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('extraction_method', sa.String(50), nullable=True),
        sa.Column('frame_count', sa.Integer(), nullable=True),
        sa.Column('contact_sheet_path', sa.String(512), nullable=True),
        sa.Column('storage_backend', sa.String(50), default='local'),
        sa.Column('storage_path', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_media_file_session', 'media_files', ['session_id'])
    op.create_index('idx_media_file_type', 'media_files', ['media_type'])
    op.create_index('idx_media_file_created', 'media_files', ['created_at'])
    
    # ... create other tables (analysis_jobs, analysis_results, user_sessions)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('user_sessions')
    op.drop_table('analysis_results')
    op.drop_table('analysis_jobs')
    op.drop_table('media_files')
    op.execute("DROP TYPE mediatype")
    op.execute("DROP TYPE processingstatus")
```

---

## 7. Environment Configuration

### 7.1 Required Environment Variables

```bash
# /opt/services/media-analysis/config/.env

# Database Configuration (PostgreSQL - af-memory instance)
DB_HOST=af-postgres-1
DB_PORT=5432
DB_NAME=af-memory
DB_USER=n8n
DB_PASSWORD=${RUNPOD_SECRET_DB_PASSWORD}

# Connection Pool Settings
DB_MIN_POOL_SIZE=5
DB_MAX_POOL_SIZE=20
DB_COMMAND_TIMEOUT=60
DB_CONNECT_TIMEOUT=10

# Migration Settings
ALEMBIC_CONFIG=/opt/services/media-analysis/alembic.ini
ALEMBIC_DATABASE_URL=postgresql+asyncpg://n8n:${DB_PASSWORD}@af-postgres-1:5432/af-memory
```

### 7.2 Configuration Loading

```python
# /opt/services/media-analysis/api/config.py

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Database
    DB_HOST: str = "af-postgres-1"
    DB_PORT: int = 5432
    DB_NAME: str = "af-memory"
    DB_USER: str = "n8n"
    DB_PASSWORD: str = ""
    
    # Pool settings
    DB_MIN_POOL_SIZE: int = 5
    DB_MAX_POOL_SIZE: int = 20
    DB_COMMAND_TIMEOUT: int = 60
    DB_CONNECT_TIMEOUT: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Database URL for SQLAlchemy
def get_database_url() -> str:
    """Build database URL from settings."""
    settings = get_settings()
    return (
        f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )
```

---

## 8. Performance Considerations

### 8.1 Connection Pool Sizing

| Server Type | min_size | max_size | Use Case |
|-------------|----------|----------|----------|
| Development | 5 | 10 | Testing |
| Production (1 GPU) | 5 | 20 | Standard load |
| Production (2+ GPUs) | 10 | 50 | High throughput |

### 8.2 Query Optimization

- Use `selectinload()` for relationships (N+1 prevention)
- Add indexes on foreign keys
- Use pagination for large result sets
- Avoid `SELECT *` - specify columns explicitly

### 8.3 Caching Strategy

```python
# Cache frequently accessed data (e.g., session metadata)
from redis import asyncio as aioredis

redis = aioredis.from_url("redis://localhost:6379")

async def get_session_with_cache(session_id: str) -> UserSession:
    cache_key = f"session:{session_id}"
    
    # Try cache first
    cached = await redis.get(cache_key)
    if cached:
        return UserSession(**json.loads(cached))
    
    # Fetch from database
    session = await get_session(session_id)
    
    # Cache for 5 minutes
    await redis.setex(cache_key, 300, json.dumps(session.dict()))
    
    return session
```

---

## 9. Error Handling

### 9.1 Database Exceptions

```python
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    DataError,
    TimeoutError as SQLTimeoutError,
)


class DatabaseError(Exception):
    """Base database exception."""
    pass


class NotFoundError(DatabaseError):
    """Record not found."""
    pass


class ConflictError(DatabaseError):
    """Duplicate key or constraint violation."""
    pass


async def handle_database_error(error: SQLAlchemyError) -> None:
    """Convert SQLAlchemy errors to domain exceptions."""
    if isinstance(error, IntegrityError):
        if "duplicate key" in str(error):
            raise ConflictError("Record already exists") from error
        raise DatabaseError("Constraint violation") from error
    
    elif isinstance(error, DataError):
        raise DatabaseError("Invalid data format") from error
    
    elif isinstance(error, SQLTimeoutError):
        raise DatabaseError("Query timeout") from error
    
    else:
        raise DatabaseError(f"Database error: {error}") from error
```

---

## 10. Testing Strategy

### 10.1 Unit Tests (In-Memory SQLite)

```python
# tests/unit/test_models.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.models.base import Base
from api.models.media_analysis import MediaFile


@pytest.fixture
def engine():
    return create_engine("sqlite:///:memory:")


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session()


def test_media_file_creation(session):
    media_file = MediaFile(
        session_id="test-session",
        original_filename="test.mp4",
        media_type=MediaType.VIDEO,
    )
    session.add(media_file)
    session.commit()
    
    assert media_file.id is not None
    assert media_file.created_at is not None
```

### 10.2 Integration Tests (PostgreSQL Test Container)

```python
# tests/integration/test_repository.py

import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


@pytest.fixture(scope="module")
def postgres_container():
    with PostgresContainer("postgres:15") as postgres:
        yield postgres


@pytest.fixture
async def async_engine(postgres_container):
    engine = create_async_engine(postgres_container.get_connection_url())
    yield engine
    await engine.dispose()


@pytest.mark.asyncio
async def test_media_file_repository(async_engine):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(async_engine) as session:
        media_file = MediaFile(
            session_id="test-session",
            original_filename="test.mp4",
            media_type=MediaType.VIDEO,
        )
        session.add(media_file)
        await session.commit()
        
        assert media_file.id is not None
```

---

## 11. Rollback Plan

### 11.1 Database Rollback

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 001

# Show current revision
alembic current
```

### 11.2 Code Rollback

```bash
# Revert to previous commit
git checkout HEAD~1

# Rebuild container
docker compose build media-analysis-api
docker compose up -d media-analysis-api
```

### 11.3 Data Recovery

```sql
-- Recover soft-deleted records
SELECT * FROM media_files WHERE deleted_at IS NOT NULL;

-- Restore specific record
UPDATE media_files 
SET deleted_at = NULL 
WHERE id = 123;
```

---

## 12. Estimated Lines of Code

| Component | Files | Estimated Lines |
|-----------|-------|-----------------|
| asyncpg pool | 1 | ~150 |
| SQLAlchemy models | 4 | ~400 |
| Pydantic schemas | 4 | ~500 |
| Repositories | 4 | ~300 |
| Dependencies | 1 | ~100 |
| Config | 1 | ~100 |
| Alembic migrations | 1 | ~200 |
| Tests | 6 | ~400 |
| **Total** | **22** | **~2,150** |

---

**Design completed.** Next: Generate final PRD.
