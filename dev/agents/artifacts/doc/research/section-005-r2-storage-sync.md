---
section: "005"
name: "r2-storage-sync"
title: "Cloudflare R2 Storage Sync (Output Persistence)"
version: "1.1"
date: "2026-01-17"
author: "oz + claude-sonnet-4-5"
task: "Document R2 output sync: r2_sync.sh + upload_to_r2.py"
timestamp: 2025-01-17T10:30:00Z
status: completed
---

# Cloudflare R2 Storage Sync (Output Persistence)

RunPod pods are ephemeral: anything written to the container filesystem is lost on restart. This project solves output persistence by running a background daemon that watches the ComfyUI output folder and uploads new media files to Cloudflare R2 (S3-compatible object storage).

## At a Glance

| Component | Source (repo) | Runtime path (container) | Purpose |
|---|---|---|---|
| R2 sync daemon | `docker/r2_sync.sh` | `/r2_sync.sh` | Watches output directory and triggers uploads |
| R2 uploader (CLI) | `docker/upload_to_r2.py` | `/upload_to_r2.py` | Upload one or more files to R2; used by daemon |
| Startup integration | `docker/start.sh` | `/start.sh` | Starts `/r2_sync.sh` when `ENABLE_R2_SYNC=true` |
| Primary log | (created at runtime) | `/var/log/r2_sync.log` | Combined daemon + uploader logs |
| nohup init log | (created at runtime) | `/var/log/r2_sync_init.log` | `nohup` stdout/stderr for daemon process |

---

## 1) R2 Sync Daemon (`r2_sync.sh`)

**Source:** `/home/oz/projects/2025/oz/12/runpod/docker/r2_sync.sh`

### What it does

`r2_sync.sh` is a long-running Bash process that:

1. Validates prerequisites (`inotifywait`, `/upload_to_r2.py`, and required env vars)
2. Watches the ComfyUI output directory recursively using inotify
3. When a new file is fully written (`close_write`), and its extension matches a whitelist of media types, it uploads that file to R2 by calling the Python uploader in the background

### Environment variables (daemon)

| Variable | Default | Required | Notes |
|---|---:|---:|---|
| `COMFYUI_OUTPUT_DIR` | `/workspace/ComfyUI/output` | No | Overrides the watch directory |
| `R2_ACCESS_KEY_ID` | (none) | Yes | Preferred credential name |
| `R2_SECRET_ACCESS_KEY` | (none) | Yes | Preferred credential name |
| `R2_ACCESS_KEY` | (none) | Alternative | Supported fallback name |
| `R2_SECRET_KEY` | (none) | Alternative | Supported fallback name |

`ENABLE_R2_SYNC` is not read by `r2_sync.sh` directly; it is used by the container entrypoint (`start.sh`) to decide whether to start the daemon.

### Dependencies

- `inotifywait` (package: `inotify-tools`)
- `python3`
- `/upload_to_r2.py` and its Python dependency `boto3` (baked into the image via `Dockerfile`)

### File detection and filtering

The daemon listens for `close_write` events and then filters by a regex of file extensions:

```bash
WATCH_PATTERNS="\.png$|\.jpg$|\.jpeg$|\.webp$|\.mp4$|\.webm$|\.gif$|\.wav$|\.mp3$|\.flac$"
```

**Important details:**

- **Event type:** `close_write` means "file was closed after writing" (good for avoiding partial uploads)
- **Case sensitivity:** the regex is case-sensitive (e.g. `.PNG` will not match)
- **Move/rename-only writes:** files introduced via rename/move without a write-close may not trigger an upload (inotify event selection is intentionally minimal)

### Concurrency model

Each detected file starts an upload in a background subshell (`(...) &`). This allows uploads to run concurrently, but it also means:

- If many files are created quickly, many Python upload processes can run at once
- There is **no queue / throttling** (by design, currently)

### Logging

- `r2_sync.sh` prepends timestamped daemon messages and writes them to `/var/log/r2_sync.log`
- It also appends `upload_to_r2.py` stdout/stderr into the same `/var/log/r2_sync.log`

From `start.sh`, the daemon is started like:

```bash
nohup /r2_sync.sh > /var/log/r2_sync_init.log 2>&1 &
```

So you may see daemon output duplicated in both:

- `/var/log/r2_sync.log` (intended primary log)
- `/var/log/r2_sync_init.log` (nohup capture)

### Daemon source code (verbatim)

```bash
#!/bin/bash
# R2 Sync Daemon - watches ComfyUI output directory and uploads new files
#
# Author: oz
# Model: claude-opus-4-5
# Date: 2025-12-29

set -e

OUTPUT_DIR="${COMFYUI_OUTPUT_DIR:-/workspace/ComfyUI/output}"
LOG_FILE="/var/log/r2_sync.log"
UPLOAD_SCRIPT="/upload_to_r2.py"

# File patterns to watch (images, videos, audio)
WATCH_PATTERNS="\.png$|\.jpg$|\.jpeg$|\.webp$|\.mp4$|\.webm$|\.gif$|\.wav$|\.mp3$|\.flac$"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check dependencies
if ! command -v inotifywait &> /dev/null; then
    log "ERROR: inotifywait not found. Install: apt-get install inotify-tools"
    exit 1
fi

if [ ! -f "$UPLOAD_SCRIPT" ]; then
    log "ERROR: Upload script not found: $UPLOAD_SCRIPT"
    exit 1
fi

# Check R2 credentials (support both naming conventions)
R2_ACCESS="${R2_ACCESS_KEY_ID:-$R2_ACCESS_KEY}"
R2_SECRET="${R2_SECRET_ACCESS_KEY:-$R2_SECRET_KEY}"
if [ -z "$R2_ACCESS" ] || [ -z "$R2_SECRET" ]; then
    log "ERROR: R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY required"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

log "Starting R2 sync daemon"
log "Watching: $OUTPUT_DIR"

# Watch for new files and upload them
inotifywait -m -r -e close_write --format '%w%f' "$OUTPUT_DIR" 2>/dev/null | while read filepath; do
    if echo "$filepath" | grep -qE "$WATCH_PATTERNS"; then
        sleep 1  # Ensure file is fully written
        if [ -f "$filepath" ]; then
            log "New file: $filepath"
            (
                python3 "$UPLOAD_SCRIPT" "$filepath" >> "$LOG_FILE" 2>&1
                [ $? -eq 0 ] && log "Uploaded: $(basename "$filepath")" || log "FAILED: $(basename "$filepath")"
            ) &
        fi
    fi
done
```

### Known behavioral notes (from the actual code)

- **Remote key collisions are possible** if multiple files share the same filename on the same day (see uploader key format below). ComfyUI typically generates unique filenames, but custom scripts may not.
- **`set -e` nuance:** the background subshell attempts to log `FAILED:` when the Python uploader returns non-zero. With `set -e` enabled, a non-zero exit from `python3` may terminate the subshell before the `FAILED:` log line executes (the Python error output is still appended to `/var/log/r2_sync.log`). If you rely on the `FAILED:` marker, validate with real failures.

---

## 2) R2 Uploader (`upload_to_r2.py`)

**Source:** `/home/oz/projects/2025/oz/12/runpod/docker/upload_to_r2.py`

### What it does

`upload_to_r2.py` is a Python CLI tool (also used by the daemon) that uploads one or more local files to Cloudflare R2 using the S3-compatible API via `boto3`.

Key features:

- Uses `boto3.client('s3', endpoint_url=...)` against R2
- Retries failed uploads (default: 3 attempts) with exponential backoff
- Automatically switches to multipart upload for files larger than 100 MB
- Stores objects under a date-based prefix (default prefix: `outputs`)

### Environment variables (uploader)

| Variable | Default | Required | Notes |
|---|---:|---:|---|
| `R2_ENDPOINT` | hardcoded example | Yes (in practice) | Override this to your own R2 endpoint |
| `R2_BUCKET` | `runpod` | Yes | Target bucket name |
| `R2_ACCESS_KEY_ID` | (none) | Yes | Preferred credential name |
| `R2_SECRET_ACCESS_KEY` | (none) | Yes | Preferred credential name |
| `R2_ACCESS_KEY` | (none) | Alternative | Supported fallback name |
| `R2_SECRET_KEY` | (none) | Alternative | Supported fallback name |

### Remote key format (how files are organized in R2)

For a local file `/some/path/myfile.png`, the uploader generates:

```
{prefix}/{YYYY-MM-DD}/{filename}
```

Example (default prefix):

```
outputs/2026-01-18/myfile.png
```

**Important details:**

- Only `local_path.name` is used (`myfile.png`). Subdirectories are not preserved
- The date folder is computed at upload time using `datetime.now()` inside the container (timezone dependent)

### Multipart uploads (files > 100 MB)

- Threshold: `100 * 1024 * 1024` bytes
- Chunk size: `50 * 1024 * 1024` bytes per part

Operationally, a multipart upload performs multiple S3 API calls (more Class A operations than a single PUT).

### CLI usage

```bash
# Show help
python3 /upload_to_r2.py --help

# Test credentials + connectivity (does not upload)
python3 /upload_to_r2.py --test

# Upload one file
python3 /upload_to_r2.py /workspace/ComfyUI/output/my_image.png

# Upload many files
python3 /upload_to_r2.py file1.png file2.mp4 file3.wav

# Upload into a custom top-level prefix
python3 /upload_to_r2.py --prefix videos /workspace/ComfyUI/output/out.mp4

# Upload with custom prefix and test connection
python3 /upload_to_r2.py --prefix archive --test /path/to/file.png
```

### Command-line arguments reference

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `files` | positional | none | One or more files to upload |
| `--test` | flag | false | Test R2 connection without uploading |
| `--prefix` | string | `outputs` | R2 key prefix (folder name) |

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success (all files uploaded, or `--test` passed) |
| 1 | Failure (any upload failed, or `--test` failed) |

### Uploader source code (verbatim)

```python
#!/usr/bin/env python3
"""
R2 Upload Script for ComfyUI Output Sync.

Uploads files to Cloudflare R2 with retry logic and organized folder structure.
Designed for use with r2_sync.sh inotifywait daemon.

Author: oz
Model: claude-opus-4-5
Date: 2025-12-29
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
import time

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
except ImportError:
    print("[R2] Error: boto3 not installed. Run: pip install boto3")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='[R2] %(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class R2Uploader:
    """Cloudflare R2 file uploader with retry logic."""

    def __init__(self):
        self.endpoint = os.environ.get(
            'R2_ENDPOINT',
            'https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com'
        )
        self.bucket = os.environ.get('R2_BUCKET', 'runpod')
        # Support both naming conventions
        self.access_key = os.environ.get('R2_ACCESS_KEY_ID') or os.environ.get('R2_ACCESS_KEY')
        self.secret_key = os.environ.get('R2_SECRET_ACCESS_KEY') or os.environ.get('R2_SECRET_KEY')

        if not self.access_key or not self.secret_key:
            logger.error("R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY environment variables required")
            raise ValueError("Missing R2 credentials")

        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version='s3v4', retries={'max_attempts': 3, 'mode': 'adaptive'}),
            region_name='auto'
        )
        logger.info(f"R2 client ready: {self.bucket}")

    def upload_file(self, local_path: str, remote_prefix: str = "outputs", max_retries: int = 3) -> bool:
        local_path = Path(local_path)
        if not local_path.exists():
            logger.error(f"File not found: {local_path}")
            return False

        date_folder = datetime.now().strftime('%Y-%m-%d')
        remote_key = f"{remote_prefix}/{date_folder}/{local_path.name}"
        file_size = local_path.stat().st_size
        logger.info(f"Uploading: {local_path.name} ({file_size / 1024 / 1024:.2f} MB)")

        for attempt in range(1, max_retries + 1):
            try:
                if file_size > 100 * 1024 * 1024:
                    self._multipart_upload(local_path, remote_key)
                else:
                    self.client.upload_file(str(local_path), self.bucket, remote_key)
                logger.info(f"Uploaded: s3://{self.bucket}/{remote_key}")
                return True
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                logger.warning(f"Attempt {attempt}/{max_retries} failed: {error_code}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Upload failed: {e}")
                    return False
            except Exception as e:
                logger.error(f"Error: {e}")
                return False
        return False

    def _multipart_upload(self, local_path: Path, remote_key: str, chunk_size: int = 50 * 1024 * 1024):
        file_size = local_path.stat().st_size
        mpu = self.client.create_multipart_upload(Bucket=self.bucket, Key=remote_key)
        upload_id = mpu['UploadId']
        parts = []
        try:
            with open(local_path, 'rb') as f:
                part_number = 1
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    response = self.client.upload_part(
                        Bucket=self.bucket, Key=remote_key,
                        PartNumber=part_number, UploadId=upload_id, Body=data
                    )
                    parts.append({'PartNumber': part_number, 'ETag': response['ETag']})
                    logger.info(f"  Part {part_number}: {min((part_number * chunk_size / file_size) * 100, 100):.0f}%")
                    part_number += 1
            self.client.complete_multipart_upload(
                Bucket=self.bucket, Key=remote_key, UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
        except Exception as e:
            self.client.abort_multipart_upload(Bucket=self.bucket, Key=remote_key, UploadId=upload_id)
            raise

    def test_connection(self) -> bool:
        try:
            self.client.list_objects_v2(Bucket=self.bucket, MaxKeys=1)
            logger.info(f"Connection OK: {self.bucket}")
            return True
        except ClientError as e:
            logger.error(f"Connection failed: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Upload files to Cloudflare R2')
    parser.add_argument('files', nargs='*', help='Files to upload')
    parser.add_argument('--test', action='store_true', help='Test R2 connection')
    parser.add_argument('--prefix', default='outputs', help='R2 key prefix')
    args = parser.parse_args()

    try:
        uploader = R2Uploader()
    except ValueError:
        sys.exit(1)

    if args.test:
        sys.exit(0 if uploader.test_connection() else 1)

    if not args.files:
        parser.print_help()
        sys.exit(1)

    success = sum(1 for f in args.files if uploader.upload_file(f, args.prefix))
    logger.info(f"Complete: {success}/{len(args.files)}")
    sys.exit(0 if success == len(args.files) else 1)


if __name__ == '__main__':
    main()
```

---

## 3) Configuration (Endpoint, Bucket, Credentials, Secrets)

### Where configuration is set

**Image build defaults (Dockerfile):**

`docker/Dockerfile` sets safe defaults for R2 syncing:

```dockerfile
ENV ENABLE_R2_SYNC="false"
ENV R2_BUCKET="runpod"
ENV R2_ENDPOINT="https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com"
ENV R2_ACCESS_KEY_ID=""
ENV R2_SECRET_ACCESS_KEY=""
```

**Runtime enablement (start.sh):**

`docker/start.sh` starts the daemon only when:

```bash
ENABLE_R2_SYNC=true
```

### Local development (Docker Compose)

Use `docker/.env` (copy from `docker/.env.example`) and set:

```dotenv
ENABLE_R2_SYNC=true
R2_ENDPOINT=https://your-account.eu.r2.cloudflarestorage.com
R2_BUCKET=runpod
R2_ACCESS_KEY_ID=your_r2_access_key_here
R2_SECRET_ACCESS_KEY=your_r2_secret_key_here
```

Then run:

```bash
cd docker
docker compose up -d --build
```

### RunPod production (recommended: secrets)

Do not hardcode secrets in templates. Use RunPod Secrets and inject them:

```text
R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}
R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}
```

### RunPod Pod Creation Command

```bash
~/.local/bin/runpodctl create pod \
  --name "hearmeman-r2-$(date +%H%M)" \
  --imageName "ghcr.io/oz/hearmeman-extended:latest" \
  --gpuType "NVIDIA GeForce RTX 4090" \
  --gpuCount 1 \
  --containerDiskSize 20 \
  --volumeSize 100 \
  --secureCloud \
  --ports "8188/http" \
  --env "ENABLE_R2_SYNC=true" \
  --env "R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com" \
  --env "R2_BUCKET=runpod" \
  --env "R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}" \
  --env "R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}"
```

### Environment variables summary

| Variable | Default | Required | Type | Description |
|----------|---------|----------|------|-------------|
| `ENABLE_R2_SYNC` | `false` | No | Visible | Enable R2 sync daemon |
| `R2_ENDPOINT` | (none) | Yes | Visible | R2 endpoint URL |
| `R2_BUCKET` | `runpod` | No | Visible | Target bucket name |
| `R2_ACCESS_KEY_ID` | (none) | Yes | **Secret** | R2 Access Key ID |
| `R2_SECRET_ACCESS_KEY` | (none) | Yes | **Secret** | R2 Secret Access Key |
| `COMFYUI_OUTPUT_DIR` | `/workspace/ComfyUI/output` | No | Visible | Watch directory |

---

## 4) File Organization in R2

### Default structure

By default, all uploads go to:

```
outputs/YYYY-MM-DD/<filename>
```

Example bucket layout:

```
s3://runpod/
└── outputs/
    ├── 2026-01-17/
    │   ├── ComfyUI_00001_.png
    │   └── tts_hello.wav
    └── 2026-01-18/
        ├── ComfyUI_00002_.png
        └── wan_video.mp4
```

### Custom prefix usage

If you upload with `--prefix videos`, the layout becomes:

```
videos/YYYY-MM-DD/<filename>
```

### Supported file types

| Category | Extensions | Use Case |
|----------|------------|----------|
| Images | `.png`, `.jpg`, `.jpeg`, `.webp` | Generated images, renders |
| Video | `.mp4`, `.webm` | T2V/I2V outputs |
| Animation | `.gif` | Short animations |
| Audio | `.wav`, `.mp3`, `.flac` | TTS voice outputs |

---

## 5) Operations: Monitoring, Manual Uploads, Troubleshooting

### Check logs (inside container)

```bash
# Follow primary log
tail -f /var/log/r2_sync.log

# Follow init log
tail -f /var/log/r2_sync_init.log

# Check for errors
grep -i error /var/log/r2_sync.log

# View recent entries
tail -50 /var/log/r2_sync.log
```

### Test connection

```bash
python3 /upload_to_r2.py --test
# Returns exit code 0 on success, 1 on failure
```

### Manually upload files

```bash
# Upload a single file
python3 /upload_to_r2.py /workspace/ComfyUI/output/some_output.png

# Upload multiple files
python3 /upload_to_r2.py file1.png file2.mp4 file3.wav

# Upload with custom prefix
python3 /upload_to_r2.py --prefix videos /path/to/video.mp4

# Test + upload
python3 /upload_to_r2.py --test /path/to/test.png
```

### Check daemon status

```bash
# Check if daemon is running
ps aux | grep r2_sync

# View process details
ps aux | grep -E "r2_sync|inotifywait"

# Kill and restart
pkill -f r2_sync.sh
nohup /r2_sync.sh > /var/log/r2_sync.log 2>&1 &
```

### Using AWS CLI (alternative)

```bash
# List R2 bucket contents
aws s3 ls s3://runpod/outputs/ \
  --endpoint-url https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com

# Upload file with AWS CLI
aws s3 cp /workspace/ComfyUI/output/image.png s3://runpod/outputs/2025-01-17/ \
  --endpoint-url https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com \
  --acl public-read

# Download from R2
aws s3 cp s3://runpod/outputs/2025-01-17/image.png ./ \
  --endpoint-url https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com
```

### Common failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| `inotifywait not found` | Missing `inotify-tools` | Install via OS package manager (already included in `docker/Dockerfile`) |
| `Missing R2 credentials` | Env vars not set in runtime | Confirm RunPod secrets injection / `docker/.env` |
| `NoSuchBucket` / `AccessDenied` | Wrong bucket name or token lacks access | Verify `R2_BUCKET`, update R2 token permissions |
| Uploads never trigger | Output path mismatch or event type mismatch | Confirm output folder; consider adding more inotify events if needed |
| `boto3 not installed` | Python package missing | Install: `pip install boto3` |
| Upload timeout on large files | Network issues, >100MB | Script auto-retries with exponential backoff |

---

## 6) Security Best Practices

- **Use RunPod Secrets** for `R2_ACCESS_KEY_ID` and `R2_SECRET_ACCESS_KEY` in production
- **Do not commit secrets** in `docker/.env` or any `.env` file. Use `docker/.env.example` as the only committed reference
- **Least privilege:** create a dedicated R2 API token/key restricted to the target bucket and only the operations you need (upload + optional list for testing)
- **No delete permission** for the sync token unless you also implement automated retention and you accept the risk
- **Rotate credentials** and re-test with `python3 /upload_to_r2.py --test` after rotation
- **Log hygiene:** uploader logs do not print credentials, but logs can contain filenames and paths - treat them as potentially sensitive

### R2 bucket policy example

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowRunPodUpload",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:user/runpod-uploader"
      },
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::runpod/*"
    },
    {
      "Sid": "AllowPublicRead",
      "Effect": "Allow",
      "Principal": "*",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::runpod/public/*"
    }
  ]
}
```

---

## 7) Storage Estimates and Cost Analysis

### Typical output sizes

| Output type | Typical parameters | Typical size |
|---|---|---:|
| Image (PNG) | 768x768 | 1-2 MB |
| Image (PNG) | 1024x1024 | 3-6 MB |
| Image (WebP) | 768x768 | 0.5-1 MB |
| Video (WAN) | 720p, ~5s | 20-50 MB |
| Video (WAN) | 720p, ~10s | 40-100 MB |
| Audio (WAV) | TTS line | 0.5-2 MB |
| Audio (MP3) | TTS line | 0.1-0.5 MB |

### Capacity examples

| Stored data | ~2 MB images | ~35 MB videos |
|---:|---:|---:|
| 1 GB | ~500 images | ~29 videos |
| 10 GB | ~5,000 images | ~290 videos |
| 50 GB | ~25,000 images | ~1,450 videos |

### Cloudflare R2 pricing model

R2 pricing can change; treat the numbers below as an **estimation framework**:

| Metric | Price | Notes |
|--------|-------|-------|
| Storage | $0.015 / GB-month | First 10GB often free |
| Class A ops (PUT, COPY, POST, LIST) | $4.50 / million | |
| Class B ops (GET, SELECT) | $0.36 / million | |
| Data Egress | $0 | Free to Cloudflare CDN |
| Data Retrieval | $0.01 / GB | First 10GB/month free |

### Quick cost tables

**Storage-only (at $0.015 / GB-month)**

| Stored GB | Est. storage cost/month |
|---:|---:|
| 10 | $0.15 |
| 50 | $0.75 |
| 100 | $1.50 |
| 500 | $7.50 |
| 1,000 | $15.00 |

**Class A operations (uploads/PUT, at $4.50 / million)**

| Uploads/month | Est. Class A cost |
|---:|---:|
| 1,000 | $0.0045 |
| 100,000 | $0.45 |
| 1,000,000 | $4.50 |

### Estimation formulas

```
StorageCost = stored_GB * 0.015
ClassACost = (uploads / 1,000,000) * 4.50
```

For large files uploaded via multipart, Class A operations increase by:

```
MultipartClassA = 1 (create) + ceil(file_size / 50MB) (parts) + 1 (complete)
```

### Monthly scenario examples

**Light usage**

| Item | Count | Data |
|---|---:|---:|
| Images | 100 | ~0.2 GB |
| Videos | 0 | 0 GB |
| Audio | 50 | ~0.05 GB |
| Total stored |  | ~0.25 GB |

Estimated cost: `0.25 * $0.015 = $0.004/month`

**Medium usage**

| Item | Count | Data |
|---|---:|---:|
| Images | 1,000 | ~2 GB |
| Videos | 100 | ~3.5 GB |
| Audio | 500 | ~0.5 GB |
| Total stored |  | ~6 GB |

Estimated cost: `6 * $0.015 = $0.09/month`

**Heavy usage**

| Item | Count | Data |
|---|---:|---:|
| Images | 10,000 | ~20 GB |
| Videos | 1,000 | ~35 GB |
| Audio | 2,000 | ~2 GB |
| Total stored |  | ~57 GB |

Estimated cost: `57 * $0.015 = $0.86/month`

### Retention planning

The provided scripts **do not** implement retention/cleanup. If you keep everything forever, storage costs scale with time.

A practical approach is a rolling retention window. If you generate `D` GB/day and retain for `N` days:

```
StoredGB = D * N
```

Example:
- 2 GB/day for 30 days -> ~60 GB stored -> `60 * $0.015 = $0.90/month`

---

## 8) Quick Reference

### Environment variables (one-liner)

```bash
export R2_ENDPOINT="https://your-account.eu.r2.cloudflarestorage.com"
export R2_BUCKET="runpod"
export R2_ACCESS_KEY_ID="your_access_key"
export R2_SECRET_ACCESS_KEY="your_secret_key"
export ENABLE_R2_SYNC="true"
```

### Common commands

```bash
# Start daemon manually
/r2_sync.sh

# Upload file
python3 /upload_to_r2.py /path/to/file.png

# Test connection
python3 /upload_to_r2.py --test

# List R2 contents
aws s3 ls s3://runpod/outputs/ --endpoint-url $R2_ENDPOINT

# Download from R2
aws s3 cp s3://runpod/outputs/2025-01-17/image.png ./ --endpoint-url $R2_ENDPOINT
```

### File locations

| File | Path |
|------|------|
| R2 Sync Daemon | `/r2_sync.sh` (in container) |
| Upload Script | `/upload_to_r2.py` (in container) |
| Daemon Log | `/var/log/r2_sync.log` |
| Init Log | `/var/log/r2_sync_init.log` |
| Output Directory | `/workspace/ComfyUI/output` |

---

## References

- [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)
- [RunPod Secrets Documentation](https://docs.runpod.io/pods/templates/secrets)
- [boto3 S3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [inotify-tools Documentation](https://github.com/inotify-tools/inotify-tools/wiki)
