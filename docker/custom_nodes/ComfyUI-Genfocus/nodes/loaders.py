"""
Model loader nodes for ComfyUI-Genfocus.

Handles loading and caching of DeblurNet, BokehNet, and Depth models.
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple

import torch
from safetensors.torch import load_file

import folder_paths

# Setup logging
logger = logging.getLogger("ComfyUI-Genfocus")

# Custom type identifiers
GENFOCUS_DEBLUR_MODEL = "GENFOCUS_DEBLUR"
GENFOCUS_BOKEH_MODEL = "GENFOCUS_BOKEH"
DEPTH_MODEL = "DEPTH_MODEL"

# Model cache for lazy loading and memory efficiency
_MODEL_CACHE: Dict[str, Any] = {}


def get_model_path(filename: str) -> str:
    """
    Resolve model path from filename.

    Searches in order:
    1. Absolute path
    2. ComfyUI models/genfocus directory
    3. Custom nodes directory
    """
    # If absolute path, use directly
    if os.path.isabs(filename) and os.path.exists(filename):
        return filename

    # Check ComfyUI model paths
    genfocus_dir = os.path.join(folder_paths.models_dir, "genfocus")
    if os.path.exists(os.path.join(genfocus_dir, filename)):
        return os.path.join(genfocus_dir, filename)

    # Check in custom_nodes directory
    custom_nodes_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_path = os.path.join(custom_nodes_dir, "models", filename)
    if os.path.exists(models_path):
        return models_path

    # Return filename for error reporting
    return filename


def list_genfocus_models() -> list:
    """List available Genfocus model files."""
    models = []
    genfocus_dir = os.path.join(folder_paths.models_dir, "genfocus")

    if os.path.exists(genfocus_dir):
        for f in os.listdir(genfocus_dir):
            if f.endswith((".safetensors", ".pt", ".pth", ".bin")):
                models.append(f)

    return models if models else ["deblurNet.safetensors", "bokehNet.safetensors"]


def get_cache_key(model_path: str, dtype: str, device: str) -> str:
    """Generate unique cache key for model configuration."""
    return f"{model_path}_{dtype}_{device}"


def clear_model_cache():
    """Clear all cached models to free memory."""
    global _MODEL_CACHE
    _MODEL_CACHE.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info("Model cache cleared")


class GenfocusDeblurNetLoader:
    """
    Load Genfocus DeblurNet model with FLUX backbone.

    DeblurNet uses a FLUX.1-DEV backbone with LoRA (rank r=128) for
    diffusion-based image deblurring to recover all-in-focus images.
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict:
        return {
            "required": {
                "model_path": (list_genfocus_models(), {
                    "default": "deblurNet.safetensors"
                }),
                "dtype": (["auto", "float32", "float16", "bfloat16"], {
                    "default": "auto"
                }),
                "device": (["cuda", "cpu"], {
                    "default": "cuda"
                }),
            },
            "optional": {
                "offload_to_cpu": ("BOOLEAN", {
                    "default": False,
                    "label_on": "Offload when idle",
                    "label_off": "Keep on GPU"
                }),
            }
        }

    RETURN_TYPES = (GENFOCUS_DEBLUR_MODEL,)
    RETURN_NAMES = ("deblur_model",)
    FUNCTION = "load_model"
    CATEGORY = "loaders/genfocus"
    DESCRIPTION = "Load Genfocus DeblurNet for image deblurring"

    def load_model(
        self,
        model_path: str,
        dtype: str,
        device: str,
        offload_to_cpu: bool = False
    ) -> Tuple[Dict[str, Any]]:
        """
        Load DeblurNet model from safetensors file.

        Args:
            model_path: Path to deblurNet.safetensors
            dtype: Data type for model (auto-detect or explicit)
            device: CPU or CUDA device
            offload_to_cpu: Whether to offload model to CPU when not in use

        Returns:
            Loaded model wrapper dict
        """
        # Resolve actual path
        full_path = get_model_path(model_path)

        # Check cache first
        cache_key = get_cache_key(full_path, dtype, device)
        if cache_key in _MODEL_CACHE:
            logger.info(f"Using cached DeblurNet model: {cache_key}")
            return (_MODEL_CACHE[cache_key],)

        # Validate file exists
        if not os.path.exists(full_path):
            raise FileNotFoundError(
                f"DeblurNet model not found at: {full_path}\n"
                f"Please download from: https://huggingface.co/nycu-cplab/Genfocus-Model"
            )

        logger.info(f"Loading DeblurNet from: {full_path}")

        # Determine dtype
        if dtype == "auto":
            model_dtype = torch.float16 if device == "cuda" else torch.float32
        else:
            dtype_map = {
                "float32": torch.float32,
                "float16": torch.float16,
                "bfloat16": torch.bfloat16
            }
            model_dtype = dtype_map[dtype]

        # Load state dict
        try:
            state_dict = load_file(full_path)
        except Exception as e:
            logger.error(f"Failed to load safetensors: {e}")
            # Try torch.load as fallback
            state_dict = torch.load(full_path, map_location="cpu")

        # Create model wrapper with metadata
        model_wrapper = {
            "type": "deblur",
            "state_dict": state_dict,
            "dtype": model_dtype,
            "device": device,
            "offload_to_cpu": offload_to_cpu,
            "model_path": full_path,
            "lora_rank": 128,  # DeblurNet uses r=128 LoRA
            # Lazy-loaded components
            "_pipeline": None,
            "_is_loaded": False,
        }

        # Cache the model wrapper
        _MODEL_CACHE[cache_key] = model_wrapper
        logger.info(f"DeblurNet loaded successfully (dtype={model_dtype}, device={device})")

        return (model_wrapper,)


class GenfocusBokehNetLoader:
    """
    Load Genfocus BokehNet model with FLUX backbone.

    BokehNet uses a FLUX.1-DEV backbone with LoRA (rank r=64) for
    diffusion-based bokeh synthesis with controllable depth-of-field.
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict:
        return {
            "required": {
                "model_path": (list_genfocus_models(), {
                    "default": "bokehNet.safetensors"
                }),
                "dtype": (["auto", "float32", "float16", "bfloat16"], {
                    "default": "auto"
                }),
                "device": (["cuda", "cpu"], {
                    "default": "cuda"
                }),
            },
            "optional": {
                "offload_to_cpu": ("BOOLEAN", {
                    "default": False,
                    "label_on": "Offload when idle",
                    "label_off": "Keep on GPU"
                }),
            }
        }

    RETURN_TYPES = (GENFOCUS_BOKEH_MODEL,)
    RETURN_NAMES = ("bokeh_model",)
    FUNCTION = "load_model"
    CATEGORY = "loaders/genfocus"
    DESCRIPTION = "Load Genfocus BokehNet for bokeh synthesis"

    def load_model(
        self,
        model_path: str,
        dtype: str,
        device: str,
        offload_to_cpu: bool = False
    ) -> Tuple[Dict[str, Any]]:
        """
        Load BokehNet model from safetensors file.

        Args:
            model_path: Path to bokehNet.safetensors
            dtype: Data type for model
            device: CPU or CUDA device
            offload_to_cpu: Whether to offload model to CPU when not in use

        Returns:
            Loaded model wrapper dict
        """
        # Resolve actual path
        full_path = get_model_path(model_path)

        # Check cache
        cache_key = get_cache_key(full_path, dtype, device)
        if cache_key in _MODEL_CACHE:
            logger.info(f"Using cached BokehNet model: {cache_key}")
            return (_MODEL_CACHE[cache_key],)

        # Validate file exists
        if not os.path.exists(full_path):
            raise FileNotFoundError(
                f"BokehNet model not found at: {full_path}\n"
                f"Please download from: https://huggingface.co/nycu-cplab/Genfocus-Model"
            )

        logger.info(f"Loading BokehNet from: {full_path}")

        # Determine dtype
        if dtype == "auto":
            model_dtype = torch.float16 if device == "cuda" else torch.float32
        else:
            dtype_map = {
                "float32": torch.float32,
                "float16": torch.float16,
                "bfloat16": torch.bfloat16
            }
            model_dtype = dtype_map[dtype]

        # Load state dict
        try:
            state_dict = load_file(full_path)
        except Exception as e:
            logger.error(f"Failed to load safetensors: {e}")
            state_dict = torch.load(full_path, map_location="cpu")

        # Create model wrapper
        model_wrapper = {
            "type": "bokeh",
            "state_dict": state_dict,
            "dtype": model_dtype,
            "device": device,
            "offload_to_cpu": offload_to_cpu,
            "model_path": full_path,
            "lora_rank": 64,  # BokehNet uses r=64 LoRA
            # Lazy-loaded components
            "_pipeline": None,
            "_is_loaded": False,
        }

        # Cache
        _MODEL_CACHE[cache_key] = model_wrapper
        logger.info(f"BokehNet loaded successfully (dtype={model_dtype}, device={device})")

        return (model_wrapper,)


class GenfocusDepthLoader:
    """
    Load auxiliary depth estimation model (depth_pro.pt).

    Uses Apple's Depth Pro for high-quality monocular depth estimation,
    providing depth maps for bokeh synthesis.
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict:
        return {
            "required": {
                "model_path": ("STRING", {
                    "default": "checkpoints/depth_pro.pt",
                    "multiline": False
                }),
                "device": (["cuda", "cpu"], {
                    "default": "cuda"
                }),
            }
        }

    RETURN_TYPES = (DEPTH_MODEL,)
    RETURN_NAMES = ("depth_model",)
    FUNCTION = "load_model"
    CATEGORY = "loaders/genfocus"
    DESCRIPTION = "Load Depth Pro model for depth estimation"

    def load_model(
        self,
        model_path: str,
        device: str
    ) -> Tuple[Dict[str, Any]]:
        """
        Load depth estimation model.

        Args:
            model_path: Path to depth_pro.pt
            device: CPU or CUDA device

        Returns:
            Loaded depth model wrapper
        """
        # Resolve path
        full_path = get_model_path(model_path)

        # Check cache
        cache_key = get_cache_key(full_path, "float32", device)
        if cache_key in _MODEL_CACHE:
            logger.info(f"Using cached Depth model: {cache_key}")
            return (_MODEL_CACHE[cache_key],)

        # Validate
        if not os.path.exists(full_path):
            raise FileNotFoundError(
                f"Depth model not found at: {full_path}\n"
                f"Please download from: https://huggingface.co/nycu-cplab/Genfocus-Model"
            )

        logger.info(f"Loading Depth model from: {full_path}")

        # Load checkpoint
        checkpoint = torch.load(full_path, map_location="cpu")

        # Create wrapper
        model_wrapper = {
            "type": "depth",
            "state_dict": checkpoint.get("state_dict", checkpoint),
            "device": device,
            "model_path": full_path,
            "_model": None,
            "_is_loaded": False,
        }

        # Cache
        _MODEL_CACHE[cache_key] = model_wrapper
        logger.info(f"Depth model loaded successfully (device={device})")

        return (model_wrapper,)
