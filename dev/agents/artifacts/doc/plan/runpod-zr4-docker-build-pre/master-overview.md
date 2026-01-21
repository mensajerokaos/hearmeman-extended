## Master Plan: RunPod SteadyDancer Docker Build and Test

### Executive Summary
Build and validate a Docker image for ComfyUI with SteadyDancer dance video generation capabilities. Includes OpenMMLab dependencies (mmcv, mmdet, mmpose, dwpose) and Flash Attention with xformers fallback. Focus on local testing before production deployment to RunPod.

### Architecture
```
Base: comfyui/comfyui:latest
├─ CUDA 12.1 + cuDNN 8.9
├─ PyTorch 2.5.1 (pinned for mmpose)
├─ mmengine 0.10.0 + mmcv 2.1.0 + mmdet 3.1.0 + mmpose 1.0.0 + dwpose 0.1.0
├─ Flash Attention 2.x (with xformers fallback)
└─ SteadyDancer fp8 model (14GB)
```

### Phase Overview
| Phase | Title | Depends On | Parallel With | Est. Steps |
|-------|-------|------------|---------------|------------|
| P1 | Environment Preparation | None | - | 4 |
| P2 | Dockerfile Validation | P1 | - | 4 |
| P3 | Dependency Installation | P2 | P4 | 5 |
| P4 | Model Configuration | P2 | P3 | 4 |
| P5 | Local Docker Build | P3, P4 | - | 5 |
| P6 | Local Testing | P5 | - | 6 |

### Detailed Phases

#### Phase 1: Environment Preparation
**Files**: `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile`
**Steps**:
1. Backup: `cp docker/Dockerfile docker/Dockerfile.backup`
2. Check GPU: `nvidia-smi | grep "CUDA Version"` (expect 12.1+)
3. Check image: `docker images | grep comfyui`
4. Check disk: `df -h /var/lib/docker` (need > 20GB free)
**Verify**: Backup exists, GPU available, > 20GB disk space

#### Phase 2: Dockerfile Validation
**Files**: `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile`
**Steps**:
1. Syntax check: `docker build -t test --no-run -f docker/Dockerfile .`
2. Verify ARGs: `grep -n "ARG.*=" docker/Dockerfile | grep -i "steadydancer\|bake"`
3. Check deps: `grep -n "mmcv\|mmpose\|dwpose" docker/Dockerfile`
4. Confirm env vars: `grep -n "ENABLE_STEADYDANCER\|STEADYDANCER_VARIANT" docker/Dockerfile`
**Verify**: Exit code 0, ARGs present, dependencies listed

#### Phase 3: Dependency Installation
**Files**: `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile`
**Steps**:
1. Build: `docker build --build-arg BAKE_STEADYDANCER=true -t test:v1 .`
2. Monitor: `docker logs -f <container>` (check every 5 min)
3. Check Flash: `grep -i "flash\|xformers" build.log`
4. If Flash fails: Rebuild with `ENABLE_FLASH_ATTN=false`
5. Verify: `docker exec <container> python -c "import mmcv, mmpose; print('OK')"`
**Verify**: Exit code 0, packages import successfully

#### Phase 4: Model Configuration
**Files**: `/home/oz/projects/2025/oz/12/runpod/docker/download_models.sh`
**Steps**:
1. Read script: `grep -n "SteadyDancer" download_models.sh | head -10`
2. Check URL: `curl -sI https://huggingface.co/kijai/SteadyDancer-14B-pruned | head -3`
3. Verify fp8 variant is default
4. Check fallback to fp16 if fp8 unavailable
**Verify**: HTTP 200 response, fp8 variant configured

#### Phase 5: Local Docker Build
**Files**: `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml`
**Steps**:
1. Build: `cd docker && docker compose build --no-cache`
2. Log: `docker compose build 2>&1 | tee build-full.log`
3. Monitor disk: `df -h /var/lib/docker` (warn if > 80%)
4. Check size: `docker images | grep steadydancer`
**Verify**: Exit code 0, image < 50GB, images listed

#### Phase 6: Local Testing
**Files**: `/home/oz/projects/2025/oz/12/runpod/docker/workflows/steadydancer-dance.json`
**Steps**:
1. Start: `docker compose up -d`
2. Wait: `sleep 30` for initialization
3. Check UI: `curl -s http://localhost:8188 | grep -q "ComfyUI" && echo "OK"`
4. Load workflow: Check steadydancer-dance.json loads in ComfyUI
5. Test generation: Queue prompt with small resolution (512x512, 30 frames)
6. Verify output: `ls -la ComfyUI/output/*.mp4 2>/dev/null | head -1`
**Verify**: ComfyUI accessible, video file created

### Parallel Execution Map
```
Wave 1: [P1]
Wave 2: [P2]
Wave 3: [P3, P4] (parallel - different files)
Wave 4: [P5] (depends on P3+P4)
Wave 5: [P6] (depends on P5)
```

### Implementation Checklist
- [ ] Phase 1: Backup created, GPU available, > 20GB disk
- [ ] Phase 2: Dockerfile syntax valid, ARGs present
- [ ] Phase 3: Dependencies install, packages import
- [ ] Phase 4: Model URLs accessible
- [ ] Phase 5: Docker image built (< 50GB)
- [ ] Phase 6: ComfyUI running, video generated
- [ ] All tests pass, 0 LSP/Docker errors
- [ ] Documentation updated in CLAUDE.md

### Ready for /implement: YES ✓
