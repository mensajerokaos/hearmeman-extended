"""
AnalysisResult model for storing analysis results from different providers.

Represents the output from various AI providers (MiniMax, Groq, Gemini, etc.)
used to analyze media content.
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


class AnalysisProvider(StrEnum):
    """
    Enumeration of supported AI analysis providers.

    Providers:
        - minimax: MiniMax AI video analysis
        - groq: Groq LLM inference
        - gemini: Google Gemini AI
        - openai: OpenAI GPT models
        - anthropic: Anthropic Claude models
        - local: Local model inference
    """

    MINIMAX = "minimax"
    GROQ = "groq"
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class AnalysisResult(Base, TimestampMixin):
    """
    Model representing an analysis result from an AI provider.

    Attributes:
        id: Unique identifier (UUID primary key)
        job_id: Foreign key to the parent AnalysisJob
        provider: AI provider used for analysis (minimax/groq/gemini/etc.)
        model: Specific model identifier used
        result_json: Full analysis result as JSONB
        confidence: Confidence score of the analysis (nullable)
        tokens_used: Number of tokens consumed (nullable)
        latency_ms: Processing latency in milliseconds (nullable)
        created_at: Timestamp when result was recorded

    Relationships:
        job: Parent AnalysisJob
    """

    __tablename__ = "analysis_result"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for the analysis result"
    )

    job_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey(
            column="analysis_job.id",
            ondelete="CASCADE",
            name="fk_analysis_result_job_id",
        ),
        nullable=False,
        doc="Foreign key to the parent analysis job"
    )

    provider: Mapped[AnalysisProvider] = mapped_column(
        String(length=64),
        nullable=False,
        doc="AI provider used for analysis"
    )

    model: Mapped[str] = mapped_column(
        String(length=256),
        nullable=False,
        doc="Specific model identifier used for analysis"
    )

    result_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Full analysis result as JSONB"
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="Confidence score of the analysis (0.0-1.0)"
    )

    tokens_used: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Number of tokens consumed by the analysis"
    )

    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Processing latency in milliseconds"
    )

    # Relationships
    job: Mapped["AnalysisJob"] = relationship(
        "AnalysisJob",
        back_populates="results",
    )

    def __repr__(self) -> str:
        """String representation of the analysis result."""
        return (
            f"<AnalysisResult(id={self.id}, "
            f"job_id={self.job_id}, "
            f"provider={self.provider}, "
            f"model={self.model})>"
        )
