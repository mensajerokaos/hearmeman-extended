"""
Add processing_log table and GIN indexes for JSONB columns.

Revision ID: 000000000002
Revises: 000000000001
Create Date: 2026-01-21 21:30:00

This migration:
1. Creates the processing_log table for audit trail
2. Adds GIN indexes for JSONB columns (metadata_json, result_json, segments_json, details_json)
3. Adds partial indexes for is_deleted filtering optimization
4. Enables pg_trgm extension for full-text search
"""

from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision: str = "000000000002"
down_revision: Union[str, None] = "000000000001"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    """Apply migration: create processing_log table and add indexes."""

    # Ensure extensions are installed
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")

    # Create ENUM types for processing_log
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE processing_stage AS ENUM (
                'upload', 'download', 'validation',
                'transcription', 'analysis', 'completion', 'cleanup'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE processing_log_status AS ENUM (
                'started', 'completed', 'failed', 'warning', 'skipped'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create processing_log table
    op.create_table(
        "processing_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_job.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "stage",
            sa.Enum(
                "upload", "download", "validation", "transcription",
                "analysis", "completion", "cleanup",
                name="processing_stage"
            ),
            nullable=False
        ),
        sa.Column(
            "status",
            sa.Enum(
                "started", "completed", "failed", "warning", "skipped",
                name="processing_log_status"
            ),
            nullable=False
        ),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("details_json", postgresql.JSONB, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # Create indexes for processing_log
    op.create_index("ix_processing_log_job_id", "processing_log", ["job_id"])
    op.create_index("ix_processing_log_stage", "processing_log", ["stage"])
    op.create_index("ix_processing_log_status", "processing_log", ["status"])
    op.create_index("ix_processing_log_created_at", "processing_log", ["created_at"])

    # GIN indexes for JSONB columns

    # 1. GIN index for analysis_job.metadata_json
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_analysis_job_metadata_gin
        ON analysis_job USING GIN (metadata_json);
    """)

    # 2. GIN index for analysis_result.result_json
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_analysis_result_result_gin
        ON analysis_result USING GIN (result_json);
    """)

    # 3. GIN index for transcription.segments_json
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_transcription_segments_gin
        ON transcription USING GIN (segments_json);
    """)

    # 4. GIN index for processing_log.details_json
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_processing_log_details_gin
        ON processing_log USING GIN (details_json);
    """)

    # Partial indexes for soft delete optimization
    # (Queries filtering WHERE is_deleted = FALSE are common)

    # 5. Partial index for analysis_job.status (active only)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_analysis_job_status_active
        ON analysis_job (status)
        WHERE is_deleted = FALSE;
    """)

    # 6. Partial index for media_file.status (active only)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_media_file_status_active
        ON media_file (status)
        WHERE is_deleted = FALSE;
    """)

    # 7. Partial index for analysis_result.provider (active only)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_analysis_result_provider_active
        ON analysis_result (provider)
        WHERE is_deleted = FALSE;
    """)

    # 8. Partial index for transcription.provider (active only)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_transcription_provider_active
        ON transcription (provider)
        WHERE is_deleted = FALSE;
    """)

    # Composite indexes for common queries

    # 9. Composite index for job_id + status (common query pattern)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_analysis_job_status_created
        ON analysis_job (status, created_at DESC)
        WHERE is_deleted = FALSE;
    """)

    # 10. Composite index for job_id + provider on analysis_result
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_analysis_result_job_provider
        ON analysis_result (job_id, provider)
        WHERE is_deleted = FALSE;
    """)

    # 11. Composite index for job_id + provider on transcription
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_transcription_job_provider
        ON transcription (job_id, provider)
        WHERE is_deleted = FALSE;
    """)


def downgrade() -> None:
    """Revert migration: drop processing_log table and remove indexes."""

    # Drop GIN indexes
    op.execute("DROP INDEX IF EXISTS ix_analysis_job_metadata_gin;")
    op.execute("DROP INDEX IF EXISTS ix_analysis_result_result_gin;")
    op.execute("DROP INDEX IF EXISTS ix_transcription_segments_gin;")
    op.execute("DROP INDEX IF EXISTS ix_processing_log_details_gin;")

    # Drop partial indexes
    op.execute("DROP INDEX IF EXISTS ix_analysis_job_status_active;")
    op.execute("DROP INDEX IF EXISTS ix_media_file_status_active;")
    op.execute("DROP INDEX IF EXISTS ix_analysis_result_provider_active;")
    op.execute("DROP INDEX IF EXISTS ix_transcription_provider_active;")

    # Drop composite indexes
    op.execute("DROP INDEX IF EXISTS ix_analysis_job_status_created;")
    op.execute("DROP INDEX IF EXISTS ix_analysis_result_job_provider;")
    op.execute("DROP INDEX IF EXISTS ix_transcription_job_provider;")

    # Drop processing_log table
    op.drop_table("processing_log")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS processing_log_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS processing_stage CASCADE;")
