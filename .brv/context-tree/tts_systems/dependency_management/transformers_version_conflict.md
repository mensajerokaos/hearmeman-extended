## Relations
@tts_systems/vibevoice/vibevoice_comfyui_integration.md
@tts_systems/xtts_v2/xtts_v2_rest_api.md

## Raw Concept
**Task:**
TTS Dependency Conflict Management

**Changes:**
- Documents critical dependency conflict between TTS systems
- Provides containerization strategy to resolve version pins

**Files:**
- docker/Dockerfile
- docker/docker-compose.yml

**Flow:**
Identify conflict -> Separate environments -> Containerize -> Orchestrate via Compose

**Timestamp:** 2026-01-17

## Narrative
### Structure
- docker/docker-compose.yml: Orchestrates separate containers for conflicting services

### Features
- XTTS v2 requires transformers == 4.36.2
- VibeVoice requires transformers >= 4.51.3
- Solution: Run XTTS in a separate container from ComfyUI/VibeVoice
- Aggregate VRAM usage is additive when co-running systems
