## Relations
@design/ai_models/model_inventory.md
@structure/models/ai_models_overview.md
@structure/docker/model_downloader.md
@design/ai_models/gpu_tier_recommendations.md

## Raw Concept
**Task:**
Document Video Generation Stack

**Changes:**
- Defines the set of supported AI models and their operational parameters
- Documents fast image generation and photorealistic SDXL workflows
- Notes VRAM limitations for 1024x1024 on 16GB cards
- Highlights SD1.5 ControlNet vs SDXL Illustrious mismatch risk
- Documents advanced video generation models and their VRAM/disk requirements
- Identifies missing auto-download for WAN 2.2 5B model in current scripts

**Files:**
- docker/download_models.sh
- docker/Dockerfile
- docker/workflows/z-image-turbo-txt2img.json
- docker/workflows/realism-illustrious-txt2img.json
- docker/workflows/wan21-t2v-14b-api.json
- docker/workflows/wan22-t2v-5b.json

**Flow:**
Prompt -> UMT5 Encoder -> Diffusion Model -> WAN VAE Decode -> VHS Video Combine -> Output Video

**Timestamp:** 2026-01-18

## Narrative
### Structure
- `section-002-ai-models.md`
- Model inventory table and GPU selection guide

- models/text_encoders/qwen_3_4b.safetensors
- models/diffusion_models/z_image_turbo_bf16.safetensors
- models/checkpoints/realismIllustriousByStableYogi_v50FP16.safetensors
- models/controlnet/control_v11p_sd15_*.safetensors

- models/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors
- models/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors
- models/diffusion_models/wan2.1_vace_14B_fp16.safetensors
- models/diffusion_models/Wan21_SteadyDancer_fp16.safetensors
- models/diffusion_models/wan2.2_fun_inp_14B_fp16.safetensors

### Dependencies
- WAN 2.1/2.2: HuggingFace (Comfy-Org repackaged)
- VibeVoice: microsoft/aoi-ot/FabioSarracino
- Illustrious: CivitAI (ID 2091367)
- Qwen-Edit: unsloth GGUF or HuggingFace full precision

- Z-Image: Qwen text encoder, Z-Image UNet, AE/VAE decoder
- Illustrious: SDXL base, optional embeddings (Stable Yogi)

- WAN shared deps: UMT5 XXL (9.5GB), WAN VAE (335MB), CLIP Vision H (1.4GB)
- TurboDiffusion requires `Comfyui_turbodiffusion` node
- VACE requires 24-28GB VRAM (48GB recommended)

### Features
- Categorized by GPU tier (Consumer, Prosumer, Datacenter)
- Includes VRAM and Disk requirements for each model
- Maps environment variables to model components
- Standardized paths under `/workspace/ComfyUI/models`

- Z-Image Turbo: Fast txt2img, 1024x1024 resolution, 16-24GB VRAM
- Realism Illustrious: Photorealistic SDXL checkpoint, 8-16GB VRAM
- ControlNet: Spatial guidance (canny, depth, openpose, lineart, normalbae) for SD1.5

- WAN 2.1/2.2: T2V (1.3B/14B), I2V (14B), distilled experts for TurboDiffusion
- VACE: Mask-based video editing and inpainting
- SteadyDancer: Stable dance/motion generation (14B)
- Fun InP: First/last frame interpolation (14B)
