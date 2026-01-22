"""
Initial migration: Create all tables for Media Analysis API.

Revision ID: 000000000001
Revises:
Create Date: 2026-01-20 12:00:00

"""

from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision: str = "000000000001"
down_revision: Union[str, None] = None
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    """Create all database tables."""
    # Create ENUM types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE job_status AS ENUM ('pending', 'processing', 'completed', 'failed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE media_type AS ENUM ('video', 'audio', 'image');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE file_type AS ENUM ('source', 'downloaded', 'extracted', 'cached', 'output');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE media_file_status AS ENUM ('pending', 'downloading', 'downloaded', 'processing', 'completed', 'failed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE analysis_provider AS ENUM ('minimax', 'groq', 'gemini', 'openai', 'anthropic', 'local');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE transcription_provider AS ENUM ('whisper', 'whisper_local', 'google', 'azure', 'deepgram', 'assemblyai', 'elevenlabs', 'minimax');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create analysis_job table
    op.create_table(
        "analysis_job",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.Enum("pending", "processing", "completed", "failed", name="job_status"), nullable=False, default="pending"),
        sa.Column("media_type", sa.Enum("video", "audio", "image", name="media_type"), nullable=False),
        sa.Column("source_url", sa.String(2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True, default={}),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create index on analysis_job.status
    op.create_index("ix_analysis_job_status", "analysis_job", ["status"])

    # Create index on analysis_job.created_at
    op.create_index("ix_analysis_job_created_at", "analysis_job", ["created_at"])

    # Create index on analysis_job.is_deleted
    op.create_index("ix_analysis_job_is_deleted", "analysis_job", ["is_deleted"])

    # Create media_file table
    op.create_table(
        "media_file",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_job.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_type", sa.Enum("source", "downloaded", "extracted", "cached", "output", name="file_type"), nullable=False, default="source"),
        sa.Column("original_url", sa.String(2048), nullable=True),
        sa.Column("cdn_url", sa.String(2048), nullable=True),
        sa.Column("mime_type", sa.String(128), nullable=True),
        sa.Column("file_size", sa.BigInteger, nullable=True),
        sa.Column("filename", sa.String(512), nullable=True),
        sa.Column("status", sa.Enum("pending", "downloading", "downloaded", "processing", "completed", "failed", name="media_file_status"), nullable=False, default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create index on media_file.job_id
    op.create_index("ix_media_file_job_id", "media_file", ["job_id"])

    # Create index on media_file.status
    op.create_index("ix_media_file_status", "media_file", ["status"])

    # Create analysis_result table
    op.create_table(
        "analysis_result",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_job.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.Enum("minimax", "groq", "gemini", "openai", "anthropic", "local", name="analysis_provider"), nullable=False),
        sa.Column("model", sa.String(256), nullable=False),
        sa.Column("result_json", postgresql.JSONB, nullable=False, default={}),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("tokens_used", sa.Integer, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create index on analysis_result.job_id
    op.create_index("ix_analysis_result_job_id", "analysis_result", ["job_id"])

    # Create index on analysis_result.provider
    op.create_index("ix_analysis_result_provider", "analysis_result", ["provider"])

    # Create transcription table
    op.create_table(
        "transcription",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_job.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.Enum("whisper", "whisper_local", "google", "azure", "deepgram", "assemblyai", "elevenlabs", "minimax", name="transcription_provider"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("segments_json", postgresql.JSONB, nullable=True),
        sa.Column("language", sa.String(10), nullable=False, default="en"),
        sa.Column("duration_seconds", sa.Float, nullable=False, default=0.0),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create index on transcription.job_id
    op.create_index("ix_transcription_job_id", "transcription", ["job_id"])

    # Create index on transcription.provider
    op.create_index("ix_transcription_provider", "transcription", ["provider"])


def downgrade() -> None:
    """Drop all database tables and types."""
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table("transcription")
    op.drop_table("analysis_result")
    op.drop_table("media_file")
    op.drop_table("analysis_job")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS transcription_provider CASCADE")
    op.execute("DROP TYPE IF EXISTS analysis_provider CASCADE")
    op.execute("DROP TYPE IF EXISTS media_file_status CASCADE")
    op.execute("DROP TYPE IF EXISTS file_type CASCADE")
    op.execute("DROP TYPE IF EXISTS media_type CASCADE")
    op.execute("DROP TYPE IF EXISTS job_status CASCADE")
