# Media Analysis API - Global Context

## Architecture Overview
The **media-analysis-api** is a FastAPI service with three-branch architecture (Audio, Video, Document) deployed on `devmaster` VPS.

## Key Infrastructure

### PostgreSQL
- **Host**: af-postgres-1 (in af-network)
- **Database**: af-memory
- **User**: n8n
- **Pattern**: Table-level isolation, connection pooling via context managers
- **Key Tables**: media_analysis_requests, media_analysis_results, media_files, contact_sheets

### VPS Deployment
- **Path**: `/opt/services/media-analysis/`
- **Container**: media-analysis-api on port 8050
- **Network**: Needs to join af-network for PostgreSQL access
- **Docker**: Managed via docker-compose.yml

### Caddy Configuration
- **Domain**: media-analysis.af.automatic.picturelle.com
- **Reverse Proxy**: localhost:8050
- **SSL**: Cloudflare DNS validation
- **Config Path**: /opt/clients/af/Caddyfile.d/

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| /health | GET | Health check |
| /api/media/video | POST | Video analysis |
| /api/media/audio | POST | Audio transcription |
| /api/media/documents | POST | Document/image analysis |
| /api/media/analyze | POST | Aggregator with prompt routing |

### Fallback Chains
```
AUDIO: Groq → Deepgram → Whisper-1 → Gemini
VISION: Qwen3-VL → Gemini 2.5 Flash → GPT-5 Mini → MiniMax (text-only)
TEXT: MiniMax → Gemini 2.5 Flash → Haiku
```

## Source Documents
- Handoff: dev/agents/artifacts/doc/handoff/media-analysis-api-post-compaction-handoff.md
- PRD: dev/agents/artifacts/doc/plan/media-analysis-api-prd.md
- Beads: .beads/issues-media-analysis.jsonl

## Anti-Patterns (AVOID)
- NO Alembic migrations (use direct SQL)
- NO Redis caching (not needed for MVP)
- NO circuit breakers (overkill)
- NO audit logging tables (not requested)
- Keep plans minimal and executable
