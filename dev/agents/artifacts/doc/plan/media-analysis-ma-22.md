# Database Models and Connection Layer for media-analysis-api

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-20 | $USER | Initial database models design |

---

# Executive Summary

This document defines the database models and connection layer for the media-analysis-api service. Based on the current state audit, the service currently uses file-based persistence with no SQLAlchemy models defined. This PRD outlines the implementation of a complete database layer including connection pooling, SQLAlchemy models, Pydantic schemas, and repository pattern for data access.

## Database Configuration

| Attribute | Value |
|-----------|-------|
| **Host** | af-postgres-1 |
| **Port** | 5432 |
| **Database** | af-memory |
| **User** | n8n |
| **Network** | af-network |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Pool** | asyncpg connection pool |

---

# System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         media-analysis-api                                   │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │   Video Branch      │  │   Audio Branch      │  │   Document Branch   │ │
│  │  /api/media/video   │  │  /api/media/audio   │  │ /api/media/document │ │
│  └──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘ │
│             │                        │                        │             │
│             └────────────────────────┼────────────────────────┘             │
│                                      │                                      │
│                          ┌───────────┴───────────┐                          │
│                          │   Repository Layer    │                          │
│                          │  - JobRepository      │                          │
│                          │  - ResultRepository   │                          │
│                          │  - AssetRepository    │                          │
│                          └───────────┬───────────┘                          │
│                                      │                                      │
│                          ┌───────────┴───────────┐                          │
│                          │   Database Models     │                          │
│                          │  - SQLAlchemy Models  │                          │
│                          └───────────┬───────────┘                          │
│                                      │                                      │
└──────────────────────────────────────┼──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PostgreSQL (af-postgres-1)                             │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                           jobs                                        │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │ id (PK), job_type, status, media_url, prompt, parameters,    │   │  │
│  │  │ result, error, created_at, updated_at, started_at, completed │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  │                              │                                        │  │
│  │              ┌───────────────┴───────────────┐                      │  │
│  │              ▼                               ▼                      │  │
│  │  ┌─────────────────────────┐     ┌─────────────────────────┐       │  │
│  │  │  media_assets           │     │  analysis_results       │       │  │
│  │  │  - id (PK)              │     │  - id (PK)              │       │  │
│  │  │  - job_id (FK)          │     │  - job_id (FK)          │       │  │
│  │  │  - asset_type           │     │  - analysis_type        │       │  │
│  │  │  - file_path            │     │  - summary              │       │  │
│  │  │  - file_size            │     │  - detailed_analysis    │       │  │
│  │  └─────────────────────────┘     └─────────────────────────┘       │  │
│  │                                                                              │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │  │
│  │  │                      transcriptions                              │  │  │
│  │  │  ┌───────────────────────────────────────────────────────────┐  │  │  │
│  │  │  │ id (PK), job_id (FK), provider, text_content, language,  │  │  │  │
│  │  │  │ confidence_score, word_timestamps, created_at             │  │  │  │
│  │  │  └───────────────────────────────────────────────────────────┘  │  │  │
│  │  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# Database Models

## Table: jobs

Stores all media analysis job requests and their lifecycle status.

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(50) NOT NULL,  -- 'video', 'audio', 'document'
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
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

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_job_type ON jobs(job_type);
```

## Table: media_assets

Stores processed media files and their metadata.

```sql
CREATE TABLE media_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    asset_type VARCHAR(50) NOT NULL,  -- 'original', 'frame', 'contact_sheet', 'transcription'
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_media_assets_job_id ON media_assets(job_id);
CREATE INDEX idx_media_assets_asset_type ON media_assets(asset_type);
```

## Table: transcriptions

Stores audio/video transcription results from multiple providers.

```sql
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,  -- 'deepgram', 'groq', 'openai', 'gemini'
    text_content TEXT NOT NULL,
    language VARCHAR(10),
    confidence_score FLOAT,
    word_timestamps JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_transcriptions_job_id ON transcriptions(job_id);
CREATE INDEX idx_transcriptions_provider ON transcriptions(provider);
```

## Table: analysis_results

Stores LLM analysis results from MiniMax and other vision providers.

```sql
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,  -- 'video', 'audio', 'document'
    summary TEXT,
    detailed_analysis JSONB,
    confidence_score FLOAT,
    model_used VARCHAR(100),
    prompt_used TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_analysis_results_job_id ON analysis_results(job_id);
CREATE INDEX idx_analysis_results_type ON analysis_results(analysis_type);
```

---

# SQLAlchemy Models

## Core Model Structure

```python
# File: /opt/services/media-analysis/api/models/base.py
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, String, Integer, BigInteger, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

class Base(DeclarativeBase):
    pass

# File: /opt/services/media-analysis/api/models/job.py
from .base import Base
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

class Job(Base):
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

# File: /opt/services/media-analysis/api/models/media_asset.py
from .base import Base
from sqlalchemy import Column, String, BigInteger, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

class MediaAsset(Base):
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

# File: /opt/services/media-analysis/api/models/transcription.py
from .base import Base
from sqlalchemy import Column, String, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

class Transcription(Base):
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

# File: /opt/services/media-analysis/api/models/analysis_result.py
from .base import Base
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

class AnalysisResult(Base):
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
```

---

# Connection Layer

## Async Connection Pool

```python
# File: /opt/services/media-analysis/api/models/database.py
import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import os

# Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://n8n:89wdPtUBK4pn6kDPQcaM@af-postgres-1:5432/af-memory"
)

# Engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
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

async def get_session() -> AsyncSession:
    """Dependency for FastAPI endpoints."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """Close database connections."""
    await engine.dispose()
```

---

# Repository Pattern

```python
# File: /opt/services/media-analysis/api/models/repositories/job_repository.py
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from models.job import Job
from typing import List, Optional
from datetime import datetime
import uuid

class JobRepository:
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

    async def update_status(
        self,
        job_id: uuid.UUID,
        status: str,
        error: Optional[str] = None,
        result: Optional[dict] = None
    ) -> Optional[Job]:
        """Update job status."""
        await self.session.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(
                status=status,
                error=error,
                result=result,
                updated_at=datetime.utcnow(),
                completed_at=datetime.utcnow() if status in ['completed', 'failed'] else None
            )
        )
        return await self.get_by_id(job_id)

    async def start_processing(self, job_id: uuid.UUID) -> Optional[Job]:
        """Mark job as processing."""
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
```

---

# Pydantic Schemas

```python
# File: /opt/services/media-analysis/api/models/schemas.py
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

class JobCreate(BaseModel):
    job_type: JobType
    media_url: str
    prompt: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

class JobResponse(BaseModel):
    id: uuid.UUID
    job_type: JobType
    status: JobStatus
    media_url: str
    prompt: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processing_time_ms: Optional[int]
    error: Optional[str]

    class Config:
        from_attributes = True

class MediaAssetCreate(BaseModel):
    job_id: uuid.UUID
    asset_type: str
    file_path: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MediaAssetResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    asset_type: str
    file_path: str
    file_size_bytes: Optional[int]
    mime_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class TranscriptionCreate(BaseModel):
    job_id: uuid.UUID
    provider: str
    text_content: str
    language: Optional[str] = None
    confidence_score: Optional[float] = None
    word_timestamps: Optional[Dict[str, Any]] = None

class TranscriptionResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    provider: str
    text_content: str
    language: Optional[str]
    confidence_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True

class AnalysisResultCreate(BaseModel):
    job_id: uuid.UUID
    analysis_type: str
    summary: Optional[str] = None
    detailed_analysis: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    model_used: Optional[str] = None
    prompt_used: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None

class AnalysisResultResponse(BaseModel):
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

---

# Implementation Plan

## Phase 1: Database Schema

1. Create SQL migration script
2. Define all table schemas
3. Create indexes for query optimization

## Phase 2: Connection Layer

1. Implement async connection pool
2. Create session factory
3. Add health check integration

## Phase 3: Models & Repositories

1. Define SQLAlchemy models
2. Implement repository pattern
3. Add Pydantic schemas

## Phase 4: Integration

1. Update API endpoints to use repositories
2. Replace file-based operations with database
3. Add transaction management

---

# Verification

## Unit Tests

```python
# test_database.py
import pytest
from api.models.database import init_db, close_db, engine

@pytest.mark.asyncio
async def test_database_connection():
    """Test database connectivity."""
    await init_db()
    assert engine is not None
    await close_db()

@pytest.mark.asyncio
async def test_job_repository():
    """Test job repository operations."""
    from api.models.repositories.job_repository import JobRepository
    from api.models.schemas import JobCreate

    # Test create
    repo = JobRepository(session)
    job_data = JobCreate(
        job_type='video',
        media_url='https://example.com/video.mp4',
        prompt='Analyze this video'
    )
    job = await repo.create(job_data.model_dump())
    assert job.id is not None
```

---

# Rollback

```bash
# Emergency rollback: Drop all tables
psql -h af-postgres-1 -U n8n -d af-memory -c "
DROP TABLE IF EXISTS analysis_results, transcriptions, media_assets, jobs CASCADE;
"
```

---

# Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| sqlalchemy | 2.0+ | ORM framework |
| asyncpg | 0.29+ | Async PostgreSQL driver |
| psycopg2-binary | 2.9+ | Sync PostgreSQL driver (for migrations) |
| alembic | 1.13+ | Migration tool |

---

**Document Version:** 1.0
**Created:** 2026-01-20
**Author:** Claude Code (Post-compaction handoff - ma-22 manual creation)
