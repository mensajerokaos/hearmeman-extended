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
ENV ENABLE_MVINVERSE="false"

# Tier 2: Prosumer GPU (24GB+ with CPU offload)
ENV ENABLE_FLASHPORTRAIT="false"
ENV ENABLE_STORYMEM="false"

# Tier 3: Datacenter GPU (48-80GB VRAM - A100/H100)
ENV ENABLE_INFCAM="false"

# GPU Memory Management
ENV GPU_MEMORY_MODE="auto"
# Options: auto, full, sequential_cpu_offload, model_cpu_offload

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

# ComfyUI-XTTS (Coqui XTTS v2) - NOTE: Has transformers compatibility issues
# Kept for future compatibility but may not load - use VibeVoice instead
RUN git clone --depth 1 https://github.com/AIFSH/ComfyUI-XTTS.git && \
    cd ComfyUI-XTTS && \
    pip install --no-cache-dir TTS pydub srt audiotsm || true

# TurboDiffusion (100-200x video speedup for WAN models)
RUN git clone --depth 1 https://github.com/anveshane/Comfyui_turbodiffusion.git && \
    cd Comfyui_turbodiffusion && \
    pip install --no-cache-dir -r requirements.txt || true

# ComfyUI-WAN (WAN 2.2 video generation nodes)
RUN git clone --depth 1 https://github.com/kijai/ComfyUI-WAN.git && \
    cd ComfyUI-WAN && \
    pip install --no-cache-dir -r requirements.txt || true

# CivitAI integration
RUN pip install --no-cache-dir civitai-downloader

# NOTE: XTTS API Server runs in separate container (docker compose --profile xtts)
# Cannot bundle due to transformers version conflict:
# - xtts-api-server requires transformers==4.36.2
# - ComfyUI/VibeVoice requires transformers>=4.51.3 (for Qwen2Tokenizer)
# See docker-compose.yml for XTTS service configuration

# ============================================
# Layer 4: Additional Dependencies
# ============================================
WORKDIR /workspace
RUN pip install --no-cache-dir \
    huggingface_hub \
    accelerate \
    safetensors \
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
    ffmpeg-python

# Flash Attention (optional - for FlashPortrait/InfCam acceleration)
RUN pip install --no-cache-dir flash_attn || echo "[Note] flash_attn install failed - will use standard attention"

# ============================================
# Layer 5: Scripts and Configuration
# ============================================
COPY start.sh /start.sh
COPY download_models.sh /download_models.sh
RUN chmod +x /start.sh /download_models.sh

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
