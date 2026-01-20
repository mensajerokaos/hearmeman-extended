## Relations
@structure/docker/docker_infrastructure_overview.md

## Raw Concept
**Task:**
Update Startup Process Documentation

**Changes:**
- Detailed startup sequence and VRAM detection logic from master-documentation.md

**Files:**
- docker/start.sh

**Flow:**
Entrypoint -> detect storage -> detect GPU -> setup access -> update nodes -> download models -> start services -> launch ComfyUI

**Timestamp:** 2026-01-18

## Narrative
### Structure
- docker/start.sh: Main entrypoint
- /var/log/jupyter.log
- /var/log/r2_sync.log

### Dependencies
- STORAGE_MODE (auto, ephemeral, persistent)
- PUBLIC_KEY (SSH)
- JUPYTER_PASSWORD (JupyterLab)
- UPDATE_NODES_ON_START

### Features
- Automated storage mode detection
- GPU VRAM detection and optimization
- Conditional service starting (SSH, Jupyter, R2 Sync)
- ComfyUI argument generation based on VRAM
- Node update logic on startup
