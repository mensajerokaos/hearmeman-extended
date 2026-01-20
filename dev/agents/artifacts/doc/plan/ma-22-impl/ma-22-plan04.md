# MA-22 Implementation Plan: Database Models and Connection Layer

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-20 | $USER | Initial implementation plan |

---

## Architecture Changes

### Files to Create

| File | Purpose | Lines |
|------|---------|-------|
| `/opt/services/media-analysis/api/models/__init__.py` | Package initialization | ~15 |
| `/opt/services/media-analysis/api/models/base.py` | SQLAlchemy Base class | ~20 |
| `/opt/services/media-analysis/api/models/database.py` | Async engine and session factory | ~70 |
| `/opt/services/media-analysis/api/models/job.py` | Job model definition | ~50 |
| `/opt/services/media-analysis/api/models/media_asset.py` | MediaAsset model definition | ~45 |
| `/opt/services/media-analysis/api/models/transcription.py` | Transcription model definition | ~45 |
| `/opt/services/media-analysis/api/models/analysis_result.py` | AnalysisResult model definition | ~50 |
| `/opt/services/media-analysis/api/models/repositories/__init__.py` | Repository package init | ~10 |
| `/opt/services/media-analysis/api/models/repositories/job_repository.py` | Job CRUD operations | ~100 |
| `/opt/services/media-analysis/api/models/schemas.py` | Pydantic validation schemas | ~150 |
| `/opt/services/media-analysis/migrations/001_create_tables.sql` | SQL migration script | ~80 |
| `/opt/services/media-analysis/tests/test_database.py` | Database connection tests | ~50 |
| `/opt/services/media-analysis/tests/test_repositories.py` | Repository unit tests | ~80 |

---

## Implementation Phases

### PHASE 1: Database Schema Creation

**Objective**: Create PostgreSQL tables for media-analysis-api

**Output File**: `/opt/services/media-analysis/migrations/001_create_tables.sql`

#### Step 1.1: Create SQL Migration Script
```python
"""
File: /opt/services/media-analysis/migrations/001_create_tables.sql

Create this file with the following content:
"""

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables (if recreating)
DROP TABLE IF EXISTS analysis_results CASCADE;
DROP TABLE IF EXISTS transcriptions CASCADE;
DROP TABLE IF EXISTS media_assets CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;

-- Create jobs table
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    media_url TEXT NOT NULL,
    prompt TEXT,
    parameters JSONB DEFAULT '{}',
    result JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    processing_time_ms INTEGER
);

-- Create indexes for jobs
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_job_type ON jobs(job_type);

-- Create media_assets table
CREATE TABLE media_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE NOT NULL,
    asset_type VARCHAR(50) NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for media_assets
CREATE INDEX idx_media_assets_job_id ON media_assets(job_id);
CREATE INDEX idx_media_assets_asset_type ON media_assets(asset_type);

-- Create transcriptions table
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE NOT NULL,
    provider VARCHAR(50) NOT NULL,
    text_content TEXT NOT NULL,
    language VARCHAR(10),
    confidence_score FLOAT,
    word_timestamps JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for transcriptions
CREATE INDEX idx_transcriptions_job_id ON transcriptions(job_id);
CREATE INDEX idx_transcriptions_provider ON transcriptions(provider);

-- Create analysis_results table
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    summary TEXT,
    detailed_analysis JSONB,
    confidence_score FLOAT,
    model_used VARCHAR(100),
    prompt_used TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for analysis_results
CREATE INDEX idx_analysis_results_job_id ON analysis_results(job_id);
CREATE INDEX idx_analysis_results_type ON analysis_results(analysis_type);

-- Add comments
COMMENT ON TABLE jobs IS 'Stores all media analysis job requests and their lifecycle status';
COMMENT ON TABLE media_assets IS 'Stores processed media files and their metadata';
COMMENT ON TABLE transcriptions IS 'Stores audio/video transcription results from multiple providers';
COMMENT ON TABLE analysis_results IS 'Stores LLM analysis results from MiniMax and other vision providers';
```

**Verification Command**:
```bash
# Execute migration
ssh devmaster "psql -h af-postgres-1 -U n8n -d af-memory -f /opt/services/media-analysis/migrations/001_create_tables.sql"

# Verify tables created
ssh devmaster "psql -h af-postgres-1 -U n8n -d af-memory -c \"\\dt\""

# Expected output:
#             List of relations
#  Schema |        Name        | Type  | Owner
# --------+-------------------+-------+-------
#  public | analysis_results  | table | n8n
#  public | jobs              | table | n8n
#  public | media_assets      | table | n8n
#  public | transcriptions    | table | n8n
# (4 rows)
```

**Rollback Command**:
```bash
# Emergency rollback
ssh devmaster "psql -h af-postgres-1 -U n8n -d af-memory -c \"
DROP TABLE IF EXISTS analysis_results, transcriptions, media_assets, jobs CASCADE;
\""
```

---

### PHASE 2: Connection Layer Implementation

**Objective**: Implement async SQLAlchemy connection pool and session management

**Output Files**:
- `/opt/services/media-analysis/api/models/base.py`
- `/opt/services/media-analysis/api/models/database.py`
- `/opt/services/media-analysis/api/models/__init__.py`

#### Step 2.1: Create Base Model Class
```python
"""
File: /opt/services/media-analysis/api/models/base.py

SQLAlchemy declarative base for all models.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass
```

#### Step 2.2: Create Database Connection Layer
```python
"""
File: /opt/services/media-analysis/api/models/database.py

Async database engine and session factory configuration.
"""

import asyncio
from typing import Optional, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import os

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://n8n:89wdPtUBK4pn6kDPQcaM@af-postgres-1:5432/af-memory"
)

# Async engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_session() -> Generator[AsyncSession, None, None]:
    """
    Dependency for FastAPI endpoints.
    Yields a session and handles commit/rollback automatically.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables using SQLAlchemy metadata."""
    from models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close all database connections."""
    await engine.dispose()


async def test_connection() -> bool:
    """Test database connectivity."""
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
            return True
    except Exception:
        return False
```

#### Step 2.3: Create Package Init
```python
"""
File: /opt/services/media-analysis/api/models/__init__.py

Models package initialization.
"""

from models.base import Base
from models.database import (
    engine,
    async_session_factory,
    get_session,
    init_db,
    close_db,
    test_connection
)

__all__ = [
    "Base",
    "engine",
    "async_session_factory",
    "get_session",
    "init_db",
    "close_db",
    "test_connection"
]
```

**Verification Commands**:
```bash
# SSH to devmaster and test Python import
ssh devmaster "cd /opt/services/media-analysis && python3 -c \"
import asyncio
from api.models.database import init_db, test_connection

async def test():
    result = await test_connection()
    print(f'Connection test: {result}')
    await init_db()
    print('Database initialized')

asyncio.run(test())
\""

# Expected output:
# Connection test: True
# Database initialized
```

**Rollback Commands**:
```bash
# No rollback needed for connection layer - just don't import it
```

---

### PHASE 3: Models & Repositories

**Objective**: Define SQLAlchemy models and repository pattern

**Output Files**:
- `/opt/services/media-analysis/api/models/job.py`
- `/opt/services/media-analysis/api/models/media_asset.py`
- `/opt/services/media-analysis/api/models/transcription.py`
- `/opt/services/media-analysis/api/models/analysis_result.py`
- `/opt/services/media-analysis/api/models/repositories/job_repository.py`
- `/opt/services/media-analysis/api/models/schemas.py`

#### Step 3.1: Create Job Model
```python
"""
File: /opt/services/media-analysis/api/models/job.py

SQLAlchemy model for jobs table.
"""

from models.base import Base
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid


class Job(Base):
    """Represents a media analysis job."""
    __tablename__ = 'jobs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False, default='pending', index=True)
    media_url = Column(Text, nullable=False)
    prompt = Column(Text)
    parameters = Column(JSON, default=dict)
    result = Column(JSON)
    error = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    processing_time_ms = Column(Integer)

    # Relationships
    assets = relationship('MediaAsset', back_populates='job', cascade='all, delete-orphan')
    transcriptions = relationship('Transcription', back_populates='job', cascade='all, delete-orphan')
    analysis_results = relationship('AnalysisResult', back_populates='job', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, type={self.job_type}, status={self.status})>"
```

#### Step 3.2: Create MediaAsset Model
```python
"""
File: /opt/services/media-analysis/api/models/media_asset.py

SQLAlchemy model for media_assets table.
"""

from models.base import Base
from sqlalchemy import Column, String, BigInteger, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid


class MediaAsset(Base):
    """Represents a processed media asset."""
    __tablename__ = 'media_assets'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False, index=True)
    asset_type = Column(String(50), nullable=False, index=True)
    file_path = Column(Text, nullable=False)
    file_size_bytes = Column(BigInteger)
    mime_type = Column(String(100))
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    job = relationship('Job', back_populates='assets')

    def __repr__(self) -> str:
        return f"<MediaAsset(id={self.id}, type={self.asset_type}, job_id={self.job_id})>"
```

#### Step 3.3: Create Transcription Model
```python
"""
File: /opt/services/media-analysis/api/models/transcription.py

SQLAlchemy model for transcriptions table.
"""

from models.base import Base
from sqlalchemy import Column, String, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid


class Transcription(Base):
    """Represents a transcription result."""
    __tablename__ = 'transcriptions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    text_content = Column(Text, nullable=False)
    language = Column(String(10))
    confidence_score = Column(Float)
    word_timestamps = Column(JSON)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    job = relationship('Job', back_populates='transcriptions')

    def __repr__(self) -> str:
        return f"<Transcription(id={self.id}, provider={self.provider}, job_id={self.job_id})>"
```

#### Step 3.4: Create AnalysisResult Model
```python
"""
File: /opt/services/media-analysis/api/models/analysis_result.py

SQLAlchemy model for analysis_results table.
"""

from models.base import Base
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid


class AnalysisResult(Base):
    """Represents an LLM analysis result."""
    __tablename__ = 'analysis_results'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False, index=True)
    summary = Column(Text)
    detailed_analysis = Column(JSON)
    confidence_score = Column(Float)
    model_used = Column(String(100))
    prompt_used = Column(Text)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    job = relationship('Job', back_populates='analysis_results')

    def __repr__(self) -> str:
        return f"<AnalysisResult(id={self.id}, type={self.analysis_type}, job_id={self.job_id})>"
```

#### Step 3.5: Create Job Repository
```python
"""
File: /opt/services/media-analysis/api/models/repositories/job_repository.py

Repository pattern implementation for Job model.
"""

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.job import Job
from typing import List, Optional
from datetime import datetime
import uuid


class JobRepository:
    """Repository for Job CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, job_data: dict) -> Job:
        """Create a new job."""
        job = Job(**job_data)
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> Optional[Job]:
        """Get job by ID."""
        result = await self.session.execute(
            select(Job).where(Job.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_by_status(self, status: str, limit: int = 100) -> List[Job]:
        """Get jobs by status."""
        result = await self.session.execute(
            select(Job)
            .where(Job.status == status)
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Job]:
        """Get all jobs with pagination."""
        result = await self.session.execute(
            select(Job)
            .order_by(Job.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        job_id: uuid.UUID,
        status: str,
        error: Optional[str] = None,
        result: Optional[dict] = None,
        processing_time_ms: Optional[int] = None
    ) -> Optional[Job]:
        """Update job status with optional result/error."""
        update_values = {
            'status': status,
            'updated_at': datetime.utcnow(),
        }
        if error:
            update_values['error'] = error
        if result:
            update_values['result'] = result
        if processing_time_ms:
            update_values['processing_time_ms'] = processing_time_ms
        if status in ['completed', 'failed']:
            update_values['completed_at'] = datetime.utcnow()

        await self.session.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(**update_values)
        )
        return await self.get_by_id(job_id)

    async def start_processing(self, job_id: uuid.UUID) -> Optional[Job]:
        """Mark job as processing with start timestamp."""
        await self.session.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(
                status='processing',
                started_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        return await self.get_by_id(job_id)

    async def delete(self, job_id: uuid.UUID) -> bool:
        """Delete a job by ID."""
        result = await self.session.execute(
            delete(Job).where(Job.id == job_id)
        )
        return result.rowcount > 0

    async def count_by_status(self) -> dict:
        """Get count of jobs grouped by status."""
        result = await self.session.execute(
            select(Job.status, sqlalchemy.func.count(Job.id))
            .group_by(Job.status)
        )
        return {status: count for status, count in result.all()}
```

#### Step 3.6: Create Pydantic Schemas
```python
"""
File: /opt/services/media-analysis/api/models/schemas.py

Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class JobStatus(str, Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'


class JobType(str, Enum):
    VIDEO = 'video'
    AUDIO = 'audio'
    DOCUMENT = 'document'


class AssetType(str, Enum):
    ORIGINAL = 'original'
    FRAME = 'frame'
    CONTACT_SHEET = 'contact_sheet'
    TRANSCRIPTION = 'transcription'


# Request Schemas

class JobCreate(BaseModel):
    """Schema for creating a new job."""
    job_type: JobType
    media_url: str
    prompt: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class MediaAssetCreate(BaseModel):
    """Schema for creating a media asset."""
    job_id: uuid.UUID
    asset_type: str
    file_path: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TranscriptionCreate(BaseModel):
    """Schema for creating a transcription."""
    job_id: uuid.UUID
    provider: str
    text_content: str
    language: Optional[str] = None
    confidence_score: Optional[float] = None
    word_timestamps: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalysisResultCreate(BaseModel):
    """Schema for creating an analysis result."""
    job_id: uuid.UUID
    analysis_type: str
    summary: Optional[str] = None
    detailed_analysis: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    model_used: Optional[str] = None
    prompt_used: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


# Response Schemas

class JobResponse(BaseModel):
    """Schema for job response."""
    id: uuid.UUID
    job_type: JobType
    status: JobStatus
    media_url: str
    prompt: Optional[str]
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processing_time_ms: Optional[int]

    class Config:
        from_attributes = True


class MediaAssetResponse(BaseModel):
    """Schema for media asset response."""
    id: uuid.UUID
    job_id: uuid.UUID
    asset_type: str
    file_path: str
    file_size_bytes: Optional[int]
    mime_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TranscriptionResponse(BaseModel):
    """Schema for transcription response."""
    id: uuid.UUID
    job_id: uuid.UUID
    provider: str
    text_content: str
    language: Optional[str]
    confidence_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisResultResponse(BaseModel):
    """Schema for analysis result response."""
    id: uuid.UUID
    job_id: uuid.UUID
    analysis_type: str
    summary: Optional[str]
    confidence_score: Optional[float]
    model_used: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
```

**Verification Commands**:
```bash
# Test model imports
ssh devmaster "cd /opt/services/media-analysis && python3 -c \"
from api.models.job import Job
from api.models.media_asset import MediaAsset
from api.models.transcription import Transcription
from api.models.analysis_result import AnalysisResult
from api.models.repositories.job_repository import JobRepository
from api.models.schemas import JobCreate, JobResponse

print('All models and schemas imported successfully')
print(f'Job columns: {Job.__table__.columns.keys()}')
\""

# Expected output:
# All models and schemas imported successfully
# Job columns: ['id', 'job_type', 'status', 'media_url', 'prompt', 'parameters', 'result', 'error', 'created_at', 'updated_at', 'started_at', 'completed_at', 'processing_time_ms']
```

**Rollback Commands**:
```bash
# Remove model files
ssh devmaster "rm -f /opt/services/media-analysis/api/models/*.py"
ssh devmaster "rm -rf /opt/services/media-analysis/api/models/repositories/"
```

---

### PHASE 4: Testing & Integration

**Objective**: Create unit tests and integrate with API endpoints

**Output Files**:
- `/opt/services/media-analysis/tests/test_database.py`
- `/opt/services/media-analysis/tests/test_repositories.py`

#### Step 4.1: Create Database Tests
```python
"""
File: /opt/services/media-analysis/tests/test_database.py

Unit tests for database connection and initialization.
"""

import pytest
import asyncio
from api.models.database import init_db, close_db, test_connection, engine


@pytest.mark.asyncio
async def test_database_connection():
    """Test database connectivity."""
    result = await test_connection()
    assert result is True


@pytest.mark.asyncio
async def test_database_initialization():
    """Test database table creation."""
    await init_db()
    assert engine is not None


@pytest.mark.asyncio
async def test_database_cleanup():
    """Test database cleanup."""
    await close_db()
    # Engine should be disposed
```

#### Step 4.2: Create Repository Tests
```python
"""
File: /opt/services/media-analysis/tests/test_repositories.py

Unit tests for repository pattern.
"""

import pytest
import uuid
from api.models.database import async_session_factory
from api.models.repositories.job_repository import JobRepository
from api.models.schemas import JobCreate


@pytest.mark.asyncio
async def test_job_repository_create():
    """Test job creation via repository."""
    async with async_session_factory() as session:
        repo = JobRepository(session)
        job_data = {
            'job_type': 'video',
            'media_url': 'https://example.com/video.mp4',
            'prompt': 'Analyze this video',
            'parameters': {}
        }
        job = await repo.create(job_data)
        assert job.id is not None
        assert job.job_type == 'video'
        assert job.status == 'pending'


@pytest.mark.asyncio
async def test_job_repository_get_by_id():
    """Test getting job by ID."""
    async with async_session_factory() as session:
        repo = JobRepository(session)
        # Create a job first
        job_data = {
            'job_type': 'audio',
            'media_url': 'https://example.com/audio.mp3'
        }
        created = await repo.create(job_data)

        # Get it back
        fetched = await repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.id == created.id


@pytest.mark.asyncio
async def test_job_repository_update_status():
    """Test updating job status."""
    async with async_session_factory() as session:
        repo = JobRepository(session)
        job_data = {
            'job_type': 'document',
            'media_url': 'https://example.com/doc.pdf'
        }
        created = await repo.create(job_data)

        # Update to processing
        updated = await repo.start_processing(created.id)
        assert updated.status == 'processing'
        assert updated.started_at is not None


@pytest.mark.asyncio
async def test_job_repository_get_by_status():
    """Test getting jobs by status."""
    async with async_session_factory() as session:
        repo = JobRepository(session)
        # Create a job
        job_data = {
            'job_type': 'video',
            'media_url': 'https://example.com/video2.mp4'
        }
        await repo.create(job_data)

        # Get pending jobs
        pending = await repo.get_by_status('pending')
        assert len(pending) >= 1
```

**Verification Commands**:
```bash
# Run tests
ssh devmaster "cd /opt/services/media-analysis && python3 -m pytest tests/test_database.py -v"
ssh devmaster "cd /opt/services/media-analysis && python3 -m pytest tests/test_repositories.py -v"

# Expected output:
# test_database.py::test_database_connection PASSED
# test_database.py::test_database_initialization PASSED
# test_database.py::test_database_cleanup PASSED
# test_repositories.py::test_job_repository_create PASSED
# test_repositories.py::test_job_repository_get_by_id PASSED
# test_repositories.py::test_job_repository_update_status PASSED
# test_repositories.py::test_job_repository_get_by_status PASSED
```

**Rollback Commands**:
```bash
# Remove test files
ssh devmaster "rm -f /opt/services/media-analysis/tests/test_*.py"
```

---

## Bash Commands Summary

### Complete Implementation
```bash
# Phase 1: Create migration
ssh devmaster "mkdir -p /opt/services/media-analysis/migrations"
# Copy migration script content to /opt/services/media-analysis/migrations/001_create_tables.sql

# Execute migration
ssh devmaster "psql -h af-postgres-1 -U n8n -d af-memory -f /opt/services/media-analysis/migrations/001_create_tables.sql"

# Phase 2-3: Create models
ssh devmaster "mkdir -p /opt/services/media-analysis/api/models/repositories"
ssh devmaster "mkdir -p /opt/services/media-analysis/tests"
# Copy all model files to /opt/services/media-analysis/api/models/

# Phase 4: Run tests
ssh devmaster "cd /opt/services/media-analysis && python3 -m pytest tests/ -v"
```

---

## Emergency Rollback

### Full Rollback (Remove Everything)
```bash
# Drop all tables
ssh devmaster "psql -h af-postgres-1 -U n8n -d af-memory -c \"
DROP TABLE IF EXISTS analysis_results, transcriptions, media_assets, jobs CASCADE;
\""

# Remove all model files
ssh devmaster "rm -rf /opt/services/media-analysis/api/models/"
ssh devmaster "rm -rf /opt/services/media-analysis/migrations/"
ssh devmaster "rm -rf /opt/services/media-analysis/tests/"
```

---

## Bead Structure

Ready-to-create bead format for tracking implementation:

```json
{
  "beads": [
    {
      "id": "bd-ma22-01",
      "content": "Create SQL migration script and execute on af-postgres-1",
      "status": "pending",
      "depends_on": []
    },
    {
      "id": "bd-ma22-02",
      "content": "Create base.py and database.py connection layer",
      "status": "pending",
      "depends_on": ["bd-ma22-01"]
    },
    {
      "id": "bd-ma22-03",
      "content": "Create SQLAlchemy models (job, media_asset, transcription, analysis_result)",
      "status": "pending",
      "depends_on": ["bd-ma22-02"]
    },
    {
      "id": "bd-ma22-04",
      "content": "Create job_repository.py and Pydantic schemas",
      "status": "pending",
      "depends_on": ["bd-ma22-03"]
    },
    {
      "id": "bd-ma22-05",
      "content": "Create and run unit tests for database and repositories",
      "status": "pending",
      "depends_on": ["bd-ma22-04"]
    }
  ]
}
```

---

*Generated: 2026-01-20*
