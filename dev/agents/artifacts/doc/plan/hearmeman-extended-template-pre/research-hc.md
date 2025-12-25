---
author: oz
model: claude-opus-4-5
date: 2025-12-24 22:15
task: Codebase and external research for Hearmeman Extended Template PRD
---

# Research: Hearmeman Extended Template

Comprehensive research for a custom RunPod template extending Hearmeman with additional AI capabilities.

## 1. Base Template Reference

### Hearmeman Template (758dsjwiqz)
From `dev/agents/artifacts/doc/plan/hearmeman-ephemeral-deploy.md`:

| Property | Value |
|----------|-------|
| Template ID | 758dsjwiqz |
| Name | One Click - ComfyUI Wan t2v i2v VACE - CUDA 12.8 |
| Base | PyTorch 2.8.0, CUDA 12.8, ComfyUI |
| Storage | 450GB ephemeral |
| Models | WAN 2.2 (720p), UMT5 XXL |

### Environment Variables (from existing template)
```
WAN_480P=false
WAN_720P=true
WAN_FUN=false
VACE=false
CIVITAI_TOKEN=
LORA_IDS=
CHECKPOINT_IDS=
```

---

## 2. Custom Nodes - GitHub Repositories

### 2.1 VibeVoice-ComfyUI (TTS Voice Cloning)

**Repository**: https://github.com/AIFSH/VibeVoice-ComfyUI (original)
**Alternative**: https://github.com/wildminder/ComfyUI-VibeVoice
**Alternative**: https://github.com/Enemyx-net/VibeVoice-ComfyUI

**Installation**:
```bash
cd /workspace/ComfyUI/custom_nodes
git clone --depth 1 https://github.com/AIFSH/VibeVoice-ComfyUI
cd VibeVoice-ComfyUI
pip install -r requirements.txt
pip install TTS bitsandbytes>=0.48.1
```

**Dependencies**:
- TTS library
- bitsandbytes>=0.48.1 (Q8 fix)
- torch, torchaudio
- transformers

**VRAM Requirements**:
| Model | Size | VRAM |
|-------|------|------|
| VibeVoice-1.5B | ~5.4GB | 8GB |
| VibeVoice-Large | ~18GB | 20GB |
| VibeVoice-Large-Q8 | ~6GB | 10GB |

---

### 2.2 ComfyUI-SCAIL-Pose (Facial Expressions)

**Repository**: https://github.com/kijai/ComfyUI-SCAIL-Pose

**Installation**:
```bash
cd /workspace/ComfyUI/custom_nodes
git clone --depth 1 https://github.com/kijai/ComfyUI-SCAIL-Pose
```

**Model Repository**: https://huggingface.co/zai-org/SCAIL-Preview

**Download**:
```bash
cd /workspace/ComfyUI/models/diffusion_models
GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/zai-org/SCAIL-Preview
cd SCAIL-Preview
git lfs pull
```

**Size**: ~28GB (includes VAE and text encoder)
**VRAM**: 24GB+ recommended

---

### 2.3 SteadyDancer (Dance Video Animation)

**Repository**: https://github.com/MCG-NJU/SteadyDancer
**Model**: https://huggingface.co/MCG-NJU/SteadyDancer-14B

**Installation**:
```bash
cd /workspace/ComfyUI/models/diffusion_models
wget -c https://huggingface.co/MCG-NJU/SteadyDancer-14B/resolve/main/Wan21_SteadyDancer_fp16.safetensors
```

**Alternative (GGUF)**:
```bash
# Smaller quantized version
wget -c https://huggingface.co/MCG-NJU/SteadyDancer-GGUF/resolve/main/SteadyDancer-14B-Q8_0.gguf
```

**Sizes**:
| Variant | Size | VRAM |
|---------|------|------|
| FP16 | 32.8GB | 28GB |
| Q8_0 GGUF | 17.4GB | 20GB |
| BF16 GGUF | 32.8GB | 28GB |

**VRAM**: 24-48GB depending on variant

---

### 2.4 Z-Image/Lumina2 Support

**Repository**: https://github.com/Tongyi-MAI/Z-Image
**Model**: https://huggingface.co/Tongyi-MAI/Z-Image-Turbo

**Components** (3 separate files):
| Component | Path | Size |
|-----------|------|------|
| Text Encoder | `models/text_encoders/qwen_3_4b.safetensors` | ~8GB |
| Diffusion Model | `models/diffusion_models/z_image_turbo_bf16.safetensors` | ~12GB |
| VAE | `models/vae/ae.safetensors` | ~335MB |

**Total Size**: ~21GB
**VRAM**: 16GB minimum, 24GB recommended

**Installation**:
```bash
cd /workspace/ComfyUI/models/text_encoders
wget -c https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/resolve/main/qwen_3_4b.safetensors

cd /workspace/ComfyUI/models/diffusion_models
wget -c https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/resolve/main/z_image_turbo_bf16.safetensors

cd /workspace/ComfyUI/models/vae
wget -c https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/resolve/main/ae.safetensors
```

---

### 2.5 ControlNet Nodes

**Main Repository**: https://github.com/Fannovel16/comfyui_controlnet_aux

**Installation**:
```bash
cd /workspace/ComfyUI/custom_nodes
git clone --depth 1 https://github.com/Fannovel16/comfyui_controlnet_aux
cd comfyui_controlnet_aux
pip install -r requirements.txt
```

**ControlNet Models** (SD1.5 v1.1):
| Model | URL | Size |
|-------|-----|------|
| Canny | lllyasviel/ControlNet-v1-1/control_v11p_sd15_canny.pth | 1.45GB |
| Depth | lllyasviel/ControlNet-v1-1/control_v11f1p_sd15_depth.pth | 1.45GB |
| Openpose | lllyasviel/ControlNet-v1-1/control_v11p_sd15_openpose.pth | 1.45GB |
| Lineart | lllyasviel/ControlNet-v1-1/control_v11p_sd15_lineart.pth | 1.45GB |
| Normal | lllyasviel/ControlNet-v1-1/control_v11p_sd15_normalbae.pth | 1.45GB |

**FP16 Versions** (smaller, recommended for ComfyUI):
- https://huggingface.co/comfyanonymous/ControlNet-v1-1_fp16_safetensors
- Size: 723MB each

**SDXL ControlNet**:
| Model | URL | Size |
|-------|-----|------|
| Canny | xinsir/controlnet-canny-sdxl-1.0 | ~2.5GB |
| Depth | xinsir/controlnet-depth-sdxl-1.0 | ~2.5GB |
| Openpose | xinsir/controlnet-openpose-sdxl-1.0 | ~2.5GB |

**Download Script**:
```bash
cd /workspace/ComfyUI/models/controlnet

# SD1.5 FP16 versions
for model in canny depth openpose lineart normalbae; do
    wget -c "https://huggingface.co/comfyanonymous/ControlNet-v1-1_fp16_safetensors/resolve/main/control_v11p_sd15_${model}_fp16.safetensors"
done
```

---

### 2.6 ComfyUI-Manager

**Repository**: https://github.com/ltdrdata/ComfyUI-Manager

**Installation** (should be baked into Docker image):
```bash
cd /workspace/ComfyUI/custom_nodes
git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Manager
```

---

## 3. Model Download URLs (Complete Reference)

### 3.1 VibeVoice Models
| Model | URL | Size |
|-------|-----|------|
| VibeVoice-1.5B | huggingface.co/microsoft/VibeVoice-1.5B | 5.4GB |
| VibeVoice-Large | huggingface.co/AIFSH/VibeVoice-Large (HF copy) | ~18GB |
| VibeVoice-Large | modelscope.cn/models/AIFSH/VibeVoice-Large (original) | ~18GB |
| VibeVoice-Large-Q8 | huggingface.co/FabioSarracino/VibeVoice-Large-Q8 | ~6GB |

### 3.2 SteadyDancer Models
| Model | URL | Size |
|-------|-----|------|
| SteadyDancer-14B FP16 | huggingface.co/MCG-NJU/SteadyDancer-14B/Wan21_SteadyDancer_fp16.safetensors | 32.8GB |
| SteadyDancer-14B Q8 | huggingface.co/MCG-NJU/SteadyDancer-GGUF/SteadyDancer-14B-Q8_0.gguf | 17.4GB |

### 3.3 SCAIL Models
| Model | URL | Size |
|-------|-----|------|
| SCAIL-Preview | huggingface.co/zai-org/SCAIL-Preview | ~28GB |
| SCAIL-Preview GGUF | huggingface.co/vantagewithai/SCAIL-Preview-GGUF | ~15GB |

### 3.4 Z-Image Turbo
| Component | URL | Size |
|-----------|-----|------|
| Text Encoder | huggingface.co/Tongyi-MAI/Z-Image-Turbo/qwen_3_4b.safetensors | ~8GB |
| Diffusion | huggingface.co/Tongyi-MAI/Z-Image-Turbo/z_image_turbo_bf16.safetensors | ~12GB |
| VAE | huggingface.co/Tongyi-MAI/Z-Image-Turbo/ae.safetensors | 335MB |

---

## 4. /workspace Mount Detection

### Detection Logic

From `dev/agents/artifacts/doc/runpod-custom-template-guide.md`:

```bash
# Check if /workspace is a mounted volume vs container disk
if [ -d "/workspace" ] && mountpoint -q "/workspace"; then
    STORAGE_MODE="persistent"
    echo "Network volume detected at /workspace"
else
    STORAGE_MODE="ephemeral"
    echo "Ephemeral storage mode (container disk)"
fi
```

### Smart Model Download Logic

```bash
#!/bin/bash
# check_and_download.sh

MODEL_PATH="$1"
MODEL_URL="$2"
MODEL_NAME=$(basename "$MODEL_PATH")

if [ -f "$MODEL_PATH" ]; then
    echo "Model exists: $MODEL_NAME"
    return 0
fi

if [ "$STORAGE_MODE" = "persistent" ]; then
    # Check network volume first
    if [ -f "/workspace/models_cache/$MODEL_NAME" ]; then
        ln -sf "/workspace/models_cache/$MODEL_NAME" "$MODEL_PATH"
        echo "Linked from cache: $MODEL_NAME"
        return 0
    fi
fi

# Download model
echo "Downloading: $MODEL_NAME"
wget -c -O "$MODEL_PATH" "$MODEL_URL"
```

---

## 5. Docker Image Strategy

From `dev/agents/artifacts/doc/docker-image-hosting-options.md`:

### Recommended: GHCR (Free Unlimited Public)

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build and push
docker build -t ghcr.io/USERNAME/hearmeman-extended:latest .
docker push ghcr.io/USERNAME/hearmeman-extended:latest
```

### Image Size Target

| Layer | Contents | Size |
|-------|----------|------|
| Base (runpod/pytorch) | PyTorch, CUDA, SSH | ~8GB |
| Custom Nodes | VibeVoice, SCAIL, ControlNet repos | ~1GB |
| Dependencies | pip packages, git repos | ~2GB |
| **Total Image** | Code only, no models | **~10-12GB** |

Models downloaded on-demand: 60-150GB depending on configuration.

---

## 6. Environment Variables Design

### Required Variables
```bash
# Feature toggles
ENABLE_VIBEVOICE=true        # Install VibeVoice node + model
ENABLE_ZIMAGE=true           # Install Z-Image Turbo components
ENABLE_STEADYDANCER=false    # Install SteadyDancer (large)
ENABLE_SCAIL=false           # Install SCAIL (large)
ENABLE_CONTROLNET=true       # Install ControlNet preprocessors

# Model selection
VIBEVOICE_MODEL=Large        # 1.5B | Large | Large-Q8
CONTROLNET_VARIANT=fp16      # fp16 | full

# Behavior
UPDATE_NODES_ON_START=false  # Git pull custom nodes on start
STORAGE_MODE=auto            # auto | ephemeral | persistent

# Inherited from Hearmeman
WAN_720P=true
WAN_480P=false
```

---

## 7. VRAM Budget Analysis

### 48GB GPU (L40S / A6000)

| Configuration | Estimated VRAM |
|---------------|----------------|
| WAN 2.2 720p alone | 24GB |
| WAN + VibeVoice-Large | 24 + 18 = 42GB (sequential load) |
| WAN + Z-Image | 24 + 16 = 40GB (sequential load) |
| WAN + SteadyDancer | 24 + 28 = swap required |
| WAN + VibeVoice + ControlNet | 24 + 18 + 2 = 44GB |

**Note**: ComfyUI supports model offloading. Only one large model active at a time.

---

## 8. Sources

- Docker Hosting: `dev/agents/artifacts/doc/docker-image-hosting-options.md`
- RunPod Template Guide: `dev/agents/artifacts/doc/runpod-custom-template-guide.md`
- Base Deployment: `dev/agents/artifacts/doc/plan/hearmeman-ephemeral-deploy.md`
- Template Config: `scripts/runpod_template_config.md`
- [VibeVoice HuggingFace](https://huggingface.co/collections/microsoft/vibevoice-68a2ef24a875c44be47b034f)
- [SteadyDancer-14B](https://huggingface.co/MCG-NJU/SteadyDancer-14B)
- [SCAIL-Preview](https://huggingface.co/zai-org/SCAIL-Preview)
- [Z-Image Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
- [ControlNet v1.1](https://huggingface.co/lllyasviel/ControlNet-v1-1)
