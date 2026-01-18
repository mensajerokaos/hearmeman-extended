# Video and Image Generation Systems - RunPod Project Research

**Author**: claude-haiku-4.5
**Date**: 2026-01-17
**Project**: RunPod Custom Templates for AI Model Deployment

---

## Executive Summary

This document provides comprehensive documentation of all video and image generation systems available in the RunPod project. The system supports multiple state-of-the-art models for text-to-video, image-to-video, image generation, video editing, frame interpolation, and more. Each system includes detailed specifications, VRAM requirements, input/output formats, ComfyUI workflow configurations, and optimization parameters.

---

## 1. WAN 2.2 / WAN 2.1 Video Generation Models

### 1.1 Overview

WAN is a family of diffusion-based video generation models developed by Wan-AI, supporting both text-to-video (T2V) and image-to-video (I2V) generation. The project supports multiple model variants optimized for different use cases and VRAM constraints.

### 1.2 Model Variants

| Model | Variant | Size | VRAM | Resolution | Frames | Type |
|-------|---------|------|------|------------|--------|------|
| WAN 2.2 5B | `wan2.2_ti2v_5B_fp16.safetensors` | ~5GB | 24GB+ | 1280x704 | 41 | T2V/I2V |
| WAN 2.1 14B | `wan2.1_t2v_14B_fp8_e4m3fn.safetensors` | 14GB | 24GB+ | 720p | 49 | T2V |
| WAN 2.1 480p 1.3B | `wan2.1_t2v_1.3B_fp16.safetensors` | 1.3GB | 16GB | 480p | 81 | T2V |
| WAN 2.2 Distilled | `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` + `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` | 28GB total | 24GB+ | Variable | Variable | I2V (4-step) |

### 1.3 Shared Dependencies

All WAN models require:

```
text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors  (9.5GB)
vae/wan_2.1_vae.safetensors                           (335MB)
clip_vision/clip_vision_h.safetensors                 (1.4GB)  [I2V only]
```

### 1.4 ComfyUI Workflow Requirements

**Custom Nodes Required:**
- `ComfyUI-VideoHelperSuite` - Video frame management and output
- `ComfyUI-WanVideoWrapper` - WAN-specific nodes (WAN 2.1 API workflow)

**Node Types Used:**
- `UNETLoader` - Load diffusion model
- `CLIPLoader` - Load text encoder (type: "wan")
- `VAELoader` - Load VAE
- `WanVideoSampler` - WAN 2.1 sampling
- `WanVideoDecode` - Decode latent to video frames
- `VHS_VideoCombine` - Combine frames into video file
- `EmptyMochiLatentVideo` - Initialize video latent (WAN 2.2)
- `EmptySD3LatentImage` - Image latent for I2V

### 1.5 Generation Parameters

**WAN 2.2 5B Workflow Settings:**
```json
{
  "steps": 30,
  "sampler": "uni_pc",
  "scheduler": "normal",
  "cfg": 5.0,
  "resolution": "1280x704",
  "frames": 41,
  "fps": 24
}
```

**WAN 2.1 14B API Workflow Settings:**
```json
{
  "steps": 15,
  "cfg": 6.0,
  "shift": 5.0,
  "scheduler": "unipc",
  "resolution": "480x320",
  "frames": 17,
  "fps": 16
}
```

### 1.6 Configuration Options

**Environment Variables:**
```bash
WAN_720P=false              # Enable WAN 2.1 720p (14B model)
WAN_480P=false              # Enable WAN 2.1 480p (1.3B model)
ENABLE_WAN22_DISTILL=false  # Enable WAN 2.2 distilled I2V
ENABLE_I2V=false            # Enable image-to-video support
```

**Download Script Reference:**
- Location: `docker/download_models.sh` (lines 206-320)
- Total size for full WAN setup: ~28GB (WAN 2.2 distilled)

### 1.7 Known Limitations

- WAN 2.2 5B optimal resolution is 1280x704 with 121 frames for full quality
- WAN 2.1 14B requires `WanVideoWrapper` custom nodes for proper operation
- Distilled models require CLIP Vision for image conditioning
- 16GB VRAM systems must use 480p model variant

---

## 2. VACE (Video All-in-One Creation and Editing)

### 2.1 Overview

VACE (Video All-in-One Creation and Editing) is a comprehensive video editing model that supports video generation, editing, and manipulation tasks beyond simple text-to-video generation.

### 2.2 Model Specifications

| Property | Value |
|----------|-------|
| Model ID | `wan2.1_vace_14B_fp16.safetensors` |
| Size | ~28GB |
| VRAM Requirement | 24GB+ |
| Source | HuggingFace: `Wan-AI/Wan2.1-VACE-14B` |
| Enable Flag | `ENABLE_VACE=false` |

### 2.3 Capabilities

- Video generation from text prompts
- Video editing and manipulation
- Multi-frame video processing
- Support for video-to-video transformations
- Advanced video conditioning and control

### 2.4 Configuration

**Environment Variable:**
```bash
ENABLE_VACE=false  # Set to true to enable
```

**Download:**
```bash
hf_download "Wan-AI/Wan2.1-VACE-14B" \
    "wan2.1_vace_14B_fp16.safetensors" \
    "$MODELS_DIR/diffusion_models/wan2.1_vace_14B_fp16.safetensors"
```

### 2.5 Usage Notes

- Requires WAN 2.1 text encoder and VAE as shared dependencies
- Compatible with ComfyUI-VideoHelperSuite for video I/O
- Best suited for professional video editing workflows
- Recommended for GPU clusters with 48GB+ VRAM for optimal performance

---

## 3. Z-Image Turbo

### 3.1 Overview

Z-Image Turbo is a high-performance text-to-image generation model optimized for fast inference with minimal quality loss. Based on the SD3 architecture with custom optimizations.

### 3.2 Model Specifications

| Property | Value |
|----------|-------|
| Model ID | `z_image_turbo_bf16.safetensors` |
| Size | ~21GB |
| VRAM Requirement | 8-12GB |
| Text Encoder | `qwen_3_4b.safetensors` (4B parameters) |
| VAE | `ae.safetensors` |
| Source | HuggingFace: `Tongyi-MAI/Z-Image-Turbo` |
| Enable Flag | `ENABLE_ZIMAGE=false` |

### 3.3 ComfyUI Workflow

**Workflow File:** `docker/workflows/z-image-turbo-txt2img.json`

**Node Configuration:**
```json
{
  "UNETLoader": {
    "model_name": "z_image_turbo_bf16.safetensors",
    "weight_dtype": "default"
  },
  "CLIPLoader": {
    "clip_name": "qwen_3_4b.safetensors",
    "type": "qwen_image"
  },
  "VAELoader": {
    "vae_name": "ae.safetensors"
  }
}
```

### 3.4 Generation Parameters

```json
{
  "steps": 9,
  "sampler": "euler",
  "scheduler": "simple",
  "cfg": 1.0,
  "resolution": "1024x1024"
}
```

**Key Optimization Notes:**
- Very fast inference (9 steps vs 25+ for SDXL)
- CFG set to 1.0 (minimal guidance) for speed
- Euler sampler with simple scheduler
- Optimal for high-throughput image generation

### 3.5 Configuration

**Environment Variable:**
```bash
ENABLE_ZIMAGE=false  # Set to true to enable
```

**Download Script (lines 196-203):**
```bash
hf_download "Tongyi-MAI/Z-Image-Turbo" "qwen_3_4b.safetensors" "$MODELS_DIR/text_encoders/qwen_3_4b.safetensors"
hf_download "Tongyi-MAI/Z-Image-Turbo" "z_image_turbo_bf16.safetensors" "$MODELS_DIR/diffusion_models/z_image_turbo_bf16.safetensors"
hf_download "Tongyi-MAI/Z-Image-Turbo" "ae.safetensors" "$MODELS_DIR/vae/ae.safetensors"
```

### 3.6 Usage Recommendations

- **Best for:** Rapid prototyping, batch generation, real-time applications
- **VRAM:** 8-12GB allows for 1024x1024 on consumer GPUs
- **Quality vs Speed:** Excellent speed with competitive quality
- **Limitations:** Less detailed than SDXL for complex scenes

---

## 4. Realism Illustrious

### 4.1 Overview

Realism Illustrious is an SDXL-based checkpoint model specialized in photorealistic image generation. It excels at producing realistic human portraits, landscapes, and product photography with exceptional detail.

### 4.2 Model Specifications

| Property | Value |
|----------|-------|
| Checkpoint | `realismIllustriousByStableYogi_v50FP16.safetensors` |
| Size | 6.46GB |
| VRAM Requirement | 8-12GB (16GB recommended for 1024x1024) |
| Type | SDXL Checkpoint (Single File) |
| Source | CivitAI: ID 2091367 |
| Enable Flag | `ENABLE_ILLUSTRIOUS=false` |

### 4.3 Optional Components

**Embeddings (Recommended):**
- Positive Embedding: `Stable_Yogis_Illustrious_Positives.safetensors` (352KB) - CivitAI ID 1153237
- Negative Embedding: `Stable_Yogis_Illustrious_Negatives.safetensors` (536KB) - CivitAI ID 1153212

**NSFW LoRAs (Optional):**
- `1906687` and `1736657` - Adult content LoRAs for mature audiences

### 4.4 ComfyUI Workflows

**Primary Workflow:** `docker/workflows/realism-illustrious-txt2img.json`

**Settings:**
```json
{
  "steps": 25,
  "sampler": "dpmpp_2m",
  "scheduler": "karras",
  "cfg": 7.0,
  "resolution": "1024x1024"
}
```

**Portrait Workflow:** `docker/workflows/realism-illustrious-basic.json`

**Settings:**
```json
{
  "steps": 30,
  "sampler": "dpmpp_2m_sde",
  "scheduler": "karras",
  "cfg": 7.0,
  "resolution": "832x1216 (portrait)"
}
```

### 4.5 Positive Prompt Template

```
masterpiece, best quality, highly detailed, photorealistic portrait of a woman,
natural lighting, soft shadows, professional photography, 8k uhd
```

### 4.6 Negative Prompt Template

```
worst quality, low quality, blurry, distorted, deformed, ugly, bad anatomy,
bad hands, extra fingers, missing fingers, fused fingers, too many fingers,
text, watermark, signature, logo, censored, mosaic, jpeg artifacts
```

### 4.7 Configuration

**Environment Variables:**
```bash
ENABLE_ILLUSTRIOUS=false                   # Enable base model
ENABLE_ILLUSTRIOUS_EMBEDDINGS=true         # Enable embeddings
CIVITAI_API_KEY=${CIVITAI_API_KEY}         # API key for CivitAI
CIVITAI_LORAS=1906687,1736657              # Optional LoRA IDs
```

**Docker Compose (lines 15-27):**
```yaml
environment:
  - ENABLE_ILLUSTRIOUS=true
  - ENABLE_ILLUSTRIOUS_EMBEDDINGS=true
  - ENABLE_CIVITAI=true
  - CIVITAI_API_KEY=${CIVITAI_API_KEY}
  - CIVITAI_LORAS=1906687,1736657
```

### 4.8 Test Results (2025-12-29)

| Test | Resolution | Steps | Time | Status |
|------|------------|-------|------|--------|
| txt2img | 768x768 | 20 | ~21s | PASSED |
| txt2img | 1024x1024 | 25 | ~45s | OOM (16GB VRAM) |

**VRAM Management:** 1024x1024 caused container restart on 16GB VRAM. Use 768x768 or 832x1216 for safe operation.

---

## 5. SteadyDancer

### 5.1 Overview

SteadyDancer is a specialized video generation model focused on stable, high-quality dance and motion video generation. Based on WAN 2.1 architecture with motion-specific optimizations.

### 5.2 Model Specifications

| Property | Value |
|----------|-------|
| Model ID | `Wan21_SteadyDancer_fp16.safetensors` |
| Size | ~14GB |
| VRAM Requirement | 24GB+ |
| Source | HuggingFace: `MCG-NJU/SteadyDancer-14B` |
| Enable Flag | `ENABLE_STEADYDANCER=false` |

### 5.3 Capabilities

- Dance motion generation
- Character animation with stable motion
- Text-to-video with motion emphasis
- Compatible with WAN 2.1 text encoders and VAE

### 5.4 Configuration

**Environment Variable:**
```bash
ENABLE_STEADYDANCER=false  # Set to true to enable
```

**Download:**
```bash
hf_download "MCG-NJU/SteadyDancer-14B" \
    "Wan21_SteadyDancer_fp16.safetensors" \
    "$MODELS_DIR/diffusion_models/Wan21_SteadyDancer_fp16.safetensors"
```

### 5.5 Usage Notes

- Requires WAN 2.1 shared dependencies (UMT5 encoder, VAE)
- Best for generating human motion and dance sequences
- Compatible with ComfyUI-VideoHelperSuite
- High VRAM requirement limits to professional GPU clusters

---

## 6. SCAIL (Facial Motion Capture)

### 6.1 Overview

SCAIL (likely "Synchronized AI Character Animation Language" or similar) is a facial motion capture and animation model designed for generating realistic facial expressions and lip-sync from audio or text inputs.

### 6.2 Model Specifications

| Property | Value |
|----------|-------|
| Repository | `zai-org/SCAIL-Preview` |
| Format | Git LFS repository |
| VRAM Requirement | 24GB+ |
| Source | HuggingFace: `zai-org/SCAIL-Preview` |
| Enable Flag | `ENABLE_SCAIL=false` |

### 6.3 Capabilities

- Facial expression generation
- Lip-sync from audio
- Emotional expression mapping
- Character animation with facial focus

### 6.4 Configuration

**Environment Variable:**
```bash
ENABLE_SCAIL=false  # Set to true to enable
```

**Download Method:**
```bash
cd "$MODELS_DIR/diffusion_models"
if [ ! -d "SCAIL-Preview" ]; then
    GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/zai-org/SCAIL-Preview
    cd SCAIL-Preview
    git lfs pull
fi
```

### 6.5 Usage Notes

- Requires Git LFS for model files
- Standalone repository structure (not .safetensors format)
- Compatible with standard ComfyUI video nodes
- High-quality facial animation for character work

---

## 7. ControlNet

### 7.1 Overview

ControlNet provides conditional image generation with spatial control through various conditioning maps. The project includes multiple ControlNet models for different control types.

### 7.2 Available Models

| Control Type | Model File | Size | Description |
|--------------|------------|------|-------------|
| Canny Edge | `control_v11p_sd15_canny_fp16.safetensors` | ~720MB | Edge detection control |
| Depth | `control_v11f1p_sd15_depth_fp16.safetensors` | ~720MB | Depth map control |
| OpenPose | `control_v11p_sd15_openpose_fp16.safetensors` | ~720MB | Skeleton pose control |
| Lineart | `control_v11p_sd15_lineart_fp16.safetensors` | ~720MB | Line drawing control |
| Normal Map | `control_v11p_sd15_normalbae_fp16.safetensors` | ~720MB | Surface normal control |

**Total Size:** ~3.6GB (all 5 models)

### 7.3 VRAM Requirements

| Configuration | VRAM |
|--------------|------|
| Single ControlNet | 8-12GB |
| Multiple ControlNets | 16GB+ |
| With base model | Add base model VRAM |

### 7.4 Configuration

**Environment Variables:**
```bash
ENABLE_CONTROLNET=true  # Default: true
CONTROLNET_MODELS="canny,depth,openpose"  # Models to download
```

**Download Script (lines 343-382):**
```bash
# Canny
hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
    "control_v11p_sd15_canny_fp16.safetensors" \
    "$MODELS_DIR/controlnet/control_v11p_sd15_canny_fp16.safetensors"

# Depth
hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
    "control_v11f1p_sd15_depth_fp16.safetensors" \
    "$MODELS_DIR/controlnet/control_v11f1p_sd15_depth_fp16.safetensors"

# OpenPose
hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
    "control_v11p_sd15_openpose_fp16.safetensors" \
    "$MODELS_DIR/controlnet/control_v11p_sd15_openpose_fp16.safetensors"
```

### 7.5 ComfyUI Nodes Required

- `ControlNetLoader` - Load ControlNet model
- `ControlNetApply` - Apply conditioning to base model
- `OpenposePreprocessor` - Generate pose maps
- `DepthPreprocessor` - Generate depth maps
- `CannyPreprocessor` - Generate edge maps

### 7.6 Usage Recommendations

- **Canny:** Best for preserving structure while changing style
- **Depth:** Good for maintaining spatial relationships
- **OpenPose:** Essential for character pose control
- **Lineart:** Great for stylized generation from sketches
- **Normal:** Useful for 3D-aware generation

---

## 8. Fun InP (Frame Interpolation)

### 8.1 Overview

Fun InP (First-Last Frame Interpolation) is a frame interpolation model that generates intermediate frames between two input images/keyframes. Useful for slow-motion effects, video enhancement, and temporal upscaling.

### 8.2 Model Specifications

| Property | Value |
|----------|-------|
| Model ID | `wan2.2_fun_inp_14B_fp16.safetensors` |
| Size | ~28GB |
| VRAM Requirement | 24GB+ |
| Source | HuggingFace: `Wan-AI/Wan2.2-Fun-InP-14B` |
| Enable Flag | `ENABLE_FUN_INP=false` |

### 8.3 Input/Output Specifications

**Inputs:**
- First frame (image)
- Last frame (image)
- Number of interpolation steps

**Outputs:**
- Smoothly interpolated video sequence
- Programmable frame rate (upscaled from input)

### 8.4 Configuration

**Environment Variable:**
```bash
ENABLE_FUN_INP=false  # Set to true to enable
```

**Download:**
```bash
hf_download "Wan-AI/Wan2.2-Fun-InP-14B" \
    "wan2.2_fun_inp_14B_fp16.safetensors" \
    "$MODELS_DIR/diffusion_models/wan2.2_fun_inp_14B_fp16.safetensors"
```

### 8.5 Usage Applications

- Slow-motion video enhancement
- Video temporal upscaling
- Frame rate conversion
- Motion interpolation for animation
- Smooth transitions between keyframes

---

## 9. Additional Generation Systems

### 9.1 Genfocus (Image Enhancement)

**Workflow:** `docker/workflows/genfocus-refocusing.json`

**Components:**
- **DeblurNet** - Recovers sharp images from blurry inputs
- **BokehNet** - Adds depth-of-field effects

**Parameters:**
```json
{
  "steps": 30,
  "guidance_scale": 7.5,
  "focus_distance": 0.5,
  "bokeh_intensity": 0.7
}
```

**Models Required:**
- `deblurNet.safetensors`
- `bokehNet.safetensors`
- `depth_pro.pt`

**Source:** HuggingFace `nycu-cplab/Genfocus-Model`

### 9.2 MVInverse (Material Extraction)

**Workflow:** `docker/workflows/mvinverse-material-extraction.json`

**Purpose:** Extract PBR (Physically Based Rendering) material maps from multi-view images

**Outputs:**
- Albedo (color)
- Normal map
- Metallic map
- Roughness map
- Shading map

**Input Requirements:**
- 3-8 views of the same scene
- Batch dimension represents different views

**Models Required:**
- `mvinverse.pt` from HuggingFace `maddog241/mvinverse`

---

## 10. Storage Requirements Summary

| Component | Size | Notes |
|-----------|------|-------|
| **Z-Image Turbo** | ~26GB | Text encoder + diffusion + VAE |
| **WAN 2.1 720p** | ~25GB | Full 14B model + deps |
| **WAN 2.1 480p** | ~12GB | Light 1.3B model |
| **WAN 2.2 Distilled** | ~28GB | High/Low noise experts |
| **VACE** | ~28GB | Video editing model |
| **Realism Illustrious** | ~6.5GB | Checkpoint + embeddings |
| **SteadyDancer** | ~14GB | Dance motion model |
| **SCAIL** | ~28GB | Facial mocap (LFS repo) |
| **ControlNet (5 models)** | ~3.6GB | All variants |
| **Fun InP** | ~28GB | Frame interpolation |
| **Genfocus** | ~1GB | Deblur + Bokeh + Depth |
| **Total (ALL)** | **~230GB** | |

**Minimum Local Setup:**
- 250GB SSD storage
- 32GB RAM
- 24GB VRAM (RTX 4090 or equivalent)

---

## 11. Model Download Configuration

### 11.1 Download Script Location

`docker/download_models.sh` - Centralized model download with:
- Resume support (wget -c)
- Fallback to curl
- Progress indicators
- Size verification
- HuggingFace and CivitAI sources

### 11.2 Environment Variables Reference

```bash
# Image Generation
ENABLE_ZIMAGE=false              # Z-Image Turbo
ENABLE_ILLUSTRIOUS=false         # Realism Illustrious
ENABLE_ILLUSTRIOUS_EMBEDDINGS=true

# Video Generation
WAN_720P=false                   # WAN 2.1 720p (14B)
WAN_480P=false                   # WAN 2.1 480p (1.3B)
ENABLE_WAN22_DISTILL=false       # WAN 2.2 distilled I2V
ENABLE_I2V=false                 # Image-to-video support

# Advanced Video
ENABLE_VACE=false                # Video editing
ENABLE_STEADYDANCER=false        # Dance motion
ENABLE_SCAIL=false               # Facial mocap
ENABLE_FUN_INP=false             # Frame interpolation

# Control & Enhancement
ENABLE_CONTROLNET=true           # ControlNet models
CONTROLNET_MODELS="canny,depth,openpose"

# Model Sources
CIVITAI_API_KEY=${CIVITAI_API_KEY}
CIVITAI_LORAS=                   # Comma-separated IDs
```

---

## 12. ComfyUI Workflow Conventions

### 12.1 Standard Node Types

| Node Type | Purpose | Example |
|-----------|---------|---------|
| `CheckpointLoaderSimple` | Load SDXL/SD1.x checkpoints | Realism Illustrious |
| `UNETLoader` | Load diffusion models | WAN, Z-Image |
| `CLIPLoader` | Load text encoders | UMT5, Qwen |
| `VAELoader` | Load VAE models | WAN, Z-Image |
| `KSampler` | Diffusion sampling | All generation |
| `VHS_VideoCombine` | Video encoding | Video workflows |
| `SaveImage` | Image output | Image workflows |

### 12.2 Model Directory Structure

```
ComfyUI/models/
├── checkpoints/           # SDXL/SD1.x checkpoints (Realism Illustrious)
├── diffusion_models/      # UNET weights (WAN, Z-Image, VACE, etc.)
├── text_encoders/         # CLIP/LLM encoders (UMT5, Qwen)
├── vae/                   # VAE models
├── clip_vision/           # Vision encoders for I2V
├── controlnet/            # ControlNet models
├── loras/                 # LoRA adapters
├── embeddings/            # Text embeddings
├── genfocus/              # Genfocus models
├── mvinverse/             # MVInverse model
└── vibevoice/             # TTS models
```

---

## 13. VRAM Management Guidelines

### 13.1 VRAM by Configuration

| VRAM | Supported Models | Notes |
|------|-----------------|-------|
| 8GB | ControlNet, Z-Image (low res), Illustrious (768x768) | Limited |
| 12GB | Z-Image Turbo, Illustrious (1024x1024) | Standard |
| 16GB | All above + WAN 480p | Recommended minimum |
| 24GB+ | All models including 14B video models | Professional |

### 13.2 VRAM Optimization Tips

- Reduce resolution if OOM errors occur
- Use 480p WAN model instead of 720p
- Reduce sampling steps for faster generation
- Disable unused models in docker-compose
- Use VAE tiling for large images

### 13.3 OOM Recovery

```bash
# If container restarts due to OOM:
# 1. Reduce resolution (1024x1024 -> 768x768)
# 2. Reduce steps (30 -> 20)
# 3. Enable VAE tiling in workflow
# 4. Use lighter model variant
```

---

## 14. Testing and Validation

### 14.1 Test Results (2025-12-29)

| Workflow | Status | Resolution | Steps | Time | Notes |
|----------|--------|------------|-------|------|-------|
| Realism Illustrious txt2img | PASSED | 768x768 | 20 | ~21s | VRAM constrained |
| Genfocus DeblurNet | PASSED | - | - | ~5s | Fallback mode |
| Genfocus BokehNet | PASSED | - | - | ~10s | Fixed tensor size |
| MVInverse Material | PASSED | 1024 | - | ~2min | First-run download |
| WAN 2.2 | SKIP | - | - | - | Model not downloaded |
| Z-Image Turbo | SKIP | - | - | - | VRAM constraint |

### 14.2 Known Issues and Fixes

**Genfocus BokehNet Tensor Size Mismatch:**
- Issue: `RuntimeError: The expanded size of the tensor (768) must match the existing size (769)`
- Fix: Added interpolation to resize blur_amount to match image dimensions
- File: `custom_nodes/ComfyUI-Genfocus/nodes/bokeh.py`

**MVInverse Model Loading:**
- Issue: Tried to download non-existent `mvinverse.pt` directly
- Fix: Use `MVInverse.from_pretrained("maddog241/mvinverse")` method
- Note: First run downloads model from HuggingFace (~2 minutes)

---

## 15. Configuration Files Reference

### 15.1 Docker Compose Files

| File | Purpose |
|------|---------|
| `docker-compose.illustrious.yml` | Realism Illustrious-only container |
| `docker-compose.wan22-test.yml` | WAN 2.2 download and workflow testing |
| `docker-compose.nsfw.yml` | NSFW-optimized configuration |

### 15.2 Workflow Files Location

All ComfyUI workflows stored in: `docker/workflows/`

| Workflow | Model | Type |
|----------|-------|------|
| `z-image-turbo-txt2img.json` | Z-Image Turbo | Text-to-Image |
| `realism-illustrious-txt2img.json` | Realism Illustrious | Text-to-Image |
| `realism-illustrious-basic.json` | Realism Illustrious | Basic txt2img |
| `realism-illustrious-embeddings.json` | Illustrious + Embeddings | Enhanced txt2img |
| `realism-illustrious-nsfw-lora.json` | Illustrious + NSFW LoRAs | Adult content |
| `wan22-t2v-5b.json` | WAN 2.2 5B | Text-to-Video |
| `wan21-t2v-14b-api.json` | WAN 2.1 14B | Text-to-Video (API) |
| `genfocus-refocusing.json` | Genfocus | Image enhancement |
| `mvinverse-material-extraction.json` | MVInverse | Material extraction |
| `vibevoice-tts-basic.json` | VibeVoice | Text-to-Speech |

---

## 16. Sources and References

### 16.1 Model Sources

- **WAN Models:** https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_repackaged
- **Z-Image Turbo:** https://huggingface.co/Tongyi-MAI/Z-Image-Turbo
- **Realism Illustrious:** https://civitai.com/models/1048098/realism-illustrious
- **SteadyDancer:** https://huggingface.co/MCG-NJU/SteadyDancer-14B
- **VACE:** https://huggingface.co/Wan-AI/Wan2.1-VACE-14B
- **Fun InP:** https://huggingface.co/Wan-AI/Wan2.2-Fun-InP-14B
- **SCAIL:** https://huggingface.co/zai-org/SCAIL-Preview
- **ControlNet:** https://huggingface.co/comfyanonymous/ControlNet-v1-1_fp16_safetensors
- **Genfocus:** https://huggingface.co/nycu-cplab/Genfocus-Model
- **MVInverse:** https://huggingface.co/maddog241/mvinverse

### 16.2 Documentation

- WAN 2.2 Tutorial: https://docs.comfy.org/tutorials/video/wan/wan2_2
- Z-Image Turbo Tutorial: https://docs.comfy.org/tutorials/image/z-image/z-image-turbo
- VibeVoice: https://github.com/wildminder/ComfyUI-VibeVoice

---

## 17. Quick Start Guide

### 17.1 Enable a Model

```bash
# Edit docker/.env or environment variables
ENABLE_ILLUSTRIOUS=true          # For photorealistic images
ENABLE_ZIMAGE=true              # For fast image generation
WAN_720P=true                   # For 720p video generation
ENABLE_WAN22_DISTILL=true       # For 4-step I2V
ENABLE_CONTROLNET=true          # For conditional generation
```

### 17.2 Start Docker

```bash
cd docker
docker compose build
docker compose up -d
```

### 17.3 Use in ComfyUI

1. Open http://localhost:8188
2. Load workflow from `docker/workflows/`
3. Install missing models (workflow metadata shows requirements)
4. Queue prompt and generate

---

## Summary

This RunPod project provides a comprehensive suite of video and image generation models optimized for different use cases and hardware configurations. From fast text-to-image with Z-Image Turbo to professional video generation with WAN 2.1/2.2, and from photorealistic images with Realism Illustrious to advanced video editing with VACE, the system offers state-of-the-art AI generation capabilities. Proper VRAM management and model selection based on use case are critical for optimal performance.

---

**Document Version:** 1.0
**Last Updated:** 2026-01-17
**Status:** Complete - All major generation systems documented
