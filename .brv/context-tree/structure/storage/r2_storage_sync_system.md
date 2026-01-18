## Relations
@structure/docker/docker_infrastructure_overview.md
@structure/docker/startup_process.md

## Raw Concept
**Task:**
Document R2 Storage Sync System

**Changes:**
- Implements persistent storage for ephemeral RunPod pods via Cloudflare R2
- Provides automated output synchronization and manual upload capabilities

**Files:**
- docker/r2_sync.sh
- docker/upload_to_r2.py
- docker/start.sh

**Flow:**
File closed (close_write) -> Match Pattern -> sleep 1s -> python3 upload_to_r2.py -> R2 Bucket

**Timestamp:** 2026-01-18

## Narrative
### Structure
- docker/r2_sync.sh (Daemon)
- docker/upload_to_r2.py (Uploader CLI)
- /var/log/r2_sync.log (Primary Log)
- /var/log/r2_sync_init.log (Nohup Capture)

### Dependencies
- inotify-tools (inotifywait)
- boto3
- upload_to_r2.py

### Features
- Background daemon (r2_sync.sh) watching /workspace/ComfyUI/output
- Regex-based file filtering (.png, .jpg, .mp4, .webm, .wav, etc.)
- Concurrent uploads using background subshells
- Date-based R2 organization: {prefix}/{YYYY-MM-DD}/{filename}
- Retries with exponential backoff and multipart support for files > 100MB
