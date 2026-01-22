"""
SQLAlchemy declarative base and mixins.

Provides base classes for all SQLAlchemy models including:
- Base: Declarative base class
- TimestampMixin: Automatic created_at and updated_at tracking
- SoftDeleteMixin: Soft delete functionality (optional)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr


class Base(DeclarativeBase):
    """
    Declarative base class for all SQLAlchemy models.

    Provides:
    - Type-safe model definition
    - Automatic table name generation from class name
    - Integration with async sessions
    """

    pass


class TimestampMixin:
    """
    Mixin for automatic timestamp tracking.

    Adds:
    - created_at: Creation timestamp (set once)
    - updated_at: Last modification timestamp (auto-updated)

    Usage:
        ```python
        class MyModel(Base, TimestampMixin):
            __tablename__ = "my_model"
            id = mapped_column(Integer, primary_key=True)
        ```
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Record creation timestamp"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Last modification timestamp"
    )


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.

    Adds:
    - deleted_at: Timestamp when record was soft-deleted (None if active)
    - is_deleted: Boolean flag for soft delete status

    Usage:
        ```python
        class MyModel(Base, TimestampMixin, SoftDeleteMixin):
            __tablename__ = "my_model"
            id = mapped_column(Integer, primary_key=True)
        ```

    Note: Requires explicit filtering by deleted_at IS NULL in queries
    for production use.
    """

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Soft delete timestamp (None if active)"
    )

    is_deleted: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        doc="Soft delete flag"
    )

    @property
    def is_active(self) -> bool:
        """
        Check if record is active (not soft-deleted).

        Returns:
            True if record is not deleted, False otherwise
        """
        return not self.is_deleted and self.deleted_at is None


class UUIDMixin:
    """
    Mixin for UUID primary key generation.

    Adds:
    - id: UUID primary key with auto-generation

    Usage:
        ```python
        class MyModel(Base, UUIDMixin):
            __tablename__ = "my_model"
        ```

    Note: UUIDs are generated client-side (Python) for compatibility
    across database backends.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name from class name (snake_case).

        Example: AnalysisJob -> analysis_jobs
        """
        name = cls.__name__
        # Convert CamelCase to snake_case
        snake_case = ""
        for i, char in enumerate(name):
            if char.isupper():
                if i > 0:
                    snake_case += "_"
                snake_case += char.lower()
            else:
                snake_case += char
        return snake_case + "s"


# Convenience exports
__all__ = [
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "UUIDMixin",
]
