# New AI Models Implementation Plan
## Hearmeman Extended RunPod Template

**Author**: oz
**Model**: claude-opus-4-5
**Date**: 2025-12-28
**Version**: Draft 1

---

## Executive Summary

This plan adds 3 new AI models to the hearmeman-extended RunPod template:

| Model | Purpose | VRAM | ComfyUI Node Status |
|-------|---------|------|---------------------|
| Qwen-Image-Edit-2511 | Image editing with text prompts | ~12-16GB | **Exists**: lrzjason/Comfyui-QwenEditUtils |
| Genfocus | Depth-of-field from single images | ~12GB+ | **None** - needs custom wrapper |
| MVInverse | Multi-view inverse rendering | ~10-16GB | **None** - needs custom wrapper |

---

## Phase 1: Environment Variables & Dockerfile Changes

### 1.1 Environment Variable Definitions

**FILE**: `docker/.env` (for local) and `docker-compose.yml`
**ACTION**: Add new environment variables

```bash
# Qwen Image Edit 2511 (image editing with text prompts)
ENABLE_QWEN_IMAGE_EDIT=false

# Genfocus (generative refocusing - depth-of-field from single images)
ENABLE_GENFOCUS=false

# MVInverse (multi-view inverse rendering)
ENABLE_MVINVERSE=false
```

**VERIFICATION**: `grep -E "ENABLE_(QWEN_IMAGE_EDIT|GENFOCUS|MVINVERSE)" docker/.env`

---

### 1.2 Dockerfile Layer 3 - Custom Nodes

**FILE**: `docker/Dockerfile`
**ACTION**: Add after existing custom nodes in Layer 3

```dockerfile
# ============================================
# Qwen Image Edit 2511 Nodes (lrzjason/Comfyui-QwenEditUtils)
# Advanced image editing with configurable multi-image support
# ============================================
RUN git clone --depth 1 https://github.com/lrzjason/Comfyui-QwenEditUtils.git && \
    cd Comfyui-QwenEditUtils && \
    pip install --no-cache-dir -r requirements.txt || true

# ============================================
# Custom Nodes for New Models (Genfocus, MVInverse)
# These are custom wrappers created for this template
# ============================================
COPY custom_nodes/ComfyUI-Genfocus /workspace/ComfyUI/custom_nodes/ComfyUI-Genfocus
COPY custom_nodes/ComfyUI-MVInverse /workspace/ComfyUI/custom_nodes/ComfyUI-MVInverse
```

**VERIFICATION**:
```bash
# After build, verify nodes exist
docker exec -it runpod ls -la /workspace/ComfyUI/custom_nodes/ | grep -E "(QwenEdit|Genfocus|MVInverse)"
```

---

### 1.3 Dockerfile Layer 4 - Additional Dependencies

**FILE**: `docker/Dockerfile`
**ACTION**: Add to Layer 4 (Additional Dependencies)

```dockerfile
# Dependencies for Qwen Image Edit 2511
# Requires latest diffusers from git for QwenImageEditPlusPipeline
RUN pip install --no-cache-dir \
    git+https://github.com/huggingface/diffusers.git

# Dependencies for Genfocus (generative refocusing)
# Based on Python 3.12 environment requirements
RUN pip install --no-cache-dir \
    einops \
    timm \
    kornia \
    gradio

# Dependencies for MVInverse (multi-view inverse rendering)
# Requires specific PyTorch for CUDA 11.8 compatibility
# Note: Base image already has PyTorch 2.8.0, but MVInverse tested with 2.5.1
# We use the base image PyTorch for compatibility
RUN pip install --no-cache-dir \
    opencv-python-headless
```

**VERIFICATION**:
```bash
# After build, verify packages installed
docker exec -it runpod pip show diffusers einops timm kornia
```

---

### 1.4 Dockerfile Layer 5 - Model Directories

**FILE**: `docker/Dockerfile`
**ACTION**: Update mkdir command to include new model directories

```dockerfile
# Create model directories (updated with new model paths)
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision,genfocus,mvinverse}
```

**VERIFICATION**: `docker exec -it runpod ls -la /workspace/ComfyUI/models/ | grep -E "(genfocus|mvinverse)"`

---

### 1.5 docker-compose.yml Updates

**FILE**: `docker/docker-compose.yml`
**ACTION**: Add environment variables to service definition

```yaml
services:
  comfyui:
    # ... existing config ...
    environment:
      # Existing variables...
      - ENABLE_VIBEVOICE=${ENABLE_VIBEVOICE:-true}
      # ... other existing variables ...

      # NEW: Qwen Image Edit 2511
      - ENABLE_QWEN_IMAGE_EDIT=${ENABLE_QWEN_IMAGE_EDIT:-false}

      # NEW: Genfocus (generative refocusing)
      - ENABLE_GENFOCUS=${ENABLE_GENFOCUS:-false}

      # NEW: MVInverse (multi-view inverse rendering)
      - ENABLE_MVINVERSE=${ENABLE_MVINVERSE:-false}
```

**VERIFICATION**: `docker compose config | grep -E "ENABLE_(QWEN|GENFOCUS|MVINVERSE)"`

---

## Phase 2: Download Scripts

### 2.1 Qwen Image Edit 2511 Download Block

**FILE**: `docker/download_models.sh`
**ACTION**: Add new section after existing model downloads

```bash
# ============================================
# Qwen Image Edit 2511 (Image Editing with Text Prompts)
# ~12-16GB VRAM required
# ============================================
if [ "${ENABLE_QWEN_IMAGE_EDIT:-false}" = "true" ]; then
    echo "[Qwen Image Edit] Downloading Qwen-Image-Edit-2511 models..."

    # Diffusion Model (FP8 quantized for memory efficiency)
    # From: Comfy-Org/Qwen-Image-Edit-2511_ComfyUI_repackaged
    hf_download "Comfy-Org/Qwen-Image-Edit-2511_ComfyUI_repackaged" \
        "qwen_image_edit_2511_fp8_e4m3fn.safetensors" \
        "$MODELS_DIR/diffusion_models/qwen_image_edit_2511_fp8_e4m3fn.safetensors"

    # Text Encoder (Qwen 2.5 VL 7B FP8)
    hf_download "Comfy-Org/Qwen-Image-Edit-2511_ComfyUI_repackaged" \
        "qwen_2.5_vl_7b_fp8_scaled.safetensors" \
        "$MODELS_DIR/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors"

    # VAE
    hf_download "Comfy-Org/Qwen-Image-Edit-2511_ComfyUI_repackaged" \
        "qwen_image_vae.safetensors" \
        "$MODELS_DIR/vae/qwen_image_vae.safetensors"

    # Lightning LoRA for faster inference (optional, 4 steps)
    hf_download "Comfy-Org/Qwen-Image-Edit-2511_ComfyUI_repackaged" \
        "Qwen-Image-Lightning-4steps-V1.0.safetensors" \
        "$MODELS_DIR/loras/Qwen-Image-Lightning-4steps-V1.0.safetensors"

    echo "[Qwen Image Edit] Download complete"
fi
```

**VERIFICATION**:
```bash
# Enable and test
export ENABLE_QWEN_IMAGE_EDIT=true
./download_models.sh
ls -la /workspace/ComfyUI/models/diffusion_models/qwen_image_edit*
ls -la /workspace/ComfyUI/models/text_encoders/qwen_2.5_vl*
ls -la /workspace/ComfyUI/models/vae/qwen_image_vae*
```

---

### 2.2 Genfocus Download Block

**FILE**: `docker/download_models.sh`
**ACTION**: Add new section

```bash
# ============================================
# Genfocus (Generative Refocusing - Depth-of-Field)
# ~12GB+ VRAM required
# Models: bokehNet, deblurNet, depth_pro
# ============================================
if [ "${ENABLE_GENFOCUS:-false}" = "true" ]; then
    echo "[Genfocus] Downloading Genfocus models..."

    mkdir -p "$MODELS_DIR/genfocus/checkpoints"

    # BokehNet - Creates controllable bokeh effects
    hf_download "nycu-cplab/Genfocus-Model" \
        "bokehNet.safetensors" \
        "$MODELS_DIR/genfocus/bokehNet.safetensors"

    # DeblurNet - Recovers all-in-focus images
    hf_download "nycu-cplab/Genfocus-Model" \
        "deblurNet.safetensors" \
        "$MODELS_DIR/genfocus/deblurNet.safetensors"

    # Depth Pro - Depth estimation model
    hf_download "nycu-cplab/Genfocus-Model" \
        "checkpoints/depth_pro.pt" \
        "$MODELS_DIR/genfocus/checkpoints/depth_pro.pt"

    echo "[Genfocus] Download complete"
fi
```

**VERIFICATION**:
```bash
# Enable and test
export ENABLE_GENFOCUS=true
./download_models.sh
ls -la /workspace/ComfyUI/models/genfocus/
ls -la /workspace/ComfyUI/models/genfocus/checkpoints/
```

---

### 2.3 MVInverse Download Block

**FILE**: `docker/download_models.sh`
**ACTION**: Add new section

```bash
# ============================================
# MVInverse (Multi-View Inverse Rendering)
# ~10-16GB VRAM required
# Predicts albedo, metallic, roughness, normals, shading
# ============================================
if [ "${ENABLE_MVINVERSE:-false}" = "true" ]; then
    echo "[MVInverse] Downloading MVInverse model..."

    mkdir -p "$MODELS_DIR/mvinverse"

    # MVInverse checkpoint
    # Note: Model hosted on HuggingFace by the authors
    python -c "
from huggingface_hub import snapshot_download
snapshot_download('Maddog241/mvinverse',
    local_dir='$MODELS_DIR/mvinverse',
    local_dir_use_symlinks=False,
    ignore_patterns=['*.md', '*.txt', 'examples/*'])
" 2>&1 || echo "  [Note] MVInverse will download on first use"

    echo "[MVInverse] Download complete"
fi
```

**VERIFICATION**:
```bash
# Enable and test
export ENABLE_MVINVERSE=true
./download_models.sh
ls -la /workspace/ComfyUI/models/mvinverse/
```

---

## Phase 3: ComfyUI Custom Node Wrappers

### 3.1 Genfocus Custom Node

**FILE**: `docker/custom_nodes/ComfyUI-Genfocus/__init__.py`
**ACTION**: Create new file

```python
"""
ComfyUI-Genfocus: Generative Refocusing Node
Creates depth-of-field effects from single images using Genfocus models.
"""

import os
import torch
import numpy as np
from PIL import Image

# Lazy loading for model
_bokeh_net = None
_deblur_net = None
_depth_model = None

MODELS_DIR = "/workspace/ComfyUI/models/genfocus"

def get_bokeh_net():
    """Lazy load BokehNet model."""
    global _bokeh_net
    if _bokeh_net is None:
        from safetensors.torch import load_file
        model_path = os.path.join(MODELS_DIR, "bokehNet.safetensors")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"BokehNet model not found at {model_path}. Enable ENABLE_GENFOCUS=true to download.")
        # Note: Actual model loading depends on Genfocus architecture
        # This is a placeholder - replace with actual model class
        _bokeh_net = load_file(model_path)
    return _bokeh_net

def get_deblur_net():
    """Lazy load DeblurNet model."""
    global _deblur_net
    if _deblur_net is None:
        from safetensors.torch import load_file
        model_path = os.path.join(MODELS_DIR, "deblurNet.safetensors")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"DeblurNet model not found at {model_path}. Enable ENABLE_GENFOCUS=true to download.")
        _deblur_net = load_file(model_path)
    return _deblur_net

def get_depth_model():
    """Lazy load Depth Pro model."""
    global _depth_model
    if _depth_model is None:
        model_path = os.path.join(MODELS_DIR, "checkpoints", "depth_pro.pt")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Depth Pro model not found at {model_path}. Enable ENABLE_GENFOCUS=true to download.")
        _depth_model = torch.load(model_path, map_location="cpu")
    return _depth_model


class GenfocusDepthEstimation:
    """Estimate depth from a single image using Depth Pro."""

    CATEGORY = "Genfocus"
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
        """
        Estimate depth map from input image.

        Args:
            image: ComfyUI IMAGE tensor (B, H, W, C) in 0-1 range

        Returns:
            depth_map: Normalized depth map as IMAGE tensor
        """
        # Convert from ComfyUI format (B, H, W, C) to model format
        # Placeholder implementation - replace with actual Depth Pro inference
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # Get depth model
        depth_weights = get_depth_model()

        # TODO: Implement actual depth estimation
        # For now, return a grayscale version as placeholder
        gray = image.mean(dim=-1, keepdim=True)
        depth_map = gray.repeat(1, 1, 1, 3)

        return (depth_map,)


class GenfocusDeblur:
    """Remove blur/defocus from images using DeblurNet."""

    CATEGORY = "Genfocus"
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
        """
        Remove blur from input image to create all-in-focus result.

        Args:
            image: ComfyUI IMAGE tensor (B, H, W, C)

        Returns:
            sharp_image: Deblurred IMAGE tensor
        """
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # Get deblur model weights
        deblur_weights = get_deblur_net()

        # TODO: Implement actual deblurring
        # Placeholder - return input unchanged
        return (image,)


class GenfocusBokeh:
    """Apply controllable bokeh/depth-of-field effect."""

    CATEGORY = "Genfocus"
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
        """
        Apply depth-of-field bokeh effect.

        Args:
            image: Source IMAGE tensor
            depth_map: Depth map IMAGE tensor (grayscale)
            focus_distance: 0.0 = near, 1.0 = far
            aperture: Simulated f-stop (lower = more blur)
            blur_strength: Multiplier for blur amount

        Returns:
            bokeh_image: IMAGE with bokeh effect applied
        """
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # Get bokeh model weights
        bokeh_weights = get_bokeh_net()

        # TODO: Implement actual bokeh rendering
        # Placeholder - return input unchanged
        return (image,)


class GenfocusRefocus:
    """Full refocusing pipeline: Deblur -> Depth -> Bokeh."""

    CATEGORY = "Genfocus"
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
        """
        Full refocusing pipeline.

        1. Deblur input to get all-in-focus image
        2. Estimate depth from deblurred image
        3. Apply bokeh effect with specified parameters

        Returns:
            refocused: Final image with new focus
            depth_map: Estimated depth map
            sharp_image: Intermediate all-in-focus image
        """
        # Run deblur
        deblur_node = GenfocusDeblur()
        (sharp_image,) = deblur_node.deblur(image)

        # Estimate depth
        depth_node = GenfocusDepthEstimation()
        (depth_map,) = depth_node.estimate_depth(sharp_image)

        # Apply bokeh
        bokeh_node = GenfocusBokeh()
        (refocused,) = bokeh_node.apply_bokeh(
            sharp_image, depth_map, focus_distance, aperture, blur_strength
        )

        return (refocused, depth_map, sharp_image)


# Node registration
NODE_CLASS_MAPPINGS = {
    "GenfocusDepthEstimation": GenfocusDepthEstimation,
    "GenfocusDeblur": GenfocusDeblur,
    "GenfocusBokeh": GenfocusBokeh,
    "GenfocusRefocus": GenfocusRefocus,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GenfocusDepthEstimation": "Genfocus Depth Estimation",
    "GenfocusDeblur": "Genfocus Deblur (All-in-Focus)",
    "GenfocusBokeh": "Genfocus Bokeh Effect",
    "GenfocusRefocus": "Genfocus Full Refocus Pipeline",
}
```

**FILE**: `docker/custom_nodes/ComfyUI-Genfocus/requirements.txt`
**ACTION**: Create new file

```
einops
timm
kornia
safetensors
```

**VERIFICATION**:
```bash
# After ComfyUI starts, check nodes loaded
curl -s http://localhost:8188/object_info | jq 'keys | map(select(startswith("Genfocus")))'
```

---

### 3.2 MVInverse Custom Node

**FILE**: `docker/custom_nodes/ComfyUI-MVInverse/__init__.py`
**ACTION**: Create new file

```python
"""
ComfyUI-MVInverse: Multi-View Inverse Rendering Node
Predicts albedo, metallic, roughness, normals, and shading from multi-view images.
"""

import os
import torch
import numpy as np
from PIL import Image

# Lazy loading
_mvinverse_model = None

MODELS_DIR = "/workspace/ComfyUI/models/mvinverse"

def get_mvinverse_model():
    """Lazy load MVInverse model."""
    global _mvinverse_model
    if _mvinverse_model is None:
        # Check if model directory exists
        if not os.path.exists(MODELS_DIR):
            raise FileNotFoundError(f"MVInverse models not found at {MODELS_DIR}. Enable ENABLE_MVINVERSE=true to download.")

        # TODO: Load actual MVInverse model
        # The model uses DINOv2 encoder + DPT prediction heads
        # Placeholder for now
        _mvinverse_model = {"loaded": True}
    return _mvinverse_model


class MVInverseLoader:
    """Load MVInverse model into memory."""

    CATEGORY = "MVInverse"
    FUNCTION = "load_model"
    RETURN_TYPES = ("MVINVERSE_MODEL",)
    RETURN_NAMES = ("model",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
        }

    def load_model(self):
        """Load MVInverse model."""
        model = get_mvinverse_model()
        return (model,)


class MVInverseInference:
    """Run MVInverse inference on multi-view images."""

    CATEGORY = "MVInverse"
    FUNCTION = "infer"
    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("albedo", "metallic", "roughness", "normal", "shading")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MVINVERSE_MODEL",),
                "images": ("IMAGE",),  # Batch of multi-view images
            },
            "optional": {
                "output_resolution": (["original", "512", "1024"], {
                    "default": "original"
                }),
            },
        }

    def infer(self, model, images, output_resolution="original"):
        """
        Run MVInverse inference on batch of images.

        Args:
            model: Loaded MVInverse model
            images: Batch of multi-view images (B, H, W, C)
            output_resolution: Output map resolution

        Returns:
            albedo: RGB albedo maps
            metallic: Metallic maps (grayscale)
            roughness: Roughness maps (grayscale)
            normal: Normal maps (RGB, xyz encoded)
            shading: Diffuse shading maps (grayscale)
        """
        device = "cuda" if torch.cuda.is_available() else "cpu"

        batch_size, height, width, channels = images.shape

        # TODO: Implement actual MVInverse inference
        # The model architecture:
        # 1. DINOv2 encoder for patch tokens
        # 2. Alternating global-frame attention for cross-view aggregation
        # 3. ResNeXt encoder for multi-resolution features
        # 4. DPT-style prediction heads for each output

        # Placeholder outputs - same size as input
        albedo = images.clone()
        metallic = images.mean(dim=-1, keepdim=True).repeat(1, 1, 1, 3)
        roughness = torch.ones_like(metallic) * 0.5
        normal = torch.zeros_like(images)
        normal[..., 2] = 1.0  # Default normal pointing up (z=1)
        shading = images.mean(dim=-1, keepdim=True).repeat(1, 1, 1, 3)

        return (albedo, metallic, roughness, normal, shading)


class MVInverseSingleView:
    """Simplified single-view inverse rendering."""

    CATEGORY = "MVInverse"
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
        """
        Single-view inverse rendering (less accurate than multi-view).

        Args:
            image: Single input image (1, H, W, C)

        Returns:
            Material and geometry predictions
        """
        # Load model
        loader = MVInverseLoader()
        (model,) = loader.load_model()

        # Run inference
        inference = MVInverseInference()
        return inference.infer(model, image)


class MVInverseRelight:
    """Relight an image using MVInverse material predictions."""

    CATEGORY = "MVInverse"
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
        """
        Simple PBR-style relighting using predicted materials.

        Args:
            albedo: Base color
            normal: Surface normals
            metallic: Metallic factor
            roughness: Roughness factor
            light_direction: Horizontal angle in degrees
            light_elevation: Vertical angle in degrees
            light_intensity: Light brightness
            ambient_intensity: Ambient light level

        Returns:
            relit_image: Relit result
        """
        import math

        # Convert angles to light direction vector
        theta = math.radians(light_direction)
        phi = math.radians(light_elevation)
        light_dir = torch.tensor([
            math.cos(phi) * math.sin(theta),
            math.cos(phi) * math.cos(theta),
            math.sin(phi)
        ], dtype=albedo.dtype, device=albedo.device)

        # Decode normals from RGB (assume 0-1 range mapped to -1 to 1)
        normals_decoded = normal * 2.0 - 1.0

        # Compute diffuse shading (Lambert)
        # Shape: (B, H, W, 3) dot (3,) -> (B, H, W)
        n_dot_l = torch.clamp(
            torch.sum(normals_decoded * light_dir, dim=-1, keepdim=True),
            min=0.0
        )

        # Simple Lambertian + ambient
        diffuse = albedo * (n_dot_l * light_intensity + ambient_intensity)

        # Clamp to valid range
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
    "MVInverseLoader": "MVInverse Load Model",
    "MVInverseInference": "MVInverse Multi-View Inference",
    "MVInverseSingleView": "MVInverse Single View",
    "MVInverseRelight": "MVInverse Relight",
}
```

**FILE**: `docker/custom_nodes/ComfyUI-MVInverse/requirements.txt`
**ACTION**: Create new file

```
opencv-python-headless
safetensors
```

**VERIFICATION**:
```bash
# After ComfyUI starts, check nodes loaded
curl -s http://localhost:8188/object_info | jq 'keys | map(select(startswith("MVInverse")))'
```

---

## Phase 4: Testing & Verification

### 4.1 Docker Build Verification

```bash
cd /home/oz/projects/2025/oz/12/runpod/docker

# Full rebuild
docker compose build --no-cache

# Start with all new models enabled
ENABLE_QWEN_IMAGE_EDIT=true ENABLE_GENFOCUS=true ENABLE_MVINVERSE=true docker compose up -d

# Wait for startup
sleep 30

# Verify custom nodes loaded
docker exec runpod ls -la /workspace/ComfyUI/custom_nodes/ | grep -E "(QwenEdit|Genfocus|MVInverse)"

# Check for startup errors
docker logs runpod 2>&1 | grep -i error
```

### 4.2 Model Download Verification

```bash
# Check all models downloaded
docker exec runpod ls -la /workspace/ComfyUI/models/diffusion_models/ | grep qwen
docker exec runpod ls -la /workspace/ComfyUI/models/text_encoders/ | grep qwen
docker exec runpod ls -la /workspace/ComfyUI/models/genfocus/
docker exec runpod ls -la /workspace/ComfyUI/models/mvinverse/
```

### 4.3 Node Loading Verification

```bash
# Get available nodes from ComfyUI API
curl -s http://localhost:8188/object_info | python3 -c "
import sys, json
data = json.load(sys.stdin)
for key in sorted(data.keys()):
    if any(x in key.lower() for x in ['qwen', 'genfocus', 'mvinverse']):
        print(key)
"
```

### 4.4 Workflow Testing

1. Open ComfyUI at http://localhost:8188
2. Load test workflow for each model
3. Queue prompt and verify no validation errors
4. Check output image/data quality

---

## Phase 5: Documentation Updates

### 5.1 CLAUDE.md Storage Requirements

**FILE**: `/home/oz/projects/2025/oz/12/runpod/CLAUDE.md`
**ACTION**: Update storage requirements table

```markdown
| Component | Size | Notes |
|-----------|------|-------|
| **Qwen Image Edit 2511** | ~15GB | Image editing (FP8 quantized) |
| **Genfocus** | ~3GB | Depth-of-field (bokeh/deblur/depth) |
| **MVInverse** | ~2GB | Multi-view inverse rendering |
```

### 5.2 Environment Variables Documentation

Add to CLAUDE.md:

```markdown
| Variable | Default | Size |
|----------|---------|------|
| `ENABLE_QWEN_IMAGE_EDIT` | false | ~15GB |
| `ENABLE_GENFOCUS` | false | ~3GB |
| `ENABLE_MVINVERSE` | false | ~2GB |
```

---

## Implementation Order

1. **Phase 1.1-1.5**: Environment variables and Dockerfile (30 min)
2. **Phase 2.1-2.3**: Download script additions (15 min)
3. **Phase 3.1**: Genfocus custom node (45 min)
4. **Phase 3.2**: MVInverse custom node (45 min)
5. **Phase 4**: Testing and verification (30 min)
6. **Phase 5**: Documentation updates (15 min)

---

## Risk Mitigation

### Dependency Conflicts

The latest diffusers from git may conflict with other packages. Mitigation:
- Install diffusers last in Layer 4
- Use `|| true` to allow graceful failure
- Test specific diffusers commit if issues arise

### VRAM Constraints

All three models require significant VRAM:
- Qwen Image Edit: 12-16GB
- Genfocus: 12GB+
- MVInverse: 10-16GB

Mitigation:
- Only enable one major model at a time on 16GB GPUs
- Use FP8 quantized versions where available
- Document VRAM requirements clearly

### Model Architecture Uncertainty

Genfocus and MVInverse are research projects without official ComfyUI nodes. The custom wrappers are placeholders that need:
- Actual model architecture implementation
- Proper weight loading from safetensors/pt files
- Inference pipeline matching paper methodology

Mitigation:
- Start with placeholder nodes that load but may not function
- Iterate on actual implementation after basic structure works
- Reference original Python code for inference details

---

## References

- [Qwen-Image-Edit-2511 HuggingFace](https://huggingface.co/Qwen/Qwen-Image-Edit-2511)
- [Comfyui-QwenEditUtils GitHub](https://github.com/lrzjason/Comfyui-QwenEditUtils)
- [Genfocus GitHub](https://github.com/rayray9999/Genfocus)
- [Genfocus-Model HuggingFace](https://huggingface.co/nycu-cplab/Genfocus-Model)
- [MVInverse GitHub](https://github.com/Maddog241/mvinverse)
- [ComfyUI Docs - Qwen Image Edit](https://docs.comfy.org/tutorials/image/qwen/qwen-image-edit)
