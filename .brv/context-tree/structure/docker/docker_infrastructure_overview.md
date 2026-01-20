## Relations
@structure/docker/docker_compose_configuration.md
@structure/docker/startup_process.md
@structure/docker/model_downloader.md

## Raw Concept
**Task:**
Document Docker Infrastructure for RunPod Custom Template

**Changes:**
- Consolidated Docker infrastructure documentation from master-documentation.md

**Files:**
- docker/Dockerfile
- docker/docker-compose.yml
- docker/start.sh
- docker/download_models.sh

**Flow:**
Build image -> docker-compose up -> start.sh (detect GPU/storage) -> download_models.sh -> r2_sync.sh (optional) -> ComfyUI start

**Timestamp:** 2026-01-18

## Narrative
### Structure
- docker/Dockerfile: Build layers and architecture
- docker/docker-compose.yml: Service definitions (ComfyUI, Chatterbox)
- docker/start.sh: Entrypoint logic
- docker/download_models.sh: Model fetching logic

### Dependencies
- Base image: RunPod PyTorch CUDA
- Systems deps: git, ffmpeg, OpenGL, SSH, aria2
- ComfyUI + Custom Nodes
- Startup scripts: start.sh, download_models.sh, r2_sync.sh

### Features
- Production-ready Docker container for AI generation
- Integrated ComfyUI with custom nodes
- Ephemeral environment support with startup model downloads
- Cloudflare R2 sync for persistence
