---
section: "004"
name: "video-image-generation"
title: "Video & Image Generation (WAN, VACE, Z-Image Turbo, Illustrious, ControlNet)"
version: "1.1"
date: "2026-01-17"
author: "oz + codex (gpt-5.2)"
task: "Document video/image generation: model variants, VRAM, I/O, ComfyUI workflows, parameters"
---

# Video & Image Generation

This section documents the **video + image generation stack** in this RunPod template, focusing on:

- **WAN 2.1/2.2** (T2V, I2V, distilled/TurboDiffusion variants)
- **VACE** (video editing)
- **Z-Image Turbo** (fast txt2img)
- **Realism Illustrious** (photorealistic SDXL)
- **SteadyDancer / SCAIL** (dance video + facial mocap)
- **ControlNet** (preprocessors + models)
- **Fun InP** (first/last frame interpolation)

The container filesystem is **ephemeral** on RunPod: pods regenerate on every start/stop. All workflows must work **with zero manual intervention** by relying on `download_models.sh` and matching ComfyUI model paths.

## At a Glance

All model paths below are **container runtime paths** under:

`/workspace/ComfyUI/models/`

| System | Primary Use | Models (on disk) | Typical VRAM | Inputs | Outputs |
|---|---|---:|---:|---|---|
| WAN 2.1 T2V 14B (FP8) | Text-to-video | ~25GB (deps + 14B) | 24GB+ | prompt | video frames -> webm/mp4/webp |
| WAN 2.1 T2V 1.3B (FP16) | Text-to-video (smaller) | ~12GB (deps + 1.3B) | 12-16GB | prompt | video frames -> webm/mp4/webp |
| WAN 2.1 I2V 14B (FP8) | Image-to-video | +14GB (i2v model) | 24GB+ | image + prompt | video |
| WAN 2.2 TI2V 5B (FP16) | Text-to-video | ~10GB (model only) | 24GB+ | prompt | video frames -> webm/mp4/webp |
| WAN 2.2 Distilled (TurboDiffusion I2V) | Fast I2V | +28GB (2 experts) | 24GB+ | image + prompt | video |
| VACE 14B (FP16) | Video editing | ~28GB | 24-28GB | video + mask + prompt | edited video |
| Z-Image Turbo | Fast txt2img | ~21GB+ (UNet + encoder + VAE) | 16GB+ (24GB recommended) | prompt | images |
| Realism Illustrious (SDXL) | Photorealistic txt2img | 6.46GB (+ embeddings optional) | 8-16GB | prompt (+ embeddings/LoRA) | images |
| SteadyDancer 14B | Dance / motion video | ~28-33GB | 24-32GB | prompt (+ pose optional) | video |
| SCAIL (Preview) | Facial animation / mocap | ~28GB | 24GB+ | face ref (+ audio/pose) | video / pose |
| ControlNet (SD1.5) | Spatial guidance | ~0.7GB each (~3.6GB for 5) | +1-4GB over base | image/pose/depth/edges | guided images |
| Fun InP 14B | Frame interpolation | ~28GB | 24GB+ | first + last frame | interpolated video |

**Important:** Several sizes/VRAM values are approximate. This repo's source of truth for *what gets downloaded* is `docker/download_models.sh` (and its log `/var/log/download_models.log` inside the container).

## Model Directory Conventions

ComfyUI expects specific folders under `ComfyUI/models/`:

```
ComfyUI/models/
├── checkpoints/        # SDXL/SD checkpoints (Illustrious)
├── diffusion_models/   # WAN, VACE, Fun InP, Z-Image UNET weights
├── text_encoders/      # UMT5 (WAN), Qwen (Z-Image)
├── vae/                # WAN VAE, Z-Image AE
├── clip_vision/        # Vision encoders for I2V
├── controlnet/         # ControlNet weights
├── embeddings/         # Textual inversion embeddings (Illustrious optional)
└── loras/              # LoRAs (optional)
```

## ComfyUI Node Requirements (Custom Nodes Installed in the Image)

Installed at build-time in `docker/Dockerfile`:

- `ComfyUI-WanVideoWrapper` (WAN 2.x nodes)
- `Comfyui_turbodiffusion` (TurboDiffusion acceleration)
- `ComfyUI-VideoHelperSuite` (video assembly/encoding, e.g. `VHS_VideoCombine`)
- `comfyui_controlnet_aux` (ControlNet preprocessors)
- `ComfyUI-SCAIL-Pose` (SCAIL-related pose nodes)

If workflows fail due to missing nodes, confirm they are present in the running container under:

`/workspace/ComfyUI/custom_nodes/`

## 1) WAN 2.1 / WAN 2.2 (Video Generation)

### 1.1 What WAN Covers

In this template, "WAN" refers to a **family** of video diffusion models and related task-specialized models:

- **T2V**: text -> video
- **I2V**: image + prompt -> video
- **Distilled/TurboDiffusion**: fast I2V using expert models
- **Task models**: VACE (editing), Fun InP (interpolation), SteadyDancer (motion)

### 1.2 Shared WAN Dependencies (Downloaded by `download_models.sh`)

These are shared across most WAN workflows:

| File | Folder | Used For | Size hint |
|---|---|---|---:|
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | `text_encoders/` | WAN text encoder | 9.5GB |
| `wan_2.1_vae.safetensors` | `vae/` | WAN VAE | 335MB |
| `clip_vision_h.safetensors` | `clip_vision/` | WAN I2V conditioning | 1.4GB |

**Optional (used by some I2V nodes):**

| File | Folder | Notes |
|---|---|---|
| `sigclip_vision_patch14_384.safetensors` | `clip_vision/` | Downloaded when `ENABLE_I2V=true` in `download_models.sh` |

### 1.3 WAN Model Variants in This Repo

These are the filenames your workflows must reference exactly.

| Variant | Primary file(s) | Folder | Typical VRAM | Notes |
|---|---|---|---:|---|
| WAN 2.1 T2V 14B (FP8) | `wan2.1_t2v_14B_fp8_e4m3fn.safetensors` | `diffusion_models/` | 24GB+ | Requires UMT5 + VAE |
| WAN 2.1 I2V 14B (FP8) | `wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors` | `diffusion_models/` | 24GB+ | Requires `clip_vision_h.safetensors` |
| WAN 2.1 T2V 1.3B (FP16, 480p) | `wan2.1_t2v_1.3B_fp16.safetensors` | `diffusion_models/` | 12-16GB | Smaller model; reuses UMT5 + VAE |
| WAN 2.2 TI2V 5B (FP16) | `wan2.2_ti2v_5B_fp16.safetensors` | `diffusion_models/` | 24GB+ | Workflow included, but model is not auto-downloaded by `download_models.sh` |
| WAN 2.2 distilled I2V experts (FP8) | `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` + `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` | `diffusion_models/` | 24GB+ | Used by TurboDiffusion 4-step I2V |

### 1.4 Downloads / Enable Flags (Startup)

`docker/download_models.sh` controls downloads via env vars.

| Env var | Default | What it downloads |
|---|---:|---|
| `WAN_720P` | `false` | WAN 2.1 14B T2V (+ UMT5/VAE/CLIP vision) |
| `ENABLE_I2V` | `false` | Adds WAN 2.1 I2V model (if `WAN_720P=true`) and downloads `sigclip_vision_patch14_384.safetensors` |
| `WAN_480P` | `false` | WAN 2.1 1.3B T2V (smaller) |
| `ENABLE_WAN22_DISTILL` | `false` | WAN 2.2 distilled expert models for TurboDiffusion I2V |

### 1.5 I/O Specifications (WAN Video)

**Inputs**

- **T2V**: prompt (positive/negative), resolution, number of frames, seed
- **I2V**: prompt + an input image (recommended to match output aspect ratio)

**Outputs**

- A sequence of decoded frames (images)
- A combined video/animation (via `VHS_VideoCombine`), typically one of:
  - `video/webm`
  - `video/mp4` (if configured)
  - `image/webp` (animated webp)

**Common constraints**

- Many WAN workflows expect width/height to be divisible by 16 (sometimes 32).
- Longer clips (more frames) scale VRAM and time significantly.

### 1.6 ComfyUI Workflow Templates Included

This repo includes two WAN starter workflows under `docker/workflows/`:

1. `docker/workflows/wan21-t2v-14b-api.json` (API-format prompt graph)
2. `docker/workflows/wan22-t2v-5b.json` (canvas workflow)

#### A) WAN 2.1 14B T2V (API Workflow)

**File:** `docker/workflows/wan21-t2v-14b-api.json`

This is a **ComfyUI API prompt** (JSON object keyed by node-id). It is intended for POSTing to `/prompt`, not for drag-and-drop into the ComfyUI canvas.

**Key nodes / requirements**

- `CLIPLoader` with `type="wan"`
- `WanVideoModelLoader` with FP8 quantization settings
- `WanVideoSampler` (WAN-specific sampler)
- `WanVideoVAELoader` + `WanVideoDecode`
- `VHS_VideoCombine` (from VideoHelperSuite) for encoding

**Parameters (as shipped in the file)**

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

#### B) WAN 2.2 5B T2V (Canvas Workflow)

**File:** `docker/workflows/wan22-t2v-5b.json`

This is a standard **ComfyUI canvas workflow** that can be dragged into the UI.

**Important:** the referenced model file (`wan2.2_ti2v_5B_fp16.safetensors`) is not currently downloaded by `docker/download_models.sh`. You must download it separately (or extend the script) before this workflow will run.

**Key nodes / requirements**

- `UNETLoader`: `wan2.2_ti2v_5B_fp16.safetensors`
- `CLIPLoader`: `umt5_xxl_fp8_e4m3fn_scaled.safetensors` with `type="wan"`
- `VAELoader`: `wan_2.1_vae.safetensors`
- `EmptyMochiLatentVideo` (video latent initializer)
- `KSampler`
- `VHS_VideoCombine` (VideoHelperSuite) for output

**Parameters (as shipped in the file)**

| Setting | Value |
|---|---:|
| Resolution | 1280x704 |
| Frames | 41 |
| Steps | 30 |
| CFG | 5.0 |
| Sampler | `uni_pc` |
| Scheduler | `normal` |
| FPS | 24 |
| Output format | `image/webp` |

### 1.7 TurboDiffusion (WAN 2.2 Distilled I2V)

TurboDiffusion is installed via:

- `docker/Dockerfile` -> clones `anveshane/Comfyui_turbodiffusion`

The **distilled expert models** are downloaded when:

- `ENABLE_WAN22_DISTILL=true`

**Intended usage**

- 4-step I2V inference using a "high noise" expert for early steps and "low noise" expert for late steps.

**Practical guidance**

- Start with **4 steps**.
- If output is unstable/noisy, try 6-8 steps (speed benefit reduces).
- Keep resolution and frame count modest until you confirm stability on your GPU tier.

## 2) VACE (WAN Video Editing)

### 2.1 What VACE Is

VACE is a WAN-family model focused on **video editing** tasks such as:

- Video inpainting / outpainting (mask-based edits across frames)
- Video-to-video edits driven by text prompts
- Content replacement while preserving motion consistency

### 2.2 Model File / Enable Flag

Downloaded by `docker/download_models.sh` when:

`ENABLE_VACE=true`

| Item | Value |
|---|---|
| Model file | `diffusion_models/wan2.1_vace_14B_fp16.safetensors` |
| Source repo (download script) | `Wan-AI/Wan2.1-VACE-14B` |
| Disk | ~28GB (FP16 14B-class) |
| VRAM | 24-28GB (48GB recommended for heavy edits) |

### 2.3 I/O Specifications (VACE)

**Inputs**

- A source video (as frames or a decoded image sequence)
- Optional mask(s) (binary/alpha) to indicate edit regions
- Prompt (and often a negative prompt)
- Output resolution + number of frames

**Outputs**

- Edited frames
- Combined output video (commonly via `VHS_VideoCombine`)

### 2.4 ComfyUI Workflow Requirements (VACE)

No ready-made VACE workflow JSON is shipped in `docker/workflows/` yet. A production-ready VACE workflow should include:

- A video/frame loader (VideoHelperSuite or equivalent)
- A VACE-capable WAN model loader node (from `ComfyUI-WanVideoWrapper`)
- A sampler node configured for your GPU tier
- A decoder node to frames
- A video combiner/encoder node (`VHS_VideoCombine`)

**Critical production rule:** the workflow must reference the model file by its exact name:

`wan2.1_vace_14B_fp16.safetensors`

### 2.5 Parameter Guidance (VACE)

Start with conservative settings:

- Steps: 20-30
- CFG: 4-7
- Frames: 17-49 (short clips first)
- FPS: 12-24

For mask-based edits, ensure mask resolution matches output resolution (or include an explicit resize step).

## 3) Z-Image Turbo (Fast Text-to-Image)

### 3.1 What Z-Image Turbo Is

Z-Image Turbo is a fast txt2img pipeline that uses:

- A **Qwen** text encoder
- A **Z-Image Turbo** UNet
- An **AE/VAE** decoder

### 3.2 Model Files / Enable Flag

Downloaded by `docker/download_models.sh` when:

`ENABLE_ZIMAGE=true`

| File | Folder |
|---|---|
| `qwen_3_4b.safetensors` | `text_encoders/` |
| `z_image_turbo_bf16.safetensors` | `diffusion_models/` |
| `ae.safetensors` | `vae/` |

**Disk + VRAM notes**

- Disk is commonly cited as **~21GB** for the UNet; total disk for all 3 components is larger.
- Practical VRAM depends heavily on resolution; for 1024x1024, plan on **16GB+** (24GB recommended).

### 3.3 Workflow Template Included

**File:** `docker/workflows/z-image-turbo-txt2img.json`

**Key nodes**

- `UNETLoader`: `z_image_turbo_bf16.safetensors`
- `CLIPLoader`: `qwen_3_4b.safetensors` with `type="qwen_image"` (**must be explicit**)
- `VAELoader`: `ae.safetensors`
- `EmptySD3LatentImage`: latent init
- `KSampler`: sampling
- `SaveImage`: output

**Parameters (as shipped in the file)**

| Setting | Value |
|---|---:|
| Resolution | 1024x1024 |
| Steps | 9 |
| CFG | 1.0 |
| Sampler | `euler` |
| Scheduler | `simple` |

## 4) Realism Illustrious (Photorealistic SDXL)

### 4.1 What It Is

Realism Illustrious is an SDXL checkpoint specialized for photorealistic imagery (portraits, landscapes, product shots).

### 4.2 Model Files / Enable Flags

Downloaded by `docker/download_models.sh` when:

- `ENABLE_ILLUSTRIOUS=true`

Optional:

- `ENABLE_ILLUSTRIOUS_EMBEDDINGS=true` (default in script)

| Item | Path | Notes |
|---|---|---|
| Checkpoint | `checkpoints/realismIllustriousByStableYogi_v50FP16.safetensors` | 6.46GB |
| Positive embedding | `embeddings/Stable_Yogis_Illustrious_Positives.safetensors` | optional |
| Negative embedding | `embeddings/Stable_Yogis_Illustrious_Negatives.safetensors` | optional |

### 4.3 Workflow Templates Included

- `docker/workflows/realism-illustrious-txt2img.json` (uses the StableYogi v5 FP16 filename)
- Additional variants exist (portrait/embeddings/LoRA), but **verify checkpoint filenames** before use.

**Parameters (from `realism-illustrious-txt2img.json`)**

| Setting | Value |
|---|---:|
| Resolution | 1024x1024 |
| Steps | 25 |
| CFG | 7.0 |
| Sampler | `dpmpp_2m` |
| Scheduler | `karras` |

### 4.4 Practical VRAM Guidance (from local testing notes)

Based on `docker/TESTING-NOTES.md`:

- 768x768 succeeded on a 16GB-class GPU.
- 1024x1024 caused an OOM/container restart on 16GB.

For reliable production operation:

- Prefer 768x768 (or portrait 832x1216) on 16GB.
- Use 24GB+ for 1024x1024 with comfortable headroom.

## 5) SteadyDancer (Dance/Motion Video)

### 5.1 What It Is

SteadyDancer is a WAN-family motion-focused model intended for stable dance/human motion generation.

### 5.2 Model File / Enable Flag

Downloaded by `docker/download_models.sh` when:

`ENABLE_STEADYDANCER=true`

| Item | Value |
|---|---|
| Model file | `diffusion_models/Wan21_SteadyDancer_fp16.safetensors` |
| Source repo (download script) | `MCG-NJU/SteadyDancer-14B` |
| Disk | ~28-33GB (FP16 14B-class) |
| VRAM | 24-32GB |

### 5.3 Workflow Requirements

No workflow JSON is shipped for SteadyDancer yet. A typical pipeline looks like:

1. Load WAN dependencies (UMT5 + WAN VAE)
2. Load the SteadyDancer model in `diffusion_models/`
3. Provide prompt + optional pose/motion guidance
4. Sample -> decode frames -> combine to video

## 6) SCAIL (Facial Mocap / Pose)

### 6.1 What It Is

SCAIL is included as a preview model repo intended for facial animation / mocap workflows. This template also installs `ComfyUI-SCAIL-Pose` nodes for pose/facial landmarks integration.

### 6.2 Model Download / Enable Flag

Downloaded by `docker/download_models.sh` when:

`ENABLE_SCAIL=true`

Implementation detail: SCAIL is downloaded via `git clone` + `git lfs pull` into:

`diffusion_models/SCAIL-Preview/`

### 6.3 Workflow Requirements

No workflow JSON is shipped for SCAIL yet. Production-ready workflows should:

- Use `ComfyUI-SCAIL-Pose` nodes for the required conditioning inputs
- Avoid assuming fixed filenames inside `SCAIL-Preview/` (verify after download)
- Start with short clips and moderate resolution to validate VRAM

## 7) ControlNet (Preprocessors + Models)

### 7.1 What is Included

**Preprocessors** are installed via:

- `Fannovel16/comfyui_controlnet_aux` (in `docker/Dockerfile`)

**Models** are downloaded by `docker/download_models.sh` under:

`models/controlnet/`

Default downloaded set is controlled by:

- `ENABLE_CONTROLNET=true` (default)
- `CONTROLNET_MODELS="canny,depth,openpose"` (default)

Available options in script:

- `canny`, `depth`, `openpose`, `lineart`, `normalbae`

### 7.2 Model Files (SD1.5 ControlNet v1.1, FP16)

| Control type | Filename |
|---|---|
| Canny | `control_v11p_sd15_canny_fp16.safetensors` |
| Depth | `control_v11f1p_sd15_depth_fp16.safetensors` |
| OpenPose | `control_v11p_sd15_openpose_fp16.safetensors` |
| Lineart | `control_v11p_sd15_lineart_fp16.safetensors` |
| NormalBae | `control_v11p_sd15_normalbae_fp16.safetensors` |

### 7.3 I/O Specifications (ControlNet)

**Inputs**

- A base diffusion model (often SD1.5) + prompt
- A conditioning image/map (edges, depth, pose, etc.) generated via a preprocessor node or supplied directly

**Outputs**

- Images guided to match the conditioning structure

### 7.4 Workflow Requirements / Notes

- Typical ComfyUI graph (conceptual):
  1. Load a base checkpoint (usually SD1.5 for these ControlNet weights)
  2. Preprocess an input image into a control map (canny/depth/openpose/etc.)
  3. Load a ControlNet model from `models/controlnet/`
  4. Apply ControlNet conditioning to the base model conditioning
  5. Sample -> decode -> save image

- The downloaded ControlNets are **SD1.5** ControlNet models; they are not drop-in for SDXL checkpoints like Illustrious.
- For Illustrious + ControlNet, you need SDXL-compatible ControlNet models (not shipped by this repo).

## 8) Fun InP (First/Last Frame Interpolation)

### 8.1 What It Is

Fun InP is a WAN-family model for generating smooth intermediate frames given a first and last frame ("first-last" control).

### 8.2 Model File / Enable Flag

Downloaded by `docker/download_models.sh` when:

`ENABLE_FUN_INP=true`

| Item | Value |
|---|---|
| Model file | `diffusion_models/wan2.2_fun_inp_14B_fp16.safetensors` |
| Source repo (download script) | `Wan-AI/Wan2.2-Fun-InP-14B` |
| Disk | ~28GB |
| VRAM | 24GB+ |

### 8.3 I/O Specifications

**Inputs**

- Start frame image
- End frame image
- Target number of frames (or an interpolation factor)

**Outputs**

- Interpolated frame sequence
- Combined video (via `VHS_VideoCombine`)

### 8.4 Parameter Guidance

Start with:

- Frames: 17-41
- FPS: 12-24

Use higher frame counts only after validating stability and VRAM headroom.

## 9) Production Workflow Checklist (Zero-Intervention)

Before committing or deploying workflows:

1. Confirm model filenames in workflows exactly match the downloads created by `docker/download_models.sh`.
2. Test locally with Docker:
   - `cd docker && docker compose up -d`
   - Load workflows from `docker/workflows/`
   - Queue a prompt and verify there are **no validation errors**
3. Validate sampler/scheduler values are supported by the ComfyUI version in the image.
4. For video workflows, verify `VHS_VideoCombine` format output (webm/mp4/webp) matches your downstream needs.

## 10) Known Issues and Notes

The following issues have been identified during documentation:

### 10.1 WAN 2.2 5B Workflow Model Not Auto-Downloaded

- `docker/workflows/wan22-t2v-5b.json` references: `diffusion_models/wan2.2_ti2v_5B_fp16.safetensors`
- `docker/download_models.sh` does NOT download this file (no `ENABLE_WAN22_5B` flag, no `hf_download` entry)
- **Result:** workflow will fail until the model is manually added/downloaded

### 10.2 WAN 2.2 Distilled Size Message Misleading

- `docker/download_models.sh` prints: "High noise (14GB) + Low noise (14GB) + shared deps = ~28GB total"
- 28GB is only the two expert diffusion models; shared deps (UMT5 9.5GB + VAE 335MB + CLIP vision 1.4GB) add ~11GB more if not already present

### 10.3 Realism Illustrious Workflow Filename Mismatches

- `docker/download_models.sh` downloads: `checkpoints/realismIllustriousByStableYogi_v50FP16.safetensors`
- Some workflows reference a different filename:
  - `realism-illustrious-basic.json` -> `realismIllustriousBy_v50FP16.safetensors`
  - `realism-illustrious-embeddings.json` -> `realismIllustriousBy_v50FP16.safetensors`
  - `realism-illustrious-nsfw-lora.json` -> `realismIllustriousBy_v50FP16.safetensors`

### 10.4 Z-Image Turbo VRAM Guidance Inconsistent

- `docker/workflows/README.md` claims 8-12GB VRAM
- `docker/TESTING-NOTES.md` states it was skipped due to VRAM constraints ("needs 24GB+")
- **Recommendation:** Treat 24GB as safe for 1024x1024 until re-tested

### 10.5 Missing Ready-Made Workflows

`download_models.sh` can download VACE, SteadyDancer, SCAIL, Fun InP, and ControlNet models, but `docker/workflows/` does not include starter JSON workflows for:
- VACE (wan2.1_vace_14B_fp16.safetensors)
- SteadyDancer (Wan21_SteadyDancer_fp16.safetensors)
- SCAIL (diffusion_models/SCAIL-Preview/)
- Fun InP (wan2.2_fun_inp_14B_fp16.safetensors)
- ControlNet guided workflows

### 10.6 ControlNet Model Family Mismatch Risk

- `download_models.sh` fetches SD1.5 ControlNet v1.1 FP16 models
- Realism Illustrious is an SDXL checkpoint; SD1.5 ControlNets are not drop-in compatible
- If SDXL ControlNet is required, additional SDXL ControlNet model downloads are needed (not in script)

## 11) Repo References

Key files backing this section:

- `docker/download_models.sh` (model downloads, filenames, env flags)
- `docker/Dockerfile` (custom nodes installed)
- `docker/TESTING-NOTES.md` (observed VRAM behavior)
- `docker/workflows/` (starter workflows)
