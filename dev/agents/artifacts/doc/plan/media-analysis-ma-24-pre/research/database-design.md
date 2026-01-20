# Database Design: Media Analysis API

**Date**: 2026-01-20
**Task**: Database Integration PRD Research - Phase 2
**Output**: /home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-24-pre/research/database-design.md

---

## 1. Table Schema

### analysis_request

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| id | UUID | PRIMARY KEY | `gen_random_uuid()` | Unique analysis identifier |
| status | VARCHAR(20) | NOT NULL, CHECK | `'pending'` | Request status (pending/processing/completed/failed/deleted) |
| media_type | VARCHAR(50) | NOT NULL | - | Media type (video/audio/document) |
| source_url | TEXT | NOT NULL | - | Original media URL |
| filename | VARCHAR(500) | NULL | - | Original filename if uploaded |
| analysis_config | JSONB | NULL | - | Configuration parameters |
| analysis_options | JSONB | NULL | - | Processing options |
| results | JSONB | NULL | - | Analysis results |
| progress | INTEGER | NOT NULL | `0` | Progress percentage (0-100) |
| error_message | TEXT | NULL | - | Error details if failed |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL | `NOW()` | Request creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL | `NOW()` | Last update timestamp |
| completed_at | TIMESTAMP WITH TIME ZONE | NULL | - | Completion timestamp |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULL | - | Soft delete timestamp |
| created_by | UUID | NULL | - | User ID (for multi-tenant) |
| celery_task_id | VARCHAR(255) | NULL | - | Celery task reference |

---

## 2. Complete SQL

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
    celery_task_id VARCHAR(255),
    CONSTRAINT valid_status_transition CHECK (
        (status = 'pending' AND completed_at IS NULL) OR
        (status = 'processing' AND completed_at IS NULL) OR
        (status = 'completed' AND completed_at IS NOT NULL) OR
        (status = 'failed' AND completed_at IS NOT NULL) OR
        (status = 'deleted' AND deleted_at IS NOT NULL)
    )
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

-- Comments for documentation
COMMENT ON TABLE analysis_request IS 'Stores media analysis requests and results';
COMMENT ON COLUMN analysis_request.status IS 'Request lifecycle: pending -> processing -> completed|failed. deleted for soft delete.';
COMMENT ON COLUMN analysis_request.progress IS 'Processing progress 0-100 percentage';
COMMENT ON COLUMN analysis_request.analysis_config IS 'LLM and processing configuration parameters';
COMMENT ON COLUMN analysis_request.analysis_options IS 'User-specified processing options';
COMMENT ON COLUMN analysis_request.results IS 'Analysis output from LLMs and processors';
COMMENT ON COLUMN analysis_request.celery_task_id IS 'Reference to Celery task for async processing';
```

---

## 3. Index Strategy

| Index | Columns | Type | Purpose | Query Pattern |
|-------|---------|------|---------|---------------|
| idx_analysis_request_status_active | status | BTREE | Filter active requests | `WHERE status != 'deleted'` |
| idx_analysis_request_created_at | created_at DESC | BTREE | Sort by date | `ORDER BY created_at DESC` |
| idx_analysis_request_status_created | status, created_at DESC | BTREE | Filter + sort | `WHERE status != 'deleted' ORDER BY created_at DESC` |
| idx_analysis_request_created_by | created_by, created_at DESC | BTREE | User queries | `WHERE created_by = ? ORDER BY created_at DESC` |
| idx_analysis_request_celery_task | celery_task_id | BTREE | Task lookup | `WHERE celery_task_id = ?` |
| idx_analysis_request_media_type | media_type | BTREE | Type filter | `WHERE media_type = ? AND status != 'deleted'` |

### Index Rationale

1. **Status Index with WHERE clause**: Filters deleted records by default, improves query performance
2. **Composite Index**: Covers both filtering and sorting for history endpoint
3. **User Index**: Supports multi-tenant isolation (optional)
4. **Task Index**: Enables Celery task tracking

### Partial Index Benefits

- Smaller index size (excludes deleted records)
- Faster queries (less data to scan)
- Automatic maintenance (no deleted records in index)

---

## 4. Migration Approach

### Tool: Alembic

**Why Alembic?**
- Industry standard for SQLAlchemy migrations
- Auto-generation from model changes
- Version control for schema changes
- Downgrade capability

### Migration Steps

```bash
# 1. Initialize Alembic (if not done)
cd /opt/services/media-analysis
alembic init alembic

# 2. Create migration script
alembic revision --autogenerate -m "Create analysis_request table"

# 3. Review generated migration
cat alembic/versions/xxx_create_analysis_request.py

# 4. Apply migration
alembic upgrade head

# 5. Verify table exists
psql -d media_analysis -c "\d analysis_request"

# 6. Test downgrade
alembic downgrade -1
```

### Generated Migration File (example)

```python
"""Create analysis_request table

Revision ID: abc123
Revises:
Create Date: 2026-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'abc123'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create table
    op.create_table(
        'analysis_request',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('media_type', sa.String(50), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('filename', sa.String(500), nullable=True),
        sa.Column('analysis_config', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('analysis_options', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('results', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('deleted_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('celery_task_id', sa.String(255), nullable=True),
        sa.CheckConstraint('status IN (\'pending\', \'processing\', \'completed\', \'failed\', \'deleted\')', name='valid_status'),
        sa.CheckConstraint('media_type IN (\'video\', \'audio\', \'document\', \'image\', \'unknown\')', name='valid_media_type'),
        sa.CheckConstraint('progress >= 0 AND progress <= 100', name='valid_progress'),
    )

    # Create indexes
    op.create_index('idx_analysis_request_status_active', 'analysis_request', ['status'], postgresql_where=(status != 'deleted'))
    op.create_index('idx_analysis_request_created_at', 'analysis_request', ['created_at'], postgresql_where=(status != 'deleted'))
    op.create_index('idx_analysis_request_status_created', 'analysis_request', ['status', 'created_at'], postgresql_where=(status != 'deleted'))
    op.create_index('idx_analysis_request_created_by', 'analysis_request', ['created_by', 'created_at'], postgresql_where=(created_by IS NOT NULL))

def downgrade() -> None:
    op.drop_index('idx_analysis_request_created_by', table_name='analysis_request')
    op.drop_index('idx_analysis_request_status_created', table_name='analysis_request')
    op.drop_index('idx_analysis_request_created_at', table_name='analysis_request')
    op.drop_index('idx_analysis_request_status_active', table_name='analysis_request')
    op.drop_table('analysis_request')
```

### Zero-Downtime Migration Strategy

1. **Backup First**
   ```bash
   pg_dump -d media_analysis > backup_pre_migration.sql
   ```

2. **Create Table (No constraints initially)**
   ```python
   # First migration: create table without constraints
   op.create_table('analysis_request', ...)
   # No FK constraints, no CHECK constraints
   ```

3. **Add Constraints in Second Migration**
   ```python
   # Second migration: add constraints after data validation
   op.create_check_constraint(...)
   op.create_foreign_key(...)
   ```

4. **Online Schema Change**
   - Use `CREATE INDEX CONCURRENTLY` for production
   - Avoid `ALTER TABLE ... SET NOT NULL` on large tables during peak hours
   - Schedule migration during low-traffic period

---

## 5. Model Implementation (SQLAlchemy)

### File: /opt/services/media-analysis/models/analysis_request.py

```python
"""
SQLAlchemy model for analysis_request table.

Table: analysis_request
Purpose: Stores media analysis requests and results
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    CheckConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase

from app.core.database import Base


class AnalysisRequest(Base):
    """
    SQLAlchemy model for media analysis requests.

    Lifecycle: pending -> processing -> completed|failed
    Soft delete: deleted status with deleted_at timestamp
    """
    __tablename__ = 'analysis_request'

    # Primary key
    id: UUID = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Status tracking
    status: str = Column(
        String(20),
        nullable=False,
        default='pending',
        doc='Request lifecycle status'
    )
    progress: int = Column(
        Integer,
        nullable=False,
        default=0,
        doc='Processing progress 0-100'
    )

    # Media metadata
    media_type: str = Column(
        String(50),
        nullable=False,
        doc='Media type: video/audio/document/image'
    )
    source_url: str = Column(
        Text,
        nullable=False,
        doc='Original media URL'
    )
    filename: Optional[str] = Column(
        String(500),
        nullable=True,
        doc='Original filename if uploaded'
    )

    # Configuration and results (JSONB for flexibility)
    analysis_config: dict = Column(
        JSONB,
        nullable=False,
        default=dict,
        doc='LLM and processing configuration'
    )
    analysis_options: dict = Column(
        JSONB,
        nullable=False,
        default=dict,
        doc='User-specified processing options'
    )
    results: dict = Column(
        JSONB,
        nullable=False,
        default=dict,
        doc='Analysis results from LLMs and processors'
    )

    # Error tracking
    error_message: Optional[str] = Column(
        Text,
        nullable=True,
        doc='Error details if failed'
    )

    # Timestamps
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc='Request creation timestamp'
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc='Last update timestamp'
    )
    completed_at: Optional[datetime] = Column(
        DateTime(timezone=True),
        nullable=True,
        doc='Completion timestamp'
    )
    deleted_at: Optional[datetime] = Column(
        DateTime(timezone=True),
        nullable=True,
        doc='Soft delete timestamp'
    )

    # Multi-tenant support
    created_by: Optional[UUID] = Column(
        UUID(as_uuid=True),
        nullable=True,
        doc='User ID for multi-tenant isolation'
    )

    # Async task reference
    celery_task_id: Optional[str] = Column(
        String(255),
        nullable=True,
        doc='Celery task ID for async processing'
    )

    # Constraints
    __table_args__ = (
        # Status values
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'deleted')",
            name='valid_status'
        ),
        # Media type values
        CheckConstraint(
            "media_type IN ('video', 'audio', 'document', 'image', 'unknown')",
            name='valid_media_type'
        ),
        # Progress range
        CheckConstraint(
            'progress >= 0 AND progress <= 100',
            name='valid_progress'
        ),
        # Partial indexes for performance
        Index(
            'idx_analysis_request_status_active',
            'status',
            postgresql_where=(status != 'deleted')
        ),
        Index(
            'idx_analysis_request_created_at',
            'created_at',
            postgresql_where=(status != 'deleted')
        ),
        Index(
            'idx_analysis_request_status_created',
            'status',
            'created_at',
            postgresql_where=(status != 'deleted')
        ),
        Index(
            'idx_analysis_request_created_by',
            'created_by',
            'created_at',
            postgresql_where=(created_by IS NOT NULL)
        ),
    )

    # Status constants
    class Status:
        PENDING = 'pending'
        PROCESSING = 'processing'
        COMPLETED = 'completed'
        FAILED = 'failed'
        DELETED = 'deleted'

    # Media type constants
    class MediaType:
        VIDEO = 'video'
        AUDIO = 'audio'
        DOCUMENT = 'document'
        IMAGE = 'image'
        UNKNOWN = 'unknown'

    def __repr__(self) -> str:
        return f'<AnalysisRequest(id={self.id}, status={self.status}, media_type={self.media_type})>'

    @property
    def is_active(self) -> bool:
        """Check if request is active (not deleted)."""
        return self.status != self.Status.DELETED

    @property
    def is_completed(self) -> bool:
        """Check if request processing is complete."""
        return self.status in (self.Status.COMPLETED, self.Status.FAILED)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate processing duration in seconds."""
        if self.completed_at and self.created_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': str(self.id),
            'status': self.status,
            'media_type': self.media_type,
            'source_url': self.source_url,
            'filename': self.filename,
            'progress': self.progress,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'results': self.results,
            'error_message': self.error_message,
        }
```

---

## 6. Pydantic Schemas

### File: /opt/services/media-analysis/schemas/analysis.py

```python
"""
Pydantic schemas for analysis request/response validation.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Request Schemas
# =============================================================================

class AnalysisConfig(BaseModel):
    """Configuration for LLM analysis."""
    model: str = Field(default="gpt-4o", description="LLM model to use")
    max_tokens: int = Field(default=2000, ge=1, le=32000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    prompt_template: Optional[str] = None


class AnalysisOptions(BaseModel):
    """User-specified processing options."""
    extract_frames: bool = Field(default=False)
    generate_contact_sheet: bool = Field(default=False)
    transcribe_audio: bool = Field(default=False)
    ocr_document: bool = Field(default=False)
    output_format: str = Field(default="summary", pattern="^(summary|detailed|json)$")


class AnalyzeRequest(BaseModel):
    """Request to analyze media."""
    prompt: str = Field(..., min_length=1, max_length=5000)
    media_url: str = Field(..., min_length=1, max_length=2000)
    media_type: Optional[str] = Field(
        None,
        pattern="^(video|audio|document|image|auto)$"
    )
    config: Optional[AnalysisConfig] = None
    options: Optional[AnalysisOptions] = None
    created_by: Optional[UUID] = None


class StatusQueryParams(BaseModel):
    """Query parameters for history endpoint."""
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    status: Optional[str] = Field(None, pattern="^(pending|processing|completed|failed|all)$")
    media_type: Optional[str] = Field(None, pattern="^(video|audio|document|image|all)$")
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: str = Field(default="created_at", pattern="^(created_at|status|media_type)$")
    order: str = Field(default="desc", pattern="^(asc|desc)$")


# =============================================================================
# Response Schemas
# =============================================================================

class AnalysisResponse(BaseModel):
    """Response after creating analysis request."""
    model_config = ConfigDict(from_attributes=True)

    analysis_id: UUID
    status: str
    estimated_time: Optional[int] = None
    message: str


class AnalysisStatusResponse(BaseModel):
    """Response for status query."""
    model_config = ConfigDict(from_attributes=True)

    analysis_id: UUID
    status: str
    progress: int
    media_type: str
    source_url: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    result_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class AnalysisHistoryItem(BaseModel):
    """Single item in history list."""
    model_config = ConfigDict(from_attributes=True)

    analysis_id: UUID
    status: str
    media_type: str
    prompt: str
    created_at: datetime
    completed_at: Optional[datetime] = None


class AnalysisHistoryResponse(BaseModel):
    """Response for history endpoint."""
    data: List[AnalysisHistoryItem]
    pagination: dict


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    code: str
```

---

## 7. Repository Pattern

### File: /opt/services/media-analysis/repositories/analysis_repository.py

```python
"""
Repository pattern for analysis_request CRUD operations.
"""
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis_request import AnalysisRequest
from app.schemas.analysis import AnalyzeRequest, StatusQueryParams


class AnalysisRepository:
    """Repository for analysis_request CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, request: AnalyzeRequest, celery_task_id: Optional[str] = None) -> AnalysisRequest:
        """
        Create new analysis request.

        Args:
            request: AnalyzeRequest with analysis parameters
            celery_task_id: Optional Celery task ID for async processing

        Returns:
            Created AnalysisRequest instance
        """
        analysis = AnalysisRequest(
            status=AnalysisRequest.Status.PENDING,
            media_type=request.media_type or 'unknown',
            source_url=request.media_url,
            analysis_config=request.config.dict() if request.config else {},
            analysis_options=request.options.dict() if request.options else {},
            progress=0,
            created_by=request.created_by,
            celery_task_id=celery_task_id,
        )

        self.session.add(analysis)
        await self.session.commit()
        await self.session.refresh(analysis)

        return analysis

    async def get_by_id(self, analysis_id: UUID) -> Optional[AnalysisRequest]:
        """
        Get analysis request by ID.

        Args:
            analysis_id: Analysis UUID

        Returns:
            AnalysisRequest or None if not found/deleted
        """
        query = select(AnalysisRequest).where(
            and_(
                AnalysisRequest.id == analysis_id,
                AnalysisRequest.status != AnalysisRequest.Status.DELETED
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        analysis_id: UUID,
        status: str,
        progress: Optional[int] = None,
        results: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> Optional[AnalysisRequest]:
        """
        Update analysis status.

        Args:
            analysis_id: Analysis UUID
            status: New status
            progress: Optional progress percentage
            results: Optional analysis results
            error_message: Optional error details

        Returns:
            Updated AnalysisRequest or None
        """
        # Build update values
        update_values = {
            'status': status,
            'updated_at': datetime.utcnow(),
        }

        if progress is not None:
            update_values['progress'] = progress

        if results is not None:
            update_values['results'] = results

        if error_message is not None:
            update_values['error_message'] = error_message

        if status in (AnalysisRequest.Status.COMPLETED, AnalysisRequest.Status.FAILED):
            update_values['completed_at'] = datetime.utcnow()

        # Execute update
        query = (
            update(AnalysisRequest)
            .where(
                and_(
                    AnalysisRequest.id == analysis_id,
                    AnalysisRequest.status != AnalysisRequest.Status.DELETED
                )
            )
            .values(**update_values)
            .returning(AnalysisRequest)
        )

        result = await self.session.execute(query)
        await self.session.commit()

        return result.scalar_one_or_none()

    async def soft_delete(self, analysis_id: UUID) -> bool:
        """
        Soft delete analysis request.

        Args:
            analysis_id: Analysis UUID

        Returns:
            True if deleted, False if not found
        """
        query = (
            update(AnalysisRequest)
            .where(
                and_(
                    AnalysisRequest.id == analysis_id,
                    AnalysisRequest.status != AnalysisRequest.Status.DELETED
                )
            )
            .values(
                status=AnalysisRequest.Status.DELETED,
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )

        result = await self.session.execute(query)
        await self.session.commit()

        return result.rowcount > 0

    async def get_history(
        self,
        filters: StatusQueryParams,
        created_by: Optional[UUID] = None,
    ) -> Tuple[List[AnalysisRequest], int]:
        """
        Get paginated analysis history.

        Args:
            filters: Query parameters
            created_by: Optional user ID for filtering

        Returns:
            Tuple of (list of AnalysisRequest, total count)
        """
        # Build base query
        conditions = [
            AnalysisRequest.status != AnalysisRequest.Status.DELETED
        ]

        if created_by:
            conditions.append(AnalysisRequest.created_by == created_by)

        if filters.status and filters.status != 'all':
            conditions.append(AnalysisRequest.status == filters.status)

        if filters.media_type and filters.media_type != 'all':
            conditions.append(AnalysisRequest.media_type == filters.media_type)

        if filters.date_from:
            conditions.append(AnalysisRequest.created_at >= filters.date_from)

        if filters.date_to:
            conditions.append(AnalysisRequest.created_at <= filters.date_to)

        # Count total
        count_query = (
            select(func.count(AnalysisRequest.id))
            .where(and_(*conditions))
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        # Build order by
        order_column = getattr(AnalysisRequest, filters.sort_by, AnalysisRequest.created_at)
        if filters.order == 'desc':
            order_column = order_column.desc()
        else:
            order_column = order_column.asc()

        # Fetch data with pagination
        query = (
            select(AnalysisRequest)
            .where(and_(*conditions))
            .order_by(order_column)
            .offset((filters.page - 1) * filters.per_page)
            .limit(filters.per_page)
        )

        result = await self.session.execute(query)
        analyses = result.scalars().all()

        return list(analyses), total

    async def get_pending_count(self) -> int:
        """Get count of pending/processing analyses."""
        query = (
            select(func.count(AnalysisRequest.id))
            .where(
                AnalysisRequest.status.in_([
                    AnalysisRequest.Status.PENDING,
                    AnalysisRequest.Status.PROCESSING
                ])
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one()
```

---

## 8. Seed Data

**Seed Data Required**: None

The `analysis_request` table does not require seed data as it stores runtime analysis requests.

---

*Research completed: 2026-01-20*
*Output: /home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-24-pre/research/database-design.md*
