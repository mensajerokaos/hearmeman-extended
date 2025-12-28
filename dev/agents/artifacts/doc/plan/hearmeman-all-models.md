# PRD: Hearmeman Extended Template - All AI Models Integration

**Author**: oz + claude-opus-4-5
**Date**: 2025-12-28
**Version**: 1.0

---

## Executive Summary

This PRD covers the complete integration of 6 new AI models into the hearmeman-extended RunPod template, organized by GPU tier:

| Tier | GPU VRAM | Models |
|------|----------|--------|
| **Consumer** | 8-24GB | Qwen-Image-Edit-2511, Genfocus, MVInverse |
| **Prosumer** | 24GB+ (CPU offload) | FlashPortrait, StoryMem |
| **Datacenter** | 48-80GB | InfCam |

**Total Storage**: ~150-200GB (all models enabled)

---

## Table of Contents

1. [Phase 1: Environment Variables & Dockerfile](#phase-1-environment-variables--dockerfile)
2. [Phase 2: Tier 1 Downloads (Consumer)](#phase-2-tier-1-downloads-consumer)
3. [Phase 3: Tier 2 Downloads (Prosumer)](#phase-3-tier-2-downloads-prosumer)
4. [Phase 4: Tier 3 Downloads (Datacenter)](#phase-4-tier-3-downloads-datacenter)
5. [Phase 5: Custom Node Wrappers](#phase-5-custom-node-wrappers)
6. [Phase 6: CPU Offloading Configuration](#phase-6-cpu-offloading-configuration)

---

## Phase 1: Environment Variables & Dockerfile

### 1.1 New Environment Variables

Add after line 12 in `docker/Dockerfile` (after `ENV COMFYUI_PORT=8188`):

```dockerfile
# GPU Tier and Model Toggle Configuration
ENV GPU_TIER="consumer"
# Options: consumer, prosumer, datacenter

ENV ENABLE_GENFOCUS="false"
ENV ENABLE_QWEN_EDIT="false"
ENV ENABLE_MVINVERSE="false"
ENV ENABLE_FLASHPORTRAIT="false"
ENV ENABLE_STORYMEM="false"
ENV ENABLE_INFCAM="false"

# GPU Memory Management
ENV GPU_MEMORY_MODE="full"
# Options: full, sequential_cpu_offload, model_cpu_offload

ENV COMFYUI_ARGS=""
# For: --lowvram, --medvram, --novram, --cpu-vae, etc.
```

### 1.2 New Pip Dependencies

Add to Layer 4 in `docker/Dockerfile` (after `protobuf`):

```dockerfile
RUN pip install --no-cache-dir \
    huggingface_hub \
    accelerate \
    safetensors \
    sentencepiece \
    protobuf \
    # New dependencies for all models
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
    flash_attn
```

### 1.3 New Model Directories

Update line 123 in `docker/Dockerfile`:

```dockerfile
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision,genfocus,infcam,mvinverse,flashportrait,storymem,qwen}
```

---

## Phase 2: Tier 1 Downloads (Consumer)

Add to `docker/download_models.sh`:

### 2.1 Qwen-Image-Edit-2511 (~10-15GB)

```bash
# ============================================
# Qwen-Image-Edit-2511 (Instruction-based Image Editing)
# ============================================
if [ "${ENABLE_QWEN_EDIT:-false}" = "true" ]; then
    echo "[Qwen-Edit] Downloading model components..."

    hf_download "Qwen/Qwen-Image-Edit-2511" \
        "qwen_2.5_vl_7b_fp8_scaled.safetensors" \
        "$MODELS_DIR/qwen/qwen_2.5_vl_7b_fp8_scaled.safetensors"
fi
```

### 2.2 Genfocus (~12GB)

```bash
# ============================================
# Genfocus (Depth-of-Field Refocusing)
# ============================================
if [ "${ENABLE_GENFOCUS:-false}" = "true" ]; then
    echo "[Genfocus] Downloading model components..."

    hf_download "nycu-cplab/Genfocus-Model" \
        "bokehNet.safetensors" \
        "$MODELS_DIR/genfocus/bokehNet.safetensors"

    hf_download "nycu-cplab/Genfocus-Model" \
        "deblurNet.safetensors" \
        "$MODELS_DIR/genfocus/deblurNet.safetensors"

    hf_download "nycu-cplab/Genfocus-Model" \
        "checkpoints/depth_pro.pt" \
        "$MODELS_DIR/genfocus/depth_pro.pt"
fi
```

### 2.3 MVInverse (~8GB)

```bash
# ============================================
# MVInverse (Multi-view Inverse Rendering)
# ============================================
if [ "${ENABLE_MVINVERSE:-false}" = "true" ]; then
    echo "[MVInverse] Cloning repository..."
    MVINVERSE_DIR="$MODELS_DIR/mvinverse"
    if [ ! -d "$MVINVERSE_DIR" ]; then
        git clone https://github.com/Maddog241/mvinverse "$MVINVERSE_DIR"
        echo "  [Note] Checkpoints download via inference.py --ckpt"
    else
        echo "  [Skip] MVInverse repository already exists"
    fi
fi
```

---

## Phase 3: Tier 2 Downloads (Prosumer)

### 3.1 FlashPortrait (~60GB full, ~10GB with CPU offload)

```bash
# ============================================
# FlashPortrait (Portrait Animation)
# VRAM: 60GB (full) | 30GB (model_cpu_offload) | 10GB (sequential_cpu_offload)
# RAM: 32GB minimum for CPU offload modes
# ============================================
if [ "${ENABLE_FLASHPORTRAIT:-false}" = "true" ]; then
    echo "[FlashPortrait] Downloading models..."

    case "${GPU_MEMORY_MODE:-full}" in
        "full"|"model_full_load")
            echo "  [FlashPortrait] Full model load (60GB VRAM required)"
            ;;
        "sequential_cpu_offload")
            echo "  [FlashPortrait] Sequential CPU offload (10GB VRAM + 32GB+ RAM)"
            ;;
        "model_cpu_offload")
            echo "  [FlashPortrait] Model CPU offload (30GB VRAM)"
            ;;
    esac

    # FlashPortrait main checkpoint
    python -c "
from huggingface_hub import snapshot_download
snapshot_download('FrancisRing/FlashPortrait',
    local_dir='$MODELS_DIR/flashportrait/FlashPortrait',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] FlashPortrait will download on first use"

    # Wan2.1 I2V 14B (required dependency)
    hf_download "Wan-AI/Wan2.1-I2V-14B-720P" \
        "wan2.1_i2v_14B_720P_fp16.safetensors" \
        "$MODELS_DIR/diffusion_models/wan2.1_i2v_14B_720P_fp16.safetensors"
fi
```

### 3.2 StoryMem (Based on Wan2.2)

```bash
# ============================================
# StoryMem (Multi-Shot Video Storytelling)
# Based on Wan2.2, uses LoRA variants (MI2V, MM2V)
# VRAM: ~20-24GB (base models + LoRA)
# ============================================
if [ "${ENABLE_STORYMEM:-false}" = "true" ]; then
    echo "[StoryMem] Downloading models and dependencies..."

    # Ensure Wan2.1 T2V base model
    if [ ! -f "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" ]; then
        echo "  [StoryMem] Downloading Wan2.1 T2V 14B base model..."
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" \
            "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors"
    fi

    # Ensure Wan2.1 I2V base model
    if [ ! -f "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" ]; then
        echo "  [StoryMem] Downloading Wan2.1 I2V 720p 14B base model..."
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" \
            "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors"
    fi

    # StoryMem LoRA variants
    echo "  [StoryMem] Downloading StoryMem LoRA variants..."
    python -c "
from huggingface_hub import snapshot_download
snapshot_download('Kevin-thu/StoryMem',
    local_dir='$MODELS_DIR/loras/StoryMem',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] StoryMem LoRAs will download on first use"
fi
```

---

## Phase 4: Tier 3 Downloads (Datacenter)

### 4.1 InfCam (~50GB+, A100/H100 Required)

```bash
# ============================================
# InfCam (Camera-Controlled Video Generation)
# WARNING: EXPERIMENTAL - DATACENTER TIER ONLY
# VRAM: 50GB+ inference, 52-56GB/GPU training
# Requires: A100 80GB or H100 80GB
# Storage: ~50GB+
# ============================================
if [ "${GPU_TIER}" = "datacenter" ] && [ "${ENABLE_INFCAM:-false}" = "true" ]; then
    echo ""
    echo "[InfCam] EXPERIMENTAL - Downloading for datacenter tier only..."

    # InfCam main checkpoint
    python -c "
from huggingface_hub import snapshot_download
snapshot_download('emjay73/InfCam',
    local_dir='$MODELS_DIR/infcam/InfCam',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] InfCam will download on first use"

    # UniDepth-v2-vitl14 (required dependency)
    python -c "
from huggingface_hub import snapshot_download
snapshot_download('lpiccinelli/unidepth-v2-vitl14',
    local_dir='$MODELS_DIR/infcam/unidepth-v2-vitl14',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] UniDepth will download on first use"

    echo "[InfCam] Download complete"
else
    if [ "${ENABLE_INFCAM:-false}" = "true" ]; then
        echo "[InfCam] Skipped - GPU_TIER must be 'datacenter'"
    fi
fi
```

---

## Phase 5: Custom Node Wrappers

### 5.1 Overview

| Model | ComfyUI Support | Node Required |
|-------|----------------|---------------|
| Qwen-Image-Edit | Native workflows | No |
| Genfocus | None | Yes - ComfyUI-Genfocus |
| MVInverse | None | Yes - ComfyUI-MVInverse |
| FlashPortrait | None | Yes - ComfyUI-FlashPortrait |
| StoryMem | Uses Wan2.2 nodes | No (uses existing ComfyUI-WAN) |
| InfCam | None | Yes (future) |

### 5.2 ComfyUI-Genfocus

**File Structure:**
```
custom_nodes/ComfyUI-Genfocus/
  __init__.py
  nodes.py
  requirements.txt
```

**nodes.py:**
```python
import torch
import numpy as np
from PIL import Image

class GenfocusLoader:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            print("Loading Genfocus model...")
            # Load bokehNet, deblurNet, depth_pro
            cls._model = "GenfocusModel"
        return cls._model

class GenfocusRefocus:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "focal_depth": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
                "blur_amount": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0, "step": 0.1}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "refocus_image"
    CATEGORY = "RunPod/Image/Genfocus"

    def refocus_image(self, image, focal_depth, blur_amount):
        model = GenfocusLoader.get_model()
        # Convert ComfyUI tensor -> PIL -> inference -> tensor
        return (image,)  # Placeholder

NODE_CLASS_MAPPINGS = {"GenfocusRefocus": GenfocusRefocus}
NODE_DISPLAY_NAME_MAPPINGS = {"GenfocusRefocus": "Genfocus Refocus Image"}
```

**Dockerfile Addition:**
```dockerfile
# Genfocus Custom Node
RUN git clone --depth 1 https://github.com/rayray9999/Genfocus.git /workspace/Genfocus_src && \
    mkdir -p custom_nodes/ComfyUI-Genfocus && \
    pip install --no-cache-dir -r /workspace/Genfocus_src/requirements.txt || true && \
    rm -rf /workspace/Genfocus_src
```

### 5.3 ComfyUI-FlashPortrait

**nodes.py:**
```python
import torch
import folder_paths

class FlashPortraitLoader:
    _model = None

    @classmethod
    def get_model(cls, gpu_memory_mode="sequential_cpu_offload"):
        if cls._model is None:
            print(f"Loading FlashPortrait ({gpu_memory_mode})...")
            cls._model = "FlashPortraitModel"
        return cls._model

class FlashPortraitAnimator:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "source_image": ("IMAGE",),
                "driving_video": (folder_paths.get_filename_list("video"),),
                "resolution": (["480x832", "720x1280", "1280x720"],),
                "gpu_memory_mode": (["sequential_cpu_offload", "model_cpu_offload", "model_full_load"],),
            }
        }

    RETURN_TYPES = ("VIDEO",)
    FUNCTION = "animate_portrait"
    CATEGORY = "RunPod/Video/FlashPortrait"

    def animate_portrait(self, source_image, driving_video, resolution, gpu_memory_mode):
        model = FlashPortraitLoader.get_model(gpu_memory_mode)
        return ("/tmp/output.mp4",)  # Placeholder

NODE_CLASS_MAPPINGS = {"FlashPortraitAnimator": FlashPortraitAnimator}
NODE_DISPLAY_NAME_MAPPINGS = {"FlashPortraitAnimator": "FlashPortrait Animate"}
```

---

## Phase 6: CPU Offloading Configuration

### 6.1 ComfyUI VRAM Flags

| Flag | VRAM Use | Description |
|------|----------|-------------|
| `--lowvram` | ~4GB | Aggressive CPU-GPU transfers |
| `--medvram` | ~6-8GB | Balanced offloading |
| `--novram` | Near-zero | Maximum offloading |
| `--cpu` | 0 | CPU-only (very slow) |
| `--cpu-vae` | Reduces | VAE on CPU |
| `--cpu-text-encoder` | Reduces | Text encoder on CPU |
| `--force-fp16` | Reduces | Half precision |
| `--reserve-vram N` | Custom | Reserve N GB for OS |

### 6.2 Recommended Configurations by GPU

| GPU VRAM | ComfyUI Args | Model Memory Mode |
|----------|--------------|-------------------|
| 8GB | `--lowvram --cpu-vae --force-fp16` | N/A |
| 12GB | `--medvram --cpu-text-encoder --force-fp16` | N/A |
| 24GB | `--normalvram` | `model_cpu_offload` |
| 48GB+ | (default) | `model_full_load` |

### 6.3 start.sh Integration

```bash
#!/bin/bash

# Detect GPU VRAM
GPU_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n 1)
echo "Detected GPU VRAM: ${GPU_VRAM} MB"

# Set flags based on VRAM
if (( GPU_VRAM < 12000 )); then
    COMFYUI_ARGS="--lowvram --cpu-vae --force-fp16"
    GPU_MEMORY_MODE="sequential_cpu_offload"
elif (( GPU_VRAM < 24000 )); then
    COMFYUI_ARGS="--medvram --cpu-text-encoder --force-fp16"
    GPU_MEMORY_MODE="model_cpu_offload"
else
    COMFYUI_ARGS=""
    GPU_MEMORY_MODE="model_full_load"
fi

export COMFYUI_ARGS
export GPU_MEMORY_MODE

python /workspace/ComfyUI/main.py $COMFYUI_ARGS
```

### 6.4 RAM Requirements

| System RAM | Use Case |
|------------|----------|
| 16GB | Minimum for `--lowvram` |
| 32GB | Comfortable for most workflows |
| 64GB+ | Large video models with CPU offload |

---

## Implementation Checklist

### Phase 1: Dockerfile Changes
- [ ] Add environment variables (GPU_TIER, ENABLE_*, GPU_MEMORY_MODE, COMFYUI_ARGS)
- [ ] Add pip dependencies
- [ ] Add model directories

### Phase 2: Tier 1 Downloads
- [ ] Qwen-Image-Edit-2511 download section
- [ ] Genfocus download section
- [ ] MVInverse clone section

### Phase 3: Tier 2 Downloads
- [ ] FlashPortrait download with memory modes
- [ ] StoryMem download with Wan2.2 dependencies

### Phase 4: Tier 3 Downloads
- [ ] InfCam download (datacenter only)

### Phase 5: Custom Nodes
- [ ] ComfyUI-Genfocus skeleton
- [ ] ComfyUI-MVInverse skeleton
- [ ] ComfyUI-FlashPortrait skeleton

### Phase 6: CPU Offloading
- [ ] Update start.sh with VRAM detection
- [ ] Document RAM requirements
- [ ] Test configurations per GPU tier

---

## Storage Summary

| Model | Size | Tier |
|-------|------|------|
| Qwen-Image-Edit-2511 | ~10-15GB | Consumer |
| Genfocus | ~12GB | Consumer |
| MVInverse | ~8GB | Consumer |
| FlashPortrait | ~60GB | Prosumer |
| StoryMem | ~20GB (LoRAs) | Prosumer |
| InfCam | ~50GB+ | Datacenter |
| **Total** | **~160-180GB** | |

---

## Artifact Files

Detailed phase documents:
- `phase1-env-dockerfile.md` - Environment variables and Dockerfile changes
- `phase2-tier1-downloads.md` - Consumer GPU model downloads
- `phase3-tier2-downloads.md` - Prosumer GPU model downloads
- `phase4-tier3-downloads.md` - Datacenter GPU model downloads
- `phase5-custom-nodes.md` - ComfyUI custom node implementations
- `phase6-cpu-offloading.md` - CPU offloading configuration guide

Located at: `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/hearmeman-all-models-pre/`
