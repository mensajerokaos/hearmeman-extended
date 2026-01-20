## Relations
@structure/generation/wan_video_generation.md
@structure/generation/specialized_generation_models.md

## Raw Concept
**Task:**
Document Video and Image Generation for RunPod Custom Template

**Changes:**
- Consolidated video and image generation documentation from master-documentation.md

**Files:**
- docker/download_models.sh
- docker/Dockerfile

**Flow:**
Select model via ENV -> download_models.sh fetches weights -> Use in ComfyUI workflows

**Timestamp:** 2026-01-18

## Narrative
### Structure
- structure/generation/wan_video_generation.md
- structure/generation/specialized_generation_models.md
- Environment variables for model selection (WAN_720P, ENABLE_ILLUSTRIOUS, etc.)

### Dependencies
- WAN 2.1/2.2, Z-Image Turbo, Realism Illustrious
- ComfyUI-WanVideoWrapper
- Comfyui_turbodiffusion
- ControlNet preprocessors (~3.6GB)

### Features
- WAN 2.1: 720p (~25GB) and 480p (~12GB) T2V
- WAN 2.2: Distilled I2V (TurboDiffusion, ~28GB)
- Z-Image Turbo (~21GB)
- Realism Illustrious (~7GB)
- VACE video editing and SteadyDancer support
