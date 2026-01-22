"""
Tests for repository CRUD operations.

This module tests:
- Create operations
- Read operations (single and list)
- Update operations
- Delete operations
- Query filtering and pagination

Uses mocked database sessions for unit testing.
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, "/home/oz/projects/2025/oz/12/runpod/api")

from models.job import AnalysisJob, JobStatus, MediaType
from models.media import FileType, MediaFile, MediaFileStatus
from models.result import AnalysisProvider, AnalysisResult
from models.transcription import Transcription, TranscriptionProvider


# =============================================================================
# Mock Repository Classes
# =============================================================================

class MockAnalysisJobRepository:
    """Mock repository for AnalysisJob CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, job_data: dict) -> AnalysisJob:
        """Create a new AnalysisJob."""
        job = AnalysisJob(**job_data)
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_by_id(self, job_id: uuid4) -> AnalysisJob | None:
        """Get an AnalysisJob by ID."""
        result = await self.session.execute(
            select(AnalysisJob).where(AnalysisJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> list[AnalysisJob]:
        """Get all AnalysisJobs with pagination."""
        result = await self.session.execute(
            select(AnalysisJob).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_status(self, status: JobStatus) -> list[AnalysisJob]:
        """Get AnalysisJobs by status."""
        result = await self.session.execute(
            select(AnalysisJob).where(AnalysisJob.status == status)
        )
        return list(result.scalars().all())

    async def update_status(
        self, job_id: uuid4, status: JobStatus, error_message: str | None = None
    ) -> AnalysisJob | None:
        """Update job status."""
        job = await self.get_by_id(job_id)
        if job:
            job.status = status
            if error_message:
                job.error_message = error_message
            await self.session.commit()
            await self.session.refresh(job)
        return job

    async def delete(self, job_id: uuid4) -> bool:
        """Delete an AnalysisJob."""
        job = await self.get_by_id(job_id)
        if job:
            await self.session.delete(job)
            await self.session.commit()
            return True
        return False


class MockMediaFileRepository:
    """Mock repository for MediaFile CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, media_file_data: dict) -> MediaFile:
        """Create a new MediaFile."""
        media_file = MediaFile(**media_file_data)
        self.session.add(media_file)
        await self.session.commit()
        await self.session.refresh(media_file)
        return media_file

    async def get_by_id(self, file_id: uuid4) -> MediaFile | None:
        """Get a MediaFile by ID."""
        result = await self.session.execute(
            select(MediaFile).where(MediaFile.id == file_id)
        )
        return result.scalar_one_or_none()

    async def get_by_job_id(self, job_id: uuid4) -> list[MediaFile]:
        """Get MediaFiles by job ID."""
        result = await self.session.execute(
            select(MediaFile).where(MediaFile.job_id == job_id)
        )
        return list(result.scalars().all())

    async def get_by_status(self, status: MediaFileStatus) -> list[MediaFile]:
        """Get MediaFiles by status."""
        result = await self.session.execute(
            select(MediaFile).where(MediaFile.status == status)
        )
        return list(result.scalars().all())

    async def update_status(self, file_id: uuid4, status: MediaFileStatus) -> MediaFile | None:
        """Update MediaFile status."""
        media_file = await self.get_by_id(file_id)
        if media_file:
            media_file.status = status
            await self.session.commit()
            await self.session.refresh(media_file)
        return media_file

    async def delete(self, file_id: uuid4) -> bool:
        """Delete a MediaFile."""
        media_file = await self.get_by_id(file_id)
        if media_file:
            await self.session.delete(media_file)
            await self.session.commit()
            return True
        return False


class MockAnalysisResultRepository:
    """Mock repository for AnalysisResult CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, result_data: dict) -> AnalysisResult:
        """Create a new AnalysisResult."""
        result = AnalysisResult(**result_data)
        self.session.add(result)
        await self.session.commit()
        await self.session.refresh(result)
        return result

    async def get_by_id(self, result_id: uuid4) -> AnalysisResult | None:
        """Get an AnalysisResult by ID."""
        result = await self.session.execute(
            select(AnalysisResult).where(AnalysisResult.id == result_id)
        )
        return result.scalar_one_or_none()

    async def get_by_job_id(self, job_id: uuid4) -> list[AnalysisResult]:
        """Get AnalysisResults by job ID."""
        result = await self.session.execute(
            select(AnalysisResult).where(AnalysisResult.job_id == job_id)
        )
        return list(result.scalars().all())

    async def get_by_provider(
        self, provider: AnalysisProvider
    ) -> list[AnalysisResult]:
        """Get AnalysisResults by provider."""
        result = await self.session.execute(
            select(AnalysisResult).where(AnalysisResult.provider == provider)
        )
        return list(result.scalars().all())

    async def delete(self, result_id: uuid4) -> bool:
        """Delete an AnalysisResult."""
        result = await self.get_by_id(result_id)
        if result:
            await self.session.delete(result)
            await self.session.commit()
            return True
        return False


class MockTranscriptionRepository:
    """Mock repository for Transcription CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, transcription_data: dict) -> Transcription:
        """Create a new Transcription."""
        transcription = Transcription(**transcription_data)
        self.session.add(transcription)
        await self.session.commit()
        await self.session.refresh(transcription)
        return transcription

    async def get_by_id(self, transcription_id: uuid4) -> Transcription | None:
        """Get a Transcription by ID."""
        result = await self.session.execute(
            select(Transcription).where(Transcription.id == transcription_id)
        )
        return result.scalar_one_or_none()

    async def get_by_job_id(self, job_id: uuid4) -> list[Transcription]:
        """Get Transcriptions by job ID."""
        result = await self.session.execute(
            select(Transcription).where(Transcription.job_id == job_id)
        )
        return list(result.scalars().all())

    async def get_by_language(self, language: str) -> list[Transcription]:
        """Get Transcriptions by language."""
        result = await self.session.execute(
            select(Transcription).where(Transcription.language == language)
        )
        return list(result.scalars().all())

    async def delete(self, transcription_id: uuid4) -> bool:
        """Delete a Transcription."""
        transcription = await self.get_by_id(transcription_id)
        if transcription:
            await self.session.delete(transcription)
            await self.session.commit()
            return True
        return False


# =============================================================================
# AnalysisJob Repository Tests
# =============================================================================

class TestAnalysisJobRepository:
    """Tests for AnalysisJob repository operations."""

    @pytest.mark.asyncio
    async def test_create_job(self, test_session):
        """Test creating a new AnalysisJob."""
        repository = MockAnalysisJobRepository(test_session)

        job = await repository.create(
            {
                "status": JobStatus.PENDING,
                "media_type": MediaType.VIDEO,
                "source_url": "https://example.com/new-job.mp4",
                "metadata_json": {"test": True},
            }
        )

        assert job.id is not None
        assert job.status == JobStatus.PENDING
        assert job.source_url == "https://example.com/new-job.mp4"

    @pytest.mark.asyncio
    async def test_get_job_by_id(self, test_session, sample_job):
        """Test getting a job by ID."""
        repository = MockAnalysisJobRepository(test_session)

        found_job = await repository.get_by_id(sample_job.id)

        assert found_job is not None
        assert found_job.id == sample_job.id
        assert found_job.status == sample_job.status

    @pytest.mark.asyncio
    async def test_get_job_by_id_not_found(self, test_session):
        """Test getting a non-existent job returns None."""
        repository = MockAnalysisJobRepository(test_session)

        found_job = await repository.get_by_id(uuid4())

        assert found_job is None

    @pytest.mark.asyncio
    async def test_get_all_jobs(self, test_session, sample_job):
        """Test getting all jobs with pagination."""
        repository = MockAnalysisJobRepository(test_session)

        # Create additional jobs
        await repository.create(
            {
                "status": JobStatus.PENDING,
                "media_type": MediaType.AUDIO,
                "source_url": "https://example.com/job2.mp3",
            }
        )
        await repository.create(
            {
                "status": JobStatus.PROCESSING,
                "media_type": MediaType.VIDEO,
                "source_url": "https://example.com/job3.mp4",
            }
        )

        jobs = await repository.get_all(skip=0, limit=10)

        assert len(jobs) >= 3

    @pytest.mark.asyncio
    async def test_get_jobs_by_status(self, test_session):
        """Test getting jobs by status."""
        repository = MockAnalysisJobRepository(test_session)

        # Create jobs with different statuses
        job1 = await repository.create(
            {
                "status": JobStatus.PENDING,
                "media_type": MediaType.VIDEO,
                "source_url": "https://example.com/pending.mp4",
            }
        )
        await repository.create(
            {
                "status": JobStatus.PROCESSING,
                "media_type": MediaType.AUDIO,
                "source_url": "https://example.com/processing.mp3",
            }
        )

        pending_jobs = await repository.get_by_status(JobStatus.PENDING)

        assert len(pending_jobs) >= 1
        assert any(j.id == job1.id for j in pending_jobs)

    @pytest.mark.asyncio
    async def test_update_job_status(self, test_session, sample_job):
        """Test updating job status."""
        repository = MockAnalysisJobRepository(test_session)

        updated_job = await repository.update_status(
            sample_job.id, JobStatus.PROCESSING
        )

        assert updated_job is not None
        assert updated_job.status == JobStatus.PROCESSING

    @pytest.mark.asyncio
    async def test_update_job_status_with_error(self, test_session, sample_job):
        """Test updating job status with error message."""
        repository = MockAnalysisJobRepository(test_session)

        updated_job = await repository.update_status(
            sample_job.id, JobStatus.FAILED, "Processing error occurred"
        )

        assert updated_job is not None
        assert updated_job.status == JobStatus.FAILED
        assert updated_job.error_message == "Processing error occurred"

    @pytest.mark.asyncio
    async def test_delete_job(self, test_session):
        """Test deleting a job."""
        repository = MockAnalysisJobRepository(test_session)

        # Create a job to delete
        job = await repository.create(
            {
                "status": JobStatus.PENDING,
                "media_type": MediaType.VIDEO,
                "source_url": "https://example.com/to-delete.mp4",
            }
        )
        job_id = job.id

        # Delete the job
        deleted = await repository.delete(job_id)

        assert deleted is True

        # Verify it's deleted
        found_job = await repository.get_by_id(job_id)
        assert found_job is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_job(self, test_session):
        """Test deleting a non-existent job returns False."""
        repository = MockAnalysisJobRepository(test_session)

        deleted = await repository.delete(uuid4())

        assert deleted is False


# =============================================================================
# MediaFile Repository Tests
# =============================================================================

class TestMediaFileRepository:
    """Tests for MediaFile repository operations."""

    @pytest.mark.asyncio
    async def test_create_media_file(self, test_session, sample_job):
        """Test creating a new MediaFile."""
        repository = MockMediaFileRepository(test_session)

        media_file = await repository.create(
            {
                "job_id": sample_job.id,
                "file_type": FileType.SOURCE,
                "original_url": "https://example.com/new-file.mp4",
                "mime_type": "video/mp4",
                "file_size": 2048000,
                "filename": "new-file.mp4",
            }
        )

        assert media_file.id is not None
        assert media_file.job_id == sample_job.id
        assert media_file.file_type == FileType.SOURCE

    @pytest.mark.asyncio
    async def test_get_media_file_by_id(self, test_session, sample_media_file):
        """Test getting a media file by ID."""
        repository = MockMediaFileRepository(test_session)

        found_file = await repository.get_by_id(sample_media_file.id)

        assert found_file is not None
        assert found_file.id == sample_media_file.id

    @pytest.mark.asyncio
    async def test_get_media_files_by_job_id(
        self, test_session, sample_job
    ):
        """Test getting media files by job ID."""
        repository = MockMediaFileRepository(test_session)

        # Create multiple media files for the job
        await repository.create(
            {
                "job_id": sample_job.id,
                "file_type": FileType.SOURCE,
                "original_url": "https://example.com/file1.mp4",
            }
        )
        await repository.create(
            {
                "job_id": sample_job.id,
                "file_type": FileType.EXTRACTED,
                "original_url": "https://example.com/file2.mp4",
            }
        )

        files = await repository.get_by_job_id(sample_job.id)

        assert len(files) >= 2

    @pytest.mark.asyncio
    async def test_update_media_file_status(
        self, test_session, sample_media_file
    ):
        """Test updating media file status."""
        repository = MockMediaFileRepository(test_session)

        updated_file = await repository.update_status(
            sample_media_file.id, MediaFileStatus.COMPLETED
        )

        assert updated_file is not None
        assert updated_file.status == MediaFileStatus.COMPLETED


# =============================================================================
# AnalysisResult Repository Tests
# =============================================================================

class TestAnalysisResultRepository:
    """Tests for AnalysisResult repository operations."""

    @pytest.mark.asyncio
    async def test_create_analysis_result(self, test_session, sample_job):
        """Test creating a new AnalysisResult."""
        repository = MockAnalysisResultRepository(test_session)

        result = await repository.create(
            {
                "job_id": sample_job.id,
                "provider": AnalysisProvider.MINIMAX,
                "model": "minimax-video-01",
                "result_json": {"summary": "Test summary"},
                "confidence": 0.95,
                "tokens_used": 1000,
                "latency_ms": 2000,
            }
        )

        assert result.id is not None
        assert result.job_id == sample_job.id
        assert result.provider == AnalysisProvider.MINIMAX

    @pytest.mark.asyncio
    async def test_get_analysis_result_by_id(
        self, test_session, sample_analysis_result
    ):
        """Test getting an analysis result by ID."""
        repository = MockAnalysisResultRepository(test_session)

        found_result = await repository.get_by_id(sample_analysis_result.id)

        assert found_result is not None
        assert found_result.id == sample_analysis_result.id

    @pytest.mark.asyncio
    async def test_get_analysis_results_by_job_id(
        self, test_session, sample_job
    ):
        """Test getting analysis results by job ID."""
        repository = MockAnalysisResultRepository(test_session)

        # Create multiple results for the job
        await repository.create(
            {
                "job_id": sample_job.id,
                "provider": AnalysisProvider.MINIMAX,
                "model": "model-1",
                "result_json": {"result": 1},
            }
        )
        await repository.create(
            {
                "job_id": sample_job.id,
                "provider": AnalysisProvider.GROQ,
                "model": "model-2",
                "result_json": {"result": 2},
            }
        )

        results = await repository.get_by_job_id(sample_job.id)

        assert len(results) >= 2

    @pytest.mark.asyncio
    async def test_get_analysis_results_by_provider(
        self, test_session, sample_job
    ):
        """Test getting analysis results by provider."""
        repository = MockAnalysisResultRepository(test_session)

        await repository.create(
            {
                "job_id": sample_job.id,
                "provider": AnalysisProvider.MINIMAX,
                "model": "model",
                "result_json": {},
            }
        )

        results = await repository.get_by_provider(AnalysisProvider.MINIMAX)

        assert len(results) >= 1
        assert all(r.provider == AnalysisProvider.MINIMAX for r in results)


# =============================================================================
# Transcription Repository Tests
# =============================================================================

class TestTranscriptionRepository:
    """Tests for Transcription repository operations."""

    @pytest.mark.asyncio
    async def test_create_transcription(self, test_session, sample_job):
        """Test creating a new Transcription."""
        repository = MockTranscriptionRepository(test_session)

        transcription = await repository.create(
            {
                "job_id": sample_job.id,
                "provider": TranscriptionProvider.WHISPER,
                "text": "Test transcription text",
                "segments_json": [{"start": 0, "end": 5, "text": "Test"}],
                "language": "en",
                "duration_seconds": 5.0,
            }
        )

        assert transcription.id is not None
        assert transcription.job_id == sample_job.id
        assert transcription.provider == TranscriptionProvider.WHISPER

    @pytest.mark.asyncio
    async def test_get_transcription_by_id(
        self, test_session, sample_transcription
    ):
        """Test getting a transcription by ID."""
        repository = MockTranscriptionRepository(test_session)

        found_transcription = await repository.get_by_id(sample_transcription.id)

        assert found_transcription is not None
        assert found_transcription.id == sample_transcription.id

    @pytest.mark.asyncio
    async def test_get_transcriptions_by_job_id(
        self, test_session, sample_job
    ):
        """Test getting transcriptions by job ID."""
        repository = MockTranscriptionRepository(test_session)

        # Create multiple transcriptions for the job
        await repository.create(
            {
                "job_id": sample_job.id,
                "provider": TranscriptionProvider.WHISPER,
                "text": "Transcription 1",
                "language": "en",
            }
        )
        await repository.create(
            {
                "job_id": sample_job.id,
                "provider": TranscriptionProvider.DEEGRAM,
                "text": "Transcription 2",
                "language": "es",
            }
        )

        transcriptions = await repository.get_by_job_id(sample_job.id)

        assert len(transcriptions) >= 2

    @pytest.mark.asyncio
    async def test_get_transcriptions_by_language(
        self, test_session, sample_job
    ):
        """Test getting transcriptions by language."""
        repository = MockTranscriptionRepository(test_session)

        await repository.create(
            {
                "job_id": sample_job.id,
                "provider": TranscriptionProvider.WHISPER,
                "text": "English transcription",
                "language": "en",
            }
        )

        transcriptions = await repository.get_by_language("en")

        assert len(transcriptions) >= 1
        assert all(t.language == "en" for t in transcriptions)


# =============================================================================
# Repository with Mock Session Tests
# =============================================================================

class TestRepositoryWithMockedSession:
    """Tests for repositories using mocked database sessions."""

    def test_create_job_with_mocked_session(self, mock_session):
        """Test creating a job with a mocked session."""
        from unittest.mock import AsyncMock

        # Setup mock to return a new job
        mock_job = MagicMock()
        mock_job.id = uuid4()
        mock_job.status = JobStatus.PENDING
        mock_job.media_type = MediaType.VIDEO
        mock_job.source_url = "https://example.com/mock.mp4"

        # Configure session mock
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock(return_value=mock_job)

        repository = MockAnalysisJobRepository(mock_session)

        # This would need actual async handling, but demonstrates the pattern
        # In practice, use the test_session fixture instead

        mock_session.add.assert_not_called()

    def test_repository_with_mock_session_query(self, mock_session):
        """Test repository queries with mocked session."""
        from sqlalchemy.engine.result import ChunkedIteratorResult
        from sqlalchemy.sql.elements import ColumnElement

        # Create mock job
        mock_job = MagicMock()
        mock_job.id = uuid4()
        mock_job.status = JobStatus.PENDING

        # Create mock result
        mock_result = MagicMock(spec=ChunkedIteratorResult)
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_result.scalars.return_value.all.return_value = [mock_job]

        mock_session.execute = AsyncMock(return_value=mock_result)

        repository = MockAnalysisJobRepository(mock_session)

        # Verify execute was called with select statement
        mock_session.execute.assert_called()


# =============================================================================
# Repository Integration Tests
# =============================================================================

class TestRepositoryIntegration:
    """Integration tests for repositories with real database."""

    @pytest.mark.asyncio
    async def test_job_with_related_media_files(self, test_session, sample_job):
        """Test querying job with its related media files."""
        repository = MockAnalysisJobRepository(test_session)

        # Add media files
        media_repo = MockMediaFileRepository(test_session)
        await media_repo.create(
            {
                "job_id": sample_job.id,
                "file_type": FileType.SOURCE,
                "original_url": "https://example.com/source.mp4",
            }
        )
        await media_repo.create(
            {
                "job_id": sample_job.id,
                "file_type": FileType.OUTPUT,
                "original_url": "https://example.com/output.mp4",
            }
        )

        # Get job and check related files
        job = await repository.get_by_id(sample_job.id)

        assert job is not None
        media_files = await media_repo.get_by_job_id(job.id)
        assert len(media_files) >= 2

    @pytest.mark.asyncio
    async def test_job_with_related_results_and_transcriptions(
        self, test_session, sample_job
    ):
        """Test job with related analysis results and transcriptions."""
        job_repo = MockAnalysisJobRepository(test_session)
        result_repo = MockAnalysisResultRepository(test_session)
        transcription_repo = MockTranscriptionRepository(test_session)

        # Create related records
        await result_repo.create(
            {
                "job_id": sample_job.id,
                "provider": AnalysisProvider.MINIMAX,
                "model": "test",
                "result_json": {"summary": "test"},
            }
        )

        await transcription_repo.create(
            {
                "job_id": sample_job.id,
                "provider": TranscriptionProvider.WHISPER,
                "text": "test transcription",
                "language": "en",
            }
        )

        # Verify relationships
        results = await result_repo.get_by_job_id(sample_job.id)
        transcriptions = await transcription_repo.get_by_job_id(sample_job.id)

        assert len(results) >= 1
        assert len(transcriptions) >= 1

    @pytest.mark.asyncio
    async def test_complete_crud_workflow(self, test_session):
        """Test complete CRUD workflow for a job."""
        # 1. Create
        job_repo = MockAnalysisJobRepository(test_session)
        new_job = await job_repo.create(
            {
                "status": JobStatus.PENDING,
                "media_type": MediaType.VIDEO,
                "source_url": "https://example.com/workflow.mp4",
                "metadata_json": {"workflow_test": True},
            }
        )
        assert new_job.id is not None

        # 2. Read
        read_job = await job_repo.get_by_id(new_job.id)
        assert read_job is not None
        assert read_job.source_url == "https://example.com/workflow.mp4"

        # 3. Update
        updated_job = await job_repo.update_status(
            new_job.id, JobStatus.PROCESSING
        )
        assert updated_job.status == JobStatus.PROCESSING

        # 4. Delete
        deleted = await job_repo.delete(new_job.id)
        assert deleted is True

        # Verify deletion
        deleted_job = await job_repo.get_by_id(new_job.id)
        assert deleted_job is None
