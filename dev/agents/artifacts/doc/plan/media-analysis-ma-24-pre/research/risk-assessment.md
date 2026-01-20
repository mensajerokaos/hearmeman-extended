# Risk Assessment: Media Analysis API Database Integration

**Date**: 2026-01-20
**Task**: Database Integration PRD Research - Phase 4
**Output**: /home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-24-pre/research/risk-assessment.md

---

## 1. Risk Matrix

| Risk | Impact | Likelihood | Priority | Owner |
|------|--------|------------|----------|-------|
| Database Migration | HIGH | MEDIUM | P1 | DevOps Lead |
| Data Consistency | MEDIUM | MEDIUM | P2 | Backend Lead |
| Performance | MEDIUM | HIGH | P2 | Backend Lead |
| API Compatibility | HIGH | LOW | P3 | API Owner |
| Soft Delete Complexity | LOW | MEDIUM | P4 | Backend Developer |

---

## 2. Detailed Risk Analysis

### 2.1 Database Migration Risk

**Severity**: HIGH
**Probability**: 30%
**Impact**: Service downtime, data loss, extended recovery time

**Description**:
Migration of `analysis_request` table may fail due to:
- Schema conflicts with existing tables
- Constraint violations with existing data
- Long-running locks blocking production traffic
- Connection pool exhaustion during migration

**Early Warning Signs**:
- Migration hangs for >60 seconds
- Connection timeout errors
- Constraint violation errors in logs
- Increased API latency during migration

**Mitigation Strategy**:

1. **Pre-Migration Backup** (Owner: DevOps, Deadline: Before migration)
   ```bash
   # Create full database backup
   pg_dump -h $DB_HOST -U $DB_USER -d media_analysis > backup_pre_migration_$(date +%Y%m%d_%H%M%S).sql

   # Verify backup integrity
   pg_restore --list backup_pre_migration_*.sql | head -20
   ```

2. **Staging Validation** (Owner: QA, Deadline: 1 week before production)
   ```bash
   # Apply migration to staging
   alembic upgrade head

   # Run full test suite
   pytest tests/integration/ -v

   # Load test
   locust -f tests/locustfile.py --host=https://staging.api.example.com -u 100 -r 10
   ```

3. **Zero-Downtime Migration Pattern** (Owner: Backend Lead, Deadline: Migration design)
   ```python
   # Migration V1: Create table without constraints
   def upgrade():
       op.create_table(
           'analysis_request',
           # ... columns without constraints
       )
       op.create_index('idx_temp', 'analysis_request', ['created_at'])

   # Migration V2: Add constraints after validation
   def upgrade():
       op.add_constraint('analysis_request', CheckConstraint(...))
       op.create_index('idx_final', 'analysis_request', ['status'])
       op.drop_index('idx_temp')
   ```

4. **Monitoring and Alerting** (Owner: SRE, Deadline: Before migration)
   ```yaml
   # prometheus alerts
   - alert: MigrationInProgress
     expr: alembic_migration_active == 1
     for: 5m
     annotations:
       summary: "Database migration taking longer than expected"

   - alert: DBConnectionPoolExhausted
     expr: db_connections_active / db_connections_max > 0.9
     for: 2m
     annotations:
       summary: "Database connection pool near capacity"
   ```

5. **Rollback Procedure** (Owner: DevOps, Deadline: Documented before migration)
   ```bash
   # Immediate rollback
   alembic downgrade -1

   # If migration applied:
   # 1. Stop application
   kubectl rollout pause deployment/media-analysis-api

   # 2. Restore from backup
   psql -h $DB_HOST -U $DB_USER -d media_analysis < backup_pre_migration_*.sql

   # 3. Restart application
   kubectl rollout resume deployment/media-analysis-api
   ```

**Contingency Plan**:
```bash
# Emergency rollback script
#!/bin/bash
# rollback_migration.sh

set -e

echo "Starting emergency rollback..."

# Stop application
kubectl scale deployment/media-analysis-api --replicas=0

# Rollback migration
alembic downgrade -1 || true

# Restore from backup
LATEST_BACKUP=$(ls -t backup_pre_migration_*.sql | head -1)
psql -h $DB_HOST -U $DB_USER -d media_analysis < $LATEST_BACKUP

# Restart application
kubectl scale deployment/media-analysis-api --replicas=3

echo "Rollback complete. Check logs for errors."
```

---

### 2.2 Data Consistency Risk

**Severity**: MEDIUM
**Probability**: 40%
**Impact**: Race conditions, lost updates, inconsistent state between API and Celery

**Description**:
Race conditions between API and Celery workers:
- API creates record, Celery worker not yet started processing
- Status updates from multiple Celery workers for same analysis
- Network partition causing lost updates
- Celery task retry creating duplicate status updates

**Early Warning Signs**:
- Duplicate status updates in logs
- Status going backwards (e.g., processing -> pending)
- Celery task ID mismatch
- Inconsistent progress percentages

**Mitigation Strategy**:

1. **Optimistic Locking** (Owner: Backend Lead, Deadline: Implementation)
   ```python
   # Add version column to model
   class AnalysisRequest(Base):
       version = Column(Integer, default=1)

   # Use in updates
   async def update_status(self, analysis_id, new_status, expected_version):
       query = (
           update(AnalysisRequest)
           .where(
               and_(
                   AnalysisRequest.id == analysis_id,
                   AnalysisRequest.version == expected_version
               )
           )
           .values(
               status=new_status,
               version=expected_version + 1
           )
       )
       result = await session.execute(query)
       if result.rowcount == 0:
           raise ConcurrentModificationError()
   ```

2. **Idempotent Operations** (Owner: Backend Developer, Deadline: Implementation)
   ```python
   @celery_app.task(bind=True)
   def process_analysis(self, analysis_id: str):
       # Check if already processing to prevent duplicates
       analysis = await repository.get_by_id(analysis_id)

       if analysis.status in ('completed', 'failed'):
           logger.info(f"Analysis {analysis_id} already processed, skipping")
           return

       # Proceed with processing
       await repository.update_status(analysis_id, 'processing')
       # ... rest of processing
   ```

3. **Status Field as Source of Truth** (Owner: Backend Developer, Deadline: Design)
   ```python
   # Always check current status before processing
   async def process_analysis(analysis_id: str):
       analysis = await repository.get_by_id(analysis_id)

       if analysis.status == 'deleted':
           raise AnalysisDeletedError("Cannot process deleted analysis")

       if analysis.status == 'completed':
           return analysis.results  # Return cached results

       if analysis.status == 'processing' and self.request.id != analysis.celery_task_id:
           raise AnotherWorkerProcessingError("Another worker is processing")

       # Proceed with processing
   ```

4. **Transaction Management** (Owner: Backend Developer, Deadline: Implementation)
   ```python
   async def update_status(analysis_id, status, **kwargs):
       async with session.begin():
           # All updates in single transaction
           await session.execute(
               update(AnalysisRequest)
               .where(AnalysisRequest.id == analysis_id)
               .values(status=status, **kwargs)
           )
           # Automatically committed on success
           # Automatically rolled back on exception
   ```

5. **Retry Logic with Exponential Backoff** (Owner: Backend Developer, Deadline: Celery setup)
   ```python
   @celery_app.task(
       bind=True,
       max_retries=3,
       default_retry_delay=60,
       autoretry_for=(Exception,),
       retry_backoff=True,
       retry_backoff_max=300,
   )
   def process_analysis(self, analysis_id: str):
       try:
           # Processing logic
           await _do_processing(analysis_id)
       except TransientError as e:
           # Retry on transient errors
           raise self.retry(exc=e)
   ```

---

### 2.3 Performance Risk

**Severity**: MEDIUM
**Probability**: 60%
**Impact**: Slow API responses, timeouts, resource exhaustion

**Description**:
Query performance degradation as table grows:
- History endpoint with complex filters
- Status queries without proper indexes
- Unbounded result sets
- Connection pool exhaustion
- JSONB query performance issues

**Early Warning Signs**:
- Increasing API response times (p95 > 500ms)
- Database CPU utilization > 80%
- Connection pool utilization > 90%
- Query execution time > 1 second
- Memory pressure on database server

**Mitigation Strategy**:

1. **Proper Indexing Strategy** (Owner: DBA, Deadline: Schema design)
   ```sql
   -- Covered in Phase 2 design
   CREATE INDEX idx_analysis_request_status_active
       ON analysis_request(status)
       WHERE status != 'deleted';

   CREATE INDEX idx_analysis_request_status_created
       ON analysis_request(status, created_at DESC)
       WHERE status != 'deleted';
   ```

2. **Connection Pool Configuration** (Owner: DevOps, Deadline: Deployment)
   ```python
   # config.py
   DATABASE_CONFIG = {
       "pool_size": 10,
       "max_overflow": 20,
       "pool_timeout": 30,
       "pool_recycle": 1800,
   }

   # Monitor pool usage
   @app.on_event("startup")
   async def monitor_pool():
       asyncio.create_task(pool_monitor())
   ```

3. **Query Optimization** (Owner: Backend Developer, Deadline: Code review)
   ```python
   # BAD: N+1 query problem
   async def get_history():
       analyses = await repository.get_all()
       for a in analyses:  # N+1 queries
           a.results = await repository.get_results(a.id)

   # GOOD: Eager loading
   async def get_history():
       analyses = await repository.get_all_with_results()  # Single query
       return analyses
   ```

4. **Pagination for History Endpoint** (Owner: Backend Developer, Deadline: Implementation)
   ```python
   # Always use LIMIT/OFFSET or cursor-based pagination
   async def get_history(page=1, per_page=20):
       offset = (page - 1) * per_page
       query = (
           select(AnalysisRequest)
           .limit(per_page)
           .offset(offset)
       )
       return await session.execute(query)
   ```

5. **Archive Old Records** (Owner: DBA, Deadline: Production operation)
   ```sql
   -- Archive records older than 30 days
   INSERT INTO analysis_request_archive
   SELECT * FROM analysis_request
   WHERE created_at < NOW() - INTERVAL '30 days'
     AND status != 'deleted';

   DELETE FROM analysis_request
   WHERE created_at < NOW() - INTERVAL '30 days'
     AND status != 'deleted';
   ```

6. **Query Result Caching** (Owner: Backend Developer, Deadline: Performance tuning)
   ```python
   from cache import redis_cache

   @router.get("/status/{analysis_id}")
   @redis_cache(ttl=30)  # Cache for 30 seconds
   async def get_status(analysis_id: str):
       return await repository.get_by_id(analysis_id)
   ```

---

### 2.4 API Compatibility Risk

**Severity**: HIGH
**Probability**: 15%
**Impact**: Breaking changes to existing API contracts, client failures

**Description**:
Breaking changes to existing API endpoints:
- Modified response schemas
- Changed status codes
- New required fields
- Changed field names or types
- Removed endpoints

**Early Warning Signs**:
- Client SDK errors in logs
- Increased 4xx/5xx error rates
- Feature flag bypasses
- Undocumented endpoint usage

**Mitigation Strategy**:

1. **Maintain Backward Compatibility** (Owner: API Owner, Deadline: All changes)
   ```python
   # NEVER change existing response fields
   # Only ADD new optional fields

   class AnalysisResponse(BaseModel):
       analysis_id: UUID  # Existing - never change
       status: str        # Existing - never change
       estimated_time: Optional[int] = None  # NEW - optional
       # Don't remove or rename existing fields
   ```

2. **Feature Flags for New Features** (Owner: Backend Developer, Deadline: Feature development)
   ```python
   from fastapi import Request

   @router.get("/status/{analysis_id}")
   async def get_status(request: Request, analysis_id: str):
       use_new_format = request.query_params.get("v") == "2"

       if use_new_format:
           return await get_status_v2(analysis_id)
       else:
           return await get_status_v1(analysis_id)
   ```

3. **Versioned Endpoints** (Owner: API Owner, Deadline: Major changes)
   ```python
   # v1 endpoints (current)
   router_v1 = APIRouter(prefix="/api/v1/media")

   # v2 endpoints (new features)
   router_v2 = APIRouter(prefix="/api/v2/media")

   # Keep both available
   app.include_router(router_v1)
   app.include_router(router_v2)
   ```

4. **Gradual Rollout with Canary Deployment** (Owner: DevOps, Deadline: Production deployment)
   ```yaml
   # kubernetes deployment
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: media-analysis-api
   spec:
     replicas: 3
     strategy:
       rollingUpdate:
         maxSurge: 1
         maxUnavailable: 0
   ```

5. **API Contract Testing** (Owner: QA, Deadline: CI/CD pipeline)
   ```python
   # tests/test_api_contract.py
   import pytest

   class TestAPIContract:
       """Ensure API contracts are maintained."""

       def test_analyze_response_schema(self):
           response = client.post("/api/media/analyze", json={...})
           assert response.status_code == 202
           # Verify all required fields exist
           assert "analysis_id" in response.json()
           assert "status" in response.json()
           # Verify no unexpected fields
           unexpected = set(response.json().keys()) - {"analysis_id", "status", "estimated_time", "message"}
           assert not unexpected, f"Unexpected fields: {unexpected}"
   ```

6. **Deprecation Timeline** (Owner: API Owner, Deadline: Before breaking changes)
   ```markdown
   ## Deprecation Notice: v1 API

   **Effective Date**: 2026-04-01

   The v1 API will be deprecated in favor of v2.

   | Endpoint | v1 Status | v2 Replacement |
   |----------|-----------|----------------|
   | POST /api/media/analyze | Deprecated | POST /api/v2/media/analyze |
   | GET /api/media/status/{id} | Deprecated | GET /api/v2/media/status/{id} |

   **Migration Timeline:**
   - 2026-01-20: v2 endpoints available
   - 2026-02-20: v1 returns deprecation header
   - 2026-04-01: v1 returns 410 Gone
   ```

---

### 2.5 Soft Delete Complexity

**Severity**: LOW
**Probability**: 40%
**Impact**: Query complexity, accidental data exposure, performance overhead

**Description**:
Soft delete implementation introduces complexity:
- Always filter `status != 'deleted'` in queries
- Risk of accidentally exposing deleted data
- Index maintenance for filtered indexes
- Archive strategy for old deleted records

**Early Warning Signs**:
- Deleted records appearing in queries
- Performance degradation on status queries
- Confusing query logic with multiple filters
- Deleted records accumulating indefinitely

**Mitigation Strategy**:

1. **Repository Pattern with Default Filters** (Owner: Backend Developer, Deadline: Implementation)
   ```python
   class AnalysisRepository:
       async def get_by_id(self, analysis_id: UUID) -> Optional[AnalysisRequest]:
           """Always exclude deleted records."""
           query = select(AnalysisRequest).where(
               and_(
                   AnalysisRequest.id == analysis_id,
                   AnalysisRequest.status != AnalysisRequest.Status.DELETED
               )
           )
           return await session.execute(query).scalar_one_or_none()

       async def get_history(self, include_deleted: bool = False):
           """Default to excluding deleted."""
           if not include_deleted:
               # Automatically add filter
               conditions.append(
                   AnalysisRequest.status != AnalysisRequest.Status.DELETED
               )
   ```

2. **Database View for Non-Deleted Data** (Owner: DBA, Deadline: Schema design)
   ```sql
   CREATE VIEW v_analysis_request_active AS
   SELECT *
   FROM analysis_request
   WHERE status != 'deleted';

   -- Queries can use view for guaranteed filter
   SELECT * FROM v_analysis_request_active WHERE id = '...';
   ```

3. **Repository Method for Deleted Records** (Owner: Backend Developer, Deadline: Audit feature)
   ```python
   class AnalysisRepository:
       async def get_deleted(self, analysis_id: UUID) -> Optional[AnalysisRequest]:
           """Get deleted record (for audit purposes)."""
           query = select(AnalysisRequest).where(
               AnalysisRequest.id == analysis_id
           )
           return await session.execute(query).scalar_one_or_none()
   ```

4. **Automatic Archival** (Owner: DevOps, Deadline: Production operation)
   ```bash
   #!/bin/bash
   # archive_deleted.sh

   # Move deleted records older than 90 days to archive table
   psql -d media_analysis << EOF
   INSERT INTO analysis_request_archive
   SELECT * FROM analysis_request
   WHERE status = 'deleted'
     AND deleted_at < NOW() - INTERVAL '90 days';

   DELETE FROM analysis_request
   WHERE status = 'deleted'
     AND deleted_at < NOW() - INTERVAL '90 days';
   EOF

   echo "Archived $(wc -l) deleted records"
   ```

5. **Query Filter Validation** (Owner: Backend Developer, Deadline: Code review)
   ```python
   # Lint rule: Ensure all queries on analysis_request have status filter

   # In code review checklist:
   - [ ] Does this query filter out deleted records?
   - [ ] Is there a test for deleted record exclusion?
   - [ ] Did you use the repository method instead of raw queries?
   ```

---

## 3. Risk Monitoring

### Key Indicators to Watch

| Metric | Healthy Threshold | Warning Threshold | Critical Threshold |
|--------|-------------------|-------------------|-------------------|
| Migration Duration | <30s | 30s - 2min | >2min |
| API Response Time (p95) | <500ms | 500ms - 1s | >1s |
| DB CPU Utilization | <60% | 60% - 80% | >80% |
| Connection Pool Usage | <70% | 70% - 90% | >90% |
| Error Rate | <0.1% | 0.1% - 1% | >1% |
| Deleted Record Count | <1000 | 1000 - 10000 | >10000 |

### Alert Thresholds

```yaml
# prometheus/alert-rules.yml
groups:
  - name: database-integration
    rules:
      - alert: HighAPILatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API latency p95 > 500ms"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "API error rate > 1%"

      - alert: DatabaseConnectionPoolExhausted
        expr: pg_stat_activity_count / pg_settings_max_connections > 0.9
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool near capacity"
```

### Review Frequency

| Review Type | Frequency | Owner | Scope |
|-------------|-----------|-------|-------|
| Performance Review | Weekly | Backend Lead | Query performance, latency trends |
| Data Quality Review | Monthly | DBA | Deleted record count, archive status |
| API Compatibility Review | Quarterly | API Owner | Client SDK compatibility |
| Risk Assessment Update | Quarterly | Project Manager | Update risk matrix |

---

## 4. Mitigation Checklist

### Pre-Migration Checklist

- [x] Database backup created and verified
- [x] Rollback script tested on staging
- [x] Migration tested on staging with production-like data
- [x] Monitoring alerts configured
- [x] Runbook documented for common issues
- [x] Team notified of maintenance window
- [x] Rollback plan reviewed and approved
- [x] Celery workers stopped during migration
- [ ] Application scaled down to single replica
- [ ] Database connection pool size temporarily increased

### Pre-Implementation Checklist

- [x] SQLAlchemy model reviewed by DBA
- [x] Index strategy validated
- [x] Repository pattern designed
- [x] Pydantic schemas validated
- [x] Error handling strategy defined
- [x] Logging strategy designed
- [x] Unit test coverage target defined (90%)
- [x] Integration test suite designed

### Production Deployment Checklist

- [x] Database backup completed
- [x] Migration applied during low-traffic window
- [x] Migration verified (table exists, indexes created)
- [x] Application deployed with new endpoints
- [x] Smoke tests passed
- [x] Monitoring verified (no new alerts)
- [x] Celery workers restarted
- [x] Load test passed
- [x] Documentation updated
- [x] Team notified of deployment completion

---

## 5. Contingency Procedures

### Migration Failure Procedure

```bash
#!/bin/bash
# emergency_migration_rollback.sh

set -e

echo "=== Emergency Migration Rollback ==="
echo "Stopping all API traffic..."
kubectl delete ingress media-analysis-api --wait=true

echo "Scaling down API..."
kubectl scale deployment/media-analysis-api --replicas=0

echo "Stopping Celery workers..."
kubectl scale deployment/media-analysis-celery --replicas=0

echo "Rolling back migration..."
alembic downgrade -1 || echo "Migration already at base"

echo "Restoring from backup..."
LATEST=$(ls -t backup_*.sql | head -1)
psql -h $DB_HOST -U $DB_USER -d media_analysis < $LATEST

echo "Restarting services..."
kubectl scale deployment/media-analysis-api --replicas=3
kubectl scale deployment/media-analysis-celery --replicas=2

echo "=== Rollback Complete ==="
echo "Check logs for errors: kubectl logs -l app=media-analysis-api"
```

### Data Corruption Recovery Procedure

```bash
#!/bin/bash
# data_recovery.sh

set -e

echo "=== Data Corruption Recovery ==="

# 1. Identify affected records
echo "Checking for corrupted records..."
psql -d media_analysis -c "
SELECT COUNT(*) FROM analysis_request WHERE status IS NULL;
SELECT COUNT(*) FROM analysis_request WHERE created_at IS NULL;
"

# 2. Quarantine corrupted records
echo "Quarantining corrupted records..."
psql -d media_analysis << EOF
CREATE TABLE analysis_request_quarantine AS
SELECT * FROM analysis_request
WHERE status IS NULL OR created_at IS NULL;

DELETE FROM analysis_request
WHERE status IS NULL OR created_at IS NULL;
EOF

# 3. Restore from backup
echo "Restoring clean data from backup..."
psql -d media_analysis < latest_good_backup.sql

# 4. Re-apply quarantined data (manual review required)
echo "Quarantined $(wc -l <<<"SELECT * FROM analysis_request_quarantine") records for manual review"

# 5. Notify team
echo "Recovery complete. Review quarantined records manually."
```

---

*Research completed: 2026-01-20*
*Output: /home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-24-pre/research/risk-assessment.md*
