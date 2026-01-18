## Relations
@structure/models/ai_models_overview.md

## Raw Concept
**Task:**
Chatterbox TTS Documentation

**Changes:**
- Adds OpenAI-compatible TTS API service
- Implements voice library management system
- Adds SSE streaming for low-latency delivery

**Files:**
- docker/chatterbox-api/
- docker/docker-compose.yml

**Flow:**
POST /audio/speech -> JSON Payload (input, voice, exaggeration) -> WAV or SSE stream

**Timestamp:** 2026-01-17

## Narrative
### Structure
- docker/chatterbox-api/: FastAPI server source
- docker/chatterbox-api/app/core/aliases.py: API alias mapping
- docker/chatterbox-api/app/core/mtl.py: Multilingual language codes

### Dependencies
- Independent of ComfyUI Python environment
- Uses Resemble AI Chatterbox libraries

### Features
- OpenAI-compatible API endpoints (/v1/audio/speech)
- Persistent voice library with upload and alias support
- Advanced artistic controls: CFG weight and Exaggeration
- Dual streaming modes: Raw WAV and SSE (Server-Sent Events)
- Support for 23 languages (multilingual model)
