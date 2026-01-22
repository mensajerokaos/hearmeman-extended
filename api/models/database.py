"""
Async SQLAlchemy 2.0 database engine configuration.

Provides async engine creation, session management, and connection pooling
for the media-analysis-api with PostgreSQL.

Supports two database modes:
1. media_analysis (new independent database) - DEFAULT
2. af_memory (legacy AF infrastructure) - fallback

Pool Configuration:
- min_size: 5 (minimum connections)
- max_size: 20 (maximum connections)
- max_overflow: 10 (additional connections beyond max_size)
- pool_timeout: 30 seconds (connection acquisition timeout)
- pool_recycle: 1800 seconds (connection recycle time)
- pool_pre_ping: True (verify connections before use)
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

logger = logging.getLogger(__name__)

# =============================================================================
# Global engine and sessionmaker references
# =============================================================================
_ENGINE: Optional[AsyncEngine] = None
_SESSION_FACTORY: Optional[async_sessionmaker[AsyncSession]] = None

# =============================================================================
# Database Configuration - Media Analysis (NEW - Independent Database)
# =============================================================================
MEDIA_DATABASE_CONFIG = {
    "host": os.environ.get("MEDIA_DB_HOST", "media-pg-1"),
    "port": int(os.environ.get("MEDIA_DB_PORT", "5432")),
    "database": os.environ.get("MEDIA_DB_NAME", "media_analysis"),
    "user": os.environ.get("MEDIA_DB_USER", "media_analysis_user"),
    "password": os.environ.get("MEDIA_DB_PASSWORD", "media_analysis_secure_pwd_2026"),
}

# =============================================================================
# Legacy Database Configuration - AF Memory (FALLBACK)
# =============================================================================
AF_DATABASE_CONFIG = {
    "host": os.environ.get("AF_DB_HOST", "af-postgres-1"),
    "port": int(os.environ.get("AF_DB_PORT", "5432")),
    "database": os.environ.get("AF_DB_NAME", "af-memory"),
    "user": os.environ.get("AF_DB_USER", "n8n"),
    "password": os.environ.get("AF_DB_PASSWORD", ""),
}

# =============================================================================
# Select Active Database Configuration
# =============================================================================
# Use MEDIA_DATABASE_URL env var for full override, otherwise use MEDIA_DATABASE_CONFIG
# Set USE_AF_DATABASE=true to use legacy AF database
USE_AF_DATABASE = os.environ.get("USE_AF_DATABASE", "false").lower() == "true"
DATABASE_CONFIG = AF_DATABASE_CONFIG if USE_AF_DATABASE else MEDIA_DATABASE_CONFIG

# =============================================================================
# Connection Pool Settings (Production-optimized)
# =============================================================================
POOL_CONFIG = {
    "min_size": int(os.environ.get("DB_POOL_MIN", "5")),
    "max_size": int(os.environ.get("DB_POOL_MAX", "20")),
    "max_overflow": int(os.environ.get("DB_POOL_OVERFLOW", "10")),
    "pool_timeout": int(os.environ.get("DB_POOL_TIMEOUT", "30")),
    "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", "1800")),
    "pool_pre_ping": True,
}


def get_database_url() -> str:
    """
    Construct async PostgreSQL connection URL.

    Priority:
    1. MEDIA_DATABASE_URL environment variable (full URL override)
    2. Constructed from DATABASE_CONFIG

    Returns:
        Async connection URL: postgresql+asyncpg://user:password@host:port/database
    """
    # Allow full URL override via environment variable
    env_url = os.environ.get("MEDIA_DATABASE_URL")
    if env_url:
        # Ensure it's an async URL
        if env_url.startswith("postgresql://"):
            env_url = env_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return env_url

    config = DATABASE_CONFIG
    password_part = f":{config['password']}" if config.get('password') else ""
    return (
        f"postgresql+asyncpg://{config['user']}{password_part}@"
        f"{config['host']}:{config['port']}/{config['database']}"
    )


# Export DATABASE_URL for Alembic compatibility
DATABASE_URL = get_database_url()


def create_async_engine_configured() -> AsyncEngine:
    """
    Create configured async SQLAlchemy engine with connection pooling.

    Uses asyncpg for high-performance async PostgreSQL connections.
    Configures pool settings for production workloads.

    Returns:
        Configured AsyncEngine instance
    """
    global _ENGINE

    if _ENGINE is not None:
        logger.warning("Engine already exists, returning existing engine")
        return _ENGINE

    pool_class = AsyncAdaptedQueuePool

    _ENGINE = create_async_engine(
        get_database_url(),
        poolclass=pool_class,
        pool_size=POOL_CONFIG["min_size"],
        max_overflow=POOL_CONFIG["max_overflow"],
        pool_timeout=POOL_CONFIG["pool_timeout"],
        pool_recycle=POOL_CONFIG["pool_recycle"],
        pool_pre_ping=POOL_CONFIG["pool_pre_ping"],
        echo=os.environ.get("DB_ECHO", "false").lower() == "true",
        echo_pool=False,
        execution_options={
            "compiled_cache": {},
        },
    )

    db_name = DATABASE_CONFIG.get("database", "unknown")
    logger.info(
        f"Created async engine for '{db_name}': pool_size={POOL_CONFIG['min_size']}, "
        f"max_overflow={POOL_CONFIG['max_overflow']}"
    )

    return _ENGINE


def init_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Initialize session factory with configured engine.

    Args:
        engine: AsyncEngine instance to bind

    Returns:
        Configured async_sessionmaker for AsyncSession creation
    """
    global _SESSION_FACTORY

    if _SESSION_FACTORY is not None:
        logger.warning("Session factory already exists, returning existing factory")
        return _SESSION_FACTORY

    _SESSION_FACTORY = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    logger.info("Initialized async session factory")
    return _SESSION_FACTORY


def set_engine(engine: AsyncEngine) -> None:
    """
    Set global engine reference.

    Args:
        engine: AsyncEngine instance to set as global
    """
    global _ENGINE
    _ENGINE = engine
    logger.info("Global engine reference set")


def set_sessionmaker(sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    """
    Set global session factory reference.

    Args:
        sessionmaker: async_sessionmaker to set as global
    """
    global _SESSION_FACTORY
    _SESSION_FACTORY = sessionmaker
    logger.info("Global session factory reference set")


def get_engine() -> AsyncEngine:
    """
    Get global engine instance.

    Returns:
        Global AsyncEngine instance

    Raises:
        RuntimeError: If engine not initialized
    """
    if _ENGINE is None:
        raise RuntimeError("Engine not initialized. Call create_async_engine_configured() first.")
    return _ENGINE


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get global session factory instance.

    Returns:
        Global async_sessionmaker instance

    Raises:
        RuntimeError: If session factory not initialized
    """
    if _SESSION_FACTORY is None:
        raise RuntimeError(
            "Session factory not initialized. Call init_session_factory(engine) first."
        )
    return _SESSION_FACTORY


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session as context manager.

    Yields:
        AsyncSession instance for database operations

    Example:
        ```python
        async with get_async_session() as session:
            await session.execute(text("SELECT 1"))
        ```
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_engine() -> None:
    """
    Close global engine and cleanup resources.

    Properly disposes of connection pool and clears global references.
    Should be called during application shutdown.
    """
    global _ENGINE, _SESSION_FACTORY

    if _ENGINE is not None:
        await _ENGINE.dispose()
        logger.info("Async engine disposed")
        _ENGINE = None

    _SESSION_FACTORY = None
    logger.info("Database engine cleanup complete")


async def verify_database_connection() -> bool:
    """
    Verify database connectivity with health check.

    Attempts to acquire a connection and execute simple query.

    Returns:
        True if connection successful, False otherwise

    Raises:
        Exception: Propagates connection errors
    """
    from sqlalchemy import text

    engine = get_engine()

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            await result.scalar()
            logger.info("Database connection verified successfully")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


# =============================================================================
# Convenience exports
# =============================================================================
__all__ = [
    # Configuration
    "DATABASE_CONFIG",
    "MEDIA_DATABASE_CONFIG",
    "AF_DATABASE_CONFIG",
    "POOL_CONFIG",
    "DATABASE_URL",
    # Engine management
    "create_async_engine_configured",
    "init_session_factory",
    "set_engine",
    "set_sessionmaker",
    "get_engine",
    "get_session_factory",
    "get_database_url",
    # Session management
    "get_async_session",
    # Cleanup
    "close_engine",
    "verify_database_connection",
]
