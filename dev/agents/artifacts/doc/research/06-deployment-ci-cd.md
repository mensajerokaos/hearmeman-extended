# RunPod Deployment, CI/CD, and Integration Documentation

**Author**: oz + claude-haiku-4-5
**Date**: 2026-01-17
**Task**: Document all deployment-related systems
**Status**: Complete

---

## Table of Contents

1. [GitHub Actions CI/CD Pipeline](#github-actions-cicd-pipeline)
2. [RunPod Deployment Configuration](#runpod-deployment-configuration)
3. [Container Startup and Initialization](#container-startup-and-initialization)
4. [Model Download Infrastructure](#model-download-infrastructure)
5. [R2 Output Synchronization](#r2-output-synchronization)
6. [Port Configuration Reference](#port-configuration-reference)
7. [Dockerfile Architecture](#dockerfile-architecture)
8. [Docker Compose Configuration](#docker-compose-configuration)
9. [Datacenter Performance Benchmarks](#datacenter-performance-benchmarks)
10. [Environment Variables Reference](#environment-variables-reference)
11. [Secrets Management](#secrets-management)
12. [Best Practices and Recommendations](#best-practices-and-recommendations)

---

## GitHub Actions CI/CD Pipeline

### Workflow Overview

The project uses GitHub Actions for automated Docker image builds and pushes to GitHub Container Registry (GHCR). The workflow triggers on pushes to main/master branches and can be manually dispatched with custom parameters.

**File Location**: `.github/workflows/docker-build.yml`

### Workflow Triggers

| Trigger Type | Condition | Purpose |
|--------------|-----------|---------|
| Push | `branches: [main, master]` | Auto-build on main branch updates |
| Push | `paths: ['docker/**']` | Rebuild only when Docker files change |
| Workflow Dispatch | Manual inputs | Custom builds with selectable model baking |

### Workflow Dispatch Parameters

```yaml
inputs:
  bake_wan_720p:
    description: 'Bake WAN 2.1 720p models (~25GB)'
    type: boolean
    default: false

  bake_wan_480p:
    description: 'Bake WAN 2.1 480p models (~12GB)'
    type: boolean
    default: false

  bake_illustrious:
    description: 'Bake Illustrious XL models (~7GB)'
    type: boolean
    default: false

  image_tag:
    description: 'Custom image tag (default: latest)'
    type: string
    default: 'latest'
```

### Build Pipeline Steps

#### Step 1: Free Disk Space

Critical step to ensure sufficient space for Docker image build (~11GB base + models).

```bash
sudo rm -rf /usr/share/dotnet
sudo rm -rf /opt/ghc
sudo rm -rf /usr/local/share/boost
sudo rm -rf "$AGENT_TOOLSDIRECTORY"
sudo rm -rf /usr/local/lib/android
sudo rm -rf /usr/share/swift
docker system prune -af --volumes || true
```

#### Step 2: Checkout Repository

```yaml
- uses: actions/checkout@v4
```

#### Step 3: Docker Buildx Setup

```yaml
- uses: docker/setup-buildx-action@v3
```

#### Step 4: GHCR Authentication

```yaml
- uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

#### Step 5: Determine Image Tag

The workflow automatically selects image tags based on build arguments:

```bash
if [ "${{ inputs.image_tag }}" != "" ] && [ "${{ inputs.image_tag }}" != "latest" ]; then
  echo "tag=${{ inputs.image_tag }}" >> $GITHUB_OUTPUT
elif [ "${{ inputs.bake_wan_720p }}" = "true" ]; then
  echo "tag=wan720p" >> $GITHUB_OUTPUT
elif [ "${{ inputs.bake_wan_480p }}" = "true" ]; then
  echo "tag=wan480p" >> $GITHUB_OUTPUT
elif [ "${{ inputs.bake_illustrious }}" = "true" ]; then
  echo "tag=illustrious" >> $GITHUB_OUTPUT
else
  echo "tag=latest" >> $GITHUB_OUTPUT
fi
```

**Tag Strategy**:
- `latest`: Default base image
- `wan720p`: Pre-baked WAN 2.1 720p models
- `wan480p`: Pre-baked WAN 2.1 480p models
- `illustrious`: Pre-baked Illustrious XL models
- Custom tags: User-specified

#### Step 6: Build and Push

```yaml
- uses: docker/build-push-action@v5
  with:
    context: ./docker
    push: true
    tags: ${{ steps.meta.outputs.tags }}
    labels: ${{ steps.meta.outputs.labels }}
    platforms: linux/amd64
    cache-from: type=gha
    cache-to: type=gha,mode=max
    build-args: |
      BAKE_WAN_720P=${{ inputs.bake_wan_720P || 'false' }}
      BAKE_WAN_480P=${{ inputs.bake_wan_480P || 'false' }}
      BAKE_ILLUSTRIOUS=${{ inputs.bake_illustrious || 'false' }}
```

### Image Metadata

```yaml
images: ghcr.io/${{ github.repository_owner }}/hearmeman-extended
tags: |
  type=raw,value=${{ steps.tag.outputs.tag }}
  type=sha,prefix=
```

### Complete Workflow File

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [main, master]
    paths:
      - 'docker/**'
  workflow_dispatch:
    inputs:
      bake_wan_720p:
        description: 'Bake WAN 2.1 720p models (~25GB)'
        required: false
        type: boolean
        default: false
      bake_wan_480p:
        description: 'Bake WAN 2.1 480p models (~12GB)'
        required: false
        type: boolean
        default: false
      bake_illustrious:
        description: 'Bake Illustrious XL models (~7GB)'
        required: false
        type: boolean
        default: false
      image_tag:
        description: 'Custom image tag (default: latest)'
        required: false
        type: string
        default: 'latest'

env:
  REGISTRY: ghcr.io

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Free Disk Space
        run: |
          sudo rm -rf /usr/share/dotnet
          sudo rm -rf /opt/ghc
          sudo rm -rf /usr/local/share/boost
          sudo rm -rf "$AGENT_TOOLSDIRECTORY"
          sudo rm -rf /usr/local/lib/android
          sudo rm -rf /usr/share/swift
          docker system prune -af --volumes || true
          df -h

      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Determine image tag
        id: tag
        run: |
          if [ "${{ inputs.image_tag }}" != "" ] && [ "${{ inputs.image_tag }}" != "latest" ]; then
            echo "tag=${{ inputs.image_tag }}" >> $GITHUB_OUTPUT
          elif [ "${{ inputs.bake_wan_720p }}" = "true" ]; then
            echo "tag=wan720p" >> $GITHUB_OUTPUT
          elif [ "${{ inputs.bake_wan_480p }}" = "true" ]; then
            echo "tag=wan480p" >> $GITHUB_OUTPUT
          elif [ "${{ inputs.bake_illustrious }}" = "true" ]; then
            echo "tag=illustrious" >> $GITHUB_OUTPUT
          else
            echo "tag=latest" >> $GITHUB_OUTPUT
          fi

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository_owner }}/hearmeman-extended
          tags: |
            type=raw,value=${{ steps.tag.outputs.tag }}
            type=sha,prefix=

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./docker
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          platforms: linux/amd64
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            BAKE_WAN_720P=${{ inputs.bake_wan_720P || 'false' }}
            BAKE_WAN_480P=${{ inputs.bake_wan_480P || 'false' }}
            BAKE_ILLUSTRIOUS=${{ inputs.bake_illustrious || 'false' }}
```

---

## RunPod Deployment Configuration

### Pod Creation Command

Complete production-ready pod creation command with all configuration options:

```bash
~/.local/bin/runpodctl create pod \
  --name "hearmeman-extended-$(date +%H%M)" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA GeForce RTX 4090" \
  --gpuCount 1 \
  --containerDiskSize 20 \
  --volumeSize 15 \
  --secureCloud \
  --ports "8188/http" \
  --ports "19123/http" \
  --env "ENABLE_VIBEVOICE=true" \
  --env "ENABLE_CONTROLNET=true" \
  --env "WAN_720P=true" \
  --env "R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}" \
  --env "R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}" \
  --env "R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com" \
  --env "R2_BUCKET=runpod" \
  --env "ENABLE_R2_SYNC=true"
```

### GPU Tier Recommendations

| GPU Model | VRAM | Tier | Best For | Cost Level |
|-----------|------|------|----------|------------|
| RTX 4090 | 24 GB | Consumer | WAN 2.2 720p, quantized video, image generation | $0.59/hr |
| RTX 4080 Super | 16 GB | Consumer | WAN 2.2 480p, VibeVoice TTS | ~$0.50/hr |
| A6000 | 48 GB | Prosumer | WAN 2.2 720p, high-res video, batch processing | ~$1.50/hr |
| A100 | 80 GB | Datacenter | Native BF16, training, large batch processing | ~$2.50/hr |
| L40S | 48 GB | Prosumer | WAN 2.2 720p, optimized for inference | ~$1.80/hr |

### Template Configuration

**Recommended Template Settings**:

| Setting | Value | Notes |
|---------|-------|-------|
| Template Name | `hearmeman-extended-r2` | Production template |
| Container Image | `ghcr.io/mensajerokaos/hearmeman-extended:latest` | Latest GHCR image |
| Container Disk | 20 GB | Base image + dependencies |
| Volume Disk | 100 GB | Models and cache storage |
| Volume Mount Path | `/workspace` | Persistent across restarts |
| HTTP Ports | `8188, 8888` | ComfyUI + JupyterLab |
| TCP Ports | `22` | SSH access |

### Environment Variables

**Core Configuration**:

```bash
# GPU and Memory
GPU_TIER=consumer              # consumer, prosumer, datacenter
GPU_MEMORY_MODE=auto           # auto, full, sequential_cpu_offload, model_cpu_offload
COMFYUI_ARGS=""                # Optional: --lowvram, --medvram, --cpu-vae

# Model Enables
ENABLE_VIBEVOICE=true          # VibeVoice TTS (~18GB)
ENABLE_WAN_720P=true           # WAN 2.1 video generation (~25GB)
ENABLE_CONTROLNET=true         # ControlNet models (~3.6GB)
ENABLE_ILLUSTRIOUS=false       # Illustrious XL (~6.5GB)
ENABLE_ZIMAGE=false            # Z-Image Turbo (~21GB)
ENABLE_WAN22_DISTILL=false     # WAN 2.2 TurboDiffusion I2V (~28GB)

# Storage
STORAGE_MODE=persistent        # persistent, ephemeral, auto
COMFYUI_PORT=8188

# R2 Sync
ENABLE_R2_SYNC=true
R2_BUCKET=runpod
R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com
```

**Secrets (via RunPod Secrets)**:

| Secret Name | Source | Purpose |
|-------------|--------|---------|
| `r2_access_key` | RunPod Secret | R2 Access Key ID |
| `r2_secret_key` | RunPod Secret | R2 Secret Access Key |
| `civitai_api_key` | RunPod Secret (optional) | CivitAI API key for LoRA downloads |

---

## Container Startup and Initialization

### Startup Sequence

The container startup process follows this exact sequence:

1. **Storage Mode Detection** - Determines if running on persistent or ephemeral storage
2. **GPU Configuration** - Detects VRAM and configures tier/memory settings
3. **SSH Setup** - If `PUBLIC_KEY` provided
4. **JupyterLab Setup** - If `JUPYTER_PASSWORD` provided
5. **Node Updates** - If `UPDATE_NODES_ON_START=true`
6. **Model Downloads** - Executes `download_models.sh`
7. **R2 Sync Daemon** - Starts if enabled
8. **ComfyUI Launch** - Starts main service

### Storage Mode Detection

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

### GPU VRAM Detection

```bash
detect_gpu_config() {
    # Detect GPU VRAM in MB
    GPU_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -n 1)

    # Auto-detect GPU tier if not set
    if [ -z "$GPU_TIER" ] || [ "$GPU_TIER" = "auto" ]; then
        if (( GPU_VRAM >= 48000 )); then
            export GPU_TIER="datacenter"
        elif (( GPU_VRAM >= 20000 )); then
            export GPU_TIER="prosumer"
        else
            export GPU_TIER="consumer"
        fi
    fi

    # Auto-detect memory mode if set to "auto"
    if [ "$GPU_MEMORY_MODE" = "auto" ]; then
        if (( GPU_VRAM >= 48000 )); then
            export GPU_MEMORY_MODE="full"
        elif (( GPU_VRAM >= 24000 )); then
            export GPU_MEMORY_MODE="model_cpu_offload"
        else
            export GPU_MEMORY_MODE="sequential_cpu_offload"
        fi
    fi

    # Auto-detect ComfyUI VRAM flags if not set
    if [ -z "$COMFYUI_ARGS" ]; then
        if (( GPU_VRAM < 8000 )); then
            export COMFYUI_ARGS="--lowvram --cpu-vae --force-fp16"
        elif (( GPU_VRAM < 12000 )); then
            export COMFYUI_ARGS="--lowvram --force-fp16"
        elif (( GPU_VRAM < 16000 )); then
            export COMFYUI_ARGS="--medvram --cpu-text-encoder --force-fp16"
        elif (( GPU_VRAM < 24000 )); then
            export COMFYUI_ARGS="--normalvram --force-fp16"
        else
            export COMFYUI_ARGS=""
        fi
    fi
}
```

### VRAM Configuration by Tier

| VRAM | Tier | Memory Mode | ComfyUI Args |
|------|------|-------------|--------------|
| < 8 GB | Consumer | sequential_cpu_offload | `--lowvram --cpu-vae --force-fp16` |
| 8-12 GB | Consumer | sequential_cpu_offload | `--lowvram --force-fp16` |
| 12-16 GB | Consumer | sequential_cpu_offload | `--medvram --cpu-text-encoder --force-fp16` |
| 16-24 GB | Consumer/Prosumer | model_cpu_offload | `--normalvram --force-fp16` |
| 24-48 GB | Prosumer | model_cpu_offload | (empty) |
| 48+ GB | Datacenter | full | (empty) |

### SSH Configuration

```bash
if [[ -n "$PUBLIC_KEY" ]]; then
    echo "[SSH] Configuring SSH access..."
    mkdir -p ~/.ssh && chmod 700 ~/.ssh
    echo "$PUBLIC_KEY" >> ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    service ssh start
    echo "[SSH] Ready on port 22"
fi
```

### JupyterLab Configuration

```bash
if [[ -n "$JUPYTER_PASSWORD" ]]; then
    echo "[Jupyter] Starting JupyterLab on port 8888..."
    nohup jupyter lab \
        --allow-root \
        --no-browser \
        --port=8888 \
        --ip=0.0.0.0 \
        --ServerApp.token="$JUPYTER_PASSWORD" \
        --ServerApp.allow_origin='*' \
        > /var/log/jupyter.log 2>&1 &
fi
```

### ComfyUI Startup

```bash
echo "[ComfyUI] Starting on port ${COMFYUI_PORT:-8188}..."
if [ -n "$COMFYUI_ARGS" ]; then
    echo "[ComfyUI] Using VRAM args: $COMFYUI_ARGS"
fi
cd /workspace/ComfyUI
exec python main.py \
    --listen 0.0.0.0 \
    --port ${COMFYUI_PORT:-8188} \
    --enable-cors-header \
    --preview-method auto \
    $COMFYUI_ARGS
```

---

## Model Download Infrastructure

### Overview

The `download_models.sh` script handles on-demand model downloads with:
- Resume support for interrupted downloads
- Multiple sources (HuggingFace, CivitAI, custom repos)
- Progress tracking and logging
- Verification checksums
- Organized directory structure

### Download Sources

| Source | Type | Use Case |
|--------|------|----------|
| HuggingFace Hub | Repository | Primary model hosting |
| CivitAI | API + Direct | LoRA models, checkpoints |
| Git LFS | Repository | Large binary files |

### Model Categories by GPU Tier

#### Tier 1: Consumer GPU (8-24GB VRAM)

**VibeVoice TTS**:
- Model: `aoi-ot/VibeVoice-Large` (~18GB)
- VRAM: 8-12GB (1.5B model), 16GB+ (7B model)
- Features: Multi-speaker TTS, voice cloning, LoRA support

**ControlNet** (~3.6GB total):
- Canny, Depth, OpenPose, Lineart, NormalBae

**WAN 2.1 480p** (~12GB):
- Text encoder (9.5GB) + VAE (335MB) + 1.3B diffusion (2GB)

**Qwen-Edit** (GGUF quantized):
- Q4_K_M: 13GB VRAM
- Q5_K_M: 15GB VRAM
- Q8_0: 22GB VRAM

**Genfocus** (~12GB):
- Depth-of-Field Refocusing
- VRAM: ~12GB

**MVInverse** (~8GB):
- Multi-view Inverse Rendering
- VRAM: ~8GB

#### Tier 2: Prosumer GPU (24GB+ with CPU Offload)

**WAN 2.1 720p** (~25GB):
- Text encoder (9.5GB) + CLIP vision (1.4GB) + VAE (335MB) + 14B diffusion (14GB)

**FlashPortrait** (~60GB):
- VRAM: 60GB (full), 30GB (model_cpu_offload), 10GB (sequential_cpu_offload)
- RAM: 32GB minimum for CPU offload modes

**StoryMem** (~20GB base + LoRAs):
- Multi-Shot Video Storytelling
- Uses LoRA variants (MI2V, MM2V)

#### Tier 3: Datacenter GPU (48-80GB VRAM)

**WAN 2.2 Distilled** (~28GB):
- High noise expert (14GB) + Low noise expert (14GB)
- TurboDiffusion I2V (4-step inference)

**InfCam** (~50GB+):
- Camera-Controlled Video Generation
- VRAM: 50GB+ inference, 52-56GB/GPU training
- Requires: A100 80GB or H100 80GB

### Download Helper Functions

#### HuggingFace Direct Download

```bash
download_model() {
    local URL="$1"
    local DEST="$2"
    local EXPECTED_SIZE="${3:-}"

    if [ -f "$DEST" ]; then
        local SIZE=$(stat -c%s "$DEST" 2>/dev/null || echo "0")
        if [ "$SIZE" -gt 1000000 ]; then
            echo "  [Skip] $(basename $DEST) already exists"
            return 0
        fi
        echo "  [Resume] $(basename $DEST) incomplete, resuming..."
    fi

    # Use wget with timeout and progress bar
    local WGET_EXIT=0
    timeout "$DOWNLOAD_TIMEOUT" wget -c --progress=bar:force:noscroll -O "$DEST" "$URL" 2>&1 || WGET_EXIT=$?

    if [ $WGET_EXIT -ne 0 ]; then
        echo "  [Warn] wget failed (exit $WGET_EXIT), trying curl..."
        timeout "$DOWNLOAD_TIMEOUT" curl -L -C - --progress-bar -o "$DEST" "$URL" || {
            echo "  [ERROR] Failed to download $(basename $DEST)"
            rm -f "$DEST"
            return 1
        }
    fi
}
```

#### HuggingFace Snapshot Download

```bash
hf_snapshot_download() {
    local REPO="$1"
    local DEST="$2"

    if [ -d "$DEST" ] && [ "$(ls -A "$DEST" 2>/dev/null)" ]; then
        echo "  [Skip] $(basename $DEST) already exists"
        return 0
    fi

    python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('$REPO',
    local_dir='$DEST',
    local_dir_use_symlinks=False)
"
}
```

#### CivitAI Download

```bash
civitai_download() {
    local VERSION_ID="$1"
    local TARGET_DIR="$2"
    local DESCRIPTION="${3:-CivitAI asset}"

    # Build URL with API key if available
    local URL="https://civitai.com/api/download/models/${VERSION_ID}"
    if [ -n "$CIVITAI_API_KEY" ]; then
        URL="${URL}?token=${CIVITAI_API_KEY}"
    fi

    # Try wget with explicit redirect handling first
    wget -c -q --show-progress \
        --max-redirect=10 \
        --content-disposition \
        -P "$TARGET_DIR" \
        "$URL" 2>/dev/null && return 0

    # Fallback to curl if wget fails
    local FILENAME=$(curl -sI -L "$URL" 2>/dev/null | grep -i "content-disposition" | sed -n 's/.*filename="\?\([^"]*\)"\?.*/\1/p' | tr -d '\r')
    if [ -z "$FILENAME" ]; then
        FILENAME="model_${VERSION_ID}.safetensors"
    fi

    curl -L -C - -o "$TARGET_DIR/$FILENAME" "$URL" || {
        echo "  [Error] Failed: $VERSION_ID"
        return 1
    }
}
```

### WAN 2.1 720p Download Example

```bash
if [ "${WAN_720P:-false}" = "true" ]; then
    echo "[WAN] Downloading WAN 2.1 720p models (~25GB total)..."

    # Text encoders (shared)
    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
        "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
        "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
        "9.5GB"

    # CLIP Vision for I2V
    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
        "split_files/clip_vision/clip_vision_h.safetensors" \
        "$MODELS_DIR/clip_vision/clip_vision_h.safetensors" \
        "1.4GB"

    # VAE
    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
        "split_files/vae/wan_2.1_vae.safetensors" \
        "$MODELS_DIR/vae/wan_2.1_vae.safetensors" \
        "335MB"

    # 720p diffusion model (T2V)
    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
        "split_files/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" \
        "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" \
        "14GB"
fi
```

### Storage Requirements Summary

| Component | Size | Notes |
|-----------|------|-------|
| Docker Image | ~12GB | Base with custom nodes |
| WAN 2.2 720p | ~25GB | Default video gen |
| WAN 2.2 480p | ~12GB | Optional |
| VibeVoice-Large | ~18GB | TTS voice cloning |
| XTTS v2 | ~1.8GB | Multilingual TTS |
| Z-Image Turbo | ~21GB | Fast image gen |
| SteadyDancer | ~33GB | Dance video |
| SCAIL | ~28GB | Facial mocap |
| ControlNet (5) | ~3.6GB | Preprocessors |
| VACE 14B | ~28GB | Video editing |
| Fun InP 14B | ~28GB | Frame interpolation |
| Realism Illustrious | ~6.5GB | Photorealistic images |
| **Total (ALL)** | **~230GB** | |
| **Typical Config** | **~80-120GB** | |

---

## R2 Output Synchronization

### Architecture Overview

```
ComfyUI Output (local) → inotifywait → r2_sync.sh → upload_to_r2.py → Cloudflare R2
                       (file watch)    (daemon)      (Python uploader)    (storage)
```

### File Watching Daemon

**Location**: `docker/r2_sync.sh`

```bash
#!/bin/bash
OUTPUT_DIR="${COMFYUI_OUTPUT_DIR:-/workspace/ComfyUI/output}"
WATCH_PATTERNS="\.png$|\.jpg$|\.jpeg$|\.webp$|\.mp4$|\.webm$|\.gif$|\.wav$|\.mp3$|\.flac$"

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

### Python Uploader

**Location**: `docker/upload_to_r2.py`

#### R2 Client Configuration

```python
class R2Uploader:
    def __init__(self):
        self.endpoint = os.environ.get(
            'R2_ENDPOINT',
            'https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com'
        )
        self.bucket = os.environ.get('R2_BUCKET', 'runpod')
        self.access_key = os.environ.get('R2_ACCESS_KEY_ID') or os.environ.get('R2_ACCESS_KEY')
        self.secret_key = os.environ.get('R2_SECRET_ACCESS_KEY') or os.environ.get('R2_SECRET_KEY')

        if not self.access_key or not self.secret_key:
            raise ValueError("Missing R2 credentials")

        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version='s3v4', retries={'max_attempts': 3, 'mode': 'adaptive'}),
            region_name='auto'
        )
```

#### Upload with Retry Logic

```python
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
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Upload failed: {e}")
                return False
    return False
```

#### Multipart Upload for Large Files

```python
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
```

### R2 Organization Structure

```
runpod-bucket/
└── outputs/
    └── YYYY-MM-DD/
        ├── image-001.png
        ├── image-002.png
        ├── video-001.mp4
        └── audio-001.wav
```

### Usage Commands

```bash
# Test R2 connection
python3 /upload_to_r2.py --test

# Upload specific file
python3 /upload_to_r2.py /workspace/ComfyUI/output/myfile.png

# Upload with custom prefix
python3 /upload_to_r2.py --prefix videos /workspace/ComfyUI/output/video.mp4

# Upload multiple files
python3 /upload_to_r2.py file1.png file2.mp4 file3.wav
```

### Storage Estimates

| Output Type | Size | 10GB R2 = |
|------------|------|-----------|
| Images (768px) | 1-2 MB | ~5,000-10,000 |
| WAN 720p video | 20-50 MB | ~200-500 |
| TTS audio | 0.5-2 MB | ~5,000-20,000 |

---

## Port Configuration Reference

### Main Service Ports

| Port | Service | Protocol | Purpose | Access |
|------|---------|----------|---------|--------|
| 8188 | ComfyUI | HTTP | Main web interface, workflow editor | Public |
| 8888 | JupyterLab | HTTP | Development environment, notebooks | Public |
| 22 | SSH | TCP | Command-line access, file transfer | Secured |

### TTS Service Ports

| Port | Service | Protocol | Purpose | Container |
|------|---------|----------|---------|-----------|
| 8000 | Chatterbox | HTTP | Resemble AI TTS API | Separate |
| 8020 | XTTS v2 | HTTP | Coqui TTS API | Separate |

### Port Security

- **8188 (ComfyUI)**: Exposed to internet, basic auth recommended
- **8888 (JupyterLab)**: Exposed, use strong password
- **22 (SSH)**: Secured, key-based authentication only
- **8000/8020 (TTS)**: Internal or secured via firewall

---

## Dockerfile Architecture

### Multi-Layer Build Strategy

The Dockerfile uses 6 distinct layers for optimal caching and build times:

#### Layer 1: System Dependencies

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

#### Layer 2: ComfyUI Base

```dockerfile
WORKDIR /workspace
RUN git clone https://github.com/comfyanonymous/ComfyUI.git && \
    cd ComfyUI && \
    pip install --no-cache-dir -r requirements.txt
```

#### Layer 3: Custom Nodes

```dockerfile
WORKDIR /workspace/ComfyUI/custom_nodes

# ComfyUI-Manager
RUN git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Manager.git

# VibeVoice-ComfyUI
RUN git clone --depth 1 https://github.com/Enemyx-net/VibeVoice-ComfyUI.git && \
    cd VibeVoice-ComfyUI && \
    pip install --no-cache-dir -r requirements.txt || true

# ComfyUI-Chatterbox
RUN git clone --depth 1 https://github.com/thefader/ComfyUI-Chatterbox.git && \
    cd ComfyUI-Chatterbox && \
    pip install --no-cache-dir -r requirements.txt || true

# ComfyUI-SCAIL-Pose
RUN git clone --depth 1 https://github.com/kijai/ComfyUI-SCAIL-Pose.git

# ControlNet Preprocessors
RUN git clone --depth 1 https://github.com/Fannovel16/comfyui_controlnet_aux.git && \
    cd comfyui_controlnet_aux && \
    pip install --no-cache-dir -r requirements.txt || true

# TurboDiffusion
RUN git clone --depth 1 https://github.com/anveshane/Comfyui_turbodiffusion.git && \
    cd Comfyui_turbodiffusion && \
    pip install --no-cache-dir -r requirements.txt || true

# ComfyUI-WanVideoWrapper
RUN git clone --depth 1 https://github.com/kijai/ComfyUI-WanVideoWrapper.git && \
    cd ComfyUI-WanVideoWrapper && \
    pip install --no-cache-dir -r requirements.txt || true

# ComfyUI-VideoHelperSuite
RUN git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git && \
    cd ComfyUI-VideoHelperSuite && \
    pip install --no-cache-dir -r requirements.txt || true
```

#### Layer 3.5: Custom AI Model Wrappers

```dockerfile
# ComfyUI-Genfocus
COPY custom_nodes/ComfyUI-Genfocus /workspace/ComfyUI/custom_nodes/ComfyUI-Genfocus
RUN cd /workspace/ComfyUI/custom_nodes/ComfyUI-Genfocus && \
    pip install --no-cache-dir -r requirements.txt || true

# ComfyUI-MVInverse
COPY custom_nodes/ComfyUI-MVInverse /workspace/ComfyUI/custom_nodes/ComfyUI-MVInverse
RUN cd /workspace/ComfyUI/custom_nodes/ComfyUI-MVInverse && \
    pip install --no-cache-dir -r requirements.txt || true
```

#### Layer 4: Additional Dependencies

```dockerfile
RUN pip install --no-cache-dir \
    huggingface_hub \
    accelerate \
    safetensors \
    boto3 \
    sentencepiece \
    protobuf \
    cupy-cuda12x \
    imageio[ffmpeg] \
    einops \
    modelscope \
    ftfy \
    lpips \
    lightning \
    pandas \
    matplotlib \
    wandb \
    ffmpeg-python \
    audiotsm \
    loguru \
    diffusers>=0.21.0 \
    peft>=0.4.0 \
    opencv-python>=4.5.0 \
    timm \
    pynvml
```

#### Layer 5: Scripts and Configuration

```dockerfile
COPY start.sh /start.sh
COPY download_models.sh /download_models.sh
COPY upload_to_r2.py /upload_to_r2.py
COPY r2_sync.sh /r2_sync.sh
RUN chmod +x /start.sh /download_models.sh /r2_sync.sh

COPY workflows/ /workspace/ComfyUI/user/default/workflows/

RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision,genfocus,qwen,mvinverse,flashportrait,storymem,infcam}
```

#### Layer 6: Build-time Model Downloads (Optional)

```dockerfile
ARG BAKE_WAN_720P
ARG BAKE_WAN_480P
ARG BAKE_ILLUSTRIOUS

# WAN 2.1 720p Models (~25GB)
RUN if [ "$BAKE_WAN_720P" = "true" ]; then \
    echo "[BUILD] Downloading WAN 2.1 720p models..." && \
    wget -q --show-progress -O /workspace/ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors \
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" && \
    wget -q --show-progress -O /workspace/ComfyUI/models/clip_vision/clip_vision_h.safetensors \
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" && \
    wget -q --show-progress -O /workspace/ComfyUI/models/vae/wan_2.1_vae.safetensors \
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" && \
    wget -q --show-progress -O /workspace/ComfyUI/models/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors \
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" && \
    echo "[BUILD] WAN 2.1 720p models downloaded"; \
    fi
```

### OCI Labels

```dockerfile
LABEL org.opencontainers.image.source=https://github.com/mensajerokaos/hearmeman-extended
LABEL org.opencontainers.image.description="ComfyUI with AI video/audio generation (WAN, VibeVoice, TurboDiffusion)"
LABEL org.opencontainers.image.licenses=MIT
```

### Exposed Ports

```dockerfile
EXPOSE 22 8188 8888
```

---

## Docker Compose Configuration

### Main Service Definition

```yaml
version: '3.8'

services:
  hearmeman-extended:
    build:
      context: .
      dockerfile: Dockerfile
    image: hearmeman-extended:local
    container_name: hearmeman-extended
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - ENABLE_VIBEVOICE=true
      - ENABLE_CONTROLNET=true
      - ENABLE_ILLUSTRIOUS=false
      - ENABLE_ZIMAGE=false
      - VIBEVOICE_MODEL=Large
      - STORAGE_MODE=persistent
      - COMFYUI_PORT=8188
      - GPU_TIER=consumer
      - GPU_MEMORY_MODE=auto
      - ENABLE_GENFOCUS=true
      - ENABLE_QWEN_EDIT=true
      - QWEN_EDIT_MODEL=Q4_K_M
      - ENABLE_MVINVERSE=true
      - ENABLE_FLASHPORTRAIT=false
      - ENABLE_STORYMEM=false
      - ENABLE_INFCAM=false
    ports:
      - "8188:8188"
      - "8888:8888"
      - "2222:22"
    volumes:
      - ./models:/workspace/ComfyUI/models
      - ./output:/workspace/ComfyUI/output
      - /home/oz/comfyui/models/vibevoice:/workspace/ComfyUI/models/vibevoice:ro
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
```

### Chatterbox TTS Service

```yaml
chatterbox:
  build:
    context: ./chatterbox-api
    dockerfile: docker/Dockerfile.gpu
  image: chatterbox-tts-api:local
  container_name: chatterbox
  runtime: nvidia
  ports:
    - "8000:4123"
  environment:
    - NVIDIA_VISIBLE_DEVICES=all
  volumes:
    - ./chatterbox-voices:/app/voices
    - ./output:/app/output
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  restart: unless-stopped
  profiles:
    - chatterbox  # Only starts with: docker compose --profile chatterbox up
```

### Volume Definitions

```yaml
volumes:
  models:
  output:
```

---

## Datacenter Performance Benchmarks

### Startup Time Comparison

| Region | Type | Startup Time | Network Speed | Recommendation |
|--------|------|--------------|---------------|----------------|
| US | Secure Cloud | ~37 sec | 51 MB/s | **Recommended** |
| US | Community | ~1 sec | Variable | Good for testing |
| EU | CZ | 4+ min | Unknown | Avoid for speed-critical |
| UAE | - | 2+ min | Slow | Avoid |

### Model Download Performance

**Secure Cloud (US)**:
- Download speed: 51 MB/s
- WAN 2.1 720p (25GB): ~8 minutes
- WAN 2.2 Distilled (28GB): ~9 minutes
- VibeVoice-Large (18GB): ~6 minutes

**Community Cloud (US)**:
- Download speed: Variable (5-50 MB/s)
- WAN 2.1 720p (25GB): 8-80 minutes
- VibeVoice-Large (18GB): 6-60 minutes

### GPU Performance by Type

| GPU | Inference Speed | VRAM | Best Use Case |
|-----|-----------------|------|---------------|
| RTX 4090 | Fast | 24 GB | Production video, image gen |
| RTX 4080 Super | Fast | 16 GB | Quantized models, TTS |
| A6000 | Fast | 48 GB | High-res video, batch |
| A100 | Fastest | 80 GB | Training, native precision |

### Cost Optimization

| Strategy | Savings | Trade-off |
|----------|---------|-----------|
| Use 480p models | 50% storage | Lower resolution |
| Quantized inference | 30-50% VRAM | Slight quality loss |
| Spot instances | 60-70% cost | Interruption risk |
| Community Cloud | Free startup | Variable performance |

---

## Environment Variables Reference

### Build-time Variables (Dockerfile)

| Variable | Default | Purpose |
|----------|---------|---------|
| `BAKE_WAN_720P` | false | Pre-download WAN 2.1 720p models |
| `BAKE_WAN_480P` | false | Pre-download WAN 2.1 480p models |
| `BAKE_ILLUSTRIOUS` | false | Pre-download Illustrious XL models |

### Runtime GPU Variables

| Variable | Default | Options | Purpose |
|----------|---------|---------|---------|
| `GPU_TIER` | consumer | consumer, prosumer, datacenter | GPU tier detection |
| `GPU_MEMORY_MODE` | auto | auto, full, sequential_cpu_offload, model_cpu_offload | Memory management |
| `COMFYUI_ARGS` | (empty) | --lowvram, --medvram, --cpu-vae, etc. | ComfyUI VRAM flags |

### Runtime Model Variables

| Variable | Default | Size | Purpose |
|----------|---------|------|---------|
| `ENABLE_VIBEVOICE` | false | 18GB | VibeVoice TTS |
| `VIBEVOICE_MODEL` | Large | 18GB | Model size: 1.5B, Large, Large-Q8 |
| `WAN_720P` | false | 25GB | WAN 2.1 720p video |
| `WAN_480P` | false | 12GB | WAN 2.1 480p video |
| `ENABLE_WAN22_DISTILL` | false | 28GB | WAN 2.2 TurboDiffusion I2V |
| `ENABLE_I2V` | false | 14GB | Image-to-Video capability |
| `ENABLE_CONTROLNET` | true | 3.6GB | ControlNet preprocessors |
| `ENABLE_ILLUSTRIOUS` | false | 6.5GB | Realism Illustrious SDXL |
| `ENABLE_ZIMAGE` | false | 21GB | Z-Image Turbo |
| `ENABLE_QWEN_EDIT` | false | 13-54GB | Qwen instruction-based editing |
| `QWEN_EDIT_MODEL` | Q4_K_M | 13GB | Quantization: Q2_K, Q3_K_M, Q4_K_M, Q5_K_M, Q6_K, Q8_0, full |
| `ENABLE_GENFOCUS` | false | 12GB | Genfocus DoF refocusing |
| `ENABLE_MVINVERSE` | false | 8GB | MVInverse multi-view rendering |
| `ENABLE_FLASHPORTRAIT` | false | 60GB | FlashPortrait animation |
| `ENABLE_STORYMEM` | false | 20GB+ | StoryMem multi-shot video |
| `ENABLE_INFCAM` | false | 50GB+ | InfCam camera control (datacenter only) |
| `ENABLE_STEADYDANCER` | false | 33GB | SteadyDancer video |
| `ENABLE_SCAIL` | false | 28GB | SCAIL facial mocap |
| `ENABLE_VACE` | false | 28GB | WAN VACE video editing |
| `ENABLE_FUN_INP` | false | 28GB | Fun InP frame interpolation |

### Runtime Storage Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `STORAGE_MODE` | auto | persistent, ephemeral, auto |
| `COMFYUI_PORT` | 8188 | ComfyUI web port |
| `ENABLE_R2_SYNC` | false | Enable R2 output sync |
| `R2_BUCKET` | runpod | R2 bucket name |
| `R2_ENDPOINT` | (configured) | R2 endpoint URL |

### Runtime Development Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `PUBLIC_KEY` | (empty) | SSH public key for access |
| `JUPYTER_PASSWORD` | (empty) | JupyterLab password |
| `UPDATE_NODES_ON_START` | false | Update custom nodes on startup |

### CivitAI Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CIVITAI_API_KEY` | (empty) | API key for CivitAI downloads |
| `CIVITAI_LORAS` | (empty) | Comma-separated LoRA version IDs |
| `ILLUSTRIOUS_LORAS` | (empty) | Comma-separated Illustrious LoRA IDs |
| `ENABLE_CIVITAI` | false | Enable CivitAI LoRA downloads |

---

## Secrets Management

### RunPod Secrets Configuration

**Never expose credentials in plain text.** Use [RunPod Secrets](https://docs.runpod.io/pods/templates/secrets) for secure credential storage:

1. **Create secrets in RunPod Console**:
   - Go to **Settings > Secrets**
   - Create `r2_access_key` with your R2 Access Key ID
   - Create `r2_secret_key` with your R2 Secret Access Key

2. **Reference in pod template** using `RUNPOD_SECRET_` prefix:

```bash
--env "R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}"
--env "R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}"
```

### Secret Variables

| Secret Name | Variable | Purpose |
|-------------|----------|---------|
| `r2_access_key` | `R2_ACCESS_KEY_ID` | R2 Access Key ID |
| `r2_secret_key` | `R2_SECRET_ACCESS_KEY` | R2 Secret Access Key |
| `civitai_api_key` | `CIVITAI_API_KEY` | CivitAI API key (optional) |

### Security Best Practices

- **Never commit secrets to git**: Add `.env*`, `secrets.yaml` to `.gitignore`
- **Use separate credentials**: Don't reuse R2 credentials across projects
- **Rotate regularly**: Periodically rotate R2 access keys
- **Audit access**: Monitor R2 bucket access logs

---

## Best Practices and Recommendations

### Deployment Recommendations

1. **Use Secure Cloud (US)**: Fastest startup (37 sec) and reliable network (51 MB/s)
2. **Pre-bake models**: Use GitHub Actions `bake_wan_720p=true` for faster pod starts
3. **Enable R2 Sync**: Protect against RunPod's ephemeral storage with automatic uploads
4. **Use GPU tier matching**: Match model configuration to available VRAM
5. **Enable monitoring**: Use JupyterLab for development, SSH for maintenance

### Model Selection Guidelines

| Use Case | Recommended Configuration | VRAM Needed |
|----------|---------------------------|-------------|
| Image generation | Illustrious + ControlNet | 8-12 GB |
| Video generation (fast) | WAN 2.1 480p | 12-16 GB |
| Video generation (quality) | WAN 2.1 720p | 24 GB |
| Video generation (turbo) | WAN 2.2 Distilled | 24 GB |
| TTS voice cloning | VibeVoice Large | 16 GB |
| Image editing | Qwen-Edit Q4_K_M | 13 GB |
| Multi-view | MVInverse | 8 GB |
| Portrait animation | FlashPortrait | 30-60 GB |

### Performance Optimization

1. **Quantization**: Use GGUF quantized models (Q4_K_M, Q5_K_M) to reduce VRAM
2. **Sequential offload**: Use `GPU_MEMORY_MODE=sequential_cpu_offload` for limited VRAM
3. **Model caching**: Enable persistent storage to avoid re-downloading models
4. **Batch processing**: Use A6000 or A100 for batch video generation
5. **Startup optimization**: Pre-bake frequently used models in Docker image

### Cost Optimization

1. **Spot instances**: Use for non-critical workloads (60-70% savings)
2. **480p models**: Use when high resolution not required (50% storage savings)
3. **Quantized inference**: Use Q4_K_M or Q5_K_M for 30-50% VRAM savings
4. **Community Cloud**: Use for development/testing (free startup)
5. **Volume sizing**: Allocate only needed storage (minimum 15GB)

### Monitoring and Maintenance

1. **Check logs**: Monitor `/var/log/download_models.log` and `/var/log/r2_sync.log`
2. **Verify uploads**: Use `python3 /upload_to_r2.py --test` to test R2 connection
3. **Monitor GPU**: Use `nvidia-smi` to track VRAM usage
4. **Update nodes**: Set `UPDATE_NODES_ON_START=true` for latest custom nodes
5. **Backup R2**: Enable R2 lifecycle rules for automatic backup

### Troubleshooting

**Common Issues**:

1. **OOM Errors**: Reduce VRAM usage with `--lowvram` or use quantized models
2. **Model Download Failures**: Check HuggingFace/CivitAI API access
3. **R2 Upload Failures**: Verify R2 credentials and endpoint URL
4. **Slow Startup**: Use pre-baked models or community cloud for testing
5. **SSH Access Issues**: Check `PUBLIC_KEY` format and permissions

**Diagnostic Commands**:

```bash
# Check GPU and VRAM
nvidia-smi

# Check R2 sync daemon
ps aux | grep r2_sync

# Test R2 connection
python3 /upload_to_r2.py --test

# View download logs
tail -50 /var/log/download_models.log

# View R2 sync logs
tail -50 /var/log/r2_sync.log

# List downloaded models
ls -lh /workspace/ComfyUI/models/diffusion_models/

# Check container status
docker ps | grep hearmeman
```

---

## Quick Reference Commands

### Local Docker Development

```bash
# Build and start
cd docker
docker compose build
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Start with specific profile
docker compose --profile chatterbox up -d
```

### R2 Operations

```bash
# Test connection
python3 /upload_to_r2.py --test

# Upload file
python3 /upload_to_r2.py /path/to/file.png

# Upload with prefix
python3 /upload_to_r2.py --prefix videos /path/to/video.mp4

# List R2 contents
aws s3 ls s3://runpod/outputs/ \
    --endpoint-url https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com
```

### GitHub Actions

```bash
# Manual trigger (via GitHub UI)
# Navigate to: Actions > Build and Push Docker Image > Run workflow

# With custom parameters (bake models):
# - bake_wan_720p: true
# - image_tag: custom-tag
```

### RunPod Management

```bash
# Create pod
~/.local/bin/runpodctl create pod --name "my-pod" --imageName "ghcr.io/user/hearmeman-extended:latest" ...

# List pods
~/.local/bin/runpodctl list pods

# Stop pod
~/.local/bin/runpodctl stop pod $POD_ID

# View pod logs
~/.local/bin/runpodctl logs $POD_ID
```

---

## Document Information

| Field | Value |
|-------|-------|
| **Author** | oz + claude-haiku-4-5 |
| **Date** | 2026-01-17 |
| **Version** | 1.0 |
| **Status** | Complete |
| **Location** | /home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/research/06-deployment-ci-cd.md |

---

*Documentation complete. All deployment, CI/CD, and RunPod integration systems documented.*
