"""
Pydantic schemas for AnalysisJob model.

Maps to: api/models/job.py::AnalysisJob
Table: analysis_job
"""

from datetime import datetime
from typing import Optional, List
from enum import StrEnum

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


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


class JobCreate(BaseModel):
    """
    Schema for creating a new analysis job.

    Used in: POST /jobs endpoint
    Validates: Required fields for job creation
    """

    media_type: MediaType = Field(
        ...,
        description="Type of media being analyzed (video/audio/image)"
    )
    source_url: Optional[str] = Field(
        None,
        max_length=2048,
        description="Original URL of the media source"
    )
    metadata_json: Optional[dict] = Field(
        None,
        description="Additional metadata as JSON"
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "media_type": "video",
                "source_url": "https://youtube.com/watch?v=example",
                "metadata_json": {"quality": "720p", "fps": 30}
            }
        }
    )


class JobUpdate(BaseModel):
    """
    Schema for updating an analysis job.

    Used in: PATCH /jobs/{id} endpoint
    Validates: Optional fields for partial updates
    All fields are optional to support partial updates.
    """

    status: Optional[JobStatus] = Field(
        None,
        description="Current status of the analysis job"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="Timestamp when job completed"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if job failed"
    )
    metadata_json: Optional[dict] = Field(
        None,
        description="Additional metadata as JSON"
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "status": "processing",
                "error_message": None
            }
        }
    )


class JobResponse(BaseModel):
    """
    Schema for analysis job API responses.

    Used in: GET /jobs/{id}, GET /jobs endpoint
    Contains: All fields from AnalysisJob model for read operations.
    """

    id: UUID = Field(..., description="Unique identifier for the analysis job")
    status: JobStatus = Field(..., description="Current status of the analysis job")
    media_type: MediaType = Field(..., description="Type of media being analyzed")
    source_url: Optional[str] = Field(
        None,
        description="Original URL of the media source"
    )
    created_at: datetime = Field(..., description="UTC timestamp when job was created")
    updated_at: datetime = Field(..., description="UTC timestamp when job was last updated")
    completed_at: Optional[datetime] = Field(
        None,
        description="Timestamp when job completed"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if job failed"
    )
    metadata_json: Optional[dict] = Field(
        None,
        description="Additional metadata as JSON"
    )

    # Relationship data (optional nested)
    media_files: Optional[List["MediaFileResponse"]] = Field(
        default_factory=list,
        description="Associated media files for this job"
    )
    results: Optional[List["AnalysisResultResponse"]] = Field(
        default_factory=list,
        description="Analysis results from different providers"
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "media_type": "video",
                "source_url": "https://youtube.com/watch?v=example",
                "created_at": "2026-01-20T10:00:00Z",
                "updated_at": "2026-01-20T10:05:00Z",
                "completed_at": "2026-01-20T10:05:00Z",
                "error_message": None,
                "metadata_json": {"quality": "720p", "fps": 30}
            }
        }
    )


class JobListResponse(BaseModel):
    """Schema for paginated list of analysis jobs."""

    items: List[JobResponse] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether more pages exist")


# Forward references for nested schemas (resolved at end of file)
from api.schemas.media import MediaFileResponse
from api.schemas.result import AnalysisResultResponse

JobResponse.model_rebuild()
