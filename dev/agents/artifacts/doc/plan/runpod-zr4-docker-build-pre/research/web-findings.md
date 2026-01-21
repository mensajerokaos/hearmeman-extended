# Web Research: RunPod SteadyDancer Docker Build
Generated: 2026-01-21T06:13:00+00:00

## Key Sources
- [SteadyDancer GitHub](https://github.com/MCG-NJU/SteadyDancer)
- [mmcv/mmdet/mmpose Documentation](https://github.com/open-mmlab/mmdetection3d)
- [Flash Attention Installation](https://github.com/Dao-AILab/flash-attention)
- [OpenMMLab Installation Guide](https://mmengine.readthedocs.io/en/latest/get_started/installation.html)

## Main Findings

### SteadyDancer Integration (Already Integrated)
- Model: MCG-NJU/SteadyDancer-14B
- Variants: fp8 (~14GB), fp16 (~28GB), GGUF
- Dependencies: mmengine, mmcv==2.1.0, mmdet>=3.1.0, mmpose, dwpose>=0.1.0
- PyTorch pinned to 2.5.1 for mmpose compatibility

### mmcv/mmdet/mmpose Requirements
- OpenMMLab stack requires specific PyTorch version
- mmcv 2.1.0 compatible with PyTorch 2.5.1
- Installation requires CUDA toolkit matching PyTorch's CUDA version
- Build from source often needed for newer versions

### Flash Attention
- Version conflicts common with different PyTorch/CUDA combinations
- Fallback to xformers recommended for stability
- Flash-attn 2.x requires CUDA 11.8+ and PyTorch 2.0+

## Installation Patterns
```dockerfile
# OpenMMLab stack
RUN pip install mmengine==0.10.0 mmcv==2.1.0 mmdet>=3.1.0 mmpose>=1.0.0

# Flash Attention with fallback
RUN pip install flash-attn --no-build-isolation || pip install xformers
```

## Common Issues
1. **Flash-attn ABI conflicts** → Solution: Fallback to xformers
2. **CUDA version mismatch** → Match PyTorch CUDA to system CUDA
3. **mmpose compatibility** → Pin PyTorch to 2.5.1
4. **Build time** → Use pre-built wheels when available

## Compatibility Matrix
| Component | Version | CUDA | Notes |
|-----------|---------|------|-------|
| PyTorch | 2.5.1 | 12.1 | Pinned for mmpose |
| mmcv | 2.1.0 | 12.1 | Compatible |
| mmdet | 3.1.0+ | 12.1 | Latest stable |
| mmpose | 1.0.0+ | 12.1 | Compatible |
| flash-attn | 2.x | 11.8+ | Fallback to xformers |
