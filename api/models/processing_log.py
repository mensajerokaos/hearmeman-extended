"""
ProcessingLog model for detailed audit trail.

Represents processing stages and events for analysis jobs,
providing a detailed audit trail for debugging and compliance.
"""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base

if TYPE_CHECKING:
    from api.models.job import AnalysisJob


class ProcessingStage(StrEnum):
    """
    Enumeration of processing stages.

    Stages:
        - upload: File upload stage
        - download: Media download from URL
        - validation: Input validation
        - transcription: Speech-to-text processing
        - analysis: AI analysis processing
        - completion: Job completion
        - cleanup: Resource cleanup
    """

    UPLOAD = "upload"
    DOWNLOAD = "download"
    VALIDATION = "validation"
    TRANSCRIPTION = "transcription"
    ANALYSIS = "analysis"
    COMPLETION = "completion"
    CLEANUP = "cleanup"


class ProcessingLogStatus(StrEnum):
    """
    Enumeration of processing log statuses.

    Statuses:
        - started: Processing stage started
        - completed: Processing stage completed successfully
        - failed: Processing stage failed
        - warning: Processing completed with warnings
        - skipped: Processing stage was skipped
    """

    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class ProcessingLog(Base):
    """
    Model representing a processing log entry.

    Provides detailed audit trail for analysis job processing stages.
    Used for debugging, compliance, and performance monitoring.

    Attributes:
        id: Unique identifier (UUID primary key)
        job_id: Foreign key to the parent AnalysisJob
        stage: Processing stage (upload/download/transcription/analysis/etc.)
        status: Status of the processing stage
        message: Human-readable log message
        details_json: Additional details as JSONB
        duration_ms: Duration of the stage in milliseconds
        created_at: Timestamp when log was recorded

    Relationships:
        job: Parent AnalysisJob
    """

    __tablename__ = "processing_log"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for the processing log entry"
    )

    job_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey(
            column="analysis_job.id",
            ondelete="CASCADE",
            name="fk_processing_log_job_id",
        ),
        nullable=False,
        doc="Foreign key to the parent analysis job"
    )

    stage: Mapped[ProcessingStage] = mapped_column(
        String(length=64),
        nullable=False,
        doc="Processing stage (upload/download/transcription/analysis/etc.)"
    )

    status: Mapped[ProcessingLogStatus] = mapped_column(
        String(length=32),
        nullable=False,
        doc="Status of the processing stage"
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Human-readable log message"
    )

    details_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
        doc="Additional details as JSONB"
    )

    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Duration of the processing stage in milliseconds"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        doc="Timestamp when log entry was created"
    )

    # Relationships
    job: Mapped["AnalysisJob"] = relationship(
        "AnalysisJob",
        back_populates="processing_logs",
    )

    def __repr__(self) -> str:
        """String representation of the processing log."""
        return (
            f"<ProcessingLog(id={self.id}, "
            f"job_id={self.job_id}, "
            f"stage={self.stage}, "
            f"status={self.status})>"
        )
