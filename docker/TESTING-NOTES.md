# Testing Notes - 2025-12-29

## Session Summary
Tested all available workflows after rebuilding the Docker image with new custom nodes.

## Test Results

### Realism Illustrious txt2img
- **Status**: PASSED
- **Resolution**: 768x768 (reduced from 1024x1024 due to VRAM constraints)
- **Steps**: 20
- **Time**: ~21s
- **Note**: 1024x1024 caused container restart (likely OOM on 16GB VRAM)

### Genfocus DeblurNet
- **Status**: PASSED
- **Time**: ~5s
- **Note**: Uses fallback mode (heuristic-based deblur, not full model)

### Genfocus BokehNet
- **Status**: PASSED (after fix)
- **Bug Found**: Tensor size mismatch in `bokeh.py` line 243
- **Cause**: Depth estimation with avg_pool2d can produce mismatched dimensions
- **Fix**: Added interpolation to resize blur_amount to match image dimensions
- **File**: `custom_nodes/ComfyUI-Genfocus/nodes/bokeh.py`

### MVInverse Material Extraction
- **Status**: PASSED (after fix)
- **Bug Found**: Loader tried to download non-existent `mvinverse.pt` from HuggingFace
- **Cause**: MVInverse uses PyTorchModelHubMixin.from_pretrained(), not direct .pt download
- **Fix**: Updated loader to use `from_pretrained()` method
- **File**: `custom_nodes/ComfyUI-MVInverse/mvinverse_loader.py`
- **Note**: First run downloads model from HuggingFace (~2 minutes)

### Skipped Tests
- **VibeVoice**: User confirmed working
- **WAN 2.2**: Model not downloaded
- **Z-Image Turbo**: VRAM constraints (needs 24GB+)

## Issues Found and Fixed This Session

### 1. BokehNet Tensor Size Mismatch
```
RuntimeError: The expanded size of the tensor (768) must match the existing size (769)
at non-singleton dimension 3. Target sizes: [1, 3, 768, 768]. Tensor sizes: [1, 1, 769, 769]
```

**Root Cause**: The depth estimation uses `avg_pool2d` with padding that can produce outputs 1px larger than expected:
```python
depth = torch.nn.functional.avg_pool2d(gradient_mag, 16, stride=1, padding=8)
```

**Fix**: Add resize after blur_amount calculation:
```python
if blur_amount.shape[-2:] != (H, W):
    blur_amount = torch.nn.functional.interpolate(
        blur_amount, size=(H, W), mode='bilinear', align_corners=False
    )
```

### 2. MVInverse HuggingFace Model Loading
```
huggingface_hub.errors.EntryNotFoundError: 404 Client Error
Entry Not Found for url: https://huggingface.co/maddog241/mvinverse/resolve/main/mvinverse.pt
```

**Root Cause**: The original loader tried to download `mvinverse.pt` directly, but the model uses `PyTorchModelHubMixin` which stores weights differently.

**Fix**: Use `MVInverse.from_pretrained("maddog241/mvinverse")` instead of manual download.

### 3. Missing mvinverse Package
```
ImportError: [MVInverse] Failed to import mvinverse package
```

**Fix**: Clone the mvinverse repo into custom_nodes:
```bash
cd /workspace/ComfyUI/custom_nodes
git clone --depth 1 https://github.com/maddog241/mvinverse.git
```

## Dependencies Added to Container
- mvinverse repo cloned to `/workspace/ComfyUI/custom_nodes/mvinverse/`
- Model downloaded to HuggingFace cache on first use

## Output Files Generated
- `output/test-illustrious_00001_.png` - Realism Illustrious output
- `output/test-genfocus-deblur_00001_.png` - DeblurNet output
- `output/test-bokeh-result_00001_.png` - BokehNet output
- `output/mvinverse-albedo_00001_.png` - Albedo map
- `output/mvinverse-normal_00001_.png` - Normal map
- `output/mvinverse-metallic_00001_.png` - Metallic map
- `output/mvinverse-roughness_00001_.png` - Roughness map
- `output/mvinverse-shading_00001_.png` - Shading map

## Future Agent Notes

### ComfyUI API Testing Pattern
```python
import requests
import json
import time

# Submit workflow
response = requests.post('http://localhost:8188/prompt', json={'prompt': workflow})
prompt_id = response.json()['prompt_id']

# Poll for completion
while True:
    response = requests.get(f'http://localhost:8188/history/{prompt_id}')
    data = response.json()
    if prompt_id in data:
        status = data[prompt_id]['status']['status_str']
        if status in ['success', 'error']:
            break
    time.sleep(5)
```

### Shell Quirks
- `jq` parse errors with complex nested JSON in zsh - use Python instead
- Docker cp with mounted volumes can fail with permission errors
- Mounted volumes already sync files - no need to copy

### VRAM Management
- 16GB VRAM limits: Use 768x768 resolution for image generation
- Models load sequentially - don't run multiple workflows in parallel
- Container may restart on OOM - reduce resolution/steps if this happens
