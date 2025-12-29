"""
GenfocusPipeline convenience node for ComfyUI.

Combines DeblurNet + BokehNet in a single node for end-to-end
generative refocusing workflows.
"""

import logging
from typing import Dict, Any, Tuple, Optional

import torch

from .deblur import GenfocusDeblur
from .bokeh import GenfocusBokeh
from ..utils.tensor_utils import comfyui_to_pytorch, pytorch_to_comfyui

logger = logging.getLogger("ComfyUI-Genfocus")

# Custom types
GENFOCUS_DEBLUR_MODEL = "GENFOCUS_DEBLUR"
GENFOCUS_BOKEH_MODEL = "GENFOCUS_BOKEH"
DEPTH_MODEL = "DEPTH_MODEL"


class GenfocusPipeline:
    """
    All-in-one Genfocus refocusing pipeline.

    Combines DeblurNet + BokehNet for end-to-end refocusing in a single node.
    This is a convenience wrapper for simple workflows that don't need
    intermediate control between stages.

    Pipeline flow:
    1. DeblurNet: Input image -> All-in-focus (AIF) image
    2. BokehNet: AIF image -> Refocused image with synthetic DOF
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict:
        return {
            "required": {
                "image": ("IMAGE",),
                "deblur_model": (GENFOCUS_DEBLUR_MODEL,),
                "bokeh_model": (GENFOCUS_BOKEH_MODEL,),
                "deblur_steps": ("INT", {
                    "default": 30,
                    "min": 1,
                    "max": 100,
                    "step": 1
                }),
                "bokeh_steps": ("INT", {
                    "default": 30,
                    "min": 1,
                    "max": 100,
                    "step": 1
                }),
                "guidance_scale": ("FLOAT", {
                    "default": 7.5,
                    "min": 0.0,
                    "max": 20.0,
                    "step": 0.5
                }),
                "focus_distance": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "display": "slider"
                }),
                "bokeh_intensity": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "display": "slider"
                }),
                "aperture_shape": (["circle", "triangle", "heart", "star", "hexagon"], {
                    "default": "circle"
                }),
            },
            "optional": {
                "text_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Optional text conditioning for deblur stage"
                }),
                "depth_map": ("DEPTH_MAP", {
                    "tooltip": "Pre-computed depth map (optional)"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff
                }),
                "denoise_strength": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "display": "slider"
                }),
                "aperture_size": ("FLOAT", {
                    "default": 0.1,
                    "min": 0.01,
                    "max": 0.5,
                    "step": 0.01
                }),
                "skip_deblur": ("BOOLEAN", {
                    "default": False,
                    "label_on": "Skip DeblurNet",
                    "label_off": "Run DeblurNet",
                    "tooltip": "Skip deblur stage if input is already sharp"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "MASK")
    RETURN_NAMES = ("deblurred_image", "refocused_image", "focus_mask")
    FUNCTION = "refocus"
    CATEGORY = "image/genfocus"
    DESCRIPTION = "Complete Genfocus pipeline: Deblur -> Bokeh synthesis"

    def __init__(self):
        self._deblur_node = None
        self._bokeh_node = None

    def _get_deblur_node(self) -> GenfocusDeblur:
        """Lazy init deblur node."""
        if self._deblur_node is None:
            self._deblur_node = GenfocusDeblur()
        return self._deblur_node

    def _get_bokeh_node(self) -> GenfocusBokeh:
        """Lazy init bokeh node."""
        if self._bokeh_node is None:
            self._bokeh_node = GenfocusBokeh()
        return self._bokeh_node

    def refocus(
        self,
        image: torch.Tensor,
        deblur_model: Dict[str, Any],
        bokeh_model: Dict[str, Any],
        deblur_steps: int,
        bokeh_steps: int,
        guidance_scale: float,
        focus_distance: float,
        bokeh_intensity: float,
        aperture_shape: str,
        text_prompt: str = "",
        depth_map: Optional[torch.Tensor] = None,
        seed: int = 0,
        denoise_strength: float = 1.0,
        aperture_size: float = 0.1,
        skip_deblur: bool = False,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Run complete refocusing pipeline.

        Args:
            image: Input image (blurry or sharp)
            deblur_model: Loaded DeblurNet model
            bokeh_model: Loaded BokehNet model
            deblur_steps: Diffusion steps for deblur stage
            bokeh_steps: Diffusion steps for bokeh stage
            guidance_scale: CFG scale for both stages
            focus_distance: Where to focus (0=near, 1=far)
            bokeh_intensity: Strength of bokeh effect
            aperture_shape: Shape of bokeh highlights
            text_prompt: Optional text conditioning
            depth_map: Optional pre-computed depth
            seed: Random seed
            denoise_strength: Denoising strength for deblur
            aperture_size: Aperture size for DOF
            skip_deblur: Skip deblur if input is already sharp

        Returns:
            Tuple of (deblurred_image, refocused_image, focus_mask)
        """
        logger.info("Starting Genfocus pipeline...")

        # Stage 1: Deblur (optional)
        if skip_deblur:
            logger.info("Skipping deblur stage (skip_deblur=True)")
            deblurred = image
        else:
            logger.info(f"Stage 1: DeblurNet (steps={deblur_steps})")

            deblur_node = self._get_deblur_node()
            (deblurred,) = deblur_node.deblur(
                image=image,
                model=deblur_model,
                steps=deblur_steps,
                guidance_scale=guidance_scale,
                text_prompt=text_prompt,
                seed=seed,
                denoise_strength=denoise_strength,
            )

        # Stage 2: Bokeh synthesis
        logger.info(f"Stage 2: BokehNet (steps={bokeh_steps})")

        bokeh_node = self._get_bokeh_node()
        (refocused, focus_mask) = bokeh_node.apply_bokeh(
            image=deblurred,
            model=bokeh_model,
            steps=bokeh_steps,
            guidance_scale=guidance_scale,
            focus_distance=focus_distance,
            bokeh_intensity=bokeh_intensity,
            aperture_shape=aperture_shape,
            depth_map=depth_map,
            seed=seed,
            aperture_size=aperture_size,
        )

        logger.info("Genfocus pipeline complete")

        return (deblurred, refocused, focus_mask)


class GenfocusDepthEstimator:
    """
    Estimate depth map using auxiliary depth model.

    Uses depth_pro.pt or similar depth estimation network to
    generate depth maps for explicit depth control in bokeh synthesis.
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict:
        return {
            "required": {
                "image": ("IMAGE",),
                "depth_model": (DEPTH_MODEL,),
            },
            "optional": {
                "normalize": ("BOOLEAN", {
                    "default": True,
                    "label_on": "Normalize to [0,1]",
                    "label_off": "Raw depth values"
                }),
                "invert": ("BOOLEAN", {
                    "default": False,
                    "label_on": "Invert (near=1)",
                    "label_off": "Normal (near=0)"
                }),
            }
        }

    RETURN_TYPES = ("DEPTH_MAP", "IMAGE")
    RETURN_NAMES = ("depth_map", "depth_preview")
    FUNCTION = "estimate_depth"
    CATEGORY = "image/genfocus"
    DESCRIPTION = "Estimate depth map from image using Depth Pro model"

    def estimate_depth(
        self,
        image: torch.Tensor,
        depth_model: Dict[str, Any],
        normalize: bool = True,
        invert: bool = False,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Estimate depth map from input image.

        Args:
            image: Input image tensor (B, H, W, C)
            depth_model: Loaded depth estimation model
            normalize: Whether to normalize output to [0, 1]
            invert: Whether to invert depth (near=1 instead of near=0)

        Returns:
            Tuple of (depth_map, depth_preview)
        """
        logger.info("Estimating depth map...")

        device = depth_model.get("device", "cuda")

        # Convert to PyTorch format
        image_pt = comfyui_to_pytorch(image).to(device)

        # Check if we have a loaded model
        model = depth_model.get("_model")

        if model is not None:
            # Use actual depth model
            with torch.no_grad():
                depth = model(image_pt)
        else:
            # Fallback: gradient-based depth estimation
            logger.warning("Depth model not loaded, using gradient-based fallback")

            gray = image_pt.mean(dim=1, keepdim=True)

            # Sobel gradients
            sobel_x = torch.tensor(
                [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]],
                dtype=image_pt.dtype, device=device
            ).view(1, 1, 3, 3)
            sobel_y = torch.tensor(
                [[-1, -2, -1], [0, 0, 0], [1, 2, 1]],
                dtype=image_pt.dtype, device=device
            ).view(1, 1, 3, 3)

            grad_x = torch.nn.functional.conv2d(gray, sobel_x, padding=1)
            grad_y = torch.nn.functional.conv2d(gray, sobel_y, padding=1)

            depth = torch.sqrt(grad_x ** 2 + grad_y ** 2)

            # Smooth
            depth = torch.nn.functional.avg_pool2d(depth, 8, stride=1, padding=4)

        # Normalize if requested
        if normalize:
            d_min, d_max = depth.min(), depth.max()
            if d_max - d_min > 0:
                depth = (depth - d_min) / (d_max - d_min)

        # Invert if requested
        if invert:
            depth = 1.0 - depth

        # Create grayscale preview for visualization
        depth_preview = depth.repeat(1, 3, 1, 1)  # (B, 3, H, W)
        depth_preview = pytorch_to_comfyui(depth_preview)

        # Depth map output (keep as single channel)
        depth_map = depth.squeeze(1)  # (B, H, W)

        logger.info(f"Depth estimation complete: shape {depth_map.shape}")

        return (depth_map.cpu(), depth_preview)
