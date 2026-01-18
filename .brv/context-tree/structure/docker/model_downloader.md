## Relations
@structure/docker/startup_process.md
@design/ai_models/model_inventory.md

## Raw Concept
**Task:**
Automate model provisioning for ephemeral pods

**Changes:**
- Handles automated model fetching at pod startup

**Files:**
- docker/download_models.sh

**Flow:**
start.sh calls download_models.sh -> checks env vars -> downloads enabled models to /workspace/ComfyUI/models

**Timestamp:** 2026-01-18T05:38:56.747Z

## Narrative
### Structure
- `docker/download_models.sh`
- Helper functions: `download_model`, `hf_download`, `hf_snapshot_download`, `civitai_download`

### Dependencies
- Uses `wget`, `curl`, and `aria2`
- Requires `huggingface_hub` Python package for snapshots
- Requires `CIVITAI_API_KEY` for private/limited CivitAI downloads

### Features
- Resumable downloads for large models
- Support for HuggingFace (individual and snapshots) and CivitAI
- Conditional downloads based on environment variables (e.g., `ENABLE_VIBEVOICE`)
- Dry run mode for testing configuration
