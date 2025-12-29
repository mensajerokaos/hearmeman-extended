"""
MVInverse Inverse Rendering Node for ComfyUI.

Executes multi-view inverse rendering to extract material properties:
albedo, normal, metallic, roughness, and shading maps.

Author: oz
Model: claude-opus-4-5
Date: 2025-12-29
"""

import torch
import torch.nn.functional as F


class MVInverseInverse:
    """
    Execute multi-view inverse rendering.

    Takes a batch of multi-view images and produces material property maps
    for each view using the MVInverse model.

    Input Format:
        images: [B, H, W, C] where B = number of views, C = 3 or 4 channels

    Output Format:
        All outputs are [B, H, W, C] in ComfyUI format (float32, range [0, 1])
        - albedo: [B, H, W, 3] - Base color/diffuse
        - normal: [B, H, W, 3] - Surface normals (remapped from [-1,1] to [0,1])
        - metallic: [B, H, W, 1] - Metallic property
        - roughness: [B, H, W, 1] - Surface roughness
        - shading: [B, H, W, 3] - Computed shading
    """

    @classmethod
    def INPUT_TYPES(cls):
        """Define input parameters for the node."""
        return {
            "required": {
                "images": ("IMAGE",),
                "mvinverse_model": ("MVINVERSE_MODEL",),
                "max_size": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 224,
                        "max": 2048,
                        "step": 14,  # Align to patch size
                        "display": "slider"
                    }
                ),
            },
            "optional": {
                "upscale_output": (
                    ["disabled", "bilinear", "nearest"],
                    {"default": "disabled"}
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("albedo", "normal", "metallic", "roughness", "shading")
    FUNCTION = "inverse_render"
    CATEGORY = "image/material"
    DESCRIPTION = "Extract material properties from multi-view images using MVInverse"

    def inverse_render(
        self,
        images,
        mvinverse_model,
        max_size,
        upscale_output="disabled"
    ):
        """
        Execute inverse rendering on multi-view images.

        Args:
            images: Input tensor [B, H, W, C] where B = number of views
            mvinverse_model: Loaded MVInverse model
            max_size: Maximum dimension for processing (aligned to patch size 14)
            upscale_output: Whether to upscale outputs to original size

        Returns:
            Tuple of (albedo, normal, metallic, roughness, shading) tensors
        """
        # Get model device and dtype
        device = next(mvinverse_model.parameters()).device
        dtype = next(mvinverse_model.parameters()).dtype

        B, H, W, C = images.shape
        print(f"[MVInverse] Input: {B} views, {H}x{W}, {C} channels")

        # Step 1: Validate input
        if B < 1:
            raise ValueError("[MVInverse] At least 1 view required")

        if B > 16:
            print(f"[MVInverse] Warning: {B} views may cause memory issues. Consider using fewer views.")

        # Step 2: Prepare images for MVInverse
        prepared, original_size, processed_size = self._prepare_images(
            images, max_size, device, dtype
        )

        print(f"[MVInverse] Processing at {processed_size[0]}x{processed_size[1]}")

        # Step 3: Run inference with memory optimization
        with torch.no_grad():
            if dtype == torch.float16 and device.type == 'cuda':
                with torch.amp.autocast('cuda', dtype=torch.float16):
                    outputs = mvinverse_model(prepared)
            else:
                outputs = mvinverse_model(prepared)

        # Step 4: Process outputs to ComfyUI format
        result = self._process_outputs(
            outputs,
            original_size,
            upscale_output
        )

        # Clear CUDA cache if needed
        if device.type == 'cuda':
            torch.cuda.empty_cache()

        print(f"[MVInverse] Output shapes: albedo={result['albedo'].shape}, "
              f"normal={result['normal'].shape}")

        return (
            result['albedo'],
            result['normal'],
            result['metallic'],
            result['roughness'],
            result['shading']
        )

    @staticmethod
    def _prepare_images(images_batch, max_size, device, dtype):
        """
        Convert ComfyUI image batch to MVInverse format.

        Converts from [B, H, W, C] (ComfyUI) to [1, B, 3, H, W] (MVInverse).
        Handles resizing and patch size alignment.

        Args:
            images_batch: Input tensor [B, H, W, C]
            max_size: Maximum longest dimension
            device: Target device
            dtype: Target dtype

        Returns:
            Tuple of (prepared_tensor, original_size, processed_size)
        """
        B, H, W, C = images_batch.shape
        original_size = (H, W)

        # Convert to [B, C, H, W] (channels first)
        images = images_batch.permute(0, 3, 1, 2)

        # Handle channel count
        if C == 4:
            # Drop alpha channel
            images = images[:, :3, :, :]
        elif C == 1:
            # Expand grayscale to RGB
            images = images.repeat(1, 3, 1, 1)
        elif C != 3:
            raise ValueError(f"[MVInverse] Unsupported channel count: {C}")

        # Calculate new size while maintaining aspect ratio
        scale = min(max_size / max(H, W), 1.0)
        new_h = int(H * scale)
        new_w = int(W * scale)

        # Align to patch size (14) - this is CRITICAL for MVInverse
        patch_size = 14
        new_h = max((new_h // patch_size) * patch_size, patch_size)
        new_w = max((new_w // patch_size) * patch_size, patch_size)

        # Resize if needed
        if (new_h, new_w) != (H, W):
            images = F.interpolate(
                images,
                size=(new_h, new_w),
                mode='bilinear',
                align_corners=False,
                antialias=True
            )

        processed_size = (new_h, new_w)

        # Add batch dimension: [B, C, H, W] -> [1, B, C, H, W]
        # MVInverse expects (batch=1, num_views=B, channels=3, H, W)
        images = images.unsqueeze(0)

        # Move to device and dtype
        images = images.to(device=device, dtype=dtype)

        return images, original_size, processed_size

    @staticmethod
    def _process_outputs(outputs, original_size, upscale_mode):
        """
        Convert MVInverse outputs to ComfyUI format.

        Handles normalization of different output types and optional
        upscaling back to original resolution.

        MVInverse output ranges:
            - albedo: [0, 255]
            - normal: [-1, 1]
            - metallic: [0, 255]
            - roughness: [0, 255]
            - shading: [0, 255]

        ComfyUI expected format:
            - All: [B, H, W, C], float32, range [0, 1]

        Args:
            outputs: Dict with keys {albedo, normal, metallic, roughness, shading}
            original_size: Tuple (H, W) of original input size
            upscale_mode: "disabled", "bilinear", or "nearest"

        Returns:
            Dict of tensors in ComfyUI format
        """
        result = {}
        H, W = original_size

        output_keys = ['albedo', 'normal', 'metallic', 'roughness', 'shading']

        for key in output_keys:
            if key not in outputs:
                raise KeyError(f"[MVInverse] Expected output '{key}' not found in model outputs")

            tensor = outputs[key]  # Expected shape: [N, H, W, C] from model

            # Handle different tensor formats from model
            if tensor.dim() == 5:
                # [1, N, H, W, C] -> [N, H, W, C]
                tensor = tensor.squeeze(0)
            elif tensor.dim() == 3:
                # [N, H, W] -> [N, H, W, 1] (for metallic/roughness)
                tensor = tensor.unsqueeze(-1)

            # Normalize based on output type
            if key == 'normal':
                # Normal maps are in [-1, 1], remap to [0, 1] for visualization
                tensor = tensor * 0.5 + 0.5
            else:
                # All others are in [0, 255], normalize to [0, 1]
                if tensor.max() > 1.0:
                    tensor = tensor / 255.0

            # Clamp to valid range
            tensor = torch.clamp(tensor, 0.0, 1.0)

            # Ensure float32 for ComfyUI compatibility
            tensor = tensor.to(torch.float32)

            # Move to CPU for ComfyUI
            tensor = tensor.cpu()

            # Optional upscaling back to original size
            if upscale_mode != "disabled":
                current_h, current_w = tensor.shape[1], tensor.shape[2]
                if (current_h, current_w) != (H, W):
                    # Convert [N, H, W, C] -> [N, C, H, W] for interpolate
                    tensor = tensor.permute(0, 3, 1, 2)

                    align_corners = False if upscale_mode == "bilinear" else None
                    tensor = F.interpolate(
                        tensor,
                        size=(H, W),
                        mode=upscale_mode,
                        align_corners=align_corners
                    )

                    # Convert back [N, C, H, W] -> [N, H, W, C]
                    tensor = tensor.permute(0, 2, 3, 1)

            # Ensure metallic and roughness have 3 channels for preview
            # (ComfyUI PreviewImage expects 3-channel images)
            if key in ['metallic', 'roughness'] and tensor.shape[-1] == 1:
                tensor = tensor.repeat(1, 1, 1, 3)

            result[key] = tensor

        return result

    @classmethod
    def IS_CHANGED(cls, images, mvinverse_model, max_size, upscale_output="disabled"):
        """
        Determine if outputs need to be recalculated.

        Returns a unique hash based on input configuration.
        """
        # Images tensor hash (simplified - based on shape and sample values)
        img_hash = f"{images.shape}_{images.mean().item():.4f}"
        return f"{img_hash}_{max_size}_{upscale_output}"
