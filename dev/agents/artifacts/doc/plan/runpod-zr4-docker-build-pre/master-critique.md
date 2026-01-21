## Master Plan Self-Critique: Pass 2

### Clarity Score: 7/10

### Vague Words Found

1. "Verify" - used multiple times without specifying what verification means
   - Line: "Verify current Dockerfile state"
   - Fix: Specify exact commands to run

2. "Check" - used without clear criteria
   - Line: "Check existing dependencies"
   - Fix: "Run pip list and grep for mmcv, mmdet, mmpose versions"

3. "Validate" - repeated without clear success criteria
   - Line: "Validate Dockerfile syntax"
   - Fix: "Run hadolint or docker build --dry-run"

4. "Optimize if needed" - vague
   - Line: "Optimize if needed"
   - Fix: "If build fails or exceeds 30 minutes, add caching and parallel builds"

5. "Monitor build progress" - no specific metrics
   - Line: "Monitor build progress"
   - Fix: "Monitor build logs every 5 minutes, check for ERROR keywords"

### Missing Edge Cases

1. **GPU availability during build**
   - Docker build may fail if no GPU available on build machine
   - Add: "Ensure build machine has NVIDIA GPU or use buildx with remote builder"

2. **Docker buildx cache exhaustion**
   - Build cache can fill disk space
   - Add: "Clear Docker cache if disk usage > 80%"

3. **Network timeouts during downloads**
   - Model downloads can timeout
   - Add: "Implement retry with exponential backoff for downloads"

4. **Permission issues**
   - Some pip installs may require sudo
   - Add: "Use --user flag or check sudo availability"

5. **Version conflicts between packages**
   - mmcv 2.1.0 may conflict with other dependencies
   - Add: "Create virtual environment or use Docker build secrets"

### Improved Draft

## Master Plan Draft v1.5: RunPod SteadyDancer Docker Build and Test

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Build Architecture                     │
├─────────────────────────────────────────────────────────────────┤
│  Base Image: comfyui/comfyui:latest                              │
│       ↓                                                          │
│  ├─ Layer 1: System Dependencies                                 │
│  │   ├─ CUDA 12.1 Toolkit                                        │
│  │   ├─ cuDNN 8.9+                                               │
│  │   ├─ FFmpeg, Git, CMake, Make                                 │
│  │   └─ Python 3.11+                                             │
│  │                                                                │
│  ├─ Layer 2: PyTorch + CUDA                                      │
│  │   ├─ PyTorch 2.5.1 (pinned for mmpose compatibility)          │
│  │   ├─ CUDA 12.1 runtime                                        │
│  │   └─ torchvision, torchaudio                                  │
│  │                                                                │
│  ├─ Layer 3: OpenMMLab Stack                                     │
│  │   ├─ mmengine 0.10.0                                          │
│  │   ├─ mmcv 2.1.0                                               │
│  │   ├─ mmdet 3.1.0+                                             │
│  │   ├─ mmpose 1.0.0+                                            │
│  │   └─ dwpose 0.1.0+ (pose estimation)                          │
│  │                                                                │
│  ├─ Layer 4: Attention Mechanisms                                │
│  │   ├─ Flash Attention 2.x (with fallback)                      │
│  │   └─ xformers 0.0.27+                                         │
│  │                                                                │
│  ├─ Layer 5: ComfyUI + Custom Nodes                              │
│  │   ├─ ComfyUI core                                             │
│  │   ├─ ComfyUI-Manager                                          │
│  │   └─ SteadyDancer custom nodes                                │
│  │                                                                │
│  └─ Layer 6: Model Downloads (Build-time)                        │
│      ├─ SteadyDancer fp8/fp16/GGUF variants                      │
│      ├─ DWPose models                                            │
│      └─ ControlNet models                                        │
└─────────────────────────────────────────────────────────────────┘
```

### Proposed Phases

1. **Phase 1: Environment Preparation**
   - Read current Dockerfile: `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile`
   - Run `docker images | grep comfyui` to check base image
   - Run `nvidia-smi` to verify GPU availability and CUDA version
   - Backup Dockerfile: `cp docker/Dockerfile docker/Dockerfile.backup`
   - Verify: Dockerfile exists and has lines > 100

2. **Phase 2: Dockerfile Validation**
   - Run `docker build --help` to verify docker buildx available
   - Run `docker build -t test --no-run -f docker/Dockerfile .`
   - Check build-args: `grep -n "ARG.*=" docker/Dockerfile | head -20`
   - Verify: Exit code 0, no syntax errors

3. **Phase 3: Dependency Installation**
   - Create build command: `docker build --build-arg BAKE_STEADYDANCER=true -t steadydancer:test .`
   - Monitor: `docker logs -f <container_id>` (tail logs every 5 min)
   - If Flash-attn fails: Check logs for "error: invalid command 'bdist_wheel'"
   - Fallback: Rebuild with `ENABLE_FLASH_ATTN=false`
   - Verify: `docker exec <container> python -c "import mmcv; import mmpose; print('OK')"`

4. **Phase 4: Model Configuration**
   - Read download script: `/home/oz/projects/2025/oz/12/runpod/docker/download_models.sh`
   - Check model URLs: `grep -n "SteadyDancer\|steadydancer" download_models.sh`
   - Verify HuggingFace access: `curl -I https://huggingface.co/api/models/kijai/SteadyDancer-14B-pruned`
   - Test: Download one small file (e.g., config.json) to verify connectivity
   - Verify: Exit code 0, file size > 0

5. **Phase 5: Local Docker Build**
   - Execute: `cd docker && docker compose build --no-cache`
   - Timeout: 45 minutes max (kill if exceeds)
   - Monitor disk: `df -h /var/lib/docker` (warn if > 80%)
   - Capture errors: `docker compose build 2>&1 | tee build.log`
   - Verify: Exit code 0, image size < 50GB

6. **Phase 6: Local Testing**
   - Start: `docker compose up -d`
   - Wait: `sleep 30` for ComfyUI to initialize
   - Check: `curl -s http://localhost:8188 | grep -q "ComfyUI" && echo "OK"`
   - Load workflow: `steadydancer-dance.json`
   - Queue prompt and verify no validation errors
   - Generate test video (use small resolution for speed)
   - Verify: Video file created in output directory

### Dependencies

| Phase | Depends On | Blocks | Can Run Parallel With |
|-------|------------|--------|----------------------|
| P1: Environment Prep | None | P2 | - |
| P2: Dockerfile Validation | P1 | P3 | - |
| P3: Dependency Installation | P2 | P5 | P4 |
| P4: Model Configuration | P2 | P5 | P3 |
| P5: Docker Build | P3, P4 | P6 | - |
| P6: Local Testing | P5 | None | - |

**Parallel execution: P3 and P4 can run concurrently**

### Risks

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Flash-attn build failure | Medium | High | Use xformers fallback, set `ENABLE_FLASH_ATTN=false` |
| CUDA version mismatch | High | Medium | Pin PyTorch 2.5.1 + CUDA 12.1, verify with `nvidia-smi` |
| mmcv compatibility | Medium | Low | Use mmcv 2.1.0 (tested with PyTorch 2.5.1) |
| Build timeouts | Low | Low | Use multi-stage builds, cache layers, set 45-min timeout |
| Model download failures | Medium | Low | Implement retry logic, use HF mirror, verify with curl |
| Docker memory exhaustion | Medium | Medium | Monitor disk space, clear cache if > 80% used |

### Open Questions

1. **Flash-attn source vs wheels** - Use pre-built wheels with fallback to xformers (simpler, faster)
2. **Build-time vs runtime downloads** - Build-time for reproducibility, runtime for flexibility
3. **Variant selection** - Include fp8 only (14GB) for faster builds, document fp16 option
4. **Pose estimation** - Use DWPose (already integrated), no need for alternatives
5. **ControlNet dependencies** - Include for dance video (already in SteadyDancer workflow)

### Implementation Notes

**Key Files Modified:**
- `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile` (add/verify dependencies)
- `/home/oz/projects/2025/oz/12/runpod/docker/download_models.sh` (model variants)
- `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml` (environment variables)

**Key Environment Variables:**
- `ENABLE_STEADYDANCER=true`
- `STEADYDANCER_VARIANT=fp8`
- `ENABLE_FLASH_ATTN=true` (with automatic fallback)

**Verification Commands:**
```bash
# Phase 1
ls -la docker/Dockerfile
nvidia-smi | grep "CUDA Version"

# Phase 2
docker build --help
docker build -t test --no-run -f docker/Dockerfile .

# Phase 3
docker build --build-arg BAKE_STEADYDANCER=true -t test:v1 . 2>&1 | tee build.log
grep -i "error\|failed" build.log

# Phase 4
curl -sI https://huggingface.co/kijai/SteadyDancer-14B-pruned | head -5

# Phase 5
cd docker && docker compose build --no-cache 2>&1 | tee build-full.log
docker images | grep steadydancer

# Phase 6
docker compose up -d
sleep 30 && curl -s http://localhost:8188 | grep -q "ComfyUI" && echo "ComfyUI OK"
```
