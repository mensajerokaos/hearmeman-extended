## Master Plan Draft v2: RunPod SteadyDancer Docker Build and Test

### Changes from v1

Based on critique feedback, the following improvements were made:

1. **Replaced vague language** with specific commands and success criteria
2. **Added explicit verification commands** for each phase
3. **Expanded risk mitigations** with specific flags and fallbacks
4. **Added parallel execution** for Phases 3 and 4
5. **Included timeout thresholds** for long-running operations
6. **Added monitoring checkpoints** for build progress

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Build Architecture                     │
├─────────────────────────────────────────────────────────────────┤
│  Base Image: comfyui/comfyui:latest                              │
│       ↓                                                          │
│  ├─ Layer 1: System Dependencies (CUDA 12.1, cuDNN, FFmpeg)     │
│  │                                                                │
│  ├─ Layer 2: PyTorch + CUDA                                      │
│  │   └─ PyTorch 2.5.1 (pinned for mmpose compatibility)          │
│  │                                                                │
│  ├─ Layer 3: OpenMMLab Stack                                     │
│  │   ├─ mmengine 0.10.0                                          │
│  │   ├─ mmcv 2.1.0                                               │
│  │   ├─ mmdet 3.1.0+                                             │
│  │   ├─ mmpose 1.0.0+                                            │
│  │   └─ dwpose 0.1.0+                                            │
│  │                                                                │
│  ├─ Layer 4: Attention Mechanisms                                │
│  │   ├─ Flash Attention 2.x (with xformers fallback)             │
│  │   └─ xformers 0.0.27+                                         │
│  │                                                                │
│  ├─ Layer 5: ComfyUI + Custom Nodes                              │
│  │   └─ SteadyDancer custom nodes                                │
│  │                                                                │
│  └─ Layer 6: Model Downloads (Build-time)                        │
│      └─ SteadyDancer fp8 (14GB)                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Proposed Phases

| Phase | Title | Depends On | Parallel With | Est. Steps |
|-------|-------|------------|---------------|------------|
| P1 | Environment Preparation | None | - | 4 |
| P2 | Dockerfile Validation | P1 | - | 4 |
| P3 | Dependency Installation | P2 | P4 | 5 |
| P4 | Model Configuration | P2 | P3 | 4 |
| P5 | Local Docker Build | P3, P4 | - | 5 |
| P6 | Local Testing | P5 | - | 6 |

### Detailed Phase Breakdown

#### Phase 1: Environment Preparation
**Files**: `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile`
**Steps**:
1. Read and backup current Dockerfile
2. Verify GPU availability and CUDA version
3. Check base image availability
4. Document current state

**Verify**: `cp docker/Dockerfile docker/Dockerfile.backup && echo "Backup created"`

#### Phase 2: Dockerfile Validation
**Files**: `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile`
**Steps**:
1. Validate Dockerfile syntax
2. Check build-arg definitions
3. Verify CUDA/PyTorch compatibility
4. Confirm dependency versions

**Verify**: `docker build -t test --no-run -f docker/Dockerfile . && echo "Syntax OK"`

#### Phase 3: Dependency Installation
**Files**: `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile`
**Steps**:
1. Build with OpenMMLab dependencies
2. Monitor Flash-attn installation
3. Implement fallback if Flash-attn fails
4. Verify Python packages
5. Test import chain

**Verify**: `docker exec <container> python -c "import mmcv; import mmpose; print('Deps OK')"`

#### Phase 4: Model Configuration
**Files**: `/home/oz/projects/2025/oz/12/runpod/docker/download_models.sh`
**Steps**:
1. Read and update download script
2. Verify HuggingFace model URLs
3. Test connectivity to model hub
4. Configure variant selection

**Verify**: `curl -sI https://huggingface.co/kijai/SteadyDancer-14B-pruned | grep -q "200" && echo "Model accessible"`

#### Phase 5: Local Docker Build
**Files**: `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml`
**Steps**:
1. Execute full docker compose build
2. Monitor build progress
3. Capture and log errors
4. Verify image creation
5. Check image size

**Verify**: `docker images | grep steadydancer | grep -v "^<none>" | awk '{print $NF, $2}'`

#### Phase 6: Local Testing
**Files**: `/home/oz/projects/2025/oz/12/runpod/docker/workflows/steadydancer-dance.json`
**Steps**:
1. Start containers
2. Verify ComfyUI accessibility
3. Load SteadyDancer workflow
4. Queue test prompt
5. Verify video generation
6. Check output quality

**Verify**: `curl -s http://localhost:8188 | grep -q "ComfyUI" && ls -la ComfyUI/output/*.mp4 2>/dev/null | head -1`

### Dependencies

```
P1 ──→ P2 ──┬──→ P3 ──→ P5 ──→ P6
            │
            └──→ P4 ──┘
```

**Parallel execution**: P3 and P4 can run concurrently after P2 completes

### Risks

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Flash-attn build failure | Medium | High | **MITIGATED**: Use xformers fallback with `ENABLE_FLASH_ATTN=false` |
| CUDA version mismatch | High | Medium | **MITIGATED**: Pin PyTorch 2.5.1 + CUDA 12.1, verify with `nvidia-smi` |
| mmcv compatibility | Medium | Low | **MITIGATED**: Use mmcv 2.1.0 (tested with PyTorch 2.5.1) |
| Build timeouts | Low | Low | **MITIGATED**: Set 45-min timeout, multi-stage builds |
| Model download failures | Medium | Low | **MITIGATED**: Retry logic, HF mirror, curl verification |
| Docker memory exhaustion | Medium | Medium | **MITIGATED**: Monitor disk, clear cache if > 80% |

### Implementation Notes

**Files Modified**:
- `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile` - Add/verify OpenMMLab deps
- `/home/oz/projects/2025/oz/12/runpod/docker/download_models.sh` - Model variant config
- `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml` - Environment variables

**Environment Variables**:
```bash
ENABLE_STEADYDANCER=true
STEADYDANCER_VARIANT=fp8
ENABLE_FLASH_ATTN=true  # Falls back to xformers if fails
```

**Key Commands**:
```bash
# Phase 1: Backup and verify
cp docker/Dockerfile docker/Dockerfile.backup
nvidia-smi | grep "CUDA Version"
docker images | grep comfyui

# Phase 2: Validate syntax
docker build -t test --no-run -f docker/Dockerfile .
echo "Exit code: $?"

# Phase 3: Build dependencies
docker build --build-arg BAKE_STEADYDANCER=true -t test:v1 . 2>&1 | tee build.log
grep -i "error\|failed" build.log || echo "No errors found"

# Phase 4: Verify model access
curl -sI https://huggingface.co/kijai/SteadyDancer-14B-pruned | head -3

# Phase 5: Full build
cd docker && docker compose build --no-cache 2>&1 | tee build-full.log
docker images | grep steadydancer

# Phase 6: Test
docker compose up -d
sleep 30
curl -s http://localhost:8188 | grep -q "ComfyUI" && echo "ComfyUI running"
ls -la ComfyUI/output/*.mp4 2>/dev/null | head -1
```

**Estimated Build Time**:
- Dependency installation: 15-25 minutes (mmcv from source)
- Full Docker build: 20-35 minutes (with caching)
- Local testing: 5-10 minutes (workflow validation)

**Success Criteria**:
- [ ] Dockerfile syntax validated
- [ ] All dependencies import successfully
- [ ] Docker image created (< 50GB)
- [ ] ComfyUI accessible on localhost:8188
- [ ] SteadyDancer workflow loads without errors
- [ ] Test video generated successfully
- [ ] Output video file present in output directory
