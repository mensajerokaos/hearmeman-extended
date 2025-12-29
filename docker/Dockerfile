# ============================================
# Hearmeman Extended Template
# ============================================
ARG BASE_IMAGE=runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04
FROM ${BASE_IMAGE}

# Build arguments
ARG COMFYUI_COMMIT=latest
ARG DEBIAN_FRONTEND=noninteractive

# Environment
ENV PYTHONUNBUFFERED=1
ENV SHELL=/bin/bash
ENV COMFYUI_PORT=8188

# GPU Tier and Model Toggle Configuration
ENV GPU_TIER="consumer"
# Options: consumer, prosumer, datacenter

# Tier 1: Consumer GPU (8-24GB VRAM)
ENV ENABLE_GENFOCUS="false"
ENV ENABLE_QWEN_EDIT="false"
ENV QWEN_EDIT_MODEL="Q4_K_M"
# Options: Q4_K_M (13GB), Q5_K_M (15GB), Q8_0 (22GB), full (54GB)
ENV ENABLE_MVINVERSE="false"

# Tier 2: Prosumer GPU (24GB+ with CPU offload)
ENV ENABLE_FLASHPORTRAIT="false"
ENV ENABLE_STORYMEM="false"

# Tier 3: Datacenter GPU (48-80GB VRAM - A100/H100)
ENV ENABLE_INFCAM="false"

# GPU Memory Management
ENV GPU_MEMORY_MODE="auto"
# Options: auto, full, sequential_cpu_offload, model_cpu_offload

# R2 Configuration
ENV ENABLE_R2_SYNC="false"
ENV R2_ENDPOINT="https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com"
ENV R2_BUCKET="runpod"
ENV R2_ACCESS_KEY_ID=""
ENV R2_SECRET_ACCESS_KEY=""

ENV COMFYUI_ARGS=""
# For: --lowvram, --medvram, --novram, --cpu-vae, etc.

# ============================================
# Layer 1: System Dependencies
# ============================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    git-lfs \
    wget \
    curl \
    vim \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    openssh-server \
    aria2 \
    inotify-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Initialize git-lfs
RUN git lfs install

# ============================================
# Layer 2: ComfyUI Base (latest for Z-Image support)
# ============================================
WORKDIR /workspace
RUN git clone https://github.com/comfyanonymous/ComfyUI.git && \
    cd ComfyUI && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Layer 3: Custom Nodes (baked in)
# ============================================
WORKDIR /workspace/ComfyUI/custom_nodes

# ComfyUI-Manager
RUN git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Manager.git

# VibeVoice-ComfyUI (Enemyx-net fork - v1.8.1+, actively maintained)
RUN git clone --depth 1 https://github.com/Enemyx-net/VibeVoice-ComfyUI.git && \
    cd VibeVoice-ComfyUI && \
    pip install --no-cache-dir -r requirements.txt || true

# ComfyUI-Chatterbox (Resemble AI TTS - zero-shot voice cloning)
RUN git clone --depth 1 https://github.com/thefader/ComfyUI-Chatterbox.git && \
    cd ComfyUI-Chatterbox && \
    pip install --no-cache-dir -r requirements.txt || true

# ComfyUI-SCAIL-Pose
RUN git clone --depth 1 https://github.com/kijai/ComfyUI-SCAIL-Pose.git

# ControlNet Preprocessors
RUN git clone --depth 1 https://github.com/Fannovel16/comfyui_controlnet_aux.git && \
    cd comfyui_controlnet_aux && \
    pip install --no-cache-dir -r requirements.txt || true

# TurboDiffusion (100-200x video speedup for WAN models)
RUN git clone --depth 1 https://github.com/anveshane/Comfyui_turbodiffusion.git && \
    cd Comfyui_turbodiffusion && \
    pip install --no-cache-dir -r requirements.txt || true

# ComfyUI-WanVideoWrapper (WAN 2.2/2.5 video generation nodes)
RUN git clone --depth 1 https://github.com/kijai/ComfyUI-WanVideoWrapper.git && \
    cd ComfyUI-WanVideoWrapper && \
    pip install --no-cache-dir -r requirements.txt || true

# ComfyUI-VideoHelperSuite (video processing utilities)
RUN git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git && \
    cd ComfyUI-VideoHelperSuite && \
    pip install --no-cache-dir -r requirements.txt || true

# CivitAI integration
RUN pip install --no-cache-dir civitai-downloader

# ============================================
# Layer 3.5: Custom AI Model Wrappers (Local)
# ============================================
# ComfyUI-Genfocus (Depth-of-Field Refocusing)
COPY custom_nodes/ComfyUI-Genfocus /workspace/ComfyUI/custom_nodes/ComfyUI-Genfocus
RUN cd /workspace/ComfyUI/custom_nodes/ComfyUI-Genfocus && \
    pip install --no-cache-dir -r requirements.txt || true

# ComfyUI-MVInverse (Multi-view Inverse Rendering)
COPY custom_nodes/ComfyUI-MVInverse /workspace/ComfyUI/custom_nodes/ComfyUI-MVInverse
RUN cd /workspace/ComfyUI/custom_nodes/ComfyUI-MVInverse && \
    pip install --no-cache-dir -r requirements.txt || true

# ============================================
# Layer 4: Additional Dependencies
# ============================================
WORKDIR /workspace
RUN pip install --no-cache-dir \
    huggingface_hub \
    accelerate \
    safetensors \
    boto3 \
    sentencepiece \
    protobuf \
    # New dependencies for AI models
    cupy-cuda12x \
    imageio[ffmpeg] \
    einops \
    modelscope \
    ftfy \
    lpips \
    lightning \
    pandas \
    matplotlib \
    wandb \
    ffmpeg-python \
    # Dependencies for custom nodes
    audiotsm \
    loguru \
    # Dependencies for Genfocus/MVInverse
    diffusers>=0.21.0 \
    peft>=0.4.0 \
    opencv-python>=4.5.0 \
    timm

# Flash Attention - DISABLED due to ABI compatibility issues with kornia
# Uncomment only if you need FlashPortrait/InfCam and have matching CUDA/PyTorch
# RUN pip install --no-cache-dir flash_attn || echo "[Note] flash_attn install failed"

# ============================================
# Layer 5: Scripts and Configuration
# ============================================
COPY start.sh /start.sh
COPY download_models.sh /download_models.sh
COPY upload_to_r2.py /upload_to_r2.py
COPY r2_sync.sh /r2_sync.sh
RUN chmod +x /start.sh /download_models.sh /r2_sync.sh

# Copy example workflows
COPY workflows/ /workspace/ComfyUI/user/default/workflows/

# SSH configuration
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Create model directories (including new AI models)
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision,genfocus,qwen,mvinverse,flashportrait,storymem,infcam}

# Expose ports (22=SSH, 8188=ComfyUI, 8888=Jupyter)
EXPOSE 22 8188 8888

# Working directory
WORKDIR /workspace/ComfyUI

# Entry point
ENTRYPOINT ["/start.sh"]
