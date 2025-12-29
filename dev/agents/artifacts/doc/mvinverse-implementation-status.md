---
author: oz
model: claude-opus-4-5
date: 2025-12-29
task: MVInverse ComfyUI Custom Node Implementation
---

# MVInverse ComfyUI Implementation Status

## Status: COMPLETE

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 27 | Node registration |
| `mvinverse_loader.py` | 197 | Model loading with caching |
| `mvinverse_inverse.py` | 256 | Inverse rendering execution |
| `requirements.txt` | 18 | Dependencies |

**Location**: `/home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-MVInverse/`

## Features Implemented

### MVInverseLoader Node
- HF Hub download (maddog241/mvinverse)
- Local checkpoint scanning
- Model caching (avoid reloading)
- FP16/FP32/auto precision
- CUDA/CPU device selection
- Multiple checkpoint format support

### MVInverseInverse Node
- Multi-view image batch input
- Format conversion: [B,H,W,C] -> [1,B,3,H,W]
- Patch size alignment (14px)
- 5 output maps: albedo, normal, metallic, roughness, shading
- Output normalization (normal: [-1,1]->[0,1], others: [0,255]->[0,1])
- Optional upscaling to original size
- Memory-efficient inference (torch.no_grad, autocast)

## Usage

```
LoadImage (view1) --> ImageBatch --> MVInverseInverse --> SaveImage (albedo)
LoadImage (view2) --|                     |              SaveImage (normal)
LoadImage (view3) --|                     |              SaveImage (metallic)
                                          |              SaveImage (roughness)
MVInverseLoader -------------------------|              SaveImage (shading)
```

## Next Steps

1. Install mvinverse package: `pip install -e <mvinverse-repo>`
2. Test with ComfyUI
3. Verify output quality
