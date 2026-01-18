---
author: oz + claude-sonnet-4-5 + ma (minimax agent)
model: claude-sonnet-4-5-20250929 + MiniMax-M2.1
date: 2026-01-17
task: Compile master documentation from 6 research sections
status: completed
sections_compiled: 6
sections_source:
  - section-001-docker-infrastructure.md
  - section-002-ai-models.md
  - section-003-tts-voice-systems.md
  - section-004-video-image-generation.md
  - section-005-r2-storage-sync.md
  - section-006-deployment-ci-cd.md
tracking_file: tracking.json
---

# Hearmeman Extended - RunPod Custom Template

## Master Documentation

**Version**: 1.0
**Date**: 2026-01-17
**Total Sections**: 6
**Status**: Complete

---

## Executive Summary

This document provides comprehensive documentation for the Hearmeman Extended RunPod custom template - a production-ready Docker container for AI-powered video, image, and audio generation. The template integrates ComfyUI with custom nodes for video generation (WAN 2.1/2.2), text-to-speech (VibeVoice, XTTS v2, Chatterbox), image generation (Realism Illustrious, Z-Image Turbo), and advanced workflows including R2 cloud storage sync for output persistence. The container is designed for ephemeral RunPod environments where models download on startup and outputs sync to Cloudflare R2 for persistence. This documentation covers Docker infrastructure, AI model configurations, TTS systems, video/image generation workflows, R2 storage sync, and deployment/CI/CD procedures.

---

## Table of Contents

### Part I: Core Infrastructure

1. [Docker Infrastructure](#section-001-docker-infrastructure)
   - Dockerfile architecture and build layers
   - Docker Compose configuration
   - Startup script (`start.sh`)
   - Model download script (`download_models.sh`)
   - Custom ComfyUI nodes

2. [AI Models Configuration](#section-002-ai-models)
   - Environment variables reference
   - Model storage requirements
   - Model paths and filenames
   - Download sources (HuggingFace, CivitAI, Git)
   - VRAM requirements by GPU tier

### Part II: Generation Systems

3. [TTS / Voice Systems](#section-003-tts-voice-systems)
   - VibeVoice-ComfyUI
   - XTTS v2 API
   - Chatterbox TTS
   - CLI tools and API endpoints
   - Performance metrics

4. [Video & Image Generation](#section-004-video-image-generation)
   - WAN 2.1/2.2 video generation
   - TurboDiffusion (WAN 2.2 distilled)
   - VACE video editing
   - Z-Image Turbo
   - Realism Illustrious
   - ControlNet preprocessors

### Part III: Operations

5. [R2 Storage Sync](#section-005-r2-storage-sync)
   - R2 sync daemon (`r2_sync.sh`)
   - Upload script (`upload_to_r2.py`)
   - Configuration and credentials
   - Storage estimates and costs

6. [Deployment, CI/CD](#section-006-deployment-ci-cd)
   - GitHub Actions workflow
   - RunPod pod creation
   - Secret management
   - Datacenter considerations
   - Troubleshooting guide

---

## Quick Reference

### Environment Variables Summary

| Variable | Default | Purpose |
|----------|---------|---------|
| `ENABLE_VIBEVOICE` | true | Enable VibeVoice TTS (~18GB) |
| `VIBEVOICE_MODEL` | Large | Model size: 1.5B, Large, Large-Q8 |
| `WAN_720P` | false | Enable WAN 2.1 720p T2V (~25GB) |
| `WAN_480P` | false | Enable WAN 2.1 480p T2V (~12GB) |
| `ENABLE_I2V` | false | Enable Image-to-Video add-on |
| `ENABLE_WAN22_DISTILL` | false | Enable TurboDiffusion I2V (~28GB) |
| `ENABLE_ILLUSTRIOUS` | false | Enable Realism Illustrious (~7GB) |
| `ENABLE_ZIMAGE` | false | Enable Z-Image Turbo (~21GB) |
| `ENABLE_CONTROLNET` | true | Enable ControlNet models (~3.6GB) |
| `ENABLE_R2_SYNC` | false | Enable R2 output sync |
| `GPU_TIER` | consumer | GPU tier: consumer, prosumer, datacenter |
| `GPU_MEMORY_MODE` | auto | Memory mode: auto, full, sequential_cpu_offload, model_cpu_offload |

### Port Reference

| Port | Service | Description |
|------|---------|-------------|
| 22 | SSH | Remote terminal access |
| 8188 | ComfyUI | Main web interface and API |
| 8000 | Chatterbox API | TTS REST API |
| 8020 | XTTS API | XTTS v2 TTS API |
| 8888 | JupyterLab | Python notebook server |

### GPU VRAM Requirements

| GPU Tier | VRAM Range | Recommended Models |
|----------|------------|-------------------|
| Consumer | 8-24GB | VibeVoice 1.5B, WAN 480p, Illustrious, ControlNet |
| Prosumer | 24-48GB | WAN 720p, TurboDiffusion, VACE, SteadyDancer |
| Datacenter | 48-80GB | InfCam, FlashPortrait, Qwen-Edit full |

---

# Section 001: Docker Infrastructure

## High-Level Architecture

**Build**: `docker/Dockerfile` builds a single image containing ComfyUI, several third-party custom nodes, and local custom nodes.

**Run**: `docker/docker-compose.yml` runs the main ComfyUI container (and optionally a Chatterbox TTS API container via a profile).

**Startup**: The container entrypoint is `docker/start.sh`, which:
- Detects storage mode and GPU tier/VRAM
- Optionally starts SSH and JupyterLab
- Runs `docker/download_models.sh` to fetch models at startup
- Optionally starts an R2 sync daemon (`docker/r2_sync.sh`)
- Launches ComfyUI (`python main.py ...`)

## Ports, Volumes, Paths

**Ports (as used by `docker/docker-compose.yml`)**

| Service | Container Port | Host Port | Purpose |
| --- | --- | --- | --- |
| hearmeman-extended | 8188 | 8188 | ComfyUI web UI + API |
| hearmeman-extended | 22 | 2222 | SSH (key-based; password auth disabled in image) |
| hearmeman-extended | 8888 | 8888 | JupyterLab (token set via `JUPYTER_PASSWORD`) |
| chatterbox | 4123 | 8000 | Chatterbox TTS API |

**Key in-container paths**

| Path | Description |
| --- | --- |
| /workspace/ComfyUI | ComfyUI checkout (cloned during image build) |
| /workspace/ComfyUI/models | Model storage root (bind-mounted in compose) |
| /workspace/ComfyUI/output | Generated outputs (bind-mounted in compose) |
| /var/log/download_models.log | Startup model download logs (`download_models.sh`) |
| /var/log/jupyter.log | JupyterLab logs (`start.sh`) |
| /var/log/r2_sync.log | R2 sync daemon logs (`r2_sync.sh`) |

## Dockerfile Architecture

### Base Image + Build Args

- Base image is configurable via `BASE_IMAGE` build arg (default is RunPod PyTorch CUDA image).
- `COMFYUI_COMMIT` build arg exists but is not used to pin a commit (ComfyUI is cloned without checkout).
- Optional model baking build args: `BAKE_WAN_720P`, `BAKE_WAN_480P`, `BAKE_ILLUSTRIOUS`.

### Layers Overview

1. **System deps**: git, git-lfs, wget/curl, ffmpeg, OpenGL libs, SSH server, aria2, inotify-tools.
2. **ComfyUI base**: clones ComfyUI into `/workspace/ComfyUI` and installs Python requirements.
3. **Third-party custom nodes**: clones multiple repos into `/workspace/ComfyUI/custom_nodes` and attempts to `pip install -r requirements.txt`.
4. **Local custom nodes**: copies `docker/custom_nodes/*` into the image and installs their requirements.
5. **Extra Python deps**: installs HuggingFace + diffusion ecosystem utilities and various runtime libs.
6. **Scripts/config**: copies `start.sh`, `download_models.sh`, `upload_to_r2.py`, `r2_sync.sh`, and example workflows.
7. **Optional baked models**: when build args are enabled, downloads WAN and/or Illustrious models into the image.

### Third-Party Custom Nodes Included

- ComfyUI-Manager (`https://github.com/ltdrdata/ComfyUI-Manager.git`)
- VibeVoice-ComfyUI (`https://github.com/Enemyx-net/VibeVoice-ComfyUI.git`)
- ComfyUI-Chatterbox (`https://github.com/thefader/ComfyUI-Chatterbox.git`)
- ComfyUI-SCAIL-Pose (`https://github.com/kijai/ComfyUI-SCAIL-Pose.git`)
- comfyui_controlnet_aux (`https://github.com/Fannovel16/comfyui_controlnet_aux.git`)
- Comfyui_turbodiffusion (`https://github.com/anveshane/Comfyui_turbodiffusion.git`)
- ComfyUI-WanVideoWrapper (`https://github.com/kijai/ComfyUI-WanVideoWrapper.git`)
- ComfyUI-VideoHelperSuite (`https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git`)

### Environment Defaults (Image-Level)

| Variable | Default | Description |
| --- | --- | --- |
| COMFYUI_PORT | 8188 | Port ComfyUI listens on |
| GPU_TIER | consumer | Intended GPU tier |
| GPU_MEMORY_MODE | auto | Memory strategy |
| COMFYUI_ARGS | "" | Extra args for VRAM handling |
| ENABLE_GENFOCUS | false | Enable Genfocus model downloads |
| ENABLE_QWEN_EDIT | false | Enable Qwen Image Edit model |
| QWEN_EDIT_MODEL | Q4_K_M | Qwen Image Edit quantization |
| ENABLE_MVINVERSE | false | Enable MVInverse repo clone |
| ENABLE_FLASHPORTRAIT | false | Enable FlashPortrait snapshot |
| ENABLE_STORYMEM | false | Enable StoryMem snapshot |
| ENABLE_INFCAM | false | Enable InfCam snapshot |
| ENABLE_R2_SYNC | false | Enable R2 output sync daemon |
| R2_ENDPOINT | (preset) | Cloudflare R2 S3 endpoint URL |
| R2_BUCKET | runpod | Target R2 bucket name |

## Startup Script: `start.sh`

### Startup Sequence

1. Detect storage mode (`STORAGE_MODE=auto|ephemeral|persistent`)
2. Detect GPU VRAM via `nvidia-smi` and auto-set configuration
3. Optional SSH setup when `PUBLIC_KEY` is set
4. Optional JupyterLab when `JUPYTER_PASSWORD` is set
5. Optional `git pull` update for custom nodes when `UPDATE_NODES_ON_START=true`
6. Run `/download_models.sh`
7. Optional background R2 sync daemon when `ENABLE_R2_SYNC=true`
8. Launch ComfyUI

### GPU VRAM Detection Thresholds

| VRAM | GPU Tier | Memory Mode | ComfyUI Args |
|------|----------|-------------|--------------|
| < 8GB | consumer | sequential_cpu_offload | --lowvram --cpu-vae --force-fp16 |
| 8-12GB | consumer | sequential_cpu_offload | --lowvram --force-fp16 |
| 12-16GB | consumer | sequential_cpu_offload | --medvram --cpu-text-encoder --force-fp16 |
| 16-24GB | consumer | model_cpu_offload | --normalvram --force-fp16 |
| 24-48GB | prosumer | model_cpu_offload | (default args) |
| 48GB+ | datacenter | full | (empty - native BF16) |

## Model Download Script: `download_models.sh`

### Download Helpers

- `download_model(URL, DEST, EXPECTED_SIZE?)`: uses `wget` with resume; falls back to `curl`
- `hf_download(REPO, FILE, DEST, EXPECTED_SIZE?)`: constructs HuggingFace URL and calls `download_model`
- `hf_snapshot_download(REPO, DEST)`: uses `huggingface_hub.snapshot_download` from Python
- `civitai_download(VERSION_ID, TARGET_DIR, DESCRIPTION?)`: downloads via CivitAI API

### Key Environment Variables

| Variable | Default | Used For |
| --- | --- | --- |
| MODELS_DIR | /workspace/ComfyUI/models | Root directory for downloads |
| DRY_RUN | false | Preview without downloading |
| DOWNLOAD_TIMEOUT | 1800 | Timeout in seconds |
| CIVITAI_API_KEY | (unset) | API token for CivitAI |
| ENABLE_VIBEVOICE | false | Enable VibeVoice downloads |
| VIBEVOICE_MODEL | Large | Model selection |
| WAN_720P | false | Enable WAN 2.1 720p |
| WAN_480P | false | Enable WAN 2.1 480p |
| ENABLE_I2V | false | Enable I2V dependencies |
| ENABLE_WAN22_DISTILL | false | Enable TurboDiffusion I2V |
| ENABLE_CONTROLNET | true | Enable ControlNet |
| ENABLE_ILLUSTRIOUS | false | Enable Illustrious |
| ENABLE_QWEN_EDIT | false | Enable Qwen Image Edit |

---

# Section 002: AI Models Configuration

## Environment Variables

### Core Configuration Variables

| Variable | Default | Description |
|----------|---------|-------------|
| GPU_TIER | consumer | GPU tier: consumer (8-24GB), prosumer (24GB+), datacenter (48-80GB) |
| GPU_MEMORY_MODE | auto | Memory mode: auto, full, model_cpu_offload, sequential_cpu_offload |
| COMFYUI_ARGS | auto | ComfyUI arguments: --lowvram, --medvram, --cpu-vae, etc. |
| STORAGE_MODE | auto | Storage mode: auto, ephemeral, persistent |
| MODELS_DIR | /workspace/ComfyUI/models | Base models directory |
| DRY_RUN | false | Preview downloads without downloading |
| DOWNLOAD_TIMEOUT | 1800 | Download timeout in seconds |

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

#### Tier 2: Prosumer GPU Models (24GB+ with CPU Offload)

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

## Model Storage Requirements

| Model | Total Disk | Download Source | Notes |
|-------|------------|-----------------|-------|
| VibeVoice 1.5B | ~4GB | HuggingFace | Smaller TTS model |
| VibeVoice Large | ~18GB | HuggingFace | Full TTS with voice cloning |
| VibeVoice Large-Q8 | ~21GB | HuggingFace | Quantized 8-bit |
| WAN 2.1 720p (T2V) | ~25GB | HuggingFace | Text-to-video 14B |
| WAN 2.1 480p | ~12GB | HuggingFace | Lightweight T2V 1.3B |
| WAN 2.2 Distilled | ~28GB | HuggingFace | TurboDiffusion I2V |
| Realism Illustrious | ~6.5GB | CivitAI | SDXL photorealism |
| Z-Image Turbo | ~21GB | HuggingFace | Fast txt2img |
| SteadyDancer | ~33GB | HuggingFace | Dance video generation |
| SCAIL | ~28GB | HuggingFace | Facial mocap |
| VACE 14B | ~28GB | HuggingFace | Video editing |
| Genfocus | ~12GB | HuggingFace | Depth-of-field refocus |
| Qwen-Edit Q4_K_M | ~13GB | unsloth/GGUF | Quantized image edit |
| ControlNet (5 models) | ~3.6GB | HuggingFace | Preprocessors |
| XTTS v2 | ~1.8GB | Coqui | Multilingual TTS |

## Model Paths and Filenames

### VibeVoice Models

| Component | Path | Filename |
|-----------|------|----------|
| Model (1.5B) | models/vibevoice/VibeVoice-1.5B/ | pytorch_model.bin |
| Model (Large) | models/vibevoice/VibeVoice-Large/ | pytorch_model.bin |
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

### WAN 2.2 Distilled Models

| Component | Path | Filename |
|-----------|------|----------|
| High Noise Expert | models/diffusion_models/ | wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors |
| Low Noise Expert | models/diffusion_models/ | wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors |

### ControlNet Models

| Model | Path | Filename |
|-------|------|----------|
| Canny | models/controlnet/ | control_v11p_sd15_canny_fp16.safetensors |
| Depth | models/controlnet/ | control_v11f1p_sd15_depth_fp16.safetensors |
| OpenPose | models/controlnet/ | control_v11p_sd15_openpose_fp16.safetensors |
| LineArt | models/controlnet/ | control_v11p_sd15_lineart_fp16.safetensors |
| Normal BAE | models/controlnet/ | control_v11p_sd15_normalbae_fp16.safetensors |

## Download Sources

### HuggingFace Repositories

| Model | Repository | Type |
|-------|------------|------|
| VibeVoice 1.5B | microsoft/VibeVoice-1.5B | Snapshot |
| VibeVoice Large | aoi-ot/VibeVoice-Large | Snapshot |
| WAN 2.1 Repackaged | Comfy-Org/Wan_2.1_ComfyUI_repackaged | Individual files |
| WAN 2.2 Repackaged | Comfy-Org/Wan_2.2_ComfyUI_Repackaged | Individual files |
| WAN 2.2 VACE | Wan-AI/Wan2.1-VACE-14B | Individual files |
| SteadyDancer | MCG-NJU/SteadyDancer-14B | Individual files |
| Z-Image Turbo | Tongyi-MAI/Z-Image-Turbo | Individual files |
| Genfocus | nycu-cplab/Genfocus-Model | Individual files |

### CivitAI Downloads

| Model | Version ID | Type |
|-------|------------|------|
| Realism Illustrious | 2091367 | Checkpoint |
| Positive Embedding | 1153237 | Embedding |
| Negative Embedding | 1153212 | Embedding |

### unsloth GGUF Repository

| Model | Repository | Quantizations |
|-------|------------|---------------|
| Qwen Image Edit 2511 | unsloth/Qwen-Image-Edit-2511-GGUF | Q2_K, Q3_K_M, Q4_K_M, Q5_K_M, Q6_K, Q8_0 |

## GPU Tier Selection Guide

### Consumer GPU (8-24GB VRAM)

**8-12GB VRAM (RTX 3080, RTX 4070)**

| Model | VRAM | Disk | Settings |
|-------|------|------|----------|
| VibeVoice 1.5B | ~8GB | ~4GB | VIBEVOICE_MODEL=1.5B |
| WAN 480p | ~10GB | ~12GB | WAN_480P=true |
| Illustrious | ~8GB | ~7GB | ENABLE_ILLUSTRIOUS=true |
| Qwen-Edit Q4_K_M | ~13GB | ~13GB | QWEN_EDIT_MODEL=Q4_K_M |

**16GB VRAM (RTX 4080 Super, RTX 4090)**

| Model | VRAM | Disk | Settings |
|-------|------|------|----------|
| VibeVoice Large | ~12GB | ~18GB | VIBEVOICE_MODEL=Large |
| WAN 720p | ~16GB | ~25GB | WAN_720P=true |
| WAN 720p + I2V | ~24GB | ~39GB | WAN_720P=true, ENABLE_I2V=true |
| Z-Image Turbo | ~16GB | ~21GB | ENABLE_ZIMAGE=true |

### Prosumer GPU (24GB+ with CPU Offload)

**24-32GB VRAM (A6000, L40S, dual RTX 4090)**

| Model | VRAM | Disk | Settings |
|-------|------|------|----------|
| FlashPortrait (CPU offload) | ~10GB + 32GB RAM | ~60GB | sequential_cpu_offload |
| StoryMem | ~20-24GB | ~20GB+ | ENABLE_STORYMEM=true |
| SteadyDancer | ~28GB | ~33GB | ENABLE_STEADYDANCER=true |
| VACE | ~24GB | ~28GB | ENABLE_VACE=true |

### Datacenter GPU (48-80GB VRAM)

**A100 80GB, H100 80GB**

| Model | VRAM | Disk | Settings |
|-------|------|------|----------|
| FlashPortrait (full load) | ~60GB | ~60GB | GPU_MEMORY_MODE=full |
| InfCam | ~50GB+ | ~50GB+ | ENABLE_INFCAM=true, GPU_TIER=datacenter |
| Qwen-Edit full | ~54GB | ~54GB | QWEN_EDIT_MODEL=full |

---

# Section 003: TTS / Voice Systems

## At a Glance

| System | How you run it | Primary API/UI | Strengths | VRAM |
|---|---|---|---|---:|
| VibeVoice-ComfyUI | Inside ComfyUI | http://localhost:8188 | Highest quality; ComfyUI workflows; LoRA; multi-speaker | ~8-16GB |
| XTTS v2 | Separate container | http://localhost:8020/docs | Simple REST API; multilingual (17 langs); voice cloning | ~4-8GB |
| Chatterbox TTS | Separate container | http://localhost:8000/docs | OpenAI-compatible endpoints; voice library; aliases; streaming | ~2-6GB |

## 1. VibeVoice-ComfyUI

### Overview

VibeVoice is a ComfyUI custom node for high-quality TTS with voice cloning.

**Repository**: https://github.com/Enemyx-net/VibeVoice-ComfyUI (v1.8.1+)
**Model**: [aoi-ot/VibeVoice-Large](https://huggingface.co/aoi-ot/VibeVoice-Large) (~18GB)

### Critical Dependencies

```txt
bitsandbytes>=0.48.1  # Critical - older versions break Q8 model
transformers>=4.51.3
accelerate
peft
librosa
soundfile
```

### Environment Variables

| Variable | Default | Size Impact | Notes |
|----------|---------|-------------|-------|
| `ENABLE_VIBEVOICE` | `true` | 18GB | Enable VibeVoice-Large TTS |
| `VIBEVOICE_MODEL` | `Large` | 18GB | Options: `1.5B`, `Large`, `Large-Q8` |

### Node Configuration

```json
{
  "class_type": "VibeVoiceSingleSpeakerNode",
  "inputs": {
    "text": "...",
    "model": "VibeVoice-Large-Q8",
    "attention_type": "auto",
    "quantize_llm": "full precision",
    "free_memory_after_generate": false,
    "diffusion_steps": 20,
    "seed": 42,
    "cfg_scale": 1.3,
    "use_sampling": false,
    "voice_to_clone": ["<LoadAudioNodeId>", 0],
    "temperature": 0.95,
    "top_p": 0.95,
    "max_words_per_chunk": 250,
    "voice_speed_factor": 1.0
  }
}
```

### Performance Notes

- **VibeVoice-1.5B**: ~8-12GB VRAM
- **VibeVoice-Large**: typically needs 16GB+ VRAM
- **VibeVoice-Large-Q8**: lower VRAM, can be slower
- Observed generation time: ~20.62s on L40S for specific test prompt

## 2. XTTS v2 API (Coqui)

### Overview

XTTS v2 is a multilingual (17 language) voice cloning TTS system. Runs as a standalone service due to dependency conflicts with ComfyUI.

**Image**: `daswer123/xtts-api-server:latest`
**Swagger UI**: http://localhost:8020/docs
**VRAM**: 4-8GB

### Endpoints

| Endpoint | Method | Description |
|---|---:|---|
| `/health` | GET | Health check |
| `/tts_to_audio/` | POST | Generate audio and return bytes |
| `/tts_to_file` | POST | Generate audio and save to server path |
| `/tts_stream` | POST | Stream audio bytes (chunked) |
| `/speakers_list` | GET | List available speakers |
| `/languages` | GET | List supported languages |

### Request Schema

```json
{
  "text": "Hello world",
  "speaker_wav": "female",
  "language": "en"
}
```

### Supported Languages (17)

| Code | Language | Code | Language |
|------|----------|------|----------|
| ar | Arabic | it | Italian |
| cs | Czech | ja | Japanese |
| de | German | ko | Korean |
| en | English | nl | Dutch |
| es | Spanish | pl | Polish |
| fr | French | pt | Portuguese |
| hi | Hindi | ru | Russian |
| hu | Hungarian | tr | Turkish |
| | | zh-cn | Chinese |

### Usage Examples

Generate audio:
```bash
curl -X POST http://localhost:8020/tts_to_audio/ \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","speaker_wav":"female","language":"en"}' \
  -o output.wav
```

Stream audio:
```bash
curl -X POST http://localhost:8020/tts_stream \
  -H "Content-Type: application/json" \
  -d '{"text":"Streaming test","speaker_wav":"female","language":"en"}' \
  | ffplay -autoexit -i -
```

### Built-in Speakers

- `male`
- `female`
- `calm_female`

## 3. Chatterbox TTS

### Overview

Chatterbox TTS is a standalone FastAPI server with OpenAI-compatible API endpoints.

**Repository**: https://github.com/resemble-ai/chatterbox
**VRAM**: ~2-6GB

### API Endpoints

| Endpoint | Aliases | Method | Description |
|---|---|---:|---|
| `/audio/speech` | `/v1/audio/speech`, `/tts` | POST | Generate WAV audio |
| `/audio/speech/stream` | `/v1/audio/speech/stream` | POST | Chunked WAV streaming |
| `/voices` | `/v1/voices` | GET/POST | List/upload voices |
| `/voices/{name}` | `/v1/voices/{name}` | GET/PUT/DELETE | Voice operations |
| `/health` | `/v1/health` | GET | Health check |
| `/models` | `/v1/models` | GET | Model list |

### Request Schema

```json
{
  "input": "Text to speak (1..3000 chars)",
  "voice": "alloy",
  "response_format": "wav",
  "speed": 1.0,
  "stream_format": "audio",
  "exaggeration": 0.5,
  "cfg_weight": 0.5,
  "temperature": 0.8
}
```

### Artistic Controls

**CFG (Classifier-Free Guidance)**

| Value | Effect |
|-------|--------|
| 0.0 | Slower, clearer, more expressive |
| 0.5 | Default balance |
| 1.0 | Stricter adherence to input, faster |

**Exaggeration**

| Value | Effect |
|-------|-------|
| 0.0 | Subtle, professional tone |
| 0.5 | General purpose |
| 1.0+ | More dramatic, expressive |

### Supported Languages (23)

ar, da, de, el, en, es, fi, fr, he, hi, it, ja, ko, ms, nl, no, pl, pt, ru, sv, sw, tr

### Usage Examples

Health check:
```bash
curl -sS http://localhost:8000/health | jq .
```

Basic TTS:
```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"chatterbox","input":"Hello world","voice":"default"}' \
  -o cb.wav
```

Upload voice:
```bash
curl -X POST http://localhost:8000/voices \
  -F "voice_file=@./myvoice.wav" \
  -F "voice_name=my-voice" \
  -F "language=en"
```

SSE streaming:
```bash
curl -N -X POST http://localhost:8000/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input":"SSE streaming test","voice":"my-voice","stream_format":"sse"}'
```

## CLI Tool: xtts-vo-gen.py

### Usage

```bash
python3 docker/scripts/xtts-vo-gen.py --help
```

### Options

| Flag | Meaning |
|---|---|
| `TEXT` | Positional text to synthesize |
| `-f, --file` | Script file; non-empty lines become separate outputs |
| `-o, --output` | Output WAV path |
| `-d, --output-dir` | Output directory (batch mode) |
| `-s, --speaker` | Speaker name or reference audio path |
| `-l, --language` | Language code |
| `-p, --prefix` | Output filename prefix |
| `--stream` | Write streaming audio bytes to stdout |
| `--list-speakers` | Query `/speakers_list` |
| `--list-languages` | Query `/languages` |

### Examples

Single line:
```bash
python3 docker/scripts/xtts-vo-gen.py "Hello world" -o hello.wav
```

Batch from file:
```bash
python3 docker/scripts/xtts-vo-gen.py -f script.txt -d ./vo-output -p scene --speaker female --language en
```

Stream to player:
```bash
python3 docker/scripts/xtts-vo-gen.py "Streaming test" --stream | ffplay -autoexit -i -
```

## Dependencies and Version Conflicts

### Critical Conflict: transformers

| System | Required Version | Conflict |
|--------|-----------------|----------|
| XTTS v2 API | `transformers==4.36.2` | **CONFLICTS** |
| VibeVoice-ComfyUI | `transformers>=4.51.3` | **CONFLICTS** |
| Chatterbox | Compatible with both | No conflict |

**Solution**: Run XTTS in a **separate container** from ComfyUI/VibeVoice.

### GPU Memory Allocation

| System | VRAM | Notes |
|--------|------|-------|
| XTTS v2 | ~4GB | Separate container |
| ComfyUI + VibeVoice | ~12GB | Main container |
| **Total (both running)** | ~16GB | Fits on 16GB GPU |

---

# Section 004: Video & Image Generation

## At a Glance

| System | Primary Use | Models (on disk) | Typical VRAM | Inputs | Outputs |
|---|---|---:|---:|---|---|
| WAN 2.1 T2V 14B (FP8) | Text-to-video | ~25GB (deps + 14B) | 24GB+ | prompt | video |
| WAN 2.1 T2V 1.3B (FP16) | Text-to-video (smaller) | ~12GB (deps + 1.3B) | 12-16GB | prompt | video |
| WAN 2.1 I2V 14B (FP8) | Image-to-video | +14GB (i2v model) | 24GB+ | image + prompt | video |
| WAN 2.2 Distilled (TurboDiffusion I2V) | Fast I2V | +28GB (2 experts) | 24GB+ | image + prompt | video |
| VACE 14B (FP16) | Video editing | ~28GB | 24-28GB | video + mask + prompt | edited video |
| Z-Image Turbo | Fast txt2img | ~21GB+ | 16GB+ (24GB recommended) | prompt | images |
| Realism Illustrious (SDXL) | Photorealistic txt2img | 6.46GB (+ embeddings) | 8-16GB | prompt | images |
| SteadyDancer 14B | Dance / motion video | ~28-33GB | 24-32GB | prompt (+ pose) | video |
| SCAIL (Preview) | Facial animation / mocap | ~28GB | 24GB+ | face ref (+ audio/pose) | video / pose |
| ControlNet (SD1.5) | Spatial guidance | ~0.7GB each (~3.6GB for 5) | +1-4GB over base | image/pose/depth/edges | guided images |
| Fun InP 14B | Frame interpolation | ~28GB | 24GB+ | first + last frame | interpolated video |

## ComfyUI Node Requirements (Custom Nodes Installed)

- `ComfyUI-WanVideoWrapper` (WAN 2.x nodes)
- `Comfyui_turbodiffusion` (TurboDiffusion acceleration)
- `ComfyUI-VideoHelperSuite` (video assembly/encoding, e.g. `VHS_VideoCombine`)
- `comfyui_controlnet_aux` (ControlNet preprocessors)
- `ComfyUI-SCAIL-Pose` (SCAIL-related pose nodes)

## Model Directory Conventions

```
ComfyUI/models/
├── checkpoints/        # SDXL/SD checkpoints (Illustrious)
├── diffusion_models/   # WAN, VACE, Fun InP, Z-Image UNET weights
├── text_encoders/      # UMT5 (WAN), Qwen (Z-Image)
├── vae/                # WAN VAE, Z-Image AE
├── clip_vision/        # Vision encoders for I2V
├── controlnet/         # ControlNet weights
├── embeddings/         # Textual inversion embeddings
└── loras/              # LoRAs (optional)
```

## 1. WAN 2.1 / WAN 2.2 Video Generation

### Shared WAN Dependencies

| File | Folder | Used For | Size hint |
|---|---|---|---:|
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | `text_encoders/` | WAN text encoder | 9.5GB |
| `wan_2.1_vae.safetensors` | `vae/` | WAN VAE | 335MB |
| `clip_vision_h.safetensors` | `clip_vision/` | WAN I2V conditioning | 1.4GB |

### WAN Model Variants

| Variant | Primary file(s) | Folder | Typical VRAM | Notes |
|---|---|---:|---:|---|
| WAN 2.1 T2V 14B (FP8) | `wan2.1_t2v_14B_fp8_e4m3fn.safetensors` | `diffusion_models/` | 24GB+ | Requires UMT5 + VAE |
| WAN 2.1 I2V 14B (FP8) | `wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors` | `diffusion_models/` | 24GB+ | Requires CLIP vision |
| WAN 2.1 T2V 1.3B (FP16) | `wan2.1_t2v_1.3B_fp16.safetensors` | `diffusion_models/` | 12-16GB | Smaller model |
| WAN 2.2 distilled I2V experts | `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` + `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` | `diffusion_models/` | 24GB+ | Used by TurboDiffusion 4-step I2V |

### Enable Flags (Startup)

| Env var | Default | What it downloads |
|---|---:|---|
| `WAN_720P` | `false` | WAN 2.1 14B T2V (+ deps) |
| `ENABLE_I2V` | `false` | Adds WAN 2.1 I2V model |
| `WAN_480P` | `false` | WAN 2.1 1.3B T2V |
| `ENABLE_WAN22_DISTILL` | `false` | WAN 2.2 distilled expert models |

### I/O Specifications

**Inputs:**
- **T2V**: prompt (positive/negative), resolution, number of frames, seed
- **I2V**: prompt + an input image (recommended to match output aspect ratio)

**Outputs:**
- A sequence of decoded frames (images)
- A combined video/animation via `VHS_VideoCombine`:
  - `video/webm`
  - `video/mp4`
  - `image/webp` (animated webp)

### Workflow Template: WAN 2.1 14B T2V (API)

**File:** `docker/workflows/wan21-t2v-14b-api.json`

**Key nodes:**
- `CLIPLoader` with `type="wan"`
- `WanVideoModelLoader` with FP8 quantization settings
- `WanVideoSampler` (WAN-specific sampler)
- `WanVideoVAELoader` + `WanVideoDecode`
- `VHS_VideoCombine` for encoding

**Parameters (as shipped):**

| Setting | Value |
|---|---:|
| Resolution | 480x320 |
| Frames | 17 |
| Steps | 15 |
| CFG | 6.0 |
| Shift | 5.0 |
| Scheduler | `unipc` |
| FPS | 16 |
| Output format | `video/webm` |

## 2. TurboDiffusion (WAN 2.2 Distilled I2V)

TurboDiffusion is installed via `anveshane/Comfyui_turbodiffusion`.

**Intended usage:**
- 4-step I2V inference using "high noise" expert for early steps and "low noise" expert for late steps

**Practical guidance:**
- Start with **4 steps**
- If output is unstable/noisy, try 6-8 steps
- Keep resolution and frame count modest until stability confirmed

## 3. VACE (WAN Video Editing)

VACE is a WAN-family model focused on **video editing** tasks such as:
- Video inpainting / outpainting (mask-based edits across frames)
- Video-to-video edits driven by text prompts
- Content replacement while preserving motion consistency

**Enable flag:** `ENABLE_VACE=true`

| Item | Value |
|---|---|
| Model file | `diffusion_models/wan2.1_vace_14B_fp16.safetensors` |
| Disk | ~28GB (FP16 14B-class) |
| VRAM | 24-28GB (48GB recommended for heavy edits) |

### Parameter Guidance

Start with conservative settings:
- Steps: 20-30
- CFG: 4-7
- Frames: 17-49 (short clips first)
- FPS: 12-24

## 4. Z-Image Turbo (Fast Text-to-Image)

**Enable flag:** `ENABLE_ZIMAGE=true`

| File | Folder |
|---|---|
| `qwen_3_4b.safetensors` | `text_encoders/` |
| `z_image_turbo_bf16.safetensors` | `diffusion_models/` |
| `ae.safetensors` | `vae/` |

**VRAM:** For 1024x1024, plan on **16GB+** (24GB recommended)

### Workflow Template

**File:** `docker/workflows/z-image-turbo-txt2img.json`

**Key nodes:**
- `UNETLoader`: `z_image_turbo_bf16.safetensors`
- `CLIPLoader`: `qwen_3_4b.safetensors` with `type="qwen_image"` (**must be explicit**)
- `VAELoader`: `ae.safetensors`
- `EmptySD3LatentImage`: latent init
- `KSampler`: sampling
- `SaveImage`: output

**Parameters:**

| Setting | Value |
|---|---:|
| Resolution | 1024x1024 |
| Steps | 9 |
| CFG | 1.0 |
| Sampler | `euler` |
| Scheduler | `simple` |

## 5. Realism Illustrious (Photorealistic SDXL)

**Enable flag:** `ENABLE_ILLUSTRIOUS=true`

| Item | Path | Notes |
|---|---|---|
| Checkpoint | `checkpoints/realismIllustriousByStableYogi_v50FP16.safetensors` | 6.46GB |
| Positive embedding | `embeddings/Stable_Yogis_Illustrious_Positives.safetensors` | optional |
| Negative embedding | `embeddings/Stable_Yogis_Illustrious_Negatives.safetensors` | optional |

### Workflow Template

**File:** `docker/workflows/realism-illustrious-txt2img.json`

**Parameters:**

| Setting | Value |
|---|---:|
| Resolution | 1024x1024 |
| Steps | 25 |
| CFG | 7.0 |
| Sampler | `dpmpp_2m` |
| Scheduler | `karras` |

### VRAM Guidance

- 768x768 succeeded on a 16GB-class GPU
- 1024x1024 caused OOM on 16GB
- Prefer 768x768 (or portrait 832x1216) on 16GB
- Use 24GB+ for 1024x1024

## 6. ControlNet (Preprocessors + Models)

**Enable flag:** `ENABLE_CONTROLNET=true` (default)
**Default models:** `canny,depth,openpose`

Available options: `canny`, `depth`, `openpose`, `lineart`, `normalbae`

### Model Files (SD1.5 ControlNet v1.1, FP16)

| Control type | Filename |
|---|---|
| Canny | `control_v11p_sd15_canny_fp16.safetensors` |
| Depth | `control_v11f1p_sd15_depth_fp16.safetensors` |
| OpenPose | `control_v11p_sd15_openpose_fp16.safetensors` |
| Lineart | `control_v11p_sd15_lineart_fp16.safetensors` |
| NormalBae | `control_v11p_sd15_normalbae_fp16.safetensors` |

**Note:** Downloaded ControlNets are SD1.5; not drop-in for SDXL checkpoints like Illustrious.

## 7. Fun InP (First/Last Frame Interpolation)

Fun InP generates smooth intermediate frames given first and last frame.

**Enable flag:** `ENABLE_FUN_INP=true`

| Item | Value |
|---|---|
| Model file | `diffusion_models/wan2.2_fun_inp_14B_fp16.safetensors` |
| Disk | ~28GB |
| VRAM | 24GB+ |

### Parameter Guidance

- Frames: 17-41
- FPS: 12-24

## 8. SteadyDancer (Dance/Motion Video)

**Enable flag:** `ENABLE_STEADYDANCER=true`

| Item | Value |
|---|---|
| Model file | `diffusion_models/Wan21_SteadyDancer_fp16.safetensors` |
| Disk | ~28-33GB |
| VRAM | 24-32GB |

## 9. SCAIL (Facial Mocap / Pose)

**Enable flag:** `ENABLE_SCAIL=true`

Downloaded via `git clone` + `git lfs pull` into:
`diffusion_models/SCAIL-Preview/`

## Known Issues and Notes

1. **WAN 2.2 5B Workflow Model Not Auto-Downloaded**
   - Workflow references `wan2.2_ti2v_5B_fp16.safetensors` which is not in `download_models.sh`

2. **WAN 2.2 Distilled Size Message Misleading**
   - Script prints ~28GB but shared deps add ~11GB more

3. **Realism Illustrious Workflow Filename Mismatches**
   - Some workflows reference different filenames than downloaded

4. **Z-Image Turbo VRAM Guidance Inconsistent**
   - Claims 8-12GB VRAM but needs 24GB+ for 1024x1024

5. **Missing Ready-Made Workflows**
   - No workflows shipped for VACE, SteadyDancer, SCAIL, Fun InP

6. **ControlNet Model Family Mismatch**
   - SD1.5 ControlNets not compatible with SDXL Illustrious

---

# Section 005: R2 Storage Sync

## Overview

RunPod pods are ephemeral: anything written to the container filesystem is lost on restart. This project solves output persistence by running a background daemon that watches the ComfyUI output folder and uploads new media files to Cloudflare R2 (S3-compatible object storage).

## Components

| Component | Runtime path | Purpose |
|---|---|---|
| R2 sync daemon | `/r2_sync.sh` | Watches output directory and triggers uploads |
| R2 uploader | `/upload_to_r2.py` | Upload one or more files to R2 |
| Startup integration | `/start.sh` | Starts daemon when `ENABLE_R2_SYNC=true` |
| Primary log | `/var/log/r2_sync.log` | Combined daemon + uploader logs |

## 1. R2 Sync Daemon (`r2_sync.sh`)

### What it does

1. Validates prerequisites (`inotifywait`, `/upload_to_r2.py`, required env vars)
2. Watches ComfyUI output directory recursively using inotify
3. When new file is fully written (`close_write`) and extension matches whitelist, uploads to R2

### File detection and filtering

```bash
WATCH_PATTERNS="\.png$|\.jpg$|\.jpeg$|\.webp$|\.mp4$|\.webm$|\.gif$|\.wav$|\.mp3$|\.flac$"
```

**Important:**
- Event type: `close_write` means "file was closed after writing"
- Case-sensitive regex (e.g., `.PNG` will not match)
- Files introduced via rename/move may not trigger upload

### Environment variables

| Variable | Default | Required | Notes |
|---|---:|---:|---|
| `COMFYUI_OUTPUT_DIR` | `/workspace/ComfyUI/output` | No | Watch directory |
| `R2_ACCESS_KEY_ID` | (none) | Yes | Preferred credential name |
| `R2_SECRET_ACCESS_KEY` | (none) | Yes | Preferred credential name |

## 2. R2 Uploader (`upload_to_r2.py`)

### Features

- Uses `boto3.client('s3', endpoint_url=...)` against R2
- Retries failed uploads (default: 3 attempts) with exponential backoff
- Automatically switches to multipart upload for files larger than 100 MB
- Stores objects under date-based prefix (default: `outputs`)

### Remote key format

```
{prefix}/{YYYY-MM-DD}/{filename}
```

Example:
```
outputs/2026-01-18/myfile.png
```

### Multipart uploads (files > 100 MB)

- Threshold: `100 * 1024 * 1024` bytes
- Chunk size: `50 * 1024 * 1024` bytes per part

### CLI usage

```bash
# Show help
python3 /upload_to_r2.py --help

# Test credentials + connectivity
python3 /upload_to_r2.py --test

# Upload one file
python3 /upload_to_r2.py /workspace/ComfyUI/output/my_image.png

# Upload many files
python3 /upload_to_r2.py file1.png file2.mp4 file3.wav

# Upload into custom prefix
python3 /upload_to_r2.py --prefix videos /workspace/ComfyUI/output/out.mp4
```

### Environment variables

| Variable | Default | Required | Notes |
|---|---:|---:|---|
| `R2_ENDPOINT` | (required) | Yes | R2 endpoint URL |
| `R2_BUCKET` | `runpod` | Yes | Target bucket name |
| `R2_ACCESS_KEY_ID` | (none) | Yes | Access key ID |
| `R2_SECRET_ACCESS_KEY` | (none) | Yes | Secret access key |

## 3. Configuration

### Docker Compose (Local Development)

```dotenv
ENABLE_R2_SYNC=true
R2_ENDPOINT=https://your-account.eu.r2.cloudflarestorage.com
R2_BUCKET=runpod
R2_ACCESS_KEY_ID=your_r2_access_key_here
R2_SECRET_ACCESS_KEY=your_r2_secret_key_here
```

### RunPod Production (Secrets)

```text
R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}
R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}
```

### RunPod Pod Creation Command

```bash
~/.local/bin/runpodctl create pod \
  --name "hearmeman-r2-$(date +%H%M)" \
  --imageName "ghcr.io/oz/hearmeman-extended:latest" \
  --gpuType "NVIDIA GeForce RTX 4090" \
  --containerDiskSize 20 \
  --volumeSize 100 \
  --secureCloud \
  --ports "8188/http" \
  --env "ENABLE_R2_SYNC=true" \
  --env "R2_ENDPOINT=https://..." \
  --env "R2_BUCKET=runpod" \
  --env "R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}" \
  --env "R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}"
```

## 4. File Organization in R2

### Default structure

```
s3://runpod/
└── outputs/
    ├── 2026-01-17/
    │   ├── ComfyUI_00001_.png
    │   └── tts_hello.wav
    └── 2026-01-18/
        ├── ComfyUI_00002_.png
        └── wan_video.mp4
```

### Supported file types

| Category | Extensions |
|----------|------------|
| Images | `.png`, `.jpg`, `.jpeg`, `.webp` |
| Video | `.mp4`, `.webm` |
| Animation | `.gif` |
| Audio | `.wav`, `.mp3`, `.flac` |

## 5. Operations

### Check logs

```bash
tail -f /var/log/r2_sync.log
grep -i error /var/log/r2_sync.log
tail -50 /var/log/r2_sync.log
```

### Test connection

```bash
python3 /upload_to_r2.py --test
# Returns exit code 0 on success
```

### Manually upload files

```bash
python3 /upload_to_r2.py /workspace/ComfyUI/output/some_output.png
python3 /upload_to_r2.py --prefix videos /path/to/video.mp4
```

### Check daemon status

```bash
ps aux | grep r2_sync
pkill -f r2_sync.sh
nohup /r2_sync.sh > /var/log/r2_sync.log 2>&1 &
```

## 6. Storage Estimates and Cost Analysis

### Typical output sizes

| Output type | Typical parameters | Typical size |
|---|---|---:|
| Image (PNG) | 768x768 | 1-2 MB |
| Image (PNG) | 1024x1024 | 3-6 MB |
| Video (WAN) | 720p, ~5s | 20-50 MB |
| Video (WAN) | 720p, ~10s | 40-100 MB |
| Audio (WAV) | TTS line | 0.5-2 MB |

### Cloudflare R2 pricing

| Metric | Price | Notes |
|--------|-------|-------|
| Storage | $0.015 / GB-month | First 10GB often free |
| Class A ops (PUT, COPY, POST, LIST) | $4.50 / million | |
| Class B ops (GET, SELECT) | $0.36 / million | |
| Data Egress | $0 | Free to Cloudflare CDN |
| Data Retrieval | $0.01 / GB | First 10GB/month free |

### Quick cost tables

**Storage-only (at $0.015 / GB-month)**

| Stored GB | Est. storage cost/month |
|---:|---:|
| 10 | $0.15 |
| 50 | $0.75 |
| 100 | $1.50 |
| 500 | $7.50 |

**Class A operations (uploads/PUT, at $4.50 / million)**

| Uploads/month | Est. Class A cost |
|---:|---:|
| 1,000 | $0.0045 |
| 100,000 | $0.45 |
| 1,000,000 | $4.50 |

## 7. Security Best Practices

- **Use RunPod Secrets** for credentials
- **Do not commit secrets** in `.env` files
- **Least privilege:** create dedicated API token restricted to target bucket
- **No delete permission** for the sync token
- **Rotate credentials** and re-test after rotation

---

# Section 006: Deployment, CI/CD

## 1. GitHub Actions Workflow

**File:** `.github/workflows/docker-build.yml`

### Workflow Triggers

```yaml
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
        description: 'Custom image tag'
        required: false
        type: string
        default: 'latest'
```

### Step-by-Step Breakdown

| Step | Action | Purpose |
|------|--------|---------|
| 1 | Free Disk Space | Remove ~20GB of unused packages |
| 2 | Checkout Repository | Clone source code for build context |
| 3 | Setup Docker Buildx | Enable advanced build features |
| 4 | Login to GHCR | Authenticate using GITHUB_TOKEN |
| 5 | Determine Image Tag | Logic to select tag based on inputs |
| 6 | Extract Metadata | Generate OCI labels and tags |
| 7 | Build and Push | Execute Docker build with cache |

### Tag Selection Matrix

| Input | Resulting Tag | Use Case |
|-------|---------------|----------|
| No inputs | `latest` | Standard builds |
| `bake_wan_720p: true` | `wan720p` | Pre-baked WAN 2.1 720p models |
| `bake_wan_480p: true` | `wan480p` | Pre-baked WAN 2.1 480p models |
| `bake_illustrious: true` | `illustrious` | Pre-baked Illustrious model |
| `image_tag: custom` | `custom` | Manual tagging |

### Cache Strategy

- `cache-from: type=gha` - Restore layers from previous builds
- `cache-to: type=gha,mode=max` - Export all layers for max cache hit

## 2. RunPod Pod Creation Commands

### Standard Deployment Command

```bash
~/.local/bin/runpodctl create pod \
  --name "hearmeman-$(date +%H%M)" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA GeForce RTX 4090" \
  --gpuCount 1 \
  --containerDiskSize 20 \
  --volumeSize 15 \
  --secureCloud \
  --ports "8188/http" \
  --ports "19123/http" \
  --env "ENABLE_VIBEVOICE=true" \
  --env "WAN_720P=true" \
  --env "ENABLE_R2_SYNC=true" \
  --env "R2_ENDPOINT=https://..." \
  --env "R2_BUCKET=runpod" \
  --env "R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}" \
  --env "R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}"
```

### Full Configuration (All Models)

```bash
~/.local/bin/runpodctl create pod \
  --name "hearmeman-full-$(date +%H%M)" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA GeForce RTX 4090" \
  --containerDiskSize 20 \
  --volumeSize 100 \
  --secureCloud \
  --ports "8188/http" \
  --env "ENABLE_VIBEVOICE=true" \
  --env "ENABLE_CONTROLNET=true" \
  --env "WAN_720P=true" \
  --env "ENABLE_WAN22_DISTILL=true" \
  --env "ENABLE_I2V=true" \
  --env "ENABLE_ILLUSTRIOUS=true" \
  --env "ENABLE_R2_SYNC=true" \
  --env "GPU_TIER=consumer" \
  --env "GPU_MEMORY_MODE=auto" \
  --env "R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}"
```

### Minimal Command (Basic Usage)

```bash
~/.local/bin/runpodctl create pod \
  --name "hearmeman-minimal" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA GeForce RTX 4090" \
  --containerDiskSize 20 \
  --volumeSize 15 \
  --ports "8188/http" \
  --env "ENABLE_VIBEVOICE=true" \
  --env "WAN_720P=true"
```

### GPU-Specific Commands

**RTX 4090 (24GB Consumer):**
```bash
--env "GPU_TIER=consumer"
--env "GPU_MEMORY_MODE=auto"
```

**RTX A6000 (48GB Prosumer):**
```bash
--gpuType "NVIDIA RTX A6000" \
--volumeSize 100 \
--secureCloud \
--env "GPU_TIER=prosumer" \
--env "GPU_MEMORY_MODE=auto"
```

**A100 80GB (Datacenter):**
```bash
--gpuType "NVIDIA A100 80GB" \
--volumeSize 150 \
--secureCloud \
--env "GPU_TIER=datacenter" \
--env "GPU_MEMORY_MODE=full"
```

## 3. Secret Management

### RunPod Secrets Configuration

| Secret Name | Value | Purpose |
|-------------|-------|---------|
| `r2_access_key` | R2 Access Key ID | R2 bucket authentication |
| `r2_secret_key` | R2 Secret Access Key | R2 bucket authentication |
| `civitai_key` | CivitAI API Token | Rate-limited model downloads |

### Referencing Secrets in Pod Template

```bash
--env "R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}"
--env "R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}"
--env "CIVITAI_API_KEY={{RUNPOD_SECRET_civitai_key}}"
```

## 4. Container Startup on RunPod

### Startup Sequence

```
+------------------+
| 1. Image Pull    | ghcr.io image pulled (~11GB)
+------------------+
         |
         v
+------------------+
| 2. GPU Detection | nvidia-smi queries VRAM
+------------------+
         |
         v
+------------------+
| 3. Storage Mode  | Detects ephemeral vs persistent
+------------------+
         |
         v
+------------------+
| 4. SSH Config    | If PUBLIC_KEY set, enables SSH
+------------------+
         |
         v
+------------------+
| 5. JupyterLab    | If JUPYTER_PASSWORD set, starts
+------------------+
         |
         v
+------------------+
| 6. Model Download| Calls download_models.sh
+------------------+
         |
         v
+------------------+
| 7. R2 Sync       | Starts r2_sync.sh daemon
+------------------+
         |
         v
+------------------+
| 8. ComfyUI       | Starts on port 8188
+------------------+
```

## 5. Datacenter Considerations

### Datacenter Speed Comparison

| Region | Startup Time | Network Speed | Recommendation |
|--------|--------------|---------------|----------------|
| **US (Secure Cloud)** | ~37 sec | 51 MB/s | **Recommended** |
| US (Community) | ~1 sec | Variable | Good for testing |
| EU (CZ) | 4+ min | Unknown | Avoid for speed-critical |
| UAE | 2+ min | Slow | Avoid |

### Model Download Speeds

| Model | Size | Time (Secure Cloud) |
|-------|------|---------------------|
| WAN 2.1 720p | 25 GB | ~8 min @ 51 MB/s |
| WAN 2.2 Distilled | 28 GB | ~9 min @ 51 MB/s |
| VibeVoice-Large | 18 GB | ~6 min @ 51 MB/s |
| Illustrious | 6.5 GB | ~2 min @ 51 MB/s |

### Pod Startup Time Breakdown

| Phase | Time (US Secure) | Time (US Community) |
|-------|------------------|---------------------|
| Image pull | ~10 sec | ~1 sec |
| Container init | ~5 sec | Instant |
| GPU detection | ~2 sec | Instant |
| Model downloads | ~15-20 min | ~15-20 min |
| ComfyUI start | ~5 sec | ~5 sec |
| **Total (no cache)** | **~20 min** | **~18 min** |
| **Total (cached)** | **~1 min** | **~30 sec** |

## 6. Environment Variable Reference

### Build-time Variables (Dockerfile)

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_R2_SYNC` | false | Enable R2 output sync daemon |
| `R2_BUCKET` | runpod | R2 bucket name |
| `BAKE_WAN_720P` | false | Pre-bake WAN models into image |
| `BAKE_WAN_480P` | false | Pre-bake WAN 480p models |
| `BAKE_ILLUSTRIOUS` | false | Pre-bake Illustrious model |

### Runtime Variables (RunPod Template)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_VIBEVOICE` | visible | false | Enable VibeVoice TTS |
| `VIBEVOICE_MODEL` | visible | Large | VibeVoice model size |
| `WAN_720P` | visible | false | Enable WAN 2.1 T2V 720p |
| `ENABLE_ILLUSTRIOUS` | visible | false | Enable Realism Illustrious |
| `ENABLE_R2_SYNC` | visible | false | Enable R2 output sync |
| `R2_ENDPOINT` | visible | - | R2 endpoint URL |
| `R2_ACCESS_KEY_ID` | secret | - | R2 access key |
| `R2_SECRET_ACCESS_KEY` | secret | - | R2 secret key |
| `GPU_TIER` | visible | consumer | GPU tier |
| `PUBLIC_KEY` | secret | - | SSH public key |
| `JUPYTER_PASSWORD` | secret | - | JupyterLab password |

## 7. Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| CUDA out of memory | VRAM exceeded | Increase --medvram or use smaller models |
| GPU not detected | nvidia-smi failed | Contact RunPod support |
| Model download timeout | Network slow | Use US datacenter, enable R2 cache |
| R2 upload fails | Invalid credentials | Verify secrets are set correctly |
| SSH not working | PUBLIC_KEY not set | Add public key to template |

### Verification Commands

```bash
# Check GPU
nvidia-smi

# Check GPU VRAM detection
nvidia-smi --query-gpu=memory.total --format=csv

# Verify ComfyUI running
curl -s http://localhost:8188/api/system_stats | jq

# Check R2 sync daemon
ps aux | grep r2_sync

# Test R2 connection
python3 /upload_to_r2.py --test

# Verify models downloaded
ls -la /workspace/ComfyUI/models/diffusion_models/
```

---

## Appendices

### Appendix A: Complete Environment Variables Matrix

| Variable | Default | Category | VRAM Impact | Secret |
|----------|---------|----------|-------------|--------|
| ENABLE_VIBEVOICE | true | TTS | ~18GB | No |
| VIBEVOICE_MODEL | Large | TTS | Varies | No |
| WAN_720P | false | Video | ~25GB | No |
| WAN_480P | false | Video | ~12GB | No |
| ENABLE_I2V | false | Video | ~14GB | No |
| ENABLE_WAN22_DISTILL | false | Video | ~28GB | No |
| ENABLE_ILLUSTRIOUS | false | Image | ~7GB | No |
| ENABLE_ZIMAGE | false | Image | ~21GB | No |
| ENABLE_CONTROLNET | true | Control | ~3.6GB | No |
| ENABLE_R2_SYNC | false | Storage | None | No |
| R2_ENDPOINT | - | Storage | - | No |
| R2_BUCKET | runpod | Storage | - | No |
| R2_ACCESS_KEY_ID | - | Storage | - | **Yes** |
| R2_SECRET_ACCESS_KEY | - | Storage | - | **Yes** |
| GPU_TIER | consumer | System | - | No |
| GPU_MEMORY_MODE | auto | System | - | No |
| PUBLIC_KEY | - | Access | - | **Yes** |
| JUPYTER_PASSWORD | - | Access | - | **Yes** |
| CIVITAI_API_KEY | - | Downloads | - | **Yes** |

### Appendix B: Model File Reference

| Model | Enable Variable | Source | Size |
|-------|-----------------|--------|------|
| VibeVoice-1.5B | ENABLE_VIBEVOICE + VIBEVOICE_MODEL=1.5B | HuggingFace | ~4GB |
| VibeVoice-Large | ENABLE_VIBEVOICE | HuggingFace | ~18GB |
| VibeVoice-Large-Q8 | ENABLE_VIBEVOICE + VIBEVOICE_MODEL=Large-Q8 | HuggingFace | ~21GB |
| WAN 2.1 720p T2V | WAN_720P | HuggingFace | ~25GB |
| WAN 2.1 720p I2V | WAN_720P + ENABLE_I2V | HuggingFace | +14GB |
| WAN 2.1 480p T2V | WAN_480P | HuggingFace | ~12GB |
| WAN 2.2 Distilled I2V | ENABLE_WAN22_DISTILL | HuggingFace | ~28GB |
| Realism Illustrious | ENABLE_ILLUSTRIOUS | CivitAI | ~7GB |
| Z-Image Turbo | ENABLE_ZIMAGE | HuggingFace | ~21GB |
| ControlNet (5) | ENABLE_CONTROLNET | HuggingFace | ~3.6GB |
| Genfocus | ENABLE_GENFOCUS | HuggingFace | ~12GB |
| Qwen-Edit | ENABLE_QWEN_EDIT | unsloth | ~13-54GB |
| VACE | ENABLE_VACE | HuggingFace | ~28GB |
| SteadyDancer | ENABLE_STEADYDANCER | HuggingFace | ~33GB |
| SCAIL | ENABLE_SCAIL | HuggingFace | ~28GB |
| Fun InP | ENABLE_FUN_INP | HuggingFace | ~28GB |
| FlashPortrait | ENABLE_FLASHPORTRAIT | HuggingFace | ~60GB |
| StoryMem | ENABLE_STORYMEM | HuggingFace | ~20GB+ |
| InfCam | ENABLE_INFCAM | HuggingFace | ~50GB+ |

### Appendix C: Port Reference Summary

| Port | Protocol | Service | Access | Security |
|------|----------|---------|--------|----------|
| 22 | TCP | SSH | SSH client | Key-based auth only |
| 8188 | HTTP | ComfyUI | Browser, API | Behind auth proxy |
| 8888 | HTTP | JupyterLab | Browser | Token required |
| 8000 | TCP | Chatterbox API | API calls | Internal only |
| 8020 | TCP | XTTS API | API calls | Internal only |

### Appendix D: Quick Start Commands

**Local Docker Development:**
```bash
cd docker
docker compose build
docker compose up -d
```

**Deploy to RunPod:**
```bash
~/.local/bin/runpodctl create pod \
  --name "hearmeman" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA GeForce RTX 4090" \
  --volumeSize 50 \
  --ports "8188/http" \
  --env "ENABLE_VIBEVOICE=true" \
  --env "WAN_720P=true"
```

**Test R2 Upload Locally:**
```bash
export R2_ENDPOINT=https://...
export R2_ACCESS_KEY_ID=your_key
export R2_SECRET_ACCESS_KEY=your_secret
python docker/upload_to_r2.py --test
```

**Manual Docker Build and Push:**
```bash
cd docker
docker tag hearmeman-extended:local ghcr.io/oz/hearmeman-extended:latest
echo $GITHUB_TOKEN | docker login ghcr.io -u oz --password-stdin
docker push ghcr.io/oz/hearmeman-extended:latest
```

---

## Document Information

| Field | Value |
|-------|-------|
| **Generated** | 2026-01-17 |
| **Sections** | 6 |
| **Agents Used** | ma (MiniMax Agent), hc (Headless Claude) |
| **Models** | claude-sonnet-4-5-20250929, MiniMax-M2.1 |
| **Source Files** | 6 research sections + tracking.json |
| **Output** | master-documentation.md |

### Source Section Files

1. `section-001-docker-infrastructure.md` - Docker infrastructure and custom nodes
2. `section-002-ai-models.md` - AI model environment variables and paths
3. `section-003-tts-voice-systems.md` - TTS systems documentation
4. `section-004-video-image-generation.md` - Video/image generation workflows
5. `section-005-r2-storage-sync.md` - R2 cloud storage sync
6. `section-006-deployment-ci-cd.md` - Deployment and CI/CD procedures

---

*Document compiled automatically from research sections. For updates, regenerate from source sections using the tracking system.*
