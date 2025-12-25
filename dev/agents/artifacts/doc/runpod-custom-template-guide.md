---
task: RunPod Custom Template Creation Best Practices
agent: hc (headless claude)
model: claude-opus-4-5-20251101
timestamp: 2025-12-24T16:45:00Z
status: completed
author: oz
---

# RunPod Custom Template Creation Guide

Complete guide for creating custom RunPod templates with direct SSH access, ComfyUI pre-installed, and pre-downloaded AI models.

## Table of Contents

1. [Base Image Recommendations](#1-base-image-recommendations)
2. [SSH Configuration for Direct Access](#2-ssh-configuration-for-direct-access)
3. [Dockerfile Template/Skeleton](#3-dockerfile-templateskeleton)
4. [Handling Large Model Files](#4-handling-large-model-files)
5. [Port Exposure Requirements](#5-port-exposure-requirements)
6. [Upload Process to RunPod](#6-upload-process-to-runpod)
7. [Local Testing Before Upload](#7-local-testing-before-upload)
8. [ComfyUI-Specific Configuration](#8-comfyui-specific-configuration)

---

## 1. Base Image Recommendations

### Official RunPod Images (Recommended)

| Image | PyTorch | Python | CUDA | Ubuntu | Use Case |
|-------|---------|--------|------|--------|----------|
| `runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04` | 2.8.0 | 3.11 | 12.8.1 | 22.04 | Latest, bleeding edge |
| `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04` | 2.4.0 | 3.11 | 12.4.1 | 22.04 | Stable, recommended |
| `runpod/pytorch:2.2.0-py3.10-cuda12.1.1-devel-ubuntu22.04` | 2.2.0 | 3.10 | 12.1.1 | 22.04 | Compatibility mode |

**Why use runpod/pytorch over nvidia/cuda:**
- Pre-configured SSH, JupyterLab, and web terminal
- Automatic public key handling via `$PUBLIC_KEY` env var
- nginx proxy for port forwarding
- uv package manager pre-installed
- Common ML dependencies included

### NVIDIA NGC Images (Minimal)

For maximum control with minimal bloat:

```dockerfile
# Minimal CUDA base
FROM nvcr.io/nvidia/cuda:12.6.3-devel-ubuntu24.04

# Or with cuDNN
FROM nvcr.io/nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04
```

**Trade-offs:**
- Smaller image size
- Requires manual SSH/JupyterLab setup
- More control over dependencies
- Longer container start command needed

### Image Selection Matrix

| Scenario | Recommended Base |
|----------|------------------|
| Quick deployment, standard ML | `runpod/pytorch:2.4.0-*` |
| ComfyUI with custom models | `runpod/pytorch:2.4.0-*` or custom |
| Minimal footprint | `nvcr.io/nvidia/cuda:12.4.1-*` |
| Specific framework version | Build from NVIDIA base |

---

## 2. SSH Configuration for Direct Access

### Method 1: Using RunPod Official Images (Easiest)

RunPod's official templates (pytorch, tensorflow, etc.) have SSH pre-configured:

1. Add your public key to RunPod account settings
2. Expose TCP port 22 in template
3. SSH works automatically

**Connection:**
```bash
# Via RunPod proxy (all pods, no file transfer)
ssh [pod-id]@ssh.runpod.io -i ~/.ssh/id_ed25519

# Via public IP (full SSH with SCP/SFTP)
ssh root@[IP-ADDRESS] -p [SSH-PORT] -i ~/.ssh/id_ed25519
```

### Method 2: Custom Image SSH Setup

For NVIDIA base images or custom builds, add SSH to your Dockerfile:

```dockerfile
# Install SSH
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    openssh-server \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure SSH
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
```

### Method 3: Container Start Command SSH Setup

If you can't modify the Dockerfile, use the template's "Container Start Command":

```bash
bash -c 'apt update && DEBIAN_FRONTEND=noninteractive apt-get install openssh-server -y && mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo "$PUBLIC_KEY" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && service ssh start && sleep infinity'
```

**Note:** This adds ~20-60 seconds to container startup while apt runs.

### SSH Start Script (Recommended)

Create `start.sh` for your container:

```bash
#!/bin/bash

echo "Starting container services..."

# Setup SSH if public key provided
if [[ $PUBLIC_KEY ]]; then
    echo "Configuring SSH access..."
    mkdir -p ~/.ssh && chmod 700 ~/.ssh
    echo "$PUBLIC_KEY" >> ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    service ssh start
    echo "SSH ready on port 22"
fi

# Start JupyterLab if password provided
if [[ $JUPYTER_PASSWORD ]]; then
    echo "Starting JupyterLab..."
    jupyter lab --allow-root --no-browser --port=8888 --ip=0.0.0.0 \
        --ServerApp.token="$JUPYTER_PASSWORD" \
        --ServerApp.allow_origin='*' &
fi

# Start your main application
exec "$@"
```

---

## 3. Dockerfile Template/Skeleton

### Complete Template for ComfyUI with Models

```dockerfile
# ============================================
# RunPod Custom Template - ComfyUI + Models
# ============================================
ARG BASE_IMAGE=runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04
FROM ${BASE_IMAGE}

# Build arguments for customization
ARG COMFYUI_VERSION=latest
ARG PYTHON_VERSION=3.11

# Environment setup
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV SHELL=/bin/bash

# ============================================
# Layer 1: System Dependencies (rarely changes)
# ============================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    curl \
    vim \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    openssh-server \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# Layer 2: Python Dependencies (occasionally changes)
# ============================================
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ============================================
# Layer 3: ComfyUI Installation (occasionally changes)
# ============================================
WORKDIR /workspace
RUN git clone https://github.com/comfyanonymous/ComfyUI.git && \
    cd ComfyUI && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Layer 4: Custom Nodes (changes more frequently)
# ============================================
WORKDIR /workspace/ComfyUI/custom_nodes

# Example: Install common custom nodes
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git && \
    cd ComfyUI-Manager && pip install --no-cache-dir -r requirements.txt

# Add more custom nodes as needed
# RUN git clone https://github.com/other/custom-node.git

# ============================================
# Layer 5: Models (largest layer, changes least)
# ============================================
WORKDIR /workspace/ComfyUI/models

# Option A: Download models during build (baked in)
# RUN wget -O checkpoints/model.safetensors https://url/to/model.safetensors

# Option B: Copy models from build context
# COPY models/checkpoints/* checkpoints/
# COPY models/loras/* loras/
# COPY models/vae/* vae/

# ============================================
# Layer 6: Configuration & Scripts (changes frequently)
# ============================================
WORKDIR /workspace

# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# SSH configuration
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# Expose ports
EXPOSE 22 8188 8888

# Set working directory
WORKDIR /workspace/ComfyUI

# CRITICAL: Don't override CMD if using runpod base image
# The base image's start.sh handles SSH, Jupyter, etc.
# Instead, add your startup logic to your start.sh

# For NVIDIA base images, use:
# CMD ["/start.sh"]

# For runpod base images, leave CMD alone or use:
ENTRYPOINT ["/start.sh"]
CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
```

### Minimal Template (NVIDIA Base)

```dockerfile
FROM nvcr.io/nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3-pip \
    git \
    wget \
    openssh-server \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python setup
RUN python3.11 -m pip install --upgrade pip

# SSH config
RUN mkdir -p /var/run/sshd ~/.ssh && \
    chmod 700 ~/.ssh && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# Your application
WORKDIR /workspace
COPY . .
RUN pip install -r requirements.txt

# Startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 22 8188

CMD ["/start.sh"]
```

---

## 4. Handling Large Model Files

### Strategy Comparison

| Strategy | Cold Start | Image Size | CI/CD | Best For |
|----------|------------|------------|-------|----------|
| Baked into image | Fast (10-30s) | Large (10-50GB) | Slow builds | Production |
| Network volume | Slow (+30-60s) | Small | Fast builds | Development |
| Download on start | Variable | Small | Fast builds | Public models |
| Hybrid | Medium | Medium | Balanced | Mixed workloads |

### Strategy 1: Baked into Docker Image (Recommended for Production)

```dockerfile
# Download during build
WORKDIR /workspace/ComfyUI/models/checkpoints
RUN wget -q --show-progress \
    -O sd_xl_base_1.0.safetensors \
    "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors"

# Or copy from build context
COPY models/ /workspace/ComfyUI/models/
```

**Optimization for large files:**
- Place model downloads LAST in Dockerfile (layer caching)
- Use multi-stage builds to keep final image smaller
- Combine multiple downloads in single RUN to reduce layers

### Strategy 2: Network Volume

```bash
# Template configuration
Volume Disk Size: 100 GB
Volume Mount Path: /runpod-volume

# In start.sh, symlink models
ln -sf /runpod-volume/models/* /workspace/ComfyUI/models/
```

**Performance note:** Adds 30-60 seconds to cold start due to network transfer.

### Strategy 3: Hybrid Approach

```bash
# In start.sh
#!/bin/bash

# Critical models baked in image (fast inference)
# Less-used models on volume (flexibility)

VOLUME_MODELS="/runpod-volume/models"
LOCAL_MODELS="/workspace/ComfyUI/models"

# Symlink volume models if volume exists
if [ -d "$VOLUME_MODELS" ]; then
    for dir in "$VOLUME_MODELS"/*/; do
        model_type=$(basename "$dir")
        for model in "$dir"*; do
            if [ -f "$model" ]; then
                ln -sf "$model" "$LOCAL_MODELS/$model_type/"
            fi
        done
    done
fi
```

### Layer Caching Best Practices

```dockerfile
# GOOD: Order from least to most frequently changed
# 1. Base image (rarely changes)
# 2. System packages (occasionally)
# 3. Python requirements (occasionally)
# 4. Application code (frequently)
# 5. Large models (rarely, but large)

# BAD: Models early in Dockerfile
# If models change, ALL subsequent layers rebuild

# GOOD: Models as final layer
RUN pip install -r requirements.txt
COPY app/ /app/
# Models last - changes here don't invalidate code layers
RUN wget -O model.safetensors https://...
```

---

## 5. Port Exposure Requirements

### Template Port Configuration

| Port | Protocol | Purpose | Required? |
|------|----------|---------|-----------|
| 22 | TCP | SSH (direct access) | Yes, for SSH |
| 8888 | HTTP | JupyterLab | Optional |
| 8188 | HTTP | ComfyUI web interface | Yes, for ComfyUI |
| 3000 | HTTP | Alternative web UI | Optional |

### Template Settings

```json
{
  "ports": [
    "22/tcp",
    "8888/http",
    "8188/http"
  ]
}
```

### In Dockerfile

```dockerfile
EXPOSE 22 8888 8188
```

### Port Mapping Notes

- **HTTP ports**: Automatically get HTTPS via RunPod proxy (e.g., `https://[pod-id]-8188.proxy.runpod.net`)
- **TCP ports**: Mapped to external port (check pod connection info for actual port)
- **Public IP**: Required for direct TCP access without proxy

---

## 6. Upload Process to RunPod

### Step 1: Build Locally

```bash
# Build with tag
docker build -t yourusername/comfyui-custom:v1.0 .

# Test locally (optional)
docker run --gpus all -p 8188:8188 yourusername/comfyui-custom:v1.0
```

### Step 2: Push to Registry

```bash
# Login to Docker Hub
docker login

# Push image
docker push yourusername/comfyui-custom:v1.0

# For GitHub Container Registry
docker tag yourusername/comfyui-custom:v1.0 ghcr.io/yourusername/comfyui-custom:v1.0
docker push ghcr.io/yourusername/comfyui-custom:v1.0
```

### Step 3: Create Template in RunPod

1. Go to RunPod Console > My Templates > New Template
2. Configure:

| Field | Value |
|-------|-------|
| Template Name | ComfyUI Custom v1.0 |
| Container Image | `yourusername/comfyui-custom:v1.0` |
| Container Disk | 20 GB (or more if needed) |
| Volume Disk | 0 GB (if models baked) or 50+ GB |
| Volume Mount Path | `/runpod-volume` |
| Expose HTTP Ports | `8888, 8188` |
| Expose TCP Ports | `22` |

3. Environment Variables:

| Key | Value | Description |
|-----|-------|-------------|
| `PUBLIC_KEY` | (leave blank) | Auto-populated from account |
| `JUPYTER_PASSWORD` | `your-password` | Optional |

### Step 4: Deploy Pod

1. Go to Pods > Deploy
2. Select your template
3. Choose GPU type
4. Select "Secure Cloud" for public IP (recommended for SSH)
5. Deploy

### Alternative: GitHub Integration

RunPod can build from your GitHub repo automatically:

1. Connect GitHub repo in RunPod settings
2. RunPod builds on push
3. Auto-deploys new versions

---

## 7. Local Testing Before Upload

### Test with Docker

```bash
# Run with GPU
docker run --gpus all \
  -p 22:22 \
  -p 8188:8188 \
  -e PUBLIC_KEY="$(cat ~/.ssh/id_ed25519.pub)" \
  -e JUPYTER_PASSWORD="test123" \
  yourusername/comfyui-custom:v1.0

# Test SSH
ssh -p 22 root@localhost

# Test ComfyUI
open http://localhost:8188
```

### Test without GPU

```bash
# CPU-only test (limited functionality)
docker run \
  -p 8188:8188 \
  -e CUDA_VISIBLE_DEVICES="" \
  yourusername/comfyui-custom:v1.0
```

### Validate Image Size

```bash
# Check image layers and sizes
docker history yourusername/comfyui-custom:v1.0

# Total image size
docker images yourusername/comfyui-custom:v1.0
```

### Size Guidelines

| Image Size | Cold Start | Recommendation |
|------------|------------|----------------|
| < 5 GB | 10-20 seconds | Excellent |
| 5-15 GB | 20-45 seconds | Good |
| 15-30 GB | 45-90 seconds | Acceptable |
| > 30 GB | 90+ seconds | Consider network volume |

---

## 8. ComfyUI-Specific Configuration

### Official RunPod Worker Images

Pre-built options with models:

| Image | Contents |
|-------|----------|
| `runpod/worker-comfyui:latest-base` | Clean ComfyUI, no models |
| `runpod/worker-comfyui:latest-flux1-schnell` | FLUX.1 schnell + encoders + VAE |
| `runpod/worker-comfyui:latest-flux1-dev` | FLUX.1 dev + encoders + VAE |
| `runpod/worker-comfyui:latest-sdxl` | SDXL checkpoint + VAEs |
| `runpod/worker-comfyui:latest-sd3` | SD3 medium |

### Extending Official Images

```dockerfile
FROM runpod/worker-comfyui:latest-base

# Add custom nodes
WORKDIR /comfyui/custom_nodes
RUN git clone https://github.com/your/custom-node.git && \
    cd custom-node && pip install -r requirements.txt

# Add models
COPY models/checkpoints/your_model.safetensors /comfyui/models/checkpoints/
COPY models/loras/your_lora.safetensors /comfyui/models/loras/
```

### Directory Structure

```
/workspace/ComfyUI/
├── models/
│   ├── checkpoints/     # Main models (.safetensors, .ckpt)
│   ├── loras/           # LoRA adapters
│   ├── vae/             # VAE models
│   ├── controlnet/      # ControlNet models
│   ├── clip/            # CLIP models
│   └── embeddings/      # Textual inversions
├── custom_nodes/        # Custom node repositories
├── input/               # Input images/audio
└── output/              # Generated outputs
```

### Complete start.sh for ComfyUI

```bash
#!/bin/bash
set -e

echo "=== RunPod ComfyUI Startup ==="
echo "Timestamp: $(date)"

# SSH Setup
if [[ -n "$PUBLIC_KEY" ]]; then
    echo "Configuring SSH..."
    mkdir -p ~/.ssh && chmod 700 ~/.ssh
    echo "$PUBLIC_KEY" >> ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    service ssh start
    echo "SSH ready on port 22"
fi

# JupyterLab (optional)
if [[ -n "$JUPYTER_PASSWORD" ]]; then
    echo "Starting JupyterLab on port 8888..."
    nohup jupyter lab \
        --allow-root \
        --no-browser \
        --port=8888 \
        --ip=0.0.0.0 \
        --ServerApp.token="$JUPYTER_PASSWORD" \
        --ServerApp.allow_origin='*' \
        > /var/log/jupyter.log 2>&1 &
fi

# Link network volume models if present
if [[ -d "/runpod-volume/models" ]]; then
    echo "Linking network volume models..."
    for type_dir in /runpod-volume/models/*/; do
        type=$(basename "$type_dir")
        target="/workspace/ComfyUI/models/$type"
        mkdir -p "$target"
        for model in "$type_dir"*; do
            [[ -f "$model" ]] && ln -sf "$model" "$target/"
        done
    done
fi

# Start ComfyUI
echo "Starting ComfyUI on port 8188..."
cd /workspace/ComfyUI
exec python main.py \
    --listen 0.0.0.0 \
    --port 8188 \
    --enable-cors-header \
    --preview-method auto
```

---

## Quick Reference: Template Checklist

Before uploading your template:

- [ ] SSH port 22 exposed as TCP
- [ ] HTTP ports (8188, 8888) exposed
- [ ] `PUBLIC_KEY` environment variable configured
- [ ] start.sh handles SSH key setup
- [ ] Models either baked or volume-mounted
- [ ] Image tested locally with GPU
- [ ] Image pushed to Docker Hub/GHCR
- [ ] Image size under 30GB (ideally under 15GB)

---

## Sources & References

- [RunPod Template Documentation](https://docs.runpod.io/pods/templates/manage-templates)
- [RunPod SSH Configuration](https://docs.runpod.io/pods/configuration/use-ssh)
- [RunPod Containers GitHub](https://github.com/runpod/containers)
- [RunPod PyTorch Images](https://hub.docker.com/r/runpod/pytorch/tags)
- [DIY Deep Learning Docker Container](https://www.runpod.io/blog/diy-deep-learning-docker-container)
- [Setting Up Remote Development on RunPod](https://leimao.github.io/blog/Setting-Up-Remote-Development-Custom-Template-Runpod/)
- [True SSH on RunPod](https://www.runpod.io/blog/how-to-achieve-true-ssh-in-runpod)
- [ComfyUI RunPod Worker](https://github.com/runpod-workers/worker-comfyui)
- [Docker Layer Caching Best Practices](https://neptune.ai/blog/best-practices-docker-for-machine-learning)
