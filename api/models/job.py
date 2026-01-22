"""
AnalysisJob model for media analysis job tracking.

Represents a media analysis task with status, metadata, and relationships
to associated media files, analysis results, and transcriptions.
"""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from api.models.media import MediaFile
    from api.models.result import AnalysisResult
    from api.models.transcription import Transcription
    from api.models.processing_log import ProcessingLog


class JobStatus(StrEnum):
    """
    Enumeration of possible job states.

    States:
        - pending: Job created, awaiting processing
        - processing: Job is currently being processed
        - completed: Job finished successfully
        - failed: Job encountered an error
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MediaType(StrEnum):
    """
    Enumeration of supported media types.

    Types:
        - video: Video file (mp4, mov, avi, etc.)
        - audio: Audio file (mp3, wav, ogg, etc.)
        - image: Image file (png, jpg, webp, etc.)
    """

    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"


class AnalysisJob(Base, TimestampMixin):
    """
    Model representing a media analysis job.

    Attributes:
        id: Unique identifier (UUID primary key)
        status: Current job status (pending/processing/completed/failed)
        media_type: Type of media being analyzed (video/audio/image)
        source_url: Original URL of the media source (nullable)
        created_at: Timestamp when job was created
        updated_at: Timestamp when job was last updated
        completed_at: Timestamp when job completed (nullable)
        error_message: Error details if job failed (nullable)
        metadata_json: Additional metadata as JSONB (nullable)

    Relationships:
        media_files: Associated media files for this job
        results: Analysis results from different providers
        transcriptions: Transcription records for this job
    """

    __tablename__ = "analysis_job"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for the analysis job"
    )

    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus,
            name="job_status",
            create_type=False,
            create_constraint=False,
        ),
        nullable=False,
        default=JobStatus.PENDING,
        doc="Current status of the analysis job"
    )

    media_type: Mapped[MediaType] = mapped_column(
        Enum(
            MediaType,
            name="media_type",
            create_type=False,
            create_constraint=False,
        ),
        nullable=False,
        doc="Type of media being analyzed"
    )

    source_url: Mapped[str | None] = mapped_column(
        String(length=2048),
        nullable=True,
        doc="Original URL of the media source"
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when job completed"
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Error message if job failed"
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
        doc="Additional metadata as JSONB"
    )

    # Relationships
    media_files: Mapped[list["MediaFile"]] = relationship(
        "MediaFile",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    results: Mapped[list["AnalysisResult"]] = relationship(
        "AnalysisResult",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    transcriptions: Mapped[list["Transcription"]] = relationship(
        "Transcription",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    processing_logs: Mapped[list["ProcessingLog"]] = relationship(
        "ProcessingLog",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the analysis job."""
        return (
            f"<AnalysisJob(id={self.id}, "
            f"status={self.status}, "
            f"media_type={self.media_type})>"
        )
