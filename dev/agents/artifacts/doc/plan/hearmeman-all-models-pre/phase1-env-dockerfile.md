# Phase 1: Environment Variables & Dockerfile Base Changes

This document outlines the modifications to the `docker/Dockerfile` to integrate new environment variables, GPU memory management flags, essential pip dependencies for new models, and create corresponding model directories.

## 1. Environment Variables + GPU Memory Management Flags

**File:** `docker/Dockerfile`
**Location:** Insert after line 12 (after `ENV COMFYUI_PORT=8188`)

**Instruction:** Add new environment variables for GPU tier configuration, model enabling flags, and GPU memory management.

```diff
--- a/docker/Dockerfile
+++ b/docker/Dockerfile
@@ -10,6 +10,16 @@
 ENV PYTHONUNBUFFERED=1
 ENV SHELL=/bin/bash
 ENV COMFYUI_PORT=8188
+# New Environment Variables for Model Toggles and GPU Management
+ENV GPU_TIER="consumer" # Options: consumer, prosumer, datacenter
+ENV ENABLE_GENFOCUS="false"
+ENV ENABLE_QWEN_EDIT="false"
+ENV ENABLE_MVINVERSE="false"
+ENV ENABLE_FLASHPORTRAIT="false"
+ENV ENABLE_STORYMEM="false"
+ENV ENABLE_INFCAM="false"
+ENV GPU_MEMORY_MODE="full" # Options: full, sequential_cpu_offload, model_cpu_offload
+ENV COMFYUI_ARGS="" # For --lowvram, --medvram, etc.
 
 # ============================================ 
 # Layer 1: System Dependencies

```

## 2. Dockerfile Modifications: Pip Dependencies

**File:** `docker/Dockerfile`
**Location:** Insert into Layer 4, after line 108 (after `protobuf`)

**Instruction:** Add new pip dependencies identified from the `new-models-research.md` document that are not already present or explicitly managed by customফতরের requirements.txt` files. Note that specific `torch` versions are not included as the base image provides a compatible PyTorch environment. Conflicting `transformers` and `controlnet-aux` versions will be explicitly installed, but this might require further conflict resolution in later phases if other custom nodes break.

```diff
--- a/docker/Dockerfile
+++ b/docker/Dockerfile
@@ -105,7 +105,21 @@
     accelerate \
     safetensors \
     sentencepiece \
-    protobuf
+    protobuf \
+    # Additional dependencies for new models (Genfocus, InfCam, MVInverse, FlashPortrait, StoryMem)
+    cupy-cuda12x \
+    transformers==4.46.2 \
+    controlnet-aux==0.0.7 \
+    imageio[ffmpeg] \
+    einops \
+    modelscope \
+    ftfy \
+    lpips \
+    lightning \
+    pandas \
+    matplotlib \
+    wandb \
+    ffmpeg-python \
+    numpy \
+    opencv-python \
+    flash_attn # For FlashPortrait and StoryMem

```

## 3. Dockerfile Modifications: Create New Model Directories

**File:** `docker/Dockerfile`
**Location:** Insert into existing `Create model directories` section, after line 119

**Instruction:** Add new directories for storing model weights related to Genfocus, InfCam, MVInverse, FlashPortrait, StoryMem, and Qwen-Image-Edit.

```diff
--- a/docker/Dockerfile
+++ b/docker/Dockerfile
@@ -116,7 +116,7 @@
     sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
 
 # Create model directories
-RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision}
+RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision,genfocus,infcam,mvinverse,flashportrait,storymem,qwen}
 
 # Expose ports (22=SSH, 8188=ComfyUI, 8888=Jupyter)
 EXPOSE 22 8188 8888

```

## Dependencies List (Consolidated New Additions):

**Environment Variables:**
- `GPU_TIER`
- `ENABLE_GENFOCUS`
- `ENABLE_QWEN_EDIT`
- `ENABLE_MVINVERSE`
- `ENABLE_FLASHPORTRAIT`
- `ENABLE_STORYMEM`
- `ENABLE_INFCAM`
- `GPU_MEMORY_MODE`
- `COMFYUI_ARGS`

**Pip Dependencies:**
- `cupy-cuda12x`
- `transformers==4.46.2`
- `controlnet-aux==0.0.7`
- `imageio[ffmpeg]`
- `einops`
- `modelscope`
- `ftfy`
- `lpips`
- `lightning`
- `pandas`
- `matplotlib`
- `wandb`
- `ffmpeg-python`
- `numpy`
- `opencv-python`
- `flash_attn`

**Model Directories:**
- `/workspace/ComfyUI/models/genfocus`
- `/workspace/ComfyUI/models/infcam`
- `/workspace/ComfyUI/models/mvinverse`
- `/workspace/ComfyUI/models/flashportrait`
- `/workspace/ComfyUI/models/storymem`
- `/workspace/ComfyUI/models/qwen`
