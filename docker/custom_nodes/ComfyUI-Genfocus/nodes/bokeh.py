"""
GenfocusBokeh node for ComfyUI.

Applies BokehNet diffusion model to synthesize photorealistic
depth-of-field effects with controllable parameters.
"""

import logging
from typing import Dict, Any, Tuple, Optional

import torch
import numpy as np

from ..utils.tensor_utils import (
    comfyui_to_pytorch,
    pytorch_to_comfyui,
    ensure_batch_dim,
    get_dtype,
    create_focus_mask,
)

logger = logging.getLogger("ComfyUI-Genfocus")

# Custom types
GENFOCUS_BOKEH_MODEL = "GENFOCUS_BOKEH"
DEPTH_MAP = "DEPTH_MAP"


# Aperture shape kernels for bokeh highlights
APERTURE_SHAPES = {
    "circle": "circular",
    "triangle": "triangular",
    "heart": "heart",
    "star": "star",
    "hexagon": "hexagonal",
}


class GenfocusBokeh:
    """
    Apply BokehNet bokeh synthesis to image.

    This node uses a FLUX-based diffusion model trained for synthesizing
    photorealistic depth-of-field effects. It can create various bokeh
    shapes and intensities based on depth information.
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict:
        return {
            "required": {
                "image": ("IMAGE",),
                "model": (GENFOCUS_BOKEH_MODEL,),
                "steps": ("INT", {
                    "default": 30,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "display": "number"
                }),
                "guidance_scale": ("FLOAT", {
                    "default": 7.5,
                    "min": 0.0,
                    "max": 20.0,
                    "step": 0.5,
                    "display": "number"
                }),
                "focus_distance": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "display": "slider",
                    "tooltip": "Focus plane distance (0=near, 1=far)"
                }),
                "bokeh_intensity": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "display": "slider",
                    "tooltip": "Strength of bokeh effect (0=none, 1=maximum)"
                }),
                "aperture_shape": (list(APERTURE_SHAPES.keys()), {
                    "default": "circle"
                }),
            },
            "optional": {
                "depth_map": (DEPTH_MAP, {
                    "tooltip": "Pre-computed depth map (optional, auto-estimated if not provided)"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "step": 1
                }),
                "aperture_size": ("FLOAT", {
                    "default": 0.1,
                    "min": 0.01,
                    "max": 0.5,
                    "step": 0.01,
                    "display": "slider",
                    "tooltip": "Aperture size (smaller = larger DOF)"
                }),
                "focus_falloff": ("FLOAT", {
                    "default": 2.0,
                    "min": 0.5,
                    "max": 10.0,
                    "step": 0.5,
                    "tooltip": "How quickly blur increases away from focus plane"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("bokeh_image", "focus_mask")
    FUNCTION = "apply_bokeh"
    CATEGORY = "image/genfocus"
    DESCRIPTION = "Apply BokehNet to synthesize depth-of-field bokeh effects"

    def __init__(self):
        self._pipeline = None
        self._depth_estimator = None

    def _ensure_pipeline(self, model: Dict[str, Any]) -> Any:
        """Lazily initialize the BokehNet diffusion pipeline."""
        if model.get("_pipeline") is not None:
            return model["_pipeline"]

        logger.info("Initializing BokehNet diffusion pipeline...")

        try:
            from diffusers import FluxPipeline, DDIMScheduler
            from peft import PeftModel

            device = model["device"]
            dtype = model["dtype"]

            # Load base FLUX.1-dev pipeline
            pipe = FluxPipeline.from_pretrained(
                "black-forest-labs/FLUX.1-dev",
                torch_dtype=dtype,
            )

            # Load LoRA weights
            state_dict = model["state_dict"]
            lora_state_dict = {
                k: v for k, v in state_dict.items()
                if "lora" in k.lower() or "adapter" in k.lower()
            }

            if lora_state_dict:
                pipe.transformer.load_state_dict(lora_state_dict, strict=False)
                logger.info(f"Loaded {len(lora_state_dict)} BokehNet LoRA parameters")

            # Configure scheduler
            pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)

            # Handle device placement
            if model.get("offload_to_cpu"):
                pipe.enable_model_cpu_offload()
            else:
                pipe = pipe.to(device)

            model["_pipeline"] = pipe
            model["_is_loaded"] = True

            return pipe

        except Exception as e:
            logger.error(f"BokehNet pipeline init failed: {e}")
            raise

    def _estimate_depth(
        self,
        image_tensor: torch.Tensor,
        device: str
    ) -> torch.Tensor:
        """
        Estimate depth map using simple gradient-based heuristic.

        This is a fallback when no depth model is provided.
        For production, use GenfocusDepthLoader with depth_pro.pt
        """
        # Simple depth estimation based on image gradients
        # Higher frequency = closer (sharper details)
        # This is a rough approximation

        gray = image_tensor.mean(dim=1, keepdim=True)  # (B, 1, H, W)

        # Compute gradients
        sobel_x = torch.tensor([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]],
                               dtype=image_tensor.dtype, device=device)
        sobel_y = torch.tensor([[-1, -2, -1], [0, 0, 0], [1, 2, 1]],
                               dtype=image_tensor.dtype, device=device)

        sobel_x = sobel_x.view(1, 1, 3, 3)
        sobel_y = sobel_y.view(1, 1, 3, 3)

        grad_x = torch.nn.functional.conv2d(gray, sobel_x, padding=1)
        grad_y = torch.nn.functional.conv2d(gray, sobel_y, padding=1)

        # Gradient magnitude
        gradient_mag = torch.sqrt(grad_x ** 2 + grad_y ** 2)

        # Smooth and normalize
        depth = torch.nn.functional.avg_pool2d(gradient_mag, 16, stride=1, padding=8)

        # Normalize to [0, 1]
        d_min, d_max = depth.min(), depth.max()
        if d_max - d_min > 0:
            depth = (depth - d_min) / (d_max - d_min)
        else:
            depth = torch.zeros_like(depth) + 0.5

        return depth

    def _apply_bokeh_blur(
        self,
        image: torch.Tensor,
        depth_map: torch.Tensor,
        focus_distance: float,
        bokeh_intensity: float,
        aperture_size: float,
        focus_falloff: float,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Apply depth-aware bokeh blur to image.

        Uses the depth map to compute per-pixel blur amounts
        based on distance from the focus plane.
        """
        device = image.device
        dtype = image.dtype
        B, C, H, W = image.shape

        # Compute circle of confusion based on depth
        coc = torch.abs(depth_map - focus_distance)
        coc = coc ** (1.0 / focus_falloff)  # Apply falloff curve

        # Scale by aperture and intensity
        blur_amount = coc * bokeh_intensity * aperture_size * 50

        # Ensure blur_amount matches image dimensions (depth estimation can produce different sizes)
        if blur_amount.shape[-2:] != (H, W):
            blur_amount = torch.nn.functional.interpolate(
                blur_amount, size=(H, W), mode='bilinear', align_corners=False
            )

        # Create focus mask (1 = in focus, 0 = blurred)
        focus_mask = 1.0 - torch.clamp(blur_amount, 0, 1)

        # Multi-scale blur approximation
        blurred = image.clone()

        for scale in [2, 4, 8, 16]:
            # Gaussian-like blur via average pooling
            kernel_size = scale * 2 + 1
            padding = scale

            # Apply blur
            blur_layer = torch.nn.functional.avg_pool2d(
                image, kernel_size, stride=1, padding=padding
            )

            # Ensure same size
            if blur_layer.shape[-2:] != image.shape[-2:]:
                blur_layer = torch.nn.functional.interpolate(
                    blur_layer, size=(H, W), mode='bilinear', align_corners=False
                )

            # Blend based on blur amount for this scale
            scale_threshold = scale / 20.0
            scale_mask = (blur_amount > scale_threshold).float()
            scale_mask = scale_mask.expand_as(image)

            blurred = blurred * (1 - scale_mask * 0.3) + blur_layer * scale_mask * 0.3

        # Final blend with original based on focus mask
        focus_mask_expanded = focus_mask.expand_as(image)
        output = image * focus_mask_expanded + blurred * (1 - focus_mask_expanded)

        return output, focus_mask.squeeze(1)

    def _run_diffusion_bokeh(
        self,
        pipeline: Any,
        image_tensor: torch.Tensor,
        depth_map: torch.Tensor,
        model: Dict[str, Any],
        steps: int,
        guidance_scale: float,
        focus_distance: float,
        bokeh_intensity: float,
        aperture_shape: str,
        seed: int,
    ) -> torch.Tensor:
        """
        Run diffusion-based bokeh synthesis.

        When full pipeline is available, uses it for high-quality
        neural bokeh synthesis. Otherwise falls back to traditional
        depth-aware blur.
        """
        device = model["device"]
        dtype = model["dtype"]

        generator = torch.Generator(device=device).manual_seed(seed)

        if pipeline is not None and hasattr(pipeline, '__call__'):
            try:
                # Prepare conditioning prompt with bokeh parameters
                prompt = (
                    f"shallow depth of field, {aperture_shape} bokeh, "
                    f"focus distance {focus_distance:.2f}, "
                    f"blur intensity {bokeh_intensity:.2f}, "
                    f"professional photography"
                )

                # Prepare image input
                image_input = image_tensor.to(device=device, dtype=dtype)
                image_input = image_input * 2.0 - 1.0  # Scale to [-1, 1]

                # Run pipeline with depth conditioning
                output = pipeline(
                    prompt=prompt,
                    image=image_input,
                    num_inference_steps=steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                    # Note: depth conditioning integration depends on
                    # specific pipeline implementation
                ).images[0]

                # Convert output
                output_np = np.array(output).astype(np.float32) / 255.0
                output_tensor = torch.from_numpy(output_np)
                output_tensor = output_tensor.unsqueeze(0).permute(0, 3, 1, 2)

                return output_tensor

            except Exception as e:
                logger.warning(f"Diffusion bokeh failed, using fallback: {e}")

        # Fallback: traditional depth-aware blur
        return None

    def apply_bokeh(
        self,
        image: torch.Tensor,
        model: Dict[str, Any],
        steps: int,
        guidance_scale: float,
        focus_distance: float,
        bokeh_intensity: float,
        aperture_shape: str,
        depth_map: Optional[torch.Tensor] = None,
        seed: int = 0,
        aperture_size: float = 0.1,
        focus_falloff: float = 2.0,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Apply BokehNet bokeh synthesis with controllable parameters.

        Args:
            image: Input image (typically all-in-focus from DeblurNet)
            model: Loaded BokehNet model
            steps: Number of diffusion steps
            guidance_scale: Classifier-free guidance scale
            focus_distance: Where to focus (0=near, 1=far)
            bokeh_intensity: Strength of bokeh effect (0-1)
            aperture_shape: Shape of bokeh highlights
            depth_map: Optional pre-computed depth map
            seed: Random seed
            aperture_size: Aperture size controlling DOF
            focus_falloff: How quickly blur increases away from focus

        Returns:
            Tuple of (bokeh_image, focus_mask)
        """
        # Validate model type
        if model.get("type") != "bokeh":
            raise ValueError(
                f"Expected BokehNet model, got: {model.get('type', 'unknown')}"
            )

        logger.info(
            f"Running BokehNet: steps={steps}, focus={focus_distance}, "
            f"intensity={bokeh_intensity}, shape={aperture_shape}"
        )

        device = model["device"]

        # Convert to PyTorch format
        image_pt = comfyui_to_pytorch(image).to(device)

        # Estimate or use provided depth map
        if depth_map is None:
            logger.info("No depth map provided, estimating from image")
            depth_pt = self._estimate_depth(image_pt, device)
        else:
            # Convert depth map to proper format
            if depth_map.ndim == 3:
                depth_pt = depth_map.unsqueeze(0).unsqueeze(0)
            elif depth_map.ndim == 4:
                depth_pt = depth_map
            else:
                depth_pt = depth_map.unsqueeze(0)

            depth_pt = depth_pt.to(device)

            # Ensure same spatial size as image
            if depth_pt.shape[-2:] != image_pt.shape[-2:]:
                depth_pt = torch.nn.functional.interpolate(
                    depth_pt, size=image_pt.shape[-2:],
                    mode='bilinear', align_corners=False
                )

        # Try diffusion-based bokeh first
        pipeline = None
        try:
            pipeline = self._ensure_pipeline(model)
        except Exception as e:
            logger.warning(f"Could not load BokehNet pipeline: {e}")

        output_pt = self._run_diffusion_bokeh(
            pipeline=pipeline,
            image_tensor=image_pt,
            depth_map=depth_pt,
            model=model,
            steps=steps,
            guidance_scale=guidance_scale,
            focus_distance=focus_distance,
            bokeh_intensity=bokeh_intensity,
            aperture_shape=aperture_shape,
            seed=seed,
        )

        # If diffusion failed, use traditional blur
        if output_pt is None:
            logger.info("Using traditional depth-aware bokeh blur")
            output_pt, focus_mask = self._apply_bokeh_blur(
                image=image_pt,
                depth_map=depth_pt,
                focus_distance=focus_distance,
                bokeh_intensity=bokeh_intensity,
                aperture_size=aperture_size,
                focus_falloff=focus_falloff,
            )
        else:
            # Create focus mask from depth for output
            focus_mask = create_focus_mask(depth_pt, focus_distance, aperture_size)
            focus_mask = focus_mask.squeeze(1)

        # Convert back to ComfyUI format
        output = pytorch_to_comfyui(output_pt)

        # Ensure focus mask is proper format for MASK output
        if focus_mask.ndim == 4:
            focus_mask = focus_mask.squeeze(1)
        if focus_mask.ndim == 2:
            focus_mask = focus_mask.unsqueeze(0)

        focus_mask = focus_mask.cpu()

        logger.info(f"BokehNet complete: output shape {output.shape}")

        return (output, focus_mask)
