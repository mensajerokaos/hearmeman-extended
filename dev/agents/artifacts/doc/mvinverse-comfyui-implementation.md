---
author: oz
model: claude-haiku-4-5-20251001
date: 2025-12-29
task: MVInverse ComfyUI Custom Node Implementation Plan
---

# MVInverse ComfyUI Integration - Implementation Plan

## Overview

This document outlines the complete implementation strategy for creating a ComfyUI custom node wrapper for MVInverse, a multi-view inverse rendering model that reconstructs scene geometry and material properties from multi-view images.

### Key Capabilities

- **Input**: Multi-view images (N views of the same scene)
- **Outputs**:
  - Albedo (base color)
  - Surface normal maps
  - Metallic properties
  - Roughness maps
  - Shading information
- **Approach**: Feed-forward inference with multi-view consistency
- **Model**: ViT-Large backbone + ResNeXt101 + DPT heads

---

## Part 1: Architecture & Node Structure

### 1.1 Node Design Overview

The MVInverse integration will consist of two main nodes:

#### Node 1: MVInverse Model Loader
- **Purpose**: Load the MVInverse model from checkpoint
- **Handles**: Model caching, device management
- **Output**: Model reference for use in inference node

#### Node 2: MVInverse Inverse Rendering Node
- **Purpose**: Execute inverse rendering on multi-view images
- **Inputs**: Multi-view image batch, loaded model, optional parameters
- **Outputs**: Tuple of material maps (albedo, normal, metallic, roughness, shading)

### 1.2 ComfyUI Node Class Structure

```python
# Class Definition Pattern
class MVInverseLoader:
    """Load MVInverse model checkpoint."""

    @classmethod
    def INPUT_TYPES(cls):
        """Define input parameters."""
        return {
            "required": {
                "checkpoint_name": (
                    ["mvinverse"],  # or list of available checkpoints
                    {"default": "mvinverse"}
                ),
                "device": (
                    ["cuda", "cpu"],
                    {"default": "cuda"}
                ),
            },
        }

    RETURN_TYPES = ("MVINVERSE_MODEL",)
    RETURN_NAMES = ("mvinverse_model",)
    FUNCTION = "load_model"
    CATEGORY = "loaders/models"

    def load_model(self, checkpoint_name, device):
        """Load and cache the model."""
        # Implementation details below
        pass


class MVInverseInverse:
    """Execute inverse rendering on multi-view images."""

    @classmethod
    def INPUT_TYPES(cls):
        """Define input parameters."""
        return {
            "required": {
                "images": ("IMAGE",),  # [B, H, W, C] - batch as views
                "mvinverse_model": ("MVINVERSE_MODEL",),
                "max_size": ("INT", {
                    "default": 1024,
                    "min": 512,
                    "max": 2048,
                    "step": 64
                }),
                "use_fp16": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("albedo", "normal", "metallic", "roughness", "shading")
    FUNCTION = "inverse_render"
    CATEGORY = "image/material"

    def inverse_render(self, images, mvinverse_model, max_size, use_fp16):
        """Execute inverse rendering."""
        # Implementation details below
        pass
```

---

## Part 2: Input/Output Definitions

### 2.1 Input Format Handling

**ComfyUI Image Format**: `[B, H, W, C]` (float32, range [0.0, 1.0])
- `B`: Batch dimension (in multi-view context = number of views `N`)
- `H`, `W`: Height, Width
- `C`: Channels (3 for RGB)

**MVInverse Expected Format**: `[1, N, 3, H, W]` (single batch with N views)
- `1`: Batch dimension (always 1 for inference)
- `N`: Number of views
- `3`: RGB channels
- `H`, `W`: Height, Width

**Conversion Strategy**:

```python
def prepare_images_for_mvinverse(images_batch, max_size=1024):
    """
    Convert ComfyUI image batch to MVInverse format.

    Args:
        images_batch: Tensor of shape [B, H, W, C] (B=number of views)
        max_size: Maximum longest dimension (default 1024)

    Returns:
        prepared: Tensor of shape [1, B, 3, H, W] ready for MVInverse
        original_shape: Tuple of original dimensions for restoration
    """
    B, H, W, C = images_batch.shape

    # Step 1: Convert from [B, H, W, C] to [B, C, H, W]
    images = images_batch.permute(0, 3, 1, 2)  # [B, C, H, W]

    # Step 2: Ensure 3 channels (handle 4-channel/grayscale)
    if C != 3:
        if C == 4:
            images = images[:, :3, :, :]  # Drop alpha
        elif C == 1:
            images = images.repeat(1, 3, 1, 1)  # Grayscale to RGB

    # Step 3: Resize to max_size while maintaining aspect ratio
    scale = min(max_size / max(H, W), 1.0)
    new_h = int(H * scale)
    new_w = int(W * scale)

    # Step 4: Adjust dimensions to be divisible by 14 (patch size)
    new_h = (new_h // 14) * 14
    new_w = (new_w // 14) * 14

    if new_h != H or new_w != W:
        images = torch.nn.functional.interpolate(
            images, size=(new_h, new_w), mode='bilinear', align_corners=False
        )

    # Step 5: Convert value range [0, 1] -> [0, 255] for model
    images = (images * 255.0).to(torch.uint8).float() / 255.0

    # Step 6: Add batch dimension [B, C, H, W] -> [1, B, C, H, W]
    images = images.unsqueeze(0)

    return images, (H, W)
```

### 2.2 Output Format Handling

**MVInverse Raw Outputs** (model returns):
- `albedo`: `[N, H, W, 3]` (range [0, 255])
- `normal`: `[N, H, W, 3]` (normalized, range [-1, 1])
- `metallic`: `[N, H, W, 1]` (range [0, 255])
- `roughness`: `[N, H, W, 1]` (range [0, 255])
- `shading`: `[N, H, W, 3]` (range [0, 255])

**ComfyUI Expected Format**: `[B, H, W, C]` (float32, range [0.0, 1.0])

**Conversion Strategy**:

```python
def process_mvinverse_outputs(outputs, original_size=None):
    """
    Convert MVInverse outputs to ComfyUI image format.

    Args:
        outputs: Dict with keys {albedo, normal, metallic, roughness, shading}
        original_size: Tuple (orig_H, orig_W) for optional upsampling

    Returns:
        Dict of tensors in ComfyUI format [B, H, W, C]
    """
    processed = {}

    for key in ['albedo', 'normal', 'metallic', 'roughness', 'shading']:
        tensor = outputs[key]  # [N, H, W, C] from model

        # Normalize to [0, 1] range based on type
        if key == 'normal':
            # Normal: remap [-1, 1] to [0, 1]
            tensor = tensor * 0.5 + 0.5
        else:
            # All others are in [0, 255], normalize to [0, 1]
            tensor = tensor / 255.0

        # Clamp values to valid range
        tensor = torch.clamp(tensor, 0.0, 1.0)

        # Ensure float32 and correct shape [N, H, W, C]
        tensor = tensor.to(torch.float32)

        processed[key] = tensor  # Ready for ComfyUI

    return processed
```

### 2.3 Complete Input/Output Type Definitions

```python
class MVInverseLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "checkpoint_name": (
                    ["mvinverse"],  # Can expand with version options
                    {"default": "mvinverse"}
                ),
                "device": (
                    ["cuda", "cpu"],
                    {"default": "cuda"}
                ),
                "use_fp16": (
                    ["auto", "true", "false"],
                    {"default": "auto"}
                ),
            },
        }

    RETURN_TYPES = ("MVINVERSE_MODEL",)
    RETURN_NAMES = ("mvinverse_model",)


class MVInverseInverse:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "mvinverse_model": ("MVINVERSE_MODEL",),
                "max_size": (
                    "INT",
                    {"default": 1024, "min": 512, "max": 2048, "step": 64}
                ),
                "use_fp16": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "preserve_original_size": ("BOOLEAN", {"default": False}),
                "upscale_output": (
                    ["disabled", "bilinear", "nearest"],
                    {"default": "disabled"}
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = (
        "albedo_maps",
        "normal_maps",
        "metallic_maps",
        "roughness_maps",
        "shading_maps"
    )
```

---

## Part 3: Model Loading Strategy

### 3.1 Checkpoint Management

```python
import folder_paths
import os

# Define checkpoint paths
CHECKPOINTS_DIR = os.path.join(
    folder_paths.get_output_directory(),
    "..",
    "models",
    "mvinverse"
)

class MVInverseLoader:
    _models_cache = {}  # Global cache to avoid reloading

    @classmethod
    def INPUT_TYPES(cls):
        # Dynamically list available checkpoints
        checkpoint_options = cls._get_available_checkpoints()
        return {
            "required": {
                "checkpoint_name": (
                    checkpoint_options,
                    {"default": checkpoint_options[0] if checkpoint_options else "mvinverse"}
                ),
                "device": (["cuda", "cpu"], {"default": "cuda"}),
                "use_fp16": (["auto", "true", "false"], {"default": "auto"}),
            },
        }

    @staticmethod
    def _get_available_checkpoints():
        """Scan for available MVInverse checkpoints."""
        checkpoints = []

        # Check local directory
        if os.path.exists(CHECKPOINTS_DIR):
            checkpoints.extend([
                f.replace(".pt", "")
                for f in os.listdir(CHECKPOINTS_DIR)
                if f.endswith(".pt")
            ])

        # Always include HF Hub option
        if "mvinverse" not in checkpoints:
            checkpoints.insert(0, "mvinverse")  # HF Hub default

        return checkpoints or ["mvinverse"]

    def load_model(self, checkpoint_name, device, use_fp16):
        """Load or retrieve cached model."""
        cache_key = f"{checkpoint_name}_{device}_{use_fp16}"

        # Return cached model if available
        if cache_key in MVInverseLoader._models_cache:
            return (MVInverseLoader._models_cache[cache_key],)

        # Determine device
        if device == "cuda" and not torch.cuda.is_available():
            print("CUDA not available, falling back to CPU")
            device = "cpu"

        # Determine precision
        dtype = torch.float16 if use_fp16 == "true" or (
            use_fp16 == "auto" and device == "cuda"
        ) else torch.float32

        # Load model
        model = self._load_checkpoint(checkpoint_name, device, dtype)
        model.eval()

        # Cache for future use
        MVInverseLoader._models_cache[cache_key] = model

        return (model,)

    @staticmethod
    def _load_checkpoint(checkpoint_name, device, dtype):
        """
        Load checkpoint from local file or HF Hub.

        Args:
            checkpoint_name: Either a local path or HF model ID
            device: torch device
            dtype: torch dtype (float16 or float32)

        Returns:
            Loaded model in eval mode
        """
        from mvinverse.models.mvinverse import MVInverse

        # Try local path first
        local_path = os.path.join(CHECKPOINTS_DIR, f"{checkpoint_name}.pt")
        if os.path.exists(local_path):
            checkpoint = torch.load(local_path, map_location=device)
            print(f"Loaded MVInverse from local path: {local_path}")
        else:
            # Load from HF Hub
            from huggingface_hub import hf_hub_download
            checkpoint_file = hf_hub_download(
                repo_id="maddog241/mvinverse",
                filename="mvinverse.pt",
                cache_dir=CHECKPOINTS_DIR,
                resume_download=True
            )
            checkpoint = torch.load(checkpoint_file, map_location=device)
            print(f"Loaded MVInverse from HF Hub")

        # Initialize model
        model = MVInverse()

        # Handle checkpoint format (dict vs direct state)
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)

        # Move to device and set precision
        model = model.to(device=device, dtype=dtype)

        return model
```

### 3.2 Memory-Efficient Inference

```python
class MVInverseInverse:
    def inverse_render(self, images, mvinverse_model, max_size, use_fp16):
        """Execute inverse rendering with memory optimization."""

        device = next(mvinverse_model.parameters()).device
        dtype = next(mvinverse_model.parameters()).dtype

        # Prepare images
        prepared_images, original_shape = self.prepare_images_for_mvinverse(
            images, max_size
        )
        prepared_images = prepared_images.to(device=device, dtype=dtype)

        # Inference with appropriate context
        with torch.no_grad():
            if device.type == 'cuda' and dtype == torch.float16:
                with torch.amp.autocast('cuda', dtype=torch.float16):
                    outputs = mvinverse_model(prepared_images)
            else:
                outputs = mvinverse_model(prepared_images)

        # Process outputs
        processed = self.process_mvinverse_outputs(outputs, original_shape)

        return (
            processed['albedo'],
            processed['normal'],
            processed['metallic'],
            processed['roughness'],
            processed['shading']
        )
```

---

## Part 4: Complete Node Implementation

### 4.1 MVInverse Loader Node

```python
"""
mvinverse_loader.py
Loads MVInverse checkpoint from local or HF Hub with model caching.
"""

import torch
import os
import folder_paths
from pathlib import Path


class MVInverseLoader:
    """Load MVInverse model checkpoint."""

    _models_cache = {}

    def __init__(self):
        self.checkpoints_dir = os.path.join(
            folder_paths.get_models_dir(), "mvinverse"
        )
        os.makedirs(self.checkpoints_dir, exist_ok=True)

    @classmethod
    def INPUT_TYPES(cls):
        checkpoints = cls._get_checkpoint_options()
        return {
            "required": {
                "checkpoint": (
                    checkpoints,
                    {"default": checkpoints[0] if checkpoints else "mvinverse"}
                ),
                "device": (
                    ["cuda", "cpu"],
                    {"default": "cuda"}
                ),
                "use_fp16": (
                    ["auto", "true", "false"],
                    {"default": "auto"}
                ),
            },
        }

    RETURN_TYPES = ("MVINVERSE_MODEL",)
    RETURN_NAMES = ("mvinverse_model",)
    FUNCTION = "load_model"
    CATEGORY = "loaders/models"

    @classmethod
    def _get_checkpoint_options(cls):
        """Get list of available checkpoints."""
        checkpoints = ["mvinverse"]  # HF Hub default

        models_dir = os.path.join(folder_paths.get_models_dir(), "mvinverse")
        if os.path.exists(models_dir):
            local_checkpoints = [
                f.replace(".pt", "")
                for f in os.listdir(models_dir)
                if f.endswith(".pt")
            ]
            checkpoints = local_checkpoints + checkpoints

        return list(dict.fromkeys(checkpoints))  # Remove duplicates

    def load_model(self, checkpoint, device, use_fp16):
        """Load MVInverse model with caching."""

        cache_key = f"{checkpoint}_{device}_{use_fp16}"

        if cache_key in MVInverseLoader._models_cache:
            print(f"[MVInverse] Using cached model: {checkpoint}")
            return (MVInverseLoader._models_cache[cache_key],)

        # Validate device
        if device == "cuda" and not torch.cuda.is_available():
            print("[MVInverse] CUDA unavailable, falling back to CPU")
            device = "cpu"

        # Determine dtype
        if use_fp16 == "true":
            dtype = torch.float16
        elif use_fp16 == "false":
            dtype = torch.float32
        else:  # auto
            dtype = torch.float16 if device == "cuda" else torch.float32

        print(f"[MVInverse] Loading {checkpoint} on {device} ({dtype})")

        # Load checkpoint
        model = self._load_checkpoint(checkpoint, device, dtype)
        model.eval()

        # Cache model
        MVInverseLoader._models_cache[cache_key] = model

        return (model,)

    def _load_checkpoint(self, checkpoint_name, device, dtype):
        """Load checkpoint from local or HF Hub."""

        from mvinverse.models.mvinverse import MVInverse
        from huggingface_hub import hf_hub_download

        # Try local first
        local_path = os.path.join(self.checkpoints_dir, f"{checkpoint_name}.pt")

        if os.path.exists(local_path):
            checkpoint_path = local_path
            print(f"[MVInverse] Loading from local: {checkpoint_path}")
        else:
            # Download from HF Hub
            checkpoint_path = hf_hub_download(
                repo_id="maddog241/mvinverse",
                filename="mvinverse.pt",
                cache_dir=self.checkpoints_dir,
                resume_download=True
            )
            print(f"[MVInverse] Downloaded from HF Hub")

        # Load weights
        checkpoint = torch.load(checkpoint_path, map_location=device)

        # Initialize model
        model = MVInverse()

        # Load state dict
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        elif isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
            model.load_state_dict(checkpoint['state_dict'])
        else:
            model.load_state_dict(checkpoint)

        # Move to device with correct dtype
        model = model.to(device=device, dtype=dtype)

        return model
```

### 4.2 MVInverse Inverse Rendering Node

```python
"""
mvinverse_inverse.py
Execute inverse rendering on multi-view images.
"""

import torch
import torch.nn.functional as F


class MVInverseInverse:
    """Execute multi-view inverse rendering."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "mvinverse_model": ("MVINVERSE_MODEL",),
                "max_size": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 512,
                        "max": 2048,
                        "step": 64,
                    }
                ),
                "use_fp16": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "upscale_output": (
                    ["disabled", "bilinear", "nearest"],
                    {"default": "disabled"}
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = (
        "albedo",
        "normal",
        "metallic",
        "roughness",
        "shading"
    )
    FUNCTION = "inverse_render"
    CATEGORY = "image/material"

    def inverse_render(
        self,
        images,
        mvinverse_model,
        max_size,
        use_fp16,
        upscale_output="disabled"
    ):
        """Execute inverse rendering on multi-view images."""

        device = next(mvinverse_model.parameters()).device
        dtype = next(mvinverse_model.parameters()).dtype

        B, H, W, C = images.shape
        print(f"[MVInverse] Input: {B} views, {H}x{W}, {C} channels")

        # Step 1: Prepare images for MVInverse
        prepared, original_size = self._prepare_images(
            images, max_size
        )
        prepared = prepared.to(device=device, dtype=dtype)

        # Step 2: Run inference
        with torch.no_grad():
            if dtype == torch.float16 and device.type == 'cuda':
                with torch.amp.autocast('cuda', dtype=torch.float16):
                    outputs = mvinverse_model(prepared)
            else:
                outputs = mvinverse_model(prepared)

        # Step 3: Process outputs to ComfyUI format
        result = self._process_outputs(outputs, original_size, upscale_output)

        return (
            result['albedo'],
            result['normal'],
            result['metallic'],
            result['roughness'],
            result['shading']
        )

    @staticmethod
    def _prepare_images(images_batch, max_size):
        """
        Convert [B, H, W, C] to [1, B, 3, H, W] for MVInverse.
        Returns prepared tensor and original size for restoration.
        """
        B, H, W, C = images_batch.shape

        # Convert to [B, C, H, W]
        images = images_batch.permute(0, 3, 1, 2)

        # Handle channel count
        if C == 4:
            images = images[:, :3, :, :]  # Drop alpha
        elif C == 1:
            images = images.repeat(1, 3, 1, 1)  # Expand grayscale

        # Resize while maintaining aspect ratio
        scale = min(max_size / max(H, W), 1.0)
        new_h = int(H * scale)
        new_w = int(W * scale)

        # Align to patch size (14)
        new_h = (new_h // 14) * 14
        new_w = (new_w // 14) * 14

        if (new_h, new_w) != (H, W):
            images = F.interpolate(
                images,
                size=(new_h, new_w),
                mode='bilinear',
                align_corners=False
            )

        # Add batch dimension: [B, C, H, W] -> [1, B, C, H, W]
        images = images.unsqueeze(0)

        return images, (H, W)

    @staticmethod
    def _process_outputs(outputs, original_size, upscale_mode):
        """
        Convert MVInverse outputs to ComfyUI format [B, H, W, C].
        Handles normalization and optional upscaling.
        """
        result = {}
        H, W = original_size

        for key in ['albedo', 'normal', 'metallic', 'roughness', 'shading']:
            tensor = outputs[key]  # [N, H, W, C] from model

            # Normalize based on output type
            if key == 'normal':
                # Remap [-1, 1] to [0, 1]
                tensor = tensor * 0.5 + 0.5
            else:
                # All others: [0, 255] -> [0, 1]
                tensor = tensor / 255.0

            # Clamp and ensure float32
            tensor = torch.clamp(tensor, 0.0, 1.0).to(torch.float32)

            # Optional upscaling back to original size
            if upscale_mode != "disabled" and (tensor.shape[1], tensor.shape[2]) != (H, W):
                tensor = tensor.permute(0, 3, 1, 2)  # [N, H, W, C] -> [N, C, H, W]
                tensor = F.interpolate(
                    tensor,
                    size=(H, W),
                    mode=upscale_mode,
                    align_corners=False if upscale_mode == "bilinear" else None
                )
                tensor = tensor.permute(0, 2, 3, 1)  # [N, C, H, W] -> [N, H, W, C]

            result[key] = tensor

        return result
```

### 4.3 Package Registration

```python
"""
__init__.py
Register nodes for ComfyUI.
"""

from .mvinverse_loader import MVInverseLoader
from .mvinverse_inverse import MVInverseInverse

NODE_CLASS_MAPPINGS = {
    "MVInverseLoader": MVInverseLoader,
    "MVInverseInverse": MVInverseInverse,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MVInverseLoader": "Load MVInverse Model",
    "MVInverseInverse": "MVInverse Inverse Render",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
```

---

## Part 5: Example Workflow

### 5.1 Basic Workflow Structure

```json
{
  "1": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "model.safetensors"
    }
  },
  "2": {
    "class_type": "LoadImage",
    "inputs": {
      "image": "view1.png"
    }
  },
  "3": {
    "class_type": "LoadImage",
    "inputs": {
      "image": "view2.png"
    }
  },
  "4": {
    "class_type": "LoadImage",
    "inputs": {
      "image": "view3.png"
    }
  },
  "5": {
    "class_type": "ImageBatch",
    "inputs": {
      "image1": ["2", 0],
      "image2": ["3", 0],
      "image3": ["4", 0]
    }
  },
  "6": {
    "class_type": "MVInverseLoader",
    "inputs": {
      "checkpoint": "mvinverse",
      "device": "cuda",
      "use_fp16": "auto"
    }
  },
  "7": {
    "class_type": "MVInverseInverse",
    "inputs": {
      "images": ["5", 0],
      "mvinverse_model": ["6", 0],
      "max_size": 1024,
      "use_fp16": true,
      "upscale_output": "disabled"
    }
  },
  "8": {
    "class_type": "SaveImage",
    "inputs": {
      "images": ["7", 0],
      "filename_prefix": "albedo"
    }
  },
  "9": {
    "class_type": "SaveImage",
    "inputs": {
      "images": ["7", 1],
      "filename_prefix": "normal"
    }
  }
}
```

### 5.2 Multi-View Workflow Steps

**Step 1**: Load multiple images representing different views
```
LoadImage (view_1.png) -> output [1, H, W, 3]
LoadImage (view_2.png) -> output [1, H, W, 3]
LoadImage (view_3.png) -> output [1, H, W, 3]
```

**Step 2**: Combine views into batch
```
ImageBatch -> [3, H, W, 3]  (3 views stacked as batch)
```

**Step 3**: Load MVInverse model
```
MVInverseLoader -> MVINVERSE_MODEL (cached)
```

**Step 4**: Execute inverse rendering
```
MVInverseInverse:
  - Input: [3, H, W, 3] (3 views)
  - Model: MVInverse
  - Output 0: Albedo [3, H, W, 3]
  - Output 1: Normal [3, H, W, 3]
  - Output 2: Metallic [3, H, W, 1]
  - Output 3: Roughness [3, H, W, 1]
  - Output 4: Shading [3, H, W, 3]
```

**Step 5**: Save outputs
```
SaveImage (albedo) -> albedo_*.png
SaveImage (normal) -> normal_*.png
SaveImage (metallic) -> metallic_*.png
SaveImage (roughness) -> roughness_*.png
SaveImage (shading) -> shading_*.png
```

---

## Part 6: Dependencies & Installation

### 6.1 Required Dependencies

```txt
# Core MVInverse package
torch>=2.5.1
torchvision>=0.20.1

# MVInverse dependencies
pillow>=9.0.0
opencv-python>=4.5.0
huggingface_hub>=0.16.0

# Optional for CUDA support
# torch-cuda-wheels (handled by CUDA-compatible torch install)
```

### 6.2 Installation in ComfyUI

**Option 1: Clone into custom_nodes**

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/maddog241/mvinverse.git
cd mvinverse
pip install -e .
git clone https://github.com/[your-user]/ComfyUI-MVInverse.git
```

**Option 2: Manual integration**

```bash
# Place files in:
ComfyUI/custom_nodes/ComfyUI-MVInverse/
├── __init__.py
├── mvinverse_loader.py
├── mvinverse_inverse.py
└── requirements.txt

# Install requirements
pip install -r ComfyUI/custom_nodes/ComfyUI-MVInverse/requirements.txt
pip install -e <mvinverse-repo>
```

### 6.3 Environment Setup

```bash
# CUDA 11.8 (recommended)
pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu118

# CPU only
pip install torch==2.5.1 torchvision==0.20.1

# Model checkpoint (~1.5GB)
# Will auto-download from HF Hub on first use
```

---

## Part 7: Implementation Checklist

### Phase 1: Core Integration
- [ ] Create `mvinverse_loader.py` with model loading and caching
- [ ] Create `mvinverse_inverse.py` with inverse rendering execution
- [ ] Implement image format conversion ([B,H,W,C] <-> [1,B,3,H,W])
- [ ] Implement output normalization and post-processing
- [ ] Create `__init__.py` for node registration

### Phase 2: Testing & Validation
- [ ] Unit test: Image format conversion correctness
- [ ] Unit test: Model loading (cache hit/miss)
- [ ] Integration test: Simple 2-view inference
- [ ] Integration test: Variable image sizes
- [ ] Validation: Output quality vs standalone inference
- [ ] Performance: Memory usage and inference speed

### Phase 3: Polish & Documentation
- [ ] Add detailed docstrings
- [ ] Create example workflow JSON
- [ ] Write user documentation
- [ ] Add error handling and user-friendly messages
- [ ] Optimize memory usage for large images/batches
- [ ] Test on CPU-only systems

### Phase 4: Publishing
- [ ] Create GitHub repository
- [ ] Add README with setup instructions
- [ ] License selection (match MVInverse license)
- [ ] Publish to ComfyUI-Manager (if applicable)
- [ ] Add usage examples and troubleshooting guide

---

## Part 8: Optimization Considerations

### Memory Efficiency

```python
# Strategies for large models/batches:

1. Model Quantization
   - torch.quantization.quantize_dynamic() for lighter inference

2. Gradient Checkpointing
   - model.gradient_checkpointing_enable() (if supported)

3. Batch Splitting
   - Process views sequentially if memory tight
   - Concatenate outputs afterward

4. Device-Aware Processing
   - Offload to CPU between inference steps
   - Use torch.cuda.empty_cache() strategically
```

### Speed Optimization

```python
# Inference acceleration:

1. Compile Model (PyTorch 2.0+)
   model = torch.compile(model, mode='reduce-overhead')

2. CUDA Graphs (for repeated inference)
   with torch.cuda.stream(stream):
       # Inference operations

3. Flash Attention
   - Already used in MVInverse decoder
   - Ensure CUDA 11.8+ for best performance

4. Kernel Fusion
   - torch.nn.functional operations fuse automatically
```

---

## Part 9: Known Limitations & Future Enhancements

### Current Limitations

1. **Minimum Image Size**: 224x224 (after patch alignment)
2. **Patch Size Constraint**: Height/Width must be divisible by 14
3. **Multi-view Count**: Typically 4-8 views optimal; more may cause memory issues
4. **Single Batch**: Currently processes one scene (batch size = 1)

### Future Enhancements

1. **Batch Processing**: Support multiple independent scenes
2. **Progressive Inference**: Stream results as views process
3. **Material Blending**: Combine outputs from different view angles
4. **Real-time Preview**: Live update during inference
5. **Export Formats**: Direct glTF/USD material export
6. **Fine-tuning Node**: Per-scene material adjustment
7. **View Weight Control**: Adjust influence of each view

---

## References

- **MVInverse Repository**: https://github.com/Maddog241/mvinverse
- **ComfyUI Documentation**: https://github.com/comfyorg/ComfyUI
- **ComfyUI Custom Nodes**: https://github.com/comfyorg/ComfyUI/blob/master/nodes.py
- **HuggingFace Hub Download**: https://huggingface.co/maddog241/mvinverse

---

**Document Version**: 1.0
**Status**: Ready for Implementation
**Last Updated**: 2025-12-29

