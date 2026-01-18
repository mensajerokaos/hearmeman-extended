## Relations
@structure/models/ai_models_overview.md
@structure/generation/wan_video_generation.md

## Raw Concept
**Task:**
Document Specialized Generation Models

**Changes:**
- Documents specialized image and video generation models beyond standard WAN T2V/I2V
- Specifies VRAM requirements and model file names for production workflows

**Files:**
- docker/download_models.sh
- docker/workflows/z-image-turbo-txt2img.json
- docker/workflows/realism-illustrious-txt2img.json

**Flow:**
Model Loader -> Sampler -> VAE Decode -> Output Image/Video

**Timestamp:** 2026-01-18

## Narrative
### Structure
- models/checkpoints/realismIllustrious*
- models/diffusion_models/z_image_turbo*
- models/controlnet/control_v11*
- models/diffusion_models/wan2.1_vace*
- models/diffusion_models/Wan21_SteadyDancer*
- models/diffusion_models/SCAIL-Preview/
- models/diffusion_models/wan2.2_fun_inp*

### Dependencies
- SDXL base (Realism Illustrious)
- Qwen text encoder (Z-Image Turbo)
- SD1.5 base (ControlNet v1.1)

### Features
- Realism Illustrious: Specialized SDXL for photorealism (8-16GB VRAM)
- Z-Image Turbo: Fast txt2img using Qwen encoder (16GB+ VRAM)
- ControlNet (SD1.5): Spatial guidance (canny, depth, openpose, lineart, normalbae)
- VACE: WAN-family video editing (inpainting/outpainting, 24-28GB VRAM)
- SteadyDancer: Motion-focused video generation (24-32GB VRAM)
- SCAIL: Facial animation and mocap workflows
- Fun InP: First/last frame interpolation for smooth video
