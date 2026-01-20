# PostgreSQL Database Schema - Implementation Plan

## Executive Summary
Create PostgreSQL database schema for media analysis API with tables for media items, analysis results, and processing jobs. Target: af-postgres-1:5432/af-memory database.

## Phase 1: Database Schema Creation

### Step 1.1: Create Database Migration Script
- File: /opt/services/media-analysis/database/migrations/001_initial_schema.sql
- Code:
```sql
-- Media Items Table
CREATE TABLE IF NOT EXISTS media_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    local_path TEXT,
    file_size BIGINT,
    mime_type VARCHAR(100),
    duration_seconds FLOAT,
    width INTEGER,
    height INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analysis Results Table
CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    media_item_id UUID REFERENCES media_items(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    result_data JSONB,
    error_message TEXT,
    token_usage INTEGER,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Processing Jobs Table
CREATE TABLE IF NOT EXISTS processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    media_item_id UUID REFERENCES media_items(id) ON DELETE CASCADE,
    workflow_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'queued',
    priority INTEGER DEFAULT 5,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_media_items_source_type ON media_items(source_type);
CREATE INDEX idx_media_items_created_at ON media_items(created_at DESC);
CREATE INDEX idx_analysis_results_media_id ON analysis_results(media_item_id);
CREATE INDEX idx_analysis_results_type_provider ON analysis_results(analysis_type, provider);
CREATE INDEX idx_processing_jobs_status ON processing_jobs(status);
CREATE INDEX idx_processing_jobs_priority ON processing_jobs(priority DESC);
```

### Step 1.2: Create Database Connection Pool
- File: /opt/services/media-analysis/src/db/connection.py
- Code:
```python
import asyncpg
from typing import Optional
import os

_pool: Optional[asyncpg.Pool] = None

async def init_pool():
    global _pool
    _pool = await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST", "af-postgres-1"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "af-memory"),
        user=os.getenv("POSTGRES_USER", "n8n"),
        password=os.getenv("POSTGRES_PASSWORD"),
        min_size=2,
        max_size=10
    )

async def get_pool() -> asyncpg.Pool:
    if _pool is None:
        await init_pool()
    return _pool

async def close_pool():
    if _pool:
        await _pool.close()
        _pool = None
```

## Phase 2: Model Definitions

### Step 2.1: Create SQLAlchemy Models
- File: /opt/services/media-analysis/src/db/models.py
- Code:
```python
from sqlalchemy import Column, String, Float, Integer, BigInteger, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class MediaItem(Base):
    __tablename__ = 'media_items'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_url = Column(Text, nullable=False)
    source_type = Column(String(50), nullable=False)
    local_path = Column(Text)
    file_size = Column(BigInteger)
    mime_type = Column(String(100))
    duration_seconds = Column(Float)
    width = Column(Integer)
    height = Column(Integer)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Phase 3: Repository Layer

### Step 3.1: Create Media Repository
- File: /opt/services/media-analysis/src/db/repositories/media_repository.py
- Code:
```python
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import MediaItem

class MediaRepository:
    async def create(self, session: AsyncSession, **kwargs) -> MediaItem:
        item = MediaItem(**kwargs)
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item
    
    async def get_by_id(self, session: AsyncSession, id: str) -> Optional[MediaItem]:
        result = await session.execute(
            select(MediaItem).where(MediaItem.id == id)
        )
        return result.scalar_one_or_none()
```

## Phase 4: Testing

### Step 4.1: Test Database Connection
- Bash: `cd /opt/services/media-analysis && python -c "import asyncio; asyncio.run(test_connection())"`
- Expected: "Database connection successful"

### Step 4.2: Run Migrations
- Bash: `psql -h af-postgres-1 -U n8n -d af-memory -f database/migrations/001_initial_schema.sql`
- Expected: "CREATE TABLE" messages for all 3 tables

## Rollback
- Bash: `psql -h af-postgres-1 -U n8n -d af-memory -c "DROP TABLE IF EXISTS analysis_results, processing_jobs, media_items CASCADE"`
- Verification: Tables no longer exist

## Bead Structure
| Phase | Bead Title | Parallel With | Blocked By |
|-------|------------|---------------|------------|
| 1 | [PRD] ma-21 - Database Schema | - | - |
| 2 | [PRD] ma-21 - Connection Pool | p1 | - |
| 3 | [PRD] ma-21 - Models & Repos | p2 | - |
| 4 | [PRD] ma-21 - Testing | p3 | - |
