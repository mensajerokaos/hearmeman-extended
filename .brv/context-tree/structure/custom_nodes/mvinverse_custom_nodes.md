## Relations
@structure/docker/docker_infrastructure_overview.md
@structure/models/ai_models_overview.md
@structure/docker/dockerfile.md
@design/ai_models/model_inventory.md

## Raw Concept
**Task:**
Custom Node Documentation: MVInverse

**Changes:**
- Adds material extraction capabilities from multi-view images
- Adds PBR material extraction to ComfyUI workflow
- Implements multi-view image processing pipeline

**Files:**
- docker/custom_nodes/ComfyUI-MVInverse/__init__.py
- docker/custom_nodes/ComfyUI-MVInverse/mvinverse_inverse.py
- docker/custom_nodes/ComfyUI-MVInverse/mvinverse_loader.py
- docker/custom_nodes/ComfyUI-MVInverse/

**Flow:**
Loader (local/HF) -> Multi-view Image Batch -> Inverse Render Node -> PBR Maps (Albedo/Normal/etc)

**Timestamp:** 2026-01-17

## Narrative
### Structure
- `docker/custom_nodes/ComfyUI-MVInverse/`
- Nodes: `MVInverseLoader`, `MVInverseInverse`

- docker/custom_nodes/ComfyUI-MVInverse/__init__.py
- docker/custom_nodes/ComfyUI-MVInverse/mvinverse_loader.py
- docker/custom_nodes/ComfyUI-MVInverse/mvinverse_inverse.py

### Dependencies
- Requires `mvinverse` package (git clone)
- Model: `maddog241/mvinverse` (HF Hub) or local `.pt` files

### Features
- Multi-view inverse rendering
- Extracts material properties: albedo, normal, metallic, roughness, shading
- Critical patch size alignment (14) for processing
- Memory-efficient inference with FP16 support

- Multi-view inverse rendering for material extraction
- Extracts: Albedo, Normal, Metallic, Roughness, Shading
- Patch size alignment (14px) for model compatibility
- Automatic checkpoint downloading from HuggingFace Hub
