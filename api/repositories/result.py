"""
Result Repository Module

Repository for AnalysisResult model with result-specific query methods.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.result import AnalysisResult, AnalysisProvider
from api.repositories.base import BaseRepository


class ResultRepository(BaseRepository[AnalysisResult]):
    """
    Repository for AnalysisResult model operations.

    Provides result-specific query methods beyond the base CRUD operations.

    Example:
        ```python
        result_repo = ResultRepository(AnalysisResult, session)
        results_by_job = await result_repo.get_by_job_id(job_id)
        results_by_provider = await result_repo.get_by_provider(AnalysisProvider.MINIMAX)
        ```
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize ResultRepository with AnalysisResult model.

        Args:
            session: AsyncSession instance for database operations
        """
        super().__init__(AnalysisResult, session)

    async def get_by_id(self, id_: UUID) -> Optional[AnalysisResult]:
        """Get a result by its UUID."""
        return await super().get_by_id(id_)

    async def get_by_job_id(
        self,
        job_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100
    ) -> List[AnalysisResult]:
        """
        Retrieve all results for a specific job.

        Args:
            job_id: UUID of the parent job
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of AnalysisResult instances
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.job_id == job_id,
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_provider(
        self,
        provider: AnalysisProvider,
        *,
        offset: int = 0,
        limit: int = 100
    ) -> List[AnalysisResult]:
        """
        Retrieve all results from a specific provider.

        Args:
            provider: AnalysisProvider enum value
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of AnalysisResult instances
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.provider == provider,
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_model(
        self,
        model: str,
        *,
        offset: int = 0,
        limit: int = 100
    ) -> List[AnalysisResult]:
        """
        Retrieve all results using a specific model.

        Args:
            model: Model identifier string
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of AnalysisResult instances
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.model == model,
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_high_confidence_results(
        self,
        min_confidence: float = 0.9,
        *,
        limit: int = 100
    ) -> List[AnalysisResult]:
        """
        Get results with confidence above threshold.

        Args:
            min_confidence: Minimum confidence score (default: 0.9)
            limit: Maximum number of results to return

        Returns:
            List of high-confidence AnalysisResult instances
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.confidence >= min_confidence,
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(desc(self.model.confidence))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_results_by_confidence_range(
        self,
        min_confidence: float,
        max_confidence: float,
        *,
        offset: int = 0,
        limit: int = 100
    ) -> List[AnalysisResult]:
        """
        Get results within a confidence range.

        Args:
            min_confidence: Minimum confidence score
            max_confidence: Maximum confidence score
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching AnalysisResult instances
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.confidence >= min_confidence,
                    self.model.confidence <= max_confidence,
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(desc(self.model.confidence))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_results_by_job_and_provider(
        self,
        job_id: UUID,
        provider: AnalysisProvider
    ) -> Optional[AnalysisResult]:
        """
        Get a specific result by job and provider.

        Args:
            job_id: UUID of the parent job
            provider: AnalysisProvider enum value

        Returns:
            AnalysisResult instance or None
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.job_id == job_id,
                    self.model.provider == provider,
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(desc(self.model.created_at))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_result_count_by_job(self, job_id: UUID) -> int:
        """
        Count results for a specific job.

        Args:
            job_id: UUID of the parent job

        Returns:
            Number of results
        """
        return await self.count(job_id=job_id)

    async def get_result_count_by_provider(self, provider: AnalysisProvider) -> int:
        """
        Count results from a specific provider.

        Args:
            provider: AnalysisProvider enum value

        Returns:
            Number of results
        """
        return await self.count(provider=provider)

    async def get_total_tokens_by_job(self, job_id: UUID) -> int:
        """
        Get total tokens used for a job's results.

        Args:
            job_id: UUID of the parent job

        Returns:
            Total tokens used
        """
        stmt = select(func.coalesce(func.sum(self.model.tokens_used), 0)).where(
            and_(
                self.model.job_id == job_id,
                self.model.is_deleted == False  # type: ignore[attr-defined]
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def get_total_latency_by_job(self, job_id: UUID) -> int:
        """
        Get total latency for a job's results.

        Args:
            job_id: UUID of the parent job

        Returns:
            Total latency in milliseconds
        """
        stmt = select(func.coalesce(func.sum(self.model.latency_ms), 0)).where(
            and_(
                self.model.job_id == job_id,
                self.model.is_deleted == False  # type: ignore[attr-defined]
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def get_average_confidence_by_job(self, job_id: UUID) -> float:
        """
        Get average confidence score for a job's results.

        Args:
            job_id: UUID of the parent job

        Returns:
            Average confidence score (0.0-1.0)
        """
        stmt = select(func.coalesce(func.avg(self.model.confidence), 0)).where(
            and_(
                self.model.job_id == job_id,
                self.model.confidence.isnot(None),
                self.model.is_deleted == False  # type: ignore[attr-defined]
            )
        )
        result = await self._session.execute(stmt)
        return float(result.scalar() or 0)

    async def get_statistics_by_provider(self) -> dict:
        """
        Get statistics grouped by provider.

        Returns:
            Dictionary with provider stats
        """
        from sqlalchemy import text

        result = await self._session.execute(
            text(f"""
                SELECT
                    provider,
                    COUNT(*) as result_count,
                    COUNT(DISTINCT job_id) as job_count,
                    AVG(COALESCE(confidence, 0)) as avg_confidence,
                    SUM(COALESCE(tokens_used, 0)) as total_tokens,
                    AVG(COALESCE(latency_ms, 0)) as avg_latency
                FROM {self.table_name}
                WHERE is_deleted = false
                GROUP BY provider
                ORDER BY result_count DESC
            """)
        )
        rows = result.fetchall()

        stats = {}
        for row in rows:
            stats[row.provider] = {
                "result_count": row.result_count,
                "job_count": row.job_count,
                "avg_confidence": float(row.avg_confidence) if row.avg_confidence else 0,
                "total_tokens": row.total_tokens,
                "avg_latency_ms": float(row.avg_latency) if row.avg_latency else 0
            }

        return stats

    async def get_latest_results(
        self,
        *,
        limit: int = 50,
        offset: int = 0
    ) -> List[AnalysisResult]:
        """
        Get the most recent results.

        Args:
            limit: Maximum number of results to return
            offset: Number of records to skip

        Returns:
            List of recent AnalysisResult instances
        """
        return await self.get_all(
            limit=limit,
            offset=offset,
            order_by="created_at",
            descending=True
        )

    async def search_results(
        self,
        query: str,
        *,
        limit: int = 50,
        offset: int = 0
    ) -> List[AnalysisResult]:
        """
        Search results by model name or result content.

        Args:
            query: Search query string
            limit: Maximum number of results
            offset: Number of records to skip

        Returns:
            List of matching AnalysisResult instances
        """
        search_pattern = f"%{query}%"
        stmt = (
            select(self.model)
            .where(
                and_(
                    or_(
                        self.model.model.ilike(search_pattern),
                        self.model.result_json.cast(str).ilike(search_pattern)
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
