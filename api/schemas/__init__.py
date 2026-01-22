"""
Pydantic schemas for Media Analysis API.

This module provides request/response validation schemas
that map to SQLAlchemy ORM models defined in api/models/.

Schemas are organized by domain:
- media.py: MediaFile schemas
- job.py: AnalysisJob schemas
- result.py: AnalysisResult schemas
- transcription.py: Transcription schemas
"""

from api.schemas.media import (
    MediaFileCreate,
    MediaFileUpdate,
    MediaFileResponse,
    MediaFileListResponse,
    FileType,
    MediaFileStatus,
)
from api.schemas.job import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobListResponse,
    JobStatus,
    MediaType,
)
from api.schemas.result import (
    AnalysisResultCreate,
    AnalysisResultUpdate,
    AnalysisResultResponse,
    AnalysisResultListResponse,
    AnalysisProvider,
)
from api.schemas.transcription import (
    TranscriptionCreate,
    TranscriptionUpdate,
    TranscriptionResponse,
    TranscriptionListResponse,
    TranscriptionProvider,
)

__all__ = [
    # Media schemas
    "MediaFileCreate",
    "MediaFileUpdate",
    "MediaFileResponse",
    "MediaFileListResponse",
    "FileType",
    "MediaFileStatus",
    # Job schemas
    "JobCreate",
    "JobUpdate",
    "JobResponse",
    "JobListResponse",
    "JobStatus",
    "MediaType",
    # Result schemas
    "AnalysisResultCreate",
    "AnalysisResultUpdate",
    "AnalysisResultResponse",
    "AnalysisResultListResponse",
    "AnalysisProvider",
    # Transcription schemas
    "TranscriptionCreate",
    "TranscriptionUpdate",
    "TranscriptionResponse",
    "TranscriptionListResponse",
    "TranscriptionProvider",
]

__version__ = "4.0.0"
