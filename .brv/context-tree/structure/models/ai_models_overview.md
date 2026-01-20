## Relations
@design/ai_models/gpu_tier_recommendations.md
@structure/models/generation/video_and_image_generation_models.md

## Raw Concept
**Task:**
Document AI Models Configuration for RunPod Custom Template

**Changes:**
- Updated model configuration and VRAM requirements from master-documentation.md

**Files:**
- docker/download_models.sh
- docker/start.sh

**Flow:**
Environment Variables -> start.sh (VRAM detection) -> download_models.sh (conditional fetching)

**Timestamp:** 2026-01-18

## Narrative
### Structure
- /workspace/ComfyUI/models: Model storage root
- Environment variables reference table
- GPU VRAM requirement matrix

### Dependencies
- Environment variables for model enabling (ENABLE_VIBEVOICE, WAN_720P, etc.)
- GPU Tier (consumer, prosumer, datacenter)
- Memory Mode (auto, sequential_cpu_offload, model_cpu_offload)

### Features
- Support for WAN 2.1/2.2, VibeVoice, Realism Illustrious, Z-Image Turbo
- Automatic VRAM detection and optimization
- Model downloading via wget, curl, and huggingface_hub
- CivitAI API integration
