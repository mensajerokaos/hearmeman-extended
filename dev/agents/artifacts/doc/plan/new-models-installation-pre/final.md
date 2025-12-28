# New AI Models Implementation Plan - FINAL
## Hearmeman Extended RunPod Template

**Author**: oz
**Model**: claude-opus-4-5
**Date**: 2025-12-28
**Version**: Final (Execution-Ready)
**Clarity Score**: 9/10

---

## Implementation Status Summary

| Model | Download Script | ComfyUI Node | Status |
|-------|-----------------|--------------|--------|
| Qwen-Image-Edit-2511 | ✅ READY | Uses existing QwenEditUtils | **READY** |
| Genfocus | ✅ READY | PLACEHOLDER (loads but no inference) | **PARTIAL** |
| MVInverse | ⚠️ NEEDS VERIFICATION | PLACEHOLDER (loads but no inference) | **BLOCKED** |

### Critical Notes

1. **Qwen-Image-Edit-2511**: Fully functional using existing ComfyUI native nodes + lrzjason/Comfyui-QwenEditUtils
2. **Genfocus**: Models download correctly, but custom node returns dummy output - needs real inference implementation
3. **MVInverse**: HuggingFace repo `Maddog241/mvinverse` cannot be verified - may need Google Drive or GitHub release

---

## Phase 1: Environment Variables & Dockerfile Changes

### 1.1 Environment Variable Definitions

**FILE**: `docker/.env`
**ACTION**: Add these lines at the end of the file

```bash
# Qwen Image Edit 2511 (image editing with text prompts)
# WARNING: BF16 model requires 24GB+ VRAM (7B text encoder + diffusion model)
ENABLE_QWEN_IMAGE_EDIT=false

# Genfocus (generative refocusing - depth-of-field from single images)
# Uses Apple ml-depth-pro for depth estimation
ENABLE_GENFOCUS=false

# MVInverse (multi-view inverse rendering)
# WARNING: Model location unverified - may fail to download
ENABLE_MVINVERSE=false
```

**VERIFICATION**:
```bash
grep -E "ENABLE_(QWEN_IMAGE_EDIT|GENFOCUS|MVINVERSE)" docker/.env
# Expected: 3 lines with =false
```

---

### 1.2 Dockerfile Layer 3 - Custom Nodes

**FILE**: `docker/Dockerfile`
**ACTION**: Add after line 88 (after `RUN pip install --no-cache-dir civitai-downloader`)

```dockerfile
# ============================================
# Qwen Image Edit 2511 Nodes (lrzjason/Comfyui-QwenEditUtils)
# Advanced image editing with configurable multi-image support
# ============================================
RUN git clone --depth 1 https://github.com/lrzjason/Comfyui-QwenEditUtils.git && \
    cd Comfyui-QwenEditUtils && \
    pip install --no-cache-dir -r requirements.txt 2>/dev/null || true

# ============================================
# Custom Nodes for New Models (Genfocus, MVInverse)
# PLACEHOLDER: These nodes LOAD in ComfyUI but return dummy output
# Real inference requires implementing model architectures
# ============================================
COPY custom_nodes/ComfyUI-Genfocus /workspace/ComfyUI/custom_nodes/ComfyUI-Genfocus
COPY custom_nodes/ComfyUI-MVInverse /workspace/ComfyUI/custom_nodes/ComfyUI-MVInverse
```

**VERIFICATION**:
```bash
# After build, verify nodes exist
docker exec -it hearmeman-extended ls -la /workspace/ComfyUI/custom_nodes/ | grep -E "(QwenEdit|Genfocus|MVInverse)"
# Expected: 3 directory entries
```

---

### 1.3 Dockerfile Layer 4 - Additional Dependencies

**FILE**: `docker/Dockerfile`
**ACTION**: Add after line 105 (after the existing `pip install` block in Layer 4)

```dockerfile
# Dependencies for Genfocus (generative refocusing)
# Based on project requirements.txt at https://github.com/rayray9999/Genfocus
# NOTE: ml-depth-pro is Apple's depth estimation model
RUN pip install --no-cache-dir \
    einops \
    timm \
    kornia \
    opencv-python-headless \
    scikit-image \
    git+https://github.com/apple/ml-depth-pro.git || echo "[WARN] ml-depth-pro install failed - Genfocus may not work"

# Dependencies for MVInverse
RUN pip install --no-cache-dir \
    opencv-python-headless || true
```

**VERIFICATION**:
```bash
# After build, verify packages installed
docker exec -it hearmeman-extended pip show einops timm kornia scikit-image
# Expected: Package info for each
```

---

### 1.4 Dockerfile Layer 5 - Model Directories

**FILE**: `docker/Dockerfile`
**ACTION**: Replace line 123 with updated mkdir command

**OLD** (line 123):
```dockerfile
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision}
```

**NEW**:
```dockerfile
# Create model directories (includes genfocus and mvinverse)
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision,genfocus,mvinverse}
```

**VERIFICATION**:
```bash
docker exec -it hearmeman-extended ls -la /workspace/ComfyUI/models/ | grep -E "(genfocus|mvinverse)"
# Expected: 2 directory entries
```

---

### 1.5 docker-compose.yml Updates

**FILE**: `docker/docker-compose.yml`
**ACTION**: Add environment variables after line 53 (after `- COMFYUI_PORT=8188`)

```yaml
      # NEW: Qwen Image Edit 2511
      # WARNING: Requires 24GB+ VRAM for BF16 model
      - ENABLE_QWEN_IMAGE_EDIT=${ENABLE_QWEN_IMAGE_EDIT:-false}

      # NEW: Genfocus (generative refocusing)
      - ENABLE_GENFOCUS=${ENABLE_GENFOCUS:-false}

      # NEW: MVInverse (multi-view inverse rendering)
      # WARNING: Model download may fail - verify HuggingFace repo exists
      - ENABLE_MVINVERSE=${ENABLE_MVINVERSE:-false}
```

**VERIFICATION**:
```bash
docker compose config 2>/dev/null | grep -E "ENABLE_(QWEN|GENFOCUS|MVINVERSE)"
# Expected: 3 lines
```

---

## Phase 2: Download Scripts

### 2.1 Qwen Image Edit 2511 Download Block

**FILE**: `docker/download_models.sh`
**ACTION**: Add after line 263 (after the Fun InP section)

```bash
# ============================================
# Qwen Image Edit 2511 (Image Editing with Text Prompts)
# WARNING: BF16 model requires ~24GB+ VRAM (7B text encoder + diffusion)
# Use FP8mixed for reduced VRAM (~16GB)
# ============================================
if [ "${ENABLE_QWEN_IMAGE_EDIT:-false}" = "true" ]; then
    echo ""
    echo "[Qwen Image Edit] Downloading Qwen-Image-Edit-2511 models..."
    echo "[WARN] BF16 model requires 24GB+ VRAM. For 16GB GPUs, use FP8mixed variant."

    # Diffusion Model (BF16 - highest quality)
    # Source: Comfy-Org/Qwen-Image-Edit_ComfyUI (VERIFIED)
    hf_download "Comfy-Org/Qwen-Image-Edit_ComfyUI" \
        "split_files/diffusion_models/qwen_image_edit_2511_bf16.safetensors" \
        "$MODELS_DIR/diffusion_models/qwen_image_edit_2511_bf16.safetensors"

    # Text Encoder (Qwen 2.5 VL 7B FP8)
    # Source: Comfy-Org/Qwen-Image_ComfyUI (shared with Qwen-Image)
    hf_download "Comfy-Org/Qwen-Image_ComfyUI" \
        "split_files/text_encoders/qwen2.5_vl_7b_fp8_e4m3fn.safetensors" \
        "$MODELS_DIR/text_encoders/qwen2.5_vl_7b_fp8_e4m3fn.safetensors"

    # VAE (shared with Qwen-Image)
    hf_download "Comfy-Org/Qwen-Image_ComfyUI" \
        "split_files/vae/qwen_image_vae.safetensors" \
        "$MODELS_DIR/vae/qwen_image_vae.safetensors"

    # Lightning LoRA for faster inference (optional, 4 steps)
    # Source: lightx2v/Qwen-Image-Edit-2511-Lightning [NEEDS VERIFICATION]
    hf_download "lightx2v/Qwen-Image-Edit-2511-Lightning" \
        "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors" \
        "$MODELS_DIR/loras/Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors" \
        || echo "  [Note] Lightning LoRA not found - using standard inference"

    echo "[Qwen Image Edit] Download complete"
fi
```

**VERIFICATION**:
```bash
# Enable and test downloads
export ENABLE_QWEN_IMAGE_EDIT=true
./download_models.sh 2>&1 | grep -E "\[Qwen|Download\]"
ls -la /workspace/ComfyUI/models/diffusion_models/qwen_image_edit*
ls -la /workspace/ComfyUI/models/text_encoders/qwen2.5_vl*
ls -la /workspace/ComfyUI/models/vae/qwen_image_vae*
```

---

### 2.2 Genfocus Download Block

**FILE**: `docker/download_models.sh`
**ACTION**: Add after the Qwen Image Edit section

```bash
# ============================================
# Genfocus (Generative Refocusing - Depth-of-Field)
# VERIFIED: nycu-cplab/Genfocus-Model exists on HuggingFace
# Models: bokehNet, deblurNet, depth_pro
# ============================================
if [ "${ENABLE_GENFOCUS:-false}" = "true" ]; then
    echo ""
    echo "[Genfocus] Downloading Genfocus models..."

    mkdir -p "$MODELS_DIR/genfocus/checkpoints"

    # BokehNet - Creates controllable bokeh effects (~safetensors)
    # VERIFIED: https://huggingface.co/nycu-cplab/Genfocus-Model
    hf_download "nycu-cplab/Genfocus-Model" \
        "bokehNet.safetensors" \
        "$MODELS_DIR/genfocus/bokehNet.safetensors"

    # DeblurNet - Recovers all-in-focus images
    # VERIFIED: https://huggingface.co/nycu-cplab/Genfocus-Model
    hf_download "nycu-cplab/Genfocus-Model" \
        "deblurNet.safetensors" \
        "$MODELS_DIR/genfocus/deblurNet.safetensors"

    # Depth Pro - Apple's depth estimation model checkpoint
    # VERIFIED: https://huggingface.co/nycu-cplab/Genfocus-Model
    hf_download "nycu-cplab/Genfocus-Model" \
        "checkpoints/depth_pro.pt" \
        "$MODELS_DIR/genfocus/checkpoints/depth_pro.pt"

    echo "[Genfocus] Download complete"
    echo "[NOTE] ComfyUI node is PLACEHOLDER - returns dummy output until inference implemented"
fi
```

**VERIFICATION**:
```bash
# Enable and test downloads
export ENABLE_GENFOCUS=true
./download_models.sh 2>&1 | grep "\[Genfocus\]"
ls -la /workspace/ComfyUI/models/genfocus/
ls -la /workspace/ComfyUI/models/genfocus/checkpoints/
# Expected: bokehNet.safetensors, deblurNet.safetensors, checkpoints/depth_pro.pt
```

---

### 2.3 MVInverse Download Block

**FILE**: `docker/download_models.sh`
**ACTION**: Add after the Genfocus section

```bash
# ============================================
# MVInverse (Multi-View Inverse Rendering)
# WARNING: HuggingFace repo Maddog241/mvinverse COULD NOT BE VERIFIED
# Model location may be GitHub Releases or Google Drive
# ============================================
if [ "${ENABLE_MVINVERSE:-false}" = "true" ]; then
    echo ""
    echo "[MVInverse] Attempting to download MVInverse model..."
    echo "[WARN] HuggingFace repo 'Maddog241/mvinverse' could not be verified"
    echo "[WARN] If download fails, check: https://github.com/Maddog241/mvinverse"

    mkdir -p "$MODELS_DIR/mvinverse"

    # Attempt snapshot download - may fail if repo doesn't exist
    python -c "
from huggingface_hub import snapshot_download
try:
    snapshot_download('Maddog241/mvinverse',
        local_dir='$MODELS_DIR/mvinverse',
        local_dir_use_symlinks=False,
        ignore_patterns=['*.md', '*.txt', 'examples/*'])
    print('[MVInverse] Download complete')
except Exception as e:
    print(f'[MVInverse] Download failed: {e}')
    print('[MVInverse] Check GitHub for manual download instructions')
" 2>&1

    echo "[NOTE] ComfyUI node is PLACEHOLDER - returns dummy output until inference implemented"
fi
```

**VERIFICATION**:
```bash
# Enable and test downloads (may fail if repo doesn't exist)
export ENABLE_MVINVERSE=true
./download_models.sh 2>&1 | grep "\[MVInverse\]"
ls -la /workspace/ComfyUI/models/mvinverse/ 2>/dev/null || echo "MVInverse models not downloaded"
```

---

## Phase 3: ComfyUI Custom Node Wrappers (PLACEHOLDER)

### 3.1 Genfocus Custom Node Directory Structure

**Create directory structure**:
```bash
mkdir -p docker/custom_nodes/ComfyUI-Genfocus
```

---

### 3.1.1 Genfocus __init__.py (PLACEHOLDER)

**FILE**: `docker/custom_nodes/ComfyUI-Genfocus/__init__.py`
**ACTION**: Create new file

```python
"""
ComfyUI-Genfocus: Generative Refocusing Node
Creates depth-of-field effects from single images using Genfocus models.

STATUS: PLACEHOLDER - Nodes LOAD in ComfyUI but return dummy output
REASON: Actual inference requires implementing model architectures from:
  - BokehNet architecture (not publicly documented)
  - DeblurNet architecture (not publicly documented)
  - ml-depth-pro integration (Apple's depth model)

TODO for real implementation:
  1. Get model architecture from Genfocus authors or demo.py
  2. Integrate ml-depth-pro for depth estimation
  3. Implement proper tensor preprocessing (normalization, resizing)
  4. Add CUDA optimization for inference
"""

import os
import torch

# Check if models exist
MODELS_DIR = "/workspace/ComfyUI/models/genfocus"

def check_models_exist():
    """Check if Genfocus models are downloaded."""
    required = [
        os.path.join(MODELS_DIR, "bokehNet.safetensors"),
        os.path.join(MODELS_DIR, "deblurNet.safetensors"),
        os.path.join(MODELS_DIR, "checkpoints", "depth_pro.pt"),
    ]
    return all(os.path.exists(f) for f in required)


class GenfocusDepthEstimation:
    """
    PLACEHOLDER: Estimate depth from a single image.

    Real implementation needs:
    - Load ml-depth-pro model from checkpoints/depth_pro.pt
    - Proper image preprocessing (resize, normalize)
    - GPU inference with depth_pro
    """

    CATEGORY = "Genfocus (PLACEHOLDER)"
    FUNCTION = "estimate_depth"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("depth_map",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
        }

    def estimate_depth(self, image):
        """PLACEHOLDER: Returns grayscale of input as fake depth map."""
        if not check_models_exist():
            print("[Genfocus] WARNING: Models not found. Enable ENABLE_GENFOCUS=true to download.")

        # PLACEHOLDER: Return grayscale as fake depth
        gray = image.mean(dim=-1, keepdim=True)
        depth_map = gray.repeat(1, 1, 1, 3)
        return (depth_map,)


class GenfocusDeblur:
    """
    PLACEHOLDER: Remove blur/defocus from images.

    Real implementation needs:
    - Load DeblurNet weights from deblurNet.safetensors
    - Determine model architecture (U-Net? ResNet?)
    - Proper inference pipeline
    """

    CATEGORY = "Genfocus (PLACEHOLDER)"
    FUNCTION = "deblur"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("sharp_image",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
        }

    def deblur(self, image):
        """PLACEHOLDER: Returns input unchanged."""
        if not check_models_exist():
            print("[Genfocus] WARNING: Models not found. Enable ENABLE_GENFOCUS=true to download.")

        # PLACEHOLDER: Return input unchanged
        return (image,)


class GenfocusBokeh:
    """
    PLACEHOLDER: Apply controllable bokeh/depth-of-field effect.

    Real implementation needs:
    - Load BokehNet weights from bokehNet.safetensors
    - Determine model architecture
    - Implement bokeh parameters (focus distance, aperture)
    """

    CATEGORY = "Genfocus (PLACEHOLDER)"
    FUNCTION = "apply_bokeh"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("bokeh_image",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "depth_map": ("IMAGE",),
                "focus_distance": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider"
                }),
                "aperture": ("FLOAT", {
                    "default": 2.8,
                    "min": 1.0,
                    "max": 22.0,
                    "step": 0.1,
                    "display": "slider"
                }),
                "blur_strength": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 5.0,
                    "step": 0.1,
                    "display": "slider"
                }),
            },
        }

    def apply_bokeh(self, image, depth_map, focus_distance, aperture, blur_strength):
        """PLACEHOLDER: Returns input unchanged."""
        if not check_models_exist():
            print("[Genfocus] WARNING: Models not found. Enable ENABLE_GENFOCUS=true to download.")

        # PLACEHOLDER: Return input unchanged
        return (image,)


class GenfocusRefocus:
    """
    PLACEHOLDER: Full refocusing pipeline: Deblur -> Depth -> Bokeh.

    Real implementation chains the above nodes with actual inference.
    """

    CATEGORY = "Genfocus (PLACEHOLDER)"
    FUNCTION = "refocus"
    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("refocused", "depth_map", "sharp_image")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "focus_distance": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider"
                }),
                "aperture": ("FLOAT", {
                    "default": 2.8,
                    "min": 1.0,
                    "max": 22.0,
                    "step": 0.1,
                }),
                "blur_strength": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 5.0,
                    "step": 0.1,
                }),
            },
        }

    def refocus(self, image, focus_distance, aperture, blur_strength):
        """PLACEHOLDER: Returns input as all outputs."""
        # Chain placeholder nodes
        deblur_node = GenfocusDeblur()
        (sharp_image,) = deblur_node.deblur(image)

        depth_node = GenfocusDepthEstimation()
        (depth_map,) = depth_node.estimate_depth(sharp_image)

        bokeh_node = GenfocusBokeh()
        (refocused,) = bokeh_node.apply_bokeh(
            sharp_image, depth_map, focus_distance, aperture, blur_strength
        )

        return (refocused, depth_map, sharp_image)


# Node registration - ComfyUI will discover these
NODE_CLASS_MAPPINGS = {
    "GenfocusDepthEstimation": GenfocusDepthEstimation,
    "GenfocusDeblur": GenfocusDeblur,
    "GenfocusBokeh": GenfocusBokeh,
    "GenfocusRefocus": GenfocusRefocus,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GenfocusDepthEstimation": "Genfocus Depth (PLACEHOLDER)",
    "GenfocusDeblur": "Genfocus Deblur (PLACEHOLDER)",
    "GenfocusBokeh": "Genfocus Bokeh (PLACEHOLDER)",
    "GenfocusRefocus": "Genfocus Refocus (PLACEHOLDER)",
}

# Print status on load
print("[ComfyUI-Genfocus] Loaded (PLACEHOLDER mode - no real inference)")
if check_models_exist():
    print("[ComfyUI-Genfocus] Models found at:", MODELS_DIR)
else:
    print("[ComfyUI-Genfocus] Models NOT found. Enable ENABLE_GENFOCUS=true")
```

---

### 3.1.2 Genfocus requirements.txt

**FILE**: `docker/custom_nodes/ComfyUI-Genfocus/requirements.txt`
**ACTION**: Create new file

```
# Genfocus dependencies (from https://github.com/rayray9999/Genfocus)
einops
timm
kornia
safetensors
scikit-image
opencv-python-headless
# ml-depth-pro installed separately in Dockerfile Layer 4
```

---

### 3.2 MVInverse Custom Node Directory Structure

**Create directory structure**:
```bash
mkdir -p docker/custom_nodes/ComfyUI-MVInverse
```

---

### 3.2.1 MVInverse __init__.py (PLACEHOLDER)

**FILE**: `docker/custom_nodes/ComfyUI-MVInverse/__init__.py`
**ACTION**: Create new file

```python
"""
ComfyUI-MVInverse: Multi-View Inverse Rendering Node
Predicts albedo, metallic, roughness, normals, and shading from multi-view images.

STATUS: PLACEHOLDER - Nodes LOAD in ComfyUI but return dummy output
REASON:
  1. HuggingFace repo 'Maddog241/mvinverse' could not be verified
  2. Model architecture requires DINOv2 + ResNeXt + DPT heads
  3. Checkpoint format and loading not documented

TODO for real implementation:
  1. Confirm model location (HuggingFace/Google Drive/GitHub Releases)
  2. Get exact checkpoint filenames
  3. Implement model loading with proper architecture
  4. Add multi-view attention mechanism
"""

import os
import torch

MODELS_DIR = "/workspace/ComfyUI/models/mvinverse"

def check_models_exist():
    """Check if MVInverse models are downloaded."""
    return os.path.exists(MODELS_DIR) and len(os.listdir(MODELS_DIR)) > 0


class MVInverseLoader:
    """
    PLACEHOLDER: Load MVInverse model.

    Real implementation needs:
    - Find actual checkpoint files
    - Load DINOv2 encoder
    - Load ResNeXt feature extractor
    - Load DPT prediction heads
    """

    CATEGORY = "MVInverse (PLACEHOLDER)"
    FUNCTION = "load_model"
    RETURN_TYPES = ("MVINVERSE_MODEL",)
    RETURN_NAMES = ("model",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
        }

    def load_model(self):
        """PLACEHOLDER: Returns dummy model dict."""
        if not check_models_exist():
            print("[MVInverse] WARNING: Models not found at", MODELS_DIR)
            print("[MVInverse] Enable ENABLE_MVINVERSE=true to attempt download")
            print("[MVInverse] NOTE: HuggingFace repo may not exist")

        # PLACEHOLDER: Return dummy model
        return ({"loaded": True, "placeholder": True},)


class MVInverseInference:
    """
    PLACEHOLDER: Run MVInverse inference on multi-view images.

    Real implementation needs:
    - DINOv2 patch token extraction
    - Cross-view attention aggregation
    - ResNeXt multi-resolution features
    - DPT-style prediction heads for each output
    """

    CATEGORY = "MVInverse (PLACEHOLDER)"
    FUNCTION = "infer"
    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("albedo", "metallic", "roughness", "normal", "shading")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MVINVERSE_MODEL",),
                "images": ("IMAGE",),
            },
            "optional": {
                "output_resolution": (["original", "512", "1024"], {
                    "default": "original"
                }),
            },
        }

    def infer(self, model, images, output_resolution="original"):
        """PLACEHOLDER: Returns dummy material maps."""
        batch_size, height, width, channels = images.shape

        # PLACEHOLDER: Generate fake outputs
        albedo = images.clone()  # Fake albedo = input
        metallic = torch.ones_like(images) * 0.0  # Non-metallic
        roughness = torch.ones_like(images) * 0.5  # Medium roughness
        normal = torch.zeros_like(images)
        normal[..., 2] = 1.0  # Default normal pointing +Z (blue)
        normal = normal * 0.5 + 0.5  # Remap to 0-1 for display
        shading = images.mean(dim=-1, keepdim=True).repeat(1, 1, 1, 3)  # Fake shading

        return (albedo, metallic, roughness, normal, shading)


class MVInverseSingleView:
    """PLACEHOLDER: Simplified single-view inverse rendering."""

    CATEGORY = "MVInverse (PLACEHOLDER)"
    FUNCTION = "infer_single"
    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("albedo", "metallic", "roughness", "normal", "shading")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
        }

    def infer_single(self, image):
        """PLACEHOLDER: Single-view wrapper."""
        loader = MVInverseLoader()
        (model,) = loader.load_model()
        inference = MVInverseInference()
        return inference.infer(model, image)


class MVInverseRelight:
    """Simple PBR-style relighting using material predictions."""

    CATEGORY = "MVInverse (PLACEHOLDER)"
    FUNCTION = "relight"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("relit_image",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "albedo": ("IMAGE",),
                "normal": ("IMAGE",),
                "metallic": ("IMAGE",),
                "roughness": ("IMAGE",),
                "light_direction": ("FLOAT", {
                    "default": 0.0,
                    "min": -180.0,
                    "max": 180.0,
                    "step": 1.0,
                    "display": "slider"
                }),
                "light_elevation": ("FLOAT", {
                    "default": 45.0,
                    "min": -90.0,
                    "max": 90.0,
                    "step": 1.0,
                    "display": "slider"
                }),
                "light_intensity": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 5.0,
                    "step": 0.1,
                }),
                "ambient_intensity": ("FLOAT", {
                    "default": 0.2,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                }),
            },
        }

    def relight(self, albedo, normal, metallic, roughness,
                light_direction, light_elevation, light_intensity, ambient_intensity):
        """Simple Lambertian relighting (works even with placeholder data)."""
        import math

        # Convert angles to light direction vector
        theta = math.radians(light_direction)
        phi = math.radians(light_elevation)
        light_dir = torch.tensor([
            math.cos(phi) * math.sin(theta),
            math.cos(phi) * math.cos(theta),
            math.sin(phi)
        ], dtype=albedo.dtype, device=albedo.device)

        # Decode normals from 0-1 to -1 to 1
        normals_decoded = normal * 2.0 - 1.0

        # Compute diffuse shading (Lambert)
        n_dot_l = torch.clamp(
            torch.sum(normals_decoded * light_dir, dim=-1, keepdim=True),
            min=0.0
        )

        # Simple Lambertian + ambient
        diffuse = albedo * (n_dot_l * light_intensity + ambient_intensity)
        relit_image = torch.clamp(diffuse, 0.0, 1.0)

        return (relit_image,)


# Node registration
NODE_CLASS_MAPPINGS = {
    "MVInverseLoader": MVInverseLoader,
    "MVInverseInference": MVInverseInference,
    "MVInverseSingleView": MVInverseSingleView,
    "MVInverseRelight": MVInverseRelight,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MVInverseLoader": "MVInverse Load (PLACEHOLDER)",
    "MVInverseInference": "MVInverse Inference (PLACEHOLDER)",
    "MVInverseSingleView": "MVInverse Single View (PLACEHOLDER)",
    "MVInverseRelight": "MVInverse Relight",
}

# Print status on load
print("[ComfyUI-MVInverse] Loaded (PLACEHOLDER mode - no real inference)")
if check_models_exist():
    print("[ComfyUI-MVInverse] Models found at:", MODELS_DIR)
else:
    print("[ComfyUI-MVInverse] Models NOT found. Enable ENABLE_MVINVERSE=true")
    print("[ComfyUI-MVInverse] NOTE: HuggingFace repo may not exist")
```

---

### 3.2.2 MVInverse requirements.txt

**FILE**: `docker/custom_nodes/ComfyUI-MVInverse/requirements.txt`
**ACTION**: Create new file

```
# MVInverse dependencies
opencv-python-headless
safetensors
```

---

## Phase 4: Testing & Verification

### 4.1 Pre-Build Verification

```bash
cd /home/oz/projects/2025/oz/12/runpod/docker

# Verify custom nodes exist
ls -la custom_nodes/ComfyUI-Genfocus/__init__.py
ls -la custom_nodes/ComfyUI-MVInverse/__init__.py

# Verify files have content
wc -l custom_nodes/ComfyUI-Genfocus/__init__.py   # Expected: ~180 lines
wc -l custom_nodes/ComfyUI-MVInverse/__init__.py  # Expected: ~200 lines
```

### 4.2 Docker Build

```bash
cd /home/oz/projects/2025/oz/12/runpod/docker

# Full rebuild
docker compose build --no-cache

# Check for build errors
docker compose build 2>&1 | grep -i error
```

### 4.3 Start with New Models Enabled

```bash
# Start with Qwen + Genfocus (MVInverse may fail)
ENABLE_QWEN_IMAGE_EDIT=true ENABLE_GENFOCUS=true ENABLE_MVINVERSE=false \
    docker compose up -d

# Wait for startup and model downloads
sleep 60

# Check logs for errors
docker logs hearmeman-extended 2>&1 | tail -100
```

### 4.4 Verify Custom Nodes Loaded

```bash
# Check nodes in filesystem
docker exec -it hearmeman-extended ls -la /workspace/ComfyUI/custom_nodes/ | \
    grep -E "(QwenEdit|Genfocus|MVInverse)"

# Check ComfyUI API for available nodes
curl -s http://localhost:8188/object_info | python3 -c "
import sys, json
data = json.load(sys.stdin)
for key in sorted(data.keys()):
    if any(x in key.lower() for x in ['qwen', 'genfocus', 'mvinverse']):
        print(key)
"
# Expected output should include:
# - TextEncodeQwenImageEditPlusAdvance (from QwenEditUtils)
# - GenfocusDepthEstimation
# - GenfocusDeblur
# - GenfocusBokeh
# - GenfocusRefocus
# - MVInverseLoader
# - MVInverseInference
# - MVInverseSingleView
# - MVInverseRelight
```

### 4.5 Verify Model Downloads

```bash
# Qwen models
docker exec -it hearmeman-extended ls -lah /workspace/ComfyUI/models/diffusion_models/ | grep qwen
docker exec -it hearmeman-extended ls -lah /workspace/ComfyUI/models/text_encoders/ | grep qwen
docker exec -it hearmeman-extended ls -lah /workspace/ComfyUI/models/vae/ | grep qwen

# Genfocus models
docker exec -it hearmeman-extended ls -lah /workspace/ComfyUI/models/genfocus/
docker exec -it hearmeman-extended ls -lah /workspace/ComfyUI/models/genfocus/checkpoints/

# MVInverse (may be empty if download failed)
docker exec -it hearmeman-extended ls -lah /workspace/ComfyUI/models/mvinverse/ 2>/dev/null || echo "MVInverse not downloaded"
```

---

## Phase 5: Documentation Updates

### 5.1 CLAUDE.md Storage Requirements Update

**FILE**: `/home/oz/projects/2025/oz/12/runpod/CLAUDE.md`
**ACTION**: Add to storage requirements table

```markdown
| **Qwen Image Edit 2511** | ~18GB | Image editing (BF16), 24GB+ VRAM required |
| **Genfocus** | ~3GB | Depth-of-field (bokeh/deblur/depth), PLACEHOLDER nodes |
| **MVInverse** | ~2GB | Multi-view inverse rendering, UNVERIFIED download |
```

### 5.2 Environment Variables Documentation

**FILE**: `/home/oz/projects/2025/oz/12/runpod/CLAUDE.md`
**ACTION**: Add to environment variables section

```markdown
| Variable | Default | Size | Notes |
|----------|---------|------|-------|
| `ENABLE_QWEN_IMAGE_EDIT` | false | ~18GB | ⚠️ Requires 24GB+ VRAM (BF16) |
| `ENABLE_GENFOCUS` | false | ~3GB | PLACEHOLDER nodes (no inference) |
| `ENABLE_MVINVERSE` | false | ~2GB | ⚠️ Download may fail (unverified HF repo) |
```

---

## Implementation Execution Order

Execute these phases sequentially:

| # | Phase | Files Modified | Est. Time |
|---|-------|---------------|-----------|
| 1 | 1.1-1.5 | `.env`, `Dockerfile`, `docker-compose.yml` | 10 min |
| 2 | 2.1-2.3 | `download_models.sh` | 10 min |
| 3 | 3.1 | `custom_nodes/ComfyUI-Genfocus/*` | 5 min |
| 4 | 3.2 | `custom_nodes/ComfyUI-MVInverse/*` | 5 min |
| 5 | 4.1-4.5 | (verification only) | 15 min |
| 6 | 5.1-5.2 | `CLAUDE.md` | 5 min |

**Total**: ~50 minutes

---

## Risk Assessment

### Known Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Qwen BF16 requires 24GB+ VRAM | HIGH | Document clearly, add FP8mixed alternative later |
| MVInverse HF repo may not exist | HIGH | Skip download gracefully, placeholder node still loads |
| Genfocus inference not implemented | MEDIUM | Placeholder returns dummy output, clearly labeled |
| ml-depth-pro may fail to install | MEDIUM | Wrapped in `|| true`, node still loads |
| diffusers version conflicts | LOW | Already tested in existing template |

### Success Criteria

- [ ] Docker builds without errors
- [ ] All 3 new environment variables recognized
- [ ] Qwen models download successfully (when enabled)
- [ ] Genfocus models download successfully (when enabled)
- [ ] All custom nodes appear in ComfyUI node browser
- [ ] Placeholder nodes return output (even if dummy)
- [ ] VRAM warnings visible in logs

---

## References

### Verified Repositories (Use These)
- [Comfy-Org/Qwen-Image-Edit_ComfyUI](https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI) ✅
- [Comfy-Org/Qwen-Image_ComfyUI](https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI) ✅
- [nycu-cplab/Genfocus-Model](https://huggingface.co/nycu-cplab/Genfocus-Model) ✅
- [lrzjason/Comfyui-QwenEditUtils](https://github.com/lrzjason/Comfyui-QwenEditUtils) ✅

### Unverified (May Need Alternative)
- [Maddog241/mvinverse](https://huggingface.co/Maddog241/mvinverse) ❓
- [lightx2v/Qwen-Image-Edit-2511-Lightning](https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning) ❓

### Documentation
- [ComfyUI Qwen Image Edit Tutorial](https://docs.comfy.org/tutorials/image/qwen/qwen-image-edit-2511)
- [Genfocus GitHub](https://github.com/rayray9999/Genfocus)
- [MVInverse GitHub](https://github.com/Maddog241/mvinverse)
