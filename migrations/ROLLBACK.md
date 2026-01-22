# Media Analysis Database Rollback Procedures

This document outlines rollback procedures for each migration in the media analysis database.

## Migration History

| Revision | Name | Dependencies | Reversible |
|----------|------|--------------|------------|
| 000000000001 | Initial tables | None | Yes |
| 000000000002 | Processing log + indexes | 000000000001 | Yes |

---

## Rollback Commands

### Using Alembic (Recommended)

```bash
# Check current migration version
alembic -c alembic.ini current

# Rollback last migration
alembic -c alembic.ini downgrade -1

# Rollback to specific revision
alembic -c alembic.ini downgrade 000000000001

# Rollback all migrations (start fresh)
alembic -c alembic.ini downgrade base
```

### Manual Rollback

#### Rollback Migration 000000000002 (Processing Log + Indexes)

```sql
-- Drop GIN indexes
DROP INDEX IF EXISTS ix_analysis_job_metadata_gin;
DROP INDEX IF EXISTS ix_analysis_result_result_gin;
DROP INDEX IF EXISTS ix_transcription_segments_gin;
DROP INDEX IF EXISTS ix_processing_log_details_gin;

-- Drop partial indexes
DROP INDEX IF EXISTS ix_analysis_job_status_active;
DROP INDEX IF EXISTS ix_media_file_status_active;
DROP INDEX IF EXISTS ix_analysis_result_provider_active;
DROP INDEX IF EXISTS ix_transcription_provider_active;

-- Drop composite indexes
DROP INDEX IF EXISTS ix_analysis_job_status_created;
DROP INDEX IF EXISTS ix_analysis_result_job_provider;
DROP INDEX IF EXISTS ix_transcription_job_provider;

-- Drop processing_log table
DROP TABLE IF EXISTS processing_log;

-- Drop enum types
DROP TYPE IF EXISTS processing_log_status CASCADE;
DROP TYPE IF EXISTS processing_stage CASCADE;

-- Update alembic version
UPDATE alembic_version SET version_num = '000000000001';
```

#### Rollback Migration 000000000001 (Initial Tables)

```sql
-- Drop tables (order matters - respect FK constraints)
DROP TABLE IF EXISTS transcription CASCADE;
DROP TABLE IF EXISTS analysis_result CASCADE;
DROP TABLE IF EXISTS media_file CASCADE;
DROP TABLE IF EXISTS analysis_job CASCADE;

-- Drop enum types
DROP TYPE IF EXISTS transcription_provider CASCADE;
DROP TYPE IF EXISTS analysis_provider CASCADE;
DROP TYPE IF EXISTS media_file_status CASCADE;
DROP TYPE IF EXISTS file_type CASCADE;
DROP TYPE IF EXISTS media_type CASCADE;
DROP TYPE IF EXISTS job_status CASCADE;

-- Remove alembic tracking
DELETE FROM alembic_version;
```

---

## Full Database Reset (Nuclear Option)

**WARNING**: This deletes ALL data. Use only in development.

```bash
# Connect to PostgreSQL as superuser
psql -h localhost -U postgres

# Drop and recreate database
DROP DATABASE IF EXISTS media_analysis;
CREATE DATABASE media_analysis OWNER media_analysis_user;

# Connect to new database
\c media_analysis

# Install extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

# Grant permissions
GRANT ALL PRIVILEGES ON DATABASE media_analysis TO media_analysis_user;
```

Then re-run migrations:
```bash
alembic -c alembic.ini upgrade head
```

---

## Emergency Recovery

### If Migration Fails Mid-Way

1. Check current state:
   ```bash
   alembic -c alembic.ini current
   ```

2. Mark migration as applied (if tables exist but version missing):
   ```bash
   alembic -c alembic.ini stamp <revision>
   ```

3. Or manually insert version:
   ```sql
   INSERT INTO alembic_version (version_num) VALUES ('000000000001');
   ```

### If Database is Corrupted

1. Restore from backup:
   ```bash
   pg_restore -h localhost -U postgres -d media_analysis /backups/media_analysis_<timestamp>.dump
   ```

2. Or recreate from scratch (development only):
   ```bash
   dropdb -h localhost -U postgres media_analysis
   createdb -h localhost -U postgres -O media_analysis_user media_analysis
   alembic -c alembic.ini upgrade head
   ```

---

## Verification After Rollback

After any rollback, verify database state:

```bash
# Run verification script
python migrations/verify_migrations.py --check-only

# Or manually check tables
psql -h localhost -U media_analysis_user -d media_analysis -c "\dt"
psql -h localhost -U media_analysis_user -d media_analysis -c "\di"
```

---

## Contact

For issues with migrations or rollback procedures:
- Review migration files in `migrations/versions/`
- Check Alembic documentation: https://alembic.sqlalchemy.org/
- Test in development before production rollback
