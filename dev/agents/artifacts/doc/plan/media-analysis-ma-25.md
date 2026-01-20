# Media Analysis API - Docker Compose Network Update PRD

**Task ID:** runpod-ma-25
**Created:** 2026-01-20 05:08:00 UTC-6
**Author:** Claude Code PRD Generator (MiniMax + Opus UltraThink)
**Status:** Final PRD

---

## 1. Executive Summary

### Problem Statement
The `media-analysis-api` container on devmaster reports "unhealthy" status despite the API responding correctly on port 8050. The root cause is DNS resolution failure for the PostgreSQL hostname `af-postgres-1` which resides on the external Docker network `af-network`.

### Solution
Update the service's `docker-compose.yml` to connect to the pre-existing `af-network` external network, enabling DNS resolution for PostgreSQL and other AF services.

### Expected Outcome
- Container health check passes (healthy status)
- PostgreSQL connectivity established for database operations
- Container can communicate with other AF services (n8n, cotizador-api, etc.)
- Foundation laid for runpod-ma-21 through runpod-ma-24 database integration

---

## 2. System Architecture

### Current Architecture (Broken)

```
┌─────────────────────────────────────────────────────────────────┐
│                     devmaster VPS                                │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           media-analysis-api Container                   │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │              FastAPI Application                 │    │    │
│  │  │  - /health endpoint (returns OK)                │    │    │
│  │  │  - /api/media/* endpoints                       │    │    │
│  │  │  - Prompt router with fallback chains           │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  │                                                          │    │
│  │  NETWORKS:                                               │    │
│  │  - media-analysis_default (bridge)                       │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                           │                           │
│         ✗ (DNS FAIL)               │                           │
│         ▼                           │                           │
│  ┌──────────────────────────────────┴──────────────────────┐   │
│  │           af-network (EXTERNAL)                          │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌───────────┐  │   │
│  │  │ af-postgres-1  │  │ n8n-container  │  │  cotizador │  │   │
│  │  │ :5432          │  │ :5678          │  │ :8000      │  │   │
│  │  └────────────────┘  └────────────────┘  └───────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Target Architecture (Fixed)

```
┌─────────────────────────────────────────────────────────────────┐
│                     devmaster VPS                                │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           media-analysis-api Container                   │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │              FastAPI Application                 │    │    │
│  │  │  - /health endpoint                             │    │    │
│  │  │  - /api/media/* endpoints                       │    │    │
│  │  │  - Prompt router with fallback chains           │    │    │
│  │  │  - Database layer (future ma-22)                │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  │                                                          │    │
│  │  NETWORKS:                                               │    │
│  │  - af-network (EXTERNAL) ◄── NEW CONNECTION             │    │
│  │    └── Can resolve: af-postgres-1, n8n, cotizador       │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                                                   │
│         ✓ (DNS SUCCESS)                                      │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           af-network (EXTERNAL)                          │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌───────────┐  │   │
│  │  │ af-postgres-1  │  │ n8n-container  │  │  cotizador │  │   │
│  │  │ :5432          │  │ :5678          │  │ :8000      │  │   │
│  │  └────────────────┘  └────────────────┘  └───────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Network Topology Details

| Network | Type | Connected Services | Purpose |
|---------|------|-------------------|---------|
| af-network | external bridge | af-postgres-1, n8n, cotizador-api, media-analysis (after fix) | Primary service interconnect |
| media-analysis_default | default bridge | media-analysis-api only | Current (isolated) |

---

## 3. Root Cause Analysis

### Issue: Container Unhealthy Status

**Symptoms:**
- `docker ps` shows `unhealthy` status
- API endpoints respond correctly (200 OK)
- Health check endpoint `/health` returns `{"status": "ok"}`

**Root Cause:**
```
1. Container starts with default bridge network (media-analysis_default)
2. Health check script attempts DNS resolution of 'af-postgres-1'
3. 'af-postgres-1' exists only on af-network (external)
4. DNS query fails: "Could not resolve hostname af-postgres-1"
5. Health check script reports failure
6. Docker marks container as unhealthy
```

**Affected Component:**
- File: `/opt/services/media-analysis/docker-compose.yml` (current)
- Missing: External network configuration

**Connection Details:**
| Property | Value |
|----------|-------|
| PostgreSQL Host | af-postgres-1 |
| PostgreSQL Port | 5432 |
| Database | af-memory |
| User | n8n |
| Required Network | af-network (external) |

---

## 4. Implementation Plan

### Phase 1: Backup Current Configuration

**Objective:** Preserve current docker-compose.yml before modification

**Actions:**
1. SSH to devmaster
2. Navigate to service directory
3. Create timestamped backup

**Commands:**
```bash
# SSH to devmaster
ssh devmaster

# Navigate to service directory
cd /opt/services/media-analysis

# Create backup with timestamp
cp docker-compose.yml docker-compose.yml.backup-$(date +%Y%m%d-%H%M%S)

# Verify backup created
ls -la docker-compose.yml.backup-*
```

**Verification:**
```bash
# Check backup exists
test -f docker-compose.yml.backup-* && echo "Backup created successfully" || echo "Backup FAILED"

# Compare sizes (should be identical)
wc -l docker-compose.yml docker-compose.yml.backup-*
```

**Expected Output:**
```
Backup created successfully
docker-compose.yml: [N] lines
docker-compose.yml.backup-[TIMESTAMP]: [N] lines
```

**Risk Level:** LOW - Read-only copy operation

---

### Phase 2: Examine Current docker-compose.yml

**Objective:** Understand current structure before modification

**Actions:**
1. Read current docker-compose.yml
2. Identify existing network configuration
3. Note service definitions and dependencies

**Commands:**
```bash
# Display full docker-compose.yml
cat /opt/services/media-analysis/docker-compose.yml

# Show structure (YAML parse)
python3 -c "import yaml; data = yaml.safe_load(open('/opt/services/media-analysis/docker-compose.yml')); print('Services:', list(data.get('services', {}).keys())); print('Networks:', list(data.get('networks', {}).keys()) if 'networks' in data else 'None defined')"
```

**Verification:**
```bash
# Check if networks section exists
grep -q 'networks:' /opt/services/media-analysis/docker-compose.yml && echo "Networks section exists" || echo "No networks section"

# Check current network configuration
grep -A 5 'networks:' /opt/services/media-analysis/docker-compose.yml 2>/dev/null || echo "No network configuration"
```

**Expected Findings:**
- `networks:` section may not exist
- `services:` contains `media-analysis-api` definition
- No external network references

**Risk Level:** LOW - Read-only inspection

---

### Phase 3: Update docker-compose.yml with Network Configuration

**Objective:** Add external af-network configuration

**Target File:** `/opt/services/media-analysis/docker-compose.yml`

**Current State (expected):**
```yaml
version: '3.8'

services:
  media-analysis-api:
    image: ...
    ports:
      - "8050:8050"
    environment:
      - ...
    restart: unless-stopped
```

**Modified State (target):**
```yaml
version: '3.8'

services:
  media-analysis-api:
    image: ...
    networks:
      - default
    ports:
      - "8050:8050"
    environment:
      - ...
    restart: unless-stopped

networks:
  default:
    name: af-network
    external: true
```

**Implementation Steps:**

**Option A: Prepend Networks Section (if no networks defined)**

```bash
# Create temporary file with network configuration
cat > /tmp/network_patch.yaml << 'EOF'

networks:
  default:
    name: af-network
    external: true
EOF

# Insert at end of file
cat /tmp/network_patch.yaml >> /opt/services/media-analysis/docker-compose.yml
```

**Option B: Full File Replacement (if networks section exists)**

```bash
# Read existing content, identify insertion point
python3 << 'PYEOF'
import yaml

with open('/opt/services/media-analysis/docker-compose.yml', 'r') as f:
    data = yaml.safe_load(f)

# Ensure networks section exists
if 'networks' not in data:
    data['networks'] = {}

# Configure default network as external af-network
data['networks']['default'] = {
    'name': 'af-network',
    'external': True
}

# Write updated configuration
with open('/opt/services/media-analysis/docker-compose.yml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print("Configuration updated successfully")
PYEOF
```

**Verification:**
```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('/opt/services/media-analysis/docker-compose.yml'))" && echo "YAML syntax valid"

# Verify network configuration present
grep -A 3 'networks:' /opt/services/media-analysis/docker-compose.yml

# Confirm external network reference
grep 'external: true' /opt/services/media-analysis/docker-compose.yml
```

**Expected Output:**
```
YAML syntax valid
networks:
  default:
    name: af-network
    external: true
external: true
```

**Risk Level:** MEDIUM - File modification with rollback plan

---

### Phase 4: Validate Docker Compose Configuration

**Objective:** Ensure configuration is syntactically correct and functional

**Commands:**
```bash
cd /opt/services/media-analysis

# Validate configuration (dry-run)
docker compose config

# Check for warnings
docker compose config 2>&1 | grep -i warning || echo "No warnings"

# Verify external network detected
docker compose config 2>&1 | grep -A 2 'networks:' || echo "Network configuration not visible in config output"
```

**Expected Output:**
```
services:
  media-analysis-api:
    networks:
    - af-network
networks:
  af-network:
    external: true
```

**Verification:**
```bash
# Exit code check
if docker compose config > /dev/null 2>&1; then
    echo "✓ Configuration valid"
else
    echo "✗ Configuration invalid - check errors above"
fi
```

**Risk Level:** LOW - Validation only, no changes

---

### Phase 5: Restart Container with New Configuration

**Objective:** Apply network configuration by restarting the service

**Commands:**
```bash
cd /opt/services/media-analysis

# Pull latest image (optional, ensure current)
docker compose pull

# Stop current container
docker compose down

# Start with new configuration
docker compose up -d

# Wait for container to initialize
sleep 10

# Verify container status
docker ps --filter name=media-analysis-api
```

**Verification:**
```bash
# Check container status
docker inspect media-analysis-api --format='{{.State.Status}}'

# Check network connections
docker inspect media-analysis-api --format='{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}'

# Verify af-network present
docker inspect media-analysis-api --format='{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}' | grep -q af-network && echo "✓ Connected to af-network" || echo "✗ Not connected to af-network"

# Test PostgreSQL DNS resolution
docker exec media-analysis-api nslookup af-postgres-1 2>&1 | head -5

# Check health status (wait up to 30 seconds)
for i in {1..30}; do
    STATUS=$(docker inspect media-analysis-api --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
    echo "Attempt $i: Health status = $STATUS"
    if [ "$STATUS" = "healthy" ]; then
        echo "✓ Container is healthy"
        break
    fi
    sleep 1
done
```

**Expected Output:**
```
Pull complete
Container stopped
Container started
Status: running
af-network
✓ Connected to af-network
Server:    127.0.0.11
Address:   127.0.0.11#53
...
Attempt 1: Health status = starting
...
Attempt N: Health status = healthy
✓ Container is healthy
```

**Risk Level:** MEDIUM - Service restart, brief downtime expected

---

### Phase 6: Functional Verification

**Objective:** Confirm API and database connectivity work correctly

**Commands:**
```bash
# Test API health endpoint
curl -s http://localhost:8050/health | jq .

# Test PostgreSQL connectivity (if database layer exists)
curl -s http://localhost:8050/health | jq '.database // "not configured"'

# Verify all endpoints respond
for endpoint in health api/media/video api/media/audio api/media/documents api/media/analyze; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8050/$endpoint")
    echo "$endpoint: $HTTP_CODE"
done
```

**Expected Output:**
```json
{
  "status": "ok",
  "version": "...",
  "database": "connected"  // after ma-22 implementation
}
```

```
health: 200
api/media/video: 200
api/media/audio: 200
api/media/documents: 200
api/media/analyze: 200
```

**Risk Level:** LOW - Read-only tests

---

## 5. Rollback Plan

### If Issues Occur

**Immediate Rollback:**
```bash
cd /opt/services/media-analysis

# Stop current container
docker compose down

# Restore backup
cp docker-compose.yml.backup-* docker-compose.yml

# Verify backup restored
docker compose config > /dev/null 2>&1 && echo "Backup valid" || echo "Backup corrupted"

# Restart with old configuration
docker compose up -d

# Wait for container
sleep 10

# Verify old status
docker ps --filter name=media-analysis-api
```

**Full Recovery Command:**
```bash
# Single command rollback
ssh devmaster 'cd /opt/services/media-analysis && \
  docker compose down && \
  cp docker-compose.yml.backup-$(ls -t docker-compose.yml.backup-* | head -1) docker-compose.yml && \
  docker compose up -d && \
  sleep 10 && \
  docker ps --filter name=media-analysis-api'
```

**Verification of Rollback:**
```bash
# Check container back to original state
docker inspect media-analysis-api --format='{{.State.Status}}'

# Verify NOT connected to af-network
docker inspect media-analysis-api --format='{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}' | grep -q af-network && echo "Still on af-network" || echo "Reverted to default network"
```

---

## 6. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| External network doesn't exist | Low | High | Verify af-network exists before deployment |
| Network naming conflict | Low | Medium | Use explicit name mapping |
| Service restart causes brief downtime | Medium | Low | Schedule during low-traffic period |
| YAML syntax error breaks container | Low | High | Validate with `docker compose config` before restart |
| Container fails to start after network change | Low | High | Rollback script ready; backup preserved |
| Other services lose connectivity | Low | High | Network is external; adding member doesn't affect others |

---

## 7. Dependencies and Prerequisites

### Prerequisites
- [x] SSH access to devmaster
- [x] Docker and docker-compose installed on devmaster
- [x] Backup of current docker-compose.yml created
- [x] af-network exists (verify: `docker network ls | grep af-network`)

### Dependencies
- **runpod-ma-22:** Database models depend on PostgreSQL connectivity (after this task)
- **runpod-ma-21:** Database schema creation (depends on this for network access)

### Blockers
- None identified

---

## 8. Success Criteria

| Criterion | Status | Verification |
|-----------|--------|--------------|
| Container starts without errors | Required | `docker compose up -d` succeeds |
| Container connects to af-network | Required | `docker inspect` shows af-network |
| DNS resolution works for af-postgres-1 | Required | `nslookup af-postgres-1` succeeds |
| Container health status is "healthy" | Required | `docker inspect --format='{{.State.Health.Status}}'` |
| API endpoints respond correctly | Required | All endpoints return 200 |
| No service disruption (brief restart only) | Required | Downtime < 60 seconds |

---

## 9. Time Estimate

| Phase | Duration | Total |
|-------|----------|-------|
| Phase 1: Backup | 1 minute | 1 min |
| Phase 2: Examine | 2 minutes | 3 min |
| Phase 3: Update | 3 minutes | 6 min |
| Phase 4: Validate | 2 minutes | 8 min |
| Phase 5: Restart + Health | 30 seconds | 9 min |
| Phase 6: Verify | 2 minutes | 11 min |

**Total Estimated Time:** 11 minutes (excluding rollback scenarios)

---

## 10. Files Modified

| File | Action | Line Numbers |
|------|--------|--------------|
| `/opt/services/media-analysis/docker-compose.yml` | Modified | Add networks section at end (after services) |
| `/opt/services/media-analysis/docker-compose.yml.backup-[TIMESTAMP]` | Created | Full copy of original |

---

## 11. References

| Document | Path | Relevance |
|----------|------|-----------|
| Handoff Document | `dev/agents/artifacts/doc/handoff/media-analysis-api-post-compaction-handoff.md` | Lines 212-218 contain exact network configuration |
| Database Schema PRD | `dev/agents/artifacts/doc/plan/media-analysis-ma-21-pre/` | Depends on this network fix |
| Docker Compose Reference | Docker official docs | External network syntax |

---

## 12. Commands Quick Reference

### Full Execution
```bash
ssh devmaster << 'EOF'
cd /opt/services/media-analysis

# Phase 1: Backup
cp docker-compose.yml docker-compose.yml.backup-$(date +%Y%m%d-%H%M%S)

# Phase 2: Examine (optional, for verification)
cat docker-compose.yml

# Phase 3: Update
python3 << 'PYEOF'
import yaml

with open('docker-compose.yml', 'r') as f:
    data = yaml.safe_load(f)

if 'networks' not in data:
    data['networks'] = {}

data['networks']['default'] = {
    'name': 'af-network',
    'external': True
}

with open('docker-compose.yml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
PYEOF

# Phase 4: Validate
docker compose config

# Phase 5: Restart
docker compose down
docker compose up -d
sleep 10

# Phase 6: Verify
docker inspect media-analysis-api --format='{{.State.Health.Status}}'
curl -s http://localhost:8050/health
EOF
```

### Rollback
```bash
ssh devmaster 'cd /opt/services/media-analysis && \
  docker compose down && \
  cp docker-compose.yml.backup-$(ls -t docker-compose.yml.backup-* | head -1) docker-compose.yml && \
  docker compose up -d'
```

---

**Document Version:** 1.0
**Generated:** 2026-01-20 05:08:00 UTC-6
**Model:** MiniMax + Opus UltraThink PRD Generator
