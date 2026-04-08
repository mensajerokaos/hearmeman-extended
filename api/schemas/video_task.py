"""
Schemas for self-hosted video task APIs.

These schemas define the public async task contract used by the
MagiHuman and control-first video endpoints.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from api.schemas.job import JobStatus


class MagiHumanTaskType(StrEnum):
    """Public task types supported by the MagiHuman endpoint."""

    DISTILL = "magihuman-distill"
    BASE = "magihuman-base"
    SR_540P = "magihuman-sr-540p"
    SR_1080P = "magihuman-sr-1080p"


class ControlVideoTaskType(StrEnum):
    """Public task types supported by the control-first endpoint."""

    TI2V_5B = "ti2v-5b"
    S2V_14B = "s2v-14b"
    ANIMATE_14B = "animate-14b"


class VideoTaskConfig(BaseModel):
    """Optional delivery configuration for async tasks."""

    webhook_url: str | None = Field(
        None,
        max_length=2048,
        description="Optional webhook URL for task completion callbacks",
    )
    webhook_secret: str | None = Field(
        None,
        max_length=512,
        description="Optional shared secret for webhook verification",
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MagiHumanTaskInput(BaseModel):
    """Input payload for MagiHuman tasks."""

    prompt: str = Field(..., min_length=1, description="Generation prompt")
    image_url: str | None = Field(
        None,
        max_length=2048,
        description="Reference image URL",
    )
    audio_url: str | None = Field(
        None,
        max_length=2048,
        description="Optional driving audio URL",
    )
    duration_seconds: int | None = Field(
        None,
        ge=1,
        le=30,
        description="Requested output duration in seconds",
    )
    aspect_ratio: str | None = Field(
        None,
        max_length=32,
        description="Requested aspect ratio such as 16:9",
    )
    seed: int | None = Field(None, description="Optional deterministic seed")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ControlVideoTaskInput(BaseModel):
    """Input payload for control-first video tasks."""

    prompt: str = Field(..., min_length=1, description="Generation prompt")
    image_url: str | None = Field(
        None,
        max_length=2048,
        description="Reference image URL",
    )
    audio_url: str | None = Field(
        None,
        max_length=2048,
        description="Optional driving audio URL",
    )
    pose_video_url: str | None = Field(
        None,
        max_length=2048,
        description="Optional pose guide video URL",
    )
    reference_video_url: str | None = Field(
        None,
        max_length=2048,
        description="Optional reference video URL for animation pipelines",
    )
    face_image_url: str | None = Field(
        None,
        max_length=2048,
        description="Optional face asset URL for replacement tasks",
    )
    background_image_url: str | None = Field(
        None,
        max_length=2048,
        description="Optional background asset URL",
    )
    size: str | None = Field(
        None,
        max_length=32,
        description="Requested canvas size such as 1024x704",
    )
    seed: int | None = Field(None, description="Optional deterministic seed")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MagiHumanTaskCreate(BaseModel):
    """Request body for the avatar-first endpoint."""

    model: Literal["magihuman"] = Field(
        default="magihuman",
        description="Public model family identifier",
    )
    task_type: MagiHumanTaskType = Field(..., description="Requested MagiHuman mode")
    input: MagiHumanTaskInput = Field(..., description="Task input payload")
    config: VideoTaskConfig = Field(
        default_factory=VideoTaskConfig,
        description="Optional delivery configuration",
    )

    @model_validator(mode="after")
    def validate_payload(self) -> "MagiHumanTaskCreate":
        """Validate MagiHuman-specific requirements."""
        if not self.input.image_url:
            raise ValueError("image_url is required for MagiHuman tasks")
        return self

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ControlVideoTaskCreate(BaseModel):
    """Request body for the control-first endpoint."""

    model: Literal["wan22"] = Field(
        default="wan22",
        description="Public model family identifier",
    )
    task_type: ControlVideoTaskType = Field(..., description="Requested Wan task type")
    input: ControlVideoTaskInput = Field(..., description="Task input payload")
    config: VideoTaskConfig = Field(
        default_factory=VideoTaskConfig,
        description="Optional delivery configuration",
    )

    @model_validator(mode="after")
    def validate_payload(self) -> "ControlVideoTaskCreate":
        """Validate control-first requirements by task type."""
        if self.task_type == ControlVideoTaskType.S2V_14B:
            if not self.input.image_url or not self.input.audio_url:
                raise ValueError("s2v-14b requires both image_url and audio_url")

        if self.task_type == ControlVideoTaskType.ANIMATE_14B:
            if not self.input.image_url:
                raise ValueError("animate-14b requires image_url")
            if not (self.input.pose_video_url or self.input.reference_video_url):
                raise ValueError(
                    "animate-14b requires pose_video_url or reference_video_url"
                )

        return self

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class VideoTaskOutput(BaseModel):
    """Public output fields for async video tasks."""

    video: str | None = Field(None, description="Stable video artifact URL")
    audio: str | None = Field(None, description="Optional stable audio artifact URL")
    artifacts: dict[str, str] = Field(
        default_factory=dict,
        description="Additional named artifact URLs",
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class VideoTaskMeta(BaseModel):
    """Public metadata payload for async video tasks."""

    created_at: datetime = Field(..., description="Task creation timestamp")
    started_at: datetime | None = Field(
        None,
        description="Timestamp when the runner started processing",
    )
    ended_at: datetime | None = Field(
        None,
        description="Timestamp when the task reached a terminal state",
    )
    backend: str | None = Field(None, description="Resolved backend identifier")
    gpu_type: str | None = Field(None, description="Intended GPU tier")
    runner_name: str | None = Field(None, description="Internal runner identifier")
    mode: str | None = Field(None, description="Mode or quality tier")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class VideoTaskData(BaseModel):
    """Public task representation returned by the async task APIs."""

    task_id: UUID = Field(..., description="Unique task identifier")
    model: str = Field(..., description="Public model family identifier")
    task_type: str = Field(..., description="Public task type")
    status: JobStatus = Field(..., description="Current public task status")
    input: dict[str, Any] = Field(default_factory=dict, description="Input payload")
    output: VideoTaskOutput = Field(
        default_factory=VideoTaskOutput,
        description="Resolved artifact payload",
    )
    meta: VideoTaskMeta = Field(..., description="Execution metadata")
    error: str | None = Field(None, description="Error details for failed tasks")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class VideoTaskEnvelope(BaseModel):
    """Standard single-task envelope."""

    code: int = Field(..., description="Application-level status code")
    data: VideoTaskData = Field(..., description="Task payload")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class VideoTaskListData(BaseModel):
    """Paginated task list payload."""

    items: list[VideoTaskData] = Field(..., description="List of task payloads")
    total: int = Field(..., description="Total items matching the filter")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether more pages exist")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class VideoTaskListEnvelope(BaseModel):
    """Standard task list envelope."""

    code: int = Field(..., description="Application-level status code")
    data: VideoTaskListData = Field(..., description="Paginated task payload")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
