---
author: $USER
model: plan00-iter1
date: 2026-01-21
task: Build and test Docker image locally (runpod-zr4)
---

# Operational Context: Docker Build for ComfyUI + SteadyDancer

## Dockerfile Layer Structure

The Dockerfile is organized into a multi-layer build process designed for production-ready AI generation environments:

1. **Base Layer**: Uses the **RunPod PyTorch CUDA** image.
2. **System Dependencies**: Includes `git`, `ffmpeg`, `OpenGL`, `SSH`, and `aria2`.
3. **Core Application**: Installation of **ComfyUI** (cloned into `/workspace/ComfyUI`).
4. **Custom Nodes**: Integration of third-party nodes (e.g., ComfyUI-Manager) and local custom nodes (`Genfocus`, `MVInverse`).
5. **Specialized Dependency Layers (Layers 4 & 5)**: This is where heavy dependencies like `mmcv` and `flash-attn` are installed.

## Pinned Versions

The following specific versions have been verified and pinned to ensure compatibility, particularly for **RTX 4080 SUPER (16GB)** targets:

- **PyTorch**: `2.5.1+cu124`
- **mmcv**: `2.1.0`
- **flash_attn**: `2.7.4.post1`
- **Other Key Deps**: `mmpose`, `dwpose` (verified alongside mmcv 2.1.0)

## Build Optimizations

- **Wave-based Dependency Pinning**: A strategy used to ensure that complex dependencies (like the mmcv/mmpose stack) are installed in a sequence that avoids version conflicts
- **Performance**: The build process is optimized for speed, with a verified build performance of approximately **158 seconds**
- **Conditional Baking**: Supports optional model baking (e.g., WAN, Illustrious) via build arguments

## Key Files

- `docker/Dockerfile`: Multi-layer architecture
- `docker/start.sh`: Container entrypoint orchestrating the startup sequence
- `docker/download_models.sh`: Logic for fetching model weights on startup
- `docker-compose.yml`: Local development with NVIDIA runtime

## Environment Variables

| Variable | Default | Notes |
|----------|---------|-------|
| `ENABLE_STEADYDANCER` | false | Dance video generation (I2V) |
| `STEADYDANCER_VARIANT` | fp8 | Model quantization (fp8/fp16/gguf) |
| `ENABLE_DWPOSE` | false | Pose extraction for dance video |
| `ENABLE_VIBEVOICE` | true | VibeVoice-Large TTS (~18GB) |

## Local Testing Procedure

```bash
cd docker
docker compose build
docker compose up -d
```

## VRAM Considerations

- 16GB (4080 SUPER): Use GGUF variant (~7GB VRAM)
- 24GB+ (A6000, L40S): Use fp16 variant (~14GB VRAM)
- Disable other heavy services (VibeVoice, XTTS, Chatterbox) to free ~24GB when running SteadyDancer
