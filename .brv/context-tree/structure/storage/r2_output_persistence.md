## Relations
@structure/storage/r2_storage_sync_system.md

## Raw Concept
**Task:**
Update R2 Output Persistence Documentation

**Changes:**
- Detailed R2 persistence logic and scripts from master-documentation.md

**Files:**
- docker/r2_sync.sh
- docker/upload_to_r2.py

**Flow:**
File created -> inotify trigger -> upload_to_r2.py -> R2 Bucket

**Timestamp:** 2026-01-18

## Narrative
### Structure
- docker/r2_sync.sh
- docker/upload_to_r2.py
- /workspace/ComfyUI/output/

### Dependencies
- Cloudflare R2 S3-compatible API
- Boto3 (Python)
- inotify-tools (for daemon)

### Features
- r2_sync.sh: Background daemon using inotifywait
- upload_to_r2.py: Core upload logic with retry and testing
- Persistence for ephemeral pods
- Verification via --test flag
- Monitoring via /var/log/r2_sync.log
