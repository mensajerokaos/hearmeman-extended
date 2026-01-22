-- =============================================================================
-- Media Analysis Database Initialization Script
-- =============================================================================
-- This script initializes the media_analysis database with:
-- 1. Database creation (if not exists)
-- 2. User creation with proper permissions
-- 3. Required PostgreSQL extensions
-- =============================================================================

-- Create database user (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'media_analysis_user') THEN
        CREATE USER media_analysis_user WITH PASSWORD 'media_analysis_secure_pwd_2026';
    END IF;
END
$$;

-- Grant connection privileges
GRANT CONNECT ON DATABASE media_analysis TO media_analysis_user;

-- Connect to media_analysis database and set up extensions
\c media_analysis

-- Create required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant schema usage
GRANT USAGE ON SCHEMA public TO media_analysis_user;

-- Grant privileges on all tables (current and future)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO media_analysis_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO media_analysis_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO media_analysis_user;

-- Grant privileges on existing objects
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO media_analysis_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO media_analysis_user;

-- Verify extensions installed
SELECT extname, extversion FROM pg_extension WHERE extname IN ('uuid-ossp', 'pg_trgm');

-- Log completion
SELECT 'Media Analysis database initialized successfully' AS status;
