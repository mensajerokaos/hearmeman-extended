---
author: $USER
model: claude-sonnet-4-5-20250929
date: 2026-01-17
task: AI Models Documentation - Environment Variables, Storage Requirements, Model Paths, and Download Sources
---
# AI Models Documentation

This document provides complete documentation for all AI models available in the Hearmeman Extended RunPod template, including environment variables, storage requirements, model paths, download sources, and GPU tier recommendations.

---

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Model Storage Requirements](#model-storage-requirements)
3. [Model Paths and Filenames](#model-paths-and-filenames)
4. [Download Sources](#download-sources)
5. [Model Selection Guide by GPU Tier](#model-selection-guide-by-gpu-tier)
6. [VRAM Requirements Summary](#vram-requirements-summary)

---

## Environment Variables

All models are controlled via environment variables. Set these in your RunPod template or docker-compose configuration.

### Core Configuration Variables

| Variable | Default | Description |
|----------|---------|-------------|
| GPU_TIER | consumer | GPU tier: consumer (8-24GB), prosumer (24GB+), datacenter (48-80GB) |
| GPU_MEMORY_MODE | auto | Memory mode: auto, full, model_cpu_offload, sequential_cpu_offload |
| COMFYUI_ARGS | auto | ComfyUI arguments: --lowvram, --medvram, --cpu-vae, etc. |
| STORAGE_MODE | auto | Storage mode: auto, ephemeral, persistent |
| MODELS_DIR | /workspace/ComfyUI/models | Base models directory |
| DRY_RUN | false | Preview downloads without downloading |
| DOWNLOAD_TIMEOUT | 1800 | Download timeout in seconds (30 min default) |

### Model Toggle Variables

#### Tier 1: Consumer GPU Models (8-24GB VRAM)

| Variable | Default | Model | VRAM | Disk |
|----------|---------|-------|------|------|
| ENABLE_VIBEVOICE | true | VibeVoice TTS | 8-16GB | ~18GB |
| ENABLE_ZIMAGE | false | Z-Image Turbo | 16-24GB | ~21GB |
| ENABLE_ILLUSTRIOUS | false | Realism Illustrious | 8-16GB | ~7GB |
| ENABLE_CONTROLNET | true | ControlNet Preprocessors | 2-8GB | ~3.6GB |
| ENABLE_I2V | false | Image-to-Video CLIP | 1-2GB | ~1.4GB |
| ENABLE_WAN22_DISTILL | false | WAN 2.2 TurboDiffusion | 24GB | ~28GB |
| ENABLE_GENFOCUS | true | Depth-of-Field Refocus | ~12GB | ~12GB |
| ENABLE_QWEN_EDIT | true | Qwen Image Edit | 8-54GB | 4-54GB |
| ENABLE_MVINVERSE | true | Multi-view Inverse Render | ~8GB | ~8GB |

#### Tier 2: Prosumer GPU Models (24GB+ VRAM with CPU Offload)

| Variable | Default | Model | VRAM | Disk |
|----------|---------|-------|------|------|
| ENABLE_FLASHPORTRAIT | false | Portrait Animation | 10-60GB | ~60GB |
| ENABLE_STORYMEM | false | Multi-Shot Storytelling | ~20-24GB | ~20GB+ |

#### Tier 3: Datacenter GPU Models (48-80GB VRAM)

| Variable | Default | Model | VRAM | Disk |
|----------|---------|-------|------|------|
| ENABLE_INFCAM | false | Camera-Controlled Video | 50GB+ | ~50GB |

#### Video Generation Models

| Variable | Default | Model | VRAM | Disk |
|----------|---------|-------|------|------|
| WAN_720P | false | WAN 2.1 720p T2V | 16-24GB | ~25GB |
| WAN_480P | false | WAN 2.1 480p T2V | 8-16GB | ~12GB |
| ENABLE_STEADYDANCER | false | SteadyDancer | 24-32GB | ~33GB |
| ENABLE_SCAIL | false | SCAIL Facial Mocap | 24-32GB | ~28GB |
| ENABLE_VACE | false | VACE Video Editing | 24-32GB | ~28GB |
| ENABLE_FUN_INP | false | Fun Interpolation | 24-32GB | ~28GB |

#### TTS and Additional Models

| Variable | Default | Model | VRAM | Disk |
|----------|---------|-------|------|------|
| ENABLE_XTTS | false | XTTS v2 Multilingual | 4-8GB | ~1.8GB |
| ENABLE_CIVITAI | false | CivitAI LoRAs | varies | varies |

### VibeVoice-Specific Variables

| Variable | Default | Description |
|----------|---------|-------------|
| VIBEVOICE_MODEL | Large | Model size: 1.5B, Large, Large-Q8 |
| VIBEVOICE_SPEAKERS | (optional) | Number of speakers (default: 4) |

### Illustrious-Specific Variables

| Variable | Default | Description |
|----------|---------|-------------|
| ENABLE_ILLUSTRIOUS_EMBEDDINGS | true | Download positive/negative embeddings |
| ILLUSTRIOUS_LORAS | (optional) | Comma-separated CivitAI version IDs |

### Qwen-Edit-Specific Variables

| Variable | Default | Description |
|----------|---------|-------------|
| QWEN_EDIT_MODEL | Q4_K_M | Quantization: Q2_K, Q3_K_M, Q4_K_M, Q5_K_M, Q6_K, Q8_0, full |

### ControlNet Variables

| Variable | Default | Description |
|----------|---------|-------------|
| CONTROLNET_MODELS | canny,depth,openpose | Comma-separated: canny, depth, openpose, lineart, normalbae |

### CivitAI Variables

| Variable | Default | Description |
|----------|---------|-------------|
| CIVITAI_API_KEY | (optional) | CivitAI API key for rate limit increase |
| CIVITAI_LORAS | (optional) | Comma-separated CivitAI version IDs |

### R2 Sync Variables

| Variable | Default | Description |
|----------|---------|-------------|
| ENABLE_R2_SYNC | false | Enable R2 output sync daemon |
| R2_ENDPOINT | (required) | R2 endpoint URL |
| R2_BUCKET | runpod | Target bucket name |
| R2_ACCESS_KEY_ID | (required) | R2 Access Key ID |
| R2_SECRET_ACCESS_KEY | (required) | R2 Secret Access Key |

---

## Model Storage Requirements

### Complete Storage Summary

| Model | Total Disk | Download Source | Notes |
|-------|------------|-----------------|-------|
| VibeVoice 1.5B | ~4GB | HuggingFace | Smaller TTS model |
| VibeVoice Large | ~18GB | HuggingFace | Full TTS with voice cloning |
| VibeVoice Large-Q8 | ~21GB | HuggingFace | Quantized 8-bit |
| WAN 2.1 720p (T2V) | ~25GB | HuggingFace | Text-to-video 14B |
| WAN 2.1 720p (I2V) | ~14GB (add-on) | HuggingFace | Image-to-video add-on |
| WAN 2.1 480p | ~12GB | HuggingFace | Lightweight T2V 1.3B |
| WAN 2.2 Distilled | ~28GB | HuggingFace | TurboDiffusion I2V |
| Realism Illustrious | ~6.5GB | CivitAI | SDXL photorealism |
| Illustrious Embeddings | ~1MB | CivitAI | Positive + negative |
| Z-Image Turbo | ~21GB | HuggingFace | Fast txt2img |
| SteadyDancer | ~33GB | HuggingFace | Dance video generation |
| SCAIL | ~28GB | HuggingFace | Facial mocap |
| VACE 14B | ~28GB | HuggingFace | Video editing |
| Fun InP 14B | ~28GB | HuggingFace | Frame interpolation |
| Genfocus | ~12GB | HuggingFace | Depth-of-field refocus |
| Qwen-Edit Q4_K_M | ~13GB | unsloth/GGUF | Quantized image edit |
| Qwen-Edit Q8_0 | ~22GB | unsloth/GGUF | High-quality quantized |
| Qwen-Edit full | ~54GB | HuggingFace | Full precision |
| MVInverse | ~8GB | Git clone | Multi-view rendering |
| FlashPortrait | ~60GB | HuggingFace | Portrait animation |
| StoryMem | ~20GB+ | HuggingFace | Multi-shot video |
| InfCam | ~50GB+ | HuggingFace | Camera-controlled video |
| ControlNet (5 models) | ~3.6GB | HuggingFace | Preprocessors |
| XTTS v2 | ~1.8GB | Coqui | Multilingual TTS |

### Storage Estimates by Configuration

| Configuration | Total Disk | VRAM |
|---------------|------------|------|
| Minimum (VibeVoice only) | ~20GB | 8-12GB |
| Typical (WAN 720p + VibeVoice) | ~45GB | 16-24GB |
| Full (All models) | ~230GB | 24-48GB+ |
| Prosumer (WAN + Illustrious) | ~60GB | 24GB+ |
| Datacenter (All + InfCam) | ~280GB | 48-80GB |

---

## Model Paths and Filenames

### VibeVoice Models

| Component | Path | Filename |
|-----------|------|----------|
| Model (1.5B) | models/vibevoice/VibeVoice-1.5B/ | pytorch_model.bin |
| Model (Large) | models/vibevoice/VibeVoice-Large/ | pytorch_model.bin |
| Model (Q8) | models/vibevoice/VibeVoice-Large-Q8/ | pytorch_model.bin |
| Tokenizer | models/vibevoice/tokenizer/ | tokenizer.json |

### WAN 2.1 Models

| Component | Path | Filename |
|-----------|------|----------|
| Text Encoder | models/text_encoders/ | umt5_xxl_fp8_e4m3fn_scaled.safetensors |
| CLIP Vision | models/clip_vision/ | clip_vision_h.safetensors |
| VAE | models/vae/ | wan_2.1_vae.safetensors |
| Diffusion (720p T2V) | models/diffusion_models/ | wan2.1_t2v_14B_fp8_e4m3fn.safetensors |
| Diffusion (720p I2V) | models/diffusion_models/ | wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors |
| Diffusion (480p T2V) | models/diffusion_models/ | wan2.1_t2v_1.3B_fp16.safetensors |

### WAN 2.2 Distilled Models (TurboDiffusion)

| Component | Path | Filename |
|-----------|------|----------|
| High Noise Expert | models/diffusion_models/ | wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors |
| Low Noise Expert | models/diffusion_models/ | wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors |

### WAN 2.2 Variants

| Model | Path | Filename |
|-------|------|----------|
| SteadyDancer | models/diffusion_models/ | Wan21_SteadyDancer_fp16.safetensors |
| VACE 14B | models/diffusion_models/ | wan2.1_vace_14B_fp16.safetensors |
| Fun InP 14B | models/diffusion_models/ | wan2.2_fun_inp_14B_fp16.safetensors |
| SCAIL | models/diffusion_models/SCAIL-Preview/ | Multiple files |

### Illustrious Models

| Component | Path | Filename | CivitAI ID |
|-----------|------|----------|------------|
| Checkpoint | models/checkpoints/ | realismIllustriousByStableYogi_v50FP16.safetensors | 2091367 |
| Positive Embed | models/embeddings/ | Stable_Yogis_Illustrious_Positives.safetensors | 1153237 |
| Negative Embed | models/embeddings/ | Stable_Yogis_Illustrious_Negatives.safetensors | 1153212 |
| NegativeXL | models/embeddings/ | negativeXL_D.safetensors | 134583 |
| PDXL | models/embeddings/ | PDXL.safetensors | 367841 |

### Z-Image Turbo Models

| Component | Path | Filename |
|-----------|------|----------|
| Text Encoder | models/text_encoders/ | qwen_3_4b.safetensors |
| Diffusion | models/diffusion_models/ | z_image_turbo_bf16.safetensors |
| VAE | models/vae/ | ae.safetensors |

### ControlNet Models

| Model | Path | Filename |
|-------|------|----------|
| Canny | models/controlnet/ | control_v11p_sd15_canny_fp16.safetensors |
| Depth | models/controlnet/ | control_v11f1p_sd15_depth_fp16.safetensors |
| OpenPose | models/controlnet/ | control_v11p_sd15_openpose_fp16.safetensors |
| LineArt | models/controlnet/ | control_v11p_sd15_lineart_fp16.safetensors |
| Normal BAE | models/controlnet/ | control_v11p_sd15_normalbae_fp16.safetensors |

### Genfocus Models

| Component | Path | Filename |
|-----------|------|----------|
| BokehNet | models/genfocus/ | bokehNet.safetensors |
| DeblurNet | models/genfocus/ | deblurNet.safetensors |
| Depth Pro | models/genfocus/ | depth_pro.pt |

### Qwen-Edit Models

| Quantization | Path | Filename |
|--------------|------|----------|
| Q2_K | models/qwen/ | qwen-image-edit-2511-Q2_K.gguf |
| Q3_K_M | models/qwen/ | qwen-image-edit-2511-Q3_K_M.gguf |
| Q4_K_M | models/qwen/ | qwen-image-edit-2511-Q4_K_M.gguf |
| Q5_K_M | models/qwen/ | qwen-image-edit-2511-Q5_K_M.gguf |
| Q6_K | models/qwen/ | qwen-image-edit-2511-Q6_K.gguf |
| Q8_0 | models/qwen/ | qwen-image-edit-2511-Q8_0.gguf |
| Full | models/qwen/Qwen-Image-Edit-2511/ | Multiple files |

### MVInverse Models

| Component | Path | Notes |
|-----------|------|-------|
| Repository | models/mvinverse/mvinverse/ | Git clone |
| Checkpoints | Auto-download | Via --ckpt flag |

### FlashPortrait Models

| Component | Path |
|-----------|------|
| Main Model | models/flashportrait/FlashPortrait/ |
| WAN I2V Dependency | models/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors |

### StoryMem Models

| Component | Path |
|-----------|------|
| Base Model (T2V) | models/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors |
| Base Model (I2V) | models/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors |
| Text Encoder | models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors |
| VAE | models/vae/wan_2.1_vae.safetensors |
| LoRA Variants | models/storymem/StoryMem/ |

### InfCam Models

| Component | Path |
|-----------|------|
| Main Model | models/infcam/InfCam/ |
| UniDepth | models/infcam/unidepth-v2-vitl14/ |
| WAN Base | models/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors |

### LoRA Storage

| Model Type | Path | Notes |
|------------|------|-------|
| Illustrious LoRAs | models/loras/ | Via ILLUSTRIOUS_LORAS variable |
| CivitAI LoRAs | models/loras/ | Via CIVITAI_LORAS variable |

---

## Download Sources

### HuggingFace Repositories

| Model | Repository | Type |
|-------|------------|------|
| VibeVoice 1.5B | microsoft/VibeVoice-1.5B | Snapshot |
| VibeVoice Large | aoi-ot/VibeVoice-Large | Snapshot |
| VibeVoice Large-Q8 | FabioSarracino/VibeVoice-Large-Q8 | Snapshot |
| WAN 2.1 Repackaged | Comfy-Org/Wan_2.1_ComfyUI_repackaged | Individual files |
| WAN 2.2 Repackaged | Comfy-Org/Wan_2.2_ComfyUI_Repackaged | Individual files |
| WAN 2.2 VACE | Wan-AI/Wan2.1-VACE-14B | Individual files |
| WAN 2.2 Fun InP | Wan-AI/Wan2.2-Fun-InP-14B | Individual files |
| SteadyDancer | MCG-NJU/SteadyDancer-14B | Individual files |
| Z-Image Turbo | Tongyi-MAI/Z-Image-Turbo | Individual files |
| SIGCLIP Vision | Comfy-Org/sigclip_vision_384 | Individual files |
| ControlNet v1.1 | comfyanonymous/ControlNet-v1-1_fp16_safetensors | Individual files |
| Genfocus | nycu-cplab/Genfocus-Model | Individual files |
| Qwen Tokenizer | Qwen/Qwen2.5-1.5B | Individual files |
| FlashPortrait | FrancisRing/FlashPortrait | Snapshot |
| StoryMem | Kevin-thu/StoryMem | Snapshot |
| InfCam | emjay73/InfCam | Snapshot |
| UniDepth | lpiccinelli/unidepth-v2-vitl14 | Snapshot |

### CivitAI Downloads

| Model | Version ID | Type |
|-------|------------|------|
| Realism Illustrious | 2091367 | Checkpoint |
| Positive Embedding | 1153237 | Embedding |
| Negative Embedding | 1153212 | Embedding |
| NegativeXL | 134583 | Embedding |
| PDXL | 367841 | Embedding |

### CivitAI API Usage

```bash
# Direct download with API key
CIVITAI_API_KEY=your_key_here

# Download with version ID
civitai_download() {
    local VERSION_ID="$1"
    local TARGET_DIR="$2"
    curl -L "https://civitai.com/api/download/models/${VERSION_ID}?token=${CIVITAI_API_KEY}" \
        -o "${TARGET_DIR}/model_${VERSION_ID}.safetensors"
}
```

### unsloth GGUF Repository

| Model | Repository | Quantizations |
|-------|------------|---------------|
| Qwen Image Edit 2511 | unsloth/Qwen-Image-Edit-2511-GGUF | Q2_K, Q3_K_M, Q4_K_M, Q5_K_M, Q6_K, Q8_0 |

### Git Clones

| Model | Repository | Notes |
|-------|------------|-------|
| SCAIL | zai-org/SCAIL-Preview | Git LFS required |
| MVInverse | Maddog241/mvinverse | Checkpoints auto-download |

---

## Model Selection Guide by GPU Tier

### Consumer GPU (8-24GB VRAM)

#### 8-12GB VRAM (RTX 3080, RTX 4070)

| Model | VRAM | Disk | Recommended Settings |
|-------|------|------|----------------------|
| VibeVoice 1.5B | ~8GB | ~4GB | VIBEVOICE_MODEL=1.5B |
| WAN 480p | ~10GB | ~12GB | WAN_480P=true |
| Illustrious | ~8GB | ~7GB | ENABLE_ILLUSTRIOUS=true |
| Qwen-Edit Q4_K_M | ~13GB | ~13GB | QWEN_EDIT_MODEL=Q4_K_M |
| XTTS v2 | ~4GB | ~2GB | ENABLE_XTTS=true |
| ControlNet | ~4GB | ~3.6GB | ENABLE_CONTROLNET=true (canny, depth) |

#### 16GB VRAM (RTX 4080 Super, RTX 4090)

| Model | VRAM | Disk | Recommended Settings |
|-------|------|------|----------------------|
| VibeVoice Large | ~12GB | ~18GB | VIBEVOICE_MODEL=Large |
| WAN 720p | ~16GB | ~25GB | WAN_720P=true |
| WAN 720p + I2V | ~24GB | ~39GB | WAN_720P=true, ENABLE_I2V=true |
| Z-Image Turbo | ~16GB | ~21GB | ENABLE_ZIMAGE=true |
| Illustrious + embeddings | ~10GB | ~7GB | ENABLE_ILLUSTRIOUS=true |
| Qwen-Edit Q5_K_M | ~15GB | ~16GB | QWEN_EDIT_MODEL=Q5_K_M |
| Genfocus | ~12GB | ~12GB | ENABLE_GENFOCUS=true |
| ControlNet (all) | ~6GB | ~3.6GB | CONTROLNET_MODELS=canny,depth,openpose,lineart,normalbae |

#### 24GB VRAM (RTX 4090 with optimizations)

| Model | VRAM | Disk | Recommended Settings |
|-------|------|------|----------------------|
| WAN 2.2 Distilled | ~24GB | ~28GB | ENABLE_WAN22_DISTILL=true |
| WAN 720p + I2V + VACE | ~32GB | ~70GB | Multi-model |
| VibeVoice Q8 | ~16GB | ~21GB | VIBEVOICE_MODEL=Large-Q8 |
| Qwen-Edit Q8_0 | ~22GB | ~22GB | QWEN_EDIT_MODEL=Q8_0 |
| All ControlNet | ~8GB | ~3.6GB | CONTROLNET_MODELS=all |

### Prosumer GPU (24GB+ with CPU Offload)

#### 24-32GB VRAM (A6000, L40S, dual RTX 4090)

| Model | VRAM | Disk | Recommended Settings |
|-------|------|------|----------------------|
| FlashPortrait (CPU offload) | ~10GB + 32GB RAM | ~60GB | ENABLE_FLASHPORTRAIT=true, GPU_MEMORY_MODE=sequential_cpu_offload |
| StoryMem | ~20-24GB | ~20GB+ | ENABLE_STORYMEM=true |
| All WAN models | ~40GB | ~80GB | Multi-model deployment |
| SteadyDancer | ~28GB | ~33GB | ENABLE_STEADYDANCER=true |
| VACE | ~24GB | ~28GB | ENABLE_VACE=true |

### Datacenter GPU (48-80GB VRAM)

#### A100 80GB, H100 80GB

| Model | VRAM | Disk | Recommended Settings |
|-------|------|------|----------------------|
| FlashPortrait (full load) | ~60GB | ~60GB | ENABLE_FLASHPORTRAIT=true, GPU_MEMORY_MODE=full |
| InfCam | ~50GB+ | ~50GB+ | ENABLE_INFCAM=true, GPU_TIER=datacenter |
| Qwen-Edit full | ~54GB | ~54GB | QWEN_EDIT_MODEL=full |
| All models + training | ~80GB | ~280GB | Full deployment |

---

## VRAM Requirements Summary

### VRAM by Model (Detailed)

| Model | Minimum VRAM | Recommended VRAM | Memory Mode Options |
|-------|--------------|------------------|---------------------|
| VibeVoice 1.5B | 6GB | 8GB | full, sequential_cpu_offload |
| VibeVoice Large | 10GB | 12GB | full, model_cpu_offload |
| VibeVoice Large-Q8 | 14GB | 16GB | full, model_cpu_offload |
| WAN 2.1 480p T2V | 8GB | 12GB | full, sequential_cpu_offload |
| WAN 2.1 720p T2V | 14GB | 20GB | full, model_cpu_offload |
| WAN 2.1 720p I2V | 14GB | 20GB | full, model_cpu_offload |
| WAN 2.2 Distilled | 20GB | 24GB | full, model_cpu_offload |
| Realism Illustrious | 6GB | 10GB | full, sequential_cpu_offload |
| Z-Image Turbo | 14GB | 20GB | full, model_cpu_offload |
| SteadyDancer | 24GB | 32GB | full, model_cpu_offload |
| SCAIL | 20GB | 28GB | full, model_cpu_offload |
| VACE 14B | 24GB | 32GB | full, model_cpu_offload |
| Fun InP 14B | 24GB | 32GB | full, model_cpu_offload |
| Genfocus | 10GB | 12GB | full, model_cpu_offload |
| Qwen-Edit Q4_K_M | 10GB | 13GB | full, model_cpu_offload |
| Qwen-Edit Q5_K_M | 12GB | 15GB | full, model_cpu_offload |
| Qwen-Edit Q8_0 | 18GB | 22GB | full, model_cpu_offload |
| Qwen-Edit full | 48GB | 54GB | full only |
| MVInverse | 6GB | 8GB | full, sequential_cpu_offload |
| FlashPortrait full | 60GB | 60GB | full only |
| FlashPortrait CPU offload | 10GB | 10GB + 32GB RAM | sequential_cpu_offload |
| FlashPortrait model offload | 30GB | 30GB | model_cpu_offload |
| StoryMem | 20GB | 24GB | full, model_cpu_offload |
| InfCam | 50GB | 50GB+ | full only |
| ControlNet (1 model) | 2GB | 4GB | full, sequential_cpu_offload |
| ControlNet (5 models) | 6GB | 8GB | full, sequential_cpu_offload |
| XTTS v2 | 4GB | 6GB | full |

### GPU Memory Mode Guide

| Mode | VRAM Required | RAM Required | Use Case |
|------|---------------|--------------|----------|
| full | Full model size | Minimal | High VRAM cards (24GB+) |
| model_cpu_offload | ~50% model size | ~50% model size | Medium VRAM (16-24GB) |
| sequential_cpu_offload | ~10-20% model size | Full model size | Low VRAM (8-16GB) |
| cpu-vae | VAE on CPU | Extra RAM | Very low VRAM |

### Auto-Detection (start.sh)

```bash
# VRAM thresholds for auto-detection
if VRAM >= 48000 MB:
    GPU_TIER = "datacenter"
    GPU_MEMORY_MODE = "full"
elif VRAM >= 20000 MB:
    GPU_TIER = "prosumer"
    GPU_MEMORY_MODE = "model_cpu_offload"
else:
    GPU_TIER = "consumer"
    GPU_MEMORY_MODE = "sequential_cpu_offload"

# ComfyUI args auto-detection
if VRAM < 8000 MB:
    COMFYUI_ARGS = "--lowvram --cpu-vae --force-fp16"
elif VRAM < 12000 MB:
    COMFYUI_ARGS = "--lowvram --force-fp16"
elif VRAM < 16000 MB:
    COMFYUI_ARGS = "--medvram --cpu-text-encoder --force-fp16"
elif VRAM < 24000 MB:
    COMFYUI_ARGS = "--normalvram --force-fp16"
else:
    COMFYUI_ARGS = ""
```

---

## Quick Reference: Environment Variable Examples

### Minimum Setup (8GB VRAM)

```yaml
environment:
  - ENABLE_VIBEVOICE=true
  - VIBEVOICE_MODEL=1.5B
  - ENABLE_CONTROLNET=true
  - CONTROLNET_MODELS=canny,depth
  - GPU_MEMORY_MODE=sequential_cpu_offload
```

### Typical Setup (16GB VRAM - RTX 4080/4090)

```yaml
environment:
  - ENABLE_VIBEVOICE=true
  - VIBEVOICE_MODEL=Large
  - WAN_720P=true
  - ENABLE_I2V=true
  - ENABLE_CONTROLNET=true
  - GPU_TIER=consumer
  - GPU_MEMORY_MODE=model_cpu_offload
```

### Full Setup (24GB VRAM - RTX 4090)

```yaml
environment:
  - ENABLE_VIBEVOICE=true
  - VIBEVOICE_MODEL=Large
  - WAN_720P=true
  - ENABLE_I2V=true
  - ENABLE_WAN22_DISTILL=true
  - ENABLE_ILLUSTRIOUS=true
  - ENABLE_ZIMAGE=true
  - ENABLE_CONTROLNET=true
  - CONTROLNET_MODELS=all
  - GPU_TIER=prosumer
  - GPU_MEMORY_MODE=model_cpu_offload
```

### Prosumer Setup (A6000, L40S)

```yaml
environment:
  - ENABLE_VIBEVOICE=true
  - VIBEVOICE_MODEL=Large-Q8
  - WAN_720P=true
  - ENABLE_I2V=true
  - ENABLE_STEADYDANCER=true
  - ENABLE_VACE=true
  - ENABLE_FLASHPORTRAIT=true
  - GPU_TIER=prosumer
  - GPU_MEMORY_MODE=model_cpu_offload
```

### Datacenter Setup (A100/H100 80GB)

```yaml
environment:
  - ENABLE_VIBEVOICE=true
  - VIBEVOICE_MODEL=Large-Q8
  - WAN_720P=true
  - ENABLE_I2V=true
  - ENABLE_STORYMEM=true
  - ENABLE_INFCAM=true
  - QWEN_EDIT_MODEL=full
  - GPU_TIER=datacenter
  - GPU_MEMORY_MODE=full
```

---

## Related Documentation

- Dockerfile - Complete build configuration
- download_models.sh - Model download script with resume support
- start.sh - Startup script with GPU detection
- docker-compose.yml - Local development configuration
- RunPod Deployment Guide - Production deployment instructions

---

Last updated: 2026-01-17
Document version: 1.0
