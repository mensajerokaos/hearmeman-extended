## Relations
@structure/docker/docker_compose_configuration.md
@structure/docker/startup_process.md

## Raw Concept
**Task:**
Build the production-ready Docker image for RunPod pods

**Changes:**
- Builds a single image containing the entire ComfyUI ecosystem and dependencies

**Files:**
- docker/Dockerfile

**Flow:**
docker build -> system deps -> ComfyUI clone -> nodes install -> scripts copy -> (optional) model bake

**Timestamp:** 2026-01-18T05:38:56.747Z

## Narrative
### Structure
- `docker/Dockerfile`
- Layers for system deps, ComfyUI base, third-party nodes, local nodes, and extra deps

### Dependencies
- Base image: Configurable via `BASE_IMAGE` (default: RunPod PyTorch CUDA)
- Requires internet access for clones and downloads
- Optional model baking via build args (`BAKE_WAN_720P`, etc.)

### Features
- Multi-layer build process
- Clones ComfyUI and various third-party custom nodes
- Includes local custom nodes (`ComfyUI-Genfocus`, `ComfyUI-MVInverse`)
- Installs system dependencies (ffmpeg, aria2, etc.)
- Supports optional model baking for faster startup
