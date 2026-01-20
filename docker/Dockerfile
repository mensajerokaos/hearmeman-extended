# ============================================
# Hearmeman Extended Template
# ============================================
ARG BASE_IMAGE=runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04
FROM ${BASE_IMAGE}

# OCI Labels for GHCR linking
LABEL org.opencontainers.image.source=https://github.com/mensajerokaos/hearmeman-extended
LABEL org.opencontainers.image.description="ComfyUI with AI video/audio generation (WAN, VibeVoice, TurboDiffusion)"
LABEL org.opencontainers.image.licenses=MIT

# Build arguments
ARG COMFYUI_COMMIT=latest
ARG DEBIAN_FRONTEND=noninteractive

# Build-time model downloads (bakes models into image for instant startup)
ARG BAKE_WAN_720P=false
ARG BAKE_WAN_480P=false
ARG BAKE_ILLUSTRIOUS=false

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
    timm \
    # NVIDIA GPU management (for TurboDiffusion)
    pynvml

# ============================================
# Layer 4.5: SteadyDancer Dependencies
# ============================================
# Install in specific order to avoid ABI conflicts
# CRITICAL: PyTorch 2.5.1 required for mmpose compatibility
RUN pip install --no-cache-dir \
    torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu124 \
    2>/dev/null || pip install --no-cache-dir \
    torch torchvision torchaudio

# Pose estimation dependencies (MMSelfCom workstack)
RUN pip install --no-cache-dir \
    mmengine \
    mmcv==2.1.0 \
    mmdet>=3.1.0 \
    mmpose \
    dwpose>=0.1.0 \
    2>/dev/null || echo "[Note] MMPose/DWPose stack install failed, some features may be limited"

# Flash Attention - REQUIRED for optimal performance with SteadyDancer
# Retries on failure to handle ABI compatibility issues
RUN pip install --no-cache-dir flash_attn==2.7.4.post1 \
    2>/dev/null || echo "[Note] flash_attn install failed, using xformers fallback"

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
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision,genfocus,qwen,mvinverse,flashportrait,storymem,infcam,steadydancer}

# ============================================
# Layer 6: Build-time Model Downloads (Optional)
# ============================================
# Re-declare ARGs after FROM (Docker requirement)
ARG BAKE_WAN_720P
ARG BAKE_WAN_480P
ARG BAKE_ILLUSTRIOUS
ARG BAKE_STEADYDANCER=false
ARG STEADYDANCER_VARIANT=fp8
ARG BAKE_TURBO=false

# WAN 2.1 720p Models (~25GB total: 14B diffusion + text encoders + VAE)
RUN if [ "$BAKE_WAN_720P" = "true" ]; then \
    echo "[BUILD] Downloading WAN 2.1 720p models..." && \
    wget -q --show-progress -O /workspace/ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors \
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" && \
    wget -q --show-progress -O /workspace/ComfyUI/models/clip_vision/clip_vision_h.safetensors \
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" && \
    wget -q --show-progress -O /workspace/ComfyUI/models/vae/wan_2.1_vae.safetensors \
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" && \
    wget -q --show-progress -O /workspace/ComfyUI/models/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors \
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" && \
    echo "[BUILD] WAN 2.1 720p models downloaded"; \
    fi

# WAN 2.1 480p Models (~12GB total: 1.3B diffusion + text encoders + VAE)
RUN if [ "$BAKE_WAN_480P" = "true" ]; then \
    echo "[BUILD] Downloading WAN 2.1 480p models..." && \
    [ -f /workspace/ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors ] || \
    wget -q --show-progress -O /workspace/ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors \
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" && \
    [ -f /workspace/ComfyUI/models/vae/wan_2.1_vae.safetensors ] || \
    wget -q --show-progress -O /workspace/ComfyUI/models/vae/wan_2.1_vae.safetensors \
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" && \
    wget -q --show-progress -O /workspace/ComfyUI/models/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors \
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors" && \
    echo "[BUILD] WAN 2.1 480p models downloaded"; \
    fi

# Illustrious XL Models (~6.5GB checkpoint + embeddings)
RUN if [ "$BAKE_ILLUSTRIOUS" = "true" ]; then \
    echo "[BUILD] Downloading Illustrious XL models..." && \
    wget -q --show-progress -O /workspace/ComfyUI/models/checkpoints/illustrious_realism_v10.safetensors \
        "https://civitai.com/api/download/models/2091367" && \
    mkdir -p /workspace/ComfyUI/models/embeddings && \
    wget -q --show-progress -O /workspace/ComfyUI/models/embeddings/negativeXL_D.safetensors \
        "https://civitai.com/api/download/models/134583" && \
    wget -q --show-progress -O /workspace/ComfyUI/models/embeddings/PDXL.safetensors \
        "https://civitai.com/api/download/models/367841" && \
    echo "[BUILD] Illustrious XL models downloaded"; \
    fi

# SteadyDancer Models (~14-28GB depending on variant)
RUN if [ "$BAKE_STEADYDANCER" = "true" ]; then \
    echo "[BUILD] Downloading SteadyDancer ${STEADYDANCER_VARIANT} model..." && \
    if [ "$STEADYDANCER_VARIANT" = "fp16" ]; then \
        wget -q --show-progress -O /workspace/ComfyUI/models/diffusion_models/Wan21_SteadyDancer_fp16.safetensors \
            "https://huggingface.co/MCG-NJU/SteadyDancer-14B/resolve/main/Wan21_SteadyDancer_fp16.safetensors" && \
        echo "[BUILD] SteadyDancer fp16 downloaded (28GB)"; \
    elif [ "$STEADYDANCER_VARIANT" = "fp8" ]; then \
        wget -q --show-progress -O /workspace/ComfyUI/models/diffusion_models/Wan21_SteadyDancer_fp8.safetensors \
            "https://huggingface.co/kijai/SteadyDancer-14B-pruned/resolve/main/Wan21_SteadyDancer_fp8.safetensors" && \
        echo "[BUILD] SteadyDancer fp8 downloaded (14GB)"; \
    fi && \
    echo "[BUILD] SteadyDancer models downloaded" || \
    echo "[BUILD] SteadyDancer download skipped or failed"; \
    fi

# TurboDiffusion Model (~14GB)
RUN if [ "$BAKE_TURBO" = "true" ]; then \
    echo "[BUILD] Downloading TurboDiffusion model (~14GB)..." && \
    wget -q --show-progress -O /workspace/ComfyUI/models/diffusion_models/wan_2.1_turbodiffusion.safetensors \
        "https://huggingface.co/kijai/wan-2.1-turbodiffusion/resolve/main/wan_2.1_turbodiffusion.safetensors" && \
    echo "[BUILD] TurboDiffusion downloaded (14GB)" || \
    echo "[BUILD] TurboDiffusion download skipped or failed"; \
    fi

# Expose ports (22=SSH, 8188=ComfyUI, 8888=Jupyter)
EXPOSE 22 8188 8888

# Working directory
WORKDIR /workspace/ComfyUI

# Entry point
ENTRYPOINT ["/start.sh"]
