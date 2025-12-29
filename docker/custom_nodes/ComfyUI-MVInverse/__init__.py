"""
ComfyUI-MVInverse
Custom nodes for MVInverse multi-view inverse rendering.

Nodes:
- MVInverseLoader: Load MVInverse model from checkpoint or HF Hub
- MVInverseInverse: Execute inverse rendering on multi-view images

Author: oz
Model: claude-opus-4-5
Date: 2025-12-29
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

WEB_DIRECTORY = None
