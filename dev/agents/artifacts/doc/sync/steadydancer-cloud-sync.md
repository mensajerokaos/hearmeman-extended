---
author: $USER
date: 2026-01-18 08:52
model: Sonnet 4.5 + Opus UltraThink
task: SteadyDancer Integration - Cloud Sync Document
---

# SteadyDancer Integration - Cloud Sync Document

**Date**: 2026-01-18
**Status**: Planning Complete - Ready for Implementation

---

## Key Research Findings (Jan 2026)

### 1. TurboDiffusion Compatibility - CONFIRMED

| Model | Base Time | Turbo Time | Speedup |
|-------|-----------|------------|---------|
| Wan-2.1-T2V-14B-720P | 4767s | 24s | **198x** |
| Wan-2.1-T2V-14B-480P | 1676s | 9.9s | **169x** |
| Wan-2.2-I2V-14B-720P | 4549s | 38s | **120x** |

**Source**: TurboDiffusion GitHub (Dec 2025) - Works with WAN 2.1 AND 2.2

### 2. RunPod Pricing (January 2026)

| GPU | Secure Cloud | Community Cloud | Spot (30-70% off) |
|-----|--------------|-----------------|-------------------|
| **A100 80GB** | $1.39-1.74/hr | $1.19/hr | $0.35-0.83/hr |
| **H100 80GB** | $2.39/hr | $1.99/hr | ~$0.70/hr |
| **RTX 4090** | - | $0.34/hr | ~$0.10/hr |

**Sources**: RunPod pricing page, Northflank, Flexprice

### 3. VRAM Budget (A100 80GB + TurboDiffusion)

| Component | VRAM |
|-----------|------|
| SteadyDancer fp16 | 28 GB |
| TurboDiffusion | 28 GB |
| UMT5-XXL Text Encoder | 9.5 GB |
| CLIP Vision + VAE | 1.7 GB |
| DWPose | 2 GB |
| Buffers | 5 GB |
| **Total** | **~65 GB** |
| **Margin** | **15 GB** |

### 4. Multi-GPU in ComfyUI

| Capability | Status | Notes |
|------------|--------|-------|
| Single workflow, multiple GPUs | ❌ NO | No native support |
| Multiple instances (batch) | ✅ YES | Run parallel for throughput |
| xDiT framework | ✅ YES | For DiT models (Flux, not SteadyDancer) |
| ComfyUI-Distributed | ✅ YES | Multi-machine support |

**Recommendation**: Single A100 80GB is optimal for SteadyDancer.

### 5. Voice Models - DISABLED

| Model | VRAM Saved |
|-------|------------|
| VibeVoice | ~18 GB |
| XTTS | ~4 GB |
| Chatterbox | ~2 GB |
| **Total** | **~24 GB** |

---

## Configuration (Final)

```bash
# Core Toggles
ENABLE_STEADYDANCER=true
STEADYDANCER_VARIANT=fp16

# Acceleration
ENABLE_WAN22_DISTILL=true

# VRAM Optimization
GPU_MEMORY_MODE=auto
COMFYUI_ARGS="--lowvram"

# Disable Voice (save 24GB)
ENABLE_VIBEVOICE=false
ENABLE_XTTS=false
ENABLE_CHATTERBOX=false

# Disable Unused
ENABLE_ILLUSTRIOUS=false
ENABLE_ZIMAGE=false
```

---

## Bead Structure

```
runpod-7lb: Test SteadyDancer dance video workflow [P1] [READY]
│
├── runpod-sgj: Push Docker image to GHCR [P2] [BLOCKED]
│   └── runpod-aox: Research Docker hosting [P1] [CLOSED]
│
├── runpod-7lb.1: Add SteadyDancer dependencies [P3]
├── runpod-7lb.2: Enhance download script [P3]
├── runpod-7lb.3: Configure DWPose extraction [P3]
├── runpod-7lb.4: Create dance workflow [P3]
├── runpod-7lb.5: Local Docker test [P2]
└── runpod-7lb.6: Deploy to RunPod A100 80GB [P1]
```

---

## RunPod Deployment Command

```bash
runpodctl create pod \
  --name "steadydancer-turbo-$(date +%H%M)" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA A100 80GB" \
  --gpuCount 1 \
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
```

---

## Cost Analysis (A100 80GB)

| Scenario | Rate | Monthly (720hrs) |
|----------|------|------------------|
| On-Demand Secure | $1.50/hr | $1,080 |
| On-Demand Community | $1.19/hr | $857 |
| Spot (50% off) | $0.60/hr | $432 |
| Spot (70% off) | $0.36/hr | $259 |

**Per-Video Cost**: ~$0.05-0.08 (3-min generation at $1-1.50/hr)

---

## References

- TurboDiffusion: https://github.com/thu-ml/TurboDiffusion
- SteadyDancer: https://github.com/MCG-NJU/SteadyDancer
- DWPose: https://github.com/IDEA-Research/DWPose
- RunPod Pricing: https://www.runpod.io/pricing
- RunPod A100: https://www.runpod.io/gpu-models/a100-pcie

