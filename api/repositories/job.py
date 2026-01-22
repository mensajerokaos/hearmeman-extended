"""
Job Repository Module

Repository for AnalysisJob model with job-specific query methods.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.job import AnalysisJob, JobStatus, MediaType
from api.repositories.base import BaseRepository


class JobRepository(BaseRepository[AnalysisJob]):
    """
    Repository for AnalysisJob model operations.

    Provides job-specific query methods beyond the base CRUD operations.

    Example:
        ```python
        job_repo = JobRepository(AnalysisJob, session)
        pending_jobs = await job_repo.get_by_status(JobStatus.PENDING)
        recent_jobs = await job_repo.get_recent(limit=10)
        ```
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize JobRepository with AnalysisJob model.

        Args:
            session: AsyncSession instance for database operations
        """
        super().__init__(AnalysisJob, session)

    async def get_by_id(self, id_: UUID) -> Optional[AnalysisJob]:
        """
        Get a job by its UUID.

        Args:
            id_: Job UUID

        Returns:
            AnalysisJob instance or None
        """
        return await super().get_by_id(id_)

    async def get_by_status(
        self,
        status: JobStatus,
        *,
        offset: int = 0,
        limit: int = 100
    ) -> List[AnalysisJob]:
        """
        Retrieve all jobs with a specific status.

        Args:
            status: JobStatus enum value (PENDING, PROCESSING, COMPLETED, FAILED)
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of AnalysisJob instances
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.status == status,
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status_count(self, status: JobStatus) -> int:
        """
        Count jobs with a specific status.

        Args:
            status: JobStatus enum value

        Returns:
            Number of jobs with the status
        """
        stmt = select(self.model).where(
            and_(
                self.model.status == status,
                self.model.is_deleted == False  # type: ignore[attr-defined]
            )
        )
        result = await self._session.execute(stmt)
        return len(result.scalars().all())

    async def get_recent(
        self,
        *,
        limit: int = 10,
        include_completed: bool = True,
        since: Optional[datetime] = None
    ) -> List[AnalysisJob]:
        """
        Get recent jobs ordered by creation date.

        Args:
            limit: Maximum number of jobs to return
            include_completed: Include completed jobs in results
            since: Only get jobs created after this datetime

        Returns:
            List of recent AnalysisJob instances
        """
        conditions = [self.model.is_deleted == False]  # type: ignore[attr-defined]

        if not include_completed:
            conditions.append(self.model.status != JobStatus.COMPLETED)

        if since:
            conditions.append(self.model.created_at >= since)

        stmt = (
            select(self.model)
            .where(and_(*conditions))
            .order_by(desc(self.model.created_at))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_jobs(self, limit: int = 10) -> List[AnalysisJob]:
        """
        Get pending jobs ordered by creation date (oldest first).

        Useful for processing queues where oldest jobs should be processed first.

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of pending AnalysisJob instances
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.status == JobStatus.PENDING,
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(self.model.created_at.asc())  # Oldest first
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_processing_jobs(self, limit: int = 100) -> List[AnalysisJob]:
        """
        Get currently processing jobs.

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of processing AnalysisJob instances
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.status == JobStatus.PROCESSING,
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(desc(self.model.created_at))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_failed_jobs(
        self,
        *,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AnalysisJob]:
        """
        Get failed jobs, optionally filtered by date.

        Args:
            since: Only get jobs that failed after this datetime
            limit: Maximum number of jobs to return

        Returns:
            List of failed AnalysisJob instances
        """
        conditions = [
            self.model.status == JobStatus.FAILED,
            self.model.is_deleted == False  # type: ignore[attr-defined]
        ]

        if since:
            conditions.append(self.model.updated_at >= since)

        stmt = (
            select(self.model)
            .where(and_(*conditions))
            .order_by(desc(self.model.updated_at))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_media_type(
        self,
        media_type: MediaType,
        *,
        offset: int = 0,
        limit: int = 100
    ) -> List[AnalysisJob]:
        """
        Get jobs by media type.

        Args:
            media_type: MediaType enum value (VIDEO, AUDIO, IMAGE)
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of AnalysisJob instances
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.media_type == media_type,
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_completed_jobs(
        self,
        *,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AnalysisJob]:
        """
        Get completed jobs, optionally filtered by date.

        Args:
            since: Only get jobs completed after this datetime
            limit: Maximum number of jobs to return

        Returns:
            List of completed AnalysisJob instances
        """
        conditions = [
            self.model.status == JobStatus.COMPLETED,
            self.model.is_deleted == False  # type: ignore[attr-defined]
        ]

        if since:
            conditions.append(self.model.completed_at >= since)

        stmt = (
            select(self.model)
            .where(and_(*conditions))
            .order_by(desc(self.model.completed_at))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_stale_processing_jobs(
        self,
        older_than_minutes: int = 30
    ) -> List[AnalysisJob]:
        """
        Get processing jobs that have been stuck for too long.

        Useful for detecting and recovering from failed processing jobs.

        Args:
            older_than_minutes: Consider jobs processing longer than this as stale

        Returns:
            List of stale processing AnalysisJob instances
        """
        cutoff_time = datetime.utcnow() - datetime.timedelta(minutes=older_than_minutes)
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.status == JobStatus.PROCESSING,
                    self.model.updated_at < cutoff_time,
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(self.model.updated_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        id_: UUID,
        status: JobStatus,
        error_message: Optional[str] = None
    ) -> Optional[AnalysisJob]:
        """
        Update job status with optional error message.

        Args:
            id_: Job UUID
            status: New JobStatus
            error_message: Optional error message (for failed jobs)

        Returns:
            Updated AnalysisJob instance or None
        """
        update_data: dict = {"status": status, "updated_at": datetime.utcnow()}

        if status == JobStatus.COMPLETED:
            update_data["completed_at"] = datetime.utcnow()
        elif status == JobStatus.FAILED:
            update_data["error_message"] = error_message or "Unknown error"

        stmt = (
            select(self.model)
            .where(self.model.id == id_)
            .execution_options(populate_existing=True)
        )
        result = await self._session.execute(stmt)
        job = result.scalar_one_or_none()

        if job:
            for key, value in update_data.items():
                setattr(job, key, value)
            await self._session.flush()
            await self._session.refresh(job)

        return job

    async def mark_as_processing(self, id_: UUID) -> Optional[AnalysisJob]:
        """
        Mark a job as processing.

        Args:
            id_: Job UUID

        Returns:
            Updated AnalysisJob instance or None
        """
        return await self.update_status(id_, JobStatus.PROCESSING)

    async def mark_as_completed(self, id_: UUID) -> Optional[AnalysisJob]:
        """
        Mark a job as completed.

        Args:
            id_: Job UUID

        Returns:
            Updated AnalysisJob instance or None
        """
        return await self.update_status(id_, JobStatus.COMPLETED)

    async def mark_as_failed(
        self,
        id_: UUID,
        error_message: str
    ) -> Optional[AnalysisJob]:
        """
        Mark a job as failed with error message.

        Args:
            id_: Job UUID
            error_message: Error description

        Returns:
            Updated AnalysisJob instance or None
        """
        return await self.update_status(id_, JobStatus.FAILED, error_message)

    async def get_job_with_relations(
        self,
        id_: UUID,
        include_media: bool = True,
        include_results: bool = True,
        include_transcriptions: bool = True
    ) -> Optional[AnalysisJob]:
        """
        Get a job with its related entities.

        Args:
            id_: Job UUID
            include_media: Include related media files
            include_results: Include analysis results
            include_transcriptions: Include transcriptions

        Returns:
            AnalysisJob instance with relations loaded or None
        """
        stmt = select(self.model).where(
            and_(
                self.model.id == id_,
                self.model.is_deleted == False  # type: ignore[attr-defined]
            )
        )

        # Note: In a real implementation, you would use joinedload or selectinload
        # to eagerly load relationships. For now, we just fetch the job.
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_statistics(self) -> dict:
        """
        Get job statistics summary.

        Returns:
            Dictionary with counts by status
        """
        from sqlalchemy import text

        result = await self._session.execute(
            text(f"""
                SELECT
                    status,
                    COUNT(*) as count
                FROM {self.table_name}
                WHERE is_deleted = false
                GROUP BY status
            """)
        )
        rows = result.fetchall()

        stats = {
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "total": 0
        }

        for row in rows:
            stats[row.status] = row.count
            stats["total"] += row.count

        return stats

    async def search_jobs(
        self,
        query: str,
        *,
        limit: int = 50,
        offset: int = 0
    ) -> List[AnalysisJob]:
        """
        Search jobs by source URL or metadata.

        Args:
            query: Search query string
            limit: Maximum number of results
            offset: Number of records to skip

        Returns:
            List of matching AnalysisJob instances
        """
        search_pattern = f"%{query}%"
        stmt = (
            select(self.model)
            .where(
                and_(
                    or_(
                        self.model.source_url.ilike(search_pattern),
                        self.model.metadata_json["description"].as_string().ilike(search_pattern)
                    ),
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(desc(self.model.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
