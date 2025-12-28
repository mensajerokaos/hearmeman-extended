# Phase 5 Task: ComfyUI Custom Node Wrappers Implementation Plan

This document outlines the implementation plan for creating custom ComfyUI nodes for Genfocus, MVInverse, and FlashPortrait models. These models currently lack native ComfyUI integration and require custom wrappers to be exposed within the ComfyUI environment.

## 1. Genfocus (Generative Refocusing)

### 1.1 Node Class Structure

```python
# nodes.py
import torch
import numpy as np
from PIL import Image

# Assume Genfocus model inference functions are in a separate module
# from ..genfocus_core import GenfocusModel

class GenfocusLoader:
    """
    Singleton-like class to load and manage the Genfocus model.
    Ensures model weights are loaded only once.
    """
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            # Placeholder for actual Genfocus model loading logic
            # This would involve loading bokehNet.safetensors, deblurNet.safetensors, depth_pro.pt
            # and initializing the Genfocus inference pipeline.
            print("Loading Genfocus model weights...")
            # cls._model = GenfocusModel(...) # Initialize your Genfocus model here
            cls._model = "MockGenfocusModel" # Placeholder
            print("Genfocus model loaded.")
        return cls._model

class GenfocusRefocus:
    def __init__(self):
        self.model = GenfocusLoader.get_model()

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "focal_depth": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
                "blur_amount": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0, "step": 0.1}),
            },
            "optional": {
                # Add any optional parameters specific to Genfocus
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "refocus_image"
    CATEGORY = "RunPod/Image/Genfocus"

    def refocus_image(self, image, focal_depth, blur_amount):
        # Convert ComfyUI IMAGE to Genfocus input format (e.g., PIL or NumPy array)
        # ComfyUI IMAGE is typically a torch.Tensor of shape [B, H, W, C] in [0, 1] range
        
        # Example conversion (ComfyUI Tensor to PIL Image)
        i = 255. * image.cpu().numpy()
        img_pil = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8)[0]) # Assuming batch size 1

        print(f"Genfocus refocusing image with focal_depth={focal_depth}, blur_amount={blur_amount}")
        # Placeholder for actual Genfocus inference call
        # result_img_pil = self.model.inference(img_pil, focal_depth, blur_amount)
        result_img_pil = img_pil # Mock result

        # Convert Genfocus output (e.g., PIL Image) back to ComfyUI IMAGE tensor
        result_img_np = np.array(result_img_pil).astype(np.float32) / 255.0
        result_img_tensor = torch.from_numpy(result_img_np)[None,] # Add batch dimension

        return (result_img_tensor,)

```

### 1.2 Integration Pattern

-   **Wrap Inference Script**: The core Genfocus inference logic will be wrapped in a Python module (e.g., `genfocus_core.py` within the `ComfyUI-Genfocus` directory). This module will expose functions for loading models and performing inference.
-   **Model Loading (Singleton Pattern)**: The `GenfocusLoader` class implements a basic singleton pattern to ensure that the large model weights (`bokehNet.safetensors`, `deblurNet.safetensors`, `depth_pro.pt`) are loaded into memory only once when the ComfyUI server starts or the node is first initialized. This prevents redundant memory usage and loading times.
-   **ComfyUI Image Tensor Conversion**:
    -   **Input**: ComfyUI provides images as `torch.Tensor` of shape `[B, H, W, C]` with pixel values in `[0, 1]`.
    -   **Conversion to Model**: Convert `torch.Tensor` to a format expected by Genfocus (e.g., `PIL.Image` or `numpy.ndarray` with `[H, W, C]` and `[0, 255]` pixel values).
    -   **Conversion from Model**: Convert Genfocus output (e.g., `PIL.Image` or `numpy.ndarray`) back to `torch.Tensor` of shape `[B, H, W, C]` in `[0, 1]` range for ComfyUI compatibility.

### 1.3 File Structure

```
ComfyUI/custom_nodes/
└── ComfyUI-Genfocus/
    ├── __init__.py
    ├── nodes.py
    ├── genfocus_core.py  # Placeholder for actual Genfocus wrapper/inference logic
    └── requirements.txt
```

### 1.4 `requirements.txt` for `ComfyUI-Genfocus`

```
# From Genfocus original requirements.txt (needs to be extracted from their repo)
# Plus any specific dependencies for our wrapper.
torch # ComfyUI already has it, but good to list
torchvision
numpy
Pillow # For image manipulation
# Placeholder: Actual Genfocus dependencies will go here
# e.g., diffusers, transformers, accelerate, etc.
```

### 1.5 Installation Instructions for Dockerfile

To be added to `docker/Dockerfile` under the "Layer 3: Custom Nodes (baked in)" section:

```dockerfile
# Genfocus
RUN git clone --depth 1 https://github.com/rayray9999/Genfocus.git /workspace/Genfocus_src && \
    mkdir -p custom_nodes/ComfyUI-Genfocus && \
    cp /workspace/Genfocus_src/genfocus_core.py custom_nodes/ComfyUI-Genfocus/genfocus_core.py && \
    cp /workspace/Genfocus_src/requirements.txt custom_nodes/ComfyUI-Genfocus/genfocus_requirements.txt && \
    rm -rf /workspace/Genfocus_src && \
    pip install --no-cache-dir -r custom_nodes/ComfyUI-Genfocus/genfocus_requirements.txt || true

# Download Genfocus model weights (to be handled by download_models.sh or directly in Dockerfile)
# Assuming models will be placed in /workspace/ComfyUI/models/genfocus
RUN mkdir -p /workspace/ComfyUI/models/genfocus
# This part would typically be in download_models.sh or a separate build step
# curl -L "https://huggingface.co/nycu-cplab/Genfocus-Model/resolve/main/bokehNet.safetensors" -o /workspace/ComfyUI/models/genfocus/bokehNet.safetensors
# curl -L "https://huggingface.co/nycu-cplab/Genfocus-Model/resolve/main/deblurNet.safetensors" -o /workspace/ComfyUI/models/genfocus/deblurNet.safetensors
# curl -L "https://huggingface.co/nycu-cplab/Genfocus-Model/resolve/main/checkpoints/depth_pro.pt" -o /workspace/ComfyUI/models/genfocus/depth_pro.pt
```
*(Note: The `cp` commands for `genfocus_core.py` and `requirements.txt` are placeholders. In a real scenario, we\'d either copy the entire Genfocus project and adapt it or write our `genfocus_core.py` from scratch, incorporating their logic.)*

---

## 2. MVInverse (Multi-view Inverse Rendering)

### 2.1 Node Class Structure

```python
# nodes.py
import torch
import numpy as np
from PIL import Image

# Assume MVInverse model inference functions are in a separate module
# from ..mvinverse_core import MVInverseModel

class MVInverseLoader:
    """
    Singleton-like class to load and manage the MVInverse model.
    Ensures model weights are loaded only once.
    """
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            print("Loading MVInverse model weights...")
            # cls._model = MVInverseModel(...) # Initialize your MVInverse model here
            cls._model = "MockMVInverseModel" # Placeholder
            print("MVInverse model loaded.")
        return cls._model

class MVInverseRender:
    def __init__(self):
        self.model = MVInverseLoader.get_model()

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_views": ("IMAGE", {"multiple": True}), # List of images
                "camera_poses": ("STRING", {"multiline": True, "placeholder": "JSON array of camera poses"}),
                # Add other required inputs as per MVInverse inference, e.g., resolution, camera intrinsics
            }
        }

    RETURN_TYPES = ("IMAGE", "MESH") # MESH might be a custom type or string path
    FUNCTION = "inverse_render"
    CATEGORY = "RunPod/3D/MVInverse"

    def inverse_render(self, image_views, camera_poses):
        # Convert ComfyUI IMAGE list to MVInverse input format
        # Each image in image_views is [B, H, W, C]
        processed_images = []
        for img_tensor in image_views:
            i = 255. * img_tensor.cpu().numpy()
            img_pil = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8)[0]) # Assuming batch size 1
            processed_images.append(img_pil) # Or convert to numpy/torch directly expected by MVInverse

        # Parse camera_poses (e.g., from JSON string to a list of arrays)
        # mv_camera_poses = json.loads(camera_poses) # Placeholder

        print(f"MVInverse performing inverse rendering with {len(image_views)} views.")
        # Placeholder for actual MVInverse inference call
        # result_mesh_data, result_render_img_pil = self.model.inference(processed_images, mv_camera_poses)
        result_render_img_pil = processed_images[0] if processed_images else Image.new('RGB', (512, 512)) # Mock image
        result_mesh_data = "mock_mesh_data.obj" # Mock mesh

        # Convert output back to ComfyUI format
        result_img_np = np.array(result_render_img_pil).astype(np.float32) / 255.0
        result_img_tensor = torch.from_numpy(result_img_np)[None,]

        return (result_img_tensor, result_mesh_data)

```

### 2.2 Integration Pattern

-   **Wrap Inference Script**: The core MVInverse inference logic will be encapsulated in a module (e.g., `mvinverse_core.py`). This module will handle model loading and the actual inverse rendering process.
-   **Model Loading (Singleton Pattern)**: The `MVInverseLoader` class will ensure that the MVInverse model and any required sub-models (e.g., DINOv2 encoder) are loaded once. MVInverse uses inference checkpoints, so the loader needs to handle checkpoint paths.
-   **ComfyUI Image Tensor Conversion**: Similar to Genfocus, convert ComfyUI `IMAGE` tensors to the format expected by MVInverse (likely `PIL.Image` or `torch.Tensor` in `[B, C, H, W]`) and convert the output back. Camera pose information will be passed as a string (e.g., JSON) and parsed within the node.

### 2.3 File Structure

```
ComfyUI/custom_nodes/
└── ComfyUI-MVInverse/
    ├── __init__.py
    ├── nodes.py
    ├── mvinverse_core.py # Placeholder for actual MVInverse wrapper/inference logic
    └── requirements.txt
```

### 2.4 `requirements.txt` for `ComfyUI-MVInverse`

```
# From MVInverse research document
torch==2.5.1 # Note: needs to be compatible with base CUDA 12.8, verify if 2.5.1 is ok
torchvision==0.20.1
torchaudio==2.5.1
opencv-python
huggingface_hub==0.35.0
numpy
Pillow
```
*(Note: `torch==2.5.1` is specified, but the base Docker image uses `pytorch:2.8.0-py3.11-cuda12.8.1`. This might require a separate `conda` environment or verification of `2.8.0` compatibility with `MVInverse`.*

### 2.5 Installation Instructions for Dockerfile

To be added to `docker/Dockerfile` under the "Layer 3: Custom Nodes (baked in)" section:

```dockerfile
# MVInverse
RUN git clone --depth 1 https://github.com/Maddog241/mvinverse.git /workspace/MVInverse_src && \
    mkdir -p custom_nodes/ComfyUI-MVInverse && \
    # We would copy relevant parts of the MVInverse source to the custom_nodes directory
    # For a full integration, this would involve copying the inference script and adapting it.
    # For now, just a placeholder copy of a custom nodes file
    cp /workspace/MVInverse_src/inference.py custom_nodes/ComfyUI-MVInverse/mvinverse_core.py && \
    echo "opencv-python\nhuggingface_hub==0.35.0\nnumpy\nPillow" > custom_nodes/ComfyUI-MVInverse/mvinverse_requirements.txt && \
    rm -rf /workspace/MVInverse_src && \
    pip install --no-cache-dir -r custom_nodes/ComfyUI-MVInverse/mvinverse_requirements.txt || true
    # Note: MVInverse specified torch==2.5.1 with CUDA 11.8. The base image has 2.8.0 with CUDA 12.8.1.
    # This might require a separate `pip install` with specific torch versions if 2.8.0 is incompatible,
    # or isolating the environment with `conda`. Assuming 2.8.0 is compatible for initial plan.
```
*(Note: Similar to Genfocus, copying `inference.py` directly is a placeholder. A proper wrapper would be written.)*

---

## 3. FlashPortrait (Portrait Animation)

### 3.1 Node Class Structure

```python
# nodes.py
import torch
import numpy as np
from PIL import Image
import folder_paths

# Assume FlashPortrait model inference functions are in a separate module
# from ..flashportrait_core import FlashPortraitModel

class FlashPortraitLoader:
    """
    Singleton-like class to load and manage the FlashPortrait model.
    Ensures model weights are loaded only once.
    """
    _model = None

    @classmethod
    def get_model(cls, gpu_memory_mode="sequential_cpu_offload"):
        if cls._model is None:
            print(f"Loading FlashPortrait model weights with mode: {gpu_memory_mode}...")
            # Placeholder for actual FlashPortrait model loading logic
            # This would involve initializing the FlashPortrait inference pipeline
            # and passing the gpu_memory_mode configuration.
            # cls._model = FlashPortraitModel(gpu_memory_mode=gpu_memory_mode)
            cls._model = "MockFlashPortraitModel" # Placeholder
            print("FlashPortrait model loaded.")
        return cls._model

class FlashPortraitAnimator:
    def __init__(self):
        # Model is loaded in the `animate_portrait` function to allow mode selection
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "source_image": ("IMAGE",),
                "driving_video": (folder_paths.get_filename_list("video"),), # Assuming video files are uploaded/available
                "resolution": (["480x832", "832x480", "512x512", "720x720", "720x1280", "1280x720"],),
                "gpu_memory_mode": (["model_full_load", "sequential_cpu_offload", "model_cpu_offload"],),
                # Add other required inputs as per FlashPortrait inference, e.g., output_fps
            }
        }

    RETURN_TYPES = ("VIDEO",) # VIDEO might be a custom type or string path
    FUNCTION = "animate_portrait"
    CATEGORY = "RunPod/Video/FlashPortrait"

    def animate_portrait(self, source_image, driving_video, resolution, gpu_memory_mode):
        # Load model with selected memory mode (can be optimized if mode is static)
        self.model = FlashPortraitLoader.get_model(gpu_memory_mode)

        # Convert ComfyUI IMAGE to FlashPortrait input format
        i = 255. * source_image.cpu().numpy()
        src_img_pil = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8)[0]) # Assuming batch size 1

        # Resolve driving_video path
        driving_video_path = folder_paths.get_full_path("video", driving_video)

        print(f"FlashPortrait animating portrait with resolution={resolution}, mode={gpu_memory_mode}")
        # Placeholder for actual FlashPortrait inference call
        # result_video_path = self.model.inference(src_img_pil, driving_video_path, resolution)
        result_video_path = "/tmp/mock_flashportrait_output.mp4" # Mock result

        return (result_video_path,)

```

### 3.2 Integration Pattern

-   **Wrap Inference Script**: The FlashPortrait inference logic will be in a module (e.g., `flashportrait_core.py`). This module will handle model loading, GPU memory modes, and video generation.
-   **Model Loading (Singleton with Mode)**: The `FlashPortraitLoader` will manage loading the FlashPortrait and Wan2.1-14B-720P models. The `gpu_memory_mode` parameter is critical for VRAM management, and ideally, the node allows selection of this mode. The `get_model` method can be extended to re-initialize the model if the mode changes, or a simpler approach can assume a fixed mode per ComfyUI instance.
-   **ComfyUI Image/Video Handling**:
    -   **Input Image**: Convert `ComfyUI IMAGE` tensor to `PIL.Image` or `numpy.ndarray`.
    -   **Input Video**: The `folder_paths.get_filename_list("video")` is used to allow users to select an uploaded video. The node will then use `folder_paths.get_full_path` to get the actual file path.
    -   **Output Video**: The node will return a path to the generated video file. A custom ComfyUI type for `VIDEO` might be needed for direct playback in the UI, or it can return a string path that the user can download.

### 3.3 File Structure

```
ComfyUI/custom_nodes/
└── ComfyUI-FlashPortrait/
    ├── __init__.py
    ├── nodes.py
    ├── flashportrait_core.py # Placeholder for actual FlashPortrait wrapper/inference logic
    └── requirements.txt
```

### 3.4 `requirements.txt` for `ComfyUI-FlashPortrait`

```
# From FlashPortrait research document
torch==2.6.0 # Note: needs to be compatible with base CUDA 12.8, verify if 2.6.0 is ok
torchvision==0.21.0
torchaudio==2.1.1
flash_attn # For optional acceleration
numpy
Pillow
# Additional dependencies from FlashPortrait's original requirements.txt
```
*(Note: FlashPortrait specifies `torch==2.6.0` with CUDA 12.4. The base Docker image uses `pytorch:2.8.0-py3.11-cuda12.8.1`. This is a potential version conflict that needs careful handling, possibly with a separate `conda` environment or by confirming backward compatibility.)*

### 3.5 Installation Instructions for Dockerfile

To be added to `docker/Dockerfile` under the "Layer 3: Custom Nodes (baked in)" section:

```dockerfile
# FlashPortrait
RUN git clone --depth 1 https://github.com/Francis-Rings/FlashPortrait.git /workspace/FlashPortrait_src && \
    mkdir -p custom_nodes/ComfyUI-FlashPortrait && \
    # Copy relevant source files, including the main inference script and any utilities.
    # For instance, a dedicated wrapper `flashportrait_core.py` might be created from FlashPortrait_src.
    cp /workspace/FlashPortrait_src/src/flashportrait/inference.py custom_nodes/ComfyUI-FlashPortrait/flashportrait_core.py && \
    echo "flash_attn\nnumpy\nPillow" > custom_nodes/ComfyUI-FlashPortrait/flashportrait_requirements.txt && \
    rm -rf /workspace/FlashPortrait_src && \
    pip install --no-cache-dir -r custom_nodes/ComfyUI-FlashPortrait/flashportrait_requirements.txt || true
    # Note: FlashPortrait specified torch==2.6.0 with CUDA 12.4. The base image has 2.8.0 with CUDA 12.8.1.
    # This might require a separate `pip install` with specific torch versions if 2.8.0 is incompatible,
    # or isolating the environment with `conda`. Assuming 2.8.0 is compatible for initial plan.
```

---

## 4. General `__init__.py` Structure for Custom Nodes

For each custom node directory (e.g., `ComfyUI-Genfocus`, `ComfyUI-MVInverse`, `ComfyUI-FlashPortrait`), the `__init__.py` file will typically look like this:

```python
# __init__.py
from .nodes import (
    GenfocusRefocus, # For Genfocus
    MVInverseRender, # For MVInverse
    FlashPortraitAnimator # For FlashPortrait
)

# List of nodes to expose to ComfyUI
NODE_CLASS_MAPPINGS = {
    "GenfocusRefocus": GenfocusRefocus,
    "MVInverseRender": MVInverseRender,
    "FlashPortraitAnimator": FlashPortraitAnimator,
}

# A dictionary that provides more descriptive names for the nodes in the ComfyUI UI
NODE_DISPLAY_NAME_MAPPINGS = {
    "GenfocusRefocus": "Genfocus Refocus Image",
    "MVInverseRender": "MVInverse Render 3D Model",
    "FlashPortraitAnimator": "FlashPortrait Animate Portrait",
}

# Optional: Category for the nodes in the ComfyUI UI
# CATEGORY = "RunPod/Image" # This is usually defined per node class for more granular categorization

print("### ComfyUI-CustomNodes Loaded ###")
```
*(Note: The `__init__.py` above combines all three for brevity, but each `custom_nodes` folder would have its own specific `__init__.py` listing only its nodes.)*

---

## 5. Model Weights Download Strategy

Model weights are large and should ideally be downloaded once. This can be managed by modifying the existing `download_models.sh` script or by adding `RUN` commands directly to the Dockerfile for specific models. Given the size, using `aria2c` for faster downloads is recommended.

### Example `download_models.sh` additions:

```bash
#!/bin/bash

# ... existing script content ...

COMFYUI_MODELS_DIR="/workspace/ComfyUI/models"

# Genfocus Models
echo "Downloading Genfocus models..."
mkdir -p "${COMFYUI_MODELS_DIR}/genfocus"
aria2c -x 16 -s 16 -o bokehNet.safetensors "https://huggingface.co/nycu-cplab/Genfocus-Model/resolve/main/bokehNet.safetensors" -d "${COMFYUI_MODELS_DIR}/genfocus"
aria2c -x 16 -s 16 -o deblurNet.safetensors "https://huggingface.co/nycu-cplab/Genfocus-Model/resolve/main/deblurNet.safetensors" -d "${COMFYUI_MODELS_DIR}/genfocus"
aria2c -x 16 -s 16 -o depth_pro.pt "https://huggingface.co/nycu-cplab/Genfocus-Model/resolve/main/checkpoints/depth_pro.pt" -d "${COMFYUI_MODELS_DIR}/genfocus"

# FlashPortrait Models
echo "Downloading FlashPortrait and Wan2.1-14B-720P models..."
mkdir -p "${COMFYUI_MODELS_DIR}/flashportrait"
# FlashPortrait checkpoints
# Assuming these are downloaded by FlashPortrait's own script or direct HF download
aria2c -x 16 -s 16 -o flashportrait_model.pth "https://huggingface.co/Francis-Ring/FlashPortrait/resolve/main/flashportrait_model.pth" -d "${COMFYUI_MODELS_DIR}/flashportrait" # Placeholder URL
# Wan2.1-14B-720P (as required by FlashPortrait)
aria2c -x 16 -s 16 -o Wan2.1-14B-720P.safetensors "https://huggingface.co/Wan-AI/Wan2.1-I2V-14B-720P/resolve/main/Wan2.1-14B-720P.safetensors" -d "${COMFYUI_MODELS_DIR}/flashportrait"

# MVInverse Models
echo "Downloading MVInverse models..."
mkdir -p "${COMFYUI_MODELS_DIR}/mvinverse"
# MVInverse uses inference checkpoints (e.g., from `--ckpt` arg). These would need to be located
# and downloaded here. Assuming a default checkpoint for now.
aria2c -x 16 -s 16 -o mvinverse_default.pth "https://huggingface.co/Maddog241/mvinverse/resolve/main/default_checkpoint.pth" -d "${COMFYUI_MODELS_DIR}/mvinverse" # Placeholder URL

# ... more models ...
```

---

## 6. Python Version and CUDA Compatibility Notes

-   **Base Image**: `runpod/pytorch:2.8.0-py3.11-cuda12.8.1` (Python 3.11, CUDA 12.8.1).
-   **Genfocus**: Requires Python 3.12, CUDA 12.x. `PyTorch 2.8.0` with `CUDA 12.8.1` *should* be compatible with Genfocus's underlying PyTorch requirements. The Python version difference (3.11 vs 3.12) needs careful testing. If conflicts arise, a dedicated `conda` environment or `pyenv` might be necessary, adding complexity. For this plan, we assume `3.11` is sufficient or that minor adjustments to the Genfocus source will make it compatible.
-   **MVInverse**: Compatible with PyTorch 2.5.1 (likely Python 3.10+), CUDA 11.8. `PyTorch 2.8.0` on `CUDA 12.8.1` is a newer version than specified. While PyTorch is often backward compatible, this needs testing. If not, a specific `pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu118` would be required, potentially clashing with the base environment or requiring a dedicated one.
-   **FlashPortrait**: Requires Python 3.8+, PyTorch 2.6.0, CUDA 12.4. Similar to MVInverse, `PyTorch 2.8.0` on `CUDA 12.8.1` is newer. Compatibility needs to be verified. A specific `pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.1.1 --index-url https://download.pytorch.org/whl/cu124` might be necessary if `2.8.0` is incompatible.

**Recommendation**: Proceed with the existing PyTorch/CUDA environment first and thoroughly test each custom node. If compatibility issues arise, then consider isolated `conda` environments for the problematic models, though this adds complexity to the Dockerfile and runtime management.
