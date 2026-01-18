## Relations
@structure/models/ai_models_overview.md
@tts_systems/dependency_management/transformers_conflict.md

## Raw Concept
**Task:**
XTTS v2 API Documentation

**Changes:**
- Provides standalone XTTS v2 API service
- Adds CLI automation for batch voice-over generation

**Files:**
- docker/scripts/xtts-vo-gen.py

**Flow:**
POST /tts_to_audio/ -> JSON Payload (text, speaker, lang) -> WAV Bytes output

**Timestamp:** 2026-01-17

## Narrative
### Structure
- daswer123/xtts-api-server:latest (Docker image)
- docker/scripts/xtts-vo-gen.py: CLI wrapper script

### Dependencies
- transformers == 4.36.2 (Strict version pin)
- Recommended to run in separate container to avoid conflicts

### Features
- Multilingual support for 17 languages
- REST API with Swagger UI (Port 8020)
- Simple voice cloning from 6-10s audio samples
- Audio streaming support via /tts_stream endpoint
