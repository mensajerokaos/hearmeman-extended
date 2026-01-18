## Relations
@structure/models/ai_models_overview.md
@design/ai_models/gpu_tier_recommendations.md

## Raw Concept
**Task:**
Document WAN Video Generation Stack

**Changes:**
- Documents the WAN video generation stack and its dependencies
- Provides VRAM guidance and resolution constraints for video models

**Files:**
- docker/download_models.sh
- docker/workflows/wan21-t2v-14b-api.json
- docker/workflows/wan22-t2v-5b.json

**Flow:**
Prompt/Image -> WAN Model Loader -> Sampler -> Decode -> VHS_VideoCombine -> Output Video

**Timestamp:** 2026-01-18

## Narrative
### Structure
- models/diffusion_models/wan2.1_*
- models/text_encoders/umt5_*
- models/vae/wan_*
- docker/workflows/wan21-t2v-14b-api.json
- docker/workflows/wan22-t2v-5b.json

### Dependencies
- ComfyUI-WanVideoWrapper
- Comfyui_turbodiffusion (for distilled)
- umt5_xxl_fp8_e4m3fn_scaled.safetensors (9.5GB)
- wan_2.1_vae.safetensors (335MB)
- clip_vision_h.safetensors (1.4GB)

### Features
- WAN 2.1 T2V 14B (FP8): High-quality text-to-video (24GB+ VRAM)
- WAN 2.1 I2V 14B (FP8): Image-to-video conditioning
- WAN 2.1 T2V 1.3B (FP16): Smaller model for 12-16GB VRAM
- WAN 2.2 Distilled (TurboDiffusion): 4-step fast I2V generation
- DIVISIBLE_BY_16: Resolution constraint for most WAN workflows
