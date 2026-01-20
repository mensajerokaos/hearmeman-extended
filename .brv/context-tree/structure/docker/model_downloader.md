## Relations
@structure/docker/docker_infrastructure_overview.md

## Raw Concept
**Task:**
Update Model Downloader Documentation

**Changes:**
- Detailed model downloader script logic from master-documentation.md

**Files:**
- docker/download_models.sh

**Flow:**
start.sh -> download_models.sh -> check ENV -> download via wget/curl/Python -> log results

**Timestamp:** 2026-01-18

## Narrative
### Structure
- /workspace/ComfyUI/models/
- /var/log/download_models.log

### Dependencies
- wget (with resume), curl (fallback)
- huggingface_hub (Python)
- CivitAI API
- Environment variables: DRY_RUN, MODELS_DIR

### Features
- hf_download: Single file download from HF
- hf_snapshot_download: Full repo snapshot from HF
- civitai_download: Version-id based download from CivitAI
- Conditional logic based on ENABLE_* variables
- Checksums and size verification support
