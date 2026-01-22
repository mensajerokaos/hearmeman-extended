"""
Alembic migration environment configuration.

This module configures the Alembic migration environment for the Media Analysis API.
It handles database connection, target metadata, and migration script generation.

Target Database: media_analysis (independent from AF infrastructure)
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import models for target metadata
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models.base import Base
from api.models.database import DATABASE_URL

# Import all models to ensure they are registered with Base.metadata
from api.models.job import AnalysisJob
from api.models.media import MediaFile
from api.models.result import AnalysisResult
from api.models.transcription import Transcription


# =============================================================================
# Configuration
# =============================================================================

# Alembic configuration object
config = context.config

# Set the database URL from environment or config
# DATABASE_URL is constructed in api/models/database.py with proper async driver
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name:
    fileConfig(config.config_file_name, disable_existing_loggers=False)


# =============================================================================
# Target Metadata
# =============================================================================

# Target metadata for migrations
# This defines the current state of the database schema
target_metadata = Base.metadata

# Naming convention for constraints (PostgreSQL best practices)
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


# =============================================================================
# Migration Functions
# =============================================================================

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations synchronously.

    Args:
        connection: Database connection
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=False,  # PostgreSQL doesn't need batch mode
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations_online() -> None:
    """
    Run migrations in 'online' mode with async engine.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Main migration entry point for online mode.

    Determines whether to run async or sync migrations based on context.
    """
    # Run async migrations for async database setup
    asyncio.run(run_async_migrations_online())


# =============================================================================
# Entry Point
# =============================================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
