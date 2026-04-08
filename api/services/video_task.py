"""
Helpers for self-hosted video task APIs.

These functions keep the FastAPI layer thin while allowing the async task
contract to be backed by the existing analysis_job table.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from api.models.job import AnalysisJob, JobStatus, MediaType
from api.schemas.video_task import (
    ControlVideoTaskCreate,
    MagiHumanTaskCreate,
    VideoTaskData,
    VideoTaskListData,
    VideoTaskMeta,
    VideoTaskOutput,
)

VIDEO_TASK_FAMILY = "video"
CONTROL_VIDEO_TASK_FAMILY = "control-video"
TASK_METADATA_KEY = "task"


@dataclass(frozen=True)
class RunnerSpec:
    """Resolved runtime metadata for a public task type."""

    backend: str
    gpu_type: str
    runner_name: str
    mode: str


RUNNER_SPECS: dict[str, dict[str, RunnerSpec]] = {
    VIDEO_TASK_FAMILY: {
        "magihuman-distill": RunnerSpec(
            backend="magihuman-distill",
            gpu_type="H100",
            runner_name="magihuman-official-entry",
            mode="distill",
        ),
        "magihuman-base": RunnerSpec(
            backend="magihuman-base",
            gpu_type="H100",
            runner_name="magihuman-official-entry",
            mode="base",
        ),
        "magihuman-sr-540p": RunnerSpec(
            backend="magihuman-sr-540p",
            gpu_type="H100",
            runner_name="magihuman-super-resolution",
            mode="540p",
        ),
        "magihuman-sr-1080p": RunnerSpec(
            backend="magihuman-sr-1080p",
            gpu_type="H100",
            runner_name="magihuman-super-resolution",
            mode="1080p",
        ),
    },
    CONTROL_VIDEO_TASK_FAMILY: {
        "ti2v-5b": RunnerSpec(
            backend="wan22-ti2v-5b",
            gpu_type="24GB+",
            runner_name="wan-direct-ti2v",
            mode="ti2v",
        ),
        "s2v-14b": RunnerSpec(
            backend="wan22-s2v-14b",
            gpu_type="H100",
            runner_name="wan-direct-s2v",
            mode="s2v",
        ),
        "animate-14b": RunnerSpec(
            backend="wan22-animate-14b",
            gpu_type="H100",
            runner_name="wan-direct-animate",
            mode="animate",
        ),
    },
}

TERMINAL_STATUSES = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELED}


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def utcnow_iso() -> str:
    """Return a stable ISO 8601 timestamp."""
    return utcnow().isoformat()


def _parse_datetime(value: Any) -> datetime | None:
    """Parse datetime values stored in task metadata."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    return None


def _task_payload(job: AnalysisJob) -> dict[str, Any]:
    """Return the task-specific metadata payload for a job."""
    metadata = deepcopy(job.metadata_json or {})
    task = metadata.get(TASK_METADATA_KEY)
    if not isinstance(task, dict):
        return {}
    return task


def derive_source_url(input_payload: dict[str, Any]) -> str | None:
    """Pick the best source URL to index on the generic job record."""
    for field_name in (
        "image_url",
        "reference_video_url",
        "pose_video_url",
        "audio_url",
        "face_image_url",
        "background_image_url",
    ):
        value = input_payload.get(field_name)
        if isinstance(value, str) and value:
            return value
    return None


def resolve_runner_spec(task_family: str, task_type: str) -> RunnerSpec:
    """Resolve runtime metadata for a task type."""
    try:
        return RUNNER_SPECS[task_family][task_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported task type '{task_type}' for '{task_family}'") from exc


def build_task_metadata(
    *,
    task_family: str,
    payload: MagiHumanTaskCreate | ControlVideoTaskCreate,
    status: JobStatus = JobStatus.STAGED,
) -> dict[str, Any]:
    """Build the metadata_json payload stored on AnalysisJob."""
    input_payload = payload.input.model_dump(exclude_none=True)
    config_payload = payload.config.model_dump(exclude_none=True)
    runner_spec = resolve_runner_spec(task_family, payload.task_type.value)

    return {
        TASK_METADATA_KEY: {
            "family": task_family,
            "api_version": "v1",
            "model": payload.model,
            "task_type": payload.task_type.value,
            "public_status": status.value,
            "input": input_payload,
            "config": config_payload,
            "output": {},
            "meta": {
                "backend": runner_spec.backend,
                "gpu_type": runner_spec.gpu_type,
                "runner_name": runner_spec.runner_name,
                "mode": runner_spec.mode,
                "accepted_at": utcnow_iso(),
            },
        }
    }


def get_public_status(job: AnalysisJob) -> JobStatus:
    """Resolve the public status for a task-backed job."""
    task = _task_payload(job)
    raw_status = task.get("public_status")
    if raw_status:
        return JobStatus(raw_status)
    return JobStatus(job.status)


def is_task_family(job: AnalysisJob, task_family: str) -> bool:
    """Return True when the job belongs to the requested task family."""
    task = _task_payload(job)
    return task.get("family") == task_family


def apply_public_status(
    job: AnalysisJob,
    *,
    status: JobStatus,
    output: dict[str, str] | None = None,
    error_message: str | None = None,
) -> dict[str, Any]:
    """Return updated metadata_json with task-specific lifecycle fields set."""
    metadata = deepcopy(job.metadata_json or {})
    task = deepcopy(metadata.get(TASK_METADATA_KEY) or {})
    task_meta = deepcopy(task.get("meta") or {})
    task_output = deepcopy(task.get("output") or {})

    task["public_status"] = status.value

    if status == JobStatus.PROCESSING and not task_meta.get("started_at"):
        task_meta["started_at"] = utcnow_iso()

    if status in TERMINAL_STATUSES:
        task_meta["ended_at"] = utcnow_iso()

    if output:
        task_output.update(output)

    if error_message:
        task["error"] = error_message
    elif status != JobStatus.FAILED:
        task.pop("error", None)

    task["meta"] = task_meta
    task["output"] = task_output
    metadata[TASK_METADATA_KEY] = task
    return metadata


def serialize_task(job: AnalysisJob) -> VideoTaskData:
    """Convert an AnalysisJob into the public task representation."""
    task = _task_payload(job)
    task_meta = task.get("meta") or {}
    status = get_public_status(job)
    ended_at = _parse_datetime(task_meta.get("ended_at")) or job.completed_at

    return VideoTaskData(
        task_id=job.id,
        model=task.get("model", "unknown"),
        task_type=task.get("task_type", "unknown"),
        status=status,
        input=task.get("input") or {},
        output=VideoTaskOutput.model_validate(task.get("output") or {}),
        meta=VideoTaskMeta(
            created_at=job.created_at,
            started_at=_parse_datetime(task_meta.get("started_at")),
            ended_at=ended_at,
            backend=task_meta.get("backend"),
            gpu_type=task_meta.get("gpu_type"),
            runner_name=task_meta.get("runner_name"),
            mode=task_meta.get("mode"),
        ),
        error=task.get("error") or job.error_message,
    )


def filter_task_jobs(
    jobs: list[AnalysisJob],
    *,
    task_family: str,
    status: JobStatus | None = None,
    task_type: str | None = None,
) -> list[AnalysisJob]:
    """Filter a list of jobs down to one public task family."""
    filtered: list[AnalysisJob] = []

    for job in jobs:
        if not is_task_family(job, task_family):
            continue
        if status and get_public_status(job) != status:
            continue
        if task_type and _task_payload(job).get("task_type") != task_type:
            continue
        filtered.append(job)

    return filtered


def paginate_task_jobs(
    jobs: list[AnalysisJob],
    *,
    page: int,
    page_size: int,
) -> VideoTaskListData:
    """Build a paginated task response from filtered jobs."""
    offset = (page - 1) * page_size
    page_items = jobs[offset : offset + page_size]

    return VideoTaskListData(
        items=[serialize_task(job) for job in page_items],
        total=len(jobs),
        page=page,
        page_size=page_size,
        has_more=(offset + len(page_items)) < len(jobs),
    )


def default_media_type() -> MediaType:
    """Return the media type used by all current video task families."""
    return MediaType.VIDEO
