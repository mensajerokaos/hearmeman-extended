## Relations
@structure/storage/r2_output_persistence.md

## Raw Concept
**Task:**
Document R2 Storage Sync for RunPod Custom Template

**Changes:**
- Updated R2 sync system documentation from master-documentation.md

**Files:**
- docker/r2_sync.sh
- docker/upload_to_r2.py

**Flow:**
ComfyUI generates file -> inotify detects change -> upload_to_r2.py called -> File uploaded to R2 bucket

**Timestamp:** 2026-01-18

## Narrative
### Structure
- docker/r2_sync.sh: Sync daemon
- docker/upload_to_r2.py: Upload logic
- /workspace/ComfyUI/output: Monitored directory

### Dependencies
- R2_ENDPOINT, R2_BUCKET, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
- inotify-tools for file system monitoring
- boto3 for Python upload script

### Features
- Background daemon (r2_sync.sh) monitors output directory
- Persistent storage for ephemeral RunPod pods
- Automatic upload of generated files to Cloudflare R2
- Verification and testing tools provided
