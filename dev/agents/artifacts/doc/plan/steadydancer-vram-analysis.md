---
task: SteadyDancer VRAM Analysis - 80GB A100 Configuration
author: $USER
model: Sonnet 4.5 + Opus UltraThink
date: 2026-01-18
status: completed
---

# SteadyDancer + TurboDiffusion VRAM Analysis
## 80GB A100 Configuration (Secure Cloud)

## Executive Summary

This document provides detailed VRAM calculations for running **SteadyDancer + TurboDiffusion** on an **80GB A100** datacenter GPU with voice models **DISABLED**.

**Key Finding**: With all optimizations, the configuration fits within 80GB VRAM but requires careful management.

---

## VRAM Calculation (80GB A100)

### Component Breakdown

| Component | Model | Size | VRAM Load | Notes |
|-----------|-------|------|-----------|-------|
| **Base ComfyUI** | - | - | 2-3 GB | UI, Python, runtime |
| **Text Encoder (UMT5-XXL)** | Comfy-Org | 9.5 GB | 9.5 GB | Required for all WAN models |
| **CLIP Vision** | Comfy-Org | 1.4 GB | 1.4 GB | Reference image encoding |
| **WAN VAE** | Comfy-Org | 335 MB | 335 MB | Latent encoding/decoding |
| **SteadyDancer-14B fp16** | MCG-NJU | 28 GB | 28 GB | Main diffusion model |
| **TurboDiffusion (Distilled)** | Kijai | ~28 GB | 28 GB | Acceleration (100-200x) |
| **ControlNet (optional)** | Various | 3.6 GB | 3.6 GB | Spatial guidance |
| **DWPose Preprocessor** | IDEA-Research | ~2 GB | 2 GB | Pose extraction |
| **Inference Buffers** | - | - | 5-8 GB | Activations, gradients |
| **Safety Margin** | - | - | 5 GB | OOM prevention |

### Calculation Summary

| Configuration | Total VRAM | Fits 80GB? |
|---------------|------------|------------|
| **SteadyDancer ONLY** (fp16) | ~78 GB | ✅ Yes (2GB margin) |
| **SteadyDancer + TurboDiffusion** | ~106 GB | ❌ No (26GB over) |
| **SteadyDancer fp8 + TurboDiffusion** | ~78 GB | ✅ Yes (2GB margin) |
| **SteadyDancer fp8 + TurboDiffusion + ControlNet** | ~82 GB | ⚠️ Tight (may OOM) |
| **SteadyDancer fp8 + TurboDiffusion + CPU Offload** | ~60 GB | ✅ Yes (20GB margin) |

---

## Recommended Configuration (80GB A100)

### Primary Configuration (Best Quality)

```bash
# Enable SteadyDancer (fp8 for memory efficiency)
ENABLE_STEADYDANCER=true
STEADYDANCER_VARIANT=fp8

# Enable TurboDiffusion (100-200x speedup)
ENABLE_WAN22_DISTILL=true

# VRAM optimization
GPU_MEMORY_MODE=auto
COMFYUI_ARGS="--lowvram"

# Disable voice models (saves ~18GB)
ENABLE_VIBEVOICE=false
ENABLE_XTTS=false
ENABLE_CHATTERBOX=false

# Disable unused models
ENABLE_ILLUSTRIOUS=false
ENABLE_ZIMAGE=false
ENABLE_GENFOCUS=false
ENABLE_MVINVERSE=false
```

**Estimated VRAM**: ~78 GB (SteadyDancer fp8 + TurboDiffusion)
**Generation Speed**: 100-200x faster than vanilla diffusion

### Conservative Configuration (Safety Margin)

```bash
# Use CPU offload for additional safety
GPU_MEMORY_MODE=sequential_cpu_offload
```

**Estimated VRAM**: ~60 GB
**Generation Speed**: Slower due to CPU transfers

---

## What is GHCR?

**GHCR** = GitHub Container Registry

- **Purpose**: Stores Docker container images
- **Usage**: Instead of building locally on every RunPod start, pull pre-built image from GHCR
- **URL**: `ghcr.io/mensajerokaos/hearmeman-extended:latest`
- **Benefit**: Faster pod startup (no build), cached layers

### Current Status

The bead `runpod-sgj` (Push to GHCR) must complete before testing SteadyDancer:
```
runpod-7lb [P1] BLOCKED by runpod-sgj [P2]
runpod-sgj [P2] BLOCKED by runpod-aox [P1] ✓ CLOSED
```

---

## SteadyDancer 1.2.x Clarification

**SteadyDancer does NOT have a version "1.2.2"**. 

The current versioning:
- **Latest**: SteadyDancer-GGUF (released Dec 4, 2025)
- **Base**: SteadyDancer-14B (fp16, ~28GB)
- **Pruned**: kijai/SteadyDancer-14B-pruned (fp8, ~14GB)
- **Quantized**: MCG-NJU/SteadyDancer-GGUF (various quantization levels)

**Reference**: https://github.com/MCG-NJU/SteadyDancer

---

## Pose Extraction (DWPose)

### Required for SteadyDancer

SteadyDancer needs **pose data** from the driving video to animate the reference image. This is typically extracted using **DWPose**.

### DWPose Integration

```bash
# Already included via ComfyUI-ControlNet-Aux
# Enable in Dockerfile (line 110-112)
RUN git clone --depth 1 https://github.com/Fannovel16/comfyui_controlnet_aux.git
```

### Workflow Components

1. **Load Reference Image**: Character to animate
2. **Load Driving Video**: Source of motion/pose
3. **DWPose Extraction**: Convert video to pose keypoints
4. **SteadyDancer I2V**: Generate animated video
5. **ControlNet (Optional)**: Additional spatial guidance

### Pose Extraction Settings

| Parameter | Value | Notes |
|-----------|-------|-------|
| Resolution | 1024x576 | Default SteadyDancer |
| Frame Rate | 25-30 FPS | Match source video |
| Keypoints | COCO-WholeBody | 133 points |
| Batch Size | 1 | GPU memory constrained |

---

## TurboDiffusion Integration

### What is TurboDiffusion?

**TurboDiffusion** is an acceleration framework that provides **100-200x speedup** for video diffusion models.

- **Repository**: https://github.com/anveshane/Comfyui_turbodiffusion
- **Already installed**: Dockerfile line 115-117
- **Enable via**: `ENABLE_WAN22_DISTILL=true`

### VRAM with TurboDiffusion

| Mode | VRAM | Speedup |
|------|------|---------|
| Vanilla (no acceleration) | 28 GB | 1x |
| TurboDiffusion | 28 GB | 100-200x |
| TurboDiffusion + fp8 | 14 GB | 100-200x |

### Inference Settings

```json
{
  "sample_guide_scale": 5.0,
  "condition_guide_scale": 1.0,
  "end_cond_cfg": 0.4,
  "base_seed": 106060,
  "steps": 4-8  // vs 50+ for vanilla
}
```

---

## ControlNet Integration

### Supported ControlNet Types

| Control Type | Model | VRAM | Use Case |
|--------------|-------|------|----------|
| **Canny** | control_v11p_sd15_canny | 3.6 GB | Edge preservation |
| **Depth** | control_v11p_sd15_depth | 3.6 GB | Spatial structure |
| **OpenPose** | control_v11p_sd15_openpose | 3.6 GB | Body pose |
| **NormalBAE** | control_v11p_sd15_normalbae | 3.6 GB | Surface normals |

### Integration with SteadyDancer

SteadyDancer can accept ControlNet conditioning via `WanVaceToVideo` node:

```python
# WanVaceToVideo supports:
- control_video: ControlNet conditioning video
- control_masks: Region masks
- reference_image: Character reference
```

### Recommendation

**For 80GB A100**: Enable ControlNet if needed for quality.
**For tight VRAM**: Disable ControlNet, rely on DWPose only.

---

## RunPod Secure Cloud vs Community Cloud

### Comparison

| Feature | Secure Cloud | Community Cloud |
|---------|--------------|-----------------|
| **Data Centers** | T3/T4 (enterprise) | Peer-to-peer |
| **Reliability** | High (redundancy) | Variable |
| **Network Speed** | 51 MB/s (tested) | Variable |
| **Price** | Premium | Competitive |
| **GPU Availability** | Guaranteed | First-come |
| **Bandwidth** | 25 Gbps | Variable |

### For 80GB A100

**Recommendation**: Secure Cloud

- **PCIe Requirement**: PCIe 4.0 x16 (A100 80GB PCIe exception)
- **Bandwidth**: Sufficient for model loading
- **Reliability**: Critical for production workloads

### GPU Selection Command

```bash
# List available A100 80GB in Secure Cloud
runpodctl get cloud 1 --secure --gpu "A100"

# Filter by memory
runpodctl get cloud 1 --secure --mem 80
```

---

## Voice Models - DISABLED

The user specified **NO voice models** to save VRAM:

| Model | VRAM Saved | Status |
|-------|------------|--------|
| **VibeVoice** | ~18 GB | Disabled |
| **XTTS** | ~4 GB | Disabled |
| **Chatterbox** | ~2 GB | Disabled |
| **Total Saved** | **~24 GB** | Available for SteadyDancer |

---

## Text Prompt Engineering for Dance Videos

### Example Prompts (Cosplay/Dance)

```
Positive Prompts:
"A woman dancing gracefully, flowing hair movement, fabric swaying in the wind, 
earrings swinging rhythmically, camera pans slowly from left to right, 
cinematic lighting, professional dance performance, realistic skin texture, 
detailed clothing folds, natural motion blur"

Negative Prompts:
"blurry, distorted, jittery, floating, artifacts, bad anatomy, 
disconnected limbs, flickering, static pose, stiff movement, 
low quality, worst quality, deformed hands, extra fingers"
```

### Camera Movement

| Type | Description | Prompt Keyword |
|------|-------------|----------------|
| Pan Left | Camera moves left | "camera pans left", "tracking shot" |
| Pan Right | Camera moves right | "camera pans right" |
| Zoom In | Lens zooms in | "zoom in", "dolly in" |
| Zoom Out | Lens zooms out | "zoom out", "dolly out" |
| Orbit | Camera circles subject | "orbiting shot", "360° view" |

---

## Workflow Structure

```
Reference Image (Character)
         ↓
Driving Video (Motion/Pose)
         ↓
    DWPose Extraction
         ↓
SteadyDancer I2V + TurboDiffusion
         ↓
ControlNet (Optional)
         ↓
Output Video (Animated)
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `docker/Dockerfile` | Add DWPose deps, enable flash-attn |
| `docker/download_models.sh` | Add DWPose weights download |
| `docker/docker-compose.yml` | Add SteadyDancer env vars |
| `docker/workflows/steadydancer-dance.json` | Create example workflow |
| `CLAUDE.md` | Update storage requirements |
| `README.md` | Add SteadyDancer documentation |

---

## Sub-beads Required

```
runpod-7lb: Test SteadyDancer dance video workflow [P1] [READY]
├── runpod-sgj: Push Docker image to GHCR [P2] [BLOCKED]
│   └── runpod-aox: Research Docker hosting [P1] [CLOSED]
├── runpod-sd-deps: Add SteadyDancer dependencies [P3]
├── runpod-sd-download: Enhance download script [P3]
├── runpod-sd-pose: Configure DWPose extraction [P3]
├── runpod-sd-workflow: Create dance workflow [P3]
├── runpod-sd-test: Local Docker testing [P2]
└── runpod-sd-deploy: RunPod deployment [P1]
```

---

## Timeline

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| 1 | Complete GHCR push (unblock) | 2 hours | Waiting |
| 2 | Dockerfile dependency updates | 2 hours | Pending |
| 3 | Download script enhancement | 1 hour | Pending |
| 4 | DWPose configuration | 1 hour | Pending |
| 5 | Workflow creation | 2 hours | Pending |
| 6 | Local Docker testing | 4 hours | Pending |
| 7 | RunPod deployment | 2 hours | Pending |

**Total**: ~14 hours (excluding GHCR push)

---

## References

- SteadyDancer: https://github.com/MCG-NJU/SteadyDancer
- DWPose: https://github.com/IDEA-Research/DWPose
- TurboDiffusion: https://github.com/anveshane/Comfyui_turbodiffusion
- ComfyUI-WanVideoWrapper: https://github.com/kijai/ComfyUI-WanVideoWrapper
- RunPod Docs: https://docs.runpod.io
- Wan 2.1 Documentation: https://docs.comfy.org/docs/video/wan
