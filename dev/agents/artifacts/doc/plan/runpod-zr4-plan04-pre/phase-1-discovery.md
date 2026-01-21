# Docker & ComfyUI Infrastructure Discovery Report

**Compiled:** 2026-01-21  
**Codebase:** `/home/oz/projects/2025/oz/12/runpod`  
**Author:** claude-opus-4-5

---

## Executive Summary

This report documents a comprehensive discovery of the Docker and ComfyUI infrastructure in the codebase. The system is a production-ready AI media generation platform with support for text-to-video, image-to-video, image generation, text-to-speech, and video processing capabilities. The infrastructure utilizes a multi-tier GPU architecture (consumer, prosumer, datacenter) with sophisticated model download and deployment patterns.

**Key Findings:**
- 10 core Docker/ComfyUI files analyzed
- 12 workflow templates for various generation tasks
- 15+ AI model families with 50+ variants
- 3-tier GPU memory management system
- Cloudflare R2 integration for output persistence
- Build-time and runtime model download options

---

## 1. Core Docker Configuration

### 1.1 Primary Dockerfile

**File:** `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile`  
**Lines:** 309

#### Base Image
```
ARG BASE_IMAGE=runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04
FROM ${BASE_IMAGE}
```

#### Build Arguments (Lines 12-20)
```dockerfile
ARG COMFYUI_COMMIT=latest
ARG BAKE_WAN_720P=false      # Optional build-time model download
ARG BAKE_WAN_480P=false
ARG BAKE_ILLUSTRIOUS=false
ARG BAKE_STEADYDANCER=false
ARG STEADYDANCER_VARIANT=fp8  # fp8=14GB, fp16=28GB
ARG BAKE_TURBO=false
```

#### Critical Environment Variables (Lines 21-56)

**GPU Tier Configuration:**
```dockerfile
ENV GPU_TIER="consumer"      # consumer (8-24GB), prosumer (24GB+), datacenter (48-80GB)
```

**Tier 1 - Consumer GPU (8-24GB VRAM):**
```dockerfile
ENV ENABLE_GENFOCUS="false"      # Depth-of-Field Refocusing (~12GB VRAM)
ENV ENABLE_QWEN_EDIT="false"     # Image Editing - GGUF quantized models
ENV QWEN_EDIT_MODEL="Q4_K_M"     # Q4_K_M=13GB, Q5_K_M=15GB, Q8_0=22GB, full=54GB
ENV ENABLE_MVINVERSE="false"     # Multi-view Inverse Rendering (~8GB VRAM)
```

**Tier 2 - Prosumer GPU (24GB+ with CPU offload):**
```dockerfile
ENV ENABLE_FLASHPORTRAIT="false" # Portrait Animation (30-60GB VRAM)
ENV ENABLE_STORYMEM="false"      # Multi-Shot Video Storytelling (~20-24GB VRAM)
```

**Tier 3 - Datacenter GPU (48-80GB VRAM - A100/H100):**
```dockerfile
ENV ENABLE_INFCAM="false"        # Camera-Controlled Video Generation (50GB+ VRAM)
```

**GPU Memory Management:**
```dockerfile
ENV GPU_MEMORY_MODE="auto"       # auto, full, sequential_cpu_offload, model_cpu_offload
```

**ComfyUI Settings:**
```dockerfile
ENV COMFYUI_ARGS=""              # --lowvram, --medvram, --novram, --cpu-vae, etc.
ENV COMFYUI_PORT=8188
```

**R2 Sync Configuration:**
```dockerfile
ENV ENABLE_R2_SYNC="false"
ENV R2_ENDPOINT="https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com"
ENV R2_BUCKET="runpod"
ENV R2_ACCESS_KEY_ID=""
ENV R2_SECRET_ACCESS_KEY=""
```

#### Custom Nodes Installed (Lines 89-131)

| Node | Repository | Purpose |
|------|-----------|---------|
| ComfyUI-Manager | ltdrdata | Package management |
| VibeVoice-ComfyUI | Enemyx-net | TTS with voice cloning (v1.8.1+) |
| ComfyUI-Chatterbox | thefader | Resemble AI TTS, zero-shot voice cloning |
| ComfyUI-SCAIL-Pose | kijai | Facial mocap |
| ControlNet Preprocessors | Fannovel16 | ControlNet models |
| TurboDiffusion | anveshane | 100-200x video acceleration |
| ComfyUI-WanVideoWrapper | kijai | WAN 2.2/2.5 video nodes |
| ComfyUI-VideoHelperSuite | Kosinkadink | Video utilities |
| ComfyUI-Genfocus | Local custom | Depth-of-field refocusing |
| ComfyUI-MVInverse | Local custom | Multi-view inverse rendering |

#### Key Dependencies (Lines 149-177)

```dockerfile
# PyTorch - REQUIRED for MMPose compatibility
RUN pip install --no-cache-dir \
    torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu124

# Pose estimation (MMSelfCom workstack)
RUN pip install --no-cache-dir \
    mmengine \
    mmcv==2.1.0 \
    mmdet>=3.1.0 \
    mmpose \
    dwpose>=0.1.0

# Flash Attention - REQUIRED for SteadyDancer
RUN pip install --no-cache-dir flash_attn==2.7.4.post1

# Core ML dependencies
RUN pip install --no-cache-dir \
    cupy-cuda12x \
    imageio[ffmpeg] \
    einops \
    modelscope \
    diffusers>=0.21.0 \
    peft>=0.4.0 \
    opencv-python>=4.5.0 \
    timm \
    pynvml  # NVIDIA GPU management for TurboDiffusion
```

#### Model Directories Created (Line 222)

```
/workspace/ComfyUI/models/
├── checkpoints/           # SDXL models
├── embeddings/            # Textual inversions
├── vibevoice/             # TTS models
├── text_encoders/         # Qwen, UMT5
├── diffusion_models/      # Z-Image, WAN models
├── vae/                   # Autoencoders
├── controlnet/            # ControlNet models
├── loras/                 # Style adapters
├── clip_vision/           # CLIP vision models
├── genfocus/              # Refocusing models
├── qwen/                  # Image editing models
├── mvinverse/             # Multi-view models
├── flashportrait/         # Portrait animation
├── storymem/              # Storytelling models
├── infcam/                # Camera control models
└── steadydancer/          # Dance video models
```

---

## 2. Docker Compose Configurations

### 2.1 Primary Compose File

**File:** `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml`  
**Services:** 2 main services

#### Service 1: Chatterbox TTS (Resemble AI)

```yaml
services:
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
    profiles:
      - chatterbox  # Only starts with: docker compose --profile chatterbox up
    API: http://localhost:8000/v1/audio/speech
    Health: http://localhost:8000/health
```

#### Service 2: Hearmeman Extended (Main ComfyUI)

```yaml
hearmeman-extended:
  build:
    context: .
    dockerfile: Dockerfile
  image: hearmeman-extended:local
  container_name: hearmeman-extended
  runtime: nvidia
  environment:
    # Default enabled models
    - ENABLE_VIBEVOICE=true
    - ENABLE_CONTROLNET=true
    
    # Default disabled models
    - ENABLE_ILLUSTRIOUS=false
    - ENABLE_ZIMAGE=false
    - ENABLE_STEADYDANCER=false
    - ENABLE_WAN22_DISTILL=false
    
    # VibeVoice configuration
    - VIBEVOICE_MODEL=Large
    
    # Storage configuration
    - STORAGE_MODE=persistent
    
    # GPU configuration
    - GPU_TIER=consumer
    - GPU_MEMORY_MODE=auto
    
    # Tier 1 - Consumer GPU (8-24GB VRAM)
    - ENABLE_GENFOCUS=true
    - ENABLE_QWEN_EDIT=true
    - QWEN_EDIT_MODEL=Q4_K_M
    - ENABLE_MVINVERSE=true
    
    # Tier 2 - Prosumer GPU (24GB+ with CPU offload)
    - ENABLE_FLASHPORTRAIT=false
    - ENABLE_STORYMEM=false
    
    # Tier 3 - Datacenter GPU (48-80GB VRAM)
    - ENABLE_INFCAM=false
    
    # SteadyDancer configuration
    - ENABLE_STEADYDANCER=false
    - STEADYDANCER_VARIANT=fp8
    - STEADYDANCER_GUIDE_SCALE=5.0
    - STEADYDANCER_CONDITION_GUIDE=1.0
    - STEADYDANCER_END_CFG=0.4
    - STEADYDANCER_SEED=106060
    
    # DWPose configuration
    - ENABLE_DWPOSE=false
    - DWPOSE_DETECT_HAND=true
    - DWPOSE_DETECT_BODY=true
    - DWPOSE_DETECT_FACE=true
    - DWPOSE_RESOLUTION=512
    
    # TurboDiffusion configuration
    - ENABLE_WAN22_DISTILL=false
    - TURBO_STEPS=4
    - TURBO_GUIDE_SCALE=5.0
    - TURBO_CONDITION_GUIDE=1.0
    - TURBO_END_CFG=0.4
  
  ports:
    - "8188:8188"    # ComfyUI
    - "8888:8888"    # Jupyter
    - "2222:22"      # SSH
  
  volumes:
    - ./models:/workspace/ComfyUI/models
    - ./output:/workspace/ComfyUI/output
    - /home/oz/comfyui/models/vibevoice:/workspace/ComfyUI/models/vibevoice:ro
```

### 2.2 Compose Variants

#### Illustrious-Only Configuration

**File:** `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.illustrious.yml`

```yaml
services:
  illustrious:
    environment:
      # ONLY Illustrious - disable everything else
      - ENABLE_VIBEVOICE=false
      - ENABLE_CONTROLNET=false
      - ENABLE_ZIMAGE=false
      - ENABLE_XTTS=false
      - ENABLE_I2V=false
      - ENABLE_VACE=false
      - ENABLE_FUN_INP=false
      - ENABLE_STEADYDANCER=false
      - ENABLE_SCAIL=false
      - WAN_720P=false
      - WAN_480P=false
      
      # Illustrious ONLY
      - ENABLE_ILLUSTRIOUS=true
      - ENABLE_ILLUSTRIOUS_EMBEDDINGS=true
      
      # CivitAI NSFW LoRAs
      - ENABLE_CIVITAI=true
      - CIVITAI_API_KEY=${CIVITAI_API_KEY}
      - CIVITAI_LORAS=1906687,1736657
```

#### WAN 2.2 Test Configuration

**File:** `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.wan22-test.yml`

Services:
1. **wan22-test-dry** - Verify script without downloads
2. **wan22-test** - Real download test (~28GB)
3. **comfyui-wan22** - Full ComfyUI with WAN 2.2 for workflow testing

---

## 3. Shell Scripts

### 3.1 Model Download Script

**File:** `/home/oz/projects/2025/oz/12/runpod/docker/download_models.sh`  
**Lines:** 867

#### Configuration
```bash
LOG_FILE="/var/log/download_models.log"
DRY_RUN="${DRY_RUN:-false}"
DOWNLOAD_TIMEOUT="${DOWNLOAD_TIMEOUT:-1800}"  # 30 min default
MODELS_DIR="${MODELS_DIR:-/workspace/ComfyUI/models}"
```

#### Key Functions

**download_model()** - Generic download with resume support
- Uses wget with timeout and progress bar
- Falls back to curl on failure
- Detects gated models (401 errors)
- Validates download completion

**hf_download()** - HuggingFace helper
- Constructs URLs from repo and file paths
- Delegates to download_model()

**civitai_download()** - CivitAI API downloader
- Handles API key authentication
- Supports content-disposition headers
- Fallback to curl for redirects

**hf_snapshot_download()** - Python-based snapshot download
- Uses huggingface_hub snapshot_download
- For large model directories

#### Model Download Patterns

**VibeVoice Models (Lines 166-202):**
```bash
# Model variants
microsoft/VibeVoice-1.5B          # 1.5B parameters
aoi-ot/VibeVoice-Large            # Default (~18GB)
FabioSarcino/VibeVoice-Large-Q8   # Quantized variant

# Required Qwen tokenizer
Qwen/Qwen2.5-1.5B tokenizer files
```

**WAN 2.1 720p Models (Lines 217-252):**
```
Total size: ~25GB
├── Text encoder: umt5_xxl_fp8_e4m3fn_scaled.safetensors (9.5GB)
├── CLIP vision: clip_vision_h.safetensors (1.4GB)
├── VAE: wan_2.1_vae.safetensors (335MB)
├── T2V diffusion: wan2.1_t2v_14B_fp8_e4m3fn.safetensors (14GB)
└── I2V diffusion (optional): wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors (14GB)
```

**WAN 2.1 480p Models (Lines 254-274):**
```
Total size: ~12GB
└── T2V diffusion: wan2.1_t2v_1.3B_fp16.safetensors
    # Reuses text encoder + VAE from 720p
```

**WAN 2.2 Distilled / TurboDiffusion I2V (Lines 281-329):**
```
Total size: ~28GB
├── High noise expert: wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors (14GB)
├── Low noise expert: wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors (14GB)
└── Shared dependencies (text encoder, VAE, CLIP vision)
```

**SteadyDancer Variants (Lines 335-403):**
```bash
# Variant selection based on VRAM
fp8  -> Wan21_SteadyDancer_fp8.safetensors (14GB)
fp16 -> Wan21_SteadyDancer_fp16.safetensors (28GB)
gguf -> steadydancer-14B-q4_k_m.gguf (quantized)
```

**TurboDiffusion (Lines 434-444):**
```
wan_2.1_turbodiffusion.safetensors (14GB)
100-200x speedup for video generation
```

**ControlNet Models (Lines 462-498):**
```
Models: canny, depth, openpose, lineart, normalbae
Format: control_v11p_sd15_*_fp16.safetensors
Total: ~3.6GB for 5 models
```

**Realism Illustrious (Lines 547-577):**
```
Checkpoints:
├── realismIllustriousByStableYogi_v50FP16.safetensors (6.46GB)
├── Stable_Yogis_Illustrious_Positives.safetensors (352KB)
└── Stable_Yogis_Illustrious_Negatives.safetensors (536KB)
```

**Qwen Image Edit (Lines 621-663):**
```
Quantization levels:
├── Q4_K_M -> qwen-image-edit-2511-Q4_K_M.gguf (13GB)
├── Q5_K_M -> qwen-image-edit-2511-Q5_K_M.gguf (15GB)
├── Q6_K   -> qwen-image-edit-2511-Q6_K.gguf
├── Q8_0   -> qwen-image-edit-2511-Q8_0.gguf (22GB)
├── Q2_K   -> qwen-image-edit-2511-Q2_K.gguf
├── Q3_K_M -> qwen-image-edit-2511-Q3_K_M.gguf
└── full   -> Qwen/Qwen-Image-Edit-2511 (54GB - datacenter only)
```

### 3.2 Startup Script

**File:** `/home/oz/projects/2025/oz/12/runpod/docker/start.sh`  
**Lines:** 166

#### Storage Mode Detection (Lines 13-31)

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
    fi
}
```

#### GPU VRAM Detection & Configuration (Lines 36-91)

**VRAM Detection:**
```bash
GPU_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits)
```

**Auto-detect GPU tier:**
```bash
if (( GPU_VRAM >= 48000 )); then
    export GPU_TIER="datacenter"
elif (( GPU_VRAM >= 20000 )); then
    export GPU_TIER="prosumer"
else
    export GPU_TIER="consumer"
fi
```

**Auto-detect memory mode:**
```bash
if (( GPU_VRAM >= 48000 )); then
    export GPU_MEMORY_MODE="full"
elif (( GPU_VRAM >= 24000 )); then
    export GPU_MEMORY_MODE="model_cpu_offload"
else
    export GPU_MEMORY_MODE="sequential_cpu_offload"
fi
```

**Auto-detect ComfyUI VRAM flags:**
```bash
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
```

#### Startup Sequence

1. Detect storage mode
2. Detect GPU configuration (VRAM, tier, memory mode, ComfyUI args)
3. Setup SSH (if PUBLIC_KEY provided)
4. Setup JupyterLab (if JUPYTER_PASSWORD provided)
5. Update custom nodes (if UPDATE_NODES_ON_START=true)
6. Download models (/download_models.sh)
7. Start R2 sync daemon (if ENABLE_R2_SYNC=true)
8. Launch ComfyUI

### 3.3 R2 Sync Daemon

**File:** `/home/oz/projects/2025/oz/12/runpod/docker/r2_sync.sh`  
**Lines:** 58

#### Configuration
```bash
OUTPUT_DIR="${COMFYUI_OUTPUT_DIR:-/workspace/ComfyUI/output}"
LOG_FILE="/var/log/r2_sync.log"
UPLOAD_SCRIPT="/upload_to_r2.py"
```

#### Watch Patterns (Line 15)
```bash
WATCH_PATTERNS="\.png$|\.jpg$|\.jpeg$|\.webp$|\.mp4$|\.webm$|\.gif$|\.wav$|\.mp3$|\.flac$"
```

#### Behavior
- Uses inotifywait to watch for close_write events
- 1-second sleep ensures file completion
- Background upload (&) to avoid blocking
- Supports both R2_ACCESS_KEY_ID and R2_ACCESS_KEY naming conventions

---

## 4. ComfyUI Workflow Files

**Location:** `/home/oz/projects/2025/oz/12/runpod/docker/workflows/`

### 4.1 Video Generation Workflows

#### steadydancer-dance.json

**Purpose:** Generate dance videos from reference images  
**Model:** SteadyDancer I2V  
**VRAM:** 14-28GB (datacenter GPU recommended)

**Key Nodes:**
```json
{
  "class_type": "LoadImage",
  "inputs": {"image": "reference_character.png"}
},
{
  "class_type": "LoadVideo",
  "inputs": {"video": "driving_dance.mp4", "frame_count": 16, "fps": 25}
},
{
  "class_type": "DWPreprocessor",
  "inputs": {
    "detect_hand": true,
    "detect_body": true,
    "detect_face": true,
    "resolution": 512
  }
},
{
  "class_type": "Wan_LoadDiffusionModel",
  "inputs": {
    "model_name": "Wan21_SteadyDancer_fp8.safetensors",
    "weight_dtype": "fp8"
  }
},
{
  "class_type": "Wan_ReferenceAttention",
  "inputs": {
    "reference_image": "1",
    "conditioning_strength": 0.8,
    "reference_type": "image"
  }
},
{
  "class_type": "Wan_CrossFrameAttention",
  "inputs": {
    "driving_video": "2",
    "frame_count": 16,
    "motion_strength": 1.0
  }
},
{
  "class_type": "Wan_KSampler",
  "inputs": {
    "seed": 106060,
    "steps": 50,
    "cfg": 5.0,
    "sampler_name": "euler",
    "scheduler": "simple"
  }
}
```

#### steadydancer-turbo.json

**Purpose:** High-speed dance video with TurboDiffusion (100-200x acceleration)  
**Models:** SteadyDancer + TurboDiffusion  
**VRAM:** 24GB+ (A100 80GB optimal)

**Key Additional Nodes:**
```json
{
  "class_type": "Wan_LoadTurbo",
  "inputs": {
    "model_name": "wan_2.1_turbodiffusion.safetensors",
    "steps": 4,
    "guide_scale": 5.0,
    "condition_guide_scale": 1.0,
    "end_cond_cfg": 0.4
  }
}
```

#### wan22-t2v-5b.json

**Purpose:** Text-to-Video with WAN 2.2 5B model  
**Model:** wan2.2_ti2v_5B_fp16.safetensors  
**VRAM:** 24GB+

**Key Nodes:**
```json
{
  "type": "UNETLoader",
  "widgets_values": ["wan2.2_ti2v_5B_fp16.safetensors", "default"]
},
{
  "type": "CLIPLoader",
  "widgets_values": ["umt5_xxl_fp8_e4m3fn_scaled.safetensors", "wan"]
},
{
  "type": "VAELoader",
  "widgets_values": ["wan_2.1_vae.safetensors"]
},
{
  "type": "EmptyMochiLatentVideo",
  "widgets_values": [1280, 704, 41, 1]  # width, height, frames, fps
}
```

### 4.2 Image Generation Workflows

#### z-image-turbo-txt2img.json

**Purpose:** Fast image generation  
**Model:** Z-Image Turbo  
**VRAM:** 8-12GB

#### realism-illustrious-txt2img.json

**Purpose:** Photorealistic image generation  
**Model:** Realism Illustrious XL  
**VRAM:** 8-12GB

#### realism-illustrious-basic.json

**Purpose:** Basic Illustrious workflow with positive/negative embeddings

#### realism-illustrious-nsfw-lora.json

**Purpose:** Illustrious with NSFW-optimized LoRAs  
**CivitAI LoRAs:** 1906687, 1736657

### 4.3 Audio Generation Workflows

#### vibevoice-tts-basic.json

**Purpose:** Text-to-Speech with VibeVoice  
**Model:** VibeVoice-Large  
**VRAM:** 8-16GB

### 4.4 Utility Workflows

#### genfocus-refocusing.json

**Purpose:** Depth-of-field refocusing  
**Model:** Genfocus  
**VRAM:** ~12GB

#### mvinverse-material-extraction.json

**Purpose:** Multi-view material extraction  
**Model:** MVInverse  
**VRAM:** ~8GB

---

## 5. Environment Variables Reference

### 5.1 Model Enable/Disable Flags

| Variable | Default | Purpose |
|----------|---------|---------|
| ENABLE_VIBEVOICE | true | VibeVoice TTS |
| ENABLE_ZIMAGE | false | Z-Image Turbo |
| ENABLE_ILLUSTRIOUS | false | Realism Illustrious |
| ENABLE_WAN22_DISTILL | false | TurboDiffusion I2V |
| ENABLE_STEADYDANCER | false | Dance video generation |
| ENABLE_DWPOSE | false | Pose estimation |
| ENABLE_CONTROLNET | true | ControlNet models |
| ENABLE_I2V | false | Image-to-Video |
| ENABLE_VACE | false | Video editing |
| ENABLE_FUN_INP | false | Frame interpolation |
| ENABLE_SCAIL | false | Facial mocap |
| ENABLE_XTTS | false | XTTS v2 TTS |
| ENABLE_CIVITAI | false | CivitAI LoRA downloads |
| ENABLE_GENFOCUS | false | Refocusing |
| ENABLE_QWEN_EDIT | false | Image editing |
| ENABLE_MVINVERSE | false | Multi-view rendering |
| ENABLE_FLASHPORTRAIT | false | Portrait animation |
| ENABLE_STORYMEM | false | Multi-shot video |
| ENABLE_INFCAM | false | Camera control |

### 5.2 Video Generation Flags

| Variable | Default | Purpose |
|----------|---------|---------|
| WAN_720P | true | WAN 2.1 720p models (~25GB) |
| WAN_480P | false | WAN 2.1 480p models (~12GB) |
| STEADYDANCER_VARIANT | fp8 | fp8 (14GB), fp16 (28GB), gguf |
| STEADYDANCER_GUIDE_SCALE | 5.0 | CFG scale |
| STEADYDANCER_CONDITION_GUIDE | 1.0 | Motion guidance |
| STEADYDANCER_END_CFG | 0.4 | Final CFG |
| STEADYDANCER_SEED | 106060 | Random seed |
| TURBO_STEPS | 4 | TurboDiffusion steps |
| TURBO_GUIDE_SCALE | 5.0 | Turbo CFG |
| TURBO_CONDITION_GUIDE | 1.0 | Turbo motion |
| TURBO_END_CFG | 0.4 | Turbo final CFG |

### 5.3 DWPose Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| ENABLE_DWPOSE | false | Enable pose estimation |
| DWPOSE_DETECT_HAND | true | Hand detection |
| DWPOSE_DETECT_BODY | true | Body detection |
| DWPOSE_DETECT_FACE | true | Face detection |
| DWPOSE_RESOLUTION | 512 | Output resolution |

### 5.4 Model Specifications

| Variable | Default | Options |
|----------|---------|---------|
| VIBEVOICE_MODEL | Large | 1.5B, Large, Large-Q8 |
| QWEN_EDIT_MODEL | Q4_K_M | Q4_K_M, Q5_K_M, Q6_K, Q8_0, Q2_K, Q3_K_M, full |

---

## 6. Quantization Patterns

### 6.1 Detected Quantization Formats

| Format | Suffix | VRAM Reduction | Use Case |
|--------|--------|----------------|----------|
| FP8 (Float8) | _fp8_e4m3fn, _fp8 | ~50% | WAN 2.1 T2V/I2V |
| FP8 Scaled | _fp8_scaled | ~50% | WAN 2.2 distilled |
| FP16 (Float16) | _fp16 | Standard | WAN 2.1 480p, VACE, Fun InP |
| GGUF | .gguf | Variable | Qwen Image Edit, SteadyDancer |

### 6.2 Model Size by Quantization

**WAN 2.1 14B Diffusion Model:**
- FP8: ~14GB
- FP16: ~28GB (if unpruned)

**SteadyDancer:**
- fp8: ~14GB
- fp16: ~28GB
- gguf (Q4_K_M): ~7GB

**Qwen Image Edit:**
- Q4_K_M: ~13GB
- Q5_K_M: ~15GB
- Q8_0: ~22GB
- Full: ~54GB

---

## 7. GPU Tier Mapping

### 7.1 Consumer GPU (8-24GB VRAM)

**Examples:** RTX 4080 Super (16GB), RTX 4090 (24GB)

**Enabled Features:**
- ENABLE_GENFOCUS
- ENABLE_QWEN_EDIT (quantized)
- ENABLE_MVINVERSE

**Memory Mode:**
```bash
GPU_MEMORY_MODE="sequential_cpu_offload"
```

**ComfyUI Args:**
```bash
# <8GB VRAM
COMFYUI_ARGS="--lowvram --cpu-vae --force-fp16"

# 8-12GB VRAM
COMFYUI_ARGS="--lowvram --force-fp16"

# 12-16GB VRAM
COMFYUI_ARGS="--medvram --cpu-text-encoder --force-fp16"

# 16-24GB VRAM
COMFYUI_ARGS="--normalvram --force-fp16"
```

### 7.2 Prosumer GPU (24GB+ VRAM)

**Examples:** RTX 6000 (48GB), A40 (48GB)

**Enabled Features:**
- ENABLE_FLASHPORTRAIT
- ENABLE_STORYMEM

**Memory Mode:**
```bash
GPU_MEMORY_MODE="model_cpu_offload"
```

**ComfyUI Args:**
```bash
# No args needed for >=24GB VRAM
COMFYUI_ARGS=""
```

### 7.3 Datacenter GPU (48-80GB VRAM)

**Examples:** A100 80GB, H100 80GB

**Enabled Features:**
- ENABLE_INFCAM
- Qwen Image Edit (full model)
- WAN 2.2 5B (fp16)

**Memory Mode:**
```bash
GPU_MEMORY_MODE="full"
```

**ComfyUI Args:**
```bash
COMFYUI_ARGS=""
```

---

## 8. Storage Requirements

### 8.1 Model Sizes

| Model | Size | Notes |
|-------|------|-------|
| VibeVoice-Large | ~18GB | TTS with voice cloning |
| WAN 2.1 720p T2V | ~25GB | 14B diffusion + text encoder + VAE |
| WAN 2.1 480p T2V | ~12GB | 1.3B diffusion |
| WAN 2.2 Distilled I2V | ~28GB | 2x expert models |
| SteadyDancer fp8 | ~14GB | Dance video |
| SteadyDancer fp16 | ~28GB | Dance video (full precision) |
| TurboDiffusion | ~14GB | 100-200x acceleration |
| Realism Illustrious | ~6.5GB | Checkpoint + embeddings |
| ControlNet (5 models) | ~3.6GB | Preprocessors |
| DWPose | ~2GB | Pose estimation |
| Qwen Image Edit Q4_K_M | ~13GB | Image editing |
| Qwen Image Edit Q8_0 | ~22GB | Image editing (higher quality) |
| Qwen Image Edit full | ~54GB | Image editing (datacenter) |
| Genfocus | ~12GB | Refocusing |
| MVInverse | ~8GB | Multi-view rendering |
| FlashPortrait | ~60GB | Portrait animation |
| StoryMem | ~20GB | LoRAs + base models |
| InfCam | ~50GB+ | Camera control (experimental) |

### 8.2 Total Storage Estimates

| Configuration | Size |
|--------------|------|
| Minimum (VibeVoice + ControlNet) | ~25GB |
| Typical (VibeVoice + WAN + ControlNet) | ~80-120GB |
| All models | ~230GB |

---

## 9. Port Configuration

| Port | Service | Protocol |
|------|---------|----------|
| 22 | SSH server | TCP |
| 8188 | ComfyUI web interface | HTTP |
| 8888 | JupyterLab (optional) | HTTP |
| 4123 | Chatterbox TTS API | HTTP |
| 8000 | Alternative TTS port | HTTP |

---

## 10. Deployment Patterns

### 10.1 Docker Build Commands

```bash
# Standard build
cd docker && docker compose build

# With TTS support
docker compose --profile chatterbox up -d

# With XTTS support
docker compose --profile xtts up xtts -d

# Illustrious-only
docker compose -f docker-compose.illustrious.yml up -d

# WAN 2.2 test (dry run)
docker compose -f docker-compose.wan22-test.yml run --rm wan22-test-dry

# WAN 2.2 test (real download, ~28GB)
docker compose -f docker-compose.wan22-test.yml run --rm wan22-test
```

### 10.2 RunPod Pod Creation

```bash
~/.local/bin/runpodctl create pod \
  --name "illustrious-$(date +%H%M)" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA GeForce RTX 4090" \
  --gpuCount 1 \
  --containerDiskSize 20 \
  --volumeSize 15 \
  --secureCloud \
  --ports "8188/http" \
  --env "ENABLE_ILLUSTRIOUS=true" \
  --env "CIVITAI_API_KEY=<key>" \
  --env "R2_ACCESS_KEY_ID=<key>" \
  --env "R2_SECRET_ACCESS_KEY=<secret>" \
  --env "R2_ENDPOINT=https://..." \
  --env "R2_BUCKET=runpod" \
  --env "ENABLE_R2_SYNC=true"
```

### 10.3 Build-Time Model Downloads

```dockerfile
# In Dockerfile or docker build
ARG BAKE_WAN_720P=true
ARG BAKE_WAN_480P=false
ARG BAKE_ILLUSTRIOUS=true
ARG BAKE_STEADYDANCER=true
ARG STEADYDANCER_VARIANT=fp8
ARG BAKE_TURBO=true
```

---

## 11. Key Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile` | 309 | Multi-layer build with ComfyUI, custom nodes, dependencies |
| `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml` | 110 | Main compose with 2 services + 90+ environment variables |
| `/home/oz/projects/2025/oz/12/runpod/docker/download_models.sh` | 867 | Comprehensive model downloader with resume support |
| `/home/oz/projects/2025/oz/12/runpod/docker/start.sh` | 166 | Startup orchestration with GPU/storage detection |
| `/home/oz/projects/2025/oz/12/runpod/docker/r2_sync.sh` | 58 | Cloudflare R2 upload daemon |
| `/home/oz/projects/2025/oz/12/runpod/docker/workflows/steadydancer-dance.json` | - | Dance animation workflow |
| `/home/oz/projects/2025/oz/12/runpod/docker/workflows/steadydancer-turbo.json` | - | Accelerated dance workflow |
| `/home/oz/projects/2025/oz/12/runpod/docker/workflows/wan22-t2v-5b.json` | - | WAN 2.2 text-to-video |
| `/home/oz/projects/2025/oz/12/runpod/docker/workflows/wan21-t2v-14b-api.json` | - | WAN 2.1 text-to-video |
| `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.illustrious.yml` | 51 | Illustrious-only config |
| `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.wan22-test.yml` | 91 | WAN 2.2 test config |

---

## 12. Version Information

| Component | Version |
|-----------|---------|
| CUDA | 12.8.1 |
| Python | 3.11 |
| PyTorch | 2.5.1 |
| torchvision | 0.20.1 |
| torchaudio | 2.5.1 |
| Ubuntu | 22.04 |
| ComfyUI | latest (GitHub) |
| ComfyUI-WanVideoWrapper | latest (kijai) |
| VibeVoice-ComfyUI | 1.8.1+ (Enemyx-net) |
| Flash Attention | 2.7.4.post1 |
| mmcv | 2.1.0 |
| mmpose | latest |

---

## 13. Critical Learnings

### 13.1 GPU Memory Management

- **Automatic detection:** Script auto-detects VRAM and applies appropriate flags
- **Tiered approach:** Different features enabled based on available VRAM
- **Quantization critical:** FP8 reduces VRAM by ~50% compared to FP16
- **Sequential offload:** Required for <24GB VRAM consumer GPUs

### 13.2 Model Download Strategy

- **Resume support:** Download script supports resuming interrupted downloads
- **Build-time option:** Models can be baked into image for instant startup
- **Multiple sources:** HuggingFace (primary), CivitAI (for SDXL models)
- **Size awareness:** Scripts report expected and actual sizes

### 13.3 SteadyDancer Requirements

- **Flash Attention mandatory:** Without it, quality degrades significantly
- **Pose extraction:** DWPose required for dance video generation
- **VRAM heavy:** Needs 24GB+ for comfortable operation
- **TurboDiffusion synergy:** 100-200x speedup when combined

### 13.4 R2 Sync Configuration

- **Daemon-based:** Background process watches for file creation
- **Credentials:** Supports both R2_ACCESS_KEY_ID and R2_ACCESS_KEY naming
- **File patterns:** Monitors for images, videos, and audio files
- **Non-blocking:** Uploads in background to avoid workflow interruption

---

## 14. Recommendations

1. **Default Composition:** Use `docker-compose.yml` for most deployments
2. **GPU Optimization:** Let `start.sh` auto-detect VRAM and configure settings
3. **Storage Planning:** Plan for 80-120GB for typical configurations
4. **Model Downloads:** Use `DRY_RUN=true` first to verify script behavior
5. **Quantization:** Prefer FP8 variants for consumer GPUs (<24GB VRAM)
6. **RunPod Deployment:** Use `--secureCloud` for reliable network speeds
7. **R2 Sync:** Enable for ephemeral RunPod pods to persist outputs

---

**End of Discovery Report**
