#!/usr/bin/env python3
"""
Migration Verification Script for Media Analysis Database

Verifies that all migrations have been applied correctly by checking:
1. All expected tables exist
2. All indexes are created
3. All foreign key constraints are valid
4. Soft delete columns are present
5. JSONB columns have GIN indexes
6. Extensions are installed

Usage:
    python migrations/verify_migrations.py --check-only
    python migrations/verify_migrations.py --run-all

Environment Variables:
    MEDIA_DATABASE_URL: PostgreSQL connection string (required)
"""

import asyncio
import argparse
import sys
import os
from typing import Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def get_connection():
    """Get async database connection."""
    import asyncpg

    database_url = os.getenv(
        "MEDIA_DATABASE_URL",
        "postgresql://media_analysis_user:mediapass123@localhost:5433/media_analysis"
    )

    # Convert sqlalchemy URL to asyncpg format
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    return await asyncpg.connect(database_url)


async def check_extensions(conn) -> dict:
    """Verify required PostgreSQL extensions are installed."""
    extensions = await conn.fetch("""
        SELECT extname FROM pg_extension
        WHERE extname IN ('uuid-ossp', 'pg_trgm')
    """)
    ext_names = [e["extname"] for e in extensions]

    return {
        "uuid-ossp": "uuid-ossp" in ext_names,
        "pg_trgm": "pg_trgm" in ext_names,
    }


async def check_tables(conn) -> dict:
    """Verify all expected tables exist."""
    tables = await conn.fetch("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename IN (
            'analysis_job', 'media_file', 'analysis_result',
            'transcription', 'processing_log', 'alembic_version'
        )
    """)
    table_names = [t["tablename"] for t in tables]

    expected_tables = [
        "analysis_job",
        "media_file",
        "analysis_result",
        "transcription",
        "processing_log",
        "alembic_version",
    ]

    return {table: table in table_names for table in expected_tables}


async def check_indexes(conn) -> dict:
    """Verify all expected indexes exist."""
    indexes = await conn.fetch("""
        SELECT indexname, tablename FROM pg_indexes
        WHERE schemaname = 'public'
    """)

    expected_indexes = [
        # Core table indexes
        "ix_analysis_job_status",
        "ix_analysis_job_created_at",
        "ix_analysis_job_is_deleted",
        "ix_media_file_job_id",
        "ix_media_file_status",
        "ix_analysis_result_job_id",
        "ix_analysis_result_provider",
        "ix_transcription_job_id",
        "ix_transcription_provider",
        # Processing log indexes
        "ix_processing_log_job_id",
        "ix_processing_log_stage",
        "ix_processing_log_status",
        "ix_processing_log_created_at",
        # GIN indexes
        "ix_analysis_job_metadata_gin",
        "ix_analysis_result_result_gin",
        "ix_transcription_segments_gin",
        "ix_processing_log_details_gin",
        # Partial indexes
        "ix_analysis_job_status_active",
        "ix_media_file_status_active",
        "ix_analysis_result_provider_active",
        "ix_transcription_provider_active",
        # Composite indexes
        "ix_analysis_job_status_created",
        "ix_analysis_result_job_provider",
        "ix_transcription_job_provider",
    ]

    index_names = [i["indexname"] for i in indexes]
    return {idx: idx in index_names for idx in expected_indexes}


async def check_foreign_keys(conn) -> dict:
    """Verify all foreign key constraints exist."""
    fks = await conn.fetch("""
        SELECT conname AS constraint_name
        FROM pg_constraint
        WHERE contype = 'f'
        AND connamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
    """)

    expected_fks = [
        "fk_media_file_job_id",
        "fk_analysis_result_job_id",
        "fk_transcription_job_id",
        "fk_processing_log_job_id",
    ]

    fk_names = [f["constraint_name"] for f in fks]

    # Also check unnamed FKs (from sa.ForeignKey)
    return {fk: fk in fk_names or any(fk.replace("fk_", "") in name for name in fk_names) for fk in expected_fks}


async def check_soft_delete_columns(conn) -> dict:
    """Verify soft delete columns exist on applicable tables."""
    columns = await conn.fetch("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name IN ('analysis_job', 'media_file', 'analysis_result', 'transcription')
        AND column_name IN ('is_deleted', 'deleted_at')
    """)

    result = {}
    for table in ["analysis_job", "media_file", "analysis_result", "transcription"]:
        table_cols = [c["column_name"] for c in columns if c["table_name"] == table]
        result[f"{table}.is_deleted"] = "is_deleted" in table_cols
        result[f"{table}.deleted_at"] = "deleted_at" in table_cols

    return result


async def check_enum_types(conn) -> dict:
    """Verify enum types exist."""
    types = await conn.fetch("""
        SELECT typname FROM pg_type
        WHERE typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        AND typtype = 'e'
    """)

    expected_types = [
        "job_status",
        "media_type",
        "file_type",
        "media_file_status",
        "analysis_provider",
        "transcription_provider",
        "processing_stage",
        "processing_log_status",
    ]

    type_names = [t["typname"] for t in types]
    return {t: t in type_names for t in expected_types}


async def run_test_operations(conn) -> dict:
    """Run test insert/update/delete operations (optional)."""
    try:
        # Test insert
        job_id = await conn.fetchval("""
            INSERT INTO analysis_job (status, media_type)
            VALUES ('pending', 'video')
            RETURNING id
        """)

        # Test insert media_file
        media_id = await conn.fetchval("""
            INSERT INTO media_file (job_id, file_type, status)
            VALUES ($1, 'source', 'pending')
            RETURNING id
        """, job_id)

        # Test insert processing_log
        log_id = await conn.fetchval("""
            INSERT INTO processing_log (job_id, stage, status)
            VALUES ($1, 'upload', 'started')
            RETURNING id
        """, job_id)

        # Test soft delete
        await conn.execute("""
            UPDATE analysis_job SET is_deleted = TRUE, deleted_at = NOW()
            WHERE id = $1
        """, job_id)

        # Clean up (hard delete)
        await conn.execute("DELETE FROM processing_log WHERE id = $1", log_id)
        await conn.execute("DELETE FROM media_file WHERE id = $1", media_id)
        await conn.execute("DELETE FROM analysis_job WHERE id = $1", job_id)

        return {
            "insert_job": True,
            "insert_media": True,
            "insert_log": True,
            "soft_delete": True,
            "cleanup": True,
        }

    except Exception as e:
        return {"error": str(e)}


async def verify_all(check_only: bool = True) -> dict[str, Any]:
    """Run all verification checks."""
    conn = await get_connection()

    try:
        results = {
            "extensions": await check_extensions(conn),
            "tables": await check_tables(conn),
            "indexes": await check_indexes(conn),
            "foreign_keys": await check_foreign_keys(conn),
            "soft_delete_columns": await check_soft_delete_columns(conn),
            "enum_types": await check_enum_types(conn),
        }

        if not check_only:
            results["test_operations"] = await run_test_operations(conn)

        return results

    finally:
        await conn.close()


def print_results(results: dict[str, Any]) -> bool:
    """Print verification results and return success status."""
    all_passed = True

    for category, checks in results.items():
        print(f"\n=== {category.upper().replace('_', ' ')} ===")

        if isinstance(checks, dict):
            for check, passed in checks.items():
                status = "PASS" if passed else "FAIL"
                symbol = "[+]" if passed else "[-]"
                print(f"  {symbol} {check}: {status}")
                if not passed:
                    all_passed = False
        else:
            print(f"  {checks}")

    return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify media analysis database migrations"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        default=True,
        help="Only check schema (no test operations)"
    )
    parser.add_argument(
        "--run-all",
        action="store_true",
        help="Run all checks including test operations"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    check_only = not args.run_all

    try:
        results = asyncio.run(verify_all(check_only=check_only))

        if args.json:
            import json
            print(json.dumps(results, indent=2, default=str))
        else:
            all_passed = print_results(results)

            print("\n" + "=" * 50)
            if all_passed:
                print("VERIFICATION PASSED: All checks completed successfully")
                sys.exit(0)
            else:
                print("VERIFICATION FAILED: Some checks did not pass")
                sys.exit(1)

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
