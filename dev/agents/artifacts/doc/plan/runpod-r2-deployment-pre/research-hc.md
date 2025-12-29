# RunPod Template Codebase Analysis

This analysis documents existing patterns in the hearmeman-extended Docker template for R2 integration.

---

## 1. Dockerfile Patterns

### Layer Structure (5 Layers)
```
Layer 1: System Dependencies (apt-get)
Layer 2: ComfyUI Base (git clone + pip)
Layer 3: Custom Nodes (multiple git clones)
Layer 3.5: Local Custom Nodes (COPY from host)
Layer 4: Additional Python Dependencies (pip)
Layer 5: Scripts and Configuration (COPY + chmod)
```

### Environment Variable Conventions
- **GPU Tier System**: `GPU_TIER` = consumer/prosumer/datacenter
- **Feature Toggles**: `ENABLE_*` pattern (e.g., `ENABLE_VIBEVOICE`, `ENABLE_ZIMAGE`)
- **Model Selection**: `*_MODEL` pattern (e.g., `VIBEVOICE_MODEL=Large`)
- **Memory Modes**: `GPU_MEMORY_MODE` = auto/full/sequential_cpu_offload/model_cpu_offload

### Model Directory Structure
```
/workspace/ComfyUI/models/
├── checkpoints/
├── embeddings/
├── vibevoice/
├── text_encoders/
├── diffusion_models/
├── vae/
├── controlnet/
├── loras/
├── clip_vision/
├── genfocus/
├── qwen/
├── mvinverse/
├── flashportrait/
├── storymem/
└── infcam/
```

### R2 Integration Points
Add new env vars:
```dockerfile
ENV R2_ENDPOINT=""
ENV R2_ACCESS_KEY=""
ENV R2_SECRET_KEY=""
ENV R2_BUCKET="runpod"
ENV ENABLE_R2_SYNC="false"
```

---

## 2. start.sh Patterns

### Storage Mode Detection (Lines 13-27)
```bash
detect_storage_mode() {
    if [ "$STORAGE_MODE" = "ephemeral" ]; then
        echo "ephemeral"
    elif [ "$STORAGE_MODE" = "persistent" ]; then
        echo "persistent"
    elif [ "$STORAGE_MODE" = "auto" ] || [ -z "$STORAGE_MODE" ]; then
        if [ -d "/workspace" ] && mountpoint -q "/workspace" 2>/dev/null; then
            echo "persistent"
        else
            echo "ephemeral"
        fi
    else
        echo "ephemeral"
    fi
}
```

### GPU Configuration Auto-Detection (Lines 36-91)
- Detects VRAM via `nvidia-smi`
- Auto-selects tier based on VRAM thresholds
- Sets ComfyUI VRAM flags (`--lowvram`, `--medvram`, etc.)

### Service Startup Sequence
1. Storage mode detection
2. GPU configuration
3. SSH setup (if PUBLIC_KEY set)
4. JupyterLab setup (if JUPYTER_PASSWORD set)
5. Custom nodes update (if UPDATE_NODES_ON_START=true)
6. Model downloads (/download_models.sh)
7. ComfyUI start (exec python main.py)

### R2 Integration Points
Add after model downloads, before ComfyUI start:
```bash
# ============================================
# R2 Output Sync Setup
# ============================================
if [ "${ENABLE_R2_SYNC:-false}" = "true" ]; then
    echo "[R2] Starting background sync daemon..."
    /r2_sync.sh &
fi
```

---

## 3. download_models.sh Patterns

### Helper Functions

**download_model()** (Lines 9-26):
```bash
download_model() {
    local URL="$1"
    local DEST="$2"
    local NAME=$(basename "$DEST")

    if [ -f "$DEST" ]; then
        echo "  [Skip] $NAME already exists"
        return 0
    fi

    mkdir -p "$(dirname "$DEST")"
    wget -c -q --show-progress -O "$DEST" "$URL" || {
        echo "  [Error] Failed to download $NAME"
        rm -f "$DEST"
        return 1
    }
}
```

**hf_download()** (Lines 29-34):
```bash
hf_download() {
    local REPO="$1"
    local FILE="$2"
    local DEST="$3"
    download_model "https://huggingface.co/${REPO}/resolve/main/${FILE}" "$DEST"
}
```

**civitai_download()** (Lines 37-56):
- Uses version ID for downloads
- Supports API key via `$CIVITAI_API_KEY`
- Uses `--content-disposition` for proper filenames

### Conditional Downloads Pattern
```bash
if [ "${ENABLE_FEATURE:-false}" = "true" ]; then
    echo "[Feature] Downloading..."
    # download commands
fi
```

### Python HuggingFace Downloads
```bash
python -c "
from huggingface_hub import snapshot_download
snapshot_download('repo/model',
    local_dir='$MODELS_DIR/feature/model',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] Will download on first use"
```

---

## 4. docker-compose.yml Patterns

### Volume Mount Strategy
```yaml
volumes:
  - ./models:/workspace/ComfyUI/models           # Models persistence
  - ./output:/workspace/ComfyUI/output           # Output persistence
  - /home/oz/comfyui/models/vibevoice:/workspace/ComfyUI/models/vibevoice:ro  # Shared read-only
```

### Environment Variable Organization
```yaml
environment:
  # Existing models
  - ENABLE_VIBEVOICE=true
  - ENABLE_CONTROLNET=true
  # GPU Configuration
  - GPU_TIER=consumer
  - GPU_MEMORY_MODE=auto
  # Tier 1: Consumer GPU
  - ENABLE_GENFOCUS=true
  # Tier 2: Prosumer GPU
  - ENABLE_FLASHPORTRAIT=false
  # Tier 3: Datacenter GPU
  - ENABLE_INFCAM=false
```

### GPU Resource Allocation
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

### Service Profiles
```yaml
profiles:
  - chatterbox  # Only starts with: docker compose --profile chatterbox up
```

---

## 5. Suggested R2 Sync Implementation

### New File: r2_sync.sh
```bash
#!/bin/bash
# R2 output sync daemon using inotifywait

OUTPUT_DIR="${COMFYUI_OUTPUT_DIR:-/workspace/ComfyUI/output}"
R2_BUCKET="${R2_BUCKET:-runpod}"

# Install inotify-tools if needed
if ! command -v inotifywait &> /dev/null; then
    apt-get update && apt-get install -y inotify-tools
fi

# Start watching
inotifywait -m -r -e close_write --format '%w%f' "$OUTPUT_DIR" | while read FILE; do
    if [[ "$FILE" =~ \.(png|jpg|webp|mp4|webm|wav|mp3)$ ]]; then
        python3 /upload_to_r2.py "$FILE" &
    fi
done
```

### New File: upload_to_r2.py
```python
#!/usr/bin/env python3
import os
import sys
import boto3
from botocore.config import Config

def upload_file(file_path):
    r2 = boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY"],
        aws_secret_access_key=os.environ["R2_SECRET_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="auto"
    )

    bucket = os.environ.get("R2_BUCKET", "runpod")
    key = f"outputs/{os.path.basename(file_path)}"

    r2.upload_file(file_path, bucket, key)
    print(f"[R2] Uploaded: {key}")

if __name__ == "__main__":
    upload_file(sys.argv[1])
```

### Dockerfile Additions
```dockerfile
# Add inotify-tools to Layer 1
RUN apt-get update && apt-get install -y --no-install-recommends \
    inotify-tools \
    ...

# Copy R2 sync scripts in Layer 5
COPY r2_sync.sh /r2_sync.sh
COPY upload_to_r2.py /upload_to_r2.py
RUN chmod +x /r2_sync.sh /upload_to_r2.py
```

### Environment Variables for RunPod Template
```
R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com
R2_ACCESS_KEY=<from secrets>
R2_SECRET_KEY=<from secrets>
R2_BUCKET=runpod
ENABLE_R2_SYNC=true
```

---

## 6. RunPod Template Configuration

### Template Settings
```
Name: hearmeman-extended
Container Image: ghcr.io/oz/hearmeman-extended:latest
Container Disk: 20GB (min for base image)
Volume Disk: 100GB (for models)
HTTP Ports: 8188 (ComfyUI), 8888 (Jupyter)
TCP Ports: 22 (SSH)
```

### Environment Variables (Secrets)
- `R2_ACCESS_KEY` - Use RunPod Secrets
- `R2_SECRET_KEY` - Use RunPod Secrets
- `CIVITAI_API_KEY` - Use RunPod Secrets

### Environment Variables (Visible)
```
ENABLE_R2_SYNC=true
R2_BUCKET=runpod
R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com
WAN_720P=true
ENABLE_VIBEVOICE=true
GPU_TIER=auto
```

---

*End of Codebase Analysis*
