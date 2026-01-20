# Phase Cross-References and Dependencies

## Phase Dependency Mapping

| Phase | Depends On | Parallel With | Blocks | Critical Path |
|-------|------------|---------------|--------|---------------|
| Phase 1: Source Analysis | - | - | Phases 2-8 | YES (Foundation) |
| Phase 2: Scaffold Structure | Phase 1 | - | Phases 3-4, 6-7 | YES (Foundation) |
| Phase 3: Code Renaming | Phase 2 | - | Phase 5 | YES (Core Work) |
| Phase 4: Network Config | Phase 2 | - | Phase 7 | NO |
| Phase 5: Aggregator | Phase 3 | - | Phase 8 | YES (Core Work) |
| Phase 6: MiniMax Integration | Phase 2 | - | Phase 8 | NO |
| Phase 7: Caddyfile | Phase 4 | - | Phase 8 | NO |
| Phase 8: Testing | Phases 3, 5, 6, 7 | - | - | YES (End State) |

## Cross-References by Phase

### Phase 1 → Phase 3: File List
- **Input**: Source inventory from Phase 1
- **Used In**: Phase 3.1 (File copy commands)
- **Reference**: Lines 191-205 (PRD)
- **File**: `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-api-source-inventory.md`

### Phase 1 → Phase 2: Directory Structure
- **Input**: Source file list and counts
- **Used In**: Phase 2.2 (Target directory structure)
- **Reference**: Lines 292-312 (PRD)
- **Pattern**: Mirror source structure with renamed paths

### Phase 2 → Phase 4: Docker Configuration
- **Input**: Empty docker/ directory created
- **Used In**: Phase 4.1-4.3 (Docker Compose, Dockerfile, .env)
- **Reference**: Lines 497-651 (PRD)
- **Files**: docker/docker-compose.yml, docker/Dockerfile, config/.env

### Phase 3 → Phase 5: Endpoint Patterns
- **Input**: Renamed endpoints in media_analysis_api.py
- **Used In**: Phase 5.1-5.3 (Aggregator router registration)
- **Reference**: Lines 685-805 (PRD)
- **File**: api/media_analysis_api.py

### Phase 4 → Phase 7: Network Configuration
- **Input**: media-services-network created in docker-compose.yml
- **Used In**: Phase 7.1 (Caddyfile reverse_proxy)
- **Reference**: Lines 1129-1159 (PRD)
- **File**: Caddyfile

### Phase 6 → Phase 5: MiniMax Integration
- **Input**: minimax_client.py and minimax_integration.py
- **Used In**: Phase 5.2 (Aggregator uses MiniMax for vision)
- **Reference**: Lines 941-1039 (PRD)
- **File**: api/minimax_integration.py

### Phase 6 → Phase 8: MiniMax Testing
- **Input**: MiniMax client and integration modules
- **Used In**: Phase 8.4 (MiniMax integration test)
- **Reference**: Lines 1241-1265 (PRD)
- **Test**: test-minimax.sh script

### Phase 7 → Phase 8: Caddyfile Testing
- **Input**: Validated Caddyfile
- **Used In**: Phase 8.1-8.2 (Service startup)
- **Reference**: Lines 1163-1168 (PRD)
- **Test**: validate-caddyfile.sh script

## Quick Reference Links

### Architecture
- [Before Architecture](#current-architecture-before) - Lines 74-101
- [After Architecture](#target-architecture-after) - Lines 113-147
- [Network Isolation](#network-isolation-detail) - Enhanced section

### Endpoint Mapping
- [Complete Endpoint Table](#complete-endpoint-migration-table) - Lines 1657-1665
- [Aggregator Request Format](#aggregator-request-format) - Lines 1706-1717
- [Aggregator Response Format](#aggregator-response-format) - Lines 1722-1736

### Code Patterns
- [CotizadorAPI → MediaAnalysisAPI](#phase-3-surgical-code-renaming) - Lines 363-383
- [Endpoint Renaming](#phase-3-2-endpoint-renaming) - Lines 385-400
- [Environment Variables](#phase-3-3-environment-variable-renaming) - Lines 402-414

### Configuration
- [Docker Compose](#phase-4-1-create-docker-compose-file) - Lines 497-526
- [Dockerfile](#phase-4-2-create-dockerfile) - Lines 572-613
- [Caddyfile](#phase-7-1-design-caddyfile-structure) - Lines 1069-1123

### Verification
- [Quick Verification Script](#quick-verification-script) - Lines 1745-1775
- [Safety Checklist](#safety-checklist-1) - Lines 1503-1519
- [Risk Assessment](#risk-assessment--mitigation) - Lines 1424-1468

### File:Line Targets
- cotizador_api.py main file: Line 191
- Class definitions: Line 222
- Function definitions: Line 228
- Route decorators: Line 234
- Docker Compose: Line 240
- Environment variables: Line 246

## Dependency Graph (Text)

```
START
  │
  ├─ Phase 1 (1-2 hrs)
  │     │
  │     └─ Produces: source-inventory.md
  │            │
  ├─ Phase 2 (30 min)
  │     │ Requires: source-inventory.md
  │     │
  │     ├─ Creates: /opt/services/media-analysis/ structure
  │     ├─ Creates: api/__init__.py
  │     ├─ Creates: config/requirements.txt
  │     │
  │     └─ Produces: Empty directory structure
  │            │
  ├─ Phase 3 (4-6 hrs)
  │     │ Requires: Directory structure
  │     │
  │     ├─ Copies and renames: cotizador_api.py → media_analysis_api.py
  │     ├─ Copies and renames: cotizador.py → media_analysis.py
  │     ├─ Updates: All endpoint decorators
  │     └─ Produces: Fully renamed codebase
  │            │
  ├─ Phase 4 (1-2 hrs)
  │     │ Requires: Empty directory structure
  │     │
  │     ├─ Creates: docker-compose.yml with media-services-network
  │     ├─ Creates: Dockerfile
  │     ├─ Creates: .env with MEDIA_ANALYSIS_ prefix
  │     └─ Produces: Docker configuration
  │            │
  ├─ Phase 5 (3-4 hrs)
  │     │ Requires: Fully renamed codebase
  │     │
  │     ├─ Implements: POST /api/media/analyze endpoint
  │     ├─ Implements: Aggregator router
  │     └─ Produces: Natural language aggregator
  │            │
  ├─ Phase 6 (2-3 hrs)
  │     │ Requires: Empty directory structure
  │     │
  │     ├─ Creates: minimax_client.py
  │     ├─ Creates: minimax_integration.py
  │     └─ Produces: MiniMax API client with fallback
  │            │
  ├─ Phase 7 (1-2 hrs)
  │     │ Requires: Docker configuration
  │     │
  │     ├─ Creates: Caddyfile
  │     └─ Produces: Routing configuration
  │            │
  └─ Phase 8 (2-4 hrs)
        │ Requires: All previous phases complete
        │
        ├─ Builds: Docker image
        ├─ Starts: Containers
        ├─ Tests: All endpoints
        └─ Produces: Production-ready service

END
```

## Bead Task References

| Bead ID | Phase | Task | Status | Dependency |
|---------|-------|------|--------|------------|
| ma-01 | 1 | Read cotizador-api structure | pending | none |
| ma-02 | 1 | Read contact sheet scripts | pending | ma-01 |
| ma-03 | 1 | Create PRD | pending | ma-01, ma-02 |
| ma-04 | 2 | Clone service | pending | ma-03 |
| ma-05 | 3 | Rename endpoints | pending | ma-04 |
| ma-06 | 5 | Add aggregator | pending | ma-05 |
| ma-07 | 3 | Add video branch | pending | ma-05 |
| ma-08 | 3 | Add audio branch | pending | ma-05 |
| ma-09 | 3 | Add document branch | pending | ma-05 |
| ma-10 | 6 | Integrate MiniMax | pending | ma-04 |
| ma-11 | 7 | Create Caddyfile | pending | ma-04 |
| ma-12 | 8 | Deploy and test | pending | ma-05, ma-06, ma-10, ma-11 |

## Parallel Execution Map

### Phase 1 (Can Run in Parallel)
- ma-01: SSH and catalog files
- ma-02: Read contact sheet scripts
- Result: Both produce input for ma-03

### Phase 3 (Can Run in Parallel)
- ma-05: Rename endpoints
- ma-07: Video branch
- ma-08: Audio branch
- ma-09: Document branch
- Result: All update different sections of codebase

### Phase 8 (Can Run in Parallel)
- ma-12-t3: Test branch endpoints
- ma-12-t4: Test aggregator endpoint
- ma-12-t5: Test MiniMax integration
- ma-12-t6: Security scan
- Result: All tests can run concurrently

## Key Blocker Conditions

| Blocker | Phase | Condition | Waived By |
|---------|-------|-----------|-----------|
| Source inventory | 2 | Phase 1 output exists | Phase 1 completion |
| Directory structure | 3 | Phase 2 output exists | Phase 2 completion |
| Renamed codebase | 5 | Phase 3 output exists | Phase 3 completion |
| Docker config | 7 | Phase 4 output exists | Phase 4 completion |
| All code ready | 8 | Phases 3, 5, 6, 7 complete | All phase leads |
