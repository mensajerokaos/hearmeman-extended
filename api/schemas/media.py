"""
Pydantic schemas for MediaFile model.

Maps to: api/models/media.py::MediaFile
Table: media_file
"""

from datetime import datetime
from typing import Optional, List
from enum import StrEnum

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


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


class MediaFileCreate(BaseModel):
    """
    Schema for creating a new media file record.

    Used in: POST /media endpoint
    Validates: Required fields for initial media file registration
    """

    job_id: UUID = Field(
        ...,
        description="Foreign key to the parent analysis job"
    )
    file_type: FileType = Field(
        default=FileType.SOURCE,
        description="Type of media file"
    )
    original_url: Optional[str] = Field(
        None,
        max_length=2048,
        description="Original source URL of the media file"
    )
    cdn_url: Optional[str] = Field(
        None,
        max_length=2048,
        description="CDN or storage URL where file is accessible"
    )
    mime_type: Optional[str] = Field(
        None,
        max_length=128,
        description="MIME type of the file (e.g., video/mp4)"
    )
    file_size: Optional[int] = Field(
        None,
        ge=0,
        description="Size of file in bytes"
    )
    filename: Optional[str] = Field(
        None,
        max_length=512,
        description="Original filename"
    )
    status: MediaFileStatus = Field(
        default=MediaFileStatus.PENDING,
        description="Current processing status"
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "file_type": "source",
                "original_url": "https://youtube.com/watch?v=example",
                "mime_type": "video/mp4",
                "file_size": 104857600,
                "filename": "interview_video.mp4",
                "status": "pending"
            }
        }
    )


class MediaFileUpdate(BaseModel):
    """
    Schema for updating a media file.

    Used in: PATCH /media/{id} endpoint (internal use)
    Validates: Optional fields for partial updates
    All fields are optional to support partial updates.
    """

    file_type: Optional[FileType] = Field(
        None,
        description="Updated type of media file"
    )
    original_url: Optional[str] = Field(
        None,
        max_length=2048,
        description="Updated original source URL"
    )
    cdn_url: Optional[str] = Field(
        None,
        max_length=2048,
        description="Updated CDN or storage URL"
    )
    mime_type: Optional[str] = Field(
        None,
        max_length=128,
        description="Updated MIME type (e.g., video/mp4)"
    )
    file_size: Optional[int] = Field(
        None,
        ge=0,
        description="Updated size in bytes"
    )
    filename: Optional[str] = Field(
        None,
        max_length=512,
        description="Updated original filename"
    )
    status: Optional[MediaFileStatus] = Field(
        None,
        description="Updated processing status"
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "status": "downloaded",
                "cdn_url": "https://cdn.example.com/downloaded/video.mp4",
                "file_size": 104857600
            }
        }
    )


class MediaFileResponse(BaseModel):
    """
    Schema for media file API responses.

    Used in: GET /media/{id}, GET /media endpoint
    Contains: All fields from MediaFile model for read operations.
    """

    id: UUID = Field(..., description="Unique identifier for the media file")
    job_id: UUID = Field(..., description="Foreign key to the parent analysis job")
    file_type: FileType = Field(..., description="Type of media file")
    original_url: Optional[str] = Field(
        None,
        description="Original source URL of the media file"
    )
    cdn_url: Optional[str] = Field(
        None,
        description="CDN or storage URL where file is accessible"
    )
    mime_type: Optional[str] = Field(
        None,
        description="MIME type of the file"
    )
    file_size: Optional[int] = Field(
        None,
        description="Size of file in bytes"
    )
    filename: Optional[str] = Field(
        None,
        description="Original filename"
    )
    status: MediaFileStatus = Field(..., description="Current processing status")
    created_at: datetime = Field(..., description="UTC timestamp when record was created")
    updated_at: datetime = Field(..., description="UTC timestamp when record was last updated")

    # Relationship data (optional nested)
    job: Optional["JobResponse"] = Field(
        default=None,
        description="Parent analysis job"
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "file_type": "source",
                "original_url": "https://youtube.com/watch?v=example",
                "mime_type": "video/mp4",
                "file_size": 104857600,
                "filename": "interview_video.mp4",
                "status": "completed",
                "created_at": "2026-01-20T10:00:00Z",
                "updated_at": "2026-01-20T10:05:00Z"
            }
        }
    )


class MediaFileListResponse(BaseModel):
    """Schema for paginated list of media files."""

    items: List[MediaFileResponse] = Field(..., description="List of media files")
    total: int = Field(..., description="Total number of media files")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether more pages exist")


# Forward references for nested schemas (resolved at end of file)
from api.schemas.job import JobResponse

MediaFileResponse.model_rebuild()
