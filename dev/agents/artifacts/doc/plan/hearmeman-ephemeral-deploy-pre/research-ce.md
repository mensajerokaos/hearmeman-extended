---
author: oz
model: claude-opus-4-5
date: 2025-12-24 01:32
updated: 2025-12-24 21:55
task: Hearmeman ephemeral deployment best practices research
---

# RunPod Hearmeman Template Deployment Best Practices

Comprehensive research for deploying the Hearmeman "One Click - ComfyUI Wan t2v i2v VACE - CUDA 12.8" template with custom models (VibeVoice, SteadyDancer, SCAIL).

---

## Table of Contents

1. [Hearmeman Template Overview](#1-hearmeman-template-overview)
2. [Environment Variables](#2-environment-variables)
3. [Model Downloads & Sizes](#3-model-downloads--sizes)
4. [VRAM Requirements](#4-vram-requirements)
5. [SSH Connection Workflow](#5-ssh-connection-workflow)
6. [Post-Deploy Scripts](#6-post-deploy-scripts)
7. [Cost Analysis](#7-cost-analysis)
8. [Troubleshooting](#8-troubleshooting)
9. [GPU Comparison (L40S vs A6000)](#9-gpu-comparison-l40s-vs-a6000)
10. [Web Research Sources](#10-web-research-sources)

---

## 1. Hearmeman Template Overview

### Template Details

| Property | Value |
|----------|-------|
| **Template Name** | One Click - ComfyUI Wan t2v i2v VACE - CUDA 12.8 |
| **Template ID** | `758dsjwiqz` |
| **Deploy URL** | https://console.runpod.io/deploy?template=758dsjwiqz |
| **Base Image** | PyTorch 2.8.0 + CUDA 12.8 |
| **Ephemeral Storage** | 450GB (free) |
| **HTTP Port** | 8188 (ComfyUI) |
| **TCP Port** | 22 (SSH) |

### Pre-Installed Components

- ComfyUI + ComfyUI Manager
- WAN 2.1/2.2 support (T2V + I2V)
- VACE (Video Animation Control Engine)
- Kijai's ComfyUI-WanVideoWrapper
- PyTorch 2.8.0, CUDA 12.8, cuDNN 9

### Startup Behavior

1. Container starts with base ComfyUI
2. Reads environment variables
3. Downloads requested models based on flags
4. Starts ComfyUI on port 8188

### Recommended GPUs

| GPU | VRAM | Price/hr | Filter |
|-----|------|----------|--------|
| **L40S** | 48GB | $0.69/hr | CUDA 12.8, 48GB |
| **L40** | 48GB | $0.69/hr | CUDA 12.8, 48GB |
| **A6000** | 48GB | $0.33/hr | CUDA 12.8, 48GB |
| **A40** | 48GB | $0.40/hr | CUDA 12.8, 48GB |

**Important**: Filter for CUDA 12.8 compatibility when selecting GPU.

---

## 2. Environment Variables

### Hearmeman Template Variables

Set these in the RunPod console BEFORE deploying (Edit Template):

| Variable | Default | Options | Description |
|----------|---------|---------|-------------|
| `WAN_480P` | `false` | true/false | Download 480p WAN models |
| `WAN_720P` | `false` | true/false | Download 720p WAN models |
| `WAN_FUN` | `false` | true/false | Download WAN Fun models |
| `VACE` | `false` | true/false | Download VACE models |
| `CIVITAI_TOKEN` | - | string | Your CivitAI API key |
| `LORA_IDS` | - | csv | Comma-separated LoRA version IDs |
| `CHECKPOINT_IDS` | - | csv | Comma-separated checkpoint IDs |

### Recommended Configuration

**For Jose Obscura Documentary**:

```bash
WAN_480P=false        # Skip 480p (too low)
WAN_720P=true         # Enable 720p models
WAN_FUN=false         # Skip Fun variants
VACE=false            # Skip VACE (not needed yet)
CIVITAI_TOKEN=        # Optional: your token
LORA_IDS=             # Optional: specific LoRAs
CHECKPOINT_IDS=       # Optional: specific checkpoints
```

### How to Set Variables

1. Go to https://console.runpod.io/deploy?template=758dsjwiqz
2. Click "Edit Template" (pencil icon)
3. Set environment variables
4. Select GPU (L40S or A6000 recommended)
5. Click "Deploy"

---

## 3. Model Downloads & Sizes

### WAN Models (Pre-Installed by Template)

| Model | Size | Download Time* | Enabled By |
|-------|------|----------------|------------|
| WAN 2.1 T2V-14B FP8 | ~15GB | ~3-5 min | `WAN_720P=true` |
| WAN 2.1 I2V-14B FP8 | ~15GB | ~3-5 min | `WAN_720P=true` |
| WAN 2.2 MoE High/Low Noise | ~28GB each | ~5-8 min | `WAN_720P=true` |
| UMT5 XXL Text Encoder | ~15GB | ~3-5 min | Auto |
| WAN VAE | ~0.5GB | ~10 sec | Auto |

*Download times based on ~500MB/s datacenter speeds

### Custom Models (Manual Install)

#### VibeVoice TTS

| Component | Size | VRAM | Source |
|-----------|------|------|--------|
| VibeVoice-ComfyUI node | ~50MB | - | GitHub |
| VibeVoice-1.5B model | ~3GB | ~6GB | HuggingFace |
| VibeVoice-Large (7B) | ~18GB | ~20GB | HuggingFace |
| VibeVoice-Large-Q8 | ~8GB | ~12GB | HuggingFace |
| VibeVoice-Large-Q4 | ~4GB | ~8GB | HuggingFace |
| TTS dependencies | ~2GB | - | pip |

**Total VibeVoice**: ~20-23GB (with Large model)

**Requirements**:
- Python 3.8+, PyTorch 2.0+, CUDA 11.8+
- bitsandbytes >= 0.48.1 (critical for Q8 model)
- sageattention (optional, for sage attention mode)
- Context: 64K tokens (1.5B) or 32K tokens (Large)
- Max audio duration: ~90 min (1.5B) or ~45 min (Large)

#### SteadyDancer

| Component | Size | VRAM | Source |
|-----------|------|------|--------|
| Wan21_SteadyDancer_fp16.safetensors | ~32GB | 24GB+ | HuggingFace/Kijai |
| Wan21_SteadyDancer_fp8.safetensors | ~16.4GB | 12-16GB | HuggingFace/Kijai |
| SteadyDancer-GGUF | ~8GB | 8-12GB | HuggingFace |

**Download URLs**:
- FP16: https://huggingface.co/Kijai/WanVideo_comfy/tree/main/SteadyDancer
- FP8: https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/tree/main/SteadyDancer

**Current Limitations** (as of Dec 2024):
- Pose detector, alignment, augmentor still missing
- Use vitpose/dwpose and lightx2v as alternatives
- Set CFG to 1.0 when using lightx2v

**Recommended**: FP8 for 24GB, FP16 for 48GB VRAM GPUs

#### SCAIL

| Component | Size | VRAM | Source |
|-----------|------|------|--------|
| Wan21-14B-SCAIL-preview_bf16 | ~28GB | 24GB+ | HuggingFace/Kijai |
| Wan21-14B-SCAIL-preview_fp8 | ~14GB | 12-16GB | HuggingFace/Kijai |
| ComfyUI-SCAIL-Pose node | ~100MB | - | GitHub/Kijai |
| yolov10m.onnx (person detection) | ~50MB | <1GB | Wan-AI |
| vitpose-l-wholebody.onnx | ~200MB | <1GB | HuggingFace |

**Installation**:
```bash
# Required custom nodes (via ComfyUI Manager):
- ComfyUI-WanVideoWrapper
- ComfyUI-WanAnimatePreprocess (for DWpose)
- ComfyUI-SCAIL-Pose (requires taichi, pyrender)

# Manual dependencies:
pip install taichi pyrender
```

**Model Locations**:
- Diffusion models: `ComfyUI/models/diffusion_models/`
- Detection models: `ComfyUI/models/detection/`

**Resolution Guidelines**:
- 480p: Lower VRAM systems (12-16GB)
- 720p: Higher VRAM (24GB+)
- Use "sdpa" attention backend on 2XL/3XL machines

**Note**: SCAIL includes VAE and T5 in checkpoint, may share with WAN.

### Total Storage Requirements

| Scenario | Estimated Size |
|----------|----------------|
| Base Hearmeman (WAN only) | ~60-80GB |
| + VibeVoice | ~80-100GB |
| + SteadyDancer FP16 | ~110-130GB |
| + SCAIL | ~140-160GB |
| All models | ~160-200GB |

**Verdict**: 450GB ephemeral is plenty.

---

## 4. VRAM Requirements

### By Model

| Model | Min VRAM | Recommended | Notes |
|-------|----------|-------------|-------|
| **WAN 2.2 I2V-14B** | 24GB | 48GB | MoE loads both experts |
| **SteadyDancer FP16** | 24GB | 48GB | Best quality |
| **SteadyDancer FP8** | 12-16GB | 24GB | Good quality |
| **SCAIL 14B** | 24GB | 48GB | Full quality |
| **SCAIL GGUF** | 8GB | 16GB | Quantized |
| **VibeVoice-Large** | 16-18GB | 24GB | Voice cloning |
| **VibeVoice-1.5B** | 4-6GB | 8GB | Lighter version |

### Concurrent Workloads

| Combination | Est. VRAM | Possible on 48GB? |
|-------------|-----------|-------------------|
| WAN I2V only | 24-30GB | ✅ Yes |
| WAN + VibeVoice | 30-40GB | ✅ Yes |
| SteadyDancer + VibeVoice | 35-45GB | ✅ Yes (tight) |
| SCAIL + VibeVoice | 35-45GB | ✅ Yes (tight) |
| All three simultaneously | 50-60GB | ❌ No (switch between) |

### Memory Optimization Techniques

1. **Block Swapping** (30-40 blocks): Offloads model layers to CPU RAM
2. **FP8 Quantization**: Reduces VRAM by ~50%
3. **GGUF Versions**: For low VRAM (<16GB)
4. **Sequential Loading**: Load one model at a time, unload before next

---

## 5. SSH Connection Workflow

### Initial Connection Setup

After pod starts:

1. **Get SSH Details** (from RunPod console):
   - Host IP: Varies per session
   - Port: Varies per session (NOT 22)

2. **Update SSH Config** (`~/.ssh/config`):

```bash
Host runpod
    HostName <NEW_IP>
    Port <NEW_PORT>
    User root
    IdentityFile ~/.ssh/id_rsa
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
```

3. **Test Connection**:

```bash
ssh runpod "echo 'Connection OK'"
```

### Automated SSH Update Script

```bash
#!/bin/bash
# update_runpod_ssh.sh

API_KEY=$(grep RUNPOD_API_KEY ~/.zshrc | tail -1 | cut -d'"' -f2)
POD_ID="<your_pod_id>"

# Get pod info
POD_INFO=$(curl -s --request POST \
  --url "https://api.runpod.io/graphql?api_key=$API_KEY" \
  --header 'content-type: application/json' \
  --data '{"query": "query { myself { pods { id runtime { ports { ip publicPort } } } } }"}')

# Extract IP and port
NEW_IP=$(echo "$POD_INFO" | jq -r ".data.myself.pods[] | select(.id==\"$POD_ID\") | .runtime.ports[0].ip")
NEW_PORT=$(echo "$POD_INFO" | jq -r ".data.myself.pods[] | select(.id==\"$POD_ID\") | .runtime.ports[0].publicPort")

# Update SSH config
sed -i "s/HostName .*/HostName $NEW_IP/" ~/.ssh/config
sed -i "s/Port [0-9]*/Port $NEW_PORT/" ~/.ssh/config

echo "Updated SSH config: $NEW_IP:$NEW_PORT"
```

### Post-Connection Commands

```bash
# Check model download status
ssh runpod "tail -100 /var/log/startup.log"

# Check GPU status
ssh runpod "nvidia-smi"

# Check disk space
ssh runpod "df -h"

# Check ComfyUI status
ssh runpod "curl -s localhost:8188/system_stats | head -c 200"
```

---

## 6. Post-Deploy Scripts

### Master Installation Script

Create and run after Hearmeman template starts:

```bash
#!/bin/bash
# install_extra_models.sh
set -e

echo "=== Installing Extra Models for Jose Obscura ==="
echo "Started: $(date)"

# ===== 1. VibeVoice TTS =====
echo "[1/4] Installing VibeVoice..."
cd /workspace/ComfyUI/custom_nodes
if [ ! -d "VibeVoice-ComfyUI" ]; then
    git clone https://github.com/AIFSH/VibeVoice-ComfyUI
    cd VibeVoice-ComfyUI
    pip install -r requirements.txt 2>/dev/null || pip install TTS
    echo "VibeVoice node installed"
else
    echo "VibeVoice already installed"
fi

# ===== 2. SteadyDancer (Dance Animation) =====
echo "[2/4] Installing SteadyDancer..."
cd /workspace/ComfyUI/models/diffusion_models
if [ ! -f "Wan21_SteadyDancer_fp16.safetensors" ]; then
    echo "Downloading SteadyDancer FP16 (28GB)..."
    wget -c https://huggingface.co/MCG-NJU/SteadyDancer-14B/resolve/main/Wan21_SteadyDancer_fp16.safetensors
    echo "SteadyDancer downloaded"
else
    echo "SteadyDancer already installed"
fi

# ===== 3. SCAIL Pose Node =====
echo "[3/4] Installing SCAIL Pose Node..."
cd /workspace/ComfyUI/custom_nodes
if [ ! -d "ComfyUI-SCAIL-Pose" ]; then
    git clone https://github.com/kijai/ComfyUI-SCAIL-Pose
    echo "SCAIL Pose node installed"
else
    echo "SCAIL Pose already installed"
fi

# ===== 4. SCAIL Model (Optional - Large) =====
echo "[4/4] Installing SCAIL Model..."
cd /workspace/ComfyUI/models/diffusion_models
if [ ! -d "SCAIL-Preview" ]; then
    echo "Downloading SCAIL-Preview (28GB)..."
    GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/zai-org/SCAIL-Preview
    cd SCAIL-Preview
    git lfs pull
    echo "SCAIL downloaded"
else
    echo "SCAIL already installed"
fi

# ===== 5. Copy Voice Reference =====
echo "Setting up voice reference..."
cd /workspace/ComfyUI/input
if [ ! -f "es-JoseObscura_woman.mp3" ]; then
    echo "NOTE: Upload voice reference to /workspace/ComfyUI/input/"
fi

echo "=== Installation Complete ==="
echo "Finished: $(date)"
echo ""
echo "Next steps:"
echo "1. Restart ComfyUI: python /workspace/ComfyUI/main.py --listen 0.0.0.0"
echo "2. Upload voice reference to /workspace/ComfyUI/input/"
echo "3. Set up SSH tunnel: ssh -L 8188:localhost:8188 runpod"
```

### Quick Install Commands (Copy-Paste Ready)

#### VibeVoice Only

```bash
cd /workspace/ComfyUI/custom_nodes && \
git clone https://github.com/AIFSH/VibeVoice-ComfyUI && \
pip install TTS
```

#### SteadyDancer Only

```bash
cd /workspace/ComfyUI/models/diffusion_models && \
wget -c https://huggingface.co/MCG-NJU/SteadyDancer-14B/resolve/main/Wan21_SteadyDancer_fp16.safetensors
```

#### SCAIL Only

```bash
cd /workspace/ComfyUI/models/diffusion_models && \
GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/zai-org/SCAIL-Preview && \
cd SCAIL-Preview && git lfs pull

cd /workspace/ComfyUI/custom_nodes && \
git clone https://github.com/kijai/ComfyUI-SCAIL-Pose
```

### Verification Commands

```bash
# Check all installed models
ls -lah /workspace/ComfyUI/models/diffusion_models/

# Check custom nodes
ls /workspace/ComfyUI/custom_nodes/

# Check disk usage
du -sh /workspace/ComfyUI/models/*

# Check VRAM usage
nvidia-smi
```

---

## 7. Cost Analysis

### Per-Session Costs

| GPU | Base Rate | Model Download | Per Hour After |
|-----|-----------|----------------|----------------|
| L40S | $0.69/hr | ~$0.15 (15 min) | $0.69/hr |
| L40 | $0.69/hr | ~$0.15 (15 min) | $0.69/hr |
| A6000 | $0.33/hr | ~$0.07 (15 min) | $0.33/hr |
| A40 | $0.40/hr | ~$0.09 (15 min) | $0.40/hr |

### Model Download Times (Once Per Session)

| Model Set | Size | Time @ 500MB/s | Cost @ $0.69/hr |
|-----------|------|----------------|-----------------|
| Base WAN 720p | ~60GB | ~2 min | $0.02 |
| + VibeVoice | ~20GB | ~1 min | $0.01 |
| + SteadyDancer | ~28GB | ~1 min | $0.01 |
| + SCAIL | ~28GB | ~1 min | $0.01 |
| **Total** | ~136GB | ~5-8 min | ~$0.06-0.10 |

### Ephemeral vs Network Volume Comparison

| Approach | Fixed Cost/mo | Per-Session | Break-even |
|----------|---------------|-------------|------------|
| **Ephemeral** | $0 | $0.06-0.10 download | - |
| **Network Volume 50GB** | $3.50/mo | $0 (cached) | 35-60 sessions |
| **Network Volume 100GB** | $7/mo | $0 (cached) | 70-120 sessions |

**Recommendation**: For <30 sessions/month, ephemeral is cheaper.

### Typical Session Costs

| Session Type | Duration | GPU | Cost |
|--------------|----------|-----|------|
| Quick TTS (VibeVoice) | 30 min | A6000 | ~$0.20 |
| Video gen + TTS | 2 hr | L40S | ~$1.50 |
| Extended editing | 4 hr | L40S | ~$2.90 |
| Full day production | 8 hr | A6000 | ~$2.80 |

---

## 8. Troubleshooting

### Common Issues

#### 1. Connection Refused

**Symptom**: `ssh: connect to host ... port ...: Connection refused`

**Cause**: Pod stopped or SSH port changed

**Solution**:
```bash
# Check pod status via API
curl -s --request POST \
  --url "https://api.runpod.io/graphql?api_key=$API_KEY" \
  --data '{"query": "query { myself { pods { id desiredStatus } } }"}'

# Restart pod if stopped
# Update SSH config with new port
```

#### 2. CUDA Not Initialized

**Symptom**: `torch.cuda.is_available()` returns False

**Cause**: Cold start CUDA driver mismatch

**Solution**:
```bash
ssh runpod "python -c 'import torch; print(torch.cuda.is_available())'"
# If False, restart the pod completely
```

#### 3. Out of VRAM

**Symptom**: `CUDA out of memory`

**Solution**:
```bash
# Check current VRAM usage
ssh runpod "nvidia-smi"

# Use FP8 or GGUF versions
# Enable block swapping in ComfyUI workflow
# Restart ComfyUI to clear GPU memory
ssh runpod "pkill -f 'python.*main.py'; sleep 2; python /workspace/ComfyUI/main.py --listen 0.0.0.0 &"
```

#### 4. Model Download Stuck

**Symptom**: Download at 0% or hanging

**Solution**:
```bash
# Check download progress
ssh runpod "tail -50 /var/log/startup.log"

# Kill and retry with wget resume
ssh runpod "pkill wget; wget -c <URL>"
```

#### 5. ComfyUI Not Responding

**Symptom**: `curl localhost:8188` times out

**Solution**:
```bash
# Check if ComfyUI is running
ssh runpod "ps aux | grep main.py"

# Check logs
ssh runpod "tail -100 /workspace/comfyui.log"

# Restart ComfyUI
ssh runpod "pkill -f main.py; nohup python /workspace/ComfyUI/main.py --listen 0.0.0.0 > /workspace/comfyui.log 2>&1 &"
```

### Health Check Script

```bash
#!/bin/bash
# runpod_health_check.sh

echo "=== RunPod Health Check ==="

# 1. SSH Connection
echo -n "SSH: "
ssh -o ConnectTimeout=5 runpod "echo OK" 2>/dev/null || echo "FAILED"

# 2. GPU Status
echo -n "GPU: "
ssh runpod "nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader" 2>/dev/null || echo "FAILED"

# 3. ComfyUI Status
echo -n "ComfyUI: "
ssh runpod "curl -s localhost:8188/system_stats | head -c 50" 2>/dev/null || echo "NOT RUNNING"

# 4. Disk Space
echo -n "Disk: "
ssh runpod "df -h /workspace | tail -1 | awk '{print \$4 \" free\"}'" 2>/dev/null || echo "FAILED"

echo "=== Done ==="
```

---

## Sources

### Official Documentation
1. [RunPod Documentation](https://docs.runpod.io/)
2. [Hearmeman Templates Spreadsheet](https://docs.google.com/spreadsheets/d/1NfbfZLzE9GIAD5B_y6xjK1IdW95c14oS1JuIG9QihL8)
3. [ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)

### Model Sources
4. [SteadyDancer HuggingFace](https://huggingface.co/MCG-NJU/SteadyDancer-14B)
5. [SCAIL-Preview HuggingFace](https://huggingface.co/zai-org/SCAIL-Preview)
6. [VibeVoice-ComfyUI GitHub](https://github.com/AIFSH/VibeVoice-ComfyUI)

### Project Documentation
7. `~/.claude/commands/runpod.md` - RunPod skill reference
8. `CLAUDE.md` - Project-specific RunPod setup
9. `dev/agents/artifacts/doc/scail-vs-steadydancer.md` - Model comparison
10. `dev/agents/artifacts/doc/wan-nsfw-comparison.md` - WAN capabilities

---

## 9. GPU Comparison (L40S vs A6000)

### Architecture Comparison

| Feature | NVIDIA L40S | NVIDIA RTX A6000 |
|---------|-------------|------------------|
| **Architecture** | Ada Lovelace | Ampere |
| **VRAM** | 48GB GDDR6 | 48GB GDDR6 |
| **CUDA Cores** | 18,176 | 10,752 |
| **Tensor Cores** | 4th Generation | 3rd Generation |
| **RT Cores** | 3rd Generation | 2nd Generation |
| **Power** | 300W | ~300W |
| **Lithography** | 60% more advanced | - |
| **Target Market** | Data Center AI | Workstation |

### L40S Key Features for AI/Video

- **Transformer Engine**: Optimizes FP8/FP16 precision for inference
- **4th Gen Tensor Cores**: Better AI throughput
- **Generative AI Optimized**: Designed for Stable Diffusion, LLM inference
- **Higher CUDA Count**: 69% more cores than A6000

### RunPod Pricing Comparison (2025)

| GPU | Community Cloud | Secure Cloud | Best For |
|-----|-----------------|--------------|----------|
| **L40S** | $0.69/hr | $0.99/hr | Video generation, AI inference |
| **RTX A6000** | ~$0.44/hr | ~$0.79/hr | Budget-conscious workflows |
| **L40** | $0.69/hr | $0.99/hr | Similar to L40S |
| **A40** | $0.40/hr | - | Budget alternative |

### Recommendation for Documentary Production

**L40S is preferred** for WAN 2.2 video generation because:
1. Ada Lovelace optimized for generative AI workloads
2. Higher CUDA core count (69% more than A6000)
3. Transformer Engine for efficient FP8/FP16 operations
4. Same VRAM (48GB) at competitive pricing ($0.69/hr)

**A6000 is acceptable** for:
- TTS-only sessions (VibeVoice)
- Budget constraints
- Non-critical video generation

---

## 10. Web Research Sources

### RunPod Template Documentation
- [Wan2.2/2.1 in 1 click - RunPod Template (CivitAI)](https://civitai.com/articles/11960/wan2221-in-1-click-with-workflows-included-runpod-template)
- [How to Deploy VACE on RunPod (RunPod Blog)](https://www.runpod.io/blog/how-to-deploy-vace-on-runpod)
- [CivitAI Downloader Guide (CivitAI)](https://civitai.com/articles/12333/how-to-use-hearmemans-civitai-downloader-when-deploying-a-runpod-template)
- [RunPod Template - Wan for RTX 5090 (Patreon)](https://www.patreon.com/posts/runpod-template-127804299)

### WAN 2.2 Models & Kijai Wrapper
- [Wan-AI/Wan2.2-T2V-A14B (HuggingFace)](https://huggingface.co/Wan-AI/Wan2.2-T2V-A14B)
- [kijai/ComfyUI-WanVideoWrapper (GitHub)](https://github.com/kijai/ComfyUI-WanVideoWrapper)
- [Wan2.2 ComfyUI Workflow Guide (ComfyUI Wiki)](https://comfyui-wiki.com/en/tutorial/advanced/video/wan2.2/wan2-2)
- [QuantStack/Wan2.2-T2V-A14B-GGUF (HuggingFace)](https://huggingface.co/QuantStack/Wan2.2-T2V-A14B-GGUF)
- [Kijai/WanVideo_comfy (HuggingFace)](https://huggingface.co/Kijai/WanVideo_comfy)

### VibeVoice TTS
- [ComfyUI-VibeVoice (GitHub - wildminder)](https://github.com/wildminder/ComfyUI-VibeVoice)
- [VibeVoice-ComfyUI (GitHub - Enemyx-net)](https://github.com/Enemyx-net/VibeVoice-ComfyUI)
- [Multi-Speaker Audio with VibeVoice (Next Diffusion)](https://www.nextdiffusion.ai/tutorials/multi-speaker-audio-generation-microsoft-vibevoice-comfyui)
- [VibeVoice Tutorial (lilys.ai)](https://lilys.ai/notes/en/comfyui-tutorial-20251031/comfyui-tutorial-vibevoice-text-to-speech)

### SteadyDancer
- [MCG-NJU/SteadyDancer (GitHub)](https://github.com/MCG-NJU/SteadyDancer)
- [Kijai/WanVideo_comfy_fp8_scaled - SteadyDancer (HuggingFace)](https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/tree/main/SteadyDancer)
- [Steady Dancer Wan 2.1 Tutorial](https://www.stablediffusiontutorials.com/2025/11/steady-dancer.html)
- [SteadyDancer in ComfyUI (RunComfy)](https://www.runcomfy.com/comfyui-workflows/steadydancer-in-comfyui-i2v-human-animation-workflow)
- [SteadyDancer workflow discussion (HuggingFace)](https://huggingface.co/Kijai/WanVideo_comfy/discussions/110)

### SCAIL
- [kijai/ComfyUI-SCAIL-Pose (GitHub)](https://github.com/kijai/ComfyUI-SCAIL-Pose)
- [zai-org/SCAIL (GitHub - Official)](https://github.com/zai-org/SCAIL)
- [SCAIL Model in ComfyUI Workflow (RunComfy)](https://www.runcomfy.com/comfyui-workflows/scail-model-in-comfyui-pose-based-character-animation-workflow)
- [Wan SCAIL Pose Tutorial](https://www.stablediffusiontutorials.com/2025/12/scail-pose.html)

### GPU Specifications & Pricing
- [L40S vs RTX A6000 Benchmark (RunPod)](https://www.runpod.io/gpu-compare/l40s-vs-rtx-a6000)
- [Comparing NVIDIA AI GPUs (NADDOD)](https://www.naddod.com/blog/comparing-nvidia-top-ai-gpus-h100-a100-a6000-and-l40s)
- [RunPod Pricing](https://www.runpod.io/pricing)
- [GPU Price Comparison 2025 (getdeploying.com)](https://getdeploying.com/reference/cloud-gpu)

### Storage & Best Practices
- [RunPod Storage Options (Documentation)](https://docs.runpod.io/pods/storage/types)
- [Avoid Pod Errors - Resource Selection (RunPod Blog)](https://www.runpod.io/blog/avoid-pod-errors-runpod-resources)
- [Storage and Data Management (DeepWiki)](https://deepwiki.com/runpod/docs/3.4-storage-and-data-management)

---

*Document generated: 2025-12-24*
*Updated: 2025-12-24 21:55 (added GPU comparison and web sources)*
*Project: Jose Obscura - La Maquila Erotica Documentary*
