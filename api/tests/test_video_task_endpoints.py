"""Endpoint-level contract tests for the self-hosted video task APIs."""

import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from api.main import (
    cancel_control_video_task,
    create_control_video_task,
    create_video_task,
    get_video_task,
    list_control_video_tasks,
    list_video_tasks,
)
from api.repositories.job import JobRepository
from api.schemas.job import JobStatus
from api.schemas.video_task import (
    ControlVideoTaskCreate,
    ControlVideoTaskType,
    MagiHumanTaskCreate,
    MagiHumanTaskType,
)


@pytest.mark.asyncio
async def test_create_video_task_persists_staged_job(test_session):
    """Avatar-first create route should persist a staged task-backed job."""
    repo = JobRepository(test_session)

    response = await create_video_task(
        MagiHumanTaskCreate(
            task_type=MagiHumanTaskType.DISTILL,
            input={
                "prompt": "A woman speaks directly to camera.",
                "image_url": "https://example.com/ref.png",
                "audio_url": "https://example.com/voice.wav",
            },
        ),
        repo=repo,
    )

    assert response.code == 201
    assert response.data.status == JobStatus.STAGED
    assert response.data.model == "magihuman"
    assert response.data.task_type == "magihuman-distill"
    assert response.data.meta.backend == "magihuman-distill"

    stored_job = await repo.get_by_id(response.data.task_id)
    assert stored_job is not None
    assert stored_job.status == JobStatus.STAGED
    assert stored_job.metadata_json["task"]["family"] == "video"


@pytest.mark.asyncio
async def test_list_routes_split_video_families(test_session):
    """Video and control-video list routes should only return their own family."""
    repo = JobRepository(test_session)

    await create_video_task(
        MagiHumanTaskCreate(
            task_type=MagiHumanTaskType.BASE,
            input={
                "prompt": "A presenter addresses the audience.",
                "image_url": "https://example.com/ref.png",
            },
        ),
        repo=repo,
    )
    await create_control_video_task(
        ControlVideoTaskCreate(
            task_type=ControlVideoTaskType.TI2V_5B,
            input={"prompt": "A camera move through a hallway."},
        ),
        repo=repo,
    )

    avatar_tasks = await list_video_tasks(repo=repo)
    control_tasks = await list_control_video_tasks(repo=repo)

    assert avatar_tasks.data.total == 1
    assert control_tasks.data.total == 1
    assert avatar_tasks.data.items[0].model == "magihuman"
    assert control_tasks.data.items[0].model == "wan22"


@pytest.mark.asyncio
async def test_cancel_control_video_task_marks_terminal_state(test_session):
    """Cancel route should move a queued control task into canceled state."""
    repo = JobRepository(test_session)

    created = await create_control_video_task(
        ControlVideoTaskCreate(
            task_type=ControlVideoTaskType.S2V_14B,
            input={
                "prompt": "A presenter follows the voice track.",
                "image_url": "https://example.com/ref.png",
                "audio_url": "https://example.com/voice.wav",
            },
        ),
        repo=repo,
    )

    canceled = await cancel_control_video_task(
        str(created.data.task_id),
        repo=repo,
    )

    assert canceled.code == 200
    assert canceled.data.status == JobStatus.CANCELED
    assert canceled.data.error == "Task canceled by user"
    assert canceled.data.meta.ended_at is not None


@pytest.mark.asyncio
async def test_get_video_task_rejects_wrong_family(test_session):
    """Avatar route should not expose control-video tasks."""
    repo = JobRepository(test_session)

    created = await create_control_video_task(
        ControlVideoTaskCreate(
            task_type=ControlVideoTaskType.TI2V_5B,
            input={"prompt": "A simple tracking shot."},
        ),
        repo=repo,
    )

    with pytest.raises(HTTPException) as exc:
        await get_video_task(str(created.data.task_id), repo=repo)

    assert exc.value.status_code == 404
