"""
Transcription Repository Module

Repository for Transcription model with transcription-specific query methods.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.transcription import Transcription, TranscriptionProvider
from api.repositories.base import BaseRepository


class TranscriptionRepository(BaseRepository[Transcription]):
    """
    Repository for Transcription model operations.

    Provides transcription-specific query methods beyond the base CRUD operations.

    Example:
        ```python
        transcription_repo = TranscriptionRepository(Transcription, session)
        transcriptions_by_job = await transcription_repo.get_by_job_id(job_id)
        transcriptions_by_provider = await transcription_repo.get_by_provider(TranscriptionProvider.WHISPER)
        ```
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize TranscriptionRepository with Transcription model.

        Args:
            session: AsyncSession instance for database operations
        """
        super().__init__(Transcription, session)

    async def get_by_id(self, id_: UUID) -> Optional[Transcription]:
        """Get a transcription by its UUID."""
        return await super().get_by_id(id_)

    async def get_by_job_id(
        self,
        job_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100
    ) -> List[Transcription]:
        """
        Retrieve all transcriptions for a specific job.

        Args:
            job_id: UUID of the parent job
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Transcription instances
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
        provider: TranscriptionProvider,
        *,
        offset: int = 0,
        limit: int = 100
    ) -> List[Transcription]:
        """
        Retrieve all transcriptions from a specific provider.

        Args:
            provider: TranscriptionProvider enum value
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Transcription instances
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

    async def get_by_language(
        self,
        language: str,
        *,
        offset: int = 0,
        limit: int = 100
    ) -> List[Transcription]:
        """
        Retrieve all transcriptions in a specific language.

        Args:
            language: Language code (e.g., 'en', 'es', 'fr')
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Transcription instances
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.language == language,
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_high_confidence_transcriptions(
        self,
        min_confidence: float = 0.9,
        *,
        limit: int = 100
    ) -> List[Transcription]:
        """
        Get transcriptions with confidence above threshold.

        Args:
            min_confidence: Minimum confidence score (default: 0.9)
            limit: Maximum number of transcriptions to return

        Returns:
            List of high-confidence Transcription instances
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

    async def get_by_job_and_provider(
        self,
        job_id: UUID,
        provider: TranscriptionProvider
    ) -> Optional[Transcription]:
        """
        Get a specific transcription by job and provider.

        Args:
            job_id: UUID of the parent job
            provider: TranscriptionProvider enum value

        Returns:
            Transcription instance or None
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
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_transcription_count_by_job(self, job_id: UUID) -> int:
        """
        Count transcriptions for a specific job.

        Args:
            job_id: UUID of the parent job

        Returns:
            Number of transcriptions
        """
        return await self.count(job_id=job_id)

    async def get_transcription_count_by_provider(self, provider: TranscriptionProvider) -> int:
        """
        Count transcriptions from a specific provider.

        Args:
            provider: TranscriptionProvider enum value

        Returns:
            Number of transcriptions
        """
        return await self.count(provider=provider)

    async def get_total_words_by_job(self, job_id: UUID) -> int:
        """
        Get total word count for a job's transcriptions.

        Args:
            job_id: UUID of the parent job

        Returns:
            Total word count
        """
        stmt = select(func.coalesce(func.sum(self.model.word_count), 0)).where(
            and_(
                self.model.job_id == job_id,
                self.model.is_deleted == False  # type: ignore[attr-defined]
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def get_total_duration_by_job(self, job_id: UUID) -> float:
        """
        Get total duration for a job's transcriptions.

        Args:
            job_id: UUID of the parent job

        Returns:
            Total duration in seconds
        """
        stmt = select(func.coalesce(func.sum(self.model.duration_seconds), 0)).where(
            and_(
                self.model.job_id == job_id,
                self.model.is_deleted == False  # type: ignore[attr-defined]
            )
        )
        result = await self._session.execute(stmt)
        return float(result.scalar() or 0)

    async def get_total_tokens_by_job(self, job_id: UUID) -> int:
        """
        Get total tokens used for a job's transcriptions.

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

    async def get_average_confidence_by_job(self, job_id: UUID) -> float:
        """
        Get average confidence score for a job's transcriptions.

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

    async def get_language_distribution_by_job(self, job_id: UUID) -> dict:
        """
        Get language distribution for a job's transcriptions.

        Args:
            job_id: UUID of the parent job

        Returns:
            Dictionary mapping language codes to counts
        """
        stmt = select(
            self.model.language,
            func.count(self.model.id)
        ).where(
            and_(
                self.model.job_id == job_id,
                self.model.language.isnot(None),
                self.model.is_deleted == False  # type: ignore[attr-defined]
            )
        ).group_by(self.model.language)

        result = await self._session.execute(stmt)
        rows = result.fetchall()

        distribution = {}
        for row in rows:
            if row.language:
                distribution[row.language] = row.count

        return distribution

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
                    COUNT(*) as transcription_count,
                    COUNT(DISTINCT job_id) as job_count,
                    AVG(COALESCE(confidence, 0)) as avg_confidence,
                    AVG(COALESCE(duration_seconds, 0)) as avg_duration,
                    AVG(COALESCE(word_count, 0)) as avg_words,
                    SUM(COALESCE(tokens_used, 0)) as total_tokens
                FROM {self.table_name}
                WHERE is_deleted = false
                GROUP BY provider
                ORDER BY transcription_count DESC
            """)
        )
        rows = result.fetchall()

        stats = {}
        for row in rows:
            stats[row.provider] = {
                "transcription_count": row.transcription_count,
                "job_count": row.job_count,
                "avg_confidence": float(row.avg_confidence) if row.avg_confidence else 0,
                "avg_duration_seconds": float(row.avg_duration) if row.avg_duration else 0,
                "avg_word_count": float(row.avg_words) if row.avg_words else 0,
                "total_tokens": row.total_tokens
            }

        return stats

    async def get_latest_transcriptions(
        self,
        *,
        limit: int = 50,
        offset: int = 0
    ) -> List[Transcription]:
        """
        Get the most recent transcriptions.

        Args:
            limit: Maximum number of transcriptions to return
            offset: Number of records to skip

        Returns:
            List of recent Transcription instances
        """
        return await self.get_all(
            limit=limit,
            offset=offset,
            order_by="created_at",
            descending=True
        )

    async def search_transcriptions(
        self,
        query: str,
        *,
        limit: int = 50,
        offset: int = 0
    ) -> List[Transcription]:
        """
        Search transcriptions by text content.

        Args:
            query: Search query string
            limit: Maximum number of results
            offset: Number of records to skip

        Returns:
            List of matching Transcription instances
        """
        search_pattern = f"%{query}%"
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.text.ilike(search_pattern),
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(desc(self.model.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_transcriptions_with_segments(
        self,
        job_id: UUID,
        *,
        limit: int = 100
    ) -> List[Transcription]:
        """
        Get transcriptions that have timestamped segments.

        Args:
            job_id: UUID of the parent job
            limit: Maximum number of transcriptions to return

        Returns:
            List of Transcription instances with segments
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.job_id == job_id,
                    self.model.segments_json.isnot(None),
                    self.model.segments_json != [],
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(desc(self.model.created_at))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_text(
        self,
        id_: UUID,
        text: str
    ) -> Optional[Transcription]:
        """
        Update transcription text content.

        Args:
            id_: Transcription UUID
            text: Updated text content

        Returns:
            Updated Transcription instance or None
        """
        return await self.update(id_, text=text)
