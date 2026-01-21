# Local Research: RunPod SteadyDancer Docker Build
Generated: 2026-01-21T06:13:00+00:00

## Files Found
- `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile` - Main Docker build file
- `/home/oz/projects/2025/oz/12/runpod/docker/download_models.sh` - Model download script
- `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml` - Docker compose config
- `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/implement-runs/steadydancer-20260118-121739/` - Previous SteadyDancer integration

## Key Excerpts
From CLAUDE.md:
- SteadyDancer already integrated with ENABLE_STEADYDANCER env var
- PyTorch pinned to 2.5.1 for mmpose compatibility
- Flash-attn with xformers fallback implemented
- Model variants: fp8 (14GB), fp16 (28GB)

## Existing Patterns
1. **Dockerfile Structure** (lines 179-300):
   - SteadyDancer dependencies: mmengine, mmcv==2.1.0, mmdet>=3.1.0, mmpose, dwpose>=0.1.0
   - Build ARGs: BAKE_STEADYDANCER, STEADYDANCER_VARIANT
   - Conditional downloads based on build args

2. **Download Script** (lines 322-435):
   - Model download from HuggingFace
   - fp8/fp16/GGUF variant support
   - Resume capability for partial downloads

3. **Docker Compose** (lines 69-89):
   - Environment variables for SteadyDancer configuration
   - Volume mounts for model directories

## Docker Patterns
- Multi-stage Docker builds
- Build args for conditional installation
- Model downloads at build-time or runtime
- Environment variable configuration

## Dependencies Already Documented
- ✅ mmcv, mmdet, mmpose, dwpose
- ✅ PyTorch 2.5.1 (pinned)
- ✅ Flash-attn with xformers fallback
- ✅ SteadyDancer model variants
- ✅ Workflow files (steadydancer-dance.json, steadydancer-turbo.json)

## Gaps for Web Research
- Latest Flash Attention v2.6.3 compatibility
- CUDA 12.4+ compatibility with mmcv 2.1.0
- Alternative pose estimation (DWPose vs PoseEstimation)
