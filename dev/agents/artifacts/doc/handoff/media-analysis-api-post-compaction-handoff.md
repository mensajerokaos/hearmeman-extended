# Media Analysis API - Post-Compaction Handoff Document

**Date:** 2026-01-20
**Session:** Post-long-conversation compaction
**Project:** media-analysis-api (/opt/services/media-analysis/)

---

## Executive Summary

The media-analysis-api service has been successfully deployed to devmaster on port 8050 with working fallback chains for transcription, vision, document, text, and reasoning tasks. A PostgreSQL + File System epic has been created to add persistent storage for tracking analysis history.

---

## Completed Work (Before Compaction)

### Deployment Status
| Component | Status | Details |
|-----------|--------|---------|
| Container | ✅ Running | `media-analysis-api` on port 8050 |
| Health Check | ✅ OK | Returns status, version, features |
| Endpoints | ✅ All 200 | /health, /api/media/video, /api/media/audio, /api/media/documents, /api/media/analyze |
| Qwen3-VL | ✅ Configured | novita → phala → fireworks providers |
| GPT-5 Mini | ✅ Configured | openai/gpt-5-mini via OpenRouter |
| Gemini 2.5 Flash | ✅ Configured | google-vertex → google-ai-studio |
| MiniMax | ✅ Direct API | Text-only (no vision MCP yet) |
| Whisper Adapter | ✅ Created | OpenAI Whisper integration |

### Beads Completed
| Bead ID | Task | Status |
|---------|------|--------|
| runpod-15 | Add QWEN3_VL and GPT5_MINI providers | ✅ Closed |
| runpod-16 | Create Whisper adapter | ✅ Closed |
| runpod-17 | Update fallback chains | ✅ Closed |
| runpod-18 | Add OPENAI_API_KEY | ✅ Closed |
| runpod-19 | Test fallback chains | ✅ Closed |
| runpod-20 | Deploy to devmaster | ✅ Closed |

### Fallback Chains Configured

```
AUDIO TRANSCRIPTION:
  Primary:     Groq (whisper-large-v3)
  Fallback 1:  Deepgram (nova-2)
  Fallback 2:  Whisper-1 (OpenAI)
  Fallback 3:  Gemini 3.5 Flash (OpenRouter)

VISION/DOCUMENT ANALYSIS:
  Primary:     Qwen3-VL 30B A3B (novita → phala → fireworks)
  Fallback 1:  Gemini 2.5 Flash (google-vertex → google-ai-studio)
  Fallback 2:  GPT-5 Mini (openai/gpt-5-mini, OpenRouter)
  Fallback 3:  MiniMax (direct API - text only)

TEXT GENERATION:
  Primary:     MiniMax (direct API)
  Fallback 1:  Gemini 2.5 Flash (google-vertex → google-ai-studio)
  Fallback 2:  Haiku (OpenRouter)

REASONING/ANALYSIS:
  Primary:     MiniMax (direct API)
  Fallback 1:  Gemini 2.5 Flash (google-vertex → google-ai-studio)
  Fallback 2:  Haiku (OpenRouter)
```

---

## Current Issues

### 1. Container Health Status
- **Issue:** Container shows "unhealthy" despite API responding correctly
- **Cause:** PostgreSQL DNS resolution failure (`af-postgres-1` hostname not resolving)
- **Impact:** None - API functions correctly, health check endpoint returns OK
- **Root Cause:** Container on separate network, not connected to af-network
- **Fix:** Add af-network to docker-compose.yml (runpod-ma-25)

### 2. MiniMax Vision MCP Not Integrated
- **Issue:** MiniMax can only do text analysis (no vision MCP integration)
- **Impact:** MiniMax is fallback only for vision tasks
- **Research Needed:** runpod-ma-27

---

## Remaining Work (Epic + Tasks Created)

### EPIC: PostgreSQL + File System Support
**ID:** runpod-ma-epic-01
**Priority:** P1
**Description:** Add persistent storage to track analysis history, store media files, and enable querying of past results.

#### Child Tasks

| ID | Task | Priority | Dependencies |
|----|------|----------|--------------|
| runpod-ma-21 | Create PostgreSQL Database Schema | P1 | None |
| runpod-ma-22 | Create Database Models and Connection Layer | P1 | ma-21 |
| runpod-ma-23 | Implement File Storage Organization System | P1 | None |
| runpod-ma-24 | Integrate Database with API Endpoints | P2 | ma-22, ma-23 |
| runpod-ma-25 | Update Docker Compose with PostgreSQL Network | P2 | ma-22 |

### Subsequent Tasks

| ID | Task | Priority | Description |
|----|------|----------|-------------|
| runpod-ma-26 | TEST: Vision Fallback Chain | P1 | Comprehensive test of Qwen3→Gemini→GPT-5→MiniMax |
| runpod-ma-27 | RESEARCH: MiniMax Vision MCP | P1 | Research MiniMax MCP integration for vision |
| runpod-ma-28 | Create Caddyfile Configuration | P1 | External routing for media-analysis.af.automatic.picturelle.com |

---

## Detailed Execution Instructions

### runpod-ma-21: Create PostgreSQL Database Schema

Execute on devmaster:
```bash
# SSH to devmaster
ssh devmaster

# Create tables in af-memory database
docker exec af-postgres-1 psql -U n8n -d af-memory << 'EOF'
CREATE TABLE IF NOT EXISTS media_analysis_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    media_url TEXT NOT NULL,
    prompt TEXT NOT NULL,
    media_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    model_used VARCHAR(100),
    latency_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS media_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES media_analysis_requests(id) ON DELETE CASCADE,
    result_text TEXT NOT NULL,
    model_used VARCHAR(100) NOT NULL,
    prompt_used TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    latency_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS media_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_path TEXT,
    storage_path TEXT NOT NULL,
    size_bytes BIGINT,
    mime_type VARCHAR(100),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS contact_sheets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES media_analysis_requests(id) ON DELETE CASCADE,
    storage_path TEXT NOT NULL,
    frames_count INTEGER NOT NULL,
    grid_layout VARCHAR(20) DEFAULT '2x3',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_requests_status ON media_analysis_requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_created ON media_analysis_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_results_request ON media_analysis_results(request_id);
CREATE INDEX IF NOT EXISTS idx_files_uploaded ON media_files(uploaded_at DESC);
EOF
```

### runpod-ma-22: Create Database Models

Create directory structure:
```bash
ssh devmaster 'mkdir -p /opt/services/media-analysis/api/models'
```

Create files:
- `/opt/services/media-analysis/api/models/__init__.py`
- `/opt/services/media-analysis/api/models/database.py` - Connection pool (asyncpg)
- `/opt/services/media-analysis/api/models/analysis_request.py` - SQLAlchemy model + Pydantic schema
- `/opt/services/media-analysis/api/models/media_file.py` - File metadata model
- `/opt/services/media-analysis/api/models/contact_sheet.py` - Contact sheet model

Reference: `/opt/clients/af/services/cotizador-api/api/models/` for patterns.

### runpod-ma-23: Implement File Storage

Create directory structure:
```bash
ssh devmaster 'mkdir -p /opt/services/media-analysis/storage/{uploads,frames,contact-sheets,outputs,temp}'
ssh devmaster 'chmod 755 /opt/services/media-analysis/storage/*'
```

Create storage management module:
- `/opt/services/media-analysis/api/storage.py`
- Implement cleanup policies (temp/: 24h, uploads/: 7d, contact-sheets/: 30d, outputs: indefinite)

### runpod-ma-24: Integrate Database with Endpoints

Update these endpoints:
- `POST /api/media/analyze` - Create analysis_request record at start
- `GET /api/media/status/{id}` - Query database for status + results
- `DELETE /api/media/{id}` - Soft delete (status='deleted')
- `GET /api/media/history` - List all analyses (paginated)

### runpod-ma-25: Update Docker Compose

Update `/opt/services/media-analysis/docker-compose.yml`:
```yaml
networks:
  default:
    name: af-network
    external: true
```

### runpod-ma-26: Test Vision Fallback Chain

Execute comprehensive test:
```bash
ssh devmaster << 'EOF'
CDN_URL="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg?token=6e65f4e151b3f3675e05e712f4e7f9c867d48020870f33f61c0ea3bbcdc64cb5"

echo "=== Testing Vision Fallback Chain ==="

echo -n "[1/4] Qwen3-VL (primary): "
curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image in detail\"}" \
  -w "%{http_code}\n" -o /dev/null

echo -n "[2/4] Gemini 2.5 Flash: "
curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\", \"model\": \"gemini-2.5-flash\"}" \
  -w "%{http_code}\n" -o /dev/null

echo -n "[3/4] GPT-5 Mini: "
curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\", \"model\": \"gpt-5-mini\"}" \
  -w "%{http_code}\n" -o /dev/null

echo -n "[4/4] MiniMax (text-only fallback): "
curl -s -X POST http://localhost:8050/api/media/analyze \
  -H 'Content-Type: application/json' \
  -d "{\"media_type\": \"document\", \"media_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\"}" \
  -w "%{http_code}\n" -o /dev/null

echo "=== Test Complete ==="
EOF
```

### runpod-ma-27: Research MiniMax Vision MCP

Research steps:
1. Check MiniMax MCP configuration at `/home/oz/.claude/mcp-servers/`
2. Review understand_image tool capabilities
3. Test MiniMax vision directly (if possible)
4. Document integration requirements
5. Create PRD if viable

### runpod-ma-28: Create Caddyfile

Create Caddyfile at `/opt/services/media-analysis/Caddyfile`:
```
media-analysis.af.automatic.picturelle.com {
    reverse_proxy localhost:8050 {
        header_up Host {host}
        header_up X-Real-IP {remote}
    }
    tls {
        dns cloudflare <CLOUDFLARE_API_TOKEN>
    }
    header {
        Strict-Transport-Security max-age=31536000
        X-Content-Type-Options nosniff
    }
    rate_limit {
        zone api_limit 1000 1s
    }
}
```

Deploy:
```bash
ssh devmaster 'docker run --rm -v /opt/services/media-analysis/Caddyfile:/etc/caddy/Caddyfile caddy:2.7 validate'
ssh devmaster 'cp /opt/services/media-analysis/Caddyfile /opt/clients/af/Caddyfile.d/media-analysis.caddyfile && caddy reload --config /opt/clients/af/Caddyfile.d/media-analysis.caddyfile'
```

---

## Connection Details

### PostgreSQL (af-memory database)
| Property | Value |
|----------|-------|
| Host | af-postgres-1 |
| Port | 5432 |
| Database | af-memory |
| User | n8n |
| Password | 89wdPtUBK4pn6kDPQcaM |

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| /health | GET | Health check |
| /api/media/video | POST | Video analysis |
| /api/media/audio | POST | Audio transcription |
| /api/media/documents | POST | Document/image analysis |
| /api/media/analyze | POST | Aggregator with prompt routing |

### Fallback Chain Providers
| Task | Provider | Model | URL |
|------|----------|-------|-----|
| Audio | Groq | whisper-large-v3 | api.groq.com |
| Audio | Deepgram | nova-2 | api.deepgram.com |
| Audio | OpenAI | whisper-1 | api.openai.com |
| Vision | Qwen3-VL | qwen3-vl-30b-a3b-instruct | novita/phala/fireworks (OpenRouter) |
| Vision | Gemini | gemini-2.5-flash | google-vertex → google-ai-studio |
| Vision | OpenAI | gpt-5-mini | OpenRouter |
| Text | MiniMax | direct | api.minimax.chat |
| Text | Gemini | gemini-2.5-flash | OpenRouter |
| Text | Anthropic | haiku | OpenRouter |

---

## File Locations

| Path | Description |
|------|-------------|
| /opt/services/media-analysis/ | Service root |
| /opt/services/media-analysis/api/ | API code |
| /opt/services/media-analysis/api/capability_matrix.py | Provider configurations |
| /opt/services/media-analysis/api/prompt_router.py | Fallback chain logic |
| /opt/services/media-analysis/config/.env | Environment variables |
| /opt/services/media-analysis/docker-compose.yml | Docker configuration |
| /opt/services/media-analysis/Caddyfile | Caddy routing (needs creation) |

---

## Commands Quick Reference

```bash
# View container status
ssh devmaster 'docker ps --filter name=media-analysis'

# View logs
ssh devmaster 'docker logs media-analysis-api --tail 50'

# Restart container
ssh devmaster 'cd /opt/services/media-analysis && docker compose restart'

# Test health
ssh devmaster 'curl -s http://localhost:8050/health | jq .'

# Test endpoints
ssh devmaster 'for ep in health api/media/video api/media/audio api/media/documents api/media/analyze; do echo -n "$ep: "; curl -s -o /dev/null -w "%{http_code}" "http://localhost:8050/$ep"; done'

# Sync beads to database
cd /home/oz/projects/2025/oz/12/runpod && BD_DB=/home/oz/projects/2025/oz/12/runpod/.beads/beads.db bd sync --import-only
```

---

## PRD References

| Document | Path |
|----------|------|
| Media Analysis API PRD | dev/agents/artifacts/doc/plan/media-analysis-api-prd.md |
| PRD Audit (50/50) | dev/agents/artifacts/doc/audit/media-analysis-api-prd.md |
| Beads | .beads/issues-media-analysis.jsonl |

---

## Next Actions

1. **Immediate (P0):**
   - Run plan00 → plan04 for runpod-ma-epic-01 (PostgreSQL + File System)
   - Execute runpod-ma-26 (Vision fallback test)

2. **Short-term (P1):**
   - Execute runpod-ma-27 (MiniMax Vision MCP research)
   - Execute runpod-ma-28 (Caddyfile configuration)

3. **Medium-term (P2):**
   - Implement ma-21 through ma-25 (PostgreSQL integration)
   - Connect MiniMax MCP for vision (once research complete)

---

**Document Version:** 1.0
**Created:** 2026-01-20 08:30:00 UTC-6
**Author:** Claude Code (Post-compaction handoff)
