# PostgreSQL Database Schema for media-analysis-api

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-20 | $USER | Initial schema design |

---

# Executive Summary

This document defines the PostgreSQL database schema for the media-analysis-api service. The schema supports tracking of media analysis requests across video, audio, and document processing branches, storing processing results, generated files, and contact sheets.

## Database Configuration

| Attribute | Value |
|-----------|-------|
| **Host** | af-postgres-1 |
| **Port** | 5432 |
| **Database** | af-memory |
| **User** | n8n |
| **Network** | af-network |
| **Schema** | public (default) |

## Core Tables

| Table | Purpose |
|-------|---------|
| `media_analysis_requests` | Track all analysis requests with status and metadata |
| `media_analysis_results` | Store processing results from video, audio, document branches |
| `media_files` | Reference to generated files (frames, contact sheets, transcriptions) |
| `contact_sheets` | Store contact sheet metadata and paths |

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
│                          │   Aggregator Endpoint │                          │
│                          │ POST /api/media/analyze│                         │
│                          └───────────┬───────────┘                          │
│                                      │                                      │
└──────────────────────────────────────┼──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PostgreSQL (af-postgres-1)                             │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    media_analysis_requests                            │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │ request_id (PK), media_type, status, prompt, created_at,     │   │  │
│  │  │ completed_at, processing_time_ms, confidence_score           │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  │                              │                                          │  │
│  │              ┌───────────────┴───────────────┐                        │  │
│  │              ▼                               ▼                        │  │
│  │  ┌─────────────────────────┐     ┌─────────────────────────┐         │  │
│  │  │  media_analysis_results │     │      media_files        │         │  │
│  │  │  - result_id (PK)       │     │  - file_id (PK)         │         │  │
│  │  │  - request_id (FK)      │◄────│  - request_id (FK)      │         │  │
│  │  │  - result_type          │     │  - file_type            │         │  │
│  │  │  - provider             │     │  - file_path            │         │  │
│  │  │  - content              │     │  - file_size            │         │  │
│  │  └─────────────────────────┘     └─────────────────────────┘         │  │
│  │                                      │                                  │  │
│  │                                      ▼                                  │  │
│  │                    ┌─────────────────────────────────┐                │  │
│  │                    │        contact_sheets            │                │  │
│  │                    │  - contact_sheet_id (PK)        │                │  │
│  │                    │  - request_id (FK)              │                │  │
│  │                    │  - file_id (FK)                 │                │  │
│  │                    │  - frame_count, grid_config     │                │  │
│  │                    └─────────────────────────────────┘                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# Schema Definition

## Table: media_analysis_requests

Stores all media analysis requests with processing metadata.

```sql
CREATE TABLE media_analysis_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    media_type VARCHAR(20) NOT NULL CHECK (media_type IN ('video', 'audio', 'document', 'auto')),
    status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    prompt TEXT,
    media_url TEXT,
    media_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    processing_time_ms INTEGER,
    confidence_score DECIMAL(5,4),
    error_message TEXT,
    error_details JSONB,
    user_metadata JSONB DEFAULT '{}',
    created_by VARCHAR(100),
    source_endpoint VARCHAR(100),
    provider_chain JSONB DEFAULT '[]',
    api_costs JSONB DEFAULT '{}'
);

-- Indexes for common query patterns
CREATE INDEX idx_media_requests_status ON media_analysis_requests(status);
CREATE INDEX idx_media_requests_created_at ON media_analysis_requests(created_at DESC);
CREATE INDEX idx_media_requests_media_type ON media_analysis_requests(media_type);
CREATE INDEX idx_media_requests_status_created ON media_analysis_requests(status, created_at DESC);
```

## Table: media_analysis_results

Stores processing results from various AI providers (MiniMax, Deepgram, OpenAI, etc.).

```sql
CREATE TABLE media_analysis_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES media_analysis_requests(request_id) ON DELETE CASCADE,
    result_type VARCHAR(50) NOT NULL CHECK (result_type IN (
        'transcription', 'vision_analysis', 'summary', 'classification',
        'object_detection', 'scene_detection', 'audio_analysis', 'text_analysis',
        'face_detection', 'motion_analysis', 'metadata_extraction'
    )),
    provider VARCHAR(50) NOT NULL CHECK (provider IN (
        'minimax', 'deepgram', 'groq', 'openai', 'google', 'anthropic', 'internal'
    )),
    model_name VARCHAR(100),
    content TEXT,
    content_json JSONB,
    confidence_score DECIMAL(5,4),
    processing_time_ms INTEGER,
    token_count INTEGER,
    cost_usd DECIMAL(10,6),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for result lookups
CREATE INDEX idx_results_request_id ON media_analysis_results(request_id);
CREATE INDEX idx_results_result_type ON media_analysis_results(result_type);
CREATE INDEX idx_results_provider ON media_analysis_results(provider);
CREATE INDEX idx_results_created_at ON media_analysis_results(created_at DESC);
```

## Table: media_files

References to all generated files (frames, contact sheets, audio files, documents).

```sql
CREATE TABLE media_files (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES media_analysis_requests(request_id) ON DELETE CASCADE,
    file_type VARCHAR(30) NOT NULL CHECK (file_type IN (
        'frame', 'contact_sheet', 'audio', 'transcription', 'document',
        'thumbnail', 'preview', 'original', 'processed', 'archive'
    )),
    file_path TEXT NOT NULL,
    file_name VARCHAR(255),
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    width INTEGER,
    height INTEGER,
    duration_seconds DECIMAL(10,3),
    frame_number INTEGER,
    sequence_order INTEGER,
    checksum VARCHAR(64),
    storage_location VARCHAR(50) DEFAULT 'local' CHECK (storage_location IN ('local', 'r2', 's3', 'gcs')),
    remote_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for file lookups
CREATE INDEX idx_files_request_id ON media_files(request_id);
CREATE INDEX idx_files_file_type ON media_files(file_type);
CREATE INDEX idx_files_created_at ON media_files(created_at DESC);
CREATE INDEX idx_files_mime_type ON media_files(mime_type);
```

## Table: contact_sheets

Stores contact sheet metadata and grid configurations.

```sql
CREATE TABLE contact_sheets (
    contact_sheet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES media_analysis_requests(request_id) ON DELETE CASCADE,
    file_id UUID REFERENCES media_files(file_id) ON DELETE SET NULL,
    grid_cols INTEGER NOT NULL DEFAULT 2,
    grid_rows INTEGER NOT NULL DEFAULT 3,
    frame_count INTEGER NOT NULL,
    frames_per_sheet INTEGER NOT NULL,
    sheet_number INTEGER,
    total_sheets INTEGER,
    frame_interval_seconds DECIMAL(10,3),
    image_width INTEGER,
    image_height INTEGER,
    thumbnail_width INTEGER,
    thumbnail_height INTEGER,
    generation_method VARCHAR(50) DEFAULT 'ffmpeg' CHECK (generation_method IN ('ffmpeg', 'opencv', 'custom')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for contact sheet queries
CREATE INDEX idx_contact_sheets_request_id ON contact_sheets(request_id);
CREATE INDEX idx_contact_sheets_file_id ON contact_sheets(file_id);
```

---

# Implementation Phases

## Phase 1: Database Connection Setup

**Duration**: 15 minutes
**Objective**: Configure database connection for media-analysis-api

### Tasks

#### 1.1: Create Database User (if needed)

```bash
# SSH to devmaster and create n8n user if not exists
ssh devmaster 'psql -U af -d af-memory -c "
CREATE USER n8n WITH PASSWORD '"'"'secure_password_here'"'"';
GRANT CONNECT ON DATABASE af_memory TO n8n;
GRANT USAGE ON SCHEMA public TO n8n;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO n8n;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO n8n;
"'
```

#### 1.2: Add Environment Variables

**File: /opt/services/media-analysis/config/.env**

```bash
# Database Configuration
MEDIA_ANALYSIS_DB_HOST=af-postgres-1
MEDIA_ANALYSIS_DB_PORT=5432
MEDIA_ANALYSIS_DB_NAME=af-memory
MEDIA_ANALYSIS_DB_USER=n8n
MEDIA_ANALYSIS_DB_PASSWORD=${MEDIA_ANALYSIS_DB_PASSWORD}
MEDIA_ANALYSIS_DB_POOL_SIZE=5
MEDIA_ANALYSIS_DB_MAX_OVERFLOW=10

# Async database URL (for SQLAlchemy)
DATABASE_URL=postgresql+asyncpg://n8n:${MEDIA_ANALYSIS_DB_PASSWORD}@af-postgres-1:5432/af-memory
SYNC_DATABASE_URL=postgresql://n8n:${MEDIA_ANALYSIS_DB_PASSWORD}@af-postgres-1:5432/af-memory
```

### Phase 1 Verification

```bash
# Test database connection
ssh devmaster 'PGPASSWORD=${MEDIA_ANALYSIS_DB_PASSWORD} psql -h af-postgres-1 -U n8n -d af-memory -c "SELECT 1 as test;"'

# Expected output: test column with value 1
```

---

## Phase 2: Create Database Tables

**Duration**: 30 minutes
**Objective**: Create all tables with proper indexes and constraints

### Tasks

#### 2.1: Create media_analysis_requests Table

```sql
-- SSH to devmaster and execute
ssh devmaster 'PGPASSWORD=${MEDIA_ANALYSIS_DB_PASSWORD} psql -h af-postgres-1 -U n8n -d af-memory << 'EOF'
CREATE TABLE IF NOT EXISTS media_analysis_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    media_type VARCHAR(20) NOT NULL CHECK (media_type IN ('video', 'audio', 'document', 'auto')),
    status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    prompt TEXT,
    media_url TEXT,
    media_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    processing_time_ms INTEGER,
    confidence_score DECIMAL(5,4),
    error_message TEXT,
    error_details JSONB,
    user_metadata JSONB DEFAULT '{}',
    created_by VARCHAR(100),
    source_endpoint VARCHAR(100),
    provider_chain JSONB DEFAULT '[]',
    api_costs JSONB DEFAULT '{}'
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_media_requests_status ON media_analysis_requests(status);
CREATE INDEX IF NOT EXISTS idx_media_requests_created_at ON media_analysis_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_media_requests_media_type ON media_analysis_requests(media_type);
CREATE INDEX IF NOT EXISTS idx_media_requests_status_created ON media_analysis_requests(status, created_at DESC);
EOF'
```

#### 2.2: Create media_analysis_results Table

```sql
ssh devmaster 'PGPASSWORD=${MEDIA_ANALYSIS_DB_PASSWORD} psql -h af-postgres-1 -U n8n -d af-memory << 'EOF'
CREATE TABLE IF NOT EXISTS media_analysis_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES media_analysis_requests(request_id) ON DELETE CASCADE,
    result_type VARCHAR(50) NOT NULL CHECK (result_type IN (
        'transcription', 'vision_analysis', 'summary', 'classification',
        'object_detection', 'scene_detection', 'audio_analysis', 'text_analysis',
        'face_detection', 'motion_analysis', 'metadata_extraction'
    )),
    provider VARCHAR(50) NOT NULL CHECK (provider IN (
        'minimax', 'deepgram', 'groq', 'openai', 'google', 'anthropic', 'internal'
    )),
    model_name VARCHAR(100),
    content TEXT,
    content_json JSONB,
    confidence_score DECIMAL(5,4),
    processing_time_ms INTEGER,
    token_count INTEGER,
    cost_usd DECIMAL(10,6),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_results_request_id ON media_analysis_results(request_id);
CREATE INDEX IF NOT EXISTS idx_results_result_type ON media_analysis_results(result_type);
CREATE INDEX IF NOT EXISTS idx_results_provider ON media_analysis_results(provider);
CREATE INDEX IF NOT EXISTS idx_results_created_at ON media_analysis_results(created_at DESC);
EOF'
```

#### 2.3: Create media_files Table

```sql
ssh devmaster 'PGPASSWORD=${MEDIA_ANALYSIS_DB_PASSWORD} psql -h af-postgres-1 -U n8n -d af-memory << 'EOF'
CREATE TABLE IF NOT EXISTS media_files (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES media_analysis_requests(request_id) ON DELETE CASCADE,
    file_type VARCHAR(30) NOT NULL CHECK (file_type IN (
        'frame', 'contact_sheet', 'audio', 'transcription', 'document',
        'thumbnail', 'preview', 'original', 'processed', 'archive'
    )),
    file_path TEXT NOT NULL,
    file_name VARCHAR(255),
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    width INTEGER,
    height INTEGER,
    duration_seconds DECIMAL(10,3),
    frame_number INTEGER,
    sequence_order INTEGER,
    checksum VARCHAR(64),
    storage_location VARCHAR(50) DEFAULT 'local' CHECK (storage_location IN ('local', 'r2', 's3', 'gcs')),
    remote_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_files_request_id ON media_files(request_id);
CREATE INDEX IF NOT EXISTS idx_files_file_type ON media_files(file_type);
CREATE INDEX IF NOT EXISTS idx_files_created_at ON media_files(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_files_mime_type ON media_files(mime_type);
EOF'
```

#### 2.4: Create contact_sheets Table

```sql
ssh devmaster 'PGPASSWORD=${MEDIA_ANALYSIS_DB_PASSWORD} psql -h af-postgres-1 -U n8n -d af-memory << 'EOF'
CREATE TABLE IF NOT EXISTS contact_sheets (
    contact_sheet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES media_analysis_requests(request_id) ON DELETE CASCADE,
    file_id UUID REFERENCES media_files(file_id) ON DELETE SET NULL,
    grid_cols INTEGER NOT NULL DEFAULT 2,
    grid_rows INTEGER NOT NULL DEFAULT 3,
    frame_count INTEGER NOT NULL,
    frames_per_sheet INTEGER NOT NULL,
    sheet_number INTEGER,
    total_sheets INTEGER,
    frame_interval_seconds DECIMAL(10,3),
    image_width INTEGER,
    image_height INTEGER,
    thumbnail_width INTEGER,
    thumbnail_height INTEGER,
    generation_method VARCHAR(50) DEFAULT 'ffmpeg' CHECK (generation_method IN ('ffmpeg', 'opencv', 'custom')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_contact_sheets_request_id ON contact_sheets(request_id);
CREATE INDEX IF NOT EXISTS idx_contact_sheets_file_id ON contact_sheets(file_id);
EOF'
```

### Phase 2 Verification

```bash
# Verify all tables exist
ssh devmaster 'PGPASSWORD=${MEDIA_ANALYSIS_DB_PASSWORD} psql -h af-postgres-1 -U n8n -d af-memory -c "
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;"

# Expected output:
#  contact_sheets
#  media_analysis_requests
#  media_analysis_results
#  media_files

# Verify indexes
ssh devmaster 'PGPASSWORD=${MEDIA_ANALYSIS_DB_PASSWORD} psql -h af-postgres-1 -U n8n -d af-memory -c "
SELECT indexname FROM pg_indexes WHERE tablename LIKE 'media_%' OR tablename = 'contact_sheets'
ORDER BY indexname;"

# Expected: Multiple indexes for each table
```

---

## Phase 3: Create Database Access Layer

**Duration**: 1-2 hours
**Objective**: Implement Python database models and connection management

### Tasks

#### 3.1: Create Database Configuration Module

**File: /opt/services/media-analysis/api/db/config.py**

```python
"""Database configuration and connection management."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session

# Environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://n8n:password@af-postgres-1:5432/af-memory"
)
SYNC_DATABASE_URL = os.getenv(
    "SYNC_DATABASE_URL",
    "postgresql://n8n:password@af-postgres-1:5432/af-memory"
)

# Engine configurations
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

# Session factories
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session() -> Session:
    """Get a synchronous database session."""
    return SyncSessionLocal()


@asynccontextmanager
async def async_session_context():
    """Context manager for async sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

#### 3.2: Create SQLAlchemy Models

**File: /opt/services/media-analysis/api/db/models.py**

```python
"""SQLAlchemy ORM models for media analysis database."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, Integer, BigInteger, Float, Boolean,
    DateTime, ForeignKey, CheckConstraint, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from .config import Base


class MediaAnalysisRequest(Base):
    """Model for tracking media analysis requests."""

    __tablename__ = "media_analysis_requests"

    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    media_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending"
    )
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(
        Float(precision=4), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    user_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_endpoint: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    provider_chain: Mapped[list] = mapped_column(JSONB, default=list)
    api_costs: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    results: Mapped[List["MediaAnalysisResult"]] = relationship(
        "MediaAnalysisResult", back_populates="request", cascade="all, delete-orphan"
    )
    files: Mapped[List["MediaFile"]] = relationship(
        "MediaFile", back_populates="request", cascade="all, delete-orphan"
    )
    contact_sheets: Mapped[List["ContactSheet"]] = relationship(
        "ContactSheet", back_populates="request", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("media_type IN ('video', 'audio', 'document', 'auto')", name="check_media_type"),
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')", name="check_status"),
        Index("idx_media_requests_status", "status"),
        Index("idx_media_requests_created_at", "created_at"),
        Index("idx_media_requests_media_type", "media_type"),
        Index("idx_media_requests_status_created", "status", "created_at"),
    )


class MediaAnalysisResult(Base):
    """Model for storing analysis results from AI providers."""

    __tablename__ = "media_analysis_results"

    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_analysis_requests.request_id", ondelete="CASCADE"),
        nullable=False
    )
    result_type: Mapped[str] = mapped_column(String(50), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Float(precision=4), nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[Optional[Decimal]] = mapped_column(Float(precision=6), nullable=True)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    request: Mapped["MediaAnalysisRequest"] = relationship("MediaAnalysisRequest", back_populates="results")

    __table_args__ = (
        CheckConstraint("result_type IN ('transcription', 'vision_analysis', 'summary', 'classification', 'object_detection', 'scene_detection', 'audio_analysis', 'text_analysis', 'face_detection', 'motion_analysis', 'metadata_extraction')", name="check_result_type"),
        CheckConstraint("provider IN ('minimax', 'deepgram', 'groq', 'openai', 'google', 'anthropic', 'internal')", name="check_provider"),
        Index("idx_results_request_id", "request_id"),
        Index("idx_results_result_type", "result_type"),
        Index("idx_results_provider", "provider"),
        Index("idx_results_created_at", "created_at"),
    )


class MediaFile(Base):
    """Model for referencing generated media files."""

    __tablename__ = "media_files"

    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_analysis_requests.request_id", ondelete="CASCADE"),
        nullable=False
    )
    file_type: Mapped[str] = mapped_column(String(30), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[Decimal]] = mapped_column(Float(precision=3), nullable=True)
    frame_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sequence_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    storage_location: Mapped[str] = mapped_column(String(50), default="local")
    remote_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    request: Mapped["MediaAnalysisRequest"] = relationship("MediaAnalysisRequest", back_populates="files")
    contact_sheet: Mapped[Optional["ContactSheet"]] = relationship("ContactSheet", back_populates="file", uselist=False)

    __table_args__ = (
        CheckConstraint("file_type IN ('frame', 'contact_sheet', 'audio', 'transcription', 'document', 'thumbnail', 'preview', 'original', 'processed', 'archive')", name="check_file_type"),
        CheckConstraint("storage_location IN ('local', 'r2', 's3', 'gcs')", name="check_storage_location"),
        Index("idx_files_request_id", "request_id"),
        Index("idx_files_file_type", "file_type"),
        Index("idx_files_created_at", "created_at"),
        Index("idx_files_mime_type", "mime_type"),
    )


class ContactSheet(Base):
    """Model for storing contact sheet metadata."""

    __tablename__ = "contact_sheets"

    contact_sheet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_analysis_requests.request_id", ondelete="CASCADE"),
        nullable=False
    )
    file_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_files.file_id", ondelete="SET NULL"),
        nullable=True
    )
    grid_cols: Mapped[int] = mapped_column(Integer, default=2)
    grid_rows: Mapped[int] = mapped_column(Integer, default=3)
    frame_count: Mapped[int] = mapped_column(Integer, nullable=False)
    frames_per_sheet: Mapped[int] = mapped_column(Integer, nullable=False)
    sheet_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_sheets: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    frame_interval_seconds: Mapped[Optional[Decimal]] = mapped_column(Float(precision=3), nullable=True)
    image_width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    image_height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thumbnail_width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thumbnail_height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    generation_method: Mapped[str] = mapped_column(String(50), default="ffmpeg")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    request: Mapped["MediaAnalysisRequest"] = relationship("MediaAnalysisRequest", back_populates="contact_sheets")
    file: Mapped[Optional["MediaFile"]] = relationship("MediaFile", back_populates="contact_sheet")

    __table_args__ = (
        CheckConstraint("generation_method IN ('ffmpeg', 'opencv', 'custom')", name="check_generation_method"),
        Index("idx_contact_sheets_request_id", "request_id"),
        Index("idx_contact_sheets_file_id", "file_id"),
    )
```

#### 3.3: Create Repository Layer

**File: /opt/services/media-analysis/api/db/repositories.py**

```python
"""Repository layer for database operations."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import MediaAnalysisRequest, MediaAnalysisResult, MediaFile, ContactSheet


class MediaAnalysisRepository:
    """Repository for media analysis request operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_request(
        self,
        media_type: str,
        prompt: Optional[str] = None,
        media_url: Optional[str] = None,
        media_path: Optional[str] = None,
        created_by: Optional[str] = None,
        source_endpoint: Optional[str] = None,
        user_metadata: Optional[Dict[str, Any]] = None,
    ) -> MediaAnalysisRequest:
        """Create a new analysis request."""
        request = MediaAnalysisRequest(
            media_type=media_type,
            status="pending",
            prompt=prompt,
            media_url=media_url,
            media_path=media_path,
            created_by=created_by,
            source_endpoint=source_endpoint,
            user_metadata=user_metadata or {},
        )
        self.session.add(request)
        await self.session.flush()
        return request

    async def get_request(
        self,
        request_id: uuid.UUID,
        include_relations: bool = False,
    ) -> Optional[MediaAnalysisRequest]:
        """Get a request by ID."""
        query = select(MediaAnalysisRequest).where(
            MediaAnalysisRequest.request_id == request_id
        )
        if include_relations:
            query = query.options(
                selectinload(MediaAnalysisRequest.results),
                selectinload(MediaAnalysisRequest.files),
                selectinload(MediaAnalysisRequest.contact_sheets),
            )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_request_status(
        self,
        request_id: uuid.UUID,
        status: str,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update request status."""
        await self.session.execute(
            update(MediaAnalysisRequest)
            .where(MediaAnalysisRequest.request_id == request_id)
            .values(
                status=status,
                error_message=error_message,
                error_details=error_details,
            )
        )

    async def complete_request(
        self,
        request_id: uuid.UUID,
        processing_time_ms: int,
        confidence_score: float,
        provider_chain: Optional[List[str]] = None,
        api_costs: Optional[Dict[str, float]] = None,
    ) -> None:
        """Mark request as completed."""
        await self.session.execute(
            update(MediaAnalysisRequest)
            .where(MediaAnalysisRequest.request_id == request_id)
            .values(
                status="completed",
                completed_at=datetime.utcnow(),
                processing_time_ms=processing_time_ms,
                confidence_score=confidence_score,
                provider_chain=provider_chain or [],
                api_costs=api_costs or {},
            )
        )

    async def list_requests(
        self,
        status: Optional[str] = None,
        media_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MediaAnalysisRequest]:
        """List requests with optional filters."""
        query = select(MediaAnalysisRequest).order_by(
            MediaAnalysisRequest.created_at.desc()
        )
        if status:
            query = query.where(MediaAnalysisRequest.status == status)
        if media_type:
            query = query.where(MediaAnalysisRequest.media_type == media_type)
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_requests(self) -> List[MediaAnalysisRequest]:
        """Get all pending requests."""
        query = (
            select(MediaAnalysisRequest)
            .where(MediaAnalysisRequest.status == "pending")
            .order_by(MediaAnalysisRequest.created_at)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class MediaAnalysisResultRepository:
    """Repository for media analysis result operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_result(
        self,
        request_id: uuid.UUID,
        result_type: str,
        provider: str,
        content: Optional[str] = None,
        content_json: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None,
        confidence_score: Optional[float] = None,
        processing_time_ms: Optional[int] = None,
        token_count: Optional[int] = None,
        cost_usd: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MediaAnalysisResult:
        """Create a new analysis result."""
        result = MediaAnalysisResult(
            request_id=request_id,
            result_type=result_type,
            provider=provider,
            content=content,
            content_json=content_json,
            model_name=model_name,
            confidence_score=confidence_score,
            processing_time_ms=processing_time_ms,
            token_count=token_count,
            cost_usd=cost_usd,
            metadata=metadata or {},
        )
        self.session.add(result)
        await self.session.flush()
        return result

    async def get_results_for_request(
        self,
        request_id: uuid.UUID,
    ) -> List[MediaAnalysisResult]:
        """Get all results for a request."""
        query = select(MediaAnalysisResult).where(
            MediaAnalysisResult.request_id == request_id
        ).order_by(MediaAnalysisResult.created_at)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class MediaFileRepository:
    """Repository for media file operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_file(
        self,
        request_id: uuid.UUID,
        file_type: str,
        file_path: str,
        file_name: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        mime_type: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration_seconds: Optional[float] = None,
        frame_number: Optional[int] = None,
        sequence_order: Optional[int] = None,
        checksum: Optional[str] = None,
        storage_location: str = "local",
        remote_url: Optional[str] = None,
    ) -> MediaFile:
        """Create a new media file record."""
        media_file = MediaFile(
            request_id=request_id,
            file_type=file_type,
            file_path=file_path,
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
            width=width,
            height=height,
            duration_seconds=duration_seconds,
            frame_number=frame_number,
            sequence_order=sequence_order,
            checksum=checksum,
            storage_location=storage_location,
            remote_url=remote_url,
        )
        self.session.add(media_file)
        await self.session.flush()
        return media_file

    async def get_files_for_request(
        self,
        request_id: uuid.UUID,
        file_type: Optional[str] = None,
    ) -> List[MediaFile]:
        """Get all files for a request."""
        query = select(MediaFile).where(
            MediaFile.request_id == request_id
        )
        if file_type:
            query = query.where(MediaFile.file_type == file_type)
        query = query.order_by(MediaFile.sequence_order, MediaFile.created_at)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_contact_sheets(
        self,
        request_id: uuid.UUID,
    ) -> List[MediaFile]:
        """Get all contact sheets for a request."""
        return await self.get_files_for_request(request_id, file_type="contact_sheet")


class ContactSheetRepository:
    """Repository for contact sheet operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_contact_sheet(
        self,
        request_id: uuid.UUID,
        file_id: Optional[uuid.UUID] = None,
        grid_cols: int = 2,
        grid_rows: int = 3,
        frame_count: int = 0,
        frames_per_sheet: int = 6,
        sheet_number: Optional[int] = None,
        total_sheets: Optional[int] = None,
        frame_interval_seconds: Optional[float] = None,
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
        thumbnail_width: Optional[int] = None,
        thumbnail_height: Optional[int] = None,
        generation_method: str = "ffmpeg",
    ) -> ContactSheet:
        """Create a new contact sheet record."""
        contact_sheet = ContactSheet(
            request_id=request_id,
            file_id=file_id,
            grid_cols=grid_cols,
            grid_rows=grid_rows,
            frame_count=frame_count,
            frames_per_sheet=frames_per_sheet,
            sheet_number=sheet_number,
            total_sheets=total_sheets,
            frame_interval_seconds=frame_interval_seconds,
            image_width=image_width,
            image_height=image_height,
            thumbnail_width=thumbnail_width,
            thumbnail_height=thumbnail_height,
            generation_method=generation_method,
        )
        self.session.add(contact_sheet)
        await self.session.flush()
        return contact_sheet

    async def get_contact_sheets_for_request(
        self,
        request_id: uuid.UUID,
    ) -> List[ContactSheet]:
        """Get all contact sheets for a request."""
        query = select(ContactSheet).where(
            ContactSheet.request_id == request_id
        ).order_by(ContactSheet.sheet_number)
        result = await self.session.execute(query)
        return list(result.scalars().all())
```

### Phase 3 Verification

```bash
# Verify Python syntax
ssh devmaster 'python3 -m py_compile /opt/services/media-analysis/api/db/config.py'
ssh devmaster 'python3 -m py_compile /opt/services/media-analysis/api/db/models.py'
ssh devmaster 'python3 -m py_compile /opt/services/media-analysis/api/db/repositories.py'

# Test database connection and model import
ssh devmaster 'cd /opt/services/media-analysis && python3 -c "
import asyncio
from api.db.config import async_engine
from api.db.models import Base

async def test():
    async with async_engine.connect() as conn:
        result = await conn.execute('SELECT 1')
        print('Database connection: OK')
    await async_engine.dispose()

asyncio.run(test())
"'
```

---

## Phase 4: Integrate with API Endpoints

**Duration**: 2-3 hours
**Objective**: Add database operations to existing API endpoints

### Tasks

#### 4.1: Update Main API Module

**File: /opt/services/media-analysis/api/media_analysis_api.py**

```python
# Add database session dependency
from .db.config import get_async_session, async_session_context
from .db.repositories import (
    MediaAnalysisRepository,
    MediaAnalysisResultRepository,
    MediaFileRepository,
    ContactSheetRepository,
)

# Add to router endpoints
@router.post("/video")
async def analyze_video(
    request: VideoRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Analyze video with database tracking."""
    repo = MediaAnalysisRepository(session)

    # Create request record
    media_request = await repo.create_request(
        media_type="video",
        media_url=request.video_url,
        media_path=request.video_path,
        prompt=request.prompt,
        source_endpoint="/api/media/video",
    )
    request_id = media_request.request_id

    # Process video (existing logic)
    result = await process_video(request)

    # Update with results
    await repo.complete_request(
        request_id=request_id,
        processing_time_ms=result.processing_time_ms,
        confidence_score=result.confidence_score,
    )

    return {"request_id": request_id, **result.dict()}
```

#### 4.2: Update Aggregator Endpoint

```python
@router.post("/analyze")
async def analyze_media(
    request: AnalyzeRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Natural language media analysis with full tracking."""
    repo = MediaAnalysisRepository(session)
    result_repo = MediaAnalysisResultRepository(session)
    file_repo = MediaFileRepository(session)

    # Create request
    media_request = await repo.create_request(
        media_type=request.media_type or "auto",
        media_url=request.media_url,
        media_path=request.media_path,
        prompt=request.prompt,
        source_endpoint="/api/media/analyze",
    )
    request_id = media_request.request_id

    # Process based on media type
    if request.media_type == "video":
        result = await process_video_analysis(request)
        # Save results
        await result_repo.create_result(
            request_id=request_id,
            result_type="vision_analysis",
            provider="minimax",
            content=result.analysis,
            confidence_score=result.confidence_score,
        )
    # ... similar for audio/document

    await repo.complete_request(
        request_id=request_id,
        processing_time_ms=result.processing_time_ms,
        confidence_score=result.confidence_score,
    )

    return {"request_id": request_id, "results": result}
```

### Phase 4 Verification

```bash
# Test endpoint with database
ssh devmaster 'cd /opt/services/media-analysis && \
curl -X POST http://localhost:8001/api/media/video \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://example.com/video.mp4"}' | jq '.'

# Verify request was recorded
ssh devmaster 'PGPASSWORD=${MEDIA_ANALYSIS_DB_PASSWORD} psql -h af-postgres-1 -U n8n -d af-memory -c "
SELECT request_id, media_type, status, created_at FROM media_analysis_requests ORDER BY created_at DESC LIMIT 5;"

# Verify results were recorded
ssh devmaster 'PGPASSWORD=${MEDIA_ANALYSIS_DB_PASSWORD} psql -h af-postgres-1 -U n8n -d af-memory -c "
SELECT request_id, result_type, provider, created_at FROM media_analysis_results ORDER BY created_at DESC LIMIT 5;"
```

---

## Phase 5: Add Query Endpoints

**Duration**: 1-2 hours
**Objective**: Add endpoints for querying request status and results

### Tasks

#### 5.1: Add Status Endpoint

**File: /opt/services/media-analysis/api/media_analysis_api.py**

```python
@router.get("/status/{request_id}")
async def get_request_status(
    request_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get status and results for a request."""
    repo = MediaAnalysisRepository(session)
    result_repo = MediaAnalysisResultRepository(session)
    file_repo = MediaFileRepository(session)

    request = await repo.get_request(request_id, include_relations=True)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    return {
        "request_id": request.request_id,
        "media_type": request.media_type,
        "status": request.status,
        "prompt": request.prompt,
        "processing_time_ms": request.processing_time_ms,
        "confidence_score": request.confidence_score,
        "created_at": request.created_at,
        "completed_at": request.completed_at,
        "results": [
            {
                "result_type": r.result_type,
                "provider": r.provider,
                "content": r.content,
                "confidence": r.confidence_score,
            }
            for r in request.results
        ],
        "files": [
            {
                "file_type": f.file_type,
                "file_path": f.file_path,
                "file_size_bytes": f.file_size_bytes,
            }
            for f in request.files
        ],
    }


@router.get("/requests")
async def list_requests(
    status: Optional[str] = None,
    media_type: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0),
    session: AsyncSession = Depends(get_async_session),
):
    """List requests with optional filters."""
    repo = MediaAnalysisRepository(session)
    requests = await repo.list_requests(
        status=status,
        media_type=media_type,
        limit=limit,
        offset=offset,
    )
    return {
        "requests": [
            {
                "request_id": r.request_id,
                "media_type": r.media_type,
                "status": r.status,
                "prompt": r.prompt,
                "created_at": r.created_at,
                "processing_time_ms": r.processing_time_ms,
            }
            for r in requests
        ],
        "count": len(requests),
    }
```

### Phase 5 Verification

```bash
# Test status endpoint
curl "http://localhost:8001/api/media/status/{request_id}" | jq '.'

# Test list endpoint
curl "http://localhost:8001/api/media/requests?status=completed&limit=10" | jq '.'

# Verify results
ssh devmaster 'PGPASSWORD=${MEDIA_ANALYSIS_DB_PASSWORD} psql -h af-postgres-1 -U n8n -d af-memory -c "
SELECT status, COUNT(*) FROM media_analysis_requests GROUP BY status;"
```

---

# Risk Assessment

## Risk Register

| ID | Risk | Impact | Probability | Severity | Mitigation |
|----|------|--------|-------------|----------|------------|
| R1 | Database connection failure | High | Low | High | Implement connection retry with exponential backoff |
| R2 | Query performance degradation | Medium | Medium | Medium | Use proper indexes; implement pagination |
| R3 | Data inconsistency | Medium | Low | Medium | Use database transactions; implement cascade deletes |
| R4 | Storage bloat | Low | Medium | Low | Implement cleanup job for old records |
| R5 | Concurrent request conflicts | Medium | Low | Medium | Use database locking for status updates |

## Contingency Plans

### R1: Connection Failure

```python
# Implement retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def get_session():
    try:
        return await anext(get_async_session())
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        raise
```

### R4: Storage Bloat

```sql
-- Create cleanup job
CREATE OR REPLACE FUNCTION cleanup_old_requests()
RETURNS void AS $$
BEGIN
    DELETE FROM media_analysis_requests
    WHERE created_at < NOW() - INTERVAL '30 days'
    AND status = 'completed';
END;
$$ LANGUAGE plpgsql;

-- Schedule with pg_cron (if available)
-- SELECT cron.schedule('cleanup-old-requests', '0 2 * * *', 'SELECT cleanup_old_requests();');
```

---

# Verification Commands Summary

## Database Setup Verification

```bash
# 1. Test connection
PGPASSWORD=${MEDIA_ANALYSIS_DB_PASSWORD} psql -h af-postgres-1 -U n8n -d af-memory -c "SELECT 1;"

# 2. Verify tables exist
PGPASSWORD=${MEDIA_ANALYSIS_DB_PASSWORD} psql -h af-postgres-1 -U n8n -d af-memory -c "\dt media_* contact_*"

# 3. Verify indexes
PGPASSWORD=${MEDIA_ANALYSIS_DB_PASSWORD} psql -h af-postgres-1 -U n8n -d af-memory -c "\di media_* contact_*"

# 4. Test API with database
curl -X POST http://localhost:8001/api/media/video \
  -H "Content-Type: application/json" \
  -d '{"video_url": "test.mp4"}'

# 5. Verify request was recorded
PGPASSWORD=${MEDIA_ANALYSIS_DB_PASSWORD} psql -h af-postgres-1 -U n8n -d af-memory -c "
SELECT request_id, media_type, status FROM media_analysis_requests ORDER BY created_at DESC LIMIT 3;"
```

---

# Appendix: Complete SQL Script

**File: /opt/services/media-analysis/scripts/init_db.sql**

```sql
-- PostgreSQL Database Schema for media-analysis-api
-- Execute on af-postgres-1:5432/af-memory as n8n user

-- Table: media_analysis_requests
CREATE TABLE IF NOT EXISTS media_analysis_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    media_type VARCHAR(20) NOT NULL CHECK (media_type IN ('video', 'audio', 'document', 'auto')),
    status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    prompt TEXT,
    media_url TEXT,
    media_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    processing_time_ms INTEGER,
    confidence_score DECIMAL(5,4),
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    user_metadata JSONB DEFAULT '{}',
    created_by VARCHAR(100),
    source_endpoint VARCHAR(100),
    provider_chain JSONB DEFAULT '[]',
    api_costs JSONB DEFAULT '{}'
);

-- Indexes for media_analysis_requests
CREATE INDEX IF NOT EXISTS idx_media_requests_status ON media_analysis_requests(status);
CREATE INDEX IF NOT EXISTS idx_media_requests_created_at ON media_analysis_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_media_requests_media_type ON media_analysis_requests(media_type);
CREATE INDEX IF NOT EXISTS idx_media_requests_status_created ON media_analysis_requests(status, created_at DESC);

-- Table: media_analysis_results
CREATE TABLE IF NOT EXISTS media_analysis_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES media_analysis_requests(request_id) ON DELETE CASCADE,
    result_type VARCHAR(50) NOT NULL CHECK (result_type IN ('transcription', 'vision_analysis', 'summary', 'classification', 'object_detection', 'scene_detection', 'audio_analysis', 'text_analysis', 'face_detection', 'motion_analysis', 'metadata_extraction')),
    provider VARCHAR(50) NOT NULL CHECK (provider IN ('minimax', 'deepgram', 'groq', 'openai', 'google', 'anthropic', 'internal')),
    model_name VARCHAR(100),
    content TEXT,
    content_json JSONB,
    confidence_score DECIMAL(5,4),
    processing_time_ms INTEGER,
    token_count INTEGER,
    cost_usd DECIMAL(10,6),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for media_analysis_results
CREATE INDEX IF NOT EXISTS idx_results_request_id ON media_analysis_results(request_id);
CREATE INDEX IF NOT EXISTS idx_results_result_type ON media_analysis_results(result_type);
CREATE INDEX IF NOT EXISTS idx_results_provider ON media_analysis_results(provider);
CREATE INDEX IF NOT EXISTS idx_results_created_at ON media_analysis_results(created_at DESC);

-- Table: media_files
CREATE TABLE IF NOT EXISTS media_files (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES media_analysis_requests(request_id) ON DELETE CASCADE,
    file_type VARCHAR(30) NOT NULL CHECK (file_type IN ('frame', 'contact_sheet', 'audio', 'transcription', 'document', 'thumbnail', 'preview', 'original', 'processed', 'archive')),
    file_path TEXT NOT NULL,
    file_name VARCHAR(255),
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    width INTEGER,
    height INTEGER,
    duration_seconds DECIMAL(10,3),
    frame_number INTEGER,
    sequence_order INTEGER,
    checksum VARCHAR(64),
    storage_location VARCHAR(50) DEFAULT 'local' CHECK (storage_location IN ('local', 'r2', 's3', 'gcs')),
    remote_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for media_files
CREATE INDEX IF NOT EXISTS idx_files_request_id ON media_files(request_id);
CREATE INDEX IF NOT EXISTS idx_files_file_type ON media_files(file_type);
CREATE INDEX IF NOT EXISTS idx_files_created_at ON media_files(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_files_mime_type ON media_files(mime_type);

-- Table: contact_sheets
CREATE TABLE IF NOT EXISTS contact_sheets (
    contact_sheet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES media_analysis_requests(request_id) ON DELETE CASCADE,
    file_id UUID REFERENCES media_files(file_id) ON DELETE SET NULL,
    grid_cols INTEGER NOT NULL DEFAULT 2,
    grid_rows INTEGER NOT NULL DEFAULT 3,
    frame_count INTEGER NOT NULL,
    frames_per_sheet INTEGER NOT NULL,
    sheet_number INTEGER,
    total_sheets INTEGER,
    frame_interval_seconds DECIMAL(10,3),
    image_width INTEGER,
    image_height INTEGER,
    thumbnail_width INTEGER,
    thumbnail_height INTEGER,
    generation_method VARCHAR(50) DEFAULT 'ffmpeg' CHECK (generation_method IN ('ffmpeg', 'opencv', 'custom')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for contact_sheets
CREATE INDEX IF NOT EXISTS idx_contact_sheets_request_id ON contact_sheets(request_id);
CREATE INDEX IF NOT EXISTS idx_contact_sheets_file_id ON contact_sheets(file_id);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO n8n;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO n8n;
```

---

**Document End**

**PRD Version:** 1.0
**Created:** 2026-01-20
**Author:** $USER
**Model:** claude-sonnet-4-5-20250929
