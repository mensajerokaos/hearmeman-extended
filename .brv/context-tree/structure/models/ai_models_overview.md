## Relations
@structure/docker/model_downloader.md
@design/ai_models/model_inventory.md

## Raw Concept
**Task:**
Video and Image Generation Documentation

**Changes:**
- Adds comprehensive documentation for video and image generation stack
- Documents VRAM requirements and I/O specs for 10+ new model variants

**Files:**
- docker/download_models.sh
- docker/workflows/

**Flow:**
User selects generation task -> Workflow loads required model components -> Sampler generates latent -> VAE decodes to frames/image -> VHS_VideoCombine encodes to webm/mp4/webp

**Timestamp:** 2026-01-18

## Narrative
### Structure
- models/diffusion_models/: UNet weights
- models/text_encoders/: Language models
- models/vae/: Autoencoders
- models/controlnet/: Conditioning models
- models/clip_vision/: Vision encoders

### Dependencies
- WAN: UMT5 XXL, WAN VAE, CLIP Vision
- Z-Image: Qwen 3.4B, Z-Image UNet, AE/VAE
- Realism Illustrious: SDXL Checkpoint, Embeddings
- ControlNet: SD1.5 Models (Canny, Depth, OpenPose, etc.)

### Features
- Video Generation: WAN 2.1/2.2 (T2V, I2V, Distilled), VACE (Editing), SteadyDancer (Motion), Fun InP (Interpolation)
- Image Generation: Z-Image Turbo (Fast), Realism Illustrious (Photorealistic)
- Spatial Guidance: ControlNet Preprocessors and Models
- Facial Animation: SCAIL (Mocap/Pose)
