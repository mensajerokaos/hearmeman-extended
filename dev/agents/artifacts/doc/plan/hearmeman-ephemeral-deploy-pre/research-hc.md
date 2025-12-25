---
author: oz
model: claude-opus-4-5
date: 2025-12-24 21:50
task: Codebase research for Hearmeman ephemeral deployment PRD
---

# Hearmeman Ephemeral Deployment - Codebase Research

Comprehensive research findings for RunPod scripts, model installations, and deployment patterns in the Jose Obscura Documental MACQ project.

---

## Table of Contents

1. [Existing RunPod Scripts and Configurations](#1-existing-runpod-scripts-and-configurations)
2. [VibeVoice Installation Requirements](#2-vibevoice-installation-requirements)
3. [SteadyDancer Installation Requirements](#3-steadydancer-installation-requirements)
4. [SCAIL Installation Requirements](#4-scail-installation-requirements)
5. [WAN 2.2 Model Requirements](#5-wan-22-model-requirements)
6. [SSH Connection Patterns](#6-ssh-connection-patterns)
7. [Post-Deploy Scripts](#7-post-deploy-scripts)
8. [Environment Variables Discovery](#8-environment-variables-discovery)
9. [Key File Paths Summary](#9-key-file-paths-summary)

---

## 1. Existing RunPod Scripts and Configurations

### Primary Startup Script

**File**: `scripts/runpod_startup.sh` (184 lines)

The main orchestration script that handles environment-driven installation of AI models and ComfyUI nodes.

```bash
#!/bin/bash
# Environment variable-driven installation
# INSTALL_ZIMAGE=1         - Z-Image-Turbo (Alibaba Tongyi-MAI)
# INSTALL_XTTS=1           - XTTS v2 (Python <3.12 required)
# INSTALL_VIBEVOICE=1      - VibeVoice TTS
# INSTALL_STEADYDANCER=1   - SteadyDancer for video
# INSTALL_SCAIL=1          - SCAIL for facial mocap
# INSTALL_TURBODIFFUSION=1 - TurboDiffusion acceleration

COMFYUI_DIR="${COMFYUI_DIR:-/ComfyUI}"
CUSTOM_NODES_DIR="$COMFYUI_DIR/custom_nodes"
```

**Key Functions**:
- `install_node()` - Clones git repo and installs requirements.txt
- Logging to `/tmp/startup.log`
- Node-specific installation with dependency checks

### CUDA Initialization Script

**File**: `scripts/runpod/cuda_init.sh` (78 lines)

Fixes cold-start CUDA issues (CUDA_ERROR_NOT_INITIALIZED, device mapping):

```bash
export CUDA_VISIBLE_DEVICES=0
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Wait for GPU with retry (max 10 attempts, 3s delay)
# CUDA warmup via PyTorch tensor allocation
```

### ComfyUI Launcher

**File**: `scripts/runpod/start_comfyui.sh` (26 lines)

```bash
#!/bin/bash
source "$SCRIPT_DIR/cuda_init.sh"
source "$VENV_PATH/bin/activate"
cd "$COMFYUI_PATH"
exec "$VENV_PATH/bin/python" main.py --listen 0.0.0.0 --port 8188
```

### Template Configuration Guide

**File**: `scripts/runpod_template_config.md` (147 lines)

Documents the Hearmeman template setup:
- Template ID: `758dsjwiqz`
- Base: ComfyUI with WAN 2.1/2.2, CUDA 12.8
- 450GB ephemeral storage included

---

## 2. VibeVoice Installation Requirements

### From runpod_startup.sh

```bash
if [ "${INSTALL_VIBEVOICE:-0}" = "1" ]; then
    install_node "https://github.com/ShmuelRonen/ComfyUI-VibeVoice.git"
fi
```

### Alternative Source (setup_runpod_vibevoice.sh)

```bash
# From wildminder fork
wget -q https://github.com/wildminder/ComfyUI-VibeVoice/archive/refs/heads/main.zip
```

### Model Downloads

```bash
if [ "${VIBEVOICE_MODEL:-}" = "Large" ]; then
    python -c "
from huggingface_hub import snapshot_download
snapshot_download('zyphra/VibeVoice-Large', local_dir='/ComfyUI/models/vibevoice/VibeVoice-Large')
"
fi
```

### Models Available

| Model | VRAM | Quality | Speed |
|-------|------|---------|-------|
| VibeVoice-1.5B | ~3GB | Good | Fast |
| VibeVoice-Large | ~18GB | Best | Slower |

### Configuration Reference

**File**: `scripts/vibevoice_config.py` (228 lines)

Key parameters:
- `cfg_scale`: 1.3 (voice adherence)
- `inference_steps`: 8-15
- `temperature`: 0.95
- `attention_mode`: SDPA (recommended)
- Quantization: 4-bit optional

**File**: `scripts/vibevoice_presets.json` (95 lines)

Presets: `fast`, `balanced`, `quality`, `low_vram`

---

## 3. SteadyDancer Installation Requirements

### From runpod_startup.sh

```bash
if [ "${INSTALL_STEADYDANCER:-0}" = "1" ]; then
    install_node "https://github.com/kijai/ComfyUI-SteadyDancer-Wrapper.git"
fi
```

### Installation Commands

```bash
cd /workspace/ComfyUI/custom_nodes
git clone https://github.com/kijai/ComfyUI-WanVideoWrapper
git clone https://github.com/kijai/ComfyUI-SteadyDancer-Wrapper
pip install -r ComfyUI-WanVideoWrapper/requirements.txt
```

### Model Download

```bash
cd /workspace/ComfyUI/models/diffusion_models
wget https://huggingface.co/MCG-NJU/SteadyDancer-14B/resolve/main/Wan21_SteadyDancer_fp16.safetensors
```

### Technical Specs (from scail-vs-steadydancer.md)

| Spec | Value |
|------|-------|
| Parameters | 14B |
| Based On | WAN 2.1 |
| VRAM (FP16) | 24GB+ |
| VRAM (FP8) | 12-16GB |
| VRAM (GGUF) | ~8GB |
| Resolution | 720p+ |

### Dependencies

```
Python 3.10
PyTorch 2.5.1, CUDA 12.1
flash-attn==2.7.4
xformers==0.0.29.post1
mmpose==1.3.2, mmdet==3.3.0, mmcv==2.1.0
moviepy==2.2.1, decord==0.6.0
```

### GGUF Quantized Version

```bash
# For low VRAM (8-16GB)
wget https://huggingface.co/MCG-NJU/SteadyDancer-GGUF/resolve/main/steadydancer.gguf
```

---

## 4. SCAIL Installation Requirements

### From runpod_startup.sh

```bash
if [ "${INSTALL_SCAIL:-0}" = "1" ]; then
    install_node "https://github.com/chaojie/ComfyUI-SCAIL.git"
    log "Note: SCAIL for facial expression mocap exploration"
fi
```

### Installation Commands

```bash
cd /workspace/ComfyUI/custom_nodes
git clone https://github.com/kijai/ComfyUI-WanVideoWrapper
git clone https://github.com/kijai/ComfyUI-SCAIL-Pose
pip install -r ComfyUI-WanVideoWrapper/requirements.txt
```

### Model Download

```bash
cd /workspace/ComfyUI/models/diffusion_models
GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/zai-org/SCAIL-Preview
cd SCAIL-Preview && git lfs pull
```

### Technical Specs (from scail-vs-steadydancer.md)

| Spec | Value |
|------|-------|
| Parameters | 14B |
| Approach | 3D OpenPose |
| VRAM (Full) | 24-48GB |
| VRAM (WanGP) | 6-12GB |
| VRAM (GGUF) | ~8GB |
| Resolution | 512p |
| Duration | 5 sec |

### Dependencies

```
Python 3.10-3.12
pip install -r requirements.txt
git submodule update --init --recursive  # pose module
```

### Key Differentiator

SCAIL handles **facial expressions** and **3D camera rotations** better than SteadyDancer, but SteadyDancer is faster and preserves style better.

---

## 5. WAN 2.2 Model Requirements

### ComfyUI Wrapper Installation

```bash
cd /workspace/ComfyUI/custom_nodes
git clone https://github.com/kijai/ComfyUI-WanVideoWrapper
pip install -r ComfyUI-WanVideoWrapper/requirements.txt
```

### Model Downloads (from wan-nsfw-comparison.md)

```bash
cd /workspace/ComfyUI/models/diffusion_models
# High-noise expert (MoE)
wget https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B/resolve/main/wan2.2_i2v_high_noise_14B_fp16.safetensors

# Low-noise expert (MoE)
wget https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B/resolve/main/wan2.2_i2v_low_noise_14B_fp16.safetensors

# Text encoder
cd ../text_encoders
wget https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5_xxl_fp8_e4m3fn_scaled.safetensors

# VAE
cd ../vae
wget https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/wan_2.1_vae.safetensors
```

### Hearmeman Template Pre-Installs

The Hearmeman template (ID: `758dsjwiqz`) includes:
- WAN 2.1/2.2 models (varies by env vars)
- CUDA 12.8
- ComfyUI with Kijai wrapper

Environment variables for model selection:
- `WAN_480P=true` - Download 480p models
- `WAN_720P=true` - Download 720p models
- `WAN_FUN=true` - Download WAN Fun models
- `VACE=true` - Download VACE models

### Model File Structure

```
ComfyUI/models/
├── diffusion_models/
│   ├── Wan2_1-T2V-14B_fp8_e4m3fn.safetensors
│   ├── wan2.2_i2v_high_noise_14B_fp16.safetensors
│   └── wan2.2_i2v_low_noise_14B_fp16.safetensors
├── text_encoders/
│   └── umt5_xxl_fp8_e4m3fn_scaled.safetensors
└── vae/
    └── wan_2.1_vae.safetensors
```

### Storage Requirements

| Component | Size |
|-----------|------|
| WAN 2.2 Models (2x14B) | ~56GB |
| Text Encoder | ~15GB |
| VAE | ~0.5GB |
| **Total WAN Stack** | **~72GB** |

### VRAM Requirements

| Model | VRAM |
|-------|------|
| WAN 2.1 T2V-1.3B | 8GB |
| WAN 2.1/2.2 T2V-14B | 24-48GB |
| WAN 2.2 TI2V-5B | 8-16GB |
| WAN 2.2 I2V-A14B (MoE) | 24-48GB |

---

## 6. SSH Connection Patterns

### RunPod SSH Proxy (Standard)

```bash
ssh {POD_ID}-64410c4b@ssh.runpod.io -i ~/.ssh/id_ed25519 -tt
```

From `scripts/vibevoice_presets.json`:
```json
{
  "_runpod": {
    "ssh": "ssh 43kqp2ypdw3uh6-64410c4b@ssh.runpod.io -i ~/.ssh/id_ed25519 -tt"
  }
}
```

### Local SSH Config Alias

From CLAUDE.md:
```bash
ssh runpod  # Uses ~/.ssh/config alias (port changes each restart)
```

### Direct IP Connection (Secure Cloud)

For pods with public IP:
```bash
ssh root@[IP-ADDRESS] -p [SSH-PORT] -i ~/.ssh/id_ed25519
```

### ComfyUI HTTP API

From `scripts/vibevoice_config.py`:
```python
@property
def comfyui_url(self) -> str:
    return f"https://{self.pod_id}-{self.comfyui_port}.proxy.runpod.net"
```

**Endpoints**:
- `POST /prompt` - Submit workflow
- `GET /history/{prompt_id}` - Check status
- Proxy format: `https://{POD_ID}-8188.proxy.runpod.net`

### RunPod GraphQL API

From `dev/agents/artifacts/doc/runpod-api/api-reference.md`:
```bash
curl -s --request POST \
  --header 'content-type: application/json' \
  --url 'https://api.runpod.io/graphql?api_key=YOUR_KEY' \
  --data '{"query": "query Pods { myself { pods { id name desiredStatus } } }"}'
```

---

## 7. Post-Deploy Scripts

### Docker Container Startup

**File**: `docker/start.sh` (52 lines)

```bash
#!/bin/bash
set -e

# SSH setup from PUBLIC_KEY env
if [[ $PUBLIC_KEY ]]; then
    mkdir -p ~/.ssh
    echo "$PUBLIC_KEY" >> ~/.ssh/authorized_keys
    chmod 700 -R ~/.ssh
    service ssh start
fi

# CUDA environment
export CUDA_VISIBLE_DEVICES=0
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=compute,utility

# CUDA test
python -c "
import torch
print(f'CUDA Available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'Device: {torch.cuda.get_device_name(0)}')
    torch.zeros(1).cuda()
    print('CUDA test passed!')
"

# Optional Jupyter
if [[ $JUPYTER_PASSWORD ]]; then
    cd /workspace
    nohup jupyter lab --allow-root --no-browser --port=8888 --ip=* \
        --ServerApp.token=$JUPYTER_PASSWORD \
        --ServerApp.allow_origin=* &> /jupyter.log &
fi

sleep infinity
```

### Venv Setup (Network Volume)

**File**: `scripts/setup_runpod_vibevoice.sh`

```bash
cd /workspace
if [ ! -d "venv" ]; then
    python3 -m venv /workspace/venv
    source /workspace/venv/bin/activate
    pip install --upgrade pip
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
fi
```

### ComfyUI Installation Pattern

```bash
if [ ! -d "ComfyUI" ]; then
    git clone https://github.com/comfyanonymous/ComfyUI.git
    cd ComfyUI
    pip install -r requirements.txt
fi
```

---

## 8. Environment Variables Discovery

### From runpod_startup.sh

| Variable | Default | Description |
|----------|---------|-------------|
| `INSTALL_ZIMAGE` | `0` | Z-Image-Turbo (~22GB total) |
| `INSTALL_XTTS` | `0` | XTTS v2 (needs Python <3.12) |
| `INSTALL_VIBEVOICE` | `0` | VibeVoice TTS |
| `INSTALL_STEADYDANCER` | `0` | SteadyDancer video |
| `INSTALL_SCAIL` | `0` | SCAIL facial mocap |
| `INSTALL_TURBODIFFUSION` | `0` | TurboDiffusion |
| `VIBEVOICE_MODEL` | - | `Large` to pre-download 18GB model |
| `COMFYUI_PORT` | `8188` | ComfyUI listen port |
| `COMFYUI_DIR` | `/ComfyUI` | ComfyUI installation path |
| `EXTRA_NODES` | - | Comma-separated git URLs |
| `DOWNLOAD_SDXL` | `0` | Download SDXL 1.0 (~7GB) |
| `DOWNLOAD_FLUX` | `0` | Download Flux.1 dev (~12GB) |

### From runpod_template_config.md (Hearmeman Template)

| Variable | Default | Description |
|----------|---------|-------------|
| `WAN_480P` | `false` | Download 480p WAN models |
| `WAN_720P` | `false` | Download 720p WAN models |
| `WAN_FUN` | `false` | Download WAN Fun models |
| `VACE` | `false` | Download VACE models |
| `CIVITAI_TOKEN` | - | CivitAI API key |
| `LORA_IDS` | - | Comma-separated LoRA version IDs |
| `CHECKPOINT_IDS` | - | Comma-separated checkpoint IDs |

### From docker/start.sh

| Variable | Description |
|----------|-------------|
| `PUBLIC_KEY` | SSH public key for root access |
| `JUPYTER_PASSWORD` | Enables Jupyter Lab on 8888 |

---

## 9. Key File Paths Summary

### Scripts

| Path | Purpose |
|------|---------|
| `scripts/runpod_startup.sh` | Main environment-driven startup |
| `scripts/runpod/cuda_init.sh` | CUDA cold-start fix |
| `scripts/runpod/start_comfyui.sh` | ComfyUI launcher with CUDA |
| `scripts/runpod/check_cuda.py` | CUDA diagnostics |
| `scripts/setup_runpod_vibevoice.sh` | VibeVoice legacy setup |
| `scripts/vibevoice_config.py` | VibeVoice Python config |
| `scripts/vibevoice_presets.json` | VibeVoice JSON presets |
| `scripts/generate_voiceover.py` | 22-segment VO generator |
| `scripts/regenerate_voiceovers.py` | VO regeneration with variations |

### Docker

| Path | Purpose |
|------|---------|
| `docker/Dockerfile` | Custom AI stack image |
| `docker/start.sh` | Container entrypoint |

### Documentation

| Path | Purpose |
|------|---------|
| `scripts/runpod_template_config.md` | Hearmeman template guide |
| `dev/agents/artifacts/doc/docker-image-hosting-options.md` | Registry comparison |
| `dev/agents/artifacts/doc/runpod-custom-template-guide.md` | Template creation guide |
| `dev/agents/artifacts/doc/runpod-api/api-reference.md` | GraphQL API reference |
| `dev/agents/artifacts/doc/scail-vs-steadydancer.md` | Model comparison |
| `dev/agents/artifacts/doc/wan-nsfw-comparison.md` | WAN version analysis |

### Workflows

| Path | Purpose |
|------|---------|
| `workflows/z-image/z_image_turbo_t2i.json` | Z-Image text-to-image |
| `workflows/z-image/z_image_turbo_i2i.json` | Z-Image image-to-image |

---

## Summary of Installation Commands

### Complete AI Stack Installation

```bash
# 1. VibeVoice TTS
INSTALL_VIBEVOICE=1
VIBEVOICE_MODEL=Large

# 2. SteadyDancer (video animation)
cd /workspace/ComfyUI/custom_nodes
git clone https://github.com/kijai/ComfyUI-WanVideoWrapper
git clone https://github.com/kijai/ComfyUI-SteadyDancer-Wrapper
pip install -r ComfyUI-WanVideoWrapper/requirements.txt

# Download model (~28GB)
cd /workspace/ComfyUI/models/diffusion_models
wget https://huggingface.co/MCG-NJU/SteadyDancer-14B/resolve/main/Wan21_SteadyDancer_fp16.safetensors

# 3. SCAIL (facial mocap)
cd /workspace/ComfyUI/custom_nodes
git clone https://github.com/kijai/ComfyUI-SCAIL-Pose
GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/zai-org/SCAIL-Preview /workspace/ComfyUI/models/diffusion_models/SCAIL-Preview
cd /workspace/ComfyUI/models/diffusion_models/SCAIL-Preview && git lfs pull

# 4. Z-Image-Turbo (text-to-image)
cd /workspace/ComfyUI/custom_nodes
git clone https://github.com/HellerCommaA/ComfyUI-ZImageLatent.git

python -c "from huggingface_hub import hf_hub_download; hf_hub_download('Comfy-Org/z_image_turbo', 'split_files/text_encoders/qwen_3_4b.safetensors', local_dir='/ComfyUI/models')"
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('Comfy-Org/z_image_turbo', 'split_files/diffusion_models/z_image_turbo_bf16.safetensors', local_dir='/ComfyUI/models')"
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('ffxvs/vae-flux', 'ae.safetensors', local_dir='/ComfyUI/models/vae')"

# 5. WAN 2.2 Models
cd /workspace/ComfyUI/models/diffusion_models
wget https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B/resolve/main/wan2.2_i2v_high_noise_14B_fp16.safetensors
wget https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B/resolve/main/wan2.2_i2v_low_noise_14B_fp16.safetensors

cd ../text_encoders
wget https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5_xxl_fp8_e4m3fn_scaled.safetensors

cd ../vae
wget https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/wan_2.1_vae.safetensors
```

### Total Storage Requirements

| Component | Size |
|-----------|------|
| VibeVoice-Large | ~18GB |
| SteadyDancer FP16 | ~28GB |
| SCAIL Preview | ~28GB |
| Z-Image-Turbo | ~22GB |
| WAN 2.2 + Encoders | ~72GB |
| **TOTAL (all models)** | **~170GB** |

**Note**: Hearmeman template provides 450GB ephemeral storage, sufficient for all models.

---

*Research completed: 2025-12-24 21:50*
*Agent: claude-opus-4-5*
*Project: Jose Obscura - Documental MACQ*
