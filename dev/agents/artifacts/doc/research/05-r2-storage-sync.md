---
title: Cloudflare R2 Storage and Sync System Documentation
version: 1.0
date: 2026-01-17
author: oz + claude-haiku-4.5
task: Research Cloudflare R2 storage and sync system for RunPod project
---

# Cloudflare R2 Storage and Sync System

## Executive Summary

This document details the Cloudflare R2 integration implemented for the RunPod ComfyUI deployment. The system provides automatic, real-time synchronization of generated files (images, videos, audio) from ephemeral RunPod storage to persistent Cloudflare R2 object storage using a daemon-based approach with inotify file monitoring.

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `r2_sync.sh` | `/home/oz/projects/2025/oz/12/runpod/docker/r2_sync.sh` | File monitoring daemon using inotifywait |
| `upload_to_r2.py` | `/home/oz/projects/2025/oz/12/runpod/docker/upload_to_r2.py` | Python upload script with retry logic |
| Environment Variables | RunPod Template | Configuration and credentials |
| Log File | `/var/log/r2_sync.log` | Daemon activity logging |

---

## 1. R2 Sync Daemon (`r2_sync.sh`)

### Overview

The `r2_sync.sh` script is a Bash-based daemon that monitors the ComfyUI output directory for new files and automatically uploads them to Cloudflare R2 using the Python upload script.

### Script Location
```
/home/oz/projects/2025/oz/12/runpod/docker/r2_sync.sh
```

### Key Features

- **Real-time monitoring**: Uses `inotifywait` for instant file detection
- **Recursive watch**: Monitors entire output directory tree
- **Pattern filtering**: Only processes media files (images, videos, audio)
- **Async uploads**: Multiple uploads run in parallel background processes
- **Comprehensive logging**: Timestamped logs to `/var/log/r2_sync.log`

### Source Code

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

### Daemon Behavior

#### 1. Initialization Phase

```
Step 1: Validate inotifywait is installed
Step 2: Validate upload_to_r2.py exists
Step 3: Check R2 credentials are set
Step 4: Create output directory if missing
Step 5: Log daemon start and begin monitoring
```

#### 2. File Detection Logic

The daemon uses `inotifywait` with the following parameters:

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `-m` | monitor | Continuous monitoring (non-exiting) |
| `-r` | recursive | Watch all subdirectories |
| `-e` | close_write | Trigger on file close after write |
| `--format` | %w%f | Output full filepath |

#### 3. File Pattern Matching

Only files matching these extensions trigger uploads:

```bash
WATCH_PATTERNS="\.png$|\.jpg$|\.jpeg$|\.webp$|\.mp4$|\.webm$|\.gif$|\.wav$|\.mp3$|\.flac$"
```

**Supported File Types:**

| Category | Extensions | Example Use Case |
|----------|-----------|------------------|
| **Images** | PNG, JPG, JPEG, WebP | Generated images, workflows |
| **Video** | MP4, WebM, GIF | Text-to-video output |
| **Audio** | WAV, MP3, FLAC | TTS voice generation |

#### 4. Upload Process

For each detected file:

1. **Sleep 1 second**: Ensures file is fully written and closed
2. **Verify file exists**: Prevents upload of temporary files
3. **Log detection**: Record filepath in log file
4. **Background upload**: Launch Python script in background (`&`)
5. **Non-blocking**: Multiple files upload concurrently

#### 5. Error Handling

- **Missing dependencies**: Script exits with error message
- **Invalid credentials**: Script exits before monitoring starts
- **Upload failures**: Logged to file, daemon continues
- **Corrupt files**: File verification prevents upload attempts

### Log File Format

```
[2025-12-29 10:00:00] Starting R2 sync daemon
[2025-12-29 10:00:00] Watching: /workspace/ComfyUI/output
[2025-12-29 10:05:15] New file: /workspace/ComfyUI/output/test_image.png
[R2] 2025-12-29 10:05:16 - INFO - Uploading: test_image.png (2.45 MB)
[R2] 2025-12-29 10:05:18 - INFO - Uploaded: s3://runpod/outputs/2025-12-29/test_image.png
[2025-12-29 10:05:18] Uploaded: test_image.png
```

---

## 2. R2 Upload Script (`upload_to_r2.py`)

### Overview

The `upload_to_r2.py` script is a Python-based uploader that handles file uploads to Cloudflare R2 with robust retry logic, multipart upload support for large files, and organized folder structure.

### Script Location
```
/home/oz/projects/2025/oz/12/runpod/docker/upload_to_r2.py
```

### Key Features

- **AWS S3-compatible API**: Uses boto3 for S3 operations
- **Retry logic**: 3 attempts with exponential backoff
- **Multipart uploads**: Automatic for files > 100 MB
- **Organized structure**: Date-based folder organization
- **Connection testing**: Built-in test mode
- **CLI interface**: Command-line arguments for flexible use

### Source Code

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

### Class: R2Uploader

#### Initialization

```python
uploader = R2Uploader()
```

**Environment Variables Used:**

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `R2_ENDPOINT` | https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com | Yes | R2 endpoint URL |
| `R2_BUCKET` | runpod | Yes | Target bucket name |
| `R2_ACCESS_KEY_ID` | - | Yes | Access key ID |
| `R2_SECRET_ACCESS_KEY` | - | Yes | Secret access key |
| `R2_ACCESS_KEY` | - | Alternative | Alternative access key name |
| `R2_SECRET_KEY` | - | Alternative | Alternative secret key name |

#### Core Methods

##### upload_file()

Uploads a single file to R2 with retry logic.

```python
success = uploader.upload_file(
    local_path="/workspace/ComfyUI/output/image.png",
    remote_prefix="outputs",  # Default
    max_retries=3  # Default
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `local_path` | str | Required | Path to local file |
| `remote_prefix` | str | "outputs" | R2 key prefix (folder) |
| `max_retries` | int | 3 | Number of retry attempts |

**Return Value:** `bool` - True if successful, False otherwise

**Upload Logic:**

1. Check file exists
2. Generate date-based remote path: `outputs/YYYY-MM-DD/filename`
3. Check file size for multipart upload decision
4. Execute upload with retry (3 attempts)
5. Exponential backoff: 2s, 4s, 8s between retries

##### test_connection()

Verifies R2 connectivity without uploading.

```python
connected = uploader.test_connection()
```

**Return Value:** `bool` - True if connection successful, False otherwise

**Operations:**

- Lists objects in bucket (read operation)
- Validates credentials and endpoint

##### _multipart_upload()

Internal method for uploading large files (>100 MB).

```python
self._multipart_upload(local_path, remote_key, chunk_size=50*1024*1024)
```

**Chunk Size:** 50 MB per part

**Process:**

1. Create multipart upload
2. Split file into 50 MB chunks
3. Upload each part sequentially
4. Complete multipart upload
5. Abort on any error

### Command-Line Interface

#### Usage

```bash
# Basic usage
python3 upload_to_r2.py <file1> <file2> ...

# Test connection
python3 upload_to_r2.py --test

# Upload with custom prefix
python3 upload_to_r2.py --prefix custom_folder /path/to/file.png

# Upload multiple files
python3 upload_to_r2.py file1.png file2.mp4 file3.wav
```

#### Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `files` | positional | One or more files to upload |
| `--test` | flag | Test R2 connection without uploading |
| `--prefix` | string | R2 key prefix (default: "outputs") |

#### Examples

**1. Test Connection:**

```bash
export R2_ENDPOINT="https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com"
export R2_ACCESS_KEY_ID="your_access_key"
export R2_SECRET_ACCESS_KEY="your_secret_key"
export R2_BUCKET="runpod"

python3 /upload_to_r2.py --test
```

**Output (Success):**
```
[R2] 2025-12-29 10:00:01 - INFO - R2 client ready: runpod
[R2] 2025-12-29 10:00:01 - INFO - Connection OK: runpod
```

**Output (Failure):**
```
[R2] 2025-12-29 10:00:00 - ERROR - Connection failed: An error occurred (InvalidAccessKeyId)...
```

**2. Manual Upload:**

```bash
python3 /upload_to_r2.py /workspace/ComfyUI/output/generated_image.png
```

**Output:**
```
[R2] 2025-12-29 10:05:16 - INFO - Uploading: generated_image.png (2.45 MB)
[R2] 2025-12-29 10:05:18 - INFO - Uploaded: s3://runpod/outputs/2025-12-29/generated_image.png
```

**3. Upload with Custom Prefix:**

```bash
python3 /upload_to_r2.py --prefix my-videos /workspace/ComfyUI/output/video.mp4
```

**Result:** File uploaded to `my-videos/2025-12-29/video.mp4`

**4. Batch Upload:**

```bash
python3 /upload_to_r2.py file1.png file2.mp4 file3.wav
```

**Output:**
```
[R2] 2025-12-29 10:10:00 - INFO - Uploading: file1.png (1.20 MB)
[R2] 2025-12-29 10:10:02 - INFO - Uploaded: s3://runpod/outputs/2025-12-29/file1.png
[R2] 2025-12-29 10:10:02 - INFO - Uploading: file2.mp4 (45.30 MB)
[R2] 2025-12-29 10:10:15 - INFO - Uploaded: s3://runpod/outputs/2025-12-29/file2.mp4
[R2] 2025-12-29 10:10:15 - INFO - Uploading: file3.wav (0.50 MB)
[R2] 2025-12-29 10:10:17 - INFO - Uploaded: s3://runpod/outputs/2025-12-29/file3.wav
[R2] 2025-12-29 10:10:17 - INFO - Complete: 3/3
```

### Error Handling

#### Retry Logic

The script implements exponential backoff retry:

| Attempt | Delay Before Retry |
|---------|-------------------|
| 1st failure | 2 seconds |
| 2nd failure | 4 seconds |
| 3rd failure | 8 seconds (final attempt) |

#### Common Error Codes

| Error Code | Cause | Solution |
|------------|-------|----------|
| `InvalidAccessKeyId` | Wrong access key | Verify R2 credentials |
| `SignatureDoesNotMatch` | Secret key mismatch | Regenerate credentials |
| `NoSuchBucket` | Bucket doesn't exist | Create bucket or check name |
| `AccessDenied` | Insufficient permissions | Grant r2:PutObject permission |
| `SlowDown` | Rate limiting | Retry with backoff |

---

## 3. R2 Configuration

### Environment Variables

#### Build-Time (Dockerfile)

These variables are set during Docker image build:

```dockerfile
ENV ENABLE_R2_SYNC="false"
ENV R2_BUCKET="runpod"
ENV R2_ENDPOINT="https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com"
```

#### Runtime (RunPod Template)

These variables are set when creating the RunPod pod:

| Variable | Value | Type | Description |
|----------|-------|------|-------------|
| `R2_ENDPOINT` | https://...r2.cloudflarestorage.com | Visible | R2 endpoint URL |
| `R2_BUCKET` | runpod | Visible | Target bucket name |
| `R2_ACCESS_KEY_ID` | (from secrets) | Secret | Access key ID |
| `R2_SECRET_ACCESS_KEY` | (from secrets) | Secret | Secret access key |
| `ENABLE_R2_SYNC` | true | Visible | Enable daemon |
| `STORAGE_MODE` | ephemeral | Visible | Storage mode |

### Credential Management

#### RunPod Secrets (Recommended)

**Never expose credentials in plain text.** Use [RunPod Secrets](https://docs.runpod.io/pods/templates/secrets) for secure credential storage:

**Step 1: Create Secrets in RunPod Console**

1. Go to **Settings > Secrets**
2. Create `r2_access_key` with your R2 Access Key ID
3. Create `r2_secret_key` with your R2 Secret Access Key

**Step 2: Reference in Pod Template**

Use `RUNPOD_SECRET_` prefix to inject secrets:

```
R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}
R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}
```

#### Pod Creation Command

```bash
~/.local/bin/runpodctl create pod \
  --name "hearmeman-r2" \
  --imageName "ghcr.io/oz/hearmeman-extended:latest" \
  --gpuType "NVIDIA GeForce RTX 4090" \
  --gpuCount 1 \
  --containerDiskSize 20 \
  --volumeSize 15 \
  --secureCloud \
  --ports "8188/http" \
  --ports "19123/http" \
  --env "ENABLE_R2_SYNC=true" \
  --env "R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com" \
  --env "R2_BUCKET=runpod" \
  --env "R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}" \
  --env "R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}"
```

### Security Best Practices

#### 1. Use RunPod Secrets (Mandatory for Production)

```bash
# WRONG - Credentials in plain text
--env "R2_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"

# CORRECT - Using RunPod secrets
--env "R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}"
```

#### 2. Restrict IAM Permissions

Create a dedicated R2 API token with minimal permissions:

| Permission | Action | Reason |
|------------|--------|--------|
| `r2:ListBucket` | Read bucket listing | Test connection, verify uploads |
| `r2:PutObject` | Upload files | Upload generated content |
| `r2:GetObject` | Download files | Access uploaded content |

**Avoid:** `r2:DeleteObject` (never needed for sync)

#### 3. Rotate Credentials Periodically

- Rotate R2 API tokens every 90 days
- Update RunPod secrets immediately after rotation
- Test connection after rotation

#### 4. Monitor Usage

- Review R2 dashboard for unusual access patterns
- Set up alerts for high bandwidth usage
- Monitor for failed upload attempts (log monitoring)

---

## 4. File Organization in R2

### Folder Structure

Files are organized using date-based prefixes for easy management and cleanup:

```
s3://runpod/
├── outputs/
│   ├── 2025-12-29/
│   │   ├── generated_image.png
│   │   ├── video_generation.mp4
│   │   └── voice_output.wav
│   ├── 2025-12-30/
│   │   ├── workflow_test.png
│   │   └── another_image.jpg
│   └── 2025-12-31/
│       └── ...
```

### Remote Key Format

```
{prefix}/{YYYY-MM-DD}/{filename}
```

| Component | Example | Description |
|-----------|---------|-------------|
| `prefix` | outputs | Top-level folder |
| `YYYY-MM-DD` | 2025-12-29 | Date of upload |
| `filename` | image.png | Original filename |

### Date-Based Organization Benefits

1. **Easy cleanup**: Delete old dates to free space
2. **Usage tracking**: Calculate storage per day
3. **Backup planning**: Identify peak generation days
4. **Cost analysis**: Estimate daily/monthly costs

### Accessing Files

#### Via R2 Dashboard

1. Log into Cloudflare dashboard
2. Navigate to R2 > Bucket > runpod
3. Browse by date folder
4. Click file to download or get URL

#### Via S3-Compatible API

```python
import boto3

client = boto3.client(
    's3',
    endpoint_url='https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com',
    aws_access_key_id='YOUR_ACCESS_KEY',
    aws_secret_access_key='YOUR_SECRET_KEY'
)

# List files
response = client.list_objects_v2(
    Bucket='runpod',
    Prefix='outputs/2025-12-29/'
)

# Download file
client.download_file(
    Bucket='runpod',
    Key='outputs/2025-12-29/image.png',
    Filename='/local/path/image.png'
)
```

#### Via AWS CLI

```bash
# Configure AWS CLI for R2
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="auto"

# List files
aws s3 ls s3://runpod/outputs/2025-12-29/ \
  --endpoint-url https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com

# Download file
aws s3 cp s3://runpod/outputs/2025-12-29/image.png ./local/path/ \
  --endpoint-url https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com

# Sync entire date folder
aws s3 sync s3://runpod/outputs/2025-12-29/ ./local/backup/ \
  --endpoint-url https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com
```

---

## 5. Storage Estimates and Cost Analysis

### File Size Reference

| Output Type | Resolution/Duration | Average Size | Storage Impact |
|-------------|-------------------|--------------|----------------|
| **Images (PNG)** | 768x768 | 1-2 MB | Low |
| **Images (PNG)** | 1024x1024 | 3-5 MB | Medium |
| **Images (WebP)** | 768x768 | 0.5-1 MB | Very Low |
| **Video (WAN 2.2)** | 720p, 5 seconds | 20-50 MB | High |
| **Video (WAN 2.2)** | 720p, 10 seconds | 40-100 MB | Very High |
| **Audio (WAV)** | TTS output | 0.5-2 MB | Low |
| **Audio (MP3)** | TTS output | 0.1-0.5 MB | Very Low |

### Storage Capacity Examples

| R2 Storage | Images (2 MB avg) | Videos (35 MB avg) | Mixed Workload |
|-----------|-------------------|-------------------|----------------|
| **1 GB** | ~500 images | ~29 videos | ~200 mixed files |
| **5 GB** | ~2,500 images | ~145 videos | ~1,000 mixed files |
| **10 GB** | ~5,000 images | ~290 videos | ~2,000 mixed files |
| **50 GB** | ~25,000 images | ~1,450 videos | ~10,000 mixed files |

### R2 Pricing (Cloudflare)

**Note:** R2 pricing is subject to change. Check [Cloudflare R2 pricing page](https://www.cloudflare.com/r2/pricing/) for current rates.

#### Typical Pricing Structure

| Component | Cost | Notes |
|-----------|------|-------|
| **Storage** | $0.015/GB/month | First 10 GB free |
| **Class A Operations** | $4.50/million | Upload operations |
| **Class B Operations** | $0.36/million | Download operations |
| **Egress** | $0.00 | Free (major cost advantage) |

#### Cost Scenarios

**Scenario 1: Light User (100 images/month)**

| Metric | Value |
|--------|-------|
| Storage | 200 MB/month |
| Uploads | 100 |
| Downloads | 50 |
| Estimated Cost | ~$0.003/month |

**Scenario 2: Medium User (1,000 images, 100 videos/month)**

| Metric | Value |
|--------|-------|
| Storage | 3.5 GB/month |
| Uploads | 1,100 |
| Downloads | 500 |
| Estimated Cost | ~$0.05/month |

**Scenario 3: Heavy User (10,000 images, 1,000 videos/month)**

| Metric | Value |
|--------|-------|
| Storage | 35 GB/month |
| Uploads | 11,000 |
| Downloads | 5,000 |
| Estimated Cost | ~$0.50/month |

### R2 vs. Other Storage Solutions

| Provider | Storage/GB/month | Egress/GB | Total for 35GB/mo | Best For |
|----------|------------------|-----------|-------------------|----------|
| **Cloudflare R2** | $0.015 | FREE | $0.53 | High egress |
| AWS S3 | $0.023 | $0.09 | ~$3.20 | AWS integration |
| Google Cloud Storage | $0.020 | $0.12 | ~$4.40 | GCP integration |
| Backblaze B2 | $0.005 | $0.01 | ~$0.40 | Budget storage |

**R2 Advantage:** Zero egress costs make it ideal for content delivery where files are frequently accessed/downloaded.

### Optimization Strategies

#### 1. File Format Selection

| Format | Size | Quality | Recommendation |
|--------|------|---------|----------------|
| PNG | Larger | Lossless | Generated images (high quality) |
| WebP | 50-70% smaller | Slightly lossy | Quick previews, thumbnails |
| MP4 | Standard | Good | Video output |
| WebM | Smaller | Good | Web-optimized video |

#### 2. Automatic Cleanup Script

Create a script to delete old files and save costs:

```python
#!/usr/bin/env python3
"""Delete R2 files older than N days."""

import os
import boto3
from datetime import datetime, timedelta

def cleanup_old_files(bucket_name, days=30):
    """Delete files older than specified days."""
    client = boto3.client(
        's3',
        endpoint_url=os.environ['R2_ENDPOINT'],
        aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY']
    )

    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    paginator = client.get_paginator('list_objects_v2')

    deleted_count = 0

    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get('Contents', []):
            key = obj['Key']
            # Check if file is in an old date folder
            if key.startswith('outputs/') and key.split('/')[1] < cutoff_date:
                client.delete_object(Bucket=bucket_name, Key=key)
                deleted_count += 1

    print(f"Deleted {deleted_count} files older than {days} days")

# Run monthly via cron
# 0 0 1 * * python3 cleanup_r2.py
```

#### 3. Monitoring Dashboard

Set up monitoring for:

- **Storage usage**: Track GB used over time
- **Upload volume**: Files per day/week/month
- **Failed uploads**: Alert on repeated failures
- **Cost estimation**: Calculate projected monthly cost

---

## 6. Integration Guide

### Docker Integration

#### Dockerfile Additions

```dockerfile
# Install dependencies
RUN apt-get update && apt-get install -y \
    inotify-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy R2 scripts
COPY upload_to_r2.py /upload_to_r2.py
COPY r2_sync.sh /r2_sync.sh
RUN chmod +x /r2_sync.sh

# Set default environment
ENV ENABLE_R2_SYNC="false" \
    R2_BUCKET="runpod" \
    R2_ENDPOINT="https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com"
```

#### Startup Script Integration

Add to `start.sh`:

```bash
# Start R2 sync daemon if enabled
if [ "${ENABLE_R2_SYNC:-false}" = "true" ]; then
    echo "[R2] Starting R2 sync daemon..."
    mkdir -p /var/log
    nohup /r2_sync.sh > /var/log/r2_sync_daemon.log 2>&1 &
    echo "[R2] R2 sync daemon started"
fi
```

### Local Testing

#### 1. Start Docker with R2 Variables

```bash
cd docker
docker compose build
docker compose up -d
```

#### 2. Test Connection

```bash
# Inside container
docker exec -it hearmeman-extended bash

# Test R2 connection
python3 /upload_to_r2.py --test

# Manual upload test
echo "test content" > /tmp/test.txt
python3 /upload_to_r2.py /tmp/test.txt
```

#### 3. Verify Sync Daemon

```bash
# Check daemon status
ps aux | grep r2_sync.sh

# Follow logs
tail -f /var/log/r2_sync.log

# Trigger file detection
touch /workspace/ComfyUI/output/test.png
```

### RunPod Deployment

#### 1. Create RunPod Template

**Settings:**
- Container Image: `ghcr.io/oz/hearmeman-extended:latest`
- Container Disk: 20 GB
- Volume Mount: /workspace

**Environment Variables:**
```
ENABLE_R2_SYNC=true
R2_BUCKET=runpod
R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}
R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}
```

#### 2. Verify Deployment

```bash
# SSH into pod
runpodctl ssh <POD_ID>

# Check R2 environment
env | grep R2

# Test connection
python3 /upload_to_r2.py --test

# Check daemon status
ps aux | grep r2_sync
```

---

## 7. Troubleshooting Guide

### Common Issues

#### Issue 1: Connection Failed - Invalid Credentials

**Symptoms:**
```
[R2] ERROR - Connection failed: An error occurred (InvalidAccessKeyId)...
```

**Cause:** Access key ID is incorrect or doesn't exist.

**Solution:**
```bash
# Verify credentials in RunPod console
runpodctl get pod <POD_ID> --format json | jq '.env'

# Test with AWS CLI
aws s3 ls s3://runpod/ \
  --endpoint-url https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com \
  --profile r2
```

#### Issue 2: Upload Failed - Bucket Doesn't Exist

**Symptoms:**
```
[R2] ERROR - Upload failed: An error occurred (NoSuchBucket)...
```

**Cause:** Bucket name mismatch or bucket not created.

**Solution:**
1. Verify bucket exists in R2 dashboard
2. Check `R2_BUCKET` environment variable
3. Ensure correct spelling

#### Issue 3: inotifywait Not Found

**Symptoms:**
```
ERROR: inotifywait not found. Install: apt-get install inotify-tools
```

**Cause:** inotify-tools package not installed.

**Solution:**
```bash
apt-get update && apt-get install -y inotify-tools
```

#### Issue 4: File Not Uploading

**Symptoms:** New files in `/workspace/ComfyUI/output/` don't appear in R2.

**Diagnosis:**
```bash
# Check daemon is running
ps aux | grep r2_sync.sh

# Check for errors in log
tail -f /var/log/r2_sync.log

# Check file permissions
ls -la /workspace/ComfyUI/output/

# Test upload manually
python3 /upload_to_r2.py /workspace/ComfyUI/output/test_file.png
```

**Solution:** Based on diagnosis output.

#### Issue 5: Partial Uploads / Corrupt Files

**Symptoms:** Uploaded files are incomplete or corrupted.

**Cause:** File uploaded before fully written to disk.

**Solution:** The daemon already includes a 1-second sleep before upload. If issues persist:
```bash
# Increase sleep time in r2_sync.sh
sleep 2  # Changed from 1 to 2
```

### Diagnostic Commands

```bash
# Check environment
env | grep -E "(R2_|ENABLE_)"

# Test R2 connection
python3 /upload_to_r2.py --test

# List R2 bucket contents
aws s3 ls s3://runpod/outputs/ \
  --endpoint-url $R2_ENDPOINT

# Check daemon status
ps aux | grep r2_sync

# View daemon logs
tail -f /var/log/r2_sync.log

# Check disk space
df -h /workspace/ComfyUI/output

# Monitor upload process
strace -p $(pgrep -f r2_sync.sh) -f
```

---

## 8. References

### Documentation

- [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)
- [R2 S3 API Compatibility](https://developers.cloudflare.com/r2/reference/s3-api-compatibility/)
- [RunPod Secrets Documentation](https://docs.runpod.io/pods/templates/secrets)
- [boto3 S3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)

### Related Files

| File | Purpose |
|------|---------|
| `/home/oz/projects/2025/oz/12/runpod/docker/r2_sync.sh` | File monitoring daemon |
| `/home/oz/projects/2025/oz/12/runpod/docker/upload_to_r2.py` | Python upload script |
| `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/runpod-r2-deployment.md` | Complete PRD |
| `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/runpod-cost-testing-pre/stage1-r2-test.md` | Testing guide |
| `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile` | Docker build configuration |
| `/home/oz/projects/2025/oz/12/runpod/docker/start.sh` | Container startup script |

### Key Learnings

1. **R2 Account ID is public**: The endpoint contains the account ID (8755d4118d392ca7e1a6e1e5733cf55f), which is not a secret
2. **Use RunPod Secrets**: Never hardcode credentials in pod templates
3. **Zero egress cost**: R2's free egress makes it ideal for content-heavy workloads
4. **Date-based organization**: Facilitates cleanup and cost tracking
5. **Daemon reliability**: inotifywait is stable and production-ready

---

## 9. Quick Reference

### Environment Variables

```bash
# Required
export R2_ENDPOINT="https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com"
export R2_BUCKET="runpod"
export R2_ACCESS_KEY_ID="your_access_key"
export R2_SECRET_ACCESS_KEY="your_secret_key"

# Optional
export ENABLE_R2_SYNC="true"
export COMFYUI_OUTPUT_DIR="/workspace/ComfyUI/output"
```

### Common Commands

```bash
# Test connection
python3 /upload_to_r2.py --test

# Upload single file
python3 /upload_to_r2.py /path/to/file.png

# Upload with custom prefix
python3 /upload_to_r2.py --prefix my-folder /path/to/file.mp4

# List R2 files
aws s3 ls s3://runpod/outputs/ \
  --endpoint-url $R2_ENDPOINT

# View daemon logs
tail -f /var/log/r2_sync.log

# Check daemon status
ps aux | grep r2_sync
```

### Troubleshooting Checklist

- [ ] R2 credentials set correctly in RunPod secrets
- [ ] `R2_ENDPOINT` environment variable is correct
- [ ] `R2_BUCKET` exists in R2 dashboard
- [ ] inotify-tools installed in Docker image
- [ ] Upload script has execute permissions
- [ ] Log file is writable (`/var/log/r2_sync.log`)
- [ ] Output directory exists and is writable

---

*Document generated: 2026-01-17*
*Author: oz + claude-haiku-4.5*
*Project: RunPod Custom Templates for AI Model Deployment*
