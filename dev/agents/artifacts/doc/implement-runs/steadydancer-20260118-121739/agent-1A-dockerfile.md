# Agent 1A: Dockerfile Updates

## Changes Applied

### 1. SteadyDancer Dependencies (Lines 179-202)
Added Layer 4.5 with:
- PyTorch 2.5.1 pinning (cu124)
- Pose estimation stack: mmengine, mmcv==2.1.0, mmdet>=3.1.0, mmpose, dwpose>=0.1.0
- Flash Attention 2.7.4.post1 with fallback

### 2. Model Directory Update (Line 222)
Added `steadydancer` to model directories list

### 3. Build Arguments (Lines 231-233)
- ARG BAKE_STEADYDANCER=false
- ARG STEADYDANCER_VARIANT=fp8
- ARG BAKE_TURBO=false

### 4. Build-time Downloads (Lines 276-300)
- SteadyDancer fp16/fp8 download (conditional on BAKE_STEADYDANCER)
- TurboDiffusion download (conditional on BAKE_TURBO)

## Verification
```bash
docker build -t hearmeman-extended:test . --progress=plain 2>&1 | grep -E "(Layer|Step|ERROR)"
```

## Files Modified
- `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile` (lines 179-202, 222, 231-233, 276-300)
