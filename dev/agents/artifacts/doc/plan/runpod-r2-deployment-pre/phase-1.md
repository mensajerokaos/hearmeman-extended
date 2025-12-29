# Phase 1: R2 Sync Infrastructure - Detailed Implementation Specification

This specification details the implementation of a real-time file synchronization system between the RunPod environment and Cloudflare R2.

## 1.1: Create `upload_to_r2.py`

**File Path:** `/home/oz/projects/2025/oz/12/runpod/docker/upload_to_r2.py`

```python
import os
import sys
import time
import boto3
import argparse
import logging
from botocore.exceptions import ClientError
from botocore.config import Config
from datetime import datetime

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/r2_upload.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_r2_client():
    """Initialize and return the R2 S3 client."""
    r2_endpoint = os.getenv("R2_ENDPOINT")
    r2_access_key = os.getenv("R2_ACCESS_KEY_ID")
    r2_secret_key = os.getenv("R2_SECRET_ACCESS_KEY")

    if not all([r2_endpoint, r2_access_key, r2_secret_key]):
        logger.error("R2 environment variables are missing.")
        sys.exit(1)

    return boto3.client(
        "s3",
        endpoint_url=r2_endpoint,
        aws_access_key_id=r2_access_key,
        aws_secret_access_key=r2_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="auto"
    )

class ProgressPercentage:
    """Progress callback for large files."""
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0

    def __call__(self, bytes_amount):
        self._seen_so_far += bytes_amount
        percentage = (self._seen_so_far / self._size) * 100
        sys.stdout.write(
            f"\r{self._filename}  {self._seen_so_far} / {self._size}  ({percentage:.2f}%)"
        )
        sys.stdout.flush()

def upload_file(file_path, bucket, retries=3, backoff=2):
    """Upload a file to R2 with retry logic."""
    client = get_r2_client()
    filename = os.path.basename(file_path)
    
    # Organize path: outputs/YYYY-MM-DD/filename
    date_str = datetime.now().strftime("%Y-%m-%d")
    object_name = f"outputs/{date_str}/{filename}"

    for attempt in range(retries):
        try:
            logger.info(f"Uploading {file_path} to {bucket}/{object_name} (Attempt {attempt+1})")
            client.upload_file(
                file_path, 
                bucket, 
                object_name,
                Callback=ProgressPercentage(file_path)
            )
            print() # Newline after progress
            logger.info(f"Successfully uploaded {filename}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload {filename}: {e}")
            if attempt < retries - 1:
                sleep_time = backoff ** (attempt + 1)
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error(f"Max retries reached for {filename}")
                return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload file to Cloudflare R2")
    parser.add_argument("file", help="Path to the file to upload")
    parser.add_argument("--test", action="store_true", help="Run a test upload")
    args = parser.parse_args()

    bucket = os.getenv("R2_BUCKET", "runpod")
    
    if args.test:
        logger.info("Running test upload...")
        # Create a small dummy file for testing if it doesn't exist
        test_file = "test_r2_upload.txt"
        with open(test_file, "w") as f:
            f.write(f"R2 Upload Test - {datetime.now()}")
        success = upload_file(test_file, bucket)
        if success:
            logger.info("Test upload completed successfully.")
            os.remove(test_file)
        else:
            logger.error("Test upload failed.")
            sys.exit(1)
    else:
        if not os.path.exists(args.file):
            logger.error(f"File not found: {args.file}")
            sys.exit(1)
        upload_file(args.file, bucket)
```

**Verification:**
```bash
# Set dummy env vars for syntax check
export R2_ENDPOINT=https://...
export R2_ACCESS_KEY_ID=...
export R2_SECRET_ACCESS_KEY=...
python3 upload_to_r2.py --help
```

---

## 1.2: Create `r2_sync.sh`

**File Path:** `/home/oz/projects/2025/oz/12/runpod/docker/r2_sync.sh`

```bash
#!/bin/bash

# Configuration
WATCH_DIR="/workspace/ComfyUI/output"
LOG_FILE="/var/log/r2_sync.log"
UPLOAD_SCRIPT="/upload_to_r2.py"

echo "Starting R2 Sync Daemon..." | tee -a "$LOG_FILE"
echo "Monitoring: $WATCH_DIR" | tee -a "$LOG_FILE"

# Ensure log exists
touch "$LOG_FILE"

# Pattern matching for media files
# .png, .jpg, .mp4, .webm, .wav, .flac
PATTERN=".*\\.(png|jpg|jpeg|mp4|webm|wav|flac)$"

inotifywait -m -e close_write --format '%w%f' "$WATCH_DIR" | while read NEW_FILE
do
    if [[ "$NEW_FILE" =~ $PATTERN ]]; then
        echo "$(date): New file detected: $NEW_FILE" >> "$LOG_FILE"
        # Background upload (non-blocking)
        python3 "$UPLOAD_SCRIPT" "$NEW_FILE" >> "$LOG_FILE" 2>&1 &
    fi
done
```

**Verification:**
```bash
bash -n r2_sync.sh
```

---

## 1.3: Modify `Dockerfile`

**File Path:** `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile`

### Changes:

**BEFORE (System Dependencies):**
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    git-lfs \
    wget \
    curl \
    vim \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    openssh-server \
    aria2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
```

**AFTER (System Dependencies):**
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    git-lfs \
    wget \
    curl \
    vim \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    openssh-server \
    aria2 \
    inotify-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
```

**BEFORE (Additional Dependencies):**
```dockerfile
RUN pip install --no-cache-dir \
    huggingface_hub \
    accelerate \
    ...
```

**AFTER (Additional Dependencies):**
```dockerfile
RUN pip install --no-cache-dir \
    huggingface_hub \
    accelerate \
    boto3 \
    ...
```

**BEFORE (Scripts and Configuration):**
```dockerfile
COPY start.sh /start.sh
COPY download_models.sh /download_models.sh
RUN chmod +x /start.sh /download_models.sh
```

**AFTER (Scripts and Configuration):**
```dockerfile
COPY start.sh /start.sh
COPY download_models.sh /download_models.sh
COPY upload_to_r2.py /upload_to_r2.py
COPY r2_sync.sh /r2_sync.sh
RUN chmod +x /start.sh /download_models.sh /r2_sync.sh
```

**Environment Variables Addition:**
Add near other ENV variables:
```dockerfile
# R2 Configuration
ENV ENABLE_R2_SYNC="false"
ENV R2_ENDPOINT="https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com"
ENV R2_BUCKET="runpod"
ENV R2_ACCESS_KEY_ID=""
ENV R2_SECRET_ACCESS_KEY=""
```

---

## 1.4: Modify `start.sh`

**File Path:** `/home/oz/projects/2025/oz/12/runpod/docker/start.sh`

### Changes:

**Insertion Point:** Before starting ComfyUI.

**BEFORE:**
```bash
# ============================================ 
# Start ComfyUI
# ============================================ 
echo "[ComfyUI] Starting on port ${COMFYUI_PORT:-8188}..."
```

**AFTER:**
```bash
# ============================================ 
# R2 Sync Daemon Setup
# ============================================ 
if [ "${ENABLE_R2_SYNC:-false}" = "true" ]; then
    echo "[R2 Sync] Starting background sync daemon..."
    # Ensure output directory exists before watching
    mkdir -p /workspace/ComfyUI/output
    nohup /r2_sync.sh > /var/log/r2_sync_init.log 2>&1 & 
    echo "[R2 Sync] Daemon active, monitoring /workspace/ComfyUI/output"
fi

# ============================================ 
# Start ComfyUI
# ============================================ 
echo "[ComfyUI] Starting on port ${COMFYUI_PORT:-8188}..."
```

