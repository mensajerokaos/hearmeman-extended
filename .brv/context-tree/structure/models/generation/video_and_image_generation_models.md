## Relations
@structure/models/ai_models_overview.md
@structure/docker/model_downloader.md

## Raw Concept
**Task:**
Video and Image Generation Documentation

**Changes:**
- Documents the complete video and image generation model stack
- Specifies VRAM requirements and I/O formats for each model type
- Identifies filename and download mismatches in current workflows

**Files:**
- docker/download_models.sh
- docker/workflows/
- docker/Dockerfile

**Flow:**
User selects model -> start.sh detects VRAM -> download_models.sh fetches enabled models -> ComfyUI node loads model from /workspace/ComfyUI/models/ -> Workflow executes generation

**Timestamp:** 2026-01-17

## Narrative
### Structure
- models/diffusion_models/: UNet weights
- models/text_encoders/: Language models
- models/vae/: Variational Autoencoders
- models/clip_vision/: Vision encoders
- models/controlnet/: ControlNet weights
- models/checkpoints/: Base model checkpoints

### Dependencies
- WAN 2.1/2.2: UMT5 text encoder, WAN VAE, CLIP Vision
- VACE: wan2.1_vace_14B_fp16.safetensors
- Z-Image Turbo: Qwen text encoder, AE/VAE decoder
- Realism Illustrious: StableYogi v50 FP16
- SteadyDancer: mcg-nju/SteadyDancer-14B
- SCAIL: zai-org/SCAIL-Preview (Git LFS)
- ControlNet: SD1.5 ControlNet v1.1 FP16 models
- Fun InP: wan2.2_fun_inp_14B_fp16.safetensors

### Features
- Text-to-Video (T2V) and Image-to-Video (I2V) via WAN 2.x
- Fast I2V via TurboDiffusion (distilled expert models)
- Video editing via VACE (inpainting/outpainting)
- Photorealistic txt2img via Realism Illustrious (SDXL)
- Dance/motion video via SteadyDancer
- Facial mocap/animation via SCAIL
- Spatial guidance via ControlNet (SD1.5)
- Frame interpolation via Fun InP (first-last control)
