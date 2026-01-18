## Relations
@structure/docker/startup_process.md
@design/ai_models/gpu_tier_recommendations.md
@structure/storage/r2_storage_sync_system.md

## Raw Concept
**Task:**
Document RunPod Deployment Patterns

**Changes:**
- Documents production deployment patterns for RunPod pods
- Provides hardware-specific configuration presets and benchmark data

**Files:**
- docker/start.sh
- docker/download_models.sh

**Flow:**
Pod Creation -> Image Pull -> start.sh Initialization -> Service Readiness

**Timestamp:** 2026-01-18

## Narrative
### Structure
- docker/start.sh (Startup logic)
- RunPod Template environment variables

### Dependencies
- runpodctl
- RunPod Secrets (r2_access_key, r2_secret_key, civitai_key)

### Features
- Standardized pod creation commands for different GPU tiers
- Environment variable mapping for all 25+ models
- Port configuration: 8188 (ComfyUI), 22 (SSH), 8888 (Jupyter), 8000 (XTTS)
- Datacenter selection: US Secure Cloud (51 MB/s) recommended for production
- Startup sequence: GPU detection -> Storage detection -> Model Download -> R2 Sync -> ComfyUI launch
