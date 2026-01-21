## Master Plan Draft: RunPod SteadyDancer Docker Build and Test

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
   - Verify current Dockerfile state
   - Check existing dependencies
   - Identify gaps in current configuration
   - Backup current Dockerfile

2. **Phase 2: Dockerfile Validation**
   - Validate Dockerfile syntax
   - Check build-arg availability
   - Verify CUDA/PyTorch compatibility
   - Test Docker build context

3. **Phase 3: Dependency Installation**
   - Install OpenMMLab stack
   - Configure Flash Attention with fallback
   - Set up DWPose dependencies
   - Verify Python package versions

4. **Phase 4: Model Configuration**
   - Update download script for variants
   - Configure model directories
   - Set environment variables
   - Validate model URLs

5. **Phase 5: Local Docker Build**
   - Execute docker build
   - Monitor build progress
   - Capture build errors
   - Optimize if needed

6. **Phase 6: Local Testing**
   - Start Docker containers
   - Validate ComfyUI access
   - Test SteadyDancer workflow
   - Verify video generation

### Dependencies

| Phase | Depends On | Blocks |
|-------|------------|--------|
| P1: Environment Prep | None | P2 |
| P2: Dockerfile Validation | P1 | P3 |
| P3: Dependency Installation | P2 | P4, P5 |
| P4: Model Configuration | P2 | None (parallel with P3) |
| P5: Docker Build | P3, P4 | P6 |
| P6: Local Testing | P5 | None |

**Parallel execution possible between P3 and P4**

### Risks

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Flash-attn build failure | Medium | High | Use xformers fallback |
| CUDA version mismatch | High | Medium | Pin PyTorch 2.5.1 + CUDA 12.1 |
| mmcv compatibility | Medium | Low | Use mmcv 2.1.0 (tested with PyTorch 2.5.1) |
| Build timeouts | Low | Low | Use multi-stage builds, cache layers |
| Model download failures | Medium | Low | Implement retry logic, use HF mirror |
| Docker memory exhaustion | Medium | Medium | Limit parallel build stages |

### Open Questions

1. Should Flash-attn be built from source or use pre-built wheels?
2. Should model downloads happen at build-time or runtime?
3. Should we include both fp8 and fp16 variants or just fp8 (smaller)?
4. Should we use DWPose or move to a lighter alternative?
5. Should we include ControlNet dependencies for dance video generation?

### Initial Concerns

1. **Flash-attn ABI conflicts** - Known issue with PyTorch 2.5.1; xformers fallback implemented
2. **Build size** - OpenMMLab stack adds significant image size (~5-10GB)
3. **Build time** - mmcv from source can take 10-20 minutes
4. **GPU compatibility** - Need to ensure CUDA versions match between PyTorch and system
