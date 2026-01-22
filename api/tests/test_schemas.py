"""
Tests for Pydantic schemas and validation.

This module tests:
- Schema validation rules
- Serialization and deserialization
- Enum handling
- Forward references
- Example payloads
"""

import sys
from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

sys.path.insert(0, "/home/oz/projects/2025/oz/12/runpod/api")

from schemas.job import JobCreate, JobResponse, JobUpdate, JobStatus, MediaType
from schemas.media import (
    MediaFileCreate,
    MediaFileResponse,
    MediaFileUpdate,
    FileType,
    MediaFileStatus,
)
from schemas.result import (
    AnalysisResultCreate,
    AnalysisResultResponse,
    AnalysisResultUpdate,
    AnalysisProvider,
)
from schemas.transcription import (
    TranscriptionCreate,
    TranscriptionResponse,
    TranscriptionUpdate,
    TranscriptionProvider,
)


# =============================================================================
# Job Schema Tests
# =============================================================================

class TestJobCreateSchema:
    """Tests for JobCreate schema validation."""

    def test_valid_job_create(self, valid_job_create_schema):
        """Test creating a valid JobCreate instance."""
        job = JobCreate(**valid_job_create_schema)

        assert job.status == JobStatus.PENDING
        assert job.media_type == MediaType.VIDEO
        assert job.source_url == "https://example.com/video.mp4"
        assert job.metadata_json == {"priority": "high", "tags": ["interview", "ai"]}

    def test_job_create_without_metadata(self):
        """Test JobCreate without optional metadata_json."""
        job = JobCreate(
            status=JobStatus.PENDING,
            media_type=MediaType.AUDIO,
            source_url="https://example.com/audio.mp3",
        )

        assert job.metadata_json is None

    def test_job_create_with_empty_metadata(self):
        """Test JobCreate with empty dict metadata_json."""
        job = JobCreate(
            status=JobStatus.PENDING,
            media_type=MediaType.IMAGE,
            source_url="https://example.com/image.jpg",
            metadata_json={},
        )

        assert job.metadata_json == {}

    def test_job_create_invalid_status(self):
        """Test JobCreate rejects invalid status."""
        with pytest.raises(ValidationError):
            JobCreate(
                status="invalid_status",
                media_type=MediaType.VIDEO,
                source_url="https://example.com/video.mp4",
            )

    def test_job_create_invalid_media_type(self):
        """Test JobCreate rejects invalid media_type."""
        with pytest.raises(ValidationError):
            JobCreate(
                status=JobStatus.PENDING,
                media_type="invalid_type",
                source_url="https://example.com/video.mp4",
            )

    def test_job_create_missing_source_url(self):
        """Test JobCreate requires source_url."""
        with pytest.raises(ValidationError):
            JobCreate(
                status=JobStatus.PENDING,
                media_type=MediaType.VIDEO,
            )

    def test_job_create_missing_media_type(self):
        """Test JobCreate requires media_type."""
        with pytest.raises(ValidationError):
            JobCreate(
                status=JobStatus.PENDING,
                source_url="https://example.com/video.mp4",
            )

    def test_job_create_invalid_url(self):
        """Test JobCreate validates URL format."""
        with pytest.raises(ValidationError):
            JobCreate(
                status=JobStatus.PENDING,
                media_type=MediaType.VIDEO,
                source_url="not-a-valid-url",
            )

    def test_job_create_model_dump(self):
        """Test JobCreate serialization to dict."""
        job = JobCreate(
            status=JobStatus.PROCESSING,
            media_type=MediaType.VIDEO,
            source_url="https://example.com/video.mp4",
            metadata_json={"test": True},
        )

        dumped = job.model_dump()

        assert dumped["status"] == "processing"
        assert dumped["media_type"] == "video"
        assert dumped["source_url"] == "https://example.com/video.mp4"
        assert dumped["metadata_json"] == {"test": True}

    def test_job_create_model_dump_json(self):
        """Test JobCreate serialization to JSON-compatible dict."""
        job = JobCreate(
            status=JobStatus.COMPLETED,
            media_type=MediaType.AUDIO,
            source_url="https://example.com/audio.mp3",
        )

        dumped = job.model_dump(mode="json")

        assert dumped["status"] == "completed"
        assert dumped["media_type"] == "audio"


class TestJobResponseSchema:
    """Tests for JobResponse schema serialization."""

    def test_job_response_from_dict(self, sample_job):
        """Test creating JobResponse from model instance."""
        from schemas.job import JobResponse

        response = JobResponse.model_validate(sample_job)

        assert response.id == sample_job.id
        assert response.status == sample_job.status
        assert response.media_type == sample_job.media_type
        assert response.source_url == sample_job.source_url

    def test_job_response_serialization(self, sample_job):
        """Test JobResponse serializes all fields."""
        from schemas.job import JobResponse

        response = JobResponse.model_validate(sample_job)
        dumped = response.model_dump()

        assert "id" in dumped
        assert "status" in dumped
        assert "media_type" in dumped
        assert "source_url" in dumped
        assert "created_at" in dumped
        assert "updated_at" in dumped
        assert "metadata_json" in dumped

    def test_job_response_json_serialization(self, sample_job):
        """Test JobResponse serializes to JSON."""
        from schemas.job import JobResponse

        response = JobResponse.model_validate(sample_job)
        json_str = response.model_dump_json()

        assert '"id"' in json_str
        assert '"status"' in json_str
        assert "pending" in json_str


class TestJobUpdateSchema:
    """Tests for JobUpdate schema validation."""

    def test_job_update_partial(self):
        """Test JobUpdate allows partial updates."""
        update = JobUpdate(status=JobStatus.PROCESSING)

        assert update.status == JobStatus.PROCESSING
        assert update.media_type is None
        assert update.source_url is None

    def test_job_update_all_fields(self):
        """Test JobUpdate with all fields."""
        update = JobUpdate(
            status=JobStatus.COMPLETED,
            media_type=MediaType.VIDEO,
            source_url="https://example.com/new-url.mp4",
        )

        assert update.status == JobStatus.COMPLETED
        assert update.media_type == MediaType.VIDEO
        assert update.source_url == "https://example.com/new-url.mp4"


# =============================================================================
# Media File Schema Tests
# =============================================================================

class TestMediaFileCreateSchema:
    """Tests for MediaFileCreate schema validation."""

    def test_valid_media_file_create(self, valid_media_file_create_schema):
        """Test creating a valid MediaFileCreate instance."""
        media_file = MediaFileCreate(**valid_media_file_create_schema)

        assert media_file.file_type == FileType.SOURCE
        assert media_file.original_url == "https://example.com/video.mp4"
        assert media_file.mime_type == "video/mp4"
        assert media_file.file_size == 1024000

    def test_media_file_create_without_optional_fields(self):
        """Test MediaFileCreate without optional fields."""
        media_file = MediaFileCreate(
            file_type=FileType.SOURCE,
            original_url="https://example.com/file.mp4",
        )

        assert media_file.mime_type is None
        assert media_file.file_size is None
        assert media_file.filename is None

    def test_media_file_create_invalid_file_type(self):
        """Test MediaFileCreate rejects invalid file_type."""
        with pytest.raises(ValidationError):
            MediaFileCreate(
                file_type="invalid_type",
                original_url="https://example.com/file.mp4",
            )

    def test_media_file_create_negative_file_size(self):
        """Test MediaFileCreate rejects negative file_size."""
        with pytest.raises(ValidationError):
            MediaFileCreate(
                file_type=FileType.SOURCE,
                original_url="https://example.com/file.mp4",
                file_size=-100,
            )


class TestMediaFileResponseSchema:
    """Tests for MediaFileResponse schema serialization."""

    def test_media_file_response_from_dict(self, sample_media_file):
        """Test creating MediaFileResponse from model instance."""
        from schemas.media import MediaFileResponse

        response = MediaFileResponse.model_validate(sample_media_file)

        assert response.id == sample_media_file.id
        assert response.file_type == sample_media_file.file_type
        assert response.original_url == sample_media_file.original_url


# =============================================================================
# Analysis Result Schema Tests
# =============================================================================

class TestAnalysisResultCreateSchema:
    """Tests for AnalysisResultCreate schema validation."""

    def test_valid_analysis_result_create(
        self, valid_analysis_result_create_schema
    ):
        """Test creating a valid AnalysisResultCreate instance."""
        result = AnalysisResultCreate(**valid_analysis_result_create_schema)

        assert result.provider == AnalysisProvider.MINIMAX
        assert result.model == "minimax-video-01"
        assert result.result_json == {"summary": "Test analysis", "topics": ["AI"]}
        assert result.confidence == 0.95
        assert result.tokens_used == 1500
        assert result.latency_ms == 2500

    def test_result_create_without_optional_fields(self):
        """Test AnalysisResultCreate without optional fields."""
        result = AnalysisResultCreate(
            provider=AnalysisProvider.LOCAL,
            model="test-model",
            result_json={},
        )

        assert result.confidence is None
        assert result.tokens_used is None
        assert result.latency_ms is None

    def test_result_create_invalid_provider(self):
        """Test AnalysisResultCreate rejects invalid provider."""
        with pytest.raises(ValidationError):
            AnalysisResultCreate(
                provider="invalid_provider",
                model="test",
                result_json={},
            )

    def test_result_create_confidence_out_of_range(self):
        """Test AnalysisResultCreate validates confidence range."""
        # Confidence > 1
        with pytest.raises(ValidationError):
            AnalysisResultCreate(
                provider=AnalysisProvider.MINIMAX,
                model="test",
                result_json={},
                confidence=1.5,
            )

        # Confidence < 0
        with pytest.raises(ValidationError):
            AnalysisResultCreate(
                provider=AnalysisProvider.MINIMAX,
                model="test",
                result_json={},
                confidence=-0.1,
            )


class TestAnalysisResultResponseSchema:
    """Tests for AnalysisResultResponse schema serialization."""

    def test_analysis_result_response_from_dict(self, sample_analysis_result):
        """Test creating AnalysisResultResponse from model instance."""
        from schemas.result import AnalysisResultResponse

        response = AnalysisResultResponse.model_validate(sample_analysis_result)

        assert response.id == sample_analysis_result.id
        assert response.provider == sample_analysis_result.provider
        assert response.model == sample_analysis_result.model


# =============================================================================
# Transcription Schema Tests
# =============================================================================

class TestTranscriptionCreateSchema:
    """Tests for TranscriptionCreate schema validation."""

    def test_valid_transcription_create(self, valid_transcription_create_schema):
        """Test creating a valid TranscriptionCreate instance."""
        transcription = TranscriptionCreate(**valid_transcription_create_schema)

        assert transcription.provider == TranscriptionProvider.WHISPER
        assert transcription.text == "Sample transcription text"
        assert transcription.segments_json == [
            {"start": 0, "end": 5, "text": "Sample"}
        ]
        assert transcription.language == "en"
        assert transcription.duration_seconds == 5.0

    def test_transcription_create_without_optional_fields(self):
        """Test TranscriptionCreate without optional fields."""
        transcription = TranscriptionCreate(
            provider=TranscriptionProvider.WHISPER,
            text="Sample text",
        )

        assert transcription.segments_json is None
        assert transcription.language is None
        assert transcription.duration_seconds is None

    def test_transcription_create_invalid_provider(self):
        """Test TranscriptionCreate rejects invalid provider."""
        with pytest.raises(ValidationError):
            TranscriptionCreate(
                provider="invalid_provider",
                text="Sample text",
            )

    def test_transcription_create_negative_duration(self):
        """Test TranscriptionCreate rejects negative duration."""
        with pytest.raises(ValidationError):
            TranscriptionCreate(
                provider=TranscriptionProvider.WHISPER,
                text="Sample text",
                duration_seconds=-1.0,
            )


class TestTranscriptionResponseSchema:
    """Tests for TranscriptionResponse schema serialization."""

    def test_transcription_response_from_dict(self, sample_transcription):
        """Test creating TranscriptionResponse from model instance."""
        from schemas.transcription import TranscriptionResponse

        response = TranscriptionResponse.model_validate(sample_transcription)

        assert response.id == sample_transcription.id
        assert response.provider == sample_transcription.provider
        assert response.text == sample_transcription.text


# =============================================================================
# Enum Handling Tests
# =============================================================================

class TestEnumHandling:
    """Tests for enum field handling in schemas."""

    @pytest.mark.parametrize(
        "status_str",
        ["pending", "processing", "completed", "failed"],
    )
    def test_job_status_from_string(self, status_str):
        """Test JobStatus enum from string value."""
        job = JobCreate(
            status=status_str,
            media_type=MediaType.VIDEO,
            source_url="https://example.com/test.mp4",
        )

        assert job.status.value == status_str

    @pytest.mark.parametrize(
        "media_type_str",
        ["video", "audio", "image"],
    )
    def test_media_type_from_string(self, media_type_str):
        """Test MediaType enum from string value."""
        job = JobCreate(
            status=JobStatus.PENDING,
            media_type=media_type_str,
            source_url="https://example.com/test.mp4",
        )

        assert job.media_type.value == media_type_str

    @pytest.mark.parametrize(
        "provider_str",
        ["minimax", "groq", "gemini", "openai", "anthropic", "local"],
    )
    def test_analysis_provider_from_string(self, provider_str):
        """Test AnalysisProvider enum from string value."""
        result = AnalysisResultCreate(
            provider=provider_str,
            model="test",
            result_json={},
        )

        assert result.provider.value == provider_str

    @pytest.mark.parametrize(
        "provider_str",
        ["whisper", "google", "azure", "deepgram", "assemblyai", "openai"],
    )
    def test_transcription_provider_from_string(self, provider_str):
        """Test TranscriptionProvider enum from string value."""
        transcription = TranscriptionCreate(
            provider=provider_str,
            text="Sample text",
        )

        assert transcription.provider.value == provider_str


# =============================================================================
# Serialization Tests
# =============================================================================

class TestSerialization:
    """Tests for schema serialization."""

    def test_job_create_serialization_roundtrip(self):
        """Test JobCreate serialization and deserialization."""
        original = JobCreate(
            status=JobStatus.PENDING,
            media_type=MediaType.VIDEO,
            source_url="https://example.com/test.mp4",
            metadata_json={"key": "value"},
        )

        # Serialize to dict
        dumped = original.model_dump()
        # Deserialize back
        restored = JobCreate(**dumped)

        assert restored.status == original.status
        assert restored.media_type == original.media_type
        assert restored.source_url == original.source_url
        assert restored.metadata_json == original.metadata_json

    def test_media_file_create_serialization_roundtrip(self):
        """Test MediaFileCreate serialization and deserialization."""
        original = MediaFileCreate(
            file_type=FileType.SOURCE,
            original_url="https://example.com/test.mp4",
            mime_type="video/mp4",
            file_size=1024000,
            filename="test.mp4",
        )

        dumped = original.model_dump()
        restored = MediaFileCreate(**dumped)

        assert restored.file_type == original.file_type
        assert restored.original_url == original.original_url
        assert restored.mime_type == original.mime_type
        assert restored.file_size == original.file_size

    def test_analysis_result_create_serialization_roundtrip(self):
        """Test AnalysisResultCreate serialization and deserialization."""
        original = AnalysisResultCreate(
            provider=AnalysisProvider.MINIMAX,
            model="test-model",
            result_json={"data": [1, 2, 3]},
            confidence=0.85,
            tokens_used=1000,
            latency_ms=2000,
        )

        dumped = original.model_dump()
        restored = AnalysisResultCreate(**dumped)

        assert restored.provider == original.provider
        assert restored.model == original.model
        assert restored.result_json == original.result_json
        assert restored.confidence == original.confidence

    def test_transcription_create_serialization_roundtrip(self):
        """Test TranscriptionCreate serialization and deserialization."""
        original = TranscriptionCreate(
            provider=TranscriptionProvider.WHISPER,
            text="Sample transcription",
            segments_json=[{"start": 0, "end": 5, "text": "Sample"}],
            language="en",
            duration_seconds=5.0,
        )

        dumped = original.model_dump()
        restored = TranscriptionCreate(**dumped)

        assert restored.provider == original.provider
        assert restored.text == original.text
        assert restored.segments_json == original.segments_json
        assert restored.language == original.language


# =============================================================================
# Complex Type Tests
# =============================================================================

class TestComplexTypes:
    """Tests for complex type handling in schemas."""

    def test_metadata_json_with_nested_dict(self):
        """Test metadata_json with nested dictionary."""
        nested_metadata = {
            "config": {
                "nested": {
                    "deep": "value",
                }
            },
            "list": [1, 2, 3],
        }

        job = JobCreate(
            status=JobStatus.PENDING,
            media_type=MediaType.VIDEO,
            source_url="https://example.com/test.mp4",
            metadata_json=nested_metadata,
        )

        assert job.metadata_json["config"]["nested"]["deep"] == "value"
        assert job.metadata_json["list"] == [1, 2, 3]

    def test_result_json_with_array(self):
        """Test result_json with array data."""
        array_data = [{"id": 1}, {"id": 2}, {"id": 3}]

        result = AnalysisResultCreate(
            provider=AnalysisProvider.LOCAL,
            model="test",
            result_json=array_data,
        )

        assert result.result_json == array_data
        assert len(result.result_json) == 3

    def test_segments_json_with_timestamps(self):
        """Test segments_json with timestamp data."""
        segments = [
            {"start": 0.0, "end": 2.5, "text": "Hello"},
            {"start": 2.5, "end": 5.0, "text": "World"},
            {"start": 5.0, "end": 10.0, "text": "More text"},
        ]

        transcription = TranscriptionCreate(
            provider=TranscriptionProvider.WHISPER,
            text="Hello World More text",
            segments_json=segments,
        )

        assert len(transcription.segments_json) == 3
        assert transcription.segments_json[0]["start"] == 0.0
        assert transcription.segments_json[2]["end"] == 10.0
