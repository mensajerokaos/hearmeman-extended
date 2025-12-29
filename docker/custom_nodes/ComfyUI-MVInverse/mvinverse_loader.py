"""
MVInverse Model Loader Node for ComfyUI.

Loads MVInverse checkpoint from local storage or HuggingFace Hub with model caching.
Supports FP16/FP32 precision and automatic device selection.

Author: oz
Model: claude-opus-4-5
Date: 2025-12-29
"""

import torch
import os
import sys
from pathlib import Path

# ComfyUI imports
import folder_paths


class MVInverseLoader:
    """
    Load MVInverse model checkpoint.

    This node loads the MVInverse model from either a local checkpoint file
    or downloads it from HuggingFace Hub. The model is cached to avoid
    reloading on subsequent runs.

    Outputs:
        MVINVERSE_MODEL: The loaded model ready for inference
    """

    # Global model cache to avoid reloading
    _models_cache = {}

    def __init__(self):
        """Initialize loader and ensure checkpoint directory exists."""
        self.checkpoints_dir = os.path.join(
            folder_paths.models_dir, "mvinverse"
        )
        os.makedirs(self.checkpoints_dir, exist_ok=True)

    @classmethod
    def INPUT_TYPES(cls):
        """Define input parameters for the node."""
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
    DESCRIPTION = "Load MVInverse model for multi-view inverse rendering"

    @classmethod
    def _get_checkpoint_options(cls):
        """
        Get list of available checkpoints.

        Scans the mvinverse models directory for local .pt files and
        always includes the HF Hub default option.

        Returns:
            List of checkpoint names (without .pt extension)
        """
        checkpoints = ["mvinverse"]  # HF Hub default always available

        # Scan local models directory
        models_dir = os.path.join(folder_paths.models_dir, "mvinverse")
        if os.path.exists(models_dir):
            local_checkpoints = [
                f.replace(".pt", "")
                for f in os.listdir(models_dir)
                if f.endswith(".pt")
            ]
            # Prepend local checkpoints (priority over HF Hub)
            checkpoints = local_checkpoints + checkpoints

        # Remove duplicates while preserving order
        return list(dict.fromkeys(checkpoints))

    @classmethod
    def IS_CHANGED(cls, checkpoint, device, use_fp16):
        """
        Check if model needs to be reloaded.

        Returns a hash based on the configuration. ComfyUI uses this
        to determine if cached outputs are still valid.
        """
        return f"{checkpoint}_{device}_{use_fp16}"

    def load_model(self, checkpoint, device, use_fp16):
        """
        Load MVInverse model with caching.

        Args:
            checkpoint: Name of checkpoint file or "mvinverse" for HF Hub
            device: "cuda" or "cpu"
            use_fp16: "auto", "true", or "false"

        Returns:
            Tuple containing the loaded model
        """
        cache_key = f"{checkpoint}_{device}_{use_fp16}"

        # Return cached model if available
        if cache_key in MVInverseLoader._models_cache:
            print(f"[MVInverse] Using cached model: {checkpoint}")
            return (MVInverseLoader._models_cache[cache_key],)

        # Validate device availability
        if device == "cuda" and not torch.cuda.is_available():
            print("[MVInverse] CUDA unavailable, falling back to CPU")
            device = "cpu"

        # Determine dtype based on settings
        if use_fp16 == "true":
            dtype = torch.float16
        elif use_fp16 == "false":
            dtype = torch.float32
        else:  # auto
            dtype = torch.float16 if device == "cuda" else torch.float32

        print(f"[MVInverse] Loading {checkpoint} on {device} ({dtype})")

        # Load the model
        model = self._load_checkpoint(checkpoint, device, dtype)
        model.eval()

        # Disable gradient computation for inference
        for param in model.parameters():
            param.requires_grad = False

        # Cache model for future use
        MVInverseLoader._models_cache[cache_key] = model

        print(f"[MVInverse] Model loaded successfully")
        return (model,)

    def _load_checkpoint(self, checkpoint_name, device, dtype):
        """
        Load checkpoint from local file or HuggingFace Hub.

        Args:
            checkpoint_name: Either a local filename (without .pt) or "mvinverse" for HF Hub
            device: Target device ("cuda" or "cpu")
            dtype: Target dtype (torch.float16 or torch.float32)

        Returns:
            Loaded MVInverse model in eval mode
        """
        # Try to import MVInverse
        try:
            from mvinverse.models.mvinverse import MVInverse
        except ImportError:
            # Try adding the custom_nodes path
            custom_nodes_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "mvinverse"
            )
            if os.path.exists(custom_nodes_path):
                sys.path.insert(0, custom_nodes_path)
                from mvinverse.models.mvinverse import MVInverse
            else:
                raise ImportError(
                    "[MVInverse] Failed to import mvinverse package. "
                    "Please ensure mvinverse is installed: pip install -e <mvinverse-repo>"
                )

        # Check for local checkpoint first
        local_path = os.path.join(self.checkpoints_dir, f"{checkpoint_name}.pt")

        if os.path.exists(local_path):
            # Load from local checkpoint file
            print(f"[MVInverse] Loading from local: {local_path}")
            checkpoint = torch.load(
                local_path,
                map_location=device,
                weights_only=False
            )
            model = MVInverse()
        else:
            # Use from_pretrained to download from HuggingFace Hub
            # This uses PyTorchModelHubMixin's built-in download mechanism
            print(f"[MVInverse] Downloading from HuggingFace Hub (maddog241/mvinverse)...")
            try:
                model = MVInverse.from_pretrained("maddog241/mvinverse")
                print(f"[MVInverse] Downloaded and loaded successfully")
                checkpoint = None  # Already loaded via from_pretrained
            except Exception as e:
                raise RuntimeError(
                    f"[MVInverse] Failed to download from HuggingFace Hub: {e}. "
                    "Ensure you have internet access or provide a local checkpoint."
                )

        # Load state dict - handle different checkpoint formats
        # (Skip if checkpoint is None - already loaded via from_pretrained)
        if checkpoint is not None:
            if isinstance(checkpoint, dict):
                if 'model_state_dict' in checkpoint:
                    model.load_state_dict(checkpoint['model_state_dict'])
                elif 'state_dict' in checkpoint:
                    model.load_state_dict(checkpoint['state_dict'])
                elif 'model' in checkpoint:
                    model.load_state_dict(checkpoint['model'])
                else:
                    # Assume the dict is the state dict itself
                    model.load_state_dict(checkpoint)
            else:
                # Direct state dict
                model.load_state_dict(checkpoint)

        # Move to device and set precision
        model = model.to(device=device, dtype=dtype)

        return model

    @classmethod
    def clear_cache(cls):
        """
        Clear the model cache.

        Useful for freeing VRAM when switching between models.
        """
        cls._models_cache.clear()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("[MVInverse] Model cache cleared")
