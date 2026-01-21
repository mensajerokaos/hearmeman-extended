# Operational Context

## Target Platform
- **Hardware**: NVIDIA RTX 4080 SUPER (16GB VRAM)
- **Quantization**: GGUF (~7GB VRAM usage for models)
- **CUDA Version**: 12.4 (cu124)

## Core Dependencies
- **PyTorch**: 2.5.1+cu124
- **MMCV**: 2.1.0 (Computer Vision)
- **MMPose**: 1.3.0 (Pose Estimation)
- **Flash Attention**: 2.7.4.post1
- **ComfyUI**: Latest stable with custom nodes

## Application Stack
- **SteadyDancer**: Video generation (I2V - Image to Video)
- **ComfyUI**: WebUI for workflow orchestration
- **R2 Sync**: Cloudflare R2 for output persistence

## Build Requirements
- Multi-layer Dockerfile optimization
- VRAM-aware model loading (GGUF quantization)
- Local Docker testing workflow
- Production-ready deployment on RunPod

## Reference Architecture
- Based on existing ComfyUI + VibeVoice templates
- Model download on startup (ephemeral storage)
- Environment-driven feature flags
