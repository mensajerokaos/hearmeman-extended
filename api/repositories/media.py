"""
Media Repository Module

Repository for MediaFile model with file-specific query methods.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.media import MediaFile, FileType, MediaFileStatus
from api.repositories.base import BaseRepository


class MediaRepository(BaseRepository[MediaFile]):
    """
    Repository for MediaFile model operations.

    Provides file-specific query methods beyond the base CRUD operations.

    Example:
        ```python
        media_repo = MediaRepository(MediaFile, session)
        pending_files = await media_repo.get_by_status(MediaFileStatus.PENDING)
        files_by_job = await media_repo.get_by_job_id(job_id)
        ```
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize MediaRepository with MediaFile model.

        Args:
            session: AsyncSession instance for database operations
        """
        super().__init__(MediaFile, session)

    async def get_by_id(self, id_: UUID) -> Optional[MediaFile]:
        """Get a media file by its UUID."""
        return await super().get_by_id(id_)

    async def get_by_job_id(
        self,
        job_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100
    ) -> List[MediaFile]:
        """
        Retrieve all media files for a specific job.

        Args:
            job_id: UUID of the parent job
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of MediaFile instances
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

    async def get_by_status(
        self,
        status: MediaFileStatus,
        *,
        offset: int = 0,
        limit: int = 100
    ) -> List[MediaFile]:
        """
        Retrieve all media files with a specific status.

        Args:
            status: MediaFileStatus enum value
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of MediaFile instances
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

    async def get_by_file_type(
        self,
        file_type: FileType,
        *,
        offset: int = 0,
        limit: int = 100
    ) -> List[MediaFile]:
        """
        Retrieve all media files of a specific type.

        Args:
            file_type: FileType enum value (source, downloaded, extracted, cached, output)
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of MediaFile instances
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.file_type == file_type,
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_downloading_files(self, limit: int = 100) -> List[MediaFile]:
        """
        Get files currently being downloaded.

        Args:
            limit: Maximum number of files to return

        Returns:
            List of downloading MediaFile instances
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.status == MediaFileStatus.DOWNLOADING,
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(self.model.created_at.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_completed_files(
        self,
        job_id: Optional[UUID] = None,
        *,
        limit: int = 100
    ) -> List[MediaFile]:
        """
        Get completed media files.

        Args:
            job_id: Optional job UUID to filter by
            limit: Maximum number of files to return

        Returns:
            List of completed MediaFile instances
        """
        conditions = [
            self.model.status == MediaFileStatus.COMPLETED,
            self.model.is_deleted == False  # type: ignore[attr-defined]
        ]

        if job_id:
            conditions.append(self.model.job_id == job_id)

        stmt = (
            select(self.model)
            .where(and_(*conditions))
            .order_by(desc(self.model.created_at))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_failed_files(
        self,
        *,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[MediaFile]:
        """
        Get failed media files, optionally filtered by date.

        Args:
            since: Only get files that failed after this datetime
            limit: Maximum number of files to return

        Returns:
            List of failed MediaFile instances
        """
        conditions = [
            self.model.status == MediaFileStatus.FAILED,
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

    async def get_files_by_mime_type(
        self,
        mime_type: str,
        *,
        offset: int = 0,
        limit: int = 100
    ) -> List[MediaFile]:
        """
        Get media files by MIME type.

        Args:
            mime_type: MIME type string (e.g., 'video/mp4', 'audio/mp3')
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching MediaFile instances
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.mime_type == mime_type,
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_files_by_size_range(
        self,
        min_size: int,
        max_size: int,
        *,
        offset: int = 0,
        limit: int = 100
    ) -> List[MediaFile]:
        """
        Get media files within a size range (in bytes).

        Args:
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching MediaFile instances
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.file_size >= min_size,
                    self.model.file_size <= max_size,
                    self.model.is_deleted == False  # type: ignore[attr-defined]
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        id_: UUID,
        status: MediaFileStatus,
        cdn_url: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> Optional[MediaFile]:
        """
        Update media file status with optional additional fields.

        Args:
            id_: Media file UUID
            status: New MediaFileStatus
            cdn_url: Optional updated CDN URL
            file_size: Optional updated file size

        Returns:
            Updated MediaFile instance or None
        """
        update_data: dict = {"status": status, "updated_at": datetime.utcnow()}

        if cdn_url is not None:
            update_data["cdn_url"] = cdn_url
        if file_size is not None:
            update_data["file_size"] = file_size

        stmt = (
            select(self.model)
            .where(self.model.id == id_)
            .execution_options(populate_existing=True)
        )
        result = await self._session.execute(stmt)
        media_file = result.scalar_one_or_none()

        if media_file:
            for key, value in update_data.items():
                setattr(media_file, key, value)
            await self._session.flush()
            await self._session.refresh(media_file)

        return media_file

    async def mark_as_downloading(self, id_: UUID) -> Optional[MediaFile]:
        """
        Mark a media file as downloading.

        Args:
            id_: Media file UUID

        Returns:
            Updated MediaFile instance or None
        """
        return await self.update_status(id_, MediaFileStatus.DOWNLOADING)

    async def mark_as_downloaded(
        self,
        id_: UUID,
        cdn_url: str,
        file_size: int
    ) -> Optional[MediaFile]:
        """
        Mark a media file as downloaded.

        Args:
            id_: Media file UUID
            cdn_url: The downloaded file URL
            file_size: The downloaded file size in bytes

        Returns:
            Updated MediaFile instance or None
        """
        return await self.update_status(
            id_,
            MediaFileStatus.DOWNLOADED,
            cdn_url=cdn_url,
            file_size=file_size
        )

    async def mark_as_processing(self, id_: UUID) -> Optional[MediaFile]:
        """
        Mark a media file as processing.

        Args:
            id_: Media file UUID

        Returns:
            Updated MediaFile instance or None
        """
        return await self.update_status(id_, MediaFileStatus.PROCESSING)

    async def mark_as_completed(self, id_: UUID) -> Optional[MediaFile]:
        """
        Mark a media file as completed.

        Args:
            id_: Media file UUID

        Returns:
            Updated MediaFile instance or None
        """
        return await self.update_status(id_, MediaFileStatus.COMPLETED)

    async def mark_as_failed(self, id_: UUID) -> Optional[MediaFile]:
        """
        Mark a media file as failed.

        Args:
            id_: Media file UUID

        Returns:
            Updated MediaFile instance or None
        """
        return await self.update_status(id_, MediaFileStatus.FAILED)

    async def get_file_count_by_job(self, job_id: UUID) -> int:
        """
        Count media files for a specific job.

        Args:
            job_id: UUID of the parent job

        Returns:
            Number of media files
        """
        return await self.count(job_id=job_id)

    async def get_total_file_size_by_job(self, job_id: UUID) -> int:
        """
        Get total file size for a job's media files.

        Args:
            job_id: UUID of the parent job

        Returns:
            Total size in bytes
        """
        from sqlalchemy import func

        stmt = select(func.sum(self.model.file_size)).where(
            and_(
                self.model.job_id == job_id,
                self.model.status == MediaFileStatus.COMPLETED,
                self.model.is_deleted == False  # type: ignore[attr-defined]
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def search_files(
        self,
        query: str,
        *,
        limit: int = 50,
        offset: int = 0
    ) -> List[MediaFile]:
        """
        Search files by filename or original URL.

        Args:
            query: Search query string
            limit: Maximum number of results
            offset: Number of records to skip

        Returns:
            List of matching MediaFile instances
        """
        search_pattern = f"%{query}%"
        stmt = (
            select(self.model)
            .where(
                and_(
                    or_(
                        self.model.filename.ilike(search_pattern),
                        self.model.original_url.ilike(search_pattern),
                        self.model.cdn_url.ilike(search_pattern)
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
