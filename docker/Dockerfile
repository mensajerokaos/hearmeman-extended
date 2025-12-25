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

# VibeVoice-ComfyUI
RUN git clone --depth 1 https://github.com/AIFSH/VibeVoice-ComfyUI.git && \
    cd VibeVoice-ComfyUI && \
    pip install --no-cache-dir TTS bitsandbytes>=0.48.1 || true

# ComfyUI-SCAIL-Pose
RUN git clone --depth 1 https://github.com/kijai/ComfyUI-SCAIL-Pose.git

# ControlNet Preprocessors
RUN git clone --depth 1 https://github.com/Fannovel16/comfyui_controlnet_aux.git && \
    cd comfyui_controlnet_aux && \
    pip install --no-cache-dir -r requirements.txt || true

# ComfyUI-XTTS (Coqui XTTS v2)
RUN git clone --depth 1 https://github.com/AIFSH/ComfyUI-XTTS.git && \
    cd ComfyUI-XTTS && \
    pip install --no-cache-dir TTS pydub || true

# TurboDiffusion (100-200x video speedup for WAN models)
RUN git clone --depth 1 https://github.com/anveshane/Comfyui_turbodiffusion.git && \
    cd Comfyui_turbodiffusion && \
    pip install --no-cache-dir -r requirements.txt || true

# CivitAI integration
RUN pip install --no-cache-dir civitai-downloader

# ============================================
# Layer 4: Additional Dependencies
# ============================================
WORKDIR /workspace
RUN pip install --no-cache-dir \
    huggingface_hub \
    accelerate \
    safetensors \
    sentencepiece \
    protobuf

# ============================================
# Layer 5: Scripts and Configuration
# ============================================
COPY start.sh /start.sh
COPY download_models.sh /download_models.sh
RUN chmod +x /start.sh /download_models.sh

# SSH configuration
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Create model directories
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision}

# Expose ports
EXPOSE 22 8188 8888

# Working directory
WORKDIR /workspace/ComfyUI

# Entry point
ENTRYPOINT ["/start.sh"]
