"""
MediaFile model for tracking media files associated with analysis jobs.

Represents media files that have been downloaded, processed, or generated
during the analysis workflow.
"""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from api.models.job import AnalysisJob


class FileType(StrEnum):
    """
    Enumeration of supported file types.

    Types:
        - source: Original media file from user input
        - downloaded: Media file downloaded from source URL
        - extracted: Frame or clip extracted from video
        - cached: Cached copy for reprocessing
        - output: Generated output file
    """

    SOURCE = "source"
    DOWNLOADED = "downloaded"
    EXTRACTED = "extracted"
    CACHED = "cached"
    OUTPUT = "output"


class MediaFileStatus(StrEnum):
    """
    Enumeration of media file processing states.

    States:
        - pending: File not yet processed
        - downloading: File is being downloaded
        - downloaded: File successfully downloaded
        - processing: File is being processed
        - completed: File processing complete
        - failed: File processing failed
    """

    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MediaFile(Base, TimestampMixin):
    """
    Model representing a media file associated with an analysis job.

    Attributes:
        id: Unique identifier (UUID primary key)
        job_id: Foreign key to the parent AnalysisJob
        file_type: Type of media file (source/downloaded/extracted/cached/output)
        original_url: Original source URL (nullable)
        cdn_url: CDN or storage URL where file is accessible (nullable)
        mime_type: MIME type of the file (e.g., video/mp4)
        file_size: Size of file in bytes
        filename: Original filename
        status: Current processing status
        created_at: Timestamp when record was created

    Relationships:
        job: Parent AnalysisJob
    """

    __tablename__ = "media_file"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for the media file"
    )

    job_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey(
            column="analysis_job.id",
            ondelete="CASCADE",
            name="fk_media_file_job_id",
        ),
        nullable=False,
        doc="Foreign key to the parent analysis job"
    )

    file_type: Mapped[FileType] = mapped_column(
        String(length=32),
        nullable=False,
        default=FileType.SOURCE,
        doc="Type of media file"
    )

    original_url: Mapped[str | None] = mapped_column(
        String(length=2048),
        nullable=True,
        doc="Original source URL of the media file"
    )

    cdn_url: Mapped[str | None] = mapped_column(
        String(length=2048),
        nullable=True,
        doc="CDN or storage URL where file is accessible"
    )

    mime_type: Mapped[str | None] = mapped_column(
        String(length=128),
        nullable=True,
        doc="MIME type of the file (e.g., video/mp4, audio/mp3)"
    )

    file_size: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        doc="Size of file in bytes"
    )

    filename: Mapped[str | None] = mapped_column(
        String(length=512),
        nullable=True,
        doc="Original filename"
    )

    status: Mapped[MediaFileStatus] = mapped_column(
        String(length=32),
        nullable=False,
        default=MediaFileStatus.PENDING,
        doc="Current processing status"
    )

    # Relationships
    job: Mapped["AnalysisJob"] = relationship(
        "AnalysisJob",
        back_populates="media_files",
    )

    def __repr__(self) -> str:
        """String representation of the media file."""
        return (
            f"<MediaFile(id={self.id}, "
            f"job_id={self.job_id}, "
            f"file_type={self.file_type}, "
            f"status={self.status})>"
        )
