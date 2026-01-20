# Agent 1B: Download Script Updates

## Changes Applied

### 1. Enhanced SteadyDancer Section (Lines 322-394)
- Added fp8/fp16/GGUF variant support via STEADYDANCER_VARIANT
- fp8: kijai/SteadyDancer-14B-pruned (14GB)
- fp16: MCG-NJU/SteadyDancer-14B (28GB)
- GGUF: MCG-NJU/SteadyDancer-GGUF (7GB)
- Shared dependency checks (UMT5, CLIP Vision, VAE)

### 2. DWPose Section (Lines 396-418)
- yzd-v/DWPose weights (~2GB)
- ControlNet openpose model (~1.2GB)

### 3. TurboDiffusion Section (Lines 420-435)
- kijai/wan-2.1-turbodiffusion (~14GB)

## Verification
```bash
bash -n /home/oz/projects/2025/oz/12/runpod/docker/download_models.sh
```

## Files Modified
- `/home/oz/projects/2025/oz/12/runpod/docker/download_models.sh` (lines 322-435)
