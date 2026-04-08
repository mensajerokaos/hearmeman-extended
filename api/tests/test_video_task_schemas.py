"""Tests for the self-hosted video task schema contract."""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from api.schemas.job import JobStatus
from api.schemas.video_task import (
    ControlVideoTaskCreate,
    ControlVideoTaskType,
    MagiHumanTaskCreate,
    MagiHumanTaskType,
    VideoTaskEnvelope,
    VideoTaskMeta,
    VideoTaskOutput,
)


class TestMagiHumanTaskCreate:
    """Validation tests for avatar-first task creation."""

    def test_requires_reference_image(self):
        """MagiHuman requests require image_url."""
        with pytest.raises(ValidationError):
            MagiHumanTaskCreate(
                task_type=MagiHumanTaskType.DISTILL,
                input={"prompt": "A person speaks to camera."},
            )

    def test_accepts_audio_conditioning(self):
        """MagiHuman accepts image-driven tasks with optional audio."""
        task = MagiHumanTaskCreate(
            task_type=MagiHumanTaskType.BASE,
            input={
                "prompt": "A presenter speaks to camera.",
                "image_url": "https://example.com/ref.png",
                "audio_url": "https://example.com/voice.wav",
                "duration_seconds": 5,
            },
        )

        assert task.model == "magihuman"
        assert task.task_type == MagiHumanTaskType.BASE
        assert task.input.audio_url == "https://example.com/voice.wav"


class TestControlVideoTaskCreate:
    """Validation tests for control-first task creation."""

    def test_s2v_requires_image_and_audio(self):
        """S2V needs both image_url and audio_url."""
        with pytest.raises(ValidationError):
            ControlVideoTaskCreate(
                task_type=ControlVideoTaskType.S2V_14B,
                input={
                    "prompt": "A presenter follows the voice track.",
                    "image_url": "https://example.com/ref.png",
                },
            )

    def test_animate_requires_pose_or_reference_video(self):
        """Animate needs a driving asset in addition to image_url."""
        with pytest.raises(ValidationError):
            ControlVideoTaskCreate(
                task_type=ControlVideoTaskType.ANIMATE_14B,
                input={
                    "prompt": "Animate the presenter.",
                    "image_url": "https://example.com/ref.png",
                },
            )

    def test_ti2v_can_be_minimal(self):
        """TI2V can be created with prompt-only input."""
        task = ControlVideoTaskCreate(
            task_type=ControlVideoTaskType.TI2V_5B,
            input={"prompt": "A cinematic pan across the room."},
        )

        assert task.model == "wan22"
        assert task.task_type == ControlVideoTaskType.TI2V_5B


def test_video_task_envelope_accepts_public_status():
    """The response envelope should accept the staged public task state."""
    payload = VideoTaskEnvelope(
        code=200,
        data={
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "model": "magihuman",
            "task_type": "magihuman-distill",
            "status": JobStatus.STAGED,
            "input": {"prompt": "A presenter speaks to camera."},
            "output": VideoTaskOutput(video=None),
            "meta": VideoTaskMeta(
                created_at="2026-04-08T00:00:00Z",
                backend="magihuman-distill",
                gpu_type="H100",
                runner_name="magihuman-official-entry",
                mode="distill",
            ),
            "error": None,
        },
    )

    assert payload.data.status == JobStatus.STAGED
