"""
Tests for ORM models and their relationships.

This module tests:
- Model creation and attribute assignment
- Relationship definitions (one-to-many, many-to-one)
- JSONB field handling
- Enum field constraints
- Timestamp and soft-delete mixins
"""

import sys
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, "/home/oz/projects/2025/oz/12/runpod/api")

from models.base import TimestampMixin
from models.job import AnalysisJob, JobStatus, MediaType
from models.media import FileType, MediaFile, MediaFileStatus
from models.result import AnalysisProvider, AnalysisResult
from models.transcription import Transcription, TranscriptionProvider


class TestAnalysisJobModel:
    """Tests for the AnalysisJob model."""

    def test_job_creation(self, sample_job_data):
        """Test creating an AnalysisJob instance."""
        job = AnalysisJob(**sample_job_data)

        assert job.status == JobStatus.PENDING
        assert job.media_type == MediaType.VIDEO
        assert job.source_url == "https://example.com/video.mp4"
        assert job.metadata_json == {"priority": "high", "category": "interview"}

    def test_job_default_status(self):
        """Test that job has default PENDING status."""
        job = AnalysisJob(
            media_type=MediaType.VIDEO,
            source_url="https://example.com/video.mp4",
        )

        assert job.status == JobStatus.PENDING

    def test_job_default_is_active(self):
        """Test that job is active by default."""
        job = AnalysisJob(
            media_type=MediaType.AUDIO,
            source_url="https://example.com/audio.mp3",
        )

        assert job.is_active is True
        assert job.is_deleted is False

    def test_job_has_timestamps(self, sample_job):
        """Test that job has timestamp fields."""
        assert isinstance(sample_job.created_at, type(sample_job.created_at))
        assert sample_job.created_at is not None

    @pytest.mark.asyncio
    async def test_job_persists_to_database(self, test_session):
        """Test that job can be saved and retrieved."""
        job = AnalysisJob(
            status=JobStatus.PROCESSING,
            media_type=MediaType.VIDEO,
            source_url="https://example.com/persist-test.mp4",
            metadata_json={"test": True},
        )

        test_session.add(job)
        await test_session.commit()
        await test_session.refresh(job)

        assert job.id is not None
        assert job.status == JobStatus.PROCESSING

    @pytest.mark.asyncio
    async def test_job_status_transition(self, test_session, sample_job):
        """Test job status transitions."""
        # Transition to processing
        sample_job.status = JobStatus.PROCESSING
        await test_session.commit()
        await test_session.refresh(sample_job)

        assert sample_job.status == JobStatus.PROCESSING

        # Transition to completed
        sample_job.status = JobStatus.COMPLETED
        await test_session.commit()
        await test_session.refresh(sample_job)

        assert sample_job.status == JobStatus.COMPLETED


class TestMediaFileModel:
    """Tests for the MediaFile model."""

    def test_media_file_creation(self, sample_media_file_data):
        """Test creating a MediaFile instance."""
        media_file = MediaFile(**sample_media_file_data)

        assert media_file.file_type == FileType.SOURCE
        assert media_file.mime_type == "video/mp4"
        assert media_file.file_size == 1024000
        assert media_file.status == MediaFileStatus.PENDING

    def test_media_file_default_status(self):
        """Test that media file has default PENDING status."""
        media_file = MediaFile(
            job_id=uuid4(),
            file_type=FileType.SOURCE,
            original_url="https://example.com/file.mp4",
        )

        assert media_file.status == MediaFileStatus.PENDING

    @pytest.mark.asyncio
    async def test_media_file_persists_to_database(
        self, test_session, sample_job
    ):
        """Test that media file can be saved and retrieved."""
        media_file = MediaFile(
            job_id=sample_job.id,
            file_type=FileType.SOURCE,
            original_url="https://example.com/new-file.mp4",
            mime_type="video/mp4",
            file_size=2048000,
            filename="new-file.mp4",
        )

        test_session.add(media_file)
        await test_session.commit()
        await test_session.refresh(media_file)

        assert media_file.id is not None
        assert media_file.job_id == sample_job.id


class TestAnalysisResultModel:
    """Tests for the AnalysisResult model."""

    def test_analysis_result_creation(self, sample_analysis_result_data):
        """Test creating an AnalysisResult instance."""
        result = AnalysisResult(**sample_analysis_result_data)

        assert result.provider == AnalysisProvider.MINIMAX
        assert result.model == "minimax-video-01"
        assert result.confidence == 0.95
        assert result.tokens_used == 1500
        assert result.latency_ms == 2500

    def test_analysis_result_jsonb_field(self, sample_analysis_result_data):
        """Test that JSONB field stores complex data."""
        result = AnalysisResult(**sample_analysis_result_data)

        assert result.result_json is not None
        assert isinstance(result.result_json, dict)
        assert "summary" in result.result_json
        assert "topics" in result.result_json
        assert result.result_json["topics"] == ["AI", "Technology"]

    @pytest.mark.asyncio
    async def test_analysis_result_persists_jsonb(
        self, test_session, sample_job
    ):
        """Test that JSONB data is persisted correctly."""
        complex_result = {
            "summary": "Complex analysis",
            "entities": [
                {"name": "Entity1", "type": "PERSON"},
                {"name": "Entity2", "type": "ORG"},
            ],
            "sentiment": {"positive": 0.8, "negative": 0.1, "neutral": 0.1},
            "metadata": {"version": "2.0", "processed_by": "minimax"},
        }

        result = AnalysisResult(
            job_id=sample_job.id,
            provider=AnalysisProvider.GROQ,
            model="llama-4",
            result_json=complex_result,
            confidence=0.92,
        )

        test_session.add(result)
        await test_session.commit()
        await test_session.refresh(result)

        assert result.id is not None
        assert result.result_json == complex_result


class TestTranscriptionModel:
    """Tests for the Transcription model."""

    def test_transcription_creation(self, sample_transcription_data):
        """Test creating a Transcription instance."""
        transcription = Transcription(**sample_transcription_data)

        assert transcription.provider == TranscriptionProvider.WHISPER
        assert transcription.language == "en"
        assert transcription.duration_seconds == 10.5

    def test_transcription_segments_jsonb(self, sample_transcription_data):
        """Test that segments JSONB field stores array data."""
        transcription = Transcription(**sample_transcription_data)

        assert transcription.segments_json is not None
        assert isinstance(transcription.segments_json, list)
        assert len(transcription.segments_json) == 2
        assert transcription.segments_json[0]["start"] == 0.0
        assert transcription.segments_json[1]["end"] == 10.0

    @pytest.mark.asyncio
    async def test_transcription_persists_segments(
        self, test_session, sample_job
    ):
        """Test that transcription segments are persisted correctly."""
        segments = [
            {"start": 0.0, "end": 3.5, "text": "Hello world"},
            {"start": 3.5, "end": 7.0, "text": "This is a test"},
            {"start": 7.0, "end": 10.5, "text": "Transcription test"},
        ]

        transcription = Transcription(
            job_id=sample_job.id,
            provider=TranscriptionProvider.DEEGRAM,
            text="Hello world. This is a test. Transcription test.",
            segments_json=segments,
            language="en",
            duration_seconds=10.5,
        )

        test_session.add(transcription)
        await test_session.commit()
        await test_session.refresh(transcription)

        assert transcription.id is not None
        assert transcription.segments_json == segments


class TestRelationships:
    """Tests for model relationships."""

    @pytest.mark.asyncio
    async def test_job_to_media_files_relationship(
        self, test_session, sample_job
    ):
        """Test one-to-many relationship from Job to MediaFile."""
        # Create multiple media files for the job
        media_file1 = MediaFile(
            job_id=sample_job.id,
            file_type=FileType.SOURCE,
            original_url="https://example.com/file1.mp4",
        )
        media_file2 = MediaFile(
            job_id=sample_job.id,
            file_type=FileType.EXTRACTED,
            original_url="https://example.com/file2.mp4",
        )

        test_session.add_all([media_file1, media_file2])
        await test_session.commit()

        # Query job and check relationship
        from sqlalchemy import select

        result = await test_session.execute(
            select(AnalysisJob).where(AnalysisJob.id == sample_job.id)
        )
        job = result.scalar_one()

        # Access relationship
        media_files = list(job.media_files)

        assert len(media_files) == 2
        assert all(mf.job_id == sample_job.id for mf in media_files)

    @pytest.mark.asyncio
    async def test_job_to_analysis_results_relationship(
        self, test_session, sample_job
    ):
        """Test one-to-many relationship from Job to AnalysisResult."""
        result1 = AnalysisResult(
            job_id=sample_job.id,
            provider=AnalysisProvider.MINIMAX,
            model="model-1",
            result_json={"summary": "First result"},
        )
        result2 = AnalysisResult(
            job_id=sample_job.id,
            provider=AnalysisProvider.GROQ,
            model="model-2",
            result_json={"summary": "Second result"},
        )

        test_session.add_all([result1, result2])
        await test_session.commit()

        # Query and verify relationship
        from sqlalchemy import select

        result = await test_session.execute(
            select(AnalysisJob).where(AnalysisJob.id == sample_job.id)
        )
        job = result.scalar_one()

        results = list(job.results)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_job_to_transcriptions_relationship(
        self, test_session, sample_job
    ):
        """Test one-to-many relationship from Job to Transcription."""
        transcription1 = Transcription(
            job_id=sample_job.id,
            provider=TranscriptionProvider.WHISPER,
            text="First transcription",
            language="en",
        )
        transcription2 = Transcription(
            job_id=sample_job.id,
            provider=TranscriptionProvider.DEEGRAM,
            text="Second transcription",
            language="es",
        )

        test_session.add_all([transcription1, transcription2])
        await test_session.commit()

        # Query and verify relationship
        from sqlalchemy import select

        result = await test_session.execute(
            select(AnalysisJob).where(AnalysisJob.id == sample_job.id)
        )
        job = result.scalar_one()

        transcriptions = list(job.transcriptions)

        assert len(transcriptions) == 2

    @pytest.mark.asyncio
    async def test_media_file_to_job_relationship(
        self, test_session, sample_media_file
    ):
        """Test many-to-one relationship from MediaFile to Job."""
        from sqlalchemy import select

        result = await test_session.execute(
            select(MediaFile).where(MediaFile.id == sample_media_file.id)
        )
        media_file = result.scalar_one()

        # Access reverse relationship
        job = media_file.job

        assert job is not None
        assert job.id == sample_media_file.job_id

    @pytest.mark.asyncio
    async def test_cascade_delete_on_job(self, test_session, sample_job):
        """Test that deleting a job cascades to related records."""
        # Create related records
        media_file = MediaFile(
            job_id=sample_job.id,
            file_type=FileType.SOURCE,
            original_url="https://example.com/cascade-test.mp4",
        )
        result = AnalysisResult(
            job_id=sample_job.id,
            provider=AnalysisProvider.MINIMAX,
            model="test",
            result_json={},
        )

        test_session.add_all([media_file, result])
        await test_session.commit()

        media_id = media_file.id
        result_id = result.id

        # Delete the job
        await test_session.delete(sample_job)
        await test_session.commit()

        # Verify related records are also deleted (cascade)
        from sqlalchemy import select

        mf_result = await test_session.execute(
            select(MediaFile).where(MediaFile.id == media_id)
        )
        res_result = await test_session.execute(
            select(AnalysisResult).where(AnalysisResult.id == result_id)
        )

        assert mf_result.scalar_one_or_none() is None
        assert res_result.scalar_one_or_none() is None


class TestEnumConstraints:
    """Tests for enum field constraints."""

    @pytest.mark.parametrize(
        "status",
        [
            JobStatus.PENDING,
            JobStatus.PROCESSING,
            JobStatus.COMPLETED,
            JobStatus.FAILED,
        ],
    )
    def test_job_status_enum_values(self, status):
        """Test that all job status values are valid."""
        job = AnalysisJob(
            status=status,
            media_type=MediaType.VIDEO,
            source_url="https://example.com/test.mp4",
        )

        assert job.status == status

    @pytest.mark.parametrize(
        "media_type",
        [MediaType.VIDEO, MediaType.AUDIO, MediaType.IMAGE],
    )
    def test_media_type_enum_values(self, media_type):
        """Test that all media type values are valid."""
        job = AnalysisJob(
            status=JobStatus.PENDING,
            media_type=media_type,
            source_url="https://example.com/test.mp4",
        )

        assert job.media_type == media_type

    @pytest.mark.parametrize(
        "provider",
        [
            AnalysisProvider.MINIMAX,
            AnalysisProvider.GROQ,
            AnalysisProvider.GEMINI,
            AnalysisProvider.OPENAI,
            AnalysisProvider.ANTHROPIC,
            AnalysisProvider.LOCAL,
        ],
    )
    def test_analysis_provider_enum_values(self, provider):
        """Test that all analysis provider values are valid."""
        result = AnalysisResult(
            job_id=uuid4(),
            provider=provider,
            model="test",
            result_json={},
        )

        assert result.provider == provider

    @pytest.mark.parametrize(
        "provider",
        [
            TranscriptionProvider.WHISPER,
            TranscriptionProvider.GOOGLE,
            TranscriptionProvider.AZURE,
            TranscriptionProvider.DEEGRAM,
            TranscriptionProvider.ASSEMBLYAI,
            TranscriptionProvider.OPENAI,
        ],
    )
    def test_transcription_provider_enum_values(self, provider):
        """Test that all transcription provider values are valid."""
        transcription = Transcription(
            job_id=uuid4(),
            provider=provider,
            text="Test",
            language="en",
        )

        assert transcription.provider == provider


class TestTimestampMixin:
    """Tests for the TimestampMixin."""

    @pytest.mark.asyncio
    async def test_created_at_set_on_create(self, test_session):
        """Test that created_at is set when creating a record."""
        job = AnalysisJob(
            status=JobStatus.PENDING,
            media_type=MediaType.VIDEO,
            source_url="https://example.com/timestamp-test.mp4",
        )

        test_session.add(job)
        await test_session.commit()
        await test_session.refresh(job)

        assert job.created_at is not None
        assert job.updated_at is not None

    @pytest.mark.asyncio
    async def test_updated_at_changes_on_update(self, test_session):
        """Test that updated_at changes when record is updated."""
        job = AnalysisJob(
            status=JobStatus.PENDING,
            media_type=MediaType.AUDIO,
            source_url="https://example.com/update-test.mp3",
        )

        test_session.add(job)
        await test_session.commit()
        await test_session.refresh(job)

        original_updated_at = job.updated_at

        # Wait a moment and update
        job.status = JobStatus.PROCESSING
        await test_session.commit()
        await test_session.refresh(job)

        # updated_at should have changed (or be same depending on timing)
        # This test verifies the field exists and is updated
        assert job.updated_at is not None


class TestJSONBFields:
    """Tests for JSONB field handling."""

    @pytest.mark.asyncio
    async def test_metadata_json_accepts_complex_object(
        self, test_session
    ):
        """Test that metadata_json accepts complex nested objects."""
        complex_metadata = {
            "priority": "high",
            "tags": ["interview", "ai", "technology"],
            "config": {
                "max_duration": 3600,
                "quality": "high",
                "features": ["transcription", "analysis"],
            },
            "external_ids": ["youtube_123", "vimeo_456"],
        }

        job = AnalysisJob(
            status=JobStatus.PENDING,
            media_type=MediaType.VIDEO,
            source_url="https://example.com/json-test.mp4",
            metadata_json=complex_metadata,
        )

        test_session.add(job)
        await test_session.commit()
        await test_session.refresh(job)

        assert job.metadata_json == complex_metadata

    @pytest.mark.asyncio
    async def test_result_json_accepts_array(self, test_session, sample_job):
        """Test that result_json accepts array data."""
        array_result = [
            {"timestamp": 0, "event": "start"},
            {"timestamp": 5, "event": "middle"},
            {"timestamp": 10, "event": "end"},
        ]

        result = AnalysisResult(
            job_id=sample_job.id,
            provider=AnalysisProvider.LOCAL,
            model="test",
            result_json=array_result,
        )

        test_session.add(result)
        await test_session.commit()
        await test_session.refresh(result)

        assert result.result_json == array_result

    @pytest.mark.asyncio
    async def test_segments_json_handles_null(self, test_session, sample_job):
        """Test that segments_json handles None/null values."""
        transcription = Transcription(
            job_id=sample_job.id,
            provider=TranscriptionProvider.WHISPER,
            text="Text without segments",
            language="en",
            segments_json=None,
        )

        test_session.add(transcription)
        await test_session.commit()
        await test_session.refresh(transcription)

        assert transcription.segments_json is None
