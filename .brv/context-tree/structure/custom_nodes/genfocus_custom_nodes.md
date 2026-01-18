## Relations
@structure/docker/docker_infrastructure_overview.md
@structure/models/ai_models_overview.md
@structure/docker/dockerfile.md
@design/ai_models/model_inventory.md

## Raw Concept
**Task:**
Custom Node Documentation: Genfocus

**Changes:**
- Adds generative refocusing capabilities to ComfyUI
- Implements lazy model loading and caching

**Files:**
- docker/custom_nodes/ComfyUI-Genfocus/__init__.py
- docker/custom_nodes/ComfyUI-Genfocus/nodes/bokeh.py
- docker/custom_nodes/ComfyUI-Genfocus/nodes/deblur.py
- docker/custom_nodes/ComfyUI-Genfocus/

**Flow:**
Load model (Loader) -> Input Image -> Processing Node (Deblur/Bokeh) -> Result Image + Focus Mask

**Timestamp:** 2026-01-17

## Narrative
### Structure
- `docker/custom_nodes/ComfyUI-Genfocus/`
- Nodes: `GenfocusDeblur`, `GenfocusBokeh`, `GenfocusPipeline`, `GenfocusDepthEstimator`

- docker/custom_nodes/ComfyUI-Genfocus/__init__.py
- docker/custom_nodes/ComfyUI-Genfocus/nodes/bokeh.py
- docker/custom_nodes/ComfyUI-Genfocus/nodes/deblur.py
- docker/custom_nodes/ComfyUI-Genfocus/nodes/loaders.py
- docker/custom_nodes/ComfyUI-Genfocus/nodes/pipeline.py

### Dependencies
- Requires `diffusers`, `peft`, `torch`
- Models: `bokehNet.safetensors`, `deblurNet.safetensors`, `depth_pro.pt`

### Features
- DeblurNet: Recover all-in-focus images from blurry input
- BokehNet: Synthesize photorealistic depth-of-field effects
- Depth Estimator: Integrated depth prediction
- Efficient tensor utilities for ComfyUI <-> PyTorch conversion

- DeblurNet: Recovers all-in-focus images from blurry input
- BokehNet: Synthesize photorealistic depth-of-field effects
- Depth Estimator: Automated depth map generation
- ComfyUI Node Integration: Loaders and processing nodes
