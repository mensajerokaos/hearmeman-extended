"""
Pydantic schemas for Transcription model.

Maps to: api/models/transcription.py::Transcription
Table: transcription
"""

from datetime import datetime
from typing import Optional, List, Any
from enum import StrEnum

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class TranscriptionProvider(StrEnum):
    """
    Enumeration of supported transcription providers.

    Providers:
        - whisper: OpenAI Whisper (default)
        - whisper_local: Local Whisper model
        - google: Google Speech-to-Text
        - azure: Azure Cognitive Services
        - deepgram: Deepgram API
        - assemblyai: AssemblyAI API
        - elevenlabs: ElevenLabs API
        - minimax: MiniMax AI transcription
    """

    WHISPER = "whisper"
    WHISPER_LOCAL = "whisper_local"
    GOOGLE = "google"
    AZURE = "azure"
    DEEPGRAM = "deepgram"
    ASSEMBLYAI = "assemblyai"
    ELEVENLABS = "elevenlabs"
    MINIMAX = "minimax"


class TranscriptionCreate(BaseModel):
    """
    Schema for creating a new transcription record.

    Used in: POST /transcriptions endpoint (internal use)
    Validates: Required fields for transcription creation
    """

    job_id: UUID = Field(
        ...,
        description="Foreign key to the parent analysis job"
    )
    provider: TranscriptionProvider = Field(
        default=TranscriptionProvider.WHISPER,
        description="Transcription provider used"
    )
    text: str = Field(
        ...,
        description="Full transcribed text content"
    )
    segments_json: Optional[List[dict]] = Field(
        None,
        description="Timestamped segments with speaker labels if available"
    )
    language: Optional[str] = Field(
        None,
        max_length=10,
        description="Detected or specified language code (e.g., 'en', 'es', 'fr')"
    )
    duration_seconds: Optional[float] = Field(
        None,
        ge=0.0,
        description="Duration of the media in seconds"
    )
    word_count: Optional[int] = Field(
        None,
        ge=0,
        description="Number of words in the transcription"
    )
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Average confidence score of the transcription (0.0-1.0)"
    )
    tokens_used: Optional[int] = Field(
        None,
        ge=0,
        description="Number of tokens consumed by the transcription"
    )
    latency_ms: Optional[int] = Field(
        None,
        ge=0,
        description="Processing latency in milliseconds"
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "provider": "whisper",
                "text": "Hello, this is a sample transcription...",
                "segments_json": [
                    {"id": 1, "start": 0.0, "end": 5.0, "text": "Hello, this is", "speaker": "SPEAKER_01"},
                    {"id": 2, "start": 5.0, "end": 10.0, "text": "a sample transcription.", "speaker": "SPEAKER_01"}
                ],
                "language": "en",
                "duration_seconds": 300.5,
                "word_count": 450,
                "confidence": 0.98,
                "tokens_used": 1200,
                "latency_ms": 15000
            }
        }
    )


class TranscriptionUpdate(BaseModel):
    """
    Schema for updating a transcription.

    Used in: PATCH /transcriptions/{id} endpoint (internal use)
    Validates: Optional fields for partial updates
    """

    text: Optional[str] = Field(
        None,
        description="Updated transcription text"
    )
    segments_json: Optional[List[dict]] = Field(
        None,
        description="Updated timestamped segments"
    )
    language: Optional[str] = Field(
        None,
        max_length=10,
        description="Updated language code"
    )
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Updated confidence score"
    )
    tokens_used: Optional[int] = Field(
        None,
        ge=0,
        description="Updated token count"
    )
    latency_ms: Optional[int] = Field(
        None,
        ge=0,
        description="Updated latency in milliseconds"
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "text": "Corrected transcription text...",
                "confidence": 0.99
            }
        }
    )


class TranscriptionResponse(BaseModel):
    """
    Schema for transcription API responses.

    Used in: GET /transcriptions/{id}, GET /transcriptions endpoint
    Contains: All fields from Transcription model for read operations.
    """

    id: UUID = Field(..., description="Unique identifier for the transcription")
    job_id: UUID = Field(..., description="Foreign key to the parent analysis job")
    provider: TranscriptionProvider = Field(..., description="Transcription provider used")
    text: str = Field(..., description="Full transcribed text content")
    segments_json: Optional[List[dict]] = Field(
        None,
        description="Timestamped segments with speaker labels"
    )
    language: Optional[str] = Field(
        None,
        description="Detected or specified language code"
    )
    duration_seconds: Optional[float] = Field(
        None,
        description="Duration of the media in seconds"
    )
    word_count: Optional[int] = Field(
        None,
        description="Number of words in the transcription"
    )
    confidence: Optional[float] = Field(
        None,
        description="Average confidence score (0.0-1.0)"
    )
    tokens_used: Optional[int] = Field(
        None,
        description="Number of tokens consumed"
    )
    latency_ms: Optional[int] = Field(
        None,
        description="Processing latency in milliseconds"
    )
    created_at: datetime = Field(..., description="UTC timestamp when transcription was created")
    updated_at: datetime = Field(..., description="UTC timestamp when transcription was last updated")

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
                "id": "660e8400-e29b-41d4-a716-446655440001",
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "provider": "whisper",
                "text": "Hello, this is a sample transcription...",
                "segments_json": [
                    {"id": 1, "start": 0.0, "end": 5.0, "text": "Hello, this is", "speaker": "SPEAKER_01"}
                ],
                "language": "en",
                "duration_seconds": 300.5,
                "word_count": 450,
                "confidence": 0.98,
                "tokens_used": 1200,
                "latency_ms": 15000,
                "created_at": "2026-01-20T10:00:00Z",
                "updated_at": "2026-01-20T10:05:00Z"
            }
        }
    )


class TranscriptionListResponse(BaseModel):
    """Schema for paginated list of transcriptions."""

    items: List[TranscriptionResponse] = Field(..., description="List of transcriptions")
    total: int = Field(..., description="Total number of transcriptions")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether more pages exist")


# Forward references for nested schemas (resolved at end of file)
from api.schemas.job import JobResponse

TranscriptionResponse.model_rebuild()
