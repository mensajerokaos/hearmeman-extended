# RunPod AI Generation System - Comprehensive Documentation

**Author**: AI Research Assistant
**Date**: 2026-01-17
**Task**: Gather comprehensive data about RunPod AI generation system

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Architecture](#core-architecture)
3. [Docker Configuration](#docker-configuration)
4. [AI Models & Capabilities](#ai-models--capabilities)
5. [TTS Systems](#tts-systems)
6. [Video Generation](#video-generation)
7. [Cloudflare R2 Integration](#cloudflare-r2-integration)
8. [Deployment Configuration](#deployment-configuration)
9. [Research Findings](#research-findings)
10. [Environment Variables](#environment-variables)
11. [Best Practices](#best-practices)

---

## 1. System Overview

This is a custom RunPod template project for deploying AI models with on-demand model downloads. The system uses a production-ready Docker image (~12GB) with ComfyUI as the core orchestration layer, enabling flexible deployment of various AI models including text-to-speech, video generation, and image generation.

**Key Characteristics:**
- Container-based deployment on RunPod GPU infrastructure
- On-demand model downloads (60-150GB models downloaded at runtime)
- Environment-driven feature configuration
- Cloudflare R2 integration for output persistence
- Ephemeral storage with automatic upload to R2

**Project Location**: `/home/oz/projects/2025/oz/12/runpod/`

---

## 2. Core Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RUNPOD GPU POD (Ephemeral)                          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      DOCKER CONTAINER (~12GB)                       │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                    ComfyUI (Python Backend)                 │   │   │
│  │  │                                                              │   │   │
│  │  │  Custom Nodes (Baked in):                                   │   │   │
│  │  │  ├── VibeVoice-ComfyUI (TTS)                               │   │   │
│  │  │  ├── ComfyUI-Chatterbox (TTS)                              │   │   │
│  │  │  ├── ComfyUI-WanVideoWrapper (WAN 2.1/2.2)                 │   │   │
│  │  │  ├── Comfyui_turbodiffusion (Speedup)                      │   │   │
│  │  │  ├── comfyui_controlnet_aux                                │   │   │
│  │  │  ├── ComfyUI-Manager                                       │   │   │
│  │  │  └── [Custom nodes for Genfocus, MVInverse]                │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                      │   │
│  │  Scripts:                                                            │   │
│  │  ├── start.sh (Entry point with GPU detection)                     │   │
│  │  ├── download_models.sh (On-demand downloads)                      │   │
│  │  ├── r2_sync.sh (Output monitoring daemon)                         │   │
│  │  └── upload_to_r2.py (S3-compatible upload)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Storage:                                                                  │
│  - Container Disk: 450GB (ephemeral, lost on restart)                     │
│  - Models: Downloaded to /workspace/ComfyUI/models                         │
│  - Outputs: /workspace/ComfyUI/output (watched by r2_sync.sh)              │
│                                                                             │
│  Network:                                                                   │
│  - Ports: 8188 (ComfyUI), 8888 (JupyterLab), 22 (SSH)                     │
│  - GPU: 1x NVIDIA GPU (RTX 4090/A6000/L40S)                               │
│  - R2 Sync: Background daemon uploads new outputs                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ R2 Sync Daemon (inotifywait)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CLOUDFLARE R2 OBJECT STORAGE                           │
│                                                                             │
│  Endpoint: https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com
│  Bucket: runpod                                                              │
│  Structure:                                                                  │
│  ├── outputs/YYYY-MM-DD/*.png                                              │
│  ├── outputs/YYYY-MM-DD/*.mp4                                              │
│  ├── outputs/YYYY-MM-DD/*.wav                                              │
│  └── logs/r2_sync.log                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Base Components

| Component | Version | Purpose |
|-----------|---------|---------|
| **Base Image** | `runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04` | GPU PyTorch environment |
| **ComfyUI** | Latest (2025) | Node-based workflow GUI/backend |
| **Python** | 3.11 | Runtime environment |
| **CUDA** | 12.8.1 | GPU acceleration |
| **cuDNN** | 9 | Deep learning library |

---

## 3. Docker Configuration

### Dockerfile Structure

**File**: `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile`

The Dockerfile uses a multi-layer architecture for efficient builds:

```dockerfile
# Layer 1: Base System
# =====================
FROM runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04

# Layer 2: System Dependencies
RUN apt-get install -y \
    git, git-lfs, wget, curl, vim, ffmpeg, libsm6, libxext6, \
    libgl1-mesa-glx, openssh-server, aria2, inotify-tools

# Layer 3: ComfyUI Core
RUN git clone https://github.com/comfyanonymous/ComfyUI.git && \
    pip install -r requirements.txt

# Layer 4: Custom Nodes (13 nodes baked in)
WORKDIR /workspace/ComfyUI/custom_nodes
RUN git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Manager.git
RUN git clone --depth 1 https://github.com/Enemyx-net/VibeVoice-ComfyUI.git
RUN git clone --depth 1 https://github.com/thefader/ComfyUI-Chatterbox.git
RUN git clone --depth 1 https://github.com/kijai/ComfyUI-SCAIL-Pose.git
RUN git clone --depth 1 https://github.com/Fannovel16/comfyui_controlnet_aux.git
RUN git clone --depth 1 https://github.com/anveshane/Comfyui_turbodiffusion.git
RUN git clone --depth 1 https://github.com/kijai/ComfyUI-WanVideoWrapper.git
RUN git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git

# Layer 5: Python Dependencies
RUN pip install \
    huggingface_hub, accelerate, safetensors, boto3, sentencepiece, \
    protobuf, cupy-cuda12x, imageio[ffmpeg], einops, modelscope, \
    ftfy, lpips, lightning, pandas, matplotlib, wandb, ffmpeg-python, \
    audiotsm, loguru, diffusers>=0.21.0, peft>=0.4.0, \
    opencv-python>=4.5.0, timm, pynvlib

# Layer 6: Configuration
COPY start.sh /start.sh
COPY download_models.sh /download_models.sh
COPY r2_sync.sh /r2_sync.sh
COPY upload_to_r2.py /upload_to_r2.py
RUN chmod +x /start.sh /download_models.sh /r2_sync.sh

# Layer 7: Model Directories
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision,genfocus,qwen,mvinverse,flashportrait,storymem,infcam}

# Port Exposure
EXPOSE 22 8188 8888

# Entrypoint
ENTRYPOINT ["/start.sh"]
```

### Docker Compose Configuration

**File**: `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml`

```yaml
version: '3.8'

services:
  # Main ComfyUI Service
  hearmeman-extended:
    build:
      context: .
      dockerfile: Dockerfile
    image: hearmeman-extended:local
    container_name: hearmeman-extended
    runtime: nvidia
    ports:
      - "8188:8188"   # ComfyUI web interface
      - "8888:8888"   # JupyterLab
      - "2222:22"     # SSH
    environment:
      # Core Configuration
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

      # Tier 1 Models (Consumer GPU - 8-24GB VRAM)
      - ENABLE_GENFOCUS=true
      - ENABLE_QWEN_EDIT=true
      - QWEN_EDIT_MODEL=Q4_K_M
      - ENABLE_MVINVERSE=true

      # Tier 2 Models (Prosumer GPU - 24GB+)
      - ENABLE_FLASHPORTRAIT=false
      - ENABLE_STORYMEM=false

      # Tier 3 Models (Datacenter - 48-80GB)
      - ENABLE_INFCAM=false
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

volumes:
  models:
  output:
```

---

## 4. AI Models & Capabilities

### Model Architecture Tiers

The system organizes AI models into three tiers based on VRAM requirements:

#### Tier 1: Consumer GPU (8-24GB VRAM)

| Model | Size | VRAM | Purpose |
|-------|------|------|---------|
| **VibeVoice-1.5B** | 5.4GB | 8GB | Text-to-speech, multi-speaker |
| **VibeVoice-Large** | 18GB | 20GB | High-quality TTS |
| **Genfocus** | ~12GB | 12GB | Depth-of-field refocusing |
| **MVInverse** | ~8GB | 8GB | Multi-view inverse rendering |
| **Qwen-Image-Edit-2511 (Q4_K_M)** | ~13GB | 13GB | Instruction-based image editing |

#### Tier 2: Prosumer GPU (24GB+ with CPU Offload)

| Model | Size | VRAM | Purpose |
|-------|------|------|---------|
| **FlashPortrait** | ~60GB | 30GB (with offload) | Portrait animation |
| **StoryMem** | ~20GB | 20-24GB | Multi-shot video storytelling |

#### Tier 3: Datacenter GPU (48-80GB VRAM)

| Model | Size | VRAM | Purpose |
|-------|------|------|---------|
| **InfCam** | ~50GB+ | 50GB+ | Camera-controlled video generation |

### Model Storage Requirements

| Component | Size | Notes |
|-----------|------|-------|
| **Docker Image** | ~12GB | Base with custom nodes |
| **WAN 2.2 720p** | ~25GB | Default video generation |
| **WAN 2.2 480p** | ~12GB | Optional video generation |
| **VibeVoice-Large** | ~18GB | TTS voice cloning |
| **XTTS v2** | ~1.8GB | Multilingual TTS |
| **Z-Image Turbo** | ~21GB | Fast image generation |
| **SteadyDancer** | ~33GB | Dance video generation |
| **SCAIL** | ~28GB | Facial mocap |
| **ControlNet (5 models)** | ~3.6GB | Preprocessors |
| **VACE 14B** | ~28GB | Video editing |
| **Fun InP 14B** | ~28GB | Frame interpolation |
| **Realism Illustrious** | ~6.5GB | Photorealistic images |
| **Total (ALL)** | **~230GB** | |
| **Typical Config** | **~80-120GB** | |

---

## 5. TTS Systems

### 5.1 VibeVoice-ComfyUI (Primary TTS)

**Repository**: https://github.com/Enemyx-net/VibeVoice-ComfyUI
**Latest Release**: v1.8.1+ (October 2025)
**Model Source**: HuggingFace aoi-ot/VibeVoice-Large (~18GB)

**Key Features:**
- Multi-speaker TTS (up to 4 speakers)
- Voice cloning from audio reference (6-second sample)
- LoRA support for voice customization
- Speed control
- Expressive, long-form conversational audio

**Model Variants:**
| Model | Size | VRAM | Use Case |
|-------|------|------|----------|
| VibeVoice-1.5B | 5.4GB | 8GB | Resource-constrained environments |
| VibeVoice-Large | 18GB | 20GB | High-quality production TTS |
| VibeVoice-Large-Q8 | 6GB | 10GB | Optimized quality/size balance |

**Critical Dependencies:**
```
bitsandbytes>=0.48.1  # Critical for Q8 model compatibility
transformers>=4.51.3
accelerate
peft
librosa
soundfile
```

**Installation:**
```bash
git clone --depth 1 https://github.com/Enemyx-net/VibeVoice-ComfyUI.git
cd VibeVoice-ComfyUI
pip install -r requirements.txt
```

### 5.2 XTTS v2 Standalone Server

**Repository**: https://github.com/daswer123/xtts-api-server
**Docker Image**: `daswer123/xtts-api-server:latest`
**Model**: Coqui XTTS v2 (~1.8GB)
**VRAM**: 4-8GB

**Why Separate Container:**
- `xtts-api-server` requires `transformers==4.36.2`
- ComfyUI/VibeVoice requires `transformers>=4.51.3`
- Version conflict requires separate containers

**Supported Languages (17 total):**
- en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko, id

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tts_to_audio/` | POST | Returns audio bytes directly |
| `/tts_to_file` | POST | Saves to server file path |
| `/tts_stream` | POST | Streams audio chunks (~200ms latency) |
| `/speakers_list` | GET | List available speakers |
| `/languages` | GET | List supported languages |

**API Example:**
```bash
# Generate audio file
curl -X POST "http://localhost:8020/tts_to_audio/" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "speaker_wav": "female", "language": "en"}' \
  -o output.wav

# Voice cloning from reference
curl -X POST "http://localhost:8020/tts_to_audio/" \
  -H "Content-Type: application/json" \
  -d '{"text": "Clone my voice", "speaker_wav": "/path/to/reference.wav", "language": "en"}' \
  -o cloned.wav
```

**VO Automation Script**: `docker/scripts/xtts-vo-gen.py`
```bash
# Single line generation
python xtts-vo-gen.py "Hello world" -o hello.wav

# Batch from script
python xtts-vo-gen.py -f script.txt -d ./vo-output --speaker male

# List options
python xtts-vo-gen.py --list-speakers
python xtts-vo-gen.py --list-languages
```

### 5.3 Chatterbox TTS (Resemble AI)

**Container**: `chatterbox-tts-api:local`
**API**: http://localhost:8000/docs
**VRAM**: 2-4GB
**ComfyUI Node**: `ComfyUI-Chatterbox` (thefader/ComfyUI-Chatterbox)

**Features:**
- Zero-shot voice cloning
- Emotion control
- OpenAI-compatible API

**API Example:**
```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model": "chatterbox", "input": "Hello world", "voice": "default"}' \
  -o speech.wav
```

---

## 6. Video Generation

### 6.1 WAN 2.1/2.2 Video Generation

**Repository**: https://github.com/kijai/ComfyUI-WanVideoWrapper
**Organization**: Wan-AI
**Models**: Available on HuggingFace

#### Model Variants

| Model | Resolution | Parameters | VRAM | Size |
|-------|------------|-----------|------|------|
| Wan2.1-T2V-14B-720P | 720p | 14B | 24GB | ~25GB |
| Wan2.1-T2V-1.3B-480P | 480p | 1.3B | 16GB | ~12GB |
| Wan2.1-I2V-14B-720P | 720p (I2V) | 14B | 24GB | ~25GB |
| Wan2.2-I2V-High-Noise | 720p | 14B | 24GB | ~14GB |
| Wan2.2-I2V-Low-Noise | 720p | 14B | 24GB | ~14GB |

#### Key Features (2025)

**Text-to-Video (T2V):**
- 720p and 480p resolution options
- 14B parameter diffusion model
- UMT5-XXL text encoder (9.5GB)
- CLIP Vision for image understanding

**Image-to-Video (I2V):**
- Transform static images to video
- CLIP Vision model required (1.4GB)
- Compatible with TurboDiffusion for 100-200x speedup

**Video Editing (VACE):**
- In-painting and out-painting
- Video composition
- All-in-one video editing capabilities

**Frame Interpolation (Fun InP):**
- First-last frame control
- Smooth interpolation between frames
- Enhanced video smoothness

### 6.2 TurboDiffusion

**Repository**: https://github.com/anveshane/Comfyui_turbodiffusion
**Speed Improvement**: 100-200x faster video generation

**Purpose:**
- Accelerates WAN 2.1/2.2 video generation
- Uses distilled model variants
- Reduces generation time from minutes to seconds

**Requirements:**
- WAN 2.2 distilled models (high/low noise experts)
- ~28GB total for distilled models

### 6.3 Additional Video Models

| Model | Size | VRAM | Purpose |
|-------|------|------|---------|
| **SteadyDancer** | ~33GB | 28GB | Dance/motion video generation |
| **SCAIL-Preview** | ~28GB | 24GB | Facial expression animation |
| **ControlNet (5 models)** | ~3.6GB | 2GB each | Preprocessing (canny, depth, openpose, lineart, normal) |

---

## 7. Cloudflare R2 Integration

### Overview

Cloudflare R2 provides S3-compatible object storage with **zero egress fees**, making it ideal for storing AI-generated outputs (images, videos, audio) from RunPod pods.

**Key Benefits:**
- S3-compatible API (works with AWS SDK)
- No egress bandwidth charges
- Automatic upload via daemon
- Persistent storage across pod restarts

### Configuration

**R2 Endpoint Structure:**
```
https://<account_id>.eu.r2.cloudflarestorage.com
```

**For this project:**
```
R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com
R2_BUCKET=runpod
```

### Upload Script (upload_to_r2.py)

**Location**: `/home/oz/projects/2025/oz/12/runpod/docker/upload_to_r2.py`

```python
#!/usr/bin/env python3
"""
Upload generated files to Cloudflare R2
S3-compatible API with boto3
"""
import boto3
import os
import sys
from datetime import datetime

def upload_to_r2(filepath):
    """Upload file to R2 with timestamped path"""
    # Configure S3 client
    s3_client = boto3.client(
        's3',
        endpoint_url=os.environ['R2_ENDPOINT'],
        aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
        region_name='auto'
    )

    # Generate R2 path with date
    date_str = datetime.now().strftime('%Y-%m-%d')
    filename = os.path.basename(filepath)
    r2_key = f"outputs/{date_str}/{filename}"

    # Upload
    bucket = os.environ['R2_BUCKET']
    s3_client.upload_file(filepath, bucket, r2_key)

    print(f"Uploaded: {r2_key}")
    return f"https://{bucket}.{os.environ['R2_ENDPOINT'].split('://')[1]}/{r2_key}"
```

### Sync Daemon (r2_sync.sh)

**Location**: `/home/oz/projects/2025/oz/12/runpod/docker/r2_sync.sh`

**Mechanism:**
1. Uses `inotifywait` to monitor `/workspace/ComfyUI/output`
2. Watches for file close_write events
3. Uploads new PNG, JPG, MP4, WAV, and other files
4. Runs as background daemon

**Key Code:**
```bash
#!/bin/bash
OUTPUT_DIR="${COMFYUI_OUTPUT_DIR:-/workspace/ComfyUI/output}"
WATCH_PATTERNS="\.png$|\.jpg$|\.jpeg$|\.webp$|\.mp4$|\.webm$|\.gif$|\.wav$|\.mp3$|\.flac$"

# Watch for new files
inotifywait -m -r -e close_write --format '%w%f' "$OUTPUT_DIR" | while read filepath; do
    if echo "$filepath" | grep -qE "$WATCH_PATTERNS"; then
        sleep 1  # Ensure file is fully written
        python3 /upload_to_r2.py "$filepath" &
    fi
done
```

**Configuration:**
```bash
# Environment Variables
ENABLE_R2_SYNC=true
R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com
R2_BUCKET=runpod
R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}
R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}
```

### Best Practices for R2 Sync

1. **Use RunPod Secrets**:
   - Never expose credentials in plain text
   - Use `RUNPOD_SECRET_r2_access_key` and `RUNPOD_SECRET_r2_secret_key`
   - Create secrets in RunPod Console → Settings → Secrets

2. **File Watching Strategy**:
   - Monitor `close_write` event (file completion)
   - Add 1-second sleep before upload (ensures file is flushed)
   - Run uploads in background (prevents blocking)

3. **Storage Organization**:
   ```
   s3://runpod/
   ├── outputs/
   │   ├── 2026-01-17/
   │   │   ├── workflow_001.png
   │   │   ├── video_002.mp4
   │   │   └── audio_003.wav
   │   └── 2026-01-18/
   │       └── ...
   └── logs/
       └── r2_sync.log
   ```

4. **Cost Optimization**:
   - R2 has no egress fees (unlike AWS S3)
   - Storage pricing: ~$0.015/GB/month
   - Ideal for high-volume AI output storage

---

## 8. Deployment Configuration

### RunPod Pod Creation Command

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
  --env "VIBEVOICE_MODEL=Large" \
  --env "ENABLE_CONTROLNET=true" \
  --env "ENABLE_ILLUSTRIOUS=false" \
  --env "ENABLE_ZIMAGE=false" \
  --env "CIVITAI_API_KEY=<key>" \
  --env "R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}" \
  --env "R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}" \
  --env "R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com" \
  --env "R2_BUCKET=runpod" \
  --env "ENABLE_R2_SYNC=true"
```

### Critical Deployment Learnings

| Requirement | Details |
|-------------|---------|
| **Web Terminal** | MUST enable `--ports "8188/http"` for web access |
| **Secure Cloud** | Use `--secureCloud` for dedicated 25Gbps bandwidth |
| **Datacenter Speed** | US: ~1 sec startup, EU: 4+ min startup - prefer US |
| **Model Downloads** | Secure Cloud: 51 MB/s, Community Cloud: variable |
| **CivitAI Fallback** | Curl fallback handles 307 redirects automatically |
| **Model Filenames** | CivitAI downloads as `model_<id>.safetensors` |

### Datacenter Speed Comparison

| Region | Startup Time | Network Speed | Recommendation |
|--------|--------------|---------------|----------------|
| US (Secure Cloud) | ~37 sec | 51 MB/s | **Recommended** |
| US (Community) | ~1 sec | Variable | Good for testing |
| EU (CZ) | 4+ min | Unknown | Avoid for speed-critical |
| UAE | 2+ min | Slow | Avoid |

### Tested Configurations

| Config | GPU | Cost | Result |
|--------|-----|------|--------|
| Illustrious (US Secure) | RTX 4090 | $0.59/hr | Working |
| Container startup | - | - | ~37 sec |
| Model download (6.5GB) | - | - | ~2 min |
| Image generation | - | - | ~5 sec |
| R2 sync | - | - | Automatic |

---

## 9. Research Findings

### 9.1 ComfyUI Latest Version (2025)

**Current Version**: v0.3.76 (December 2, 2025)
**Official Site**: https://www.comfy.org/

**Key 2025 Features:**

1. **Subgraph Feature** (August 2025)
   - Package complex node combinations into reusable subgraph nodes
   - Improved workflow organization
   - Enhanced collaboration capabilities

2. **New ComfyUI-Manager** (December 2025)
   - Refreshed user interface
   - Better node discovery and management
   - Enhanced installation workflow

3. **ComfyUI Studio** (December 2025)
   - 200+ ready-to-use workflows
   - AI-powered workflow templates
   - Integrated model manager

4. **New Interface Design**
   - Significantly improved UX
   - Smart templates
   - Better mobile support

**Repository**: https://github.com/Comfy-Org/ComfyUI

### 9.2 VibeVoice-ComfyUI Latest Version

**Repository**: https://github.com/Enemyx-net/VibeVoice-ComfyUI
**Latest Release**: October 2025
**Status**: Actively maintained

**Key Findings:**
- Microsoft deleted official VibeVoice repository in September 2025
- Enemyx-net fork is the primary maintained version
- Wildminder also maintains an alternative fork
- Models still available on HuggingFace (aoi-ot/VibeVoice-Large)

**Critical Issue (September 2025)**:
- Original Microsoft repository suddenly deleted
- Community forks continue maintenance
- Model weights still accessible via HuggingFace

### 9.3 WAN 2.2 Video Generation Models

**Organization**: Wan-AI
**Repository**: https://github.com/kijai/ComfyUI-WanVideoWrapper
**HuggingFace**: https://huggingface.co/Wan-AI

**Model Family (2025)**:

| Model | Type | Release | Features |
|-------|------|---------|----------|
| Wan2.1-T2V-14B | Text-to-Video | Feb 2025 | 720p, 14B parameters |
| Wan2.1-I2V-14B | Image-to-Video | Feb 2025 | Image-to-video conversion |
| Wan2.2-TI2V-5B | Text-to-Video | Aug 2025 | 5B parameters, efficient |
| Wan2.1-VACE-14B | Video Editing | 2025 | In/out painting, editing |
| Wan2.2-Fun-InP-14B | Interpolation | 2025 | Frame interpolation |

**Consumer GPU Support**:
- Can run on 16GB VRAM with quantized models
- 480p model (1.3B) fits in 16GB
- 720p model (14B) requires 24GB+

**Key Capabilities**:
- Text-to-video generation
- Image-to-video transformation
- Video editing and in-painting
- Frame interpolation
- Multi-modal understanding

### 9.4 XTTS v2 API Features

**Repository**: https://github.com/daswer123/xtts-api-server
**Documentation**: https://github.com/daswer123/xtts-api-server/wiki

**API Capabilities (2025)**:

1. **Core TTS Features**:
   - 17 language support
   - Voice cloning from 6-second sample
   - Streaming with <200ms latency
   - Real-time audio generation

2. **REST API Endpoints**:
   ```
   POST /tts_to_audio/     - Direct audio bytes
   POST /tts_to_file       - Save to file path
   POST /tts_stream        - Streaming chunks
   GET /speakers_list      - Available voices
   GET /languages          - Supported languages
   ```

3. **Integration Options**:
   - FastAPI server
   - Docker container
   - MaryTTS compatibility mode
   - OpenAI-compatible speech API

4. **Language Support** (17 languages):
   - European: en, es, fr, de, it, pt, pl, tr, ru, nl, cs
   - Asian: zh-cn, ja, hu, ko, id
   - Middle Eastern: ar

### 9.5 Cloudflare R2 Best Practices

**Documentation**: https://developers.cloudflare.com/r2/

**Key Best Practices (2025)**:

1. **S3 API Compatibility**:
   - R2 implements S3 API for easy migration
   - Use AWS SDK for Python (boto3)
   - Configure endpoint_url to R2 endpoint

2. **Authentication**:
   ```python
   s3_client = boto3.client(
       's3',
       endpoint_url='https://<account>.r2.cloudflarestorage.com',
       aws_access_key_id='ACCESS_KEY',
       aws_secret_access_key='SECRET_KEY',
       region_name='auto'
   )
   ```

3. **Zero Egress Fees**:
   - No charges for data retrieval
   - Ideal for high-volume AI outputs
   - Reduces storage costs significantly

4. **Automation Patterns**:
   - inotifywait for file watching (Linux)
   - Background daemon for continuous sync
   - Retry logic with exponential backoff
   - Logging for debugging

5. **Performance Optimization**:
   - Batch uploads when possible
   - Use appropriate file sizes
   - Monitor with Cloudflare dashboard
   - Set up lifecycle rules for cost control

6. **Security**:
   - Use R2 API tokens (not global API keys)
   - Implement least-privilege access
   - Enable audit logging
   - Use bucket-level policies

---

## 10. Environment Variables

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
| `ENABLE_ILLUSTRIOUS` | bool | false | Download Realism Illustrious checkpoint |
| `ENABLE_WAN22_DISTILL` | bool | false | Download WAN 2.2 distilled models |

### Model Selection

| Variable | Type | Default | Options |
|----------|------|---------|---------|
| `VIBEVOICE_MODEL` | string | Large | `1.5B`, `Large`, `Large-Q8` |
| `QWEN_EDIT_MODEL` | string | Q4_K_M | `Q4_K_M`, `Q5_K_M`, `Q6_K`, `Q8_0`, `Q2_K`, `Q3_K_M`, `full` |
| `CONTROLNET_MODELS` | string | canny,depth,openpose | Comma-separated list |
| `CIVITAI_API_KEY` | string | - | CivitAI API key for NSFW/gated models |
| `CIVITAI_LORAS` | string | - | Comma-separated CivitAI model version IDs |

### Behavior Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `UPDATE_NODES_ON_START` | bool | false | Git pull custom nodes on each start |
| `STORAGE_MODE` | string | auto | `auto`, `ephemeral`, `persistent` |
| `COMFYUI_PORT` | int | 8188 | ComfyUI web interface port |
| `GPU_TIER` | string | auto | `consumer`, `prosumer`, `datacenter` |
| `GPU_MEMORY_MODE` | string | auto | `auto`, `full`, `sequential_cpu_offload`, `model_cpu_offload` |
| `COMFYUI_ARGS` | string | - | Additional CLI args for ComfyUI |

### R2 Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_R2_SYNC` | bool | false | Enable R2 output sync daemon |
| `R2_ENDPOINT` | string | - | R2 endpoint URL |
| `R2_BUCKET` | string | runpod | Target bucket name |
| `R2_ACCESS_KEY_ID` | string | - | R2 access key (use secrets) |
| `R2_SECRET_ACCESS_KEY` | string | - | R2 secret key (use secrets) |

### WAN Model Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `WAN_720P` | bool | true | Download WAN 2.1 720p models (~25GB) |
| `WAN_480P` | bool | false | Download WAN 2.2 480p models (~12GB) |

---

## 11. Best Practices

### 11.1 Production Deployment Checklist

- [ ] Use `--secureCloud` for reliable bandwidth
- [ ] Prefer US datacenters for faster startup
- [ ] Use RunPod Secrets for R2 credentials
- [ ] Enable R2 sync for output persistence
- [ ] Test all models in local Docker first
- [ ] Verify all node values match ComfyUI version
- [ ] Check model paths match download scripts

### 11.2 Model Selection by VRAM

| GPU VRAM | Recommended Configuration |
|----------|--------------------------|
| 8GB | VibeVoice 1.5B, MVInverse |
| 12GB | VibeVoice 1.5B, Genfocus, Qwen-Edit (Q4_K_M) |
| 16GB | VibeVoice-Large, WAN 480p, XTTS v2 |
| 24GB | All Tier 1 + WAN 720p + ControlNet |
| 48GB+ | Full suite (all models enabled) |

### 11.3 Storage Management

**Ephemeral Pods** (no volume):
- Models re-downloaded on each cold start
- Use R2 for output persistence
- Expect 2-5 minute startup for full model suite

**Persistent Pods** (with volume):
- Models cached between sessions
- Faster subsequent starts
- Data survives pod restarts

### 11.4 Cost Optimization

1. **Model Selection**: Enable only needed models
2. **Datacenter**: Use US Secure Cloud (faster = cheaper)
3. **R2 Storage**: No egress fees ideal for AI outputs
4. **Spot Instances**: Use for non-critical workloads
5. **Idle Timeout**: Set reasonable pod timeout

### 11.5 Troubleshooting Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| CUDA out of memory | Model too large for VRAM | Use smaller model or enable CPU offload |
| Model download fails | Network/URL issue | Check wget/curl fallback in download script |
| R2 upload fails | Missing credentials | Verify secrets are set correctly |
| ComfyUI won't start | Port conflict or GPU issue | Check logs, verify GPU available |
| XTTS not working | Transformers version conflict | Use separate container |

---

## Document References

### Source Files
- **Dockerfile**: `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile`
- **docker-compose.yml**: `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml`
- **start.sh**: `/home/oz/projects/2025/oz/12/runpod/docker/start.sh`
- **download_models.sh**: `/home/oz/projects/2025/oz/12/runpod/docker/download_models.sh`
- **r2_sync.sh**: `/home/oz/projects/2025/oz/12/runpod/docker/r2_sync.sh`
- **PRD**: `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/hearmeman-extended-template.md`
- **R2 Deployment Plan**: `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/runpod-r2-deployment-pre/master-overview.md`

### External References
- [ComfyUI Official](https://www.comfy.org/)
- [ComfyUI GitHub](https://github.com/Comfy-Org/ComfyUI)
- [VibeVoice-ComfyUI](https://github.com/Enemyx-net/VibeVoice-ComfyUI)
- [WAN Video Generation](https://huggingface.co/Wan-AI)
- [XTTS API Server](https://github.com/daswer123/xtts-api-server)
- [Cloudflare R2 Docs](https://developers.cloudflare.com/r2/)
- [RunPod Documentation](https://docs.runpod.io/)

---

**Document Generated**: 2026-01-17
**Status**: Complete Research Documentation
**Output Location**: `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/research/system-docs-raw.md`
