## Relations
@structure/docker/startup_process.md
@structure/infrastructure/docker_infrastructure.md
@structure/docker/r2_sync_utilities.md

## Raw Concept
**Task:**
Document R2 Output Persistence System

**Changes:**
- Implements persistent output storage for ephemeral RunPod pods
- Provides automated background synchronization to Cloudflare R2
- Adds CLI utility for manual and tested R2 uploads
- Provides automated output persistence for ephemeral RunPod pods
- Implements concurrent, non-throttled uploads to remote S3-compatible storage

**Files:**
- docker/r2_sync.sh
- docker/upload_to_r2.py
- docker/start.sh

**Flow:**
File written to output -> close_write event -> check extension -> background upload -> Cloudflare R2 bucket

**Timestamp:** 2026-01-18

## Narrative
### Structure
- docker/r2_sync.sh: Bash daemon script
- docker/upload_to_r2.py: Python CLI uploader
- /var/log/r2_sync.log: Primary synchronization log

- docker/r2_sync.sh: Daemon script
- docker/upload_to_r2.py: Uploader CLI
- /var/log/r2_sync.log: Primary logs
- /var/log/r2_sync_init.log: Startup capture

### Dependencies
- inotify-tools (inotifywait)
- python3
- boto3

- `inotify-tools` (inotifywait)
- `python3` + `boto3`
- Cloudflare R2 S3-compatible API credentials

### Features
- Real-time file monitoring via `r2_sync.sh` daemon
- Whitelisted media extensions (png, jpg, mp4, webm, wav, etc.)
- Concurrent background uploads via `upload_to_r2.py`
- Organized R2 storage structure: {prefix}/{YYYY-MM-DD}/{filename}
- Resumable multipart uploads for files > 100MB
- Exponential backoff retry logic (3 attempts)

- `r2_sync.sh`: Background daemon watching `/workspace/ComfyUI/output`
- Whitelist filtering: .png, .jpg, .webp, .mp4, .webm, .gif, .wav, .mp3, .flac
- `upload_to_r2.py`: CLI with retry logic, exponential backoff, and multipart support (>100MB)
- Organized R2 key format: `{prefix}/{YYYY-MM-DD}/{filename}`
- Cost analysis: ~$0.015/GB-month storage, $4.50/million Class A operations
