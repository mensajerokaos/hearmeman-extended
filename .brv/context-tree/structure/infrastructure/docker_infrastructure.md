## Relations
@structure/models/vram_requirements.md
@structure/audio_voice/tts_systems.md

## Raw Concept
**Task:**
Document Docker infrastructure for RunPod custom template

**Changes:**
- Introduces production-ready RunPod Docker infrastructure
- Automates model downloads and GPU detection
- Integrates R2 sync for output persistence

**Files:**
- docker/Dockerfile
- docker/docker-compose.yml
- docker/start.sh
- docker/download_models.sh
- docker/r2_sync.sh
- docker/upload_to_r2.py

**Flow:**
Dockerfile build -> container start -> start.sh -> GPU/storage detection -> download_models.sh -> R2 sync (optional) -> ComfyUI launch

**Timestamp:** 2026-01-18

## Narrative
### Structure
- docker/Dockerfile
- docker/docker-compose.yml
- docker/start.sh
- docker/download_models.sh
- docker/r2_sync.sh
- docker/upload_to_r2.py

### Dependencies
- ComfyUI (cloned into /workspace/ComfyUI)
- Third-party nodes (ComfyUI-Manager, VibeVoice, etc.)
- Local custom nodes (Genfocus, MVInverse)

### Features
- Configurable BASE_IMAGE (default RunPod PyTorch CUDA)
- Multi-layer build: system deps, ComfyUI base, custom nodes, extra Python deps
- Optional model baking (WAN, Illustrious) via build args
- Entrypoint: start.sh
