"""
Tensor conversion utilities for ComfyUI-Genfocus.

ComfyUI IMAGE format: [B, H, W, C] float32, range [0, 1]
PyTorch convention: [B, C, H, W] with various ranges
"""

import torch
import numpy as np
from typing import Union, Optional


def comfyui_to_pytorch(image_tensor: torch.Tensor) -> torch.Tensor:
    """
    Convert ComfyUI IMAGE tensor to PyTorch convention.

    Args:
        image_tensor: ComfyUI IMAGE tensor with shape (B, H, W, C)

    Returns:
        PyTorch tensor with shape (B, C, H, W)
    """
    if image_tensor.ndim == 3:
        # Single image without batch: (H, W, C) -> (1, C, H, W)
        return image_tensor.permute(2, 0, 1).unsqueeze(0)
    elif image_tensor.ndim == 4:
        # Batched: (B, H, W, C) -> (B, C, H, W)
        return image_tensor.permute(0, 3, 1, 2)
    else:
        raise ValueError(f"Expected 3D or 4D tensor, got {image_tensor.ndim}D")


def pytorch_to_comfyui(tensor: torch.Tensor) -> torch.Tensor:
    """
    Convert PyTorch tensor to ComfyUI IMAGE format.

    Args:
        tensor: PyTorch tensor with shape (B, C, H, W)

    Returns:
        ComfyUI IMAGE tensor with shape (B, H, W, C), float32, range [0, 1]
    """
    if tensor.ndim == 3:
        # Single image without batch: (C, H, W) -> (1, H, W, C)
        tensor = tensor.unsqueeze(0)

    if tensor.ndim != 4:
        raise ValueError(f"Expected 3D or 4D tensor, got {tensor.ndim}D")

    # Permute from (B, C, H, W) to (B, H, W, C)
    output = tensor.permute(0, 2, 3, 1)

    # Ensure float32 and clamp to [0, 1]
    output = output.float()
    output = torch.clamp(output, 0.0, 1.0)

    return output


def normalize_to_comfyui(array: Union[np.ndarray, torch.Tensor]) -> torch.Tensor:
    """
    Normalize array/tensor values to [0, 1] range for ComfyUI.

    Args:
        array: Input array (numpy or torch) with arbitrary range

    Returns:
        torch.Tensor with values in [0, 1] range
    """
    if isinstance(array, np.ndarray):
        array = torch.from_numpy(array)

    array = array.float()

    # If values are in [0, 255], normalize to [0, 1]
    if array.max() > 1.0:
        array = array / 255.0

    # Clamp to valid range
    array = torch.clamp(array, 0.0, 1.0)

    return array


def ensure_batch_dim(tensor: torch.Tensor, expected_dims: int = 4) -> torch.Tensor:
    """
    Ensure tensor has batch dimension.

    Args:
        tensor: Input tensor
        expected_dims: Expected number of dimensions (default 4 for images)

    Returns:
        Tensor with batch dimension added if necessary
    """
    while tensor.ndim < expected_dims:
        tensor = tensor.unsqueeze(0)
    return tensor


def to_device(
    tensor: torch.Tensor,
    device: Union[str, torch.device],
    dtype: Optional[torch.dtype] = None
) -> torch.Tensor:
    """
    Move tensor to device with optional dtype conversion.

    Args:
        tensor: Input tensor
        device: Target device ('cuda', 'cpu', or torch.device)
        dtype: Optional dtype to convert to

    Returns:
        Tensor on specified device with specified dtype
    """
    if dtype is not None:
        return tensor.to(device=device, dtype=dtype)
    return tensor.to(device=device)


def get_dtype(dtype_str: str, device: str = "cuda") -> torch.dtype:
    """
    Get torch dtype from string specification.

    Args:
        dtype_str: One of 'auto', 'float32', 'float16', 'bfloat16'
        device: Target device (used for 'auto' mode)

    Returns:
        torch.dtype
    """
    if dtype_str == "auto":
        return torch.float16 if device == "cuda" else torch.float32

    dtype_map = {
        "float32": torch.float32,
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
    }

    if dtype_str not in dtype_map:
        raise ValueError(f"Unknown dtype: {dtype_str}. Expected one of {list(dtype_map.keys())}")

    return dtype_map[dtype_str]


def depth_to_grayscale(depth_map: torch.Tensor) -> torch.Tensor:
    """
    Convert single-channel depth map to 3-channel grayscale for visualization.

    Args:
        depth_map: Depth tensor with shape (B, 1, H, W) or (B, H, W)

    Returns:
        Grayscale tensor with shape (B, 3, H, W)
    """
    if depth_map.ndim == 3:
        depth_map = depth_map.unsqueeze(1)

    # Normalize depth to [0, 1] for visualization
    d_min = depth_map.min()
    d_max = depth_map.max()
    if d_max - d_min > 0:
        depth_map = (depth_map - d_min) / (d_max - d_min)

    # Repeat to 3 channels
    return depth_map.repeat(1, 3, 1, 1)


def create_focus_mask(
    depth_map: torch.Tensor,
    focus_distance: float,
    aperture: float = 0.1
) -> torch.Tensor:
    """
    Create a focus mask based on depth map and focus distance.

    Args:
        depth_map: Normalized depth map (B, 1, H, W), values in [0, 1]
        focus_distance: Focus plane distance in [0, 1]
        aperture: Aperture size controlling DOF (smaller = more blur)

    Returns:
        Focus mask tensor (B, 1, H, W), 1 = in focus, 0 = blurred
    """
    # Calculate circle of confusion
    coc = torch.abs(depth_map - focus_distance)

    # Convert to focus weight (inverse of blur amount)
    # Using a smooth falloff based on aperture
    focus_mask = torch.exp(-(coc ** 2) / (2 * aperture ** 2))

    return focus_mask
