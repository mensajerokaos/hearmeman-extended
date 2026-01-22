"""
FastAPI dependency injection for database sessions.

Provides FastAPI Depends() compatible functions for:
- get_engine: Dependency to get database engine
- get_session: Dependency to get async session
- get_session_factory: Dependency to get session factory
- get_async_session: Context manager dependency

Usage in FastAPI routes:
    ```python
    from fastapi import APIRouter, Depends
    from api.models.database import get_engine, get_session
    from api.models.dependencies import get_session_factory

    router = APIRouter()

    @router.get("/items/")
    async def read_items(
        session = Depends(get_session)
    ):
        # Use session for database operations
        pass
    ```
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from api.models.database import (
    get_engine,
    get_session_factory,
)

# Type aliases for clarity
SessionFactory = async_sessionmaker[AsyncSession]
Engine = AsyncEngine


def get_engine_dependency() -> Engine:
    """
    FastAPI dependency to get database engine.

    Returns:
        AsyncEngine instance

    Raises:
        HTTPException: 503 if engine not initialized
    """
    try:
        return get_engine()
    except RuntimeError as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail=f"Database not available: {str(e)}"
        )


def get_session_factory_dependency() -> SessionFactory:
    """
    FastAPI dependency to get session factory.

    Returns:
        async_sessionmaker[AsyncSession] instance

    Raises:
        HTTPException: 503 if session factory not initialized
    """
    try:
        return get_session_factory()
    except RuntimeError as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail=f"Database session factory not available: {str(e)}"
        )


async def get_session_dependency(
    session_factory: SessionFactory = Depends(get_session_factory_dependency)
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get async database session.

    Provides automatic session management with commit/rollback.
    Sessions are automatically returned to pool after use.

    Args:
        session_factory: Injected session factory

    Yields:
        AsyncSession instance

    Example:
        ```python
        @router.post("/items/")
        async def create_item(
            item: ItemCreate,
            session: AsyncSession = Depends(get_session)
        ):
            db_item = ItemModel(**item.model_dump())
            session.add(db_item)
            await session.commit()
            await session.refresh(db_item)
            return db_item
        ```
    """
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_async_session_dependency(
    session_factory: SessionFactory = Depends(get_session_factory_dependency)
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for async context manager session.

    Alternative to get_session_dependency when manual control needed.

    Args:
        session_factory: Injected session factory

    Yields:
        AsyncSession instance
    """
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Convenience function aliases for common usage
get_engine = get_engine_dependency
get_session = get_session_dependency
get_session_factory = get_session_factory_dependency

# Re-export for Depends usage
__all__ = [
    "get_engine",
    "get_session",
    "get_session_factory",
    "get_async_session",
    "get_engine_dependency",
    "get_session_factory_dependency",
    "get_session_dependency",
    "get_async_session_dependency",
]
