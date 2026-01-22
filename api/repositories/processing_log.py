"""
ProcessingLog Repository Module

Repository for managing ProcessingLog entries with audit trail functionality.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.processing_log import ProcessingLog, ProcessingStage, ProcessingLogStatus
from api.repositories.base import BaseRepository


class ProcessingLogRepository(BaseRepository[ProcessingLog]):
    """
    Repository for ProcessingLog operations.

    Extends BaseRepository with processing-specific methods.
    Note: ProcessingLog does not use soft delete (is_deleted is not present).
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with ProcessingLog model."""
        super().__init__(ProcessingLog, session)

    async def get_by_id(self, id_: UUID) -> Optional[ProcessingLog]:
        """
        Override: ProcessingLog has no is_deleted field.

        Args:
            id_: Primary key value (UUID)

        Returns:
            ProcessingLog instance if found, None otherwise
        """
        stmt = select(self._model).where(self._model.id == id_)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_job_id(
        self,
        job_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0
    ) -> list[ProcessingLog]:
        """
        Get all processing logs for a job.

        Args:
            job_id: ID of the analysis job
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of ProcessingLog instances ordered by created_at
        """
        stmt = (
            select(self._model)
            .where(self._model.job_id == job_id)
            .order_by(self._model.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_stage(
        self,
        job_id: UUID,
        stage: ProcessingStage
    ) -> list[ProcessingLog]:
        """
        Get all logs for a specific processing stage.

        Args:
            job_id: ID of the analysis job
            stage: Processing stage to filter by

        Returns:
            List of ProcessingLog instances for the stage
        """
        stmt = (
            select(self._model)
            .where(
                self._model.job_id == job_id,
                self._model.stage == stage
            )
            .order_by(self._model.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_by_stage(
        self,
        job_id: UUID,
        stage: ProcessingStage
    ) -> Optional[ProcessingLog]:
        """
        Get the most recent log entry for a stage.

        Args:
            job_id: ID of the analysis job
            stage: Processing stage to filter by

        Returns:
            Most recent ProcessingLog for the stage or None
        """
        stmt = (
            select(self._model)
            .where(
                self._model.job_id == job_id,
                self._model.stage == stage
            )
            .order_by(self._model.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_failures(
        self,
        job_id: UUID
    ) -> list[ProcessingLog]:
        """
        Get all failed processing stages for a job.

        Args:
            job_id: ID of the analysis job

        Returns:
            List of failed ProcessingLog instances
        """
        stmt = (
            select(self._model)
            .where(
                self._model.job_id == job_id,
                self._model.status == ProcessingLogStatus.FAILED
            )
            .order_by(self._model.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def log_start(
        self,
        job_id: UUID,
        stage: ProcessingStage,
        message: Optional[str] = None,
        details_json: Optional[dict] = None
    ) -> ProcessingLog:
        """
        Log the start of a processing stage.

        Args:
            job_id: ID of the analysis job
            stage: Processing stage that is starting
            message: Optional log message
            details_json: Optional additional details

        Returns:
            Created ProcessingLog instance
        """
        return await self.create(
            job_id=job_id,
            stage=stage,
            status=ProcessingLogStatus.STARTED,
            message=message,
            details_json=details_json
        )

    async def log_complete(
        self,
        job_id: UUID,
        stage: ProcessingStage,
        duration_ms: Optional[int] = None,
        message: Optional[str] = None,
        details_json: Optional[dict] = None
    ) -> ProcessingLog:
        """
        Log the successful completion of a processing stage.

        Args:
            job_id: ID of the analysis job
            stage: Processing stage that completed
            duration_ms: Duration of the stage in milliseconds
            message: Optional log message
            details_json: Optional additional details

        Returns:
            Created ProcessingLog instance
        """
        return await self.create(
            job_id=job_id,
            stage=stage,
            status=ProcessingLogStatus.COMPLETED,
            duration_ms=duration_ms,
            message=message,
            details_json=details_json
        )

    async def log_failure(
        self,
        job_id: UUID,
        stage: ProcessingStage,
        message: str,
        duration_ms: Optional[int] = None,
        details_json: Optional[dict] = None
    ) -> ProcessingLog:
        """
        Log a failure in a processing stage.

        Args:
            job_id: ID of the analysis job
            stage: Processing stage that failed
            message: Error message
            duration_ms: Duration before failure in milliseconds
            details_json: Optional error details (traceback, etc.)

        Returns:
            Created ProcessingLog instance
        """
        return await self.create(
            job_id=job_id,
            stage=stage,
            status=ProcessingLogStatus.FAILED,
            message=message,
            duration_ms=duration_ms,
            details_json=details_json
        )

    async def log_warning(
        self,
        job_id: UUID,
        stage: ProcessingStage,
        message: str,
        duration_ms: Optional[int] = None,
        details_json: Optional[dict] = None
    ) -> ProcessingLog:
        """
        Log a warning in a processing stage.

        Args:
            job_id: ID of the analysis job
            stage: Processing stage with warning
            message: Warning message
            duration_ms: Duration of the stage in milliseconds
            details_json: Optional warning details

        Returns:
            Created ProcessingLog instance
        """
        return await self.create(
            job_id=job_id,
            stage=stage,
            status=ProcessingLogStatus.WARNING,
            message=message,
            duration_ms=duration_ms,
            details_json=details_json
        )

    async def count_by_job(self, job_id: UUID) -> int:
        """
        Count all log entries for a job.

        Args:
            job_id: ID of the analysis job

        Returns:
            Number of log entries
        """
        from sqlalchemy import func
        stmt = select(func.count(self._model.id)).where(
            self._model.job_id == job_id
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0
