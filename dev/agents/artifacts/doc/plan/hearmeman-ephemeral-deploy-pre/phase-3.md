---
author: oz
model: claude-opus-4-5
date: 2025-12-24 01:42
task: Phase 3 expansion - Model installation for Hearmeman ephemeral deployment
---

# Phase 3: Model Installation (Expanded)

**Objective**: Install custom models not included in Hearmeman template.
**Duration**: 10-15 minutes (parallel downloads)
**Prerequisites**: Phase 1 & 2 complete (pod running, SSH connected)

---

## Table of Contents

1. [Quick Start (Copy-Paste)](#1-quick-start-copy-paste)
2. [VibeVoice Installation](#2-vibevoice-installation)
3. [SteadyDancer Installation](#3-steadydancer-installation)
4. [SCAIL Installation (Optional)](#4-scail-installation-optional)
5. [Voice Reference Sync](#5-voice-reference-sync)
6. [Monitoring & Progress](#6-monitoring--progress)
7. [Disk Space Management](#7-disk-space-management)
8. [Timing Estimates](#8-timing-estimates)

---

## 1. Quick Start (Copy-Paste)

### Complete Installation Script

Copy this entire script to pod and run:

```bash
#!/bin/bash
# install_extra_models.sh - Full post-deploy model installation
# Usage: ssh runpod "bash -s" < install_extra_models.sh

set -e

echo "============================================"
echo "=== Jose Obscura - Model Installation ==="
echo "============================================"
echo "Started: $(date)"
echo ""

# Track timing
START_TIME=$(date +%s)

# Disk check
echo "[Disk] Checking available space..."
DISK_FREE=$(df -BG /workspace | tail -1 | awk '{print $4}' | tr -d 'G')
echo "Available: ${DISK_FREE}GB"
if [ "$DISK_FREE" -lt 100 ]; then
    echo "WARNING: Less than 100GB free. SCAIL installation may fail."
fi
echo ""

# ============================================
# 1. VibeVoice TTS (P0 - Critical)
# ============================================
echo "[1/4] Installing VibeVoice..."
VV_START=$(date +%s)

cd /workspace/ComfyUI/custom_nodes
if [ ! -d "VibeVoice-ComfyUI" ]; then
    echo "  Cloning VibeVoice-ComfyUI node..."
    git clone --depth 1 https://github.com/AIFSH/VibeVoice-ComfyUI

    cd VibeVoice-ComfyUI
    echo "  Installing dependencies..."
    pip install -q TTS 2>/dev/null || pip install TTS

    # Install additional requirements if they exist
    if [ -f "requirements.txt" ]; then
        pip install -q -r requirements.txt 2>/dev/null || true
    fi

    VV_END=$(date +%s)
    echo "  VibeVoice installed ($(($VV_END - $VV_START))s)"
else
    echo "  VibeVoice already present, skipping"
fi
echo ""

# ============================================
# 2. VibeVoice-Large Model (P0 - Critical)
# ============================================
echo "[2/4] Downloading VibeVoice-Large model..."
VV_MODEL_START=$(date +%s)

# VibeVoice stores models in HuggingFace cache or local paths
# The model downloads automatically on first use, but we can pre-download
cd /workspace/ComfyUI/custom_nodes/VibeVoice-ComfyUI

# Pre-download the VibeVoice model via Python
python -c "
from huggingface_hub import snapshot_download
import os

# VibeVoice-Large (18GB)
print('  Downloading VibeVoice-Large from HuggingFace...')
try:
    snapshot_download(
        repo_id='AIFSH/VibeVoice-Large',
        local_dir='/workspace/ComfyUI/models/vibevoice/VibeVoice-Large',
        local_dir_use_symlinks=False,
        resume_download=True
    )
    print('  VibeVoice-Large downloaded successfully')
except Exception as e:
    print(f'  Note: Will download on first use. {e}')
" 2>&1 || echo "  Model will download on first ComfyUI use"

VV_MODEL_END=$(date +%s)
echo "  Model step complete ($(($VV_MODEL_END - $VV_MODEL_START))s)"
echo ""

# ============================================
# 3. SteadyDancer (P1)
# ============================================
echo "[3/4] Downloading SteadyDancer..."
SD_START=$(date +%s)

cd /workspace/ComfyUI/models/diffusion_models
if [ ! -f "Wan21_SteadyDancer_fp16.safetensors" ]; then
    echo "  Downloading SteadyDancer FP16 (28GB)..."
    echo "  URL: huggingface.co/MCG-NJU/SteadyDancer-14B"

    wget -c --progress=bar:force:noscroll \
        -O Wan21_SteadyDancer_fp16.safetensors \
        "https://huggingface.co/MCG-NJU/SteadyDancer-14B/resolve/main/Wan21_SteadyDancer_fp16.safetensors"

    SD_END=$(date +%s)
    echo "  SteadyDancer downloaded ($(($SD_END - $SD_START))s)"
else
    echo "  SteadyDancer already present, skipping"
    ls -lh Wan21_SteadyDancer_fp16.safetensors
fi
echo ""

# ============================================
# 4. SCAIL (P2 - Optional)
# ============================================
echo "[4/4] Installing SCAIL (optional)..."
SCAIL_START=$(date +%s)

# Check disk space before SCAIL (requires 28GB)
DISK_FREE=$(df -BG /workspace | tail -1 | awk '{print $4}' | tr -d 'G')
if [ "$DISK_FREE" -lt 35 ]; then
    echo "  SKIP: Insufficient disk space (${DISK_FREE}GB free, need 35GB)"
    echo "  To install SCAIL later: see Phase 3 docs"
else
    # SCAIL Pose ComfyUI Node
    cd /workspace/ComfyUI/custom_nodes
    if [ ! -d "ComfyUI-SCAIL-Pose" ]; then
        echo "  Cloning ComfyUI-SCAIL-Pose node..."
        git clone --depth 1 https://github.com/kijai/ComfyUI-SCAIL-Pose
        echo "  SCAIL Pose node installed"
    else
        echo "  SCAIL Pose node already present"
    fi

    # SCAIL Model (28GB)
    cd /workspace/ComfyUI/models/diffusion_models
    if [ ! -d "SCAIL-Preview" ]; then
        echo "  Downloading SCAIL-Preview model (28GB)..."
        echo "  Using Git LFS (may take 3-5 min)..."

        # Clone without LFS first (fast)
        GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/zai-org/SCAIL-Preview

        # Then pull LFS files
        cd SCAIL-Preview
        git lfs pull

        SCAIL_END=$(date +%s)
        echo "  SCAIL downloaded ($(($SCAIL_END - $SCAIL_START))s)"
    else
        echo "  SCAIL already present, skipping"
        du -sh SCAIL-Preview
    fi
fi
echo ""

# ============================================
# Summary
# ============================================
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))

echo "============================================"
echo "=== Installation Complete ==="
echo "============================================"
echo ""
echo "Duration: ${TOTAL_DURATION}s ($((TOTAL_DURATION / 60))m $((TOTAL_DURATION % 60))s)"
echo ""
echo "Installed models:"
echo "-----------------"
du -sh /workspace/ComfyUI/models/diffusion_models/* 2>/dev/null || true
du -sh /workspace/ComfyUI/models/vibevoice/* 2>/dev/null || true
echo ""
echo "Custom nodes:"
echo "-------------"
ls -1 /workspace/ComfyUI/custom_nodes/
echo ""
echo "Disk usage:"
echo "-----------"
df -h /workspace
echo ""
echo "Next steps:"
echo "1. Sync voice reference: scp voice.mp3 runpod:/workspace/ComfyUI/input/"
echo "2. Restart ComfyUI: pkill -f main.py; nohup python /workspace/ComfyUI/main.py --listen 0.0.0.0 > /workspace/comfyui.log 2>&1 &"
echo "3. Verify: curl localhost:8188/system_stats"
```

### One-Liner Execution

```bash
# From local machine
cat scripts/install_extra_models.sh | ssh runpod "bash -s"

# Or create on pod and run
ssh runpod "cat > /workspace/install_extra_models.sh" < scripts/install_extra_models.sh
ssh runpod "chmod +x /workspace/install_extra_models.sh && /workspace/install_extra_models.sh"
```

---

## 2. VibeVoice Installation

### 2.1 Clone ComfyUI-VibeVoice Node

```bash
cd /workspace/ComfyUI/custom_nodes

# Clone the official VibeVoice ComfyUI node
git clone --depth 1 https://github.com/AIFSH/VibeVoice-ComfyUI

# Enter directory
cd VibeVoice-ComfyUI
```

**Repository**: https://github.com/AIFSH/VibeVoice-ComfyUI
**Size**: ~50MB
**Time**: <30 seconds

### 2.2 Install Dependencies

```bash
cd /workspace/ComfyUI/custom_nodes/VibeVoice-ComfyUI

# Primary dependency: TTS library (Coqui)
pip install TTS

# If requirements.txt exists, install those too
pip install -r requirements.txt 2>/dev/null || true

# Additional audio dependencies (usually pre-installed)
pip install soundfile librosa 2>/dev/null || true
```

**Key Dependencies**:
| Package | Version | Size | Purpose |
|---------|---------|------|---------|
| TTS | >=0.22 | ~2GB | Coqui text-to-speech |
| torch | >=2.0 | (pre-installed) | PyTorch |
| transformers | >=4.36 | (pre-installed) | HuggingFace |
| soundfile | >=0.12 | ~1MB | Audio I/O |
| librosa | >=0.10 | ~2MB | Audio processing |

**Time**: 1-2 minutes

### 2.3 Download VibeVoice-Large Model

The VibeVoice-Large model (18GB) provides the best voice cloning quality.

```bash
# Option A: Pre-download via Python (recommended)
python -c "
from huggingface_hub import snapshot_download

print('Downloading VibeVoice-Large (18GB)...')
snapshot_download(
    repo_id='AIFSH/VibeVoice-Large',
    local_dir='/workspace/ComfyUI/models/vibevoice/VibeVoice-Large',
    local_dir_use_symlinks=False,
    resume_download=True
)
print('Download complete!')
"
```

```bash
# Option B: Direct wget (if HF hub fails)
mkdir -p /workspace/ComfyUI/models/vibevoice
cd /workspace/ComfyUI/models/vibevoice

# Download model files
wget -c https://huggingface.co/AIFSH/VibeVoice-Large/resolve/main/model.safetensors
wget -c https://huggingface.co/AIFSH/VibeVoice-Large/resolve/main/config.json
```

**Model Details**:
| File | Size | Purpose |
|------|------|---------|
| model.safetensors | ~18GB | Main model weights |
| config.json | ~2KB | Model configuration |
| tokenizer/* | ~5MB | Text tokenization |

**Time**: 2-4 minutes @ 500MB/s datacenter speeds

### 2.4 Verify VibeVoice Installation

```bash
# Check node installed
ls -la /workspace/ComfyUI/custom_nodes/VibeVoice-ComfyUI/

# Check model downloaded
du -sh /workspace/ComfyUI/models/vibevoice/VibeVoice-Large/

# Test import
python -c "import sys; sys.path.insert(0, '/workspace/ComfyUI'); from custom_nodes import *; print('Nodes loaded')"
```

---

## 3. SteadyDancer Installation

### 3.1 Download FP16 Safetensors (28GB)

SteadyDancer extends WAN 2.1 for dance/motion video generation.

```bash
cd /workspace/ComfyUI/models/diffusion_models

# Download SteadyDancer FP16 (best quality for 48GB VRAM)
wget -c --progress=bar:force:noscroll \
    -O Wan21_SteadyDancer_fp16.safetensors \
    "https://huggingface.co/MCG-NJU/SteadyDancer-14B/resolve/main/Wan21_SteadyDancer_fp16.safetensors"
```

**Download Options**:
| Version | Size | VRAM | Quality | Command |
|---------|------|------|---------|---------|
| FP16 (recommended) | 28GB | 24-48GB | Best | `wget ...fp16.safetensors` |
| FP8 | 14GB | 12-24GB | Good | `wget ...fp8.safetensors` |
| GGUF | 8GB | 8-16GB | OK | `wget ...gguf` |

**Time**: 1-2 minutes @ 500MB/s

### 3.2 Model Placement

SteadyDancer must be placed in `diffusion_models` (not `checkpoints`):

```
/workspace/ComfyUI/models/
├── diffusion_models/           # <-- SteadyDancer goes here
│   ├── wan-*.safetensors       # WAN 2.2 models (from Hearmeman)
│   └── Wan21_SteadyDancer_fp16.safetensors  # <-- SteadyDancer
├── checkpoints/                # NOT here
└── clip/text_encoders/         # Shared T5 encoder
```

### 3.3 Verify SteadyDancer

```bash
# Check file exists and size
ls -lh /workspace/ComfyUI/models/diffusion_models/Wan21_SteadyDancer_fp16.safetensors

# Expected: ~28GB
# -rw-r--r-- 1 root root 28G Dec 24 01:45 Wan21_SteadyDancer_fp16.safetensors
```

---

## 4. SCAIL Installation (Optional)

SCAIL (Scalable AI for Language and Images) provides facial expression control. Install only if needed and disk space permits.

### 4.1 Check Prerequisites

```bash
# Verify disk space (need 35GB free for SCAIL)
df -h /workspace

# If less than 35GB free, skip SCAIL or remove unused models
```

### 4.2 Install SCAIL Pose Node

```bash
cd /workspace/ComfyUI/custom_nodes

# Clone Kijai's SCAIL Pose wrapper
git clone --depth 1 https://github.com/kijai/ComfyUI-SCAIL-Pose

# Install any dependencies
cd ComfyUI-SCAIL-Pose
pip install -r requirements.txt 2>/dev/null || true
```

**Repository**: https://github.com/kijai/ComfyUI-SCAIL-Pose
**Time**: <30 seconds

### 4.3 Download SCAIL Model via Git LFS

```bash
cd /workspace/ComfyUI/models/diffusion_models

# Step 1: Clone repo without LFS files (fast)
GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/zai-org/SCAIL-Preview

# Step 2: Pull LFS files (downloads 28GB)
cd SCAIL-Preview
git lfs pull
```

**Why two steps?**
- `GIT_LFS_SKIP_SMUDGE=1` clones repo structure instantly
- `git lfs pull` downloads only the large files
- Allows resume if interrupted

**Model Contents**:
| File | Size | Purpose |
|------|------|---------|
| SCAIL-Preview-14B.safetensors | ~28GB | Main model |
| VAE (embedded) | included | Video encoding |
| config.json | ~2KB | Settings |

**Time**: 2-4 minutes @ 500MB/s

### 4.4 Alternative: GGUF Version (8GB)

If disk space is limited:

```bash
cd /workspace/ComfyUI/models/diffusion_models

# Download GGUF quantized version
wget -c https://huggingface.co/zai-org/SCAIL-Preview-GGUF/resolve/main/SCAIL-Preview-Q4_K_M.gguf
```

### 4.5 Verify SCAIL Installation

```bash
# Check node
ls /workspace/ComfyUI/custom_nodes/ComfyUI-SCAIL-Pose/

# Check model
du -sh /workspace/ComfyUI/models/diffusion_models/SCAIL-Preview/

# List contents
ls -la /workspace/ComfyUI/models/diffusion_models/SCAIL-Preview/
```

---

## 5. Voice Reference Sync

### 5.1 Upload Voice Reference File

The Jose Obscura narrator voice file must be uploaded to the pod:

```bash
# From local Windows/WSL
scp "/mnt/r/Jose Obscura/Documental MACQ/Audio/VO/es-JoseObscura_woman.mp3" \
    runpod:/workspace/ComfyUI/input/

# Or from NAS path
scp "R:\Jose Obscura\Documental MACQ\Audio\VO\es-JoseObscura_woman.mp3" \
    runpod:/workspace/ComfyUI/input/

# Or from Linux mount
scp ~/mnt/nas/Jose\ Obscura/Documental\ MACQ/Audio/VO/es-JoseObscura_woman.mp3 \
    runpod:/workspace/ComfyUI/input/
```

### 5.2 Verify Voice File

```bash
ssh runpod "ls -la /workspace/ComfyUI/input/*.mp3"

# Check file is valid audio
ssh runpod "file /workspace/ComfyUI/input/es-JoseObscura_woman.mp3"

# Get duration (if ffprobe available)
ssh runpod "ffprobe -v error -show_entries format=duration -of csv=p=0 /workspace/ComfyUI/input/es-JoseObscura_woman.mp3"
```

### 5.3 Voice File Requirements

For best VibeVoice results:
| Property | Recommended | Notes |
|----------|-------------|-------|
| Format | MP3/WAV | MP3 preferred for size |
| Duration | 10-30 seconds | Longer = better cloning |
| Sample Rate | 44.1kHz | Standard audio rate |
| Channels | Mono | Stereo works but mono preferred |
| Content | Clear speech | Minimal background noise |

---

## 6. Monitoring & Progress

### 6.1 Real-Time Download Monitoring

```bash
# Watch download progress in another terminal
ssh runpod "watch -n 2 'ls -lh /workspace/ComfyUI/models/diffusion_models/*.safetensors 2>/dev/null; df -h /workspace'"
```

### 6.2 Background Download with Logging

```bash
# Run installation in background with full logs
ssh runpod "nohup /workspace/install_extra_models.sh > /workspace/install.log 2>&1 &"

# Monitor log
ssh runpod "tail -f /workspace/install.log"
```

### 6.3 Check Running Downloads

```bash
# Check active wget processes
ssh runpod "ps aux | grep wget"

# Check network throughput
ssh runpod "ifstat 1 5"

# Check CPU/Memory during install
ssh runpod "top -bn1 | head -20"
```

### 6.4 Download Resume

All downloads use `-c` flag for resume capability:

```bash
# If download interrupted, just re-run the same command
wget -c https://huggingface.co/MCG-NJU/SteadyDancer-14B/resolve/main/Wan21_SteadyDancer_fp16.safetensors

# For git lfs, re-run pull
cd /workspace/ComfyUI/models/diffusion_models/SCAIL-Preview
git lfs pull
```

---

## 7. Disk Space Management

### 7.1 Space Requirements

| Component | Size | Cumulative |
|-----------|------|------------|
| Base System | ~50GB | 50GB |
| WAN 720p (Hearmeman) | ~60GB | 110GB |
| VibeVoice | ~20GB | 130GB |
| SteadyDancer FP16 | ~28GB | 158GB |
| SCAIL | ~28GB | 186GB |
| **Total** | | **~186GB** |
| **Available (Ephemeral)** | | **450GB** |
| **Headroom** | | **~264GB** |

### 7.2 Check Current Usage

```bash
# Disk usage summary
ssh runpod "df -h /workspace"

# By directory
ssh runpod "du -sh /workspace/ComfyUI/models/*"

# Detailed breakdown
ssh runpod "du -sh /workspace/ComfyUI/models/diffusion_models/*"
```

### 7.3 Free Space If Needed

```bash
# Remove pip cache (can save 2-5GB)
ssh runpod "rm -rf /root/.cache/pip"

# Remove HuggingFace cache duplicates
ssh runpod "rm -rf /root/.cache/huggingface/hub/*-blobs-*"

# Remove old logs
ssh runpod "rm -f /workspace/*.log"

# If SCAIL not needed, skip or remove
ssh runpod "rm -rf /workspace/ComfyUI/models/diffusion_models/SCAIL-Preview"
```

### 7.4 Model Size Comparison

Choose model variants based on disk constraints:

| Model | Full (FP16) | Quantized (FP8/GGUF) | Savings |
|-------|-------------|----------------------|---------|
| SteadyDancer | 28GB | 8GB (GGUF) | 20GB |
| SCAIL | 28GB | 8GB (GGUF) | 20GB |
| VibeVoice | 18GB (Large) | 3GB (1.5B) | 15GB |

---

## 8. Timing Estimates

### 8.1 Per-Component Timing

| Step | Size | Time @ 500MB/s | Notes |
|------|------|----------------|-------|
| VibeVoice node clone | 50MB | <30s | Git clone |
| VibeVoice pip install | 2GB | 1-2 min | TTS + deps |
| VibeVoice-Large download | 18GB | 2-3 min | HuggingFace |
| SteadyDancer FP16 | 28GB | 1-2 min | wget |
| SCAIL Pose node | 50MB | <30s | Git clone |
| SCAIL model | 28GB | 2-4 min | Git LFS |
| Voice reference sync | <10MB | <5s | scp |

### 8.2 Parallel vs Sequential

**Sequential (safer, easier to debug)**:
```
VibeVoice: 4-5 min
SteadyDancer: 2 min
SCAIL: 5 min
Voice sync: <1 min
---
Total: ~12 min
```

**Parallel (faster)**:
```bash
# Run all downloads in parallel
ssh runpod "
  cd /workspace/ComfyUI/models/diffusion_models && \
  wget -c -q https://...steadydancer.safetensors &
  git lfs pull SCAIL-Preview &
  wait
"
# Total: ~5-6 min (limited by largest download)
```

### 8.3 Total Phase 3 Duration

| Scenario | Time |
|----------|------|
| Minimum (VibeVoice only) | 5 min |
| Standard (VibeVoice + SteadyDancer) | 8 min |
| Full (all models) | 12-15 min |
| With issues/retries | 20 min |

---

## Quick Reference Commands

### Copy-Paste One-Liners

```bash
# Full installation
ssh runpod "curl -sL https://example.com/install.sh | bash"  # If hosted

# VibeVoice only
ssh runpod "cd /workspace/ComfyUI/custom_nodes && git clone https://github.com/AIFSH/VibeVoice-ComfyUI && pip install TTS"

# SteadyDancer only
ssh runpod "cd /workspace/ComfyUI/models/diffusion_models && wget -c https://huggingface.co/MCG-NJU/SteadyDancer-14B/resolve/main/Wan21_SteadyDancer_fp16.safetensors"

# Voice sync
scp voice.mp3 runpod:/workspace/ComfyUI/input/

# Restart ComfyUI after install
ssh runpod "pkill -f main.py; nohup python /workspace/ComfyUI/main.py --listen 0.0.0.0 > /workspace/comfyui.log 2>&1 &"

# Verify everything
ssh runpod "ls -la /workspace/ComfyUI/custom_nodes/ && ls -lh /workspace/ComfyUI/models/diffusion_models/*.safetensors && ls /workspace/ComfyUI/input/*.mp3"
```

---

## Troubleshooting

### Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| Download stalls | Progress stuck at X% | Re-run with `-c` for resume |
| Git LFS fails | "Smudge filter" error | `git lfs install && git lfs pull` |
| Pip install fails | Module not found | `pip install --upgrade pip && pip install TTS` |
| Disk full | "No space left" | Remove unused models, use GGUF versions |
| Import error | "No module named" | Restart ComfyUI after node install |

### Error Recovery

```bash
# If VibeVoice install fails
ssh runpod "cd /workspace/ComfyUI/custom_nodes && rm -rf VibeVoice-ComfyUI && git clone https://github.com/AIFSH/VibeVoice-ComfyUI"

# If wget fails mid-download
ssh runpod "cd /workspace/ComfyUI/models/diffusion_models && rm -f Wan21_SteadyDancer_fp16.safetensors.tmp && wget -c ..."

# If SCAIL LFS fails
ssh runpod "cd /workspace/ComfyUI/models/diffusion_models/SCAIL-Preview && git lfs fetch --all && git lfs checkout"
```

---

*Phase 3 Document | Jose Obscura - La Maquila Erotica Documentary*
*Updated: 2025-12-24*
