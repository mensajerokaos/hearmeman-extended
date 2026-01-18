## Raw Concept
**Task:**
Docker Infrastructure Documentation

**Changes:**
- Introduces production-ready Docker infrastructure for RunPod pods
- Implements automated environment detection for VRAM and storage
- Adds background sync to Cloudflare R2

**Files:**
- docker/Dockerfile
- docker/docker-compose.yml
- docker/start.sh
- docker/download_models.sh
- docker/r2_sync.sh
- docker/upload_to_r2.py

**Flow:**
Dockerfile builds image -> start.sh detects GPU/Storage -> download_models.sh fetches assets -> R2 sync starts -> ComfyUI launches

**Timestamp:** 2026-01-17

## Narrative
### Structure
- docker/Dockerfile: Build configuration
- docker/docker-compose.yml: Service orchestration
- docker/start.sh: Container entrypoint script
- docker/download_models.sh: Model downloader
- docker/r2_sync.sh: R2 sync daemon
- docker/custom_nodes/: Local custom nodes directory

### Dependencies
- Requires NVIDIA Container Toolkit
- Depends on RunPod PyTorch base image
- Local custom nodes: ComfyUI-Genfocus, ComfyUI-MVInverse

### Features
- Multi-layer build for ComfyUI and custom nodes
- GPU tier and storage mode auto-detection
- Automated model downloading at startup
- R2 output synchronization daemon
- Integrated SSH and JupyterLab access
