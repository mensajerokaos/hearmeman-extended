## Relations
@structure/docker/dockerfile.md
@structure/docker/startup_process.md

## Raw Concept
**Task:**
Define local run topology and service configuration

**Changes:**
- Defines the runtime topology for the RunPod custom template
- Configures port mappings and volume mounts for persistence

**Files:**
- docker/docker-compose.yml

**Flow:**
docker-compose up -> starts hearmeman-extended container -> executes start.sh

**Timestamp:** 2026-01-18T05:38:56.747Z

## Narrative
### Structure
- `docker/docker-compose.yml`
- Binds `./models` to `/workspace/ComfyUI/models`
- Binds `./output` to `/workspace/ComfyUI/output`

### Dependencies
- Requires NVIDIA Container Toolkit
- Depends on `docker/Dockerfile` for build
- Uses `docker/start.sh` as entrypoint
- Optional `chatterbox` service requires `chatterbox` profile

### Features
- Multi-container setup for ComfyUI and Chatterbox TTS API
- Persistent volumes for models (`/workspace/ComfyUI/models`) and output (`/workspace/ComfyUI/output`)
- GPU support via `nvidia` runtime
- Port mapping for ComfyUI (8188), SSH (2222), JupyterLab (8888), and Chatterbox (8000)
