# Media Analysis API - Final Implementation Roadmap

**Generated:** 2026-01-20
**Session:** Full Auto Parallel Planning (MAO)
**Total Tasks:** 8 PRDs → 32 Beads (4 phases x 8 PRDs)

---

## Executive Summary

All 8 plan00 → plan04 planning cycles have been completed in parallel using MAO (Multi-Agent Orchestrator). This document provides the complete implementation roadmap with dependencies, execution order, and verification procedures.

### Planning Statistics

| Metric | Value |
|--------|-------|
| **Plan00 PRDs Generated** | 8 |
| **Plan04 Implementation Plans** | 8 |
| **Total Beads Created** | 32 |
| **Execution Time** | ~90 minutes |
| **Parallelization** | 8x plan00 → 8x plan04 |

---

## Task Dependencies

### Dependency Graph

```
                    ┌─────────────────────────────────────────┐
                    │     EPIC: PostgreSQL + File System      │
                    │           runpod-ma-epic-01             │
                    └─────────────────┬───────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│   ma-21: Schema     │   │   ma-23: Storage    │   │   ma-25: Docker     │
│   (P1)              │   │   (P1)              │   │   (P2)              │
│                     │   │                     │   │                     │
│ Creates:            │   │ Creates:            │   │ Updates:            │
│ - jobs table        │   │ - uploads/          │   │ - docker-compose    │
│ - media_assets      │   │ - frames/           │   │ - af-network        │
│ - transcriptions    │   │ - contact-sheets/   │   │ - health checks     │
│ - analysis_results  │   │ - outputs/          │   │                     │
└──────────┬──────────┘   │ - temp/             │   └──────────┬──────────┘
           │              └─────────────────────┘              │
           │                                                    │
           ▼                                                    │
┌─────────────────────┐                           ┌────────────▼──────────┐
│   ma-22: Models     │                           │   ma-24: Integration  │
│   (P1)              │                           │   (P2)                │
│                     │                           │                       │
│ Creates:            │                           │ Updates:              │
│ - SQLAlchemy models │                           │ - /api/media/analyze  │
│ - asyncpg pool      │                           │ - /api/media/status   │
│ - Pydantic schemas  │                           │ - /api/media/history  │
│ - Repository layer  │                           │ - /api/media/{id}     │
└──────────┬──────────┘                           └───────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SUBSEQUENT TASKS (Independent)                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│   ma-26: Test       │   │   ma-27: Research   │   │   ma-28: Caddyfile  │
│   (P1)              │   │   (P1)              │   │   (P1)              │
│                     │   │                     │   │                     │
│ Creates:            │   │ Researches:         │   │ Creates:            │
│ - Vision test       │   │ - MiniMax MCP       │   │ - Caddyfile         │
│ - Fallback chain    │   │ - understand_image  │   │ - Reverse proxy     │
│ - Provider tests    │   │ - Integration path  │   │ - TLS configuration │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
```

---

## Implementation Order

### Wave 1: Foundation (Can Execute in Parallel)

| Bead ID | Task | Phase | Description | Est. Time |
|---------|------|-------|-------------|-----------|
| ma-21-p1 | ma-21 | 1 | Create Database Schema | ~5 min |
| ma-23-p1 | ma-23 | 1 | Create Storage Directory Structure | ~3 min |
| ma-25-p1 | ma-25 | 1 | Update Docker Compose | ~2 min |

### Wave 2: Database Integration (After Wave 1)

| Bead ID | Task | Phase | Description | Est. Time | Blocked By |
|---------|------|-------|-------------|-----------|------------|
| ma-22-p1 | ma-22 | 1 | Create Database Connection Pool | ~5 min | ma-21-p1 |
| ma-22-p2 | ma-22 | 2 | Define SQLAlchemy Models | ~10 min | ma-22-p1 |
| ma-21-p2 | ma-21 | 2 | Create Migration Script | ~5 min | ma-21-p1 |
| ma-24-p1 | ma-24 | 1 | Update API Endpoints | ~15 min | ma-22-p2, ma-21-p2 |

### Wave 3: Storage & Testing (After Wave 2)

| Bead ID | Task | Phase | Description | Est. Time | Blocked By |
|---------|------|-------|-------------|-----------|------------|
| ma-23-p2 | ma-23 | 2 | Implement Storage Manager | ~10 min | ma-23-p1 |
| ma-25-p2 | ma-25 | 2 | Configure Environment | ~3 min | ma-25-p1 |
| ma-26-p1 | ma-26 | 1 | Create Test Framework | ~5 min | - |
| ma-26-p2 | ma-26 | 2 | Implement Fallback Chain | ~10 min | ma-26-p1 |

### Wave 4: Research & Configuration (Independent)

| Bead ID | Task | Phase | Description | Est. Time | Blocked By |
|---------|------|-------|-------------|-----------|------------|
| ma-27-p1 | ma-27 | 1 | Research MiniMax MCP | ~15 min | - |
| ma-28-p1 | ma-28 | 1 | Create Caddyfile | ~5 min | - |

### Wave 5: Final Integration & Testing (After Waves 2-4)

| Bead ID | Task | Phase | Description | Est. Time | Blocked By |
|---------|------|-------|-------------|-----------|------------|
| ma-24-p2 | ma-24 | 2 | Add Service Layer | ~10 min | ma-24-p1 |
| ma-23-p3 | ma-23 | 3 | Integrate with API | ~10 min | ma-23-p2 |
| ma-25-p3 | ma-25 | 3 | Add Health Checks | ~5 min | ma-25-p2 |
| ma-26-p3 | ma-26 | 3 | Provider Implementations | ~15 min | ma-26-p2 |

### Wave 6: Verification & Deployment

| Bead ID | Task | Phase | Description | Est. Time | Blocked By |
|---------|------|-------|-------------|-----------|------------|
| ma-21-p3 | ma-21 | 3 | Run Migrations | ~5 min | ma-21-p2 |
| ma-22-p3 | ma-22 | 3 | Test Connection | ~3 min | ma-22-p2 |
| ma-23-p4 | ma-23 | 4 | Storage Testing | ~5 min | ma-23-p3 |
| ma-24-p3 | ma-24 | 4 | Integration Testing | ~10 min | ma-24-p2 |
| ma-25-p4 | ma-25 | 4 | Docker Testing | ~5 min | ma-25-p3 |
| ma-26-p4 | ma-26 | 4 | Full Test Suite | ~10 min | ma-26-p3 |
| ma-27-p2 | ma-27 | 2 | Document Integration | ~10 min | ma-27-p1 |
| ma-28-p2 | ma-28 | 2 | Deploy Caddyfile | ~5 min | ma-28-p1 |

---

## Plan04 Document Locations

| Task | Plan04 Path | Beads |
|------|-------------|-------|
| ma-21 | `/dev/agents/artifacts/doc/plan/ma-21-impl/ma-21-plan04.md` | 4 |
| ma-22 | `/dev/agents/artifacts/doc/plan/ma-22-impl/ma-22-plan04.md` | 4 |
| ma-23 | `/dev/agents/artifacts/doc/plan/ma-23-impl/ma-23-plan04.md` | 4 |
| ma-24 | `/dev/agents/artifacts/doc/plan/ma-24-impl/ma-24-plan04.md` | 4 |
| ma-25 | `/dev/agents/artifacts/doc/plan/ma-25-impl/ma-25-plan04.md` | 4 |
| ma-26 | `/dev/agents/artifacts/doc/plan/ma-26-impl/ma-26-plan04.md` | 4 |
| ma-27 | `/dev/agents/artifacts/doc/plan/ma-27-impl/ma-27-plan04.md` | 4 |
| ma-28 | `/dev/agents/artifacts/doc/plan/ma-28-impl/ma-28-plan04.md` | 4 |

---

## Quick Start Commands

### Execute All Implementations

```bash
# Phase 1: Foundation (Parallel)
echo "=== Wave 1: Foundation ===" &
(echo "ma-21-p1" | bd update --status in_progress) &
(echo "ma-23-p1" | bd update --status in_progress) &
(echo "ma-25-p1" | bd update --status in_progress) &
wait

# Phase 2: Database Integration (Sequential with dependencies)
echo "=== Wave 2: Database ===" &
# ... continue with each bead
```

### Quick Test (After All Implementations)

```bash
# Test database connection
ssh devmaster 'curl -s http://localhost:8050/health | jq .'

# Test API endpoints
ssh devmaster 'for ep in health api/media/video api/media/audio api/media/documents api/media/analyze; do echo -n "$ep: "; curl -s -o /dev/null -w "%{http_code}" "http://localhost:8050/$ep"; done'

# Verify storage directories
ssh devmaster 'ls -la /opt/services/media-analysis/storage/'
```

---

## Rollback Procedures

### Emergency Rollback (All Tasks)

```bash
# Rollback database
ssh devmaster 'psql -h af-postgres-1 -U n8n -d af-memory -c "DROP TABLE IF EXISTS analysis_results, transcriptions, media_assets, jobs CASCADE;"'

# Rollback Docker
ssh devmaster 'cd /opt/services/media-analysis && git checkout docker-compose.yml && docker compose restart'

# Rollback Caddy
ssh devmaster 'caddy reload --config /opt/clients/af/Caddyfile.d/backup.caddyfile'
```

### Selective Rollback (Single Task)

See individual plan04 documents for task-specific rollback procedures.

---

## Success Criteria

### Functional Requirements

- [ ] Database schema created with all 4 tables
- [ ] API endpoints integrated with database
- [ ] File storage organized with cleanup policies
- [ ] Docker container healthy (af-network connected)
- [ ] Vision fallback chain tested
- [ ] Caddyfile deployed for external access

### Technical Requirements

- [ ] All 32 beads completed
- [ ] Zero LSP errors in modified files
- [ ] All tests passing
- [ ] Health check returns "healthy"
- [ ] R2 sync functional

---

## Next Steps

1. **Review** all plan04 documents in `/dev/agents/artifacts/doc/plan/*-impl/`
2. **Execute** `/implement` with all 8 PRDs
3. **Monitor** bead status via `bd ready`
4. **Verify** using quick test commands
5. **Document** any issues in beads

---

**Document Version:** 1.0
**Generated:** 2026-01-20 06:30:00 UTC-6
**Method:** MAO Parallel Planning (8x plan00 → 8x plan04)
