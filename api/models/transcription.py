"""
Transcription model for storing audio/video transcriptions.

Represents text transcriptions extracted from media content using
various speech-to-text providers.
"""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from api.models.job import AnalysisJob


class TranscriptionProvider(StrEnum):
    """
    Enumeration of supported speech-to-text providers.

    Providers:
        - whisper: OpenAI Whisper
        - whisper_local: Local Whisper model
        - google: Google Speech-to-Text
        - azure: Azure Cognitive Services Speech
        - deepgram: Deepgram API
        - assemblyai: AssemblyAI API
        - elevenlabs: ElevenLabs AI
        - minimax: MiniMax ASR
    """

    WHISPER = "whisper"
    WHISPER_LOCAL = "whisper_local"
    GOOGLE = "google"
    AZURE = "azure"
    DEEPGRAM = "deepgram"
    ASSEMBLYAI = "assemblyai"
    ELEVENLABS = "elevenlabs"
    MINIMAX = "minimax"


class Transcription(Base, TimestampMixin):
    """
    Model representing a transcription of media content.

    Attributes:
        id: Unique identifier (UUID primary key)
        job_id: Foreign key to the parent AnalysisJob
        provider: Speech-to-text provider used
        text: Full transcribed text
        segments_json: Timestamped segments as JSONB (nullable)
        language: Detected or specified language code
        duration_seconds: Duration of the media in seconds
        created_at: Timestamp when transcription was recorded

    Relationships:
        job: Parent AnalysisJob
    """

    __tablename__ = "transcription"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for the transcription"
    )

    job_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey(
            column="analysis_job.id",
            ondelete="CASCADE",
            name="fk_transcription_job_id",
        ),
        nullable=False,
        doc="Foreign key to the parent analysis job"
    )

    provider: Mapped[TranscriptionProvider] = mapped_column(
        String(length=64),
        nullable=False,
        doc="Speech-to-text provider used for transcription"
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Full transcribed text content"
    )

    segments_json: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
        doc="Timestamped segments as JSONB array"
    )

    language: Mapped[str] = mapped_column(
        String(length=10),
        nullable=False,
        default="en",
        doc="Language code (e.g., 'en', 'es', 'fr')"
    )

    duration_seconds: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        doc="Duration of the media in seconds"
    )

    # Relationships
    job: Mapped["AnalysisJob"] = relationship(
        "AnalysisJob",
        back_populates="transcriptions",
    )

    def __repr__(self) -> str:
        """String representation of the transcription."""
        return (
            f"<Transcription(id={self.id}, "
            f"job_id={self.job_id}, "
            f"provider={self.provider}, "
            f"language={self.language})>"
        )
