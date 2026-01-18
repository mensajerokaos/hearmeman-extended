---
author: oz
model: claude-haiku-4-5-20251001
date: 2025-12-29
task: Research Docker infrastructure for RunPod AI system
---

# Docker Infrastructure Documentation - RunPod AI System

## Executive Summary

This document provides comprehensive documentation of the Docker infrastructure for the RunPod AI generation system. The system uses a multi-layered Docker build with ComfyUI as the core interface, supporting various AI models for image generation, video synthesis, and text-to-speech.

**Repository**: `mensajerokaos/hearmeman-extended` (GHCR)
**Base Image**: `runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04`
**Build Layers**: 6 distinct layers for dependencies, ComfyUI, custom nodes, models, and configuration

---

## Table of Contents

1. [Dockerfile Analysis](#1-dockerfile-analysis)
2. [docker-compose.yml Services](#2-docker-composeyml-services)
3. [start.sh Startup Logic](#3-startsh-startup-logic)
4. [download_models.sh Model Downloads](#4-download_modelssh-model-downloads)
5. [scripts/ Directory](#5-scripts-directory)
6. [Configuration Reference](#6-configuration-reference)
7. [Environment Variables](#7-environment-variables)
8. [Known Issues & Quirks](#8-known-issues--quirks)

---

## 1. Dockerfile Analysis

**File**: `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile` (260 lines)

### 1.1 Base Image & Build Arguments

```dockerfile
ARG BASE_IMAGE=runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04
FROM ${BASE_IMAGE}

# Build arguments
ARG COMFYUI_COMMIT=latest
ARG DEBIAN_FRONTEND=noninteractive

# Build-time model downloads (bakes models into image)
ARG BAKE_WAN_720P=false
ARG BAKE_WAN_480P=false
ARG BAKE_ILLUSTRIOUS=false
```

**Base Image Details**:
- PyTorch 2.8.0 with Python 3.11
- CUDA 12.8.1 with cuDNN 9
- Ubuntu 22.04 LTS
- Optimized for RunPod GPU instances

### 1.2 Environment Variables

```dockerfile
ENV PYTHONUNBUFFERED=1
ENV SHELL=/bin/bash
ENV COMFYUI_PORT=8188
```

**GPU Tier Configuration**:
```dockerfile
ENV GPU_TIER="consumer"  # consumer, prosumer, datacenter
# Tier 1: Consumer GPU (8-24GB VRAM)
ENV ENABLE_GENFOCUS="false"
ENV ENABLE_QWEN_EDIT="false"
ENV QWEN_EDIT_MODEL="Q4_K_M"  # Options: Q4_K_M (13GB), Q5_K_M (15GB), Q8_0 (22GB), full (54GB)
ENV ENABLE_MVINVERSE="false"

# Tier 2: Prosumer GPU (24GB+ with CPU offload)
ENV ENABLE_FLASHPORTRAIT="false"
ENV ENABLE_STORYMEM="false"

# Tier 3: Datacenter GPU (48-80GB VRAM - A100/H100)
ENV ENABLE_INFCAM="false"

# GPU Memory Management
ENV GPU_MEMORY_MODE="auto"  # Options: auto, full, sequential_cpu_offload, model_cpu_offload

# R2 Configuration
ENV ENABLE_R2_SYNC="false"
ENV R2_ENDPOINT="https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com"
ENV R2_BUCKET="runpod"
ENV R2_ACCESS_KEY_ID=""
ENV R2_SECRET_ACCESS_KEY=""

ENV COMFYUI_ARGS=""  # Additional: --lowvram, --medvram, --novram, --cpu-vae
```

### 1.3 Layer 1: System Dependencies (Lines 59-78)

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

**Installed Packages**:
- `git` + `git-lfs`: Version control and large file support
- `wget`, `curl`: Download utilities with resume support
- `vim`: Text editor for debugging
- `ffmpeg`: Media processing (video/audio)
- `libsm6`, `libxext6`, `libgl1-mesa-glx`: OpenGL for GPU rendering
- `openssh-server`: SSH access for remote debugging
- `aria2`: Parallel download utility
- `inotify-tools`: File system monitoring (for R2 sync daemon)

### 1.4 Layer 2: ComfyUI Base (Lines 82-86)

```dockerfile
WORKDIR /workspace
RUN git clone https://github.com/comfyanonymous/ComfyUI.git && \
    cd ComfyUI && \
    pip install --no-cache-dir -r requirements.txt
```

**ComfyUI Installation**:
- Clones latest ComfyUI from GitHub
- Installs all base requirements from `requirements.txt`
- `--no-cache-dir` reduces image size

### 1.5 Layer 3: Custom Nodes (Lines 89-130)

**Baked-in Custom Nodes** (cloned at build time):

```dockerfile
WORKDIR /workspace/ComfyUI/custom_nodes

# 1. ComfyUI-Manager (Line 93-94)
RUN git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Manager.git

# 2. VibeVoice-ComfyUI (Lines 96-99) - Multi-speaker TTS with voice cloning
RUN git clone --depth 1 https://github.com/Enemyx-net/VibeVoice-ComfyUI.git && \
    cd VibeVoice-ComfyUI && \
    pip install --no-cache-dir -r requirements.txt || true

# 3. ComfyUI-Chatterbox (Lines 101-104) - Zero-shot voice cloning TTS
RUN git clone --depth 1 https://github.com/thefader/ComfyUI-Chatterbox.git && \
    cd ComfyUI-Chatterbox && \
    pip install --no-cache-dir -r requirements.txt || true

# 4. ComfyUI-SCAIL-Pose (Line 107) - Facial mocap
RUN git clone --depth 1 https://github.com/kijai/ComfyUI-SCAIL-Pose.git

# 5. ControlNet Preprocessors (Lines 109-112)
RUN git clone --depth 1 https://github.com/Fannovel16/comfyui_controlnet_aux.git && \
    cd comfyui_controlnet_aux && \
    pip install --no-cache-dir -r requirements.txt || true

# 6. TurboDiffusion (Lines 114-117) - 100-200x video speedup
RUN git clone --depth 1 https://github.com/anveshane/Comfyui_turbodiffusion.git && \
    cd Comfyui_turbodiffusion && \
    pip install --no-cache-dir -r requirements.txt || true

# 7. ComfyUI-WanVideoWrapper (Lines 119-122) - WAN 2.2/2.5 video nodes
RUN git clone --depth 1 https://github.com/kijai/ComfyUI-WanVideoWrapper.git && \
    cd ComfyUI-WanVideoWrapper && \
    pip install --no-cache-dir -r requirements.txt || true

# 8. ComfyUI-VideoHelperSuite (Lines 124-127) - Video utilities
RUN git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git && \
    cd ComfyUI-VideoHelperSuite && \
    pip install --no-cache-dir -r requirements.txt || true

# 9. CivitAI Integration (Line 130)
RUN pip install --no-cache-dir civitai-downloader
```

### 1.6 Layer 3.5: Custom AI Model Wrappers (Lines 133-143)

**Local Custom Nodes** (copied from project):

```dockerfile
# ComfyUI-Genfocus (Lines 135-138) - Depth-of-Field Refocusing
COPY custom_nodes/ComfyUI-Genfocus /workspace/ComfyUI/custom_nodes/ComfyUI-Genfocus
RUN cd /workspace/ComfyUI/custom_nodes/ComfyUI-Genfocus && \
    pip install --no-cache-dir -r requirements.txt || true

# ComfyUI-MVInverse (Lines 140-143) - Multi-view Inverse Rendering
COPY custom_nodes/ComfyUI-MVInverse /workspace/ComfyUI/custom_nodes/ComfyUI-MVInverse
RUN cd /workspace/ComfyUI/custom_nodes/ComfyUI-MVInverse && \
    pip install --no-cache-dir -r requirements.txt || true
```

### 1.7 Layer 4: Additional Dependencies (Lines 146-177)

```dockerfile
WORKDIR /workspace
RUN pip install --no-cache-dir \
    huggingface_hub \
    accelerate \
    safetensors \
    boto3 \
    sentencepiece \
    protobuf \
    # New dependencies for AI models
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
    # Dependencies for custom nodes
    audiotsm \
    loguru \
    # Dependencies for Genfocus/MVInverse
    diffusers>=0.21.0 \
    peft>=0.4.0 \
    opencv-python>=4.5.0 \
    timm \
    # NVIDIA GPU management (for TurboDiffusion)
    pynvml
```

**Key Dependencies**:
- `huggingface_hub`: Model downloads from HuggingFace
- `boto3`: S3 client for R2 uploads
- `cupy-cuda12x`: CUDA-accelerated NumPy
- `imageio[ffmpeg]`: Video I/O
- `diffusers`: HuggingFace diffusion models
- `peft`: Parameter-Efficient Fine-Tuning (LoRA support)
- `opencv-python`: Image processing
- `pynvml`: NVIDIA GPU monitoring

**Flash Attention**: Disabled by default (line 179-181) due to ABI compatibility issues with kornia

### 1.8 Layer 5: Scripts and Configuration (Lines 183-202)

```dockerfile
COPY start.sh /start.sh
COPY download_models.sh /download_models.sh
COPY upload_to_r2.py /upload_to_r2.py
COPY r2_sync.sh /r2_sync.sh
RUN chmod +x /start.sh /download_models.sh /r2_sync.sh

# Copy example workflows
COPY workflows/ /workspace/ComfyUI/user/default/workflows/

# SSH configuration
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Create model directories
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision,genfocus,qwen,mvinverse,flashportrait,storymem,infcam}
```

**Model Directory Structure**:
```
/workspace/ComfyUI/models/
├── checkpoints/          # Main model checkpoints (SDXL, Illustrious, etc.)
├── embeddings/           # Textual inversions, negative embeddings
├── vibevoice/           # VibeVoice TTS models
├── text_encoders/       # UMT5-XXL, Qwen for WAN
├── diffusion_models/    # WAN 2.1/2.2, Stable Diffusion, TurboDiffusion
├── vae/                 # VAE models
├── controlnet/          # ControlNet models
├── loras/               # LoRA adaptations
├── clip_vision/         # CLIP Vision for I2V
├── genfocus/            # Genfocus deblur/bokeh models
├── qwen/                # Qwen-Image-Edit GGUF models
├── mvinverse/           # MVInverse repository
├── flashportrait/       # FlashPortrait model
├── storymem/            # StoryMem LoRAs
└── infcam/              # InfCam model
```

### 1.9 Layer 6: Build-time Model Downloads (Lines 204-250)

**Optional Models Baked into Image** (reduces startup time):

```dockerfile
ARG BAKE_WAN_720P
ARG BAKE_WAN_480P
ARG BAKE_ILLUSTRIOUS

# WAN 2.1 720p Models (~25GB)
RUN if [ "$BAKE_WAN_720P" = "true" ]; then \
    wget -q --show-progress -O /workspace/ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors \
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" && \
    # ... more downloads
    fi

# WAN 2.1 480p Models (~12GB)
RUN if [ "$BAKE_WAN_480P" = "true" ]; then \
    # ... downloads for 1.3B model
    fi

# Illustrious XL Models (~6.5GB)
RUN if [ "$BAKE_ILLUSTRIOUS" = "true" ]; then \
    wget -q --show-progress -O /workspace/ComfyUI/models/checkpoints/illustrious_realism_v10.safetensors \
        "https://civitai.com/api/download/models/2091367" && \
    # ... embedding downloads
    fi
```

### 1.10 Port Expose & Entry Point (Lines 252-259)

```dockerfile
EXPOSE 22 8188 8888

WORKDIR /workspace/ComfyUI

ENTRYPOINT ["/start.sh"]
```

**Exposed Ports**:
- `22`: SSH server
- `8188`: ComfyUI web interface
- `8888`: JupyterLab (optional)

---

## 2. docker-compose.yml Services

**File**: `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml` (88 lines)

### 2.1 Service Overview

```yaml
version: '3.8'

services:
  chatterbox:        # Chatterbox TTS (Resemble AI)
  hearmeman-extended:  # Main ComfyUI service

volumes:
  models:
  output:
```

### 2.2 Chatterbox TTS Service (Lines 6-30)

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

**Chatterbox Details**:
- Zero-shot voice cloning TTS
- OpenAI-compatible API: `http://localhost:8000/v1/audio/speech`
- Health check: `http://localhost:8000/health`
- Separate container due to different runtime requirements

### 2.3 Hearmeman Extended Service (Lines 36-83)

```yaml
hearmeman-extended:
  build:
    context: .
    dockerfile: Dockerfile
  image: hearmeman-extended:local
  container_name: hearmeman-extended
  runtime: nvidia
  environment:
    - NVIDIA_VISIBLE_DEVICES=all
    # Existing models
    - ENABLE_VIBEVOICE=true
    - ENABLE_CONTROLNET=true
    - ENABLE_ILLUSTRIOUS=false
    - ENABLE_ZIMAGE=false
    - VIBEVOICE_MODEL=Large
    - STORAGE_MODE=persistent
    - COMFYUI_PORT=8188
    # GPU Configuration
    - GPU_TIER=consumer
    - GPU_MEMORY_MODE=auto
    # Tier 1: Consumer GPU
    - ENABLE_GENFOCUS=true
    - ENABLE_QWEN_EDIT=true
    - QWEN_EDIT_MODEL=Q4_K_M
    - ENABLE_MVINVERSE=true
    # Tier 2: Prosumer GPU
    - ENABLE_FLASHPORTRAIT=false
    - ENABLE_STORYMEM=false
    # Tier 3: Datacenter GPU
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

### 2.4 Named Volumes

```yaml
volumes:
  models:      # Local model storage
  output:      # Generated outputs
```

### 2.5 Additional Compose Files

#### docker-compose.illustrious.yml (51 lines)
Dedicated configuration for Illustrious-only deployments:

```yaml
services:
  illustrious:
    environment:
      # Disable everything else
      - ENABLE_VIBEVOICE=false
      - ENABLE_CONTROLNET=false
      - ENABLE_ZIMAGE=false
      # Only Illustrious
      - ENABLE_ILLUSTRIOUS=true
      - ENABLE_ILLUSTRIOUS_EMBEDDINGS=true
      # CivitAI NSFW LoRAs
      - ENABLE_CIVITAI=true
      - CIVITAI_API_KEY=${CIVITAI_API_KEY}
      - CIVITAI_LORAS=1906687,1736657
```

#### docker-compose.wan22-test.yml (91 lines)
Test configuration for WAN 2.2 distilled models:

```yaml
services:
  # Dry-run test (no downloads)
  wan22-test-dry:
    environment:
      - DRY_RUN=true
      - ENABLE_WAN22_DISTILL=true
    entrypoint: [/bin/bash, -c]
    command: ["/download_models.sh && echo '=== DRY RUN COMPLETE ==='"]
    profiles:
      - test

  # Real download test (~28GB)
  wan22-test:
    environment:
      - DRY_RUN=false
      - ENABLE_WAN22_DISTILL=true
      - DOWNLOAD_TIMEOUT=3600
    volumes:
      - ./models:/workspace/ComfyUI/models
    profiles:
      - test

  # Full ComfyUI with WAN 2.2
  comfyui-wan22:
    environment:
      - ENABLE_WAN22_DISTILL=true
    ports:
      - "8188:8188"
    profiles:
      - gpu
```

---

## 3. start.sh Startup Logic

**File**: `/home/oz/projects/2025/oz/12/runpod/docker/start.sh` (166 lines)

### 3.1 Storage Mode Detection (Lines 13-27)

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

DETECTED_STORAGE=$(detect_storage_mode)
export STORAGE_MODE="$DETECTED_STORAGE"
```

**Storage Modes**:
- `persistent`: Uses mounted storage (RunPod volume)
- `ephemeral`: Uses container-local storage (loses data on restart)
- `auto`: Auto-detects based on `/workspace` mount point

### 3.2 GPU VRAM Detection & Configuration (Lines 36-91)

```bash
detect_gpu_config() {
    # Detect GPU VRAM in MB
    GPU_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -n 1)

    if [ -z "$GPU_VRAM" ]; then
        echo "  [Warning] Could not detect GPU VRAM, using defaults"
        GPU_VRAM=0
    fi

    echo "[GPU] Detected VRAM: ${GPU_VRAM} MB"

    # Auto-detect GPU tier if not set
    if [ -z "$GPU_TIER" ] || [ "$GPU_TIER" = "auto" ]; then
        if (( GPU_VRAM >= 48000 )); then
            export GPU_TIER="datacenter"  # A100/H100 (48GB+)
        elif (( GPU_VRAM >= 20000 )); then
            export GPU_TIER="prosumer"     # RTX 4090 (24GB)
        else
            export GPU_TIER="consumer"      # RTX 4080, 3080 (8-16GB)
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

**VRAM Thresholds**:
| VRAM | Tier | Memory Mode | ComfyUI Args |
|------|------|-------------|--------------|
| < 8GB | consumer | sequential_cpu_offload | --lowvram --cpu-vae --force-fp16 |
| 8-12GB | consumer | sequential_cpu_offload | --lowvram --force-fp16 |
| 12-16GB | consumer | model_cpu_offload | --medvram --cpu-text-encoder --force-fp16 |
| 16-24GB | prosumer | model_cpu_offload | --normalvram --force-fp16 |
| 24-48GB | prosumer | full | (none) |
| 48GB+ | datacenter | full | (none) |

### 3.3 SSH Setup (Lines 97-105)

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

### 3.4 JupyterLab Setup (Lines 109-120)

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

### 3.5 Custom Node Updates (Lines 124-133)

```bash
if [ "${UPDATE_NODES_ON_START:-false}" = "true" ]; then
    echo "[Nodes] Updating custom nodes..."
    for dir in /workspace/ComfyUI/custom_nodes/*/; do
        if [ -d "$dir/.git" ]; then
            echo "  Updating: $(basename $dir)"
            cd "$dir" && git pull --quiet || true
        fi
    done
fi
```

### 3.6 Model Downloads (Lines 137-139)

```bash
echo "[Models] Starting model downloads..."
/download_models.sh
```

### 3.7 R2 Sync Daemon Setup (Lines 143-150)

```bash
if [ "${ENABLE_R2_SYNC:-false}" = "true" ]; then
    echo "[R2 Sync] Starting background sync daemon..."
    mkdir -p /workspace/ComfyUI/output
    nohup /r2_sync.sh > /var/log/r2_sync_init.log 2>&1 &
    echo "[R2 Sync] Daemon active, monitoring /workspace/ComfyUI/output"
fi
```

### 3.8 ComfyUI Startup (Lines 154-166)

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

**ComfyUI Arguments**:
- `--listen 0.0.0.0`: Accept connections from all interfaces
- `--enable-cors-header`: Allow cross-origin requests
- `--preview-method auto`: Auto-select preview generation method

---

## 4. download_models.sh Model Downloads

**File**: `/home/oz/projects/2025/oz/12/runpod/docker/download_models.sh` (751 lines)

### 4.1 Configuration (Lines 5-21)

```bash
LOG_FILE="/var/log/download_models.log"
DRY_RUN="${DRY_RUN:-false}"
DOWNLOAD_TIMEOUT="${DOWNLOAD_TIMEOUT:-1800}"  # 30 min default
```

### 4.2 Helper Functions

#### download_model() (Lines 28-73)
Generic download with resume support:

```bash
download_model() {
    local URL="$1"
    local DEST="$2"
    local EXPECTED_SIZE="${3:-}"

    if [ -f "$DEST" ]; then
        local SIZE=$(stat -c%s "$DEST" 2>/dev/null || echo "0")
        if [ "$SIZE" -gt 1000000 ]; then  # >1MB means likely complete
            echo "  [Skip] $NAME already exists ($(numfmt --to=iec $SIZE))"
            return 0
        fi
        echo "  [Resume] $NAME incomplete, resuming..."
    fi

    if [ "$DRY_RUN" = "true" ]; then
        echo "  [DRY-RUN] Would download: $NAME ${EXPECTED_SIZE:+($EXPECTED_SIZE)}"
        return 0
    fi

    # Try wget with progress bar
    local WGET_EXIT=0
    timeout "$DOWNLOAD_TIMEOUT" wget -c --progress=bar:force:noscroll -O "$DEST" "$URL" 2>&1 || WGET_EXIT=$?

    if [ $WGET_EXIT -ne 0 ]; then
        echo "  [Warn] wget failed (exit $WGET_EXIT), trying curl..."
        timeout "$DOWNLOAD_TIMEOUT" curl -L -C - --progress-bar -o "$DEST" "$URL" || {
            echo "  [ERROR] Failed to download $NAME after wget and curl attempts"
            rm -f "$DEST"
            return 1
        }
    fi
}
```

**Features**:
- Resume incomplete downloads with `-c` flag
- Fallback from wget to curl
- Progress bar display
- File size verification
- Dry run mode for testing

#### hf_download() (Lines 75-82)
HuggingFace download helper:

```bash
hf_download() {
    local REPO="$1"
    local FILE="$2"
    local DEST="$3"
    local EXPECTED_SIZE="${4:-}"
    download_model "https://huggingface.co/${REPO}/resolve/main/${FILE}" "$DEST" "$EXPECTED_SIZE"
}
```

#### civitai_download() (Lines 84-120)
CivitAI download with API key support:

```bash
civitai_download() {
    local VERSION_ID="$1"
    local TARGET_DIR="$2"
    local DESCRIPTION="${3:-CivitAI asset}"

    local URL="https://civitai.com/api/download/models/${VERSION_ID}"
    if [ -n "$CIVITAI_API_KEY" ]; then
        URL="${URL}?token=${CIVITAI_API_KEY}"
    fi

    # Try wget with explicit redirect handling first
    if wget --version >/dev/null 2>&1; then
        wget -c -q --show-progress \
            --max-redirect=10 \
            --content-disposition \
            -P "$TARGET_DIR" \
            "$URL" 2>/dev/null && return 0
    fi

    # Fallback to curl
    curl -L -C - -o "$TARGET_DIR/$FILENAME" "$URL" || {
        echo "  [Error] Failed: $VERSION_ID"
        return 1
    }
}
```

**Features**:
- API key authentication
- Automatic filename detection from Content-Disposition
- Max redirect handling (10 redirects)

#### hf_snapshot_download() (Lines 125-152)
HuggingFace snapshot download (full repository):

```bash
hf_snapshot_download() {
    local REPO="$1"
    local DEST="$2"

    if [ -d "$DEST" ] && [ "$(ls -A "$DEST" 2>/dev/null)" ]; then
        echo "  [Skip] $NAME already exists"
        return 0
    fi

    python3 -c "
from huggingface_hub import snapshot_download
try:
    snapshot_download('$REPO',
        local_dir='$DEST',
        local_dir_use_symlinks=False)
    print('  [OK] $NAME downloaded successfully')
except Exception as e:
    print(f'  [Error] Failed to download $NAME: {e}', file=sys.stderr)
    sys.exit(1)
"
}
```

### 4.3 Model Download Sections

#### VibeVoice Models (Lines 155-193)
```bash
if [ "${ENABLE_VIBEVOICE:-false}" = "true" ]; then
    case "${VIBEVOICE_MODEL:-Large}" in
        "1.5B")
            hf_snapshot_download "microsoft/VibeVoice-1.5B" "$MODELS_DIR/vibevoice/VibeVoice-1.5B"
            ;;
        "Large")
            hf_snapshot_download "aoi-ot/VibeVoice-Large" "$MODELS_DIR/vibevoice/VibeVoice-Large"
            ;;
        "Large-Q8")
            hf_snapshot_download "FabioSarracino/VibeVoice-Large-Q8" "$MODELS_DIR/vibevoice/VibeVoice-Large-Q8"
            ;;
    esac

    # Download Qwen tokenizer (required for VibeVoice)
    TOKENIZER_DIR="$MODELS_DIR/vibevoice/tokenizer"
    if [ ! -f "$TOKENIZER_DIR/tokenizer.json" ]; then
        echo "[VibeVoice] Downloading Qwen tokenizer..."
        mkdir -p "$TOKENIZER_DIR"
        wget -q -O "$TOKENIZER_DIR/tokenizer_config.json" \
            "https://huggingface.co/Qwen/Qwen2.5-1.5B/resolve/main/tokenizer_config.json"
        # ... more files
    fi
fi
```

#### WAN 2.2 Distilled Models (Lines 267-320)
```bash
if [ "${ENABLE_WAN22_DISTILL:-false}" = "true" ]; then
    echo "[WAN 2.2] Downloading distilled models for TurboDiffusion I2V..."
    # Text encoder (shared - 9.5GB)
    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
        "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
        "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
        "9.5GB"

    # WAN 2.2 High Noise Expert (I2V) - ~14GB FP8
    hf_download "Comfy-Org/Wan_2.2_ComfyUI_Repackaged" \
        "split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors" \
        "$MODELS_DIR/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors" \
        "14GB"

    # WAN 2.2 Low Noise Expert (I2V) - ~14GB FP8
    hf_download "Comfy-Org/Wan_2.2_ComfyUI_Repackaged" \
        "split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors" \
        "$MODELS_DIR/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors" \
        "14GB"
fi
```

#### Qwen-Image-Edit (Lines 505-547)
```bash
if [ "${ENABLE_QWEN_EDIT:-false}" = "true" ]; then
    QWEN_MODEL="${QWEN_EDIT_MODEL:-Q4_K_M}"

    case "$QWEN_MODEL" in
        "full")
            python -c "
from huggingface_hub import snapshot_download
snapshot_download('Qwen/Qwen-Image-Edit-2511',
    local_dir='$MODELS_DIR/qwen/Qwen-Image-Edit-2511',
    local_dir_use_symlinks=False)
"
            ;;
        "Q4_K_M"|"Q5_K_M"|"Q6_K"|"Q8_0"|"Q2_K"|"Q3_K_M")
            GGUF_FILE="qwen-image-edit-2511-${QWEN_MODEL}.gguf"
            GGUF_DEST="$MODELS_DIR/qwen/${GGUF_FILE}"

            if [ ! -f "$GGUF_DEST" ]; then
                python -c "
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id='unsloth/Qwen-Image-Edit-2511-GGUF',
    filename='${GGUF_FILE}',
    local_dir='$MODELS_DIR/qwen',
    local_dir_use_symlinks=False)
"
            fi
            ;;
    esac
fi
```

**Quantization Options**:
| Model | Size | VRAM |
|-------|------|------|
| Q2_K | ~9GB | 13GB |
| Q3_K_M | ~13GB | 15GB |
| Q4_K_M | ~17GB | 18GB |
| Q5_K_M | ~21GB | 22GB |
| Q6_K | ~25GB | 26GB |
| Q8_0 | ~32GB | 34GB |
| full | ~54GB | 54GB |

#### ControlNet Models (Lines 344-382)
```bash
if [ "${ENABLE_CONTROLNET:-true}" = "true" ]; then
    CONTROLNET_LIST="${CONTROLNET_MODELS:-canny,depth,openpose}"
    IFS=',' read -ra MODELS <<< "$CONTROLNET_LIST"

    for model in "${MODELS[@]}"; do
        case "$model" in
            "canny")
                hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
                    "control_v11p_sd15_canny_fp16.safetensors" \
                    "$MODELS_DIR/controlnet/control_v11p_sd15_canny_fp16.safetensors"
                ;;
            "depth")
                hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
                    "control_v11f1p_sd15_depth_fp16.safetensors" \
                    "$MODELS_DIR/controlnet/control_v11f1p_sd15_depth_fp16.safetensors"
                ;;
            "openpose")
                hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
                    "control_v11p_sd15_openpose_fp16.safetensors" \
                    "$MODELS_DIR/controlnet/control_v11p_sd15_openpose_fp16.safetensors"
                ;;
        esac
    done
fi
```

### 4.4 Download Summary (Lines 743-750)

```bash
echo ""
echo "============================================"
echo "[$(date -Iseconds)] Model download complete"
echo "============================================"
echo ""
echo "Downloaded models summary:"
ls -lh "$MODELS_DIR"/*/  2>/dev/null | grep -E "\.safetensors|\.pt|\.ckpt|\.bin" | head -20 || echo "  No models found"
echo ""
```

---

## 5. scripts/ Directory

**File**: `/home/oz/projects/2025/oz/12/runpod/docker/scripts/xtts-vo-gen.py` (225 lines)

### 5.1 XTTS Voice-Over Generator

**Purpose**: Batch TTS generation using XTTS API server

**Usage**:
```bash
# Single line
python xtts-vo-gen.py "Hello world" --output hello.wav

# From file (one line per output)
python xtts-vo-gen.py --file script.txt --output-dir ./vo-output

# Custom voice cloning
python xtts-vo-gen.py "Hello world" --speaker /path/to/reference.wav

# Stream to stdout
python xtts-vo-gen.py "Hello world" --stream | ffplay -
```

**Configuration**:
```python
XTTS_API_URL = os.environ.get("XTTS_API_URL", "http://localhost:8020")

# Built-in speakers
SPEAKERS = ["male", "female", "calm_female"]

# Supported languages
LANGUAGES = {
    "ar": "Arabic", "pt": "Brazilian Portuguese", "zh-cn": "Chinese",
    "cs": "Czech", "nl": "Dutch", "en": "English", "fr": "French",
    "de": "German", "it": "Italian", "pl": "Polish", "ru": "Russian",
    "es": "Spanish", "tr": "Turkish", "ja": "Japanese", "ko": "Korean",
    "hu": "Hungarian", "hi": "Hindi"
}
```

**API Endpoints**:
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tts_to_audio/` | POST | Returns audio bytes directly |
| `/tts_to_file` | POST | Saves to server file path |
| `/tts_stream` | POST | Streams audio chunks |
| `/speakers_list` | GET | List available speakers |
| `/languages` | GET | List supported languages |

**Key Functions**:
- `api_request()`: HTTP requests to XTTS server
- `generate_tts()`: Single TTS generation
- `process_script_file()`: Batch processing from file
- `list_speakers()`: Enumerate available voices
- `list_languages()`: Enumerate supported languages

---

## 6. Configuration Reference

### 6.1 .env File Structure

**File**: `/home/oz/projects/2025/oz/12/runpod/docker/.env.example`

```bash
# SECRETS - Use RunPod Secrets for production!
CIVITAI_API_KEY=your_civitai_api_key_here

# R2 Output Sync
ENABLE_R2_SYNC=false
R2_ENDPOINT=https://your-account.eu.r2.cloudflarestorage.com
R2_BUCKET=runpod
R2_ACCESS_KEY_ID=your_r2_access_key_here
R2_SECRET_ACCESS_KEY=your_r2_secret_key_here

# Model Toggles
ENABLE_VIBEVOICE=true
ENABLE_ZIMAGE=false
ENABLE_ILLUSTRIOUS=true
ENABLE_XTTS=false
ENABLE_CONTROLNET=true
ENABLE_I2V=false
ENABLE_VACE=false
ENABLE_FUN_INP=false
ENABLE_STEADYDANCER=false
ENABLE_SCAIL=false

# WAN Video Generation
WAN_720P=false
WAN_480P=false

# Model Variants
VIBEVOICE_MODEL=Large
CONTROLNET_MODELS=canny,depth,openpose

# CivitAI Integration
ENABLE_CIVITAI=false
CIVITAI_LORAS=
ILLUSTRIOUS_LORAS=

# ComfyUI Settings
COMFYUI_PORT=8188
STORAGE_MODE=persistent
```

---

## 7. Environment Variables

### 7.1 Model Toggles

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_VIBEVOICE` | `false` | VibeVoice TTS with voice cloning |
| `ENABLE_ZIMAGE` | `false` | Z-Image Turbo txt2img |
| `ENABLE_ILLUSTRIOUS` | `false` | Realism Illustrious SDXL |
| `ENABLE_XTTS` | `false` | XTTS v2 multilingual TTS |
| `ENABLE_CONTROLNET` | `true` | ControlNet preprocessors |
| `ENABLE_I2V` | `false` | Image-to-Video (WAN) |
| `ENABLE_VACE` | `false` | Video All-in-One editing |
| `ENABLE_FUN_INP` | `false` | First-Last frame interpolation |
| `ENABLE_STEADYDANCER` | `false` | SteadyDancer dance video |
| `ENABLE_SCAIL` | `false` | SCAIL facial mocap |
| `ENABLE_WAN22_DISTILL` | `false` | WAN 2.2 TurboDiffusion I2V |
| `WAN_720P` | `false` | WAN 2.1 T2V 720p (14B) |
| `WAN_480P` | `false` | WAN 2.2 T2V 480p (1.3B) |

### 7.2 GPU Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GPU_TIER` | `consumer` | GPU tier: consumer, prosumer, datacenter |
| `GPU_MEMORY_MODE` | `auto` | Memory mode: auto, full, sequential_cpu_offload, model_cpu_offload |
| `QWEN_EDIT_MODEL` | `Q4_K_M` | Qwen-Image-Edit quantization |
| `COMFYUI_ARGS` | (empty) | Additional ComfyUI flags |

### 7.3 Storage & Sync

| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_MODE` | `persistent` | Storage mode: persistent, ephemeral, auto |
| `ENABLE_R2_SYNC` | `false` | Enable R2 output sync daemon |
| `R2_ENDPOINT` | (hardcoded) | R2 endpoint URL |
| `R2_BUCKET` | `runpod` | R2 bucket name |
| `R2_ACCESS_KEY_ID` | (empty) | R2 access key |
| `R2_SECRET_ACCESS_KEY` | (empty) | R2 secret key |

### 7.4 Development

| Variable | Default | Description |
|----------|---------|-------------|
| `DRY_RUN` | `false` | Test download script without downloading |
| `DOWNLOAD_TIMEOUT` | `1800` | Download timeout in seconds (30 min) |
| `UPDATE_NODES_ON_START` | `false` | Update custom nodes on startup |
| `PUBLIC_KEY` | (empty) | SSH public key for access |
| `JUPYTER_PASSWORD` | (empty) | JupyterLab password |

---

## 8. Known Issues & Quirks

### 8.1 From TESTING-NOTES.md

**Genfocus BokehNet Tensor Size Mismatch**:
- **Issue**: Tensor size mismatch at `bokeh.py` line 243
- **Cause**: `avg_pool2d` with padding produces 1px larger output
- **Fix**: Add interpolation to resize blur_amount to match image dimensions

**MVInverse HuggingFace Model Loading**:
- **Issue**: Loader tried to download non-existent `mvinverse.pt`
- **Cause**: Model uses `PyTorchModelHubMixin.from_pretrained()`
- **Fix**: Use `MVInverse.from_pretrained("maddog241/mvinverse")` instead

### 8.2 Shell Quirks (From TESTING-NOTES.md)

- `jq` parse errors with complex nested JSON in zsh - use Python instead
- Docker cp with mounted volumes can fail with permission errors
- Mounted volumes already sync files - no need to copy

### 8.3 VRAM Management (From TESTING-NOTES.md)

- 16GB VRAM limits: Use 768x768 resolution for image generation
- Models load sequentially - don't run multiple workflows in parallel
- Container may restart on OOM - reduce resolution/steps if this happens

### 8.4 Common Issues

**Flash Attention Compatibility**:
- Disabled by default due to ABI compatibility issues with kornia
- Uncomment only if you need FlashPortrait/InfCam and have matching CUDA/PyTorch

**CivitAI Redirect Handling**:
- Downloads require `--max-redirect=10` for CivitAI redirects
- Fallback to curl if wget fails

**Docker Build-Time Downloads**:
- Optional model downloads at build time require separate ARG declarations after FROM
- Use `BAKE_WAN_720P=true`, `BAKE_WAN_480P=true`, or `BAKE_ILLUSTRIOUS=true`

---

## Quick Reference: Build & Run Commands

```bash
# Build main image
cd docker
docker compose build

# Start all services
docker compose up -d

# Start with specific profile
docker compose --profile chatterbox up -d

# Run Illustrious-only container
docker compose -f docker-compose.illustrious.yml up -d

# Test WAN 2.2 downloads (dry-run)
docker compose -f docker-compose.wan22-test.yml run --rm wan22-test-dry

# Test WAN 2.2 downloads (real - ~28GB)
docker compose -f docker-compose.wan22-test.yml run --rm wan22-test

# View logs
docker logs -f hearmeman-extended

# SSH into container
ssh root@localhost -p 2222
```

---

## File Locations Summary

| File | Path |
|------|------|
| Main Dockerfile | `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile` |
| Main compose | `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml` |
| Illustrious compose | `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.illustrious.yml` |
| WAN 2.2 test compose | `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.wan22-test.yml` |
| Startup script | `/home/oz/projects/2025/oz/12/runpod/docker/start.sh` |
| Download script | `/home/oz/projects/2025/oz/12/runpod/docker/download_models.sh` |
| R2 upload script | `/home/oz/projects/2025/oz/12/runpod/docker/upload_to_r2.py` |
| R2 sync daemon | `/home/oz/projects/2025/oz/12/runpod/docker/r2_sync.sh` |
| XTTS generator | `/home/oz/projects/2025/oz/12/runpod/docker/scripts/xtts-vo-gen.py` |
| Environment example | `/home/oz/projects/2025/oz/12/runpod/docker/.env.example` |
| Testing notes | `/home/oz/projects/2025/oz/12/runpod/docker/TESTING-NOTES.md` |
| Custom nodes | `/home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/` |

---

*Documentation generated: 2025-12-29*
*Author: oz + claude-haiku-4.5*
