## Relations
@structure/docker/startup_process.md
@design/ai_models/model_inventory.md

## Raw Concept
**Task:**
Guide users on model selection based on GPU resources

**Changes:**
- Standardizes performance tuning based on hardware capabilities

**Files:**
- docker/start.sh

**Flow:**
Detect VRAM -> Set GPU_TIER -> Set GPU_MEMORY_MODE -> Select models via env vars

**Timestamp:** 2026-01-18T05:38:56.747Z

## Narrative
### Structure
- `docker/start.sh` logic for auto-detection
- Tier-based model selection guide in `section-002-ai-models.md`

### Dependencies
- Based on NVIDIA GPU VRAM
- Consumer: 8-24GB (RTX 3080/4070/4080/4090)
- Prosumer: 24GB+ (A6000, L40S)
- Datacenter: 48-80GB (A100, H100)

### Features
- Automated `GPU_TIER` and `GPU_MEMORY_MODE` assignment
- Optimized `COMFYUI_ARGS` for different VRAM levels
- Recommended model sets for each tier (e.g., WAN 480p for 8GB, 720p for 16GB+)
