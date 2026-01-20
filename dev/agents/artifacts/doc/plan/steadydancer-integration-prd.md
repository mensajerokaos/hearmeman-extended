---
task: Create PRD for SteadyDancer integration into hearmeaman-extended RunPod template
author: $USER
model: Sonnet 4.5 + Opus UltraThink
date: 2026-01-18
status: updated
bead: runpod-7lb
last_updated: 2026-01-18
update_reason: Added TurboDiffusion research findings, updated cost analysis, VRAM calculations
---

# SteadyDancer Integration PRD
## hearmeaman-extended RunPod Template Enhancement

**Version**: 1.1
**Date**: 2026-01-18
**Status**: Draft
**Bead**: runpod-7lb

---

## 1 Executive Summary

### 1.1 Overview

SteadyDancer is a state-of-the-art human image animation framework developed by the Multimedia Computing Group at Nanjing University (MCG-NJU). It focuses on first-frame preservation and temporal coherence for dance video generation, addressing critical issues like identity drift that plague existing Reference-to-Video approaches. This PRD outlines the integration of SteadyDancer into the hearmeaman-extended RunPod template, adding dance video generation capabilities to the existing video/audio generation stack.

### 1.2 Key Objectives

1. **Enable dance video generation** via ComfyUI interface on RunPod
2. **Optimize for datacenter GPUs** (80GB A100) using TurboDiffusion acceleration
3. **Integrate with existing workflow system** (WAN 2.1, VibeVoice, SCAIL)
4. **Provide production-ready deployment** with on-demand model downloads
5. **Achieve 100-200x speedup** via TurboDiffusion distillation
6. **Test workflow functionality** with local Docker validation

### 1.3 Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Workflow execution | 0 validation errors | ComfyUI prompt queue |
| Generation time (Turbo) | < 30 sec (80GB A100) | TurboDiffusion acceleration |
| Generation time (vanilla) | < 5 min (80GB A100) | Baseline comparison |
| Model download | < 30 min (50 MB/s) | download_models.sh execution |
| VRAM usage | < 65GB peak (80GB A100) | nvidia-smi monitoring |
| Pod startup | < 5 min (cached) | Container restart test |
| Speedup with TurboDiffusion | 100-200x | Wan-2.1-T2V-14B-720P: 4767s → 24s (198x) |
| Monthly cost | $432-857 | A100 80GB on-demand/spot |

### 1.4 Scope

**In Scope**:
- ComfyUI node integration via ComfyUI-WanVideoWrapper
- TurboDiffusion integration for 100-200x acceleration
- Model download script integration
- Environment variable configuration
- Example workflow creation with TurboDiffusion
- Docker build optimization
- Local Docker testing

**Out of Scope**:
- Pose estimation preprocessing pipeline (separate deployment)
- Multi-GPU distributed inference (not supported by ComfyUI)
- Custom pose extraction workflow (future enhancement)
- Direct GitHub Actions deployment (use existing workflow)

---

## 2 Technical Requirements

### 2.1 Model Specifications

#### 2.1.1 SteadyDancer-14B Model

| Attribute | Value | Notes |
|-----------|-------|-------|
| **Model ID** | MCG-NJU/SteadyDancer-14B | HuggingFace repository |
| **Parameters** | 14B | Based on Wan2.1-I2V-14B-480P |
| **License** | Apache-2.0 | Commercial use allowed |
| **Task Type** | Image-to-Video (I2V) | Human image animation |
| **Base Model** | Wan-AI/Wan2.1-I2V-14B-480P | Foundation model |

#### 2.1.2 Storage Requirements

| Variant | Size | VRAM (Full Load) | VRAM (CPU Offload) |
|---------|------|------------------|-------------------|
| **fp16** | ~28 GB | 32 GB+ required | 16 GB+ |
| **fp8** | ~14 GB | 16 GB+ required | 8 GB+ |
| **GGUF Q4_K_M** | ~7 GB | 8 GB+ required | 4 GB+ |

**Recommendation**: Default to fp16 for 80GB A100 (optimal quality with TurboDiffusion)

#### 2.1.3 Model Download Sources

```bash
# Primary: HuggingFace (recommended)
huggingface-cli download MCG-NJU/SteadyDancer-14B --local-dir ./SteadyDancer-14B

# Quantized alternatives
MCG-NJU/SteadyDancer-GGUF  # GGUF quantized versions
kijai/SteadyDancer-14B-pruned  # Pruned fp16/fp8 variants
```

#### 2.1.4 Shared Dependencies (WAN 2.1)

SteadyDancer shares components with existing WAN 2.1 models:

| Component | Size | Shared | Path |
|-----------|------|--------|------|
| **UMT5-XXL Text Encoder** | 9.5 GB | Yes | text_encoders/ |
| **CLIP Vision** | 1.4 GB | Yes | clip_vision/ |
| **WAN VAE** | 335 MB | Yes | vae/ |

**Total incremental storage**: ~28-42 GB (fp16/fp16+Turbo)

### 2.2 TurboDiffusion Integration

#### 2.2.1 What is TurboDiffusion?

**TurboDiffusion** is an acceleration framework that provides **100-200x speedup** for video diffusion models.

- **Repository**: https://github.com/anveshane/Comfyui_turbodiffusion
- **Already installed**: Dockerfile line 115-117
- **Enable via**: `ENABLE_WAN22_DISTILL=true`

#### 2.2.2 TurboDiffusion Benchmarks (CONFIRMED Dec 2025)

| Model | Base Time | Turbo Time | Speedup | Status |
|-------|-----------|------------|---------|--------|
| Wan-2.1-T2V-14B-720P | 4767s (79 min) | 24s | **198x** | ✅ Confirmed |
| Wan-2.1-T2V-14B-480P | 1676s (28 min) | 9.9s | **169x** | ✅ Confirmed |
| Wan-2.2-I2V-14B-720P | 4549s (76 min) | 38s | **120x** | ✅ Confirmed |

**Source**: TurboDiffusion GitHub (Dec 2025) - Works with WAN 2.1 AND 2.2

#### 2.2.3 TurboDiffusion VRAM Requirements

| Mode | VRAM | Speedup | Notes |
|------|------|---------|-------|
| Vanilla (no acceleration) | 28 GB | 1x | 50+ steps |
| TurboDiffusion + fp16 | 28 GB | 100-200x | 4-8 steps |
| TurboDiffusion + fp8 | 14 GB | 100-200x | 4-8 steps |

**Inference Settings**:
```json
{
  "sample_guide_scale": 5.0,
  "condition_guide_scale": 1.0,
  "end_cond_cfg": 0.4,
  "base_seed": 106060,
  "steps": 4-8  // vs 50+ for vanilla
}
```

### 2.3 ComfyUI Node Integration

#### 2.3.1 Required Nodes (ComfyUI-WanVideoWrapper)

SteadyDancer requires the following nodes from ComfyUI-WanVideoWrapper:

```json
{
  "required_nodes": [
    "Wan_GlobalAveragePooling",
    "Wan_DreamPanel",
    "Wan_ReferenceAttention",
    "Wan_CrossFrameAttention"
  ],
  "wrapper_repo": "https://github.com/kijai/ComfyUI-WanVideoWrapper.git",
  "status": "already_installed"
}
```

**Note**: ComfyUI-WanVideoWrapper is already installed in the Dockerfile (line 120). No additional node installation required.

#### 2.3.2 Workflow Requirements

SteadyDancer workflows require:

1. **Reference Image**: Source character image for animation
2. **Driving Video/Pose**: Motion reference (DWPose extracted)
3. **Text Prompt**: Optional description of desired motion
4. **Conditioning Frames**: Positive and negative pose sequences

### 2.4 Dependencies Analysis

#### 2.4.1 Python Dependencies

SteadyDancer requires specific PyTorch versions and pose estimation libraries:

```python
# Core PyTorch stack (CRITICAL: version-specific)
torch==2.5.1
torchvision==0.20.1
torchaudio==2.5.1

# Attention mechanisms
flash-attn==2.7.4.post1
xformers==0.0.29.post1
xfuser[diffusers,flash-attn]

# Video processing
moviepy
decord

# Pose estimation (MMSelfCom workstack)
mmengine
mmcv==2.1.0
mmdet>=3.1.0
mmpose
```

#### 2.4.2 Compatibility Assessment

| Dependency | Current Dockerfile | Required | Action |
|------------|-------------------|----------|--------|
| torch | 2.8.0 (cuda12.8) | 2.5.1 | **Pinning required** |
| torchvision | Latest | 0.20.1 | **Pinning required** |
| mmcv | Latest | 2.1.0 | **Add specific version** |
| flash-attn | Disabled (line 181) | 2.7.4.post1 | **Enable required** |
| xformers | Latest | 0.0.29.post1 | **Pinning recommended** |

**Risk**: Version mismatches may cause runtime errors. Flash-attn is currently disabled due to ABI compatibility issues with kornia.

### 2.5 Environment Variables

```bash
# Core toggle
ENABLE_STEADYDANCER=true|false  # Default: false

# Model configuration
STEADYDANCER_VARIANT=fp8|fp16|gguf  # Default: fp16 (80GB A100)

# TurboDiffusion acceleration
ENABLE_WAN22_DISTILL=true|false  # Default: false
TURBO_STEPS=4  # Inference steps (4-8 vs 50+)
TURBO_GUIDE_SCALE=5.0
TURBO_CONDITION_GUIDE=1.0
TURBO_END_CFG=0.4

# Inference settings (optional overrides)
STEADYDANCER_GUIDE_SCALE=5.0
STEADYDANCER_CONDITION_GUIDE=1.0
STEADYDANCER_END_CFG=0.4
STEADYDANCER_SEED=106060

# VRAM optimization
GPU_MEMORY_MODE=auto|sequential_cpu_offload|model_cpu_offload
```

### 2.6 GPU Tier Classification

| Tier | VRAM | Configuration | TurboDiffusion |
|------|------|---------------|----------------|
| **Consumer** | 8-16 GB | GGUF Q4_K_M + sequential_cpu_offload | Not recommended |
| **Prosumer** | 16-24 GB | fp8 + model_cpu_offload | May work (tight) |
| **Datacenter** | 32-48 GB | fp16 + model_cpu_offload | Recommended |
| **Datacenter** | 80 GB A100 | fp16 + TurboDiffusion | **Optimal** |

---

## 3 VRAM Analysis

### 3.1 VRAM Calculation (80GB A100 + TurboDiffusion)

#### 3.1.1 Component Breakdown

| Component | Model | Size | VRAM Load | Notes |
|-----------|-------|------|-----------|-------|
| **Base ComfyUI** | - | - | 2-3 GB | UI, Python, runtime |
| **Text Encoder (UMT5-XXL)** | Comfy-Org | 9.5 GB | 9.5 GB | Required for all WAN models |
| **CLIP Vision** | Comfy-Org | 1.4 GB | 1.4 GB | Reference image encoding |
| **WAN VAE** | Comfy-Org | 335 MB | 335 MB | Latent encoding/decoding |
| **SteadyDancer-14B fp16** | MCG-NJU | 28 GB | 28 GB | Main diffusion model |
| **TurboDiffusion (Distilled)** | Kijai | ~28 GB | 28 GB | Acceleration (100-200x) |
| **DWPose Preprocessor** | IDEA-Research | ~2 GB | 2 GB | Pose extraction |
| **Inference Buffers** | - | - | 5-8 GB | Activations, gradients |
| **Safety Margin** | - | - | 5 GB | OOM prevention |

#### 3.1.2 Calculation Summary

| Configuration | Total VRAM | Fits 80GB? | Notes |
|---------------|------------|------------|-------|
| **SteadyDancer ONLY** (fp16) | ~78 GB | ✅ Yes (2GB margin) | No TurboDiffusion |
| **SteadyDancer + TurboDiffusion** (fp16) | ~106 GB | ❌ No (26GB over) | Too much VRAM |
| **SteadyDancer fp8 + TurboDiffusion** | ~78 GB | ✅ Yes (2GB margin) | Optimal |
| **SteadyDancer fp8 + TurboDiffusion + CPU Offload** | ~60 GB | ✅ Yes (20GB margin) | Conservative |

### 3.2 Voice Models - VRAM Savings

The user specified **NO voice models** to save VRAM for SteadyDancer:

| Model | VRAM Saved | Status |
|-------|------------|--------|
| **VibeVoice** | ~18 GB | Disabled |
| **XTTS** | ~4 GB | Disabled |
| **Chatterbox** | ~2 GB | Disabled |
| **Total Saved** | **~24 GB** | Available for SteadyDancer |

### 3.3 Multi-GPU Considerations

**IMPORTANT**: ComfyUI does NOT support single workflow parallelization across multiple GPUs.

| Capability | Status | Notes |
|------------|--------|-------|
| Single workflow, multiple GPUs | ❌ NO | No native support |
| Multiple instances (batch) | ✅ YES | Run parallel for throughput |
| xDiT framework | ✅ YES | For DiT models (Flux, not SteadyDancer) |
| ComfyUI-Distributed | ✅ YES | Multi-machine support |

**Recommendation**: Single A100 80GB is optimal for SteadyDancer + TurboDiffusion.

---

## 4 Implementation Plan

### 4.1 Phase 1: Dockerfile Updates

#### 4.1.1 Dependency Layer Updates

**Location**: Layer 4 (Additional Dependencies), Dockerfile lines 148-177

**Current State**:
```dockerfile
RUN pip install --no-cache-dir \
    huggingface_hub \
    accelerate \
    # ... existing packages ...
```

**Required Changes**:
```dockerfile
# SteadyDancer dependencies (add before existing pip install)
# CRITICAL: Install in specific order to avoid ABI conflicts
RUN pip install --no-cache-dir \
    torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu124 \
    || echo "[Note] PyTorch 2.5.1 install failed, using default"

# Pose estimation dependencies
RUN pip install --no-cache-dir \
    mmengine \
    mmcv==2.1.0 \
    mmdet>=3.1.0 \
    mmpose \
    || echo "[Note] MMPose stack install failed"

# Flash Attention (retry on failure)
RUN pip install --no-cache-dir flash_attn==2.7.4.post1 \
    || echo "[Note] flash_attn install failed, will retry"
```

#### 4.1.2 Model Directory Update

**Location**: Layer 5 (Scripts), Dockerfile line 201

**Current**:
```dockerfile
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,...}
```

**Update**:
```dockerfile
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision,genfocus,qwen,mvinverse,flashportrait,storymem,infcam,steadydancer}
```

### 4.2 Phase 2: Download Script Enhancement

#### 4.2.1 Existing Integration (Lines 323-328)

The download_models.sh already contains a basic SteadyDancer section:

```bash
if [ "${ENABLE_STEADYDANCER:-false}" = "true" ]; then
    echo "[SteadyDancer] Downloading model..."
    hf_download "MCG-NJU/SteadyDancer-14B" "Wan21_SteadyDancer_fp16.safetensors" "$MODELS_DIR/diffusion_models/Wan21_SteadyDancer_fp16.safetensors"
fi
```

#### 4.2.2 Enhanced Download Script

**Required Updates**:

```bash
# ============================================
# SteadyDancer (Human Image Animation)
# VRAM: 14-28GB | Size: 14-28GB
# ============================================
if [ "${ENABLE_STEADYDANCER:-false}" = "true" ]; then
    echo ""
    echo "[SteadyDancer] Downloading model (~14-28GB)..."

    STEADYDANCER_VARIANT="${STEADYDANCER_VARIANT:-fp16}"

    case "$STEADYDANCER_VARIANT" in
        "fp16")
            echo "  [Info] Downloading fp16 variant (~28GB)..."
            hf_download "MCG-NJU/SteadyDancer-14B" \
                "Wan21_SteadyDancer_fp16.safetensors" \
                "$MODELS_DIR/diffusion_models/Wan21_SteadyDancer_fp16.safetensors" \
                "28GB"
            ;;
        "fp8")
            echo "  [Info] Downloading fp8 variant (~14GB)..."
            hf_download "kijai/SteadyDancer-14B-pruned" \
                "Wan21_SteadyDancer_fp8.safetensors" \
                "$MODELS_DIR/diffusion_models/Wan21_SteadyDancer_fp8.safetensors" \
                "14GB"
            ;;
        "gguf")
            echo "  [Info] Downloading GGUF quantized variant..."
            mkdir -p "$MODELS_DIR/steadydancer"
            python3 -c "
from huggingface_hub import hf_hub_download
import os

GGUF_FILE='steadydancer-14B-q4_k_m.gguf'
hf_hub_download(
    repo_id='MCG-NJU/SteadyDancer-GGUF',
    filename=GGUF_FILE,
    local_dir='$MODELS_DIR/steadydancer',
    local_dir_use_symlinks=False
)
print('  [OK] GGUF model downloaded')
" 2>&1 || echo "  [Error] GGUF download failed"
            ;;
    esac

    # Download shared dependencies (WAN 2.1)
    echo "  [Info] Ensuring shared dependencies..."

    # Text encoder (9.5GB - skip if exists)
    if [ ! -f "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" ]; then
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
            "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
            "9.5GB"
    fi

    # CLIP Vision (1.4GB - skip if exists)
    if [ ! -f "$MODELS_DIR/clip_vision/clip_vision_h.safetensors" ]; then
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/clip_vision/clip_vision_h.safetensors" \
            "$MODELS_DIR/clip_vision/clip_vision_h.safetensors" \
            "1.4GB"
    fi

    # VAE (335MB - skip if exists)
    if [ ! -f "$MODELS_DIR/vae/wan_2.1_vae.safetensors" ]; then
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/vae/wan_2.1_vae.safetensors" \
            "$MODELS_DIR/vae/wan_2.1_vae.safetensors" \
            "335MB"
    fi

    echo "[SteadyDancer] Download complete"
fi

# ============================================
# TurboDiffusion (Distilled Model)
# VRAM: ~28GB | Size: ~28GB
# Enables 100-200x speedup
# ============================================
if [ "${ENABLE_WAN22_DISTILL:-false}" = "true" ]; then
    echo ""
    echo "[TurboDiffusion] Downloading distilled model (~28GB)..."

    hf_download "kijai/wan-2.1-turbodiffusion" \
        "wan_2.1_turbodiffusion.safetensors" \
        "$MODELS_DIR/diffusion_models/wan_2.1_turbodiffusion.safetensors" \
        "28GB"

    echo "[TurboDiffusion] Download complete"
fi
```

### 4.3 Phase 3: Docker Compose Configuration

#### 4.3.1 Environment Variable Update

**Location**: docker-compose.yml lines 37-67

**Add after ENABLE_STORYMEM**:
```yaml
# Tier 3: Datacenter GPU (48-80GB A100/H100)
- ENABLE_INFCAM=false
- ENABLE_STEADYDANCER=false
- STEADYDANCER_VARIANT=fp16
- STEADYDANCER_GUIDE_SCALE=5.0
- STEADYDANCER_CONDITION_GUIDE=1.0
- STEADYDANCER_END_CFG=0.4

# TurboDiffusion (100-200x acceleration)
- ENABLE_WAN22_DISTILL=false
```

### 4.4 Phase 4: Example Workflow Creation

#### 4.4.1 Workflow Directory

**Location**: docker/workflows/steadydancer-dance.json

#### 4.4.2 Workflow Structure (with TurboDiffusion)

```json
{
  "name": "SteadyDancer Dance Animation + TurboDiffusion",
  "nodes": [
    {
      "id": "load_image_reference",
      "class_type": "LoadImage",
      "inputs": {"image": "reference_character.png"}
    },
    {
      "id": "load_image_driving",
      "class_type": "LoadImage",
      "inputs": {"image": "driving_pose_001.png"}
    },
    {
      "id": "load_diffusion_model",
      "class_type": "Wan_LoadDiffusionModel",
      "inputs": {
        "model_name": "Wan21_SteadyDancer_fp16.safetensors",
        "weight_dtype": "fp16"
      }
    },
    {
      "id": "load_vae",
      "class_type": "Wan_LoadVAE",
      "inputs": {"vae_name": "wan_2.1_vae.safetensors"}
    },
    {
      "id": "load_turbo",
      "class_type": "Wan_LoadTurbo",
      "inputs": {
        "model_name": "wan_2.1_turbodiffusion.safetensors",
        "steps": 4,
        "guide_scale": 5.0,
        "condition_guide_scale": 1.0,
        "end_cond_cfg": 0.4
      }
    },
    {
      "id": "reference_attention",
      "class_type": "Wan_ReferenceAttention",
      "inputs": {
        "reference_image": "load_image_reference",
        "conditioning_strength": 0.8
      }
    },
    {
      "id": "cross_frame_attention",
      "class_type": "Wan_CrossFrameAttention",
      "inputs": {
        "driving_video": "load_image_driving",
        "frame_count": 16
      }
    },
    {
      "id": "ksampler",
      "class_type": "Wan_KSampler",
      "inputs": {
        "steps": 4,
        "cfg": 5.0,
        "sampler_name": "euler",
        "scheduler": "simple",
        "denoise": 1.0
      }
    },
    {
      "id": "save_video",
      "class_type": "SaveVideo",
      "inputs": {"filename_prefix": "steadydancer_dance_turbo"}
    }
  ],
  "edges": [
    ["load_image_reference", "reference_attention"],
    ["load_image_driving", "cross_frame_attention"],
    ["reference_attention", "ksampler"],
    ["cross_frame_attention", "ksampler"],
    ["ksampler", "save_video"]
  ]
}
```

### 4.5 Phase 5: Build-time Model Download (Optional)

#### 4.5.1 Dockerfile Build Arguments

**Add after line 209**:
```dockerfile
ARG BAKE_STEADYDANCER=false
ARG STEADYDANCER_VARIANT=fp16
ARG BAKE_TURBO=false
```

#### 4.5.2 Build-time Download Section

**Add after line 250**:
```dockerfile
# SteadyDancer Models (~14-28GB)
RUN if [ "$BAKE_STEADYDANCER" = "true" ]; then \
    echo "[BUILD] Downloading SteadyDancer ${STEADYDANCER_VARIANT} model..." && \
    case "$STEADYDANCER_VARIANT" in
        "fp16")
            wget -q --show-progress -O /workspace/ComfyUI/models/diffusion_models/Wan21_SteadyDancer_fp16.safetensors \
                "https://huggingface.co/MCG-NJU/SteadyDancer-14B/resolve/main/Wan21_SteadyDancer_fp16.safetensors" && \
            echo "[BUILD] SteadyDancer fp16 downloaded (28GB)" ;;
        "fp8")
            wget -q --show-progress -O /workspace/ComfyUI/models/diffusion_models/Wan21_SteadyDancer_fp8.safetensors \
                "https://huggingface.co/kijai/SteadyDancer-14B-pruned/resolve/main/Wan21_SteadyDancer_fp8.safetensors" && \
            echo "[BUILD] SteadyDancer fp8 downloaded (14GB)" ;;
    esac && \
    echo "[BUILD] SteadyDancer models downloaded" || \
    echo "[BUILD] SteadyDancer download skipped or failed"; \
    fi

# TurboDiffusion Model (~28GB)
RUN if [ "$BAKE_TURBO" = "true" ]; then \
    echo "[BUILD] Downloading TurboDiffusion model (~28GB)..." && \
    wget -q --show-progress -O /workspace/ComfyUI/models/diffusion_models/wan_2.1_turbodiffusion.safetensors \
        "https://huggingface.co/kijai/wan-2.1-turbodiffusion/resolve/main/wan_2.1_turbodiffusion.safetensors" && \
    echo "[BUILD] TurboDiffusion downloaded (28GB)" || \
    echo "[BUILD] TurboDiffusion download skipped or failed"; \
    fi
```

### 4.6 Phase 6: Documentation Update

#### 4.6.1 CLAUDE.md Update

**Add to Storage Requirements table** (after SCAIL entry):

```markdown
| **SteadyDancer** | ~33GB | Dance video generation |
| **TurboDiffusion** | ~28GB | 100-200x acceleration (optional) |
```

**Add to Environment Variables table**:

```markdown
| `ENABLE_STEADYDANCER` | false | false/true | Dance video generation |
| `STEADYDANCER_VARIANT` | fp16 | fp8/fp16/gguf | Model quantization |
| `ENABLE_WAN22_DISTILL` | false | false/true | Enable TurboDiffusion acceleration |
```

#### 4.6.2 README.md Update

**Add to Feature List**:

```markdown
### SteadyDancer (Dance Video Generation)
- **Model**: MCG-NJU/SteadyDancer-14B
- **VRAM**: 14-28GB (configurable via STEADYDANCER_VARIANT)
- **Task**: Human image animation with first-frame preservation
- **Enable**: `ENABLE_STEADYDANCER=true`
- **Reference**: [SteadyDancer Paper](https://arxiv.org/abs/2511.19320)

### TurboDiffusion (100-200x Speedup)
- **Acceleration**: 100-200x faster video generation
- **Models**: Wan-2.1-T2V-14B-720P (4767s → 24s), Wan-2.1-T2V-14B-480P (1676s → 9.9s)
- **Enable**: `ENABLE_WAN22_DISTILL=true`
- **VRAM**: ~28GB additional
- **Reference**: [TurboDiffusion GitHub](https://github.com/anveshane/Comfyui_turbodiffusion)
```

---

## 5 Testing Strategy

### 5.1 Local Docker Testing

#### 5.1.1 Pre-flight Checklist

```bash
# 1. Verify disk space (need 80GB+ free)
df -h /home/oz/projects/2025/oz/12/runpod/models

# 2. Check GPU availability
nvidia-smi

# 3. Stop existing containers
docker compose down

# 4. Clear cache (optional)
docker system prune -af
```

#### 5.1.2 Build Test

```bash
cd /home/oz/projects/2025/oz/12/runpod/docker

# Build with SteadyDancer enabled
docker compose build --build-arg BAKE_STEADYDANCER=false

# Or build-time bake (slower, instant startup)
docker compose build --build-arg BAKE_STEADYDANCER=true \
  --build-arg STEADYDANCER_VARIANT=fp16
```

#### 5.1.3 Runtime Test

```bash
# Start container with environment
ENABLE_STEADYDANCER=true \
STEADYDANCER_VARIANT=fp16 \
ENABLE_WAN22_DISTILL=true \
GPU_MEMORY_MODE=auto \
docker compose up -d

# Monitor startup
docker logs -f hearmeman-extended

# Verify model download (first run)
docker exec hearmeman-extended tail -50 /var/log/download_models.log
```

#### 5.1.4 Workflow Validation

```bash
# 1. Open ComfyUI: http://localhost:8188
# 2. Load: docker/workflows/steadydancer-dance.json
# 3. Queue prompt
# 4. Verify: NO validation errors in ComfyUI console
# 5. Check: Output video in /workspace/ComfyUI/output/
```

### 5.2 VRAM Monitoring

```bash
# Monitor GPU usage during generation
watch -n 1 nvidia-smi

# Check memory mode in container
docker exec hearmeman-extended python -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
print(f'Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
"
```

### 5.3 Performance Benchmarks

| Test Case | GPU | VRAM | Time | Speedup | Status |
|-----------|-----|------|------|---------|--------|
| Vanilla diffusion | A100 80GB | 78 GB | ~80 min | 1x | Baseline |
| TurboDiffusion | A100 80GB | 78 GB | ~24 sec | **200x** | Target |
| CPU offload mode | A100 80GB | 60 GB | ~40 sec | **120x** | Fallback |

### 5.4 RunPod Deployment Test

```bash
# Create test pod
runpodctl create pod \
  --name "steadydancer-turbo-$(date +%H%M)" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA A100 80GB" \
  --containerDiskSize 20 \
  --volumeSize 100 \
  --secureCloud \
  --ports "8188/http" \
  --env "ENABLE_STEADYDANCER=true" \
  --env "STEADYDANCER_VARIANT=fp16" \
  --env "ENABLE_WAN22_DISTILL=true" \
  --env "ENABLE_VIBEVOICE=false" \
  --env "ENABLE_XTTS=false" \
  --env "ENABLE_CHATTERBOX=false"

# Verify model download on first start
# Test workflow execution
# Measure generation time
```

---

## 6 Risks and Mitigations

### 6.1 Technical Risks

| Risk | Severity | Probability | Impact | Mitigation |
|------|----------|-------------|--------|------------|
| **TurboDiffusion VRAM overflow** | High | Medium | OOM crash | Use fp8 variant + CPU offload |
| **Flash-attn ABI conflict** | High | High | Runtime crash | Pin versions, retry on failure |
| **MMCV version mismatch** | Medium | Medium | Pose estimation failure | Install specific versions |
| **VRAM overflow (16GB GPU)** | High | Medium | OOM crash | Not recommended for TurboDiffusion |
| **Model download timeout** | Low | Low | Startup delay | Increase timeout, add resume |
| **Workflow node incompatibility** | Medium | Low | Validation errors | Test with ComfyUI-WanVideoWrapper |

### 6.2 Mitigation Strategies

#### 6.2.1 Dependency Version Pinning

```dockerfile
# Install dependencies in specific order to avoid conflicts
RUN pip install --no-cache-dir \
    torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu124 \
    2>/dev/null || pip install --no-cache-dir \
    torch torchvision torchaudio

# Flash-attn with fallback
RUN pip install --no-cache-dir flash_attn==2.7.4.post1 \
    || echo "[Warn] flash_attn install failed, using xformers"
```

#### 6.2.2 VRAM-safe Defaults (80GB A100)

```bash
# Default configuration for 80GB A100 (optimal)
ENABLE_STEADYDANCER=true
STEADYDANCER_VARIANT=fp16
ENABLE_WAN22_DISTILL=true
GPU_MEMORY_MODE=auto

# Disable voice models to save VRAM
ENABLE_VIBEVOICE=false
ENABLE_XTTS=false
ENABLE_CHATTERBOX=false
```

#### 6.2.3 Download Retry Logic

```bash
# Increase timeout for large model downloads
DOWNLOAD_TIMEOUT="${DOWNLOAD_TIMEOUT:-3600}"  # 1 hour for 28GB model

# Add retry attempts
MAX_RETRIES=3
for attempt in $(seq 1 $MAX_RETRIES); do
    hf_download "MCG-NJU/SteadyDancer-14B" ... && break
    echo "Retry $attempt/$MAX_RETRIES..."
    sleep 10
done
```

### 6.3 Rollback Plan

If SteadyDancer integration causes issues:

1. **Docker build failure**: Revert Dockerfile changes, keep ComfyUI-WanVideoWrapper
2. **Runtime crash**: Disable with `ENABLE_STEADYDANCER=false`
3. **VRAM issues**: Switch to `STEADYDANCER_VARIANT=gguf` + `GPU_MEMORY_MODE=sequential_cpu_offload` + `ENABLE_WAN22_DISTILL=false`
4. **Complete rollback**: Use git revert to previous commit

```bash
# Rollback command
git revert --no-commit <commit-hash>
git commit -m "Rollback: Revert SteadyDancer integration"
```

---

## 7 Timeline and Milestones

### 7.1 Implementation Schedule

| Phase | Task | Duration | Dependencies |
|-------|------|----------|--------------|
| **Phase 1** | Dockerfile updates | 2 hours | None |
| **Phase 2** | Download script enhancement | 1 hour | Phase 1 |
| **Phase 3** | Docker compose config | 30 min | Phase 1 |
| **Phase 4** | Example workflow creation | 2 hours | Phase 1-3 |
| **Phase 5** | Build-time model download | 1 hour | Phase 1 |
| **Phase 6** | Documentation update | 1 hour | All phases |
| **Phase 7** | Local Docker testing | 4 hours | Phase 1-6 |
| **Phase 8** | RunPod deployment test | 2 hours | Phase 7 |

**Total estimated time**: ~14 hours (excluding testing wait times)

### 7.2 Milestone Checklist

- [ ] Dockerfile dependencies pinned (Phase 1)
- [ ] Download script handles fp16/fp8 variants + TurboDiffusion (Phase 2)
- [ ] Docker compose includes SteadyDancer + TurboDiffusion env vars (Phase 3)
- [ ] Example workflow validates without errors (Phase 4)
- [ ] Build-time download works (Phase 5)
- [ ] Documentation updated (Phase 6)
- [ ] Local Docker test passes (Phase 7)
- [ ] RunPod deployment successful (Phase 8)
- [ ] TurboDiffusion 100-200x speedup verified (Phase 8)
- [ ] Bead `runpod-7lb` closed with verification (Phase 8)

---

## 8 Cost Analysis

### 8.1 RunPod Pricing (January 2026)

| GPU | Secure Cloud | Community Cloud | Spot (30-70% off) |
|-----|--------------|-----------------|-------------------|
| **A100 80GB** | $1.39-1.74/hr | $1.19/hr | $0.35-0.83/hr |
| **H100 80GB** | $2.39/hr | $1.99/hr | ~$0.70/hr |
| **RTX 4090** | - | $0.34/hr | ~$0.10/hr |

**Sources**: RunPod pricing page, Northflank, Flexprice

### 8.2 Monthly Cost Projection (A100 80GB)

| Scenario | Rate | Monthly (720 hrs) | Notes |
|----------|------|-------------------|-------|
| On-Demand Secure | $1.50/hr | **$1,080** | Enterprise SLA |
| On-Demand Community | $1.19/hr | **$857** | Best value |
| Spot (50% off) | $0.60/hr | **$432** | Production viable |
| Spot (70% off) | $0.36/hr | **$259** | Batch processing |

**Recommendation**: Spot instances at 50% off ($0.60/hr) for production workloads

### 8.3 Per-Video Cost

| Generation Time | Rate | Cost per Video |
|-----------------|------|----------------|
| 24 sec (Turbo) | $1.50/hr | $0.01 |
| 24 sec (Turbo) | $0.60/hr | $0.004 |
| 3 min (vanilla) | $1.50/hr | $0.075 |
| 3 min (vanilla) | $0.60/hr | $0.03 |

### 8.4 Storage Costs (RunPod)

| Component | Size | Cost/month (100GB @ $0.10/GB) |
|-----------|------|------------------------------|
| SteadyDancer fp16 | 28 GB | $2.80 |
| TurboDiffusion | 28 GB | $2.80 |
| Shared dependencies | 11.2 GB | $1.12 |
| **Total** | **~67 GB** | **$6.70/month** |

### 8.5 Build-time Download (GHCR)

| Model | Download Size | Bandwidth (50 MB/s) | Time |
|-------|---------------|---------------------|------|
| SteadyDancer fp16 | 28 GB | 50 MB/s | ~10 min |
| TurboDiffusion | 28 GB | 50 MB/s | ~10 min |

---

## 9 References

### 9.1 Model Resources

| Resource | URL |
|----------|-----|
| **Model Card** | https://huggingface.co/MCG-NJU/SteadyDancer-14B |
| **Pruned Variants** | https://huggingface.co/kijai/SteadyDancer-14B-pruned |
| **GGUF Quantized** | https://huggingface.co/MCG-NJU/SteadyDancer-GGUF |
| **ModelScope** | https://modelscope.cn/models/MCG-NJU/SteadyDancer-14B |
| **TurboDiffusion** | https://huggingface.co/kijai/wan-2.1-turbodiffusion |

### 9.2 Documentation

| Resource | URL |
|----------|-----|
| **Paper (arXiv)** | https://arxiv.org/abs/2511.19320 |
| **GitHub Repo** | https://github.com/MCG-NJU/SteadyDancer |
| **X-Dance Dataset** | https://huggingface.co/datasets/MCG-NJU/X-Dance |
| **DWPose Weights** | https://huggingface.co/yzd-v/DWPose |
| **TurboDiffusion GitHub** | https://github.com/anveshane/Comfyui_turbodiffusion |

### 9.3 Existing Integration

| Resource | URL |
|----------|-----|
| **ComfyUI-WanVideoWrapper** | https://github.com/kijai/ComfyUI-WanVideoWrapper |
| **Current Dockerfile** | /home/oz/projects/2025/oz/12/runpod/docker/Dockerfile |
| **Current Download Script** | /home/oz/projects/2025/oz/12/runpod/docker/download_models.sh |
| **Current Compose** | /home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml |

---

## 10 Appendix

### 10.1 Complete Dockerfile Changes

See: `docker/Dockerfile.steadydancer-integration` (to be created)

### 10.2 Complete Download Script Changes

See: `docker/download_models.sh.steadydancer-integration` (to be created)

### 10.3 Example Workflow JSON

See: `docker/workflows/steadydancer-dance.json` (to be created)

### 10.4 Test Scripts

See: `docker/scripts/test-steadydancer.sh` (to be created)

### 10.5 Environment Variable Reference

```bash
# Required
ENABLE_STEADYDANCER=true|false

# Optional
STEADYDANCER_VARIANT=fp8|fp16|gguf
STEADYDANCER_GUIDE_SCALE=5.0
STEADYDANCER_CONDITION_GUIDE=1.0
STEADYDANCER_END_CFG=0.4
STEADYDANCER_SEED=106060

# TurboDiffusion (100-200x acceleration)
ENABLE_WAN22_DISTILL=true|false
TURBO_STEPS=4
TURBO_GUIDE_SCALE=5.0
TURBO_CONDITION_GUIDE=1.0
TURBO_END_CFG=0.4
```

---

**Document Version**: 1.1
**Last Updated**: 2026-01-18
**Author**: $USER
**Review Status**: Draft - Pending Implementation
**Update History**: Added TurboDiffusion integration, updated cost analysis, updated VRAM calculations
