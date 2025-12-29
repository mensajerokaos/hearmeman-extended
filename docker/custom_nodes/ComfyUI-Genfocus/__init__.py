"""
ComfyUI-Genfocus: Generative Refocusing Custom Nodes

A ComfyUI wrapper for the Genfocus framework, enabling:
- DeblurNet: Recover all-in-focus images from blurry input
- BokehNet: Synthesize photorealistic depth-of-field effects

Based on: https://github.com/rayray9999/Genfocus
Paper: "Generative Refocusing: Flexible Defocus Control from a Single Image"

Model downloads: https://huggingface.co/nycu-cplab/Genfocus-Model
"""

import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ComfyUI-Genfocus")

# Import nodes
from .nodes.loaders import (
    GenfocusDeblurNetLoader,
    GenfocusBokehNetLoader,
    GenfocusDepthLoader,
    clear_model_cache,
)
from .nodes.deblur import GenfocusDeblur
from .nodes.bokeh import GenfocusBokeh
from .nodes.pipeline import GenfocusPipeline, GenfocusDepthEstimator

# Node class mappings for ComfyUI registration
NODE_CLASS_MAPPINGS = {
    # Loaders
    "GenfocusDeblurNetLoader": GenfocusDeblurNetLoader,
    "GenfocusBokehNetLoader": GenfocusBokehNetLoader,
    "GenfocusDepthLoader": GenfocusDepthLoader,

    # Processing nodes
    "GenfocusDeblur": GenfocusDeblur,
    "GenfocusBokeh": GenfocusBokeh,

    # Pipeline / utility nodes
    "GenfocusPipeline": GenfocusPipeline,
    "GenfocusDepthEstimator": GenfocusDepthEstimator,
}

# Display names for ComfyUI UI
NODE_DISPLAY_NAME_MAPPINGS = {
    # Loaders
    "GenfocusDeblurNetLoader": "Genfocus DeblurNet Loader",
    "GenfocusBokehNetLoader": "Genfocus BokehNet Loader",
    "GenfocusDepthLoader": "Genfocus Depth Loader",

    # Processing nodes
    "GenfocusDeblur": "Genfocus Deblur",
    "GenfocusBokeh": "Genfocus Bokeh",

    # Pipeline / utility nodes
    "GenfocusPipeline": "Genfocus Pipeline (All-in-One)",
    "GenfocusDepthEstimator": "Genfocus Depth Estimator",
}

# Web directory for custom UI elements (if any)
WEB_DIRECTORY = "./web"

# Version info
__version__ = "0.1.0"
__author__ = "ComfyUI-Genfocus Contributors"

# Exported symbols
__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
    # Loaders
    "GenfocusDeblurNetLoader",
    "GenfocusBokehNetLoader",
    "GenfocusDepthLoader",
    # Processing
    "GenfocusDeblur",
    "GenfocusBokeh",
    # Pipeline
    "GenfocusPipeline",
    "GenfocusDepthEstimator",
    # Utilities
    "clear_model_cache",
]

# Log successful initialization
logger.info(f"ComfyUI-Genfocus v{__version__} loaded successfully")
logger.info(f"Registered {len(NODE_CLASS_MAPPINGS)} nodes")

# Create models directory if it doesn't exist
models_dir = os.path.join(os.path.dirname(__file__), "models")
if not os.path.exists(models_dir):
    os.makedirs(models_dir, exist_ok=True)
    logger.info(f"Created models directory: {models_dir}")
