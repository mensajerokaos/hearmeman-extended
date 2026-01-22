"""
Pytest configuration and shared fixtures for the API test suite.

This module provides pytest fixtures for database testing, including:
- Async database session management
- Mock database engine
- Test model instances
- Common test utilities
"""

import asyncio
import sys
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add api directory to path for imports
sys.path.insert(0, "/home/oz/projects/2025/oz/12/runpod/api")

from api.models.base import Base
from api.models.job import AnalysisJob, JobStatus, MediaType
from api.models.media import FileType, MediaFile, MediaFileStatus
from api.models.result import AnalysisResult, AnalysisProvider
from api.models.transcription import Transcription, TranscriptionProvider
from api.schemas.job import JobCreate, JobResponse
from api.schemas.media import MediaFileCreate, MediaFileResponse
from api.schemas.result import AnalysisResultCreate, AnalysisResultResponse

# Note: We're not importing from api.models.database due to a naming conflict
# with the database/ package directory. We define our own test versions below.

# =============================================================================
# Test Database Functions (replacements for api.models.database functions)
# =============================================================================

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


# Test connection URL (SQLite for testing)
ASYNC_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def create_async_engine_configured(database_url: str | None = None, **kwargs):
    """Create test async engine (SQLite)."""
    url = database_url or ASYNC_DATABASE_URL
    return create_async_engine(
        url,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        **kwargs,
    )


def init_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    """Initialize async session factory."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@asynccontextmanager
async def get_async_session(
    sessionmaker: async_sessionmaker,
) -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for test database sessions."""
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def verify_database_connection(engine) -> bool:
    """Verify test database connectivity."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def close_engine(engine) -> None:
    """Dispose test engine."""
    await engine.dispose()


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_engine():
    """
    Create a test database engine with SQLite in-memory for fast testing.
    Uses StaticPool for single-connection sharing across async sessions.
    """
    # Create SQLite engine for testing (faster than PostgreSQL)
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session with automatic cleanup.
    Uses nested transactions for test isolation with automatic rollback.
    """
    # Create session factory
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        # Begin nested transaction for test isolation
        await session.begin()

        try:
            yield session
            # Rollback after test to ensure isolation
            await session.rollback()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def db_session_factory(test_engine) -> async_sessionmaker[AsyncSession]:
    """
    Create a session factory for use in repository tests.
    """
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


# =============================================================================
# Model Instance Fixtures
# =============================================================================

@pytest.fixture
def sample_job_data() -> dict:
    """Sample data for creating an AnalysisJob."""
    return {
        "status": JobStatus.PENDING,
        "media_type": MediaType.VIDEO,
        "source_url": "https://example.com/video.mp4",
        "metadata_json": {"priority": "high", "category": "interview"},
    }


@pytest.fixture
def sample_job_data_with_id() -> dict:
    """Sample data for creating an AnalysisJob with ID."""
    return {
        "id": uuid4(),
        "status": JobStatus.PENDING,
        "media_type": MediaType.VIDEO,
        "source_url": "https://example.com/video.mp4",
        "metadata_json": {"priority": "high", "category": "interview"},
    }


@pytest_asyncio.fixture
async def sample_job(test_session: AsyncSession) -> AnalysisJob:
    """Create a sample AnalysisJob in the database."""
    job = AnalysisJob(
        status=JobStatus.PENDING,
        media_type=MediaType.VIDEO,
        source_url="https://example.com/video.mp4",
        metadata_json={"priority": "high", "category": "interview"},
    )
    test_session.add(job)
    await test_session.commit()
    await test_session.refresh(job)
    return job


@pytest.fixture
def sample_media_file_data() -> dict:
    """Sample data for creating a MediaFile."""
    return {
        "job_id": None,  # Will be set when creating related to a job
        "file_type": FileType.SOURCE,
        "original_url": "https://example.com/video.mp4",
        "mime_type": "video/mp4",
        "file_size": 1024000,
        "filename": "video.mp4",
        "status": MediaFileStatus.PENDING,
    }


@pytest_asyncio.fixture
async def sample_media_file(
    test_session: AsyncSession, sample_job: AnalysisJob
) -> MediaFile:
    """Create a sample MediaFile in the database."""
    media_file = MediaFile(
        job_id=sample_job.id,
        file_type=FileType.SOURCE,
        original_url="https://example.com/video.mp4",
        mime_type="video/mp4",
        file_size=1024000,
        filename="video.mp4",
        status=MediaFileStatus.PENDING,
    )
    test_session.add(media_file)
    await test_session.commit()
    await test_session.refresh(media_file)
    return media_file


@pytest.fixture
def sample_analysis_result_data() -> dict:
    """Sample data for creating an AnalysisResult."""
    return {
        "job_id": None,
        "provider": AnalysisProvider.MINIMAX,
        "model": "minimax-video-01",
        "result_json": {"summary": "Test summary", "topics": ["AI", "Technology"]},
        "confidence": 0.95,
        "tokens_used": 1500,
        "latency_ms": 2500,
    }


@pytest_asyncio.fixture
async def sample_analysis_result(
    test_session: AsyncSession, sample_job: AnalysisJob
) -> AnalysisResult:
    """Create a sample AnalysisResult in the database."""
    result = AnalysisResult(
        job_id=sample_job.id,
        provider=AnalysisProvider.MINIMAX,
        model="minimax-video-01",
        result_json={"summary": "Test summary", "topics": ["AI", "Technology"]},
        confidence=0.95,
        tokens_used=1500,
        latency_ms=2500,
    )
    test_session.add(result)
    await test_session.commit()
    await test_session.refresh(result)
    return result


@pytest.fixture
def sample_transcription_data() -> dict:
    """Sample data for creating a Transcription."""
    return {
        "job_id": None,
        "provider": TranscriptionProvider.WHISPER,
        "text": "This is a sample transcription text.",
        "segments_json": [
            {"start": 0.0, "end": 5.0, "text": "This is"},
            {"start": 5.0, "end": 10.0, "text": " a sample"},
        ],
        "language": "en",
        "duration_seconds": 10.5,
    }


@pytest_asyncio.fixture
async def sample_transcription(
    test_session: AsyncSession, sample_job: AnalysisJob
) -> Transcription:
    """Create a sample Transcription in the database."""
    transcription = Transcription(
        job_id=sample_job.id,
        provider=TranscriptionProvider.WHISPER,
        text="This is a sample transcription text.",
        segments_json=[
            {"start": 0.0, "end": 5.0, "text": "This is"},
            {"start": 5.0, "end": 10.0, "text": " a sample"},
        ],
        language="en",
        duration_seconds=10.5,
    )
    test_session.add(transcription)
    await test_session.commit()
    await test_session.refresh(transcription)
    return transcription


# =============================================================================
# Schema Fixtures
# =============================================================================

@pytest.fixture
def valid_job_create_schema() -> dict:
    """Valid data for JobCreate schema."""
    return {
        "status": "pending",
        "media_type": "video",
        "source_url": "https://example.com/video.mp4",
        "metadata_json": {"priority": "high", "tags": ["interview", "ai"]},
    }


@pytest.fixture
def valid_media_file_create_schema() -> dict:
    """Valid data for MediaFileCreate schema."""
    return {
        "file_type": "source",
        "original_url": "https://example.com/video.mp4",
        "mime_type": "video/mp4",
        "file_size": 1024000,
        "filename": "video.mp4",
    }


@pytest.fixture
def valid_analysis_result_create_schema() -> dict:
    """Valid data for AnalysisResultCreate schema."""
    return {
        "provider": "minimax",
        "model": "minimax-video-01",
        "result_json": {"summary": "Test analysis", "topics": ["AI"]},
        "confidence": 0.95,
        "tokens_used": 1500,
        "latency_ms": 2500,
    }


@pytest.fixture
def valid_transcription_create_data() -> dict:
    """Valid data for creating a Transcription (dict format, schema not implemented yet)."""
    return {
        "provider": "whisper",
        "text": "Sample transcription text",
        "segments_json": [{"start": 0, "end": 5, "text": "Sample"}],
        "language": "en",
        "duration_seconds": 5.0,
    }


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_session(mocker):
    """Mock database session for repository unit tests."""
    mock = mocker.AsyncMock(spec=AsyncSession)
    mock.execute = mocker.AsyncMock()
    mock.commit = mocker.AsyncMock()
    mock.rollback = mocker.AsyncMock()
    mock.refresh = mocker.AsyncMock()
    mock.close = mocker.AsyncMock()
    mock.add = mocker.Mock()
    mock.delete = mocker.Mock()
    return mock


@pytest.fixture
def mock_engine(mocker):
    """Mock database engine."""
    mock = mocker.MagicMock()
    mock.dispose = mocker.AsyncMock()
    return mock


# =============================================================================
# Utility Fixtures
# =============================================================================

@pytest.fixture
def anyio_backend():
    """Set the async backend for anyio."""
    return "asyncio"


@pytest.fixture
def uuid_generator(mocker):
    """Mock UUID generation for consistent test data."""
    mock_uuid = mocker.patch("uuid.uuid4")
    mock_uuid.return_value = uuid4()
    return mock_uuid
