"""
Base Repository Module

Generic repository pattern implementation for async SQLAlchemy operations.
Provides common CRUD operations with type safety and async context manager support.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Generic, TypeVar, AsyncGenerator, Type, Optional, List, Dict, Any

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from api.models.base import Base


# Type variable for generic repository
T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    Generic repository class providing common CRUD operations.

    Args:
        model: SQLAlchemy model class
        session: AsyncSession instance

    Example:
        ```python
        class UserRepository(BaseRepository[User]):
            pass

        user_repo = UserRepository(User, session)
        user = await user_repo.get_by_id(user_id)
        ```
    """

    def __init__(self, model: Type[T], session: AsyncSession) -> None:
        """
        Initialize repository with model class and database session.

        Args:
            model: SQLAlchemy model class (must inherit from Base)
            session: AsyncSession instance for database operations
        """
        self._model = model
        self._session = session

    @property
    def model(self) -> Type[T]:
        """Get the model class."""
        return self._model

    @property
    def table_name(self) -> str:
        """Get the table name from model's __tablename__."""
        return self._model.__tablename__

    async def get_by_id(self, id_: Any) -> Optional[T]:
        """
        Retrieve a record by its primary key ID.

        Args:
            id_: Primary key value (UUID for most models)

        Returns:
            Model instance if found, None otherwise
        """
        stmt = select(self._model).where(
            self._model.id == id_,
            self._model.is_deleted == False  # type: ignore[attr-defined]
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_deleted(self, id_: Any) -> Optional[T]:
        """
        Retrieve a record by ID including soft-deleted records.

        Args:
            id_: Primary key value

        Returns:
            Model instance if found, None otherwise
        """
        stmt = select(self._model).where(self._model.id == id_)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_one(self, **kwargs: Any) -> Optional[T]:
        """
        Retrieve a single record matching the given criteria.

        Args:
            **kwargs: Field-value pairs to filter by

        Returns:
            First matching model instance or None

        Raises:
            MultipleResultsFound: If multiple records match
        """
        stmt = select(self._model).filter_by(
            is_deleted=False,  # type: ignore[attr-defined]
            **kwargs
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        descending: bool = True
    ) -> List[T]:
        """
        Retrieve all non-deleted records with pagination.

        Args:
            offset: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field name to order by (default: created_at)
            descending: Sort in descending order (default: True)

        Returns:
            List of model instances
        """
        order_column = getattr(
            self._model,
            order_by or "created_at",
            self._model.created_at  # type: ignore[attr-defined]
        )
        if descending:
            order_column = order_column.desc()

        stmt = (
            select(self._model)
            .where(self._model.is_deleted == False)  # type: ignore[attr-defined]
            .offset(offset)
            .limit(limit)
            .order_by(order_column)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list(
        self,
        *,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        descending: bool = True
    ) -> List[T]:
        """
        List records with optional filtering and pagination.

        Args:
            filters: Dictionary of field-value pairs to filter by
            offset: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field name to order by
            descending: Sort in descending order

        Returns:
            List of matching model instances
        """
        stmt = select(self._model).where(
            self._model.is_deleted == False  # type: ignore[attr-defined]
        )

        if filters:
            for key, value in filters.items():
                if hasattr(self._model, key):
                    stmt = stmt.where(getattr(self._model, key) == value)

        order_column = getattr(
            self._model,
            order_by or "created_at",
            self._model.created_at  # type: ignore[attr-defined]
        )
        if descending:
            order_column = order_column.desc()

        stmt = stmt.offset(offset).limit(limit).order_by(order_column)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, **kwargs: Any) -> int:
        """
        Count records matching the given criteria.

        Args:
            **kwargs: Field-value pairs to filter by

        Returns:
            Number of matching records
        """
        stmt = select(func.count(self._model.id)).filter_by(
            is_deleted=False,  # type: ignore[attr-defined]
            **kwargs
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def exists(self, **kwargs: Any) -> bool:
        """
        Check if any record exists matching the criteria.

        Args:
            **kwargs: Field-value pairs to filter by

        Returns:
            True if at least one record exists
        """
        count = await self.count(**kwargs)
        return count > 0

    async def create(self, **kwargs: Any) -> T:
        """
        Create a new record.

        Args:
            **kwargs: Field-value pairs for the new record

        Returns:
            Created model instance
        """
        instance = self._model(**kwargs)
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def update(self, id_: Any, **kwargs: Any) -> Optional[T]:
        """
        Update an existing record by ID.

        Args:
            id_: Primary key of the record to update
            **kwargs: Field-value pairs to update

        Returns:
            Updated model instance or None if not found
        """
        update_data = {
            k: v for k, v in kwargs.items()
            if v is not None and hasattr(self._model, k)
        }
        update_data["updated_at"] = datetime.utcnow()

        stmt = (
            update(self._model)
            .where(
                self._model.id == id_,
                self._model.is_deleted == False  # type: ignore[attr-defined]
            )
            .values(**update_data)
            .returning(self._model)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_by(self, filters: Dict[str, Any], **kwargs: Any) -> int:
        """
        Update all records matching filters.

        Args:
            filters: Field-value pairs to filter by
            **kwargs: Field-value pairs to update

        Returns:
            Number of records updated
        """
        update_data = {
            k: v for k, v in kwargs.items()
            if v is not None and hasattr(self._model, k)
        }
        update_data["updated_at"] = datetime.utcnow()

        stmt = update(self._model).filter_by(
            is_deleted=False,  # type: ignore[attr-defined]
            **filters
        ).values(**update_data)

        result = await self._session.execute(stmt)
        return result.rowcount

    async def delete(self, id_: Any, soft: bool = True) -> bool:
        """
        Delete a record by ID.

        Args:
            id_: Primary key of the record to delete
            soft: If True, perform soft delete (default: True)

        Returns:
            True if record was deleted
        """
        if soft:
            return await self.soft_delete(id_)
        else:
            return await self.hard_delete(id_)

    async def soft_delete(self, id_: Any) -> bool:
        """
        Soft delete a record by ID (sets is_deleted=True).

        Args:
            id_: Primary key of the record to soft delete

        Returns:
            True if record was found and updated
        """
        stmt = (
            update(self._model)
            .where(
                self._model.id == id_,
                self._model.is_deleted == False  # type: ignore[attr-defined]
            )
            .values(
                is_deleted=True,  # type: ignore[attr-defined]
                deleted_at=datetime.utcnow()
            )
            .returning(self._model.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def hard_delete(self, id_: Any) -> bool:
        """
        Hard delete a record by ID (permanently removes from database).

        Args:
            id_: Primary key of the record to hard delete

        Returns:
            True if record was found and deleted
        """
        stmt = (
            delete(self._model)
            .where(self._model.id == id_)
            .returning(self._model.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def restore(self, id_: Any) -> Optional[T]:
        """
        Restore a soft-deleted record.

        Args:
            id_: Primary key of the record to restore

        Returns:
            Restored model instance or None if not found
        """
        stmt = (
            update(self._model)
            .where(
                self._model.id == id_,
                self._model.is_deleted == True  # type: ignore[attr-defined]
            )
            .values(
                is_deleted=False,  # type: ignore[attr-defined]
                deleted_at=None
            )
            .returning(self._model)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[None, None]:
        """
        Context manager for database transactions.

        Usage:
            async with repo.transaction():
                await repo.create(...)
                await repo.update(...)
            # Auto-commits on success, rolls back on exception
        """
        try:
            yield
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def execute(self, stmt: Select) -> List[T]:
        """
        Execute a custom SELECT statement.

        Args:
            stmt: SQLAlchemy Select statement

        Returns:
            List of model instances
        """
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def scalar(self, stmt: Select) -> Optional[T]:
        """
        Execute a SELECT statement and return single result.

        Args:
            stmt: SQLAlchemy Select statement

        Returns:
            Single model instance or None
        """
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def query(self) -> Select:
        """
        Start building a query with the model.

        Returns:
            Select statement ready for filtering

        Usage:
            results = await repo.query().filter(
                User.status == "active"
            ).limit(10).all()
        """
        return select(self._model)

    def filter_active(self) -> Select:
        """
        Start a query filtering out soft-deleted records.

        Returns:
            Select statement with is_deleted=False filter
        """
        return select(self._model).where(
            self._model.is_deleted == False  # type: ignore[attr-defined]
        )
