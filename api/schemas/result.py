"""
Pydantic schemas for AnalysisResult model.

Maps to: api/models/result.py::AnalysisResult
Table: analysis_result
"""

from datetime import datetime
from typing import Optional, List, Any
from enum import StrEnum

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


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


class AnalysisResultCreate(BaseModel):
    """
    Schema for creating a new analysis result.

    Used in: POST /results endpoint (internal use)
    Validates: Required fields for result creation
    """

    job_id: UUID = Field(
        ...,
        description="Foreign key to the parent analysis job"
    )
    provider: AnalysisProvider = Field(
        ...,
        description="AI provider used for analysis"
    )
    model: str = Field(
        ...,
        max_length=256,
        description="Specific model identifier used for analysis"
    )
    result_json: dict = Field(
        default_factory=dict,
        description="Full analysis result as JSON"
    )
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score of the analysis (0.0-1.0)"
    )
    tokens_used: Optional[int] = Field(
        None,
        ge=0,
        description="Number of tokens consumed by the analysis"
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
                "provider": "minimax",
                "model": "minimax-video-2.0",
                "result_json": {"summary": "A video about technology", "topics": ["AI", "ML"]},
                "confidence": 0.95,
                "tokens_used": 1500,
                "latency_ms": 5000
            }
        }
    )


class AnalysisResultUpdate(BaseModel):
    """
    Schema for updating an analysis result.

    Used in: PATCH /results/{id} endpoint (internal use)
    Validates: Optional fields for partial updates
    """

    result_json: Optional[dict] = Field(
        None,
        description="Updated analysis result as JSON"
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
                "result_json": {"summary": "Updated summary"},
                "confidence": 0.98
            }
        }
    )


class AnalysisResultResponse(BaseModel):
    """
    Schema for analysis result API responses.

    Used in: GET /results/{id}, GET /results endpoint
    Contains: All fields from AnalysisResult model for read operations.
    """

    id: UUID = Field(..., description="Unique identifier for the analysis result")
    job_id: UUID = Field(..., description="Foreign key to the parent analysis job")
    provider: AnalysisProvider = Field(..., description="AI provider used for analysis")
    model: str = Field(..., description="Specific model identifier used for analysis")
    result_json: dict = Field(..., description="Full analysis result as JSON")
    confidence: Optional[float] = Field(
        None,
        description="Confidence score of the analysis (0.0-1.0)"
    )
    tokens_used: Optional[int] = Field(
        None,
        description="Number of tokens consumed by the analysis"
    )
    latency_ms: Optional[int] = Field(
        None,
        description="Processing latency in milliseconds"
    )
    created_at: datetime = Field(..., description="UTC timestamp when result was recorded")
    updated_at: datetime = Field(..., description="UTC timestamp when result was last updated")

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
                "provider": "minimax",
                "model": "minimax-video-2.0",
                "result_json": {"summary": "A video about technology", "topics": ["AI", "ML"]},
                "confidence": 0.95,
                "tokens_used": 1500,
                "latency_ms": 5000,
                "created_at": "2026-01-20T10:00:00Z",
                "updated_at": "2026-01-20T10:05:00Z"
            }
        }
    )


class AnalysisResultListResponse(BaseModel):
    """Schema for paginated list of analysis results."""

    items: List[AnalysisResultResponse] = Field(..., description="List of analysis results")
    total: int = Field(..., description="Total number of results")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether more pages exist")


# Forward references for nested schemas (resolved at end of file)
from api.schemas.job import JobResponse

AnalysisResultResponse.model_rebuild()
