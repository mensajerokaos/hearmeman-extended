"""
Database configuration package initialization.

Re-exports from the parent database.py module for backwards compatibility.
This package structure allows future expansion with submodules while
maintaining the same import paths.

Exports:
    - DATABASE_CONFIG: Current database configuration
    - MEDIA_DATABASE_CONFIG: Media analysis database configuration
    - AF_DATABASE_CONFIG: Legacy AF database configuration
    - POOL_CONFIG: Connection pool settings
    - DATABASE_URL: Constructed database URL for Alembic
    - create_async_engine_configured: Create async SQLAlchemy engine
    - init_session_factory: Initialize session factory
    - set_engine: Set global engine reference
    - set_sessionmaker: Set global session factory reference
    - get_engine: Get global engine instance
    - get_session_factory: Get global session factory instance
    - get_database_url: Get database URL
    - get_async_session: Get async database session
    - close_engine: Close global engine
    - verify_database_connection: Verify database connectivity
"""

# Import from the parent module (database.py at api/models/database.py level)
import sys
import os

# Get the parent directory (api/models/)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the database.py module directly
import importlib.util
database_py_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database.py")
spec = importlib.util.spec_from_file_location("database_module", database_py_path)
database_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(database_module)

# Re-export all public names
DATABASE_CONFIG = database_module.DATABASE_CONFIG
MEDIA_DATABASE_CONFIG = database_module.MEDIA_DATABASE_CONFIG
AF_DATABASE_CONFIG = database_module.AF_DATABASE_CONFIG
POOL_CONFIG = database_module.POOL_CONFIG
DATABASE_URL = database_module.DATABASE_URL
create_async_engine_configured = database_module.create_async_engine_configured
init_session_factory = database_module.init_session_factory
set_engine = database_module.set_engine
set_sessionmaker = database_module.set_sessionmaker
get_engine = database_module.get_engine
get_session_factory = database_module.get_session_factory
get_database_url = database_module.get_database_url
get_async_session = database_module.get_async_session
close_engine = database_module.close_engine
verify_database_connection = database_module.verify_database_connection

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
