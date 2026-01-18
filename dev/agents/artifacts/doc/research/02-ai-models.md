---
author: $USER
model: claude-haiku-4.5-20251001
date: 2026-01-17 13:45
task: Research AI models and configuration for RunPod system
---

# RunPod AI Models Research Document

## Executive Summary

This document provides comprehensive documentation of all AI models deployed in the RunPod custom template system. The system supports multiple AI workflows including text-to-image generation, video generation, text-to-speech, and specialized image editing. Models are organized by GPU tier (Consumer 8-24GB, Prosumer 24-48GB, and Datacenter 48-80GB+) to optimize resource allocation and performance.

---

## 1. Environment Variables Reference

### 1.1 Model Toggles

All models are controlled via environment variables in `/home/oz/projects/2025/oz/12/runpod/docker/.env` and `docker-compose.yml`.

| Variable | Default | Size | Description |
|----------|---------|------|-------------|
| `ENABLE_VIBEVOICE` | `true` | 18GB | VibeVoice-Large TTS voice cloning |
| `ENABLE_ZIMAGE` | `false` | 21GB | Z-Image Turbo txt2img generation |
| `ENABLE_ILLUSTRIOUS` | `false` | 6.5GB | Realism Illustrious photorealistic images |
| `ENABLE_XTTS` | `false` | 1.8GB | XTTS v2 multilingual TTS |
| `ENABLE_CONTROLNET` | `true` | 3.6GB | ControlNet preprocessors (canny, depth, openpose) |
| `ENABLE_I2V` | `false` | 14GB | Image-to-Video (I2V) base |
| `ENABLE_VACE` | `false` | 28GB | WAN VACE video editing |
| `ENABLE_FUN_INP` | `false` | 28GB | WAN Fun InP frame interpolation |
| `ENABLE_STEADYDANCER` | `false` | 33GB | SteadyDancer dance video generation |
| `ENABLE_SCAIL` | `false` | 28GB | SCAIL facial mocap |
| `WAN_720P` | `false` | 25GB | WAN 2.1 T2V 14B video generation (720p) |
| `WAN_480P` | `false` | 12GB | WAN 2.1 T2V 1.3B video generation (480p) |
| `ENABLE_WAN22_DISTILL` | `false` | 28GB | WAN 2.2 TurboDiffusion I2V (4-step inference) |

### 1.2 Model Variants

| Variable | Default | Options | Description |
|----------|---------|---------|-------------|
| `VIBEVOICE_MODEL` | `Large` | `1.5B`, `Large`, `Large-Q8` | VibeVoice model size variant |
| `CONTROLNET_MODELS` | `canny,depth,openpose` | `canny`, `depth`, `openpose`, `lineart`, `normalbae` | ControlNet model types to download |
| `QWEN_EDIT_MODEL` | `Q4_K_M` | `Q4_K_M`, `Q5_K_M`, `Q6_K`, `Q8_0`, `Q2_K`, `Q3_K_M`, `full` | Qwen image editing model quantization |

### 1.3 Integration Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_CIVITAI` | `true` | Enable CivitAI LoRA downloads |
| `CIVITAI_LORAS` | `1906687,1736657` | Comma-separated CivitAI version IDs |
| `ILLUSTRIOUS_LORAS` | (empty) | Illustrious-compatible LoRA version IDs |
| `CIVITAI_API_KEY` | `28dae357e46b6cd01c62b3a49631e442` | API key for NSFW/gated model downloads |

### 1.4 ComfyUI Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `COMFYUI_PORT` | `8188` | ComfyUI web interface port |
| `STORAGE_MODE` | `persistent` | Storage mode: `persistent`, `ephemeral`, `auto` |
| `UPDATE_NODES_ON_START` | `false` | Update custom nodes on startup |
| `GPU_TIER` | `consumer` | GPU tier: `consumer`, `prosumer`, `datacenter` |
| `GPU_MEMORY_MODE` | `auto` | Memory mode: `auto`, `full`, `model_cpu_offload`, `sequential_cpu_offload` |

---

## 2. Complete Model Specifications

### 2.1 Storage Requirements Summary

| Component | Disk Size | VRAM | Notes |
|-----------|-----------|------|-------|
| **Docker Image** | ~12GB | N/A | Base with custom nodes |
| **VibeVoice-Large** | ~18GB | 8-12GB (1.5B), 16GB+ (7B) | Multi-speaker TTS with voice cloning |
| **XTTS v2** | ~1.8GB | 4-8GB | Multilingual TTS |
| **Z-Image Turbo** | ~21GB | ~16GB | Fast text-to-image |
| **Realism Illustrious** | ~6.5GB | 8-12GB | SDXL-based photorealism |
| **WAN 2.1 720p T2V** | ~25GB | 20-24GB | Text-to-video 14B model |
| **WAN 2.1 480p T2V** | ~12GB | 12-16GB | Smaller text-to-video model |
| **WAN 2.2 TurboDistilled** | ~28GB | 24GB | 4-step I2V inference |
| **SteadyDancer** | ~33GB | 28-32GB | Dance video generation |
| **SCAIL** | ~28GB | 24-28GB | Facial mocap |
| **VACE 14B** | ~28GB | 24-28GB | Video editing |
| **Fun InP 14B** | ~28GB | 24-28GB | Frame interpolation |
| **ControlNet (5 models)** | ~3.6GB | 4-8GB | Preprocessor models |
| **Qwen-Image-Edit** | 4-54GB | 8-54GB | Instruction-based editing (quantized available) |
| **Genfocus** | ~12GB | ~12GB | Depth-of-field refocusing |
| **MVInverse** | ~8GB | ~8GB | Multi-view inverse rendering |
| **FlashPortrait** | ~60GB | 30-60GB | Portrait animation |
| **StoryMem** | ~20GB+ | 20-24GB | Multi-shot video storytelling |
| **InfCam** | ~50GB+ | 50GB+ | Camera-controlled video generation |
| **Total (ALL)** | **~230GB** | | |
| **Typical Config** | **~80-120GB** | | |

### 2.2 Model Comparison Table

| Model | Type | Source | Size | VRAM | Key Features |
|-------|------|--------|------|------|--------------|
| **VibeVoice 1.5B** | TTS | HuggingFace | 18GB | 8-12GB | Multi-speaker, voice cloning, LoRA support |
| **VibeVoice 7B** | TTS | HuggingFace | 18GB | 16GB+ | Same as 1.5B with more parameters |
| **VibeVoice Large-Q8** | TTS | HuggingFace | 18GB | 12-16GB | Quantized 8-bit version |
| **XTTS v2** | TTS | Coqui | 1.8GB | 4-8GB | 17 languages, real-time streaming |
| **Chatterbox TTS** | TTS | Resemble AI | ~2GB | 2-4GB | Zero-shot cloning, emotion control |
| **Z-Image Turbo** | txt2img | Tongyi-MAI | 21GB | ~16GB | Fast image generation |
| **Realism Illustrious** | txt2img | CivitAI | 6.5GB | 8-12GB | SDXL-based photorealism |
| **WAN 2.1 T2V 14B** | t2v | HuggingFace | 25GB | 20-24GB | Text-to-video, 720p |
| **WAN 2.1 T2V 1.3B** | t2v | HuggingFace | 12GB | 12-16GB | Smaller text-to-video, 480p |
| **WAN 2.2 Distilled** | i2v | HuggingFace | 28GB | 24GB | 4-step inference, TurboDiffusion |
| **WAN VACE 14B** | video | Wan-AI | 28GB | 24-28GB | Video editing and manipulation |
| **WAN Fun InP 14B** | interp | Wan-AI | 28GB | 24-28GB | Frame interpolation (first-last) |
| **SteadyDancer** | dance | HuggingFace | 33GB | 28-32GB | Dance video generation |
| **SCAIL** | mocap | zai-org | 28GB | 24-28GB | Facial motion capture |
| **ControlNet Canny** | control | HuggingFace | ~720MB | 4-8GB | Edge detection guidance |
| **ControlNet Depth** | control | HuggingFace | ~720MB | 4-8GB | Depth map guidance |
| **ControlNet OpenPose** | control | HuggingFace | ~720MB | 4-8GB | Pose estimation guidance |
| **ControlNet LineArt** | control | HuggingFace | ~720MB | 4-8GB | Line drawing guidance |
| **ControlNet NormalBae** | control | HuggingFace | ~720MB | 4-8GB | Surface normal guidance |
| **Qwen-Image-Edit Q4_K_M** | edit | unsloth | ~13GB | 8-16GB | Instruction-based editing |
| **Qwen-Image-Edit Q8_0** | edit | unsloth | ~22GB | 16-24GB | Higher quality quantized |
| **Qwen-Image-Edit Full** | edit | Qwen | 54GB | 48GB+ | Full precision model |
| **Genfocus** | effect | nycu-cplab | 12GB | ~12GB | Bokeh and deblur effects |
| **MVInverse** | render | GitHub | 8GB | ~8GB | Multi-view 3D reconstruction |
| **FlashPortrait** | anim | HuggingFace | 60GB | 30-60GB | Portrait animation |
| **StoryMem** | story | HuggingFace | 20GB+ | 20-24GB | Multi-shot video narratives |
| **InfCam** | camera | emjay73 | 50GB+ | 50GB+ | Camera-controlled generation |

---

## 3. Model Download Sources and Paths

### 3.1 HuggingFace Repositories

| Model | Repository | Files |
|-------|-----------|-------|
| VibeVoice 1.5B | `microsoft/VibeVoice-1.5B` | Full snapshot |
| VibeVoice Large | `aoi-ot/VibeVoice-Large` | Full snapshot |
| VibeVoice Large-Q8 | `FabioSarracino/VibeVoice-Large-Q8` | Full snapshot |
| Z-Image Turbo | `Tongyi-MAI/Z-Image-Turbo` | `qwen_3_4b.safetensors`, `z_image_turbo_bf16.safetensors`, `ae.safetensors` |
| WAN 2.1 Repackaged | `Comfy-Org/Wan_2.1_ComfyUI_repackaged` | Text encoders, VAE, diffusion models |
| WAN 2.2 Repackaged | `Comfy-Org/Wan_2.2_ComfyUI_Repackaged` | Distilled diffusion models |
| SteadyDancer | `MCG-NJU/SteadyDancer-14B` | `Wan21_SteadyDancer_fp16.safetensors` |
| SCAIL | `zai-org/SCAIL-Preview` | Git LFS repository |
| ControlNet v1-1 | `comfyanonymous/ControlNet-v1-1_fp16_safetensors` | Various ControlNet models |
| CLIP Vision | `Comfy-Org/sigclip_vision_384` | `sigclip_vision_patch14_384.safetensors` |
| WAN VACE 14B | `Wan-AI/Wan2.1-VACE-14B` | `wan2.1_vace_14B_fp16.safetensors` |
| WAN Fun InP 14B | `Wan-AI/Wan2.2-Fun-InP-14B` | `wan2.2_fun_inp_14B_fp16.safetensors` |
| Genfocus | `nycu-cplab/Genfocus-Model` | `bokehNet.safetensors`, `deblurNet.safetensors`, `checkpoints/depth_pro.pt` |
| Qwen-Edit GGUF | `unsloth/Qwen-Image-Edit-2511-GGUF` | Quantized GGUF files |
| FlashPortrait | `FrancisRing/FlashPortrait` | Full snapshot |
| StoryMem | `Kevin-thu/StoryMem` | LoRA variants |
| InfCam | `emjay73/InfCam` | Full snapshot |
| UniDepth-v2 | `lpiccinelli/unidepth-v2-vitl14` | Depth estimation |

### 3.2 CivitAI Models

| Model | Version ID | Type | Size | Notes |
|-------|-----------|------|------|-------|
| Realism Illustrious v5.0 | `2091367` | Checkpoint | 6.46GB | FP16 |
| Illustrious Positive Embedding | `1153237` | Embedding | 352KB | Stable Yogis |
| Illustrious Negative Embedding | `1153212` | Embedding | 536KB | Stable Yogis |
| CivitAI LoRA 1 | `1906687` | LoRA | varies | User-configurable |
| CivitAI LoRA 2 | `1736657` | LoRA | varies | User-configurable |

### 3.3 Download Locations

All models are stored in `/workspace/ComfyUI/models/` with the following structure:

```
/workspace/ComfyUI/models/
├── checkpoints/
│   └── realismIllustriousByStableYogi_v50FP16.safetensors
├── controlnet/
│   ├── control_v11p_sd15_canny_fp16.safetensors
│   ├── control_v11f1p_sd15_depth_fp16.safetensors
│   ├── control_v11p_sd15_openpose_fp16.safetensors
│   ├── control_v11p_sd15_lineart_fp16.safetensors
│   └── control_v11p_sd15_normalbae_fp16.safetensors
├── diffusion_models/
│   ├── wan2.1_t2v_14B_fp8_e4m3fn.safetensors
│   ├── wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors
│   ├── wan2.1_t2v_1.3B_fp16.safetensors
│   ├── wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors
│   ├── wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors
│   ├── wan2.1_vace_14B_fp16.safetensors
│   ├── wan2.2_fun_inp_14B_fp16.safetensors
│   └── Wan21_SteadyDancer_fp16.safetensors
├── text_encoders/
│   ├── umt5_xxl_fp8_e4m3fn_scaled.safetensors
│   └── qwen_3_4b.safetensors
├── vae/
│   ├── wan_2.1_vae.safetensors
│   └── ae.safetensors
├── clip_vision/
│   ├── clip_vision_h.safetensors
│   └── sigclip_vision_patch14_384.safetensors
├── vibevoice/
│   ├── VibeVoice-1.5B/
│   ├── VibeVoice-Large/
│   └── tokenizer/
├── embeddings/
│   ├── Stable_Yogis_Illustrious_Positives.safetensors
│   └── Stable_Yogis_Illustrious_Negatives.safetensors
├── loras/
│   ├── [civitai-model_*.safetensors]
│   └── [illustrious-lora_*.safetensors]
├── qwen/
│   └── qwen-image-edit-2511-[QUANT].gguf
├── genfocus/
│   ├── bokehNet.safetensors
│   ├── deblurNet.safetensors
│   └── depth_pro.pt
├── mvinverse/
│   └── mvinverse/
├── flashportrait/
│   └── FlashPortrait/
├── storymem/
│   └── StoryMem/
└── infcam/
    ├── InfCam/
    └── unidepth-v2-vitl14/
```

### 3.4 Qwen Tokenizer Path

```
/workspace/ComfyUI/models/vibevoice/tokenizer/
├── tokenizer_config.json
├── vocab.json
├── merges.txt
└── tokenizer.json
```

---

## 4. Performance Characteristics

### 4.1 Generation Speeds (Estimated)

| Model | Task | Speed | Notes |
|-------|------|-------|-------|
| **Realism Illustrious** | txt2img | ~5 sec | 768px on RTX 4090 |
| **WAN 2.1 720p T2V** | t2v 5s | ~2-5 min | 720p video generation |
| **WAN 2.2 Distilled** | i2v 4-step | ~30-60 sec | Much faster than standard |
| **VibeVoice** | TTS | ~1-2 sec | Real-time synthesis |
| **XTTS v2** | TTS | ~200ms | Streaming latency |
| **ControlNet + SDXL** | guided img | ~10 sec | Depends on resolution |
| **Z-Image Turbo** | txt2img | ~3-5 sec | Fast generation |
| **Qwen-Edit** | image edit | ~10-30 sec | Depends on size |

### 4.2 VRAM Requirements by GPU Tier

#### Consumer Tier (8-24GB VRAM)
- **Recommended**: RTX 4080 Super (16GB), RTX 4090 (24GB)
- Compatible models:
  - VibeVoice 1.5B (8-12GB)
  - VibeVoice Large-Q8 (12-16GB)
  - Realism Illustrious (8-12GB)
  - Z-Image Turbo (~16GB)
  - WAN 480p T2V 1.3B (12-16GB)
  - ControlNet models (4-8GB)
  - Qwen-Edit quantized (8-16GB)
  - Genfocus (~12GB)
  - MVInverse (~8GB)

#### Prosumer Tier (24-48GB VRAM)
- **Recommended**: A6000 (48GB), L40S (48GB)
- Additional models:
  - VibeVoice Large (16GB+)
  - WAN 720p T2V 14B (20-24GB)
  - WAN 2.2 Distilled (24GB)
  - Qwen-Edit Q8_0 (16-24GB)
  - StoryMem (20-24GB)
  - FlashPortrait (30GB with CPU offload)

#### Datacenter Tier (48-80GB VRAM)
- **Recommended**: A100 80GB, H100 80GB
- Additional models:
  - Qwen-Edit Full (48GB+)
  - FlashPortrait Full (60GB)
  - InfCam (50GB+)

### 4.3 Auto-Detection Configuration

The `start.sh` script automatically configures memory settings based on detected VRAM:

| Detected VRAM | GPU Tier | Memory Mode | ComfyUI Args |
|---------------|----------|-------------|--------------|
| <8GB | consumer | sequential_cpu_offload | `--lowvram --cpu-vae --force-fp16` |
| 8-12GB | consumer | sequential_cpu_offload | `--lowvram --force-fp16` |
| 12-16GB | consumer | sequential_cpu_offload | `--medvram --cpu-text-encoder --force-fp16` |
| 16-24GB | consumer | model_cpu_offload | `--normalvram --force-fp16` |
| 24-48GB | prosumer | full | (none) |
| 48GB+ | datacenter | full | (none) |

---

## 5. Model Selection Guide

### 5.1 By Use Case

#### Text-to-Image
| Use Case | Recommended Model | VRAM | Notes |
|----------|-------------------|------|-------|
| Photorealistic | Realism Illustrious | 8-12GB | Best for realistic images |
| Fast generation | Z-Image Turbo | ~16GB | Quick iterations |
| General purpose | SDXL + ControlNet | 8-12GB | Versatile with guidance |

#### Text-to-Video
| Use Case | Recommended Model | VRAM | Notes |
|----------|-------------------|------|-------|
| High quality 720p | WAN 2.1 T2V 14B | 20-24GB | Default video gen |
| Fast iterations | WAN 2.1 T2V 1.3B | 12-16GB | 480p, lower quality |
| Image-to-Video | WAN 2.2 Distilled | 24GB | 4-step, requires input image |
| Long sequences | WAN VACE 14B | 24-28GB | Video editing capabilities |

#### Text-to-Speech
| Use Case | Recommended Model | VRAM | Notes |
|----------|-------------------|------|-------|
| Voice cloning | VibeVoice Large | 16GB+ | Multi-speaker, LoRA support |
| Low VRAM | VibeVoice 1.5B | 8-12GB | Smaller model variant |
| Multilingual | XTTS v2 | 4-8GB | 17 languages, streaming |
| Emotion control | Chatterbox TTS | 2-4GB | Zero-shot, emotion styling |

#### Image Editing
| Use Case | Recommended Model | VRAM | Notes |
|----------|-------------------|------|-------|
| Instruction-based | Qwen-Edit Q4_K_M | 8-16GB | Natural language editing |
| High quality | Qwen-Edit Q8_0 | 16-24GB | Better detail preservation |
| Maximum quality | Qwen-Edit Full | 48GB+ | Full precision |

#### Special Effects
| Use Case | Recommended Model | VRAM | Notes |
|----------|-------------------|------|-------|
| Bokeh/Refocus | Genfocus | ~12GB | Depth-of-field effects |
| Multi-view 3D | MVInverse | ~8GB | 3D reconstruction from images |
| Portrait animation | FlashPortrait | 30-60GB | Lip-sync, expressions |

### 5.2 By GPU Configuration

#### RTX 4080 Super (16GB VRAM)
1. **Primary**: Realism Illustrious + ControlNet
2. **Secondary**: VibeVoice 1.5B or Large-Q8
3. **Optional**: WAN 480p T2V 1.3B

#### RTX 4090 (24GB VRAM)
1. **Primary**: Realism Illustrious + ControlNet
2. **Video**: WAN 720p T2V 14B
3. **TTS**: VibeVoice Large
4. **Editing**: Qwen-Edit Q8_0

#### A6000/L40S (48GB VRAM)
1. **Everything in 16GB config** +
2. **WAN 2.2 Distilled I2V**
3. **WAN VACE/Fun InP**
4. **Qwen-Edit Full**
5. **StoryMem**

#### A100/H100 (80GB VRAM)
1. **All models available** +
2. **FlashPortrait Full**
3. **InfCam**
4. **Multiple concurrent workflows**

---

## 6. Configuration Files

### 6.1 File Locations

| File | Path | Purpose |
|------|------|---------|
| Environment | `/home/oz/projects/2025/oz/12/runpod/docker/.env` | Model toggles and settings |
| Compose Config | `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml` | Container orchestration |
| Model Downloader | `/home/oz/projects/2025/oz/12/runpod/docker/download_models.sh` | On-demand model downloads |
| Startup Script | `/home/oz/projects/2025/oz/12/runpod/docker/start.sh` | Initialization and GPU detection |
| R2 Sync | `/home/oz/projects/2025/oz/12/runpod/docker/r2_sync.sh` | Output persistence to Cloudflare R2 |
| R2 Uploader | `/home/oz/projects/2025/oz/12/runpod/docker/upload_to_r2.py` | Manual file upload utility |

### 6.2 Download Modes

The `download_models.sh` script supports multiple modes:

| Mode | Environment Variable | Description |
|------|---------------------|-------------|
| **Normal** | (default) | Downloads missing models with progress |
| **Dry Run** | `DRY_RUN=true` | Shows what would be downloaded without downloading |
| **Resume** | (automatic) | Resumes partial downloads if file exists but incomplete |
| **Timeout** | `DOWNLOAD_TIMEOUT=1800` | 30-minute default per file |

### 6.3 Storage Mode Detection

The system auto-detects storage mode:

| Mode | Detection | Behavior |
|------|-----------|----------|
| **persistent** | `/workspace` is a mountpoint | Models persist across restarts |
| **ephemeral** | `/workspace` not mountpoint | Models lost on restart (fresh download each time) |
| **auto** | (default) | Auto-detects based on `/workspace` mount status |

---

## 7. Integration Details

### 7.1 TTS API Endpoints

#### XTTS v2 Standalone Server
- **Port**: 8020
- **Swagger UI**: http://localhost:8020/docs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tts_to_audio/` | POST | Returns audio bytes directly |
| `/tts_to_file` | POST | Saves to server file path |
| `/tts_stream` | POST | Streams audio chunks |
| `/speakers_list` | GET | List available speakers |
| `/languages` | GET | List supported languages |

**Example**:
```bash
curl -X POST "http://localhost:8020/tts_to_audio/" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "speaker_wav": "female", "language": "en"}' \
  -o output.wav
```

#### Chatterbox TTS
- **Port**: 8000
- **OpenAI-compatible API**: http://localhost:8000/v1/audio/speech

**Example**:
```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model": "chatterbox", "input": "Hello world", "voice": "default"}' \
  -o speech.wav
```

### 7.2 ComfyUI Workflow Validation

All workflow nodes must have explicit values (no "default" placeholders):

| Node Type | Required Field | Valid Values |
|-----------|---------------|--------------|
| CLIPLoader | `type` | `qwen_image`, `stable_diffusion`, `flux` (NOT `default`) |
| KSampler | `sampler_name` | `euler`, `dpmpp_2m`, `dpmpp_sde`, etc. |
| KSampler | `scheduler` | `simple`, `karras`, `sgm_uniform` (NOT `res_multistep`) |
| UNETLoader | `unet_name` | Exact filename match |
| VAELoader | `vae_name` | Exact filename match |

### 7.3 R2 Output Sync

RunPod ephemeral storage requires automatic upload:

| Variable | Value | Notes |
|----------|-------|-------|
| `ENABLE_R2_SYNC` | `true` | Enables daemon |
| `R2_ENDPOINT` | `https://<account>.eu.r2.cloudflarestorage.com` | Your R2 endpoint |
| `R2_BUCKET` | `runpod` | Target bucket |
| `R2_ACCESS_KEY_ID` | `{{RUNPOD_SECRET_r2_access_key}}` | Use RunPod secrets |
| `R2_SECRET_ACCESS_KEY` | `{{RUNPOD_SECRET_r2_secret_key}}` | Use RunPod secrets |

**Output Organization**: `s3://runpod/outputs/YYYY-MM-DD/filename`

---

## 8. Dependencies and Requirements

### 8.1 Python Dependencies

Critical dependencies for specific models:

```python
# VibeVoice requirements (in Dockerfile)
bitsandbytes>=0.48.1  # Critical for Q8 model
transformers>=4.51.3
accelerate
peft
librosa
soundfile
```

### 8.2 Hardware Requirements

**Minimum Local Setup**:
- 250GB SSD (NVMe recommended)
- 32GB RAM
- 24GB VRAM (RTX 4090 or equivalent)

**Recommended**:
- 500GB+ SSD for all models
- 64GB RAM for prosumer/datacenter models
- 48GB+ VRAM for full model suite

### 8.3 GPU Compatibility

| GPU Family | Supported | Notes |
|-----------|-----------|-------|
| RTX 4080 Super | Yes | Consumer tier (16GB) |
| RTX 4090 | Yes | Consumer tier (24GB) |
| A6000 | Yes | Prosumer tier (48GB) |
| L40S | Yes | Prosumer tier (48GB) |
| A100 40GB | Partial | Limited to smaller models |
| A100 80GB | Yes | Datacenter tier |
| H100 | Yes | Datacenter tier |

---

## 9. Model Download Commands

### 9.1 Manual Download Examples

```bash
# Download a single model
wget -c -O /workspace/ComfyUI/models/checkpoints/model.safetensors \
  "https://huggingface.co/repo/resolve/main/file.safetensors"

# Download from CivitAI
curl -L -o /workspace/ComfyUI/models/loras/lora.safetensors \
  "https://civitai.com/api/download/models/VERSION_ID?token=API_KEY"

# Dry run to see what would be downloaded
DRY_RUN=true /download_models.sh

# Test R2 connection
python3 /upload_to_r2.py --test
```

### 9.2 Container Startup with Models

```bash
# Start with default models
docker compose up -d

# Start with additional models
ENABLE_ILLUSTRIOUS=true \
ENABLE_VACE=true \
ENABLE_WAN22_DISTILL=true \
docker compose up -d

# Full model suite (requires 48GB+ VRAM)
ENABLE_ALL_MODELS=true \
GPU_TIER=datacenter \
docker compose up -d
```

---

## 10. Troubleshooting

### 10.1 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Out of memory | VRAM too low for model | Use smaller model or quantized version |
| Model not found | Path mismatch | Verify exact filename in workflow |
| Slow downloads | Network or storage | Use persistent storage, check R2 endpoint |
| XTTS fails | Transformer version conflict | Use separate container for XTTS |
| ControlNet errors | Missing preprocessor | Ensure ControlNet models are downloaded |
| Qwen-Edit fails | Wrong quantization | Check QWEN_EDIT_MODEL matches VRAM |

### 10.2 Verification Commands

```bash
# Check downloaded models
ls -lh /workspace/ComfyUI/models/*/

# Check GPU VRAM
nvidia-smi

# Test R2 upload
python3 /upload_to_r2.py --test

# View download logs
tail -f /var/log/download_models.log

# Check R2 sync status
tail -f /var/log/r2_sync.log
```

---

## References

- **Project Repository**: `/home/oz/projects/2025/oz/12/runpod/`
- **Docker Configuration**: `/home/oz/projects/2025/oz/12/runpod/docker/`
- **ComfyUI**: https://github.com/comfyanonymous/ComfyUI
- **VibeVoice-ComfyUI**: https://github.com/Enemyx-net/VibeVoice-ComfyUI
- **WAN 2.1 Models**: https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged
- **RunPod Documentation**: https://docs.runpod.io/
- **Cloudflare R2**: https://developers.cloudflare.com/r2/

---

**Document Version**: 1.0
**Last Updated**: 2026-01-17
**Author**: AI Research Analysis
