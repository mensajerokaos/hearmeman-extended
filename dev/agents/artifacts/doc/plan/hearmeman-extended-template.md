---
author: oz
model: claude-opus-4-5
date: 2025-12-24 22:30
task: PRD - Hearmeman Extended RunPod Template
---

# PRD: Hearmeman Extended Template

**Project**: José Obscura - La Maquila Erótica Documentary
**Template Base**: Hearmeman "One Click - ComfyUI Wan t2v i2v VACE" (758dsjwiqz)
**Version**: 1.0
**Last Updated**: 2025-12-24

---

## 1. Executive Summary

Create a custom RunPod template that extends Hearmeman with additional AI capabilities: VibeVoice TTS, SCAIL facial expressions, SteadyDancer dance video, Z-Image Turbo, and ControlNet. The template uses a ~10-15GB Docker image with custom nodes baked in, while models are downloaded on-demand based on environment variables.

### Key Features
- **VibeVoice-ComfyUI**: TTS voice cloning (1.5B/Large/Q8 variants)
- **ComfyUI-XTTS**: Coqui XTTS v2 multilingual TTS with voice cloning
- **ComfyUI-SCAIL-Pose**: Facial expression animation
- **SteadyDancer**: Dance/motion video generation
- **Z-Image Turbo**: Fast 6B image generation
- **ControlNet**: Full suite of preprocessors and models
- **ComfyUI-Manager**: Dynamic node installation
- **TurboDiffusion**: 100-200x faster video generation (WAN 2.1/2.2 compatible)
- **CivitAI Integration**: API key support for anime/NSFW LoRA downloads

### Design Principles
1. **Code baked, models on-demand**: Small image, fast cold starts
2. **Environment-driven**: Feature toggles via env vars
3. **Storage-aware**: Detect persistent vs ephemeral storage
4. **Resume-capable**: Downloads resume on interruption

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HEARMEMAN EXTENDED TEMPLATE                         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        DOCKER IMAGE (~12GB)                         │   │
│  │                                                                     │   │
│  │  Base: runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22  │   │
│  │                                                                     │   │
│  │  Custom Nodes (baked in):                                           │   │
│  │  ├── ComfyUI-Manager                                                │   │
│  │  ├── VibeVoice-ComfyUI                                              │   │
│  │  ├── ComfyUI-SCAIL-Pose                                             │   │
│  │  ├── comfyui_controlnet_aux                                         │   │
│  │  ├── Comfyui_turbodiffusion                                         │   │
│  │  ├── ComfyUI-XTTS                                                   │   │
│  │  └── (ComfyUI latest for Z-Image support)                           │   │
│  │                                                                     │   │
│  │  Integrations:                                                      │   │
│  │  └── civitai-downloader (anime/NSFW LoRAs)                         │   │
│  │                                                                     │   │
│  │  Scripts:                                                           │   │
│  │  ├── start.sh (entry point)                                         │   │
│  │  └── download_models.sh (on-demand downloads)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    ON-DEMAND MODELS (60-150GB)                      │   │
│  │                                                                     │   │
│  │  ENABLE_VIBEVOICE=true:                                             │   │
│  │  └── VibeVoice-Large (~18GB) OR VibeVoice-1.5B (~5.4GB)            │   │
│  │                                                                     │   │
│  │  ENABLE_ZIMAGE=true:                                                │   │
│  │  ├── qwen_3_4b.safetensors (~8GB)                                  │   │
│  │  ├── z_image_turbo_bf16.safetensors (~12GB)                        │   │
│  │  └── ae.safetensors (335MB)                                         │   │
│  │                                                                     │   │
│  │  ENABLE_STEADYDANCER=true:                                          │   │
│  │  └── Wan21_SteadyDancer_fp16.safetensors (~32GB)                   │   │
│  │                                                                     │   │
│  │  ENABLE_SCAIL=true:                                                 │   │
│  │  └── SCAIL-Preview (~28GB)                                          │   │
│  │                                                                     │   │
│  │  ENABLE_CONTROLNET=true:                                            │   │
│  │  └── control_v11*_fp16.safetensors (~3.6GB total)                  │   │
│  │                                                                     │   │
│  │  ENABLE_XTTS=true:                                                  │   │
│  │  └── XTTS v2 multilingual (~1.8GB)                                 │   │
│  │                                                                     │   │
│  │  ENABLE_VACE=true:                                                  │   │
│  │  └── WAN VACE 14B (~28GB) - video editing/inpaint/outpaint         │   │
│  │                                                                     │   │
│  │  ENABLE_FUN_INP=true:                                               │   │
│  │  └── WAN Fun InP 14B (~28GB) - start-end frame interpolation       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Storage Modes:                                                             │
│  • Ephemeral: 450GB container disk, models re-download each cold start     │
│  • Persistent: /workspace network volume, models cached between sessions   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Environment Variables

### Feature Toggles
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_VIBEVOICE` | bool | true | Install VibeVoice node + download model |
| `ENABLE_ZIMAGE` | bool | false | Download Z-Image Turbo components |
| `ENABLE_STEADYDANCER` | bool | false | Download SteadyDancer model |
| `ENABLE_SCAIL` | bool | false | Download SCAIL model |
| `ENABLE_CONTROLNET` | bool | true | Download ControlNet FP16 models |
| `ENABLE_XTTS` | bool | false | Download XTTS v2 model (~1.8GB) |
| `ENABLE_TURBODIFFUSION` | bool | false | Install TurboDiffusion for 100-200x speedup |
| `ENABLE_CIVITAI` | bool | false | Enable CivitAI downloader integration |
| `ENABLE_I2V` | bool | false | Download CLIP Vision for WAN I2V support |
| `ENABLE_VACE` | bool | false | Download WAN VACE (all-in-one video editing) |
| `ENABLE_FUN_INP` | bool | false | Download WAN Fun InP (start-end frame control) |

### Model Selection
| Variable | Type | Default | Options |
|----------|------|---------|---------|
| `VIBEVOICE_MODEL` | string | Large | `1.5B`, `Large`, `Large-Q8` |
| `CONTROLNET_MODELS` | string | canny,depth,openpose | Comma-separated list |
| `CIVITAI_API_KEY` | string | - | CivitAI API key for NSFW/gated models |
| `CIVITAI_LORAS` | string | - | Comma-separated CivitAI model version IDs to download |

### Behavior
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `UPDATE_NODES_ON_START` | bool | false | Git pull custom nodes on each start |
| `STORAGE_MODE` | string | auto | `auto`, `ephemeral`, `persistent` |
| `COMFYUI_PORT` | int | 8188 | ComfyUI web interface port |

### Inherited from Hearmeman (WAN 2.2 models)
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `WAN_720P` | bool | true | Download WAN 2.2 720p models (~25GB) |
| `WAN_480P` | bool | false | Download WAN 2.2 480p models (~12GB) |
| `VACE` | bool | false | Download VACE models |
| `PUBLIC_KEY` | string | - | SSH public key |
| `JUPYTER_PASSWORD` | string | - | JupyterLab password |

> **Note**: WAN 2.2 models are downloaded by the base Hearmeman start script. TurboDiffusion provides 100-200x speedup for these models when enabled.

---

## 4. Phase 1: Dockerfile

### Dockerfile

```dockerfile
# ============================================
# Hearmeman Extended Template
# ============================================
ARG BASE_IMAGE=runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04
FROM ${BASE_IMAGE}

# Build arguments
ARG COMFYUI_COMMIT=latest
ARG DEBIAN_FRONTEND=noninteractive

# Environment
ENV PYTHONUNBUFFERED=1
ENV SHELL=/bin/bash
ENV COMFYUI_PORT=8188

# ============================================
# Layer 1: System Dependencies
# ============================================
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

# Initialize git-lfs
RUN git lfs install

# ============================================
# Layer 2: ComfyUI Base (latest for Z-Image support)
# ============================================
WORKDIR /workspace
RUN git clone https://github.com/comfyanonymous/ComfyUI.git && \
    cd ComfyUI && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Layer 3: Custom Nodes (baked in)
# ============================================
WORKDIR /workspace/ComfyUI/custom_nodes

# ComfyUI-Manager
RUN git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Manager.git

# VibeVoice-ComfyUI
RUN git clone --depth 1 https://github.com/AIFSH/VibeVoice-ComfyUI.git && \
    cd VibeVoice-ComfyUI && \
    pip install --no-cache-dir TTS bitsandbytes>=0.48.1 || true

# ComfyUI-SCAIL-Pose
RUN git clone --depth 1 https://github.com/kijai/ComfyUI-SCAIL-Pose.git

# ControlNet Preprocessors
RUN git clone --depth 1 https://github.com/Fannovel16/comfyui_controlnet_aux.git && \
    cd comfyui_controlnet_aux && \
    pip install --no-cache-dir -r requirements.txt || true

# ComfyUI-XTTS (Coqui XTTS v2)
RUN git clone --depth 1 https://github.com/AIFSH/ComfyUI-XTTS.git && \
    cd ComfyUI-XTTS && \
    pip install --no-cache-dir TTS pydub || true

# TurboDiffusion (100-200x video speedup for WAN models)
RUN git clone --depth 1 https://github.com/anveshane/Comfyui_turbodiffusion.git && \
    cd Comfyui_turbodiffusion && \
    pip install --no-cache-dir -r requirements.txt || true

# CivitAI integration
RUN pip install --no-cache-dir civitai-downloader

# ============================================
# Layer 4: Additional Dependencies
# ============================================
WORKDIR /workspace
RUN pip install --no-cache-dir \
    huggingface_hub \
    accelerate \
    safetensors \
    sentencepiece \
    protobuf

# ============================================
# Layer 5: Scripts and Configuration
# ============================================
COPY start.sh /start.sh
COPY download_models.sh /download_models.sh
RUN chmod +x /start.sh /download_models.sh

# SSH configuration
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Create model directories
RUN mkdir -p /workspace/ComfyUI/models/{vibevoice,text_encoders,diffusion_models,vae,controlnet,loras}

# Expose ports
EXPOSE 22 8188 8888

# Working directory
WORKDIR /workspace/ComfyUI

# Entry point
ENTRYPOINT ["/start.sh"]
```

---

## 5. Phase 2: Start Script

### start.sh

```bash
#!/bin/bash
set -e

echo "============================================"
echo "=== Hearmeman Extended Template Startup ==="
echo "============================================"
echo "Timestamp: $(date)"
echo ""

# ============================================
# Storage Mode Detection
# ============================================
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
echo "[Storage] Mode: $STORAGE_MODE"

# ============================================
# SSH Setup
# ============================================
if [[ -n "$PUBLIC_KEY" ]]; then
    echo "[SSH] Configuring SSH access..."
    mkdir -p ~/.ssh && chmod 700 ~/.ssh
    echo "$PUBLIC_KEY" >> ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    service ssh start
    echo "[SSH] Ready on port 22"
fi

# ============================================
# JupyterLab Setup
# ============================================
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

# ============================================
# Update Custom Nodes (if enabled)
# ============================================
if [ "${UPDATE_NODES_ON_START:-false}" = "true" ]; then
    echo "[Nodes] Updating custom nodes..."
    for dir in /workspace/ComfyUI/custom_nodes/*/; do
        if [ -d "$dir/.git" ]; then
            echo "  Updating: $(basename $dir)"
            cd "$dir" && git pull --quiet || true
        fi
    done
fi

# ============================================
# Download Models
# ============================================
echo "[Models] Starting model downloads..."
/download_models.sh

# ============================================
# Start ComfyUI
# ============================================
echo "[ComfyUI] Starting on port ${COMFYUI_PORT:-8188}..."
cd /workspace/ComfyUI
exec python main.py \
    --listen 0.0.0.0 \
    --port ${COMFYUI_PORT:-8188} \
    --enable-cors-header \
    --preview-method auto
```

### download_models.sh

```bash
#!/bin/bash
# Model download script with resume support

# Helper function for downloads
download_model() {
    local URL="$1"
    local DEST="$2"
    local NAME=$(basename "$DEST")
    
    if [ -f "$DEST" ]; then
        echo "  [Skip] $NAME already exists"
        return 0
    fi
    
    echo "  [Download] $NAME"
    mkdir -p "$(dirname "$DEST")"
    wget -c -q --show-progress -O "$DEST" "$URL" || {
        echo "  [Error] Failed to download $NAME"
        rm -f "$DEST"
        return 1
    }
}

# HuggingFace download helper
hf_download() {
    local REPO="$1"
    local FILE="$2"
    local DEST="$3"
    download_model "https://huggingface.co/${REPO}/resolve/main/${FILE}" "$DEST"
}

MODELS_DIR="/workspace/ComfyUI/models"

# ============================================
# VibeVoice Models
# ============================================
if [ "${ENABLE_VIBEVOICE:-true}" = "true" ]; then
    echo "[VibeVoice] Downloading model: ${VIBEVOICE_MODEL:-Large}"
    
    case "${VIBEVOICE_MODEL:-Large}" in
        "1.5B")
            python -c "
from huggingface_hub import snapshot_download
snapshot_download('microsoft/VibeVoice-1.5B', 
    local_dir='$MODELS_DIR/vibevoice/VibeVoice-1.5B',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] Will download on first use"
            ;;
        "Large")
            python -c "
from huggingface_hub import snapshot_download
snapshot_download('AIFSH/VibeVoice-Large', 
    local_dir='$MODELS_DIR/vibevoice/VibeVoice-Large',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] Will download on first use"
            ;;
        "Large-Q8")
            python -c "
from huggingface_hub import snapshot_download
snapshot_download('FabioSarracino/VibeVoice-Large-Q8', 
    local_dir='$MODELS_DIR/vibevoice/VibeVoice-Large-Q8',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] Will download on first use"
            ;;
    esac
fi

# ============================================
# Z-Image Turbo
# ============================================
if [ "${ENABLE_ZIMAGE:-false}" = "true" ]; then
    echo "[Z-Image] Downloading components..."
    hf_download "Tongyi-MAI/Z-Image-Turbo" "qwen_3_4b.safetensors" "$MODELS_DIR/text_encoders/qwen_3_4b.safetensors"
    hf_download "Tongyi-MAI/Z-Image-Turbo" "z_image_turbo_bf16.safetensors" "$MODELS_DIR/diffusion_models/z_image_turbo_bf16.safetensors"
    hf_download "Tongyi-MAI/Z-Image-Turbo" "ae.safetensors" "$MODELS_DIR/vae/ae.safetensors"
fi

# ============================================
# SteadyDancer
# ============================================
if [ "${ENABLE_STEADYDANCER:-false}" = "true" ]; then
    echo "[SteadyDancer] Downloading model..."
    hf_download "MCG-NJU/SteadyDancer-14B" "Wan21_SteadyDancer_fp16.safetensors" "$MODELS_DIR/diffusion_models/Wan21_SteadyDancer_fp16.safetensors"
fi

# ============================================
# SCAIL
# ============================================
if [ "${ENABLE_SCAIL:-false}" = "true" ]; then
    echo "[SCAIL] Downloading model..."
    cd "$MODELS_DIR/diffusion_models"
    if [ ! -d "SCAIL-Preview" ]; then
        GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/zai-org/SCAIL-Preview
        cd SCAIL-Preview
        git lfs pull
    fi
fi

# ============================================
# ControlNet Models
# ============================================
if [ "${ENABLE_CONTROLNET:-true}" = "true" ]; then
    echo "[ControlNet] Downloading FP16 models..."
    
    CONTROLNET_LIST="${CONTROLNET_MODELS:-canny,depth,openpose}"
    IFS=',' read -ra MODELS <<< "$CONTROLNET_LIST"
    
    for model in "${MODELS[@]}"; do
        model=$(echo "$model" | xargs)  # trim whitespace
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
            "lineart")
                hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
                    "control_v11p_sd15_lineart_fp16.safetensors" \
                    "$MODELS_DIR/controlnet/control_v11p_sd15_lineart_fp16.safetensors"
                ;;
            "normalbae")
                hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
                    "control_v11p_sd15_normalbae_fp16.safetensors" \
                    "$MODELS_DIR/controlnet/control_v11p_sd15_normalbae_fp16.safetensors"
                ;;
        esac
    done
fi

# ============================================
# XTTS v2
# ============================================
if [ "${ENABLE_XTTS:-false}" = "true" ]; then
    echo "[XTTS] Downloading XTTS v2 model..."
    python -c "
from TTS.api import TTS
# This downloads the model on first init
tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=False)
print('XTTS v2 model downloaded successfully')
" 2>&1 || echo "  [Note] XTTS will download on first use"
fi

# ============================================
# CLIP Vision for I2V (Image-to-Video)
# ============================================
if [ "${ENABLE_I2V:-false}" = "true" ]; then
    echo "[I2V] Downloading CLIP Vision model..."
    mkdir -p "$MODELS_DIR/clip_vision"
    hf_download "Comfy-Org/sigclip_vision_384" \
        "sigclip_vision_patch14_384.safetensors" \
        "$MODELS_DIR/clip_vision/sigclip_vision_patch14_384.safetensors"
fi

# ============================================
# WAN VACE (Video All-in-One Creation and Editing)
# ============================================
if [ "${ENABLE_VACE:-false}" = "true" ]; then
    echo "[VACE] Downloading WAN VACE 14B model..."
    hf_download "Wan-AI/Wan2.1-VACE-14B" \
        "wan2.1_vace_14B_fp16.safetensors" \
        "$MODELS_DIR/diffusion_models/wan2.1_vace_14B_fp16.safetensors"
fi

# ============================================
# WAN Fun InP (First-Last Frame Interpolation)
# ============================================
if [ "${ENABLE_FUN_INP:-false}" = "true" ]; then
    echo "[Fun InP] Downloading WAN Fun InP 14B model..."
    hf_download "Wan-AI/Wan2.2-Fun-InP-14B" \
        "wan2.2_fun_inp_14B_fp16.safetensors" \
        "$MODELS_DIR/diffusion_models/wan2.2_fun_inp_14B_fp16.safetensors"
fi

# ============================================
# CivitAI LoRAs
# ============================================
if [ "${ENABLE_CIVITAI:-false}" = "true" ] && [ -n "$CIVITAI_LORAS" ]; then
    echo "[CivitAI] Downloading LoRAs..."

    # Store API key if provided
    if [ -n "$CIVITAI_API_KEY" ]; then
        echo "$CIVITAI_API_KEY" > /workspace/.civitai-token
        chmod 600 /workspace/.civitai-token
    fi

    IFS=',' read -ra LORA_IDS <<< "$CIVITAI_LORAS"
    for version_id in "${LORA_IDS[@]}"; do
        version_id=$(echo "$version_id" | xargs)  # trim whitespace
        echo "  [Download] CivitAI model version: $version_id"

        if [ -n "$CIVITAI_API_KEY" ]; then
            wget -c -q --show-progress \
                "https://civitai.com/api/download/models/${version_id}?token=${CIVITAI_API_KEY}" \
                --content-disposition \
                -P "$MODELS_DIR/loras/" || echo "  [Error] Failed: $version_id"
        else
            wget -c -q --show-progress \
                "https://civitai.com/api/download/models/${version_id}" \
                --content-disposition \
                -P "$MODELS_DIR/loras/" || echo "  [Error] Failed (may need API key): $version_id"
        fi
    done
fi

echo "[Models] Download complete"
```

---

## 6. Phase 3: GHCR Setup

### Repository Structure

```
hearmeman-extended/
├── .github/
│   └── workflows/
│       └── docker-build.yml
├── Dockerfile
├── start.sh
├── download_models.sh
├── requirements.txt
└── README.md
```

### GitHub Actions Workflow (.github/workflows/docker-build.yml)

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [main]
    paths:
      - 'Dockerfile'
      - 'start.sh'
      - 'download_models.sh'
      - 'requirements.txt'
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=raw,value=latest
            type=sha,prefix=

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          platforms: linux/amd64
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Manual Push Commands

```bash
# 1. Authenticate with GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# 2. Build image
docker build --platform linux/amd64 -t ghcr.io/USERNAME/hearmeman-extended:latest .

# 3. Push to GHCR
docker push ghcr.io/USERNAME/hearmeman-extended:latest

# 4. Verify
docker pull ghcr.io/USERNAME/hearmeman-extended:latest
```

---

## 7. Phase 4: Template Registration

### RunPod Template Configuration

```json
{
  "name": "Hearmeman Extended",
  "imageName": "ghcr.io/USERNAME/hearmeman-extended:latest",
  "category": "NVIDIA",
  "containerDiskInGb": 50,
  "volumeInGb": 100,
  "volumeMountPath": "/workspace",
  "ports": "8188/http,8888/http,22/tcp",
  "env": [
    {"key": "ENABLE_VIBEVOICE", "value": "true"},
    {"key": "ENABLE_ZIMAGE", "value": "false"},
    {"key": "ENABLE_STEADYDANCER", "value": "false"},
    {"key": "ENABLE_SCAIL", "value": "false"},
    {"key": "ENABLE_CONTROLNET", "value": "true"},
    {"key": "ENABLE_XTTS", "value": "false"},
    {"key": "ENABLE_TURBODIFFUSION", "value": "false"},
    {"key": "ENABLE_CIVITAI", "value": "false"},
    {"key": "CIVITAI_API_KEY", "value": ""},
    {"key": "CIVITAI_LORAS", "value": ""},
    {"key": "ENABLE_I2V", "value": "false"},
    {"key": "ENABLE_VACE", "value": "false"},
    {"key": "ENABLE_FUN_INP", "value": "false"},
    {"key": "VIBEVOICE_MODEL", "value": "Large"},
    {"key": "CONTROLNET_MODELS", "value": "canny,depth,openpose"},
    {"key": "UPDATE_NODES_ON_START", "value": "false"},
    {"key": "STORAGE_MODE", "value": "auto"},
    {"key": "WAN_720P", "value": "true"},
    {"key": "WAN_480P", "value": "false"},
    {"key": "VACE", "value": "false"}
  ],
  "isPublic": false,
  "readme": "## Hearmeman Extended\n\nExtends Hearmeman with VibeVoice TTS, SCAIL, SteadyDancer, Z-Image, and ControlNet.\n\n### Environment Variables\n- ENABLE_VIBEVOICE: Enable TTS voice cloning\n- ENABLE_ZIMAGE: Enable Z-Image Turbo\n- ENABLE_STEADYDANCER: Enable dance video\n- ENABLE_SCAIL: Enable facial expressions\n- ENABLE_CONTROLNET: Enable ControlNet\n\n### GPU Recommendations\n- 24GB VRAM: Basic features\n- 48GB VRAM: All features simultaneously"
}
```

### Template Creation (Console)

1. Go to RunPod Console → My Templates → New Template
2. Fill in:
   - **Template Name**: Hearmeman Extended
   - **Container Image**: `ghcr.io/USERNAME/hearmeman-extended:latest`
   - **Container Disk**: 50 GB
   - **Volume Disk**: 100 GB (or 0 for ephemeral)
   - **Volume Mount**: `/workspace`
   - **HTTP Ports**: `8188, 8888`
   - **TCP Ports**: `22`
3. Add environment variables from table above
4. Save template

---

## 8. Phase 5: Testing & Verification

### Local Docker Test

```bash
# Build locally
docker build -t hearmeman-extended:test .

# Run with GPU
docker run --gpus all \
  -p 8188:8188 \
  -e ENABLE_VIBEVOICE=true \
  -e ENABLE_CONTROLNET=true \
  -e PUBLIC_KEY="$(cat ~/.ssh/id_ed25519.pub)" \
  hearmeman-extended:test

# Verify
curl http://localhost:8188/system_stats
```

### RunPod Deployment Test

```bash
# 1. Deploy from template
# https://console.runpod.io/deploy?template=YOUR_TEMPLATE_ID

# 2. Wait for running status

# 3. SSH test
ssh root@IP -p PORT -i ~/.ssh/id_ed25519

# 4. Health check on pod
nvidia-smi
curl -s localhost:8188/system_stats | head -50
ls /workspace/ComfyUI/custom_nodes/
ls /workspace/ComfyUI/models/*/
```

### Verification Checklist

| # | Check | Command | Expected |
|---|-------|---------|----------|
| 1 | GPU available | `nvidia-smi` | 48GB VRAM displayed |
| 2 | ComfyUI running | `curl localhost:8188/system_stats` | JSON response |
| 3 | Manager installed | `ls custom_nodes/ComfyUI-Manager` | Directory exists |
| 4 | VibeVoice node | `ls custom_nodes/VibeVoice-ComfyUI` | Directory exists |
| 5 | SCAIL node | `ls custom_nodes/ComfyUI-SCAIL-Pose` | Directory exists |
| 6 | ControlNet aux | `ls custom_nodes/comfyui_controlnet_aux` | Directory exists |
| 6b | XTTS node | `ls custom_nodes/ComfyUI-XTTS` | Directory exists |
| 6c | TurboDiffusion | `ls custom_nodes/Comfyui_turbodiffusion` | Directory exists |
| 6d | CivitAI ready | `which civitai-downloader` | Path returned |
| 7 | Storage mode | `echo $STORAGE_MODE` | auto/ephemeral/persistent |
| 8 | VibeVoice model | `ls models/vibevoice/` | Model directory |
| 9 | ControlNet models | `ls models/controlnet/` | FP16 safetensors |
| 10 | SSH access | External SSH connection | Login successful |

### Health Check Script

```bash
#!/bin/bash
# health_check.sh

echo "=== Hearmeman Extended Health Check ==="
echo ""

# GPU
echo -n "GPU: "
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "NOT AVAILABLE"

# Disk
echo -n "Disk Free: "
df -h /workspace 2>/dev/null | tail -1 | awk '{print $4}' || echo "N/A"

# Storage Mode
echo "Storage Mode: ${STORAGE_MODE:-not set}"

# ComfyUI
echo -n "ComfyUI: "
curl -s localhost:8188/system_stats > /dev/null && echo "Running" || echo "NOT RUNNING"

# Custom Nodes
echo ""
echo "Custom Nodes:"
for dir in /workspace/ComfyUI/custom_nodes/*/; do
    echo "  - $(basename $dir)"
done

# Models
echo ""
echo "Models:"
for type in vibevoice text_encoders diffusion_models vae controlnet; do
    count=$(ls -1 /workspace/ComfyUI/models/$type/ 2>/dev/null | wc -l)
    echo "  - $type: $count files"
done

echo ""
echo "=== Check Complete ==="
```

---

## 9. Model Size Reference

| Model | Size | VRAM |
|-------|------|------|
| VibeVoice-1.5B | 5.4GB | 8GB |
| VibeVoice-Large | 18GB | 20GB |
| VibeVoice-Large-Q8 | 6GB | 10GB |
| Z-Image Turbo (total) | 21GB | 16GB |
| SteadyDancer FP16 | 32.8GB | 28GB |
| SteadyDancer Q8 GGUF | 17.4GB | 20GB |
| SCAIL-Preview | 28GB | 24GB |
| ControlNet FP16 (each) | 723MB | 2GB |
| XTTS v2 | 1.8GB | 4GB |
| TurboDiffusion deps | ~500MB | - |
| LoRAs (per CivitAI) | varies | ~1GB each |
| CLIP Vision (I2V) | ~1.5GB | 2GB |
| WAN VACE 14B | ~28GB | 24GB |
| WAN Fun InP 14B | ~28GB | 24GB |

### Recommended Configurations

| Configuration | Total Download | GPU Recommendation |
|---------------|----------------|-------------------|
| VibeVoice only | ~18GB | 24GB (A5000) |
| VibeVoice + ControlNet | ~22GB | 24GB (A5000) |
| VibeVoice + Z-Image | ~39GB | 24GB (A5000) |
| Full suite (all) | ~100GB | 48GB (L40S/A6000) |

---

## 10. Quick Start

### Deploy via Console

1. Go to: `https://console.runpod.io/deploy?template=YOUR_TEMPLATE_ID`
2. Select GPU: L40S or A6000 (48GB VRAM)
3. Set environment variables as needed
4. Deploy

### SSH Connection

```bash
# Update SSH config
cat >> ~/.ssh/config << EOF
Host runpod-extended
    HostName IP_ADDRESS
    Port SSH_PORT
    User root
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
EOF

# Connect
ssh runpod-extended

# Create tunnel
ssh -L 8188:localhost:8188 runpod-extended
```

### Browser Access

- ComfyUI: `http://localhost:8188` (via tunnel) or `https://POD_ID-8188.proxy.runpod.net`
- JupyterLab: `https://POD_ID-8888.proxy.runpod.net`

---

## 11. Appendix: Model Download URLs

### VibeVoice
```
https://huggingface.co/microsoft/VibeVoice-1.5B
https://huggingface.co/AIFSH/VibeVoice-Large
https://huggingface.co/FabioSarracino/VibeVoice-Large-Q8
```

### Z-Image Turbo
```
https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/resolve/main/qwen_3_4b.safetensors
https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/resolve/main/z_image_turbo_bf16.safetensors
https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/resolve/main/ae.safetensors
```

### SteadyDancer
```
https://huggingface.co/MCG-NJU/SteadyDancer-14B/resolve/main/Wan21_SteadyDancer_fp16.safetensors
https://huggingface.co/MCG-NJU/SteadyDancer-GGUF/resolve/main/SteadyDancer-14B-Q8_0.gguf
```

### SCAIL
```
https://huggingface.co/zai-org/SCAIL-Preview
https://huggingface.co/vantagewithai/SCAIL-Preview-GGUF
```

### ControlNet FP16
```
https://huggingface.co/comfyanonymous/ControlNet-v1-1_fp16_safetensors/resolve/main/control_v11p_sd15_canny_fp16.safetensors
https://huggingface.co/comfyanonymous/ControlNet-v1-1_fp16_safetensors/resolve/main/control_v11f1p_sd15_depth_fp16.safetensors
https://huggingface.co/comfyanonymous/ControlNet-v1-1_fp16_safetensors/resolve/main/control_v11p_sd15_openpose_fp16.safetensors
https://huggingface.co/comfyanonymous/ControlNet-v1-1_fp16_safetensors/resolve/main/control_v11p_sd15_lineart_fp16.safetensors
https://huggingface.co/comfyanonymous/ControlNet-v1-1_fp16_safetensors/resolve/main/control_v11p_sd15_normalbae_fp16.safetensors
```

### XTTS v2
```
# Downloaded via TTS library from Coqui
# Model: tts_models/multilingual/multi-dataset/xtts_v2
# Languages: en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko
# GitHub: https://github.com/AIFSH/ComfyUI-XTTS
```

---

*Document generated: 2025-12-24*
*Project: José Obscura - La Maquila Erótica Documentary*
