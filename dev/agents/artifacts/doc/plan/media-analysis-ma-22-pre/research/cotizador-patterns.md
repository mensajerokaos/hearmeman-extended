# Cotizador-API Database Patterns Research

**Research Date:** 2026-01-20
**Source:** `/opt/clients/af/services/cotizador-api/`
**Context:** MA-22 Pre-Implementation Database Layer Design

---

## 1. Database Configuration

### Environment Variables (Lines 117-125 in cotizador_api.py)

```python
DB_HOST = os.getenv("DB_HOST", "af-postgres-1")  # Docker container name
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "af-memory")
DB_USER = os.getenv("DB_USER", "n8n")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
```

**Key Observations:**
- Uses Docker container name for DB_HOST (service discovery)
- Default database: `af-memory` (shared instance)
- Default user: `n8n` (existing n8n automation user)
- Password managed via environment variable (RunPod secrets)

### Connection Pattern (Lines 242-260)

```python
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# Usage:
with conn.cursor(cursor_factory=RealDictCursor) as cur:
    cur.execute(query, params)
    result = cur.fetchall()
```

**Key Observations:**
- Uses `psycopg2` (synchronous PostgreSQL adapter)
- Uses `RealDictCursor` for dictionary-style row access
- Pattern: Context manager for connection lifecycle
- No connection pooling (single connection per request pattern)
- **LIMITATION:** Not suitable for async FastAPI applications

---

## 2. Database Tables (Inferred from Code)

Based on code analysis of `cotizador_api.py` and `archive_endpoint.py`:

### Primary Tables

| Table Name | Purpose | Key Fields |
|------------|---------|------------|
| `quotes` | Main quote records | session_id, status, damage_assessment, quote_data |
| `leads` | Kommo lead references | lead_id, contact_id, status |
| `contacts` | Customer contacts | contact_id, name, phone, email |
| `media_files` | Attached media | file_path, media_type, session_id |
| `form_tokens` | Secure form tokens | token, session_id, expiry |
| `hitl_reviews` | Review history | review_id, claim_id, reviewer_id, status |
| `ab_test_log` | A/B test events | session_id, event_type, extraction_method |

### Table Naming Convention

- **Plural form:** `quotes`, `leads`, `contacts`, `media_files`
- **Snake_case:** All lowercase with underscores
- **Prefix:** None (shared database uses context)
- **ID pattern:** `id` (auto-increment primary key)

---

## 3. Database Operations Found

### CRUD Operations

1. **Quote CRUD:**
   - Create quote from analysis results
   - Update quote status (pending → processed → approved)
   - Retrieve quote by session_id or quote_id
   - Merge duplicate quotes

2. **Lead/Contact Management:**
   - Fetch customer context from Kommo CRM
   - Link quotes to leads/contacts
   - Update lead stage in pipeline

3. **HITL (Human-In-The-Loop) Management:**
   - Queue management for reviews
   - Claim/release mechanism (CLAIM_TTL_SECONDS=600)
   - Review history tracking

4. **Media File Tracking:**
   - Store media file references
   - Track extraction method for A/B testing
   - Link files to sessions/quotes

5. **Form Token Management:**
   - Generate secure form tokens
   - Track token expiry
   - Validate tokens on submission

---

## 4. Current Limitations

### Technical Debt Identified

| Issue | Impact | Recommendation |
|-------|--------|----------------|
| Synchronous psycopg2 | Blocks event loop in async FastAPI | Migrate to asyncpg |
| No connection pooling | Poor scalability under load | Implement asyncpg pool |
| No SQLAlchemy models | Manual schema management | Add SQLAlchemy ORM |
| Direct queries in API | SQL injection risk | Use parameterized queries |
| No transaction management | Data integrity issues | Add explicit transactions |
| No migration system | Schema changes difficult | Add Alembic migrations |
| No soft delete | Data recovery impossible | Add deleted_at column |

---

## 5. Recommended Architecture for Media-Analysis-API

Based on the cotizador-api patterns and modern Python async practices:

### Proposed Stack

```python
# asyncpg connection pool
from asyncpg import Pool
import asyncpg

# SQLAlchemy Core + Async
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

# Pydantic v2
from pydantic import BaseModel, Field
from typing import Optional
```

### Connection Pool Configuration

```python
# Recommended asyncpg pool settings
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "af-postgres-1"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "af-memory"),
    "user": os.getenv("DB_USER", "n8n"),
    "password": os.getenv("DB_PASSWORD", ""),
    "min_size": 5,              # Warm connections
    "max_size": 20,             # Max concurrent connections
    "command_timeout": 60,      # Query timeout (seconds)
    "statement_cache_size": 100 # Prepared statement cache
}
```

### Proposed Directory Structure

```
/opt/services/media-analysis/api/
├── models/
│   ├── __init__.py
│   ├── database.py           # Connection pool & engine
│   ├── base.py               # SQLAlchemy Base class
│   ├── mixins.py             # TimestampMixin, SoftDeleteMixin
│   ├── session.py            # Session management
│   ├── quote.py              # Quote model
│   ├── media_file.py         # Media file model
│   ├── analysis.py           # Analysis result model
│   └── hitl_review.py        # HITL review model
├── schemas/
│   ├── __init__.py
│   ├── quote.py              # Quote schemas (Create, Update, Response)
│   ├── media_file.py         # Media file schemas
│   ├── analysis.py           # Analysis schemas
│   └── hitl_review.py        # HITL review schemas
└── dependencies.py           # Database dependency injection
```

---

## 6. Best Practices Identified

### From Cotizador-API

1. **Environment-based Configuration:**
   - Use `os.getenv()` with sensible defaults
   - Docker service names for host
   - RunPod secrets for sensitive values

2. **Context-based Naming:**
   - Table names use plural form
   - Snake_case column names
   - ISO timestamps for audit fields

3. **Session-based Tracking:**
   - Use session_id for correlation
   - Track extraction method for A/B testing
   - Link media files to sessions

### Gaps to Address

1. **Missing Async Support:**
   - Current code uses synchronous psycopg2
   - Media-analysis-api needs async for FastAPI

2. **No ORM Layer:**
   - Manual query construction
   - No type safety for queries
   - Difficult schema evolution

3. **No Transaction Scope:**
   - Implicit transactions only
   - No explicit rollback handling
   - Race condition risk in concurrent access

---

## 7. Code Examples to Reuse

### Environment Variable Loading

```python
# From cotizador_api.py (lines 117-125)
DB_HOST = os.getenv("DB_HOST", "af-postgres-1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "af-memory")
DB_USER = os.getenv("DB_USER", "n8n")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
```

### Connection Function Pattern

```python
# From cotizador_api.py (lines 247-254)
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
```

### Cursor Usage Pattern

```python
# From cotizador_api.py (lines 257-259)
with conn.cursor(cursor_factory=RealDictCursor) as cur:
    cur.execute(query, params)
    result = cur.fetchall()
```

---

## 8. Files Analyzed

| File | Size | Key Findings |
|------|------|--------------|
| `cotizador_api.py` | 343KB | Main FastAPI app, psycopg2 database usage |
| `archive_endpoint.py` | 8KB | Archive functionality with DB queries |
| `.env.example` | Template | Environment variable documentation |

---

## 9. References

- **PostgreSQLpsycopg2 Documentation:** https://www.psycopg.org/
- **asyncpg Documentation:** https://magicstack.github.io/asyncpg/
- **SQLAlchemy Async Documentation:** https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **Pydantic Documentation:** https://docs.pydantic.dev/

---

**Research completed.** Next step: Audit current media-analysis-api state.
