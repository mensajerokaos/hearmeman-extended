---
author: oz
model: claude-opus-4-5-20251101
date: 2025-12-29
task: ComfyUI-Genfocus custom node package implementation
status: completed
---

# ComfyUI-Genfocus Implementation Status

## Summary

Successfully created complete ComfyUI custom node package for Genfocus generative refocusing framework.

## Files Created

| File | Lines | Description |
|------|-------|-------------|
| `__init__.py` | 87 | Node registration, mappings |
| `nodes/loaders.py` | 257 | Model loaders (Deblur, Bokeh, Depth) |
| `nodes/deblur.py` | 237 | GenfocusDeblur processing node |
| `nodes/bokeh.py` | 343 | GenfocusBokeh with focus controls |
| `nodes/pipeline.py` | 289 | All-in-one pipeline + depth estimator |
| `nodes/__init__.py` | 14 | Node exports |
| `utils/tensor_utils.py` | 145 | ComfyUI tensor conversions |
| `utils/__init__.py` | 14 | Utility exports |
| `requirements.txt` | 10 | Dependencies |

**Total**: 9 files, ~1400 lines

## Nodes Registered

1. **GenfocusDeblurNetLoader** - Load DeblurNet (LoRA r=128)
2. **GenfocusBokehNetLoader** - Load BokehNet (LoRA r=64)
3. **GenfocusDepthLoader** - Load depth_pro.pt
4. **GenfocusDeblur** - Diffusion-based deblurring
5. **GenfocusBokeh** - Controllable bokeh synthesis
6. **GenfocusPipeline** - End-to-end refocusing
7. **GenfocusDepthEstimator** - Depth map estimation

## Key Features

- Model caching with lazy loading
- FP16/FP32/BF16 support
- CPU offloading option
- Fallback inference when FLUX unavailable
- Proper ComfyUI tensor format handling
- Focus mask output for compositing
- Multiple aperture shapes (circle, triangle, heart, star)

## Installation

```bash
cd ComfyUI/custom_nodes
git clone [this-repo] ComfyUI-Genfocus
pip install -r ComfyUI-Genfocus/requirements.txt

# Download models
mkdir -p models/genfocus
wget https://huggingface.co/nycu-cplab/Genfocus-Model/resolve/main/deblurNet.safetensors -O models/genfocus/deblurNet.safetensors
wget https://huggingface.co/nycu-cplab/Genfocus-Model/resolve/main/bokehNet.safetensors -O models/genfocus/bokehNet.safetensors
```

## Notes

- Requires HuggingFace auth for FLUX.1-dev backbone
- Full pipeline needs ~20GB VRAM at FP16
- Fallback blur available without FLUX
