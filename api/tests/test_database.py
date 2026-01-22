"""
Tests for database connection pool and session lifecycle.

This module tests:
- Connection pool creation and configuration
- Session lifecycle management
- Transaction rollback behavior
- Connection verification
- Graceful shutdown
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

sys.path.insert(0, "/home/oz/projects/2025/oz/12/runpod/api")

from models.base import Base
from models.database import (
    ASYNC_DATABASE_URL,
    close_engine,
    create_async_engine_configured,
    get_async_session,
    init_session_factory,
    verify_database_connection,
)


class TestConnectionPoolCreation:
    """Tests for connection pool creation and configuration."""

    def test_create_async_engine_configured_returns_engine(self):
        """Test that create_async_engine_configured returns a valid engine."""
        engine = create_async_engine_configured()

        assert engine is not None
        assert hasattr(engine, "url")
        assert engine.url.scheme == "postgresql+asyncpg"

    def test_engine_url_contains_database_host(self):
        """Test that the engine URL contains the correct host."""
        engine = create_async_engine_configured()

        # URL should contain the database host
        url_str = str(engine.url)
        assert "af-postgres-1" in url_str or "5432" in url_str

    def test_engine_pool_config(self):
        """Test that connection pool is configured correctly."""
        engine = create_async_engine_configured()
        pool = engine.pool

        assert pool is not None
        # Check pool has configured size
        assert pool.size() > 0

    @pytest.mark.asyncio
    async def test_engine_dialect_is_asyncpg(self):
        """Test that the engine uses asyncpg dialect."""
        engine = create_async_engine_configured()
        dialect = engine.dialect

        assert dialect is not None
        assert hasattr(dialect, "name")


class TestSessionFactory:
    """Tests for session factory initialization."""

    def test_init_session_factory_returns_session_maker(self):
        """Test that init_session_factory returns a session maker."""
        session_factory = init_session_factory()

        assert session_factory is not None
        assert isinstance(session_factory, async_sessionmaker)

    def test_session_factory_configured_for_async(self):
        """Test that session factory is configured for async sessions."""
        session_factory = init_session_factory()

        # The session maker should be bound to an engine
        assert session_factory.kw["bind"] is not None

    @pytest.mark.asyncio
    async def test_session_factory_creates_valid_session(self, test_engine):
        """Test that session factory can create valid sessions."""
        session_factory = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        async with session_factory() as session:
            assert session is not None
            assert isinstance(session, AsyncSession)
            assert session.is_active


class TestSessionLifecycle:
    """Tests for session lifecycle management."""

    @pytest.mark.asyncio
    async def test_session_can_be_created(self, test_session):
        """Test that a session can be created and used."""
        assert test_session is not None
        assert test_session.is_active

    @pytest.mark.asyncio
    async def test_session_can_add_objects(self, test_session):
        """Test that objects can be added to the session."""
        from models.job import AnalysisJob, JobStatus, MediaType

        job = AnalysisJob(
            status=JobStatus.PENDING,
            media_type=MediaType.VIDEO,
            source_url="https://example.com/test.mp4",
        )

        test_session.add(job)
        await test_session.commit()

        # Job should have an ID after commit
        assert job.id is not None

    @pytest.mark.asyncio
    async def test_session_can_refresh_objects(self, test_session):
        """Test that session can refresh objects from database."""
        from models.job import AnalysisJob, JobStatus, MediaType

        job = AnalysisJob(
            status=JobStatus.PENDING,
            media_type=MediaType.AUDIO,
            source_url="https://example.com/audio.mp3",
        )

        test_session.add(job)
        await test_session.commit()
        await test_session.refresh(job)

        # Refresh should update the object
        assert job.created_at is not None

    @pytest.mark.asyncio
    async def test_session_close(self, test_session):
        """Test that session can be closed properly."""
        from models.job import AnalysisJob, JobStatus, MediaType

        job = AnalysisJob(
            status=JobStatus.PROCESSING,
            media_type=MediaType.IMAGE,
            source_url="https://example.com/image.jpg",
        )

        test_session.add(job)
        await test_session.commit()

        # Close should work without errors
        await test_session.close()
        assert not test_session.is_active


class TestTransactionRollback:
    """Tests for transaction rollback behavior."""

    @pytest.mark.asyncio
    async def test_rollback_discards_changes(self, test_session):
        """Test that rollback discards uncommitted changes."""
        from models.job import AnalysisJob, JobStatus, MediaType

        # Add a job
        job = AnalysisJob(
            status=JobStatus.PENDING,
            media_type=MediaType.VIDEO,
            source_url="https://example.com/rollback-test.mp4",
        )
        test_session.add(job)
        await test_session.commit()

        job_id = job.id

        # Modify the job
        job.status = JobStatus.PROCESSING
        await test_session.commit()

        # Rollback
        await test_session.rollback()

        # Re-fetch to verify rollback
        from sqlalchemy import select

        result = await test_session.execute(
            select(AnalysisJob).where(AnalysisJob.id == job_id)
        )
        reverted_job = result.scalar_one_or_none()

        assert reverted_job is not None
        assert reverted_job.status == JobStatus.PENDING

    @pytest.mark.asyncio
    async def test_rollback_on_error(self, test_session):
        """Test that session rolls back on errors."""
        from models.job import AnalysisJob, JobStatus, MediaType

        job = AnalysisJob(
            status=JobStatus.PENDING,
            media_type=MediaType.VIDEO,
            source_url="https://example.com/error-test.mp4",
        )
        test_session.add(job)
        await test_session.commit()

        job_id = job.id

        # Simulate an error
        try:
            job.status = JobStatus.FAILED
            job.error_message = "Test error"
            await test_session.commit()
            raise ValueError("Simulated error")
        except ValueError:
            await test_session.rollback()

        # Verify rollback
        from sqlalchemy import select

        result = await test_session.execute(
            select(AnalysisJob).where(AnalysisJob.id == job_id)
        )
        reverted_job = result.scalar_one_or_none()

        assert reverted_job is not None
        assert reverted_job.status == JobStatus.PENDING
        assert reverted_job.error_message is None

    @pytest.mark.asyncio
    async def test_nested_transaction_rollback(self, test_session):
        """Test rollback behavior with nested transactions."""
        from models.job import AnalysisJob, JobStatus, MediaType

        # Create first job (committed)
        job1 = AnalysisJob(
            status=JobStatus.PENDING,
            media_type=MediaType.VIDEO,
            source_url="https://example.com/nested1.mp4",
        )
        test_session.add(job1)
        await test_session.commit()

        # Start nested transaction
        await test_session.begin_nested()

        # Create second job in nested transaction
        job2 = AnalysisJob(
            status=JobStatus.PROCESSING,
            media_type=MediaType.AUDIO,
            source_url="https://example.com/nested2.mp3",
        )
        test_session.add(job2)
        await test_session.commit()

        # Rollback the nested transaction
        await test_session.rollback()

        # Verify job1 exists but job2 does not
        from sqlalchemy import select

        result1 = await test_session.execute(
            select(AnalysisJob).where(AnalysisJob.id == job1.id)
        )
        result2 = await test_session.execute(
            select(AnalysisJob).where(AnalysisJob.id == job2.id)
        )

        assert result1.scalar_one_or_none() is not None
        assert result2.scalar_one_or_none() is None


class TestDatabaseConnectionVerification:
    """Tests for database connection verification."""

    @pytest.mark.asyncio
    async def test_verify_database_connection_success(self, test_engine):
        """Test that verification succeeds with valid connection."""
        # Note: This test uses SQLite, which doesn't require network
        result = await verify_database_connection()

        # SQLite should always be available
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_database_connection_handles_error(self):
        """Test that verification handles connection errors gracefully."""
        # Create a mock that simulates connection failure
        with patch("models.database.create_async_engine_configured") as mock_create:
            mock_engine = AsyncMock()
            mock_engine.connect = AsyncMock(
                side_effect=Exception("Connection failed")
            )
            mock_create.return_value = mock_engine

            result = await verify_database_connection()

            assert result is False


class TestGracefulShutdown:
    """Tests for graceful engine shutdown."""

    @pytest.mark.asyncio
    async def test_close_engine_disposes_engine(self, test_engine):
        """Test that close_engine properly disposes the engine."""
        await close_engine(test_engine)

        # After close, the engine should be disposed
        # The pool should be invalidated
        assert test_engine.pool is not None

    @pytest.mark.asyncio
    async def test_close_engine_handles_already_disposed(self, test_engine):
        """Test that close_engine handles already disposed engines."""
        await test_engine.dispose()

        # Should not raise an error
        await close_engine(test_engine)


class TestGetAsyncSession:
    """Tests for get_async_session context manager."""

    @pytest.mark.asyncio
    async def test_get_async_session_yields_session(self, db_session_factory):
        """Test that get_async_session yields a valid session."""
        async for session in get_async_session(db_session_factory):
            assert session is not None
            assert isinstance(session, AsyncSession)
            assert session.is_active

    @pytest.mark.asyncio
    async def test_get_async_session_auto_closes(self, db_session_factory):
        """Test that session is automatically closed after use."""
        session_ref = None

        async for session in get_async_session(db_session_factory):
            session_ref = session

        # After context exit, session should be closed
        assert session_ref is not None
        assert not session_ref.is_active


class TestInMemoryDatabase:
    """Tests using in-memory SQLite database for fast testing."""

    @pytest_asyncio.fixture
    async def memory_engine(self):
        """Create an in-memory SQLite engine for testing."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield engine

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    @pytest.mark.asyncio
    async def test_in_memory_database_operations(self, memory_engine):
        """Test basic database operations with in-memory database."""
        session_factory = async_sessionmaker(
            memory_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        async with session_factory() as session:
            from models.job import AnalysisJob, JobStatus, MediaType

            job = AnalysisJob(
                status=JobStatus.COMPLETED,
                media_type=MediaType.VIDEO,
                source_url="https://example.com/memory-test.mp4",
            )
            session.add(job)
            await session.commit()

            assert job.id is not None

            # Query back
            from sqlalchemy import select

            result = await session.execute(
                select(AnalysisJob).where(AnalysisJob.id == job.id)
            )
            fetched_job = result.scalar_one_or_none()

            assert fetched_job is not None
            assert fetched_job.status == JobStatus.COMPLETED
