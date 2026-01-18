## Relations
@structure/docker/docker_infrastructure_overview.md
@design/ai_models/gpu_tier_recommendations.md

## Raw Concept
**Task:**
Document Container Startup Process

**Changes:**
- Standardizes pod initialization and hardware-aware performance tuning

**Files:**
- docker/start.sh
- docker/download_models.sh

**Flow:**
Image Pull -> GPU Detection -> Storage Detection -> SSH/Jupyter -> Model Downloads -> R2 Sync -> ComfyUI Launch

**Timestamp:** 2026-01-18

## Narrative
### Structure
- docker/start.sh: Entrypoint orchestration
- VRAM Thresholds: <8GB, 8-12GB, 12-16GB, 16-24GB, 24-48GB, 48GB+

### Dependencies
- `nvidia-smi` for VRAM detection
- `download_models.sh` for model provisioning
- `r2_sync.sh` for output persistence

### Features
- Storage mode detection (ephemeral vs persistent)
- Automatic GPU tier assignment (Consumer, Prosumer, Datacenter)
- Memory mode and ComfyUI arg optimization based on VRAM
- Optional SSH and JupyterLab initialization
- Coordinated startup sequence from image pull to ComfyUI launch
