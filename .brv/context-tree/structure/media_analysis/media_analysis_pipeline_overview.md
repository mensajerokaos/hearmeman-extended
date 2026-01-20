## Relations
@structure/storage/r2_output_persistence.md
@tts_systems/overview/tts_systems_overview.md

## Raw Concept
**Task:**
Media Analysis API - Cotizador Clone

**Changes:**
- Cloned cotizador-api from AF project to create standalone media-analysis service

**Files:**
- cotizador_api.py
- docker-compose.yml
- Dockerfile
- .env
- Caddyfile

**Flow:**
POST /api/analyze/* -> Branch Logic (Audio/Video/Doc) -> Processing (FFmpeg/Deepgram/OCR) -> Result/Persistence (R2)

**Timestamp:** 2026-01-18

## Narrative
### Structure
- /opt/services/media-analysis/: Project root
- cotizador_api.py: Main API (344KB, 50+ endpoints)
- docker-compose.yml: Orchestration
- Dockerfile: Build configuration
- Caddyfile: Proxy configuration
- .env: Credentials and settings

### Dependencies
- FastAPI (Python 3.11 slim)
- FFmpeg (for frame extraction)
- Deepgram / Grok (Transcription)
- OCR Libraries (Document analysis)
- Caddy (Reverse proxy)

### Features
- Three-branch architecture: Audio, Video, and Document
- 3fps frame extraction from video
- 2x3 grid contact sheet generation for LLM analysis
- OpenAI-compatible transcription fallback (Groq/OpenAI/Gemini)
- 50+ specialized endpoints for media analysis
