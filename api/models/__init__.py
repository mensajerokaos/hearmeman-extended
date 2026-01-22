"""
Models package initialization.

Exports:
    - Base: Declarative base class for all ORM models
    - AnalysisJob: Media analysis job model
    - MediaFile: Media file tracking model
    - AnalysisResult: AI analysis result model
    - Transcription: Speech-to-text transcription model
    - JobStatus: Enumeration of job states
    - MediaType: Enumeration of media types
    - FileType: Enumeration of file types
    - MediaFileStatus: Enumeration of media file states
    - AnalysisProvider: Enumeration of AI providers
    - TranscriptionProvider: Enumeration of speech-to-text providers
"""

from api.models.base import Base
from api.models.job import (
    AnalysisJob,
    JobStatus,
    MediaType,
)
from api.models.media import (
    FileType,
    MediaFile,
    MediaFileStatus,
)
from api.models.result import (
    AnalysisProvider,
    AnalysisResult,
)
from api.models.transcription import (
    Transcription,
    TranscriptionProvider,
)
from api.models.processing_log import (
    ProcessingLog,
    ProcessingLogStatus,
    ProcessingStage,
)

__all__ = [
    # Base class
    "Base",
    # Job model
    "AnalysisJob",
    "JobStatus",
    "MediaType",
    # Media model
    "MediaFile",
    "FileType",
    "MediaFileStatus",
    # Result model
    "AnalysisResult",
    "AnalysisProvider",
    # Transcription model
    "Transcription",
    "TranscriptionProvider",
    # Processing log model
    "ProcessingLog",
    "ProcessingLogStatus",
    "ProcessingStage",
]
