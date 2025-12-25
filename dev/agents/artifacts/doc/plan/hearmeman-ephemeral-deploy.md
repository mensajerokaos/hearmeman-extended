---
author: oz
model: claude-opus-4-5
date: 2025-12-24 01:46
task: Unified PRD - Hearmeman RunPod ephemeral deployment with custom models
---

# Hearmeman Ephemeral Deployment PRD

**Project**: José Obscura - La Maquila Erótica Documentary
**Template**: Hearmeman "One Click - ComfyUI Wan t2v i2v VACE - CUDA 12.8"
**Version**: 1.0
**Last Updated**: 2025-12-24

---

## 1. Executive Summary

This PRD defines the deployment strategy for RunPod ephemeral GPU pods using the Hearmeman community template for AI-powered documentary production. The solution enables WAN 2.2 video generation, VibeVoice TTS voice cloning, and optional SteadyDancer/SCAIL motion models on 48GB VRAM GPUs with zero fixed infrastructure costs.

**Scope**: Deploy Hearmeman template with 720p WAN models, install VibeVoice for narrator voice cloning, optionally add SteadyDancer for dance/motion video. Uses 450GB ephemeral storage (free) instead of network volumes, optimizing for <30 sessions/month usage patterns.

**Key Metrics**: 15-25 minute total setup time, ~$0.10 download overhead per session, $0.33-0.69/hour GPU cost, 48GB VRAM utilization for concurrent TTS and video generation.

---

## 2. Quick Start

**TL;DR for experienced users:**

```bash
# 1. Deploy template (browser)
# https://console.runpod.io/deploy?template=758dsjwiqz
# Set: WAN_720P=true | GPU: L40S or A6000 (48GB)

# 2. Update SSH config with new IP/port from console
sed -i "s/HostName .*/HostName <IP>/" ~/.ssh/config
sed -i "s/Port [0-9]*/Port <PORT>/" ~/.ssh/config

# 3. Install extra models
ssh runpod "cd /workspace/ComfyUI/custom_nodes && git clone https://github.com/AIFSH/VibeVoice-ComfyUI && pip install TTS"
ssh runpod "cd /workspace/ComfyUI/models/diffusion_models && wget -c https://huggingface.co/MCG-NJU/SteadyDancer-14B/resolve/main/Wan21_SteadyDancer_fp16.safetensors"

# 4. Sync voice reference
scp voice.mp3 runpod:/workspace/ComfyUI/input/

# 5. Create tunnel & access ComfyUI
ssh -L 8188:localhost:8188 runpod
# Browser: http://localhost:8188
```

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LOCAL WORKSTATION                                  │
│  ┌─────────────────┐    ┌──────────────────┐    ┌────────────────────────┐  │
│  │ ~/.ssh/config   │    │ Voice Reference  │    │ ComfyUI Workflows      │  │
│  │ (runpod alias)  │    │ (.mp3 files)     │    │ (tts, steadydancer)    │  │
│  └────────┬────────┘    └────────┬─────────┘    └───────────┬────────────┘  │
│           │                      │                          │               │
└───────────┼──────────────────────┼──────────────────────────┼───────────────┘
            │                      │                          │
            │ SSH (dynamic port)   │ scp                      │ scp
            │                      │                          │
            ▼                      ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RUNPOD POD (Ephemeral)                            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           Hearmeman Template                        │   │
│  │   PyTorch 2.8.0 │ CUDA 12.8 │ ComfyUI │ WAN 2.2 (720p)             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ GPU: L40S / A6000 (48GB VRAM)                                       │   │
│  │                                                                     │   │
│  │   VRAM Allocation:                                                  │   │
│  │   ┌─────────────────┬─────────────────┬─────────────────────────┐   │   │
│  │   │ WAN 2.2 (24GB)  │ VibeVoice (18GB)│ SteadyDancer (swap)     │   │   │
│  │   └─────────────────┴─────────────────┴─────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Ephemeral Storage: 450GB                                              │ │
│  │                                                                       │ │
│  │  /workspace/                                                          │ │
│  │  ├── ComfyUI/                                                         │ │
│  │  │   ├── models/                                                      │ │
│  │  │   │   ├── diffusion_models/                                        │ │
│  │  │   │   │   ├── wan-2.2-720p-*.safetensors (~60GB)                  │ │
│  │  │   │   │   ├── Wan21_SteadyDancer_fp16.safetensors (28GB)          │ │
│  │  │   │   │   └── SCAIL-Preview/ (28GB)                               │ │
│  │  │   │   └── clip/text_encoders/ (15GB)                              │ │
│  │  │   ├── custom_nodes/                                                │ │
│  │  │   │   ├── VibeVoice-ComfyUI/                                      │ │
│  │  │   │   └── ComfyUI-SCAIL-Pose/                                     │ │
│  │  │   ├── input/                                                       │ │
│  │  │   │   └── es-JoseObscura_woman.mp3 (voice ref)                    │ │
│  │  │   └── output/tts_output/                                           │ │
│  │  ├── scripts/cuda_init.sh                                             │ │
│  │  ├── start_comfyui.sh                                                 │ │
│  │  └── comfyui.log                                                      │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Ports: 8188 (ComfyUI HTTP) │ 22 (SSH)                                     │
└─────────────────────────────────────────────────────────────────────────────┘
            │
            │ SSH Tunnel (localhost:8188)
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              WEB BROWSER                                    │
│  http://localhost:8188 → ComfyUI Interface                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| RunPod Account | Active with credits | $10+ balance |
| SSH Key | Ed25519 or RSA | Ed25519 (`~/.ssh/id_ed25519`) |
| Local Storage | 100MB (scripts/workflows) | 1GB |
| Browser | Any modern | Chrome/Firefox |
| Network | Stable broadband | Low-latency connection |

### RunPod Account Setup

1. **Create Account**: https://runpod.io (if not existing)
2. **Add SSH Key**: Settings → SSH Public Keys
   ```bash
   # Get your public key
   cat ~/.ssh/id_ed25519.pub
   ```
3. **Add Credits**: Billing → Add Funds ($10+ recommended)
4. **Verify**: GPU pods accessible in Community Cloud

### Local SSH Config Template

Add to `~/.ssh/config`:

```ssh-config
# RunPod - Hearmeman Ephemeral Pod
# Note: HostName and Port change on each pod restart
Host runpod
    HostName PLACEHOLDER_IP
    Port PLACEHOLDER_PORT
    User root
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

---

## 5. Phase 1: Template Deployment

### 5.1 Deploy via Console

| Step | Action | Details |
|------|--------|---------|
| 1 | Open deploy URL | https://console.runpod.io/deploy?template=758dsjwiqz |
| 2 | Edit Template | Click pencil icon → Set environment variables |
| 3 | Select GPU | Filter: 48GB VRAM, CUDA 12.8 → L40S or A6000 |
| 4 | Set pod name | `jose-wan-720p` (optional) |
| 5 | Click Deploy | Wait for "Running" status |

### 5.2 Environment Variables

```bash
WAN_480P=false        # Skip low resolution
WAN_720P=true         # Enable 720p models ← REQUIRED
WAN_FUN=false         # Skip Fun variants
VACE=false            # Skip VACE (optional)
CIVITAI_TOKEN=        # Optional: CivitAI API key
LORA_IDS=             # Optional: comma-separated LoRA IDs
CHECKPOINT_IDS=       # Optional: checkpoint IDs
```

### 5.3 GPU Selection Guide

| GPU | VRAM | Price/hr | Availability | Recommendation |
|-----|------|----------|--------------|----------------|
| **L40S** | 48GB | $0.69/hr | High | Best for production |
| **L40** | 48GB | $0.69/hr | Medium | Good alternative |
| **A6000** | 48GB | $0.33/hr | Medium | Budget option |
| **A40** | 48GB | $0.40/hr | Low | Acceptable |

### 5.4 Expected Downloads (Automatic)

| Model | Size | Time |
|-------|------|------|
| WAN 2.2 T2V-14B FP8 | ~15GB | 2-3 min |
| WAN 2.2 I2V-14B FP8 | ~15GB | 2-3 min |
| WAN 2.2 MoE High/Low | ~28GB ea | 5-8 min |
| UMT5 XXL Text Encoder | ~15GB | 2-3 min |
| WAN VAE | ~0.5GB | <10s |

**Total Phase 1 Duration**: 15-20 minutes

---

## 6. Phase 2: SSH Setup

### 6.1 Get Connection Details

1. Go to RunPod Console → Pods
2. Find your pod → Click "Connect"
3. Copy SSH command: `ssh root@<IP> -p <PORT> -i ~/.ssh/id_ed25519`
4. Extract IP and Port values

### 6.2 Update SSH Config

```bash
# Quick update
NEW_IP="<from_console>"
NEW_PORT="<from_console>"

sed -i "/Host runpod$/,/Host [^r]/{s/HostName .*/HostName $NEW_IP/}" ~/.ssh/config
sed -i "/Host runpod$/,/Host [^r]/{s/Port [0-9]*/Port $NEW_PORT/}" ~/.ssh/config
```

### 6.3 Verify Connection

```bash
# Test SSH
ssh runpod "echo OK"

# Check GPU
ssh runpod "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader"

# Check ComfyUI
ssh runpod "curl -s localhost:8188/system_stats | head -c 100"
```

### 6.4 Create SSH Tunnel

```bash
# Interactive (with shell)
ssh -L 8188:localhost:8188 runpod

# Background (headless)
ssh -fNL 8188:localhost:8188 runpod
```

---

## 7. Phase 3: Model Installation

### 7.1 Complete Installation Script

Save as `install_extra_models.sh` and execute on pod:

```bash
#!/bin/bash
# install_extra_models.sh - Full post-deploy model installation
set -e

echo "============================================"
echo "=== Jose Obscura - Model Installation ==="
echo "============================================"
echo "Started: $(date)"
echo ""

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

cd /workspace/ComfyUI/custom_nodes/VibeVoice-ComfyUI

python -c "
from huggingface_hub import snapshot_download
import os

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

DISK_FREE=$(df -BG /workspace | tail -1 | awk '{print $4}' | tr -d 'G')
if [ "$DISK_FREE" -lt 35 ]; then
    echo "  SKIP: Insufficient disk space (${DISK_FREE}GB free, need 35GB)"
else
    cd /workspace/ComfyUI/custom_nodes
    if [ ! -d "ComfyUI-SCAIL-Pose" ]; then
        echo "  Cloning ComfyUI-SCAIL-Pose node..."
        git clone --depth 1 https://github.com/kijai/ComfyUI-SCAIL-Pose
        echo "  SCAIL Pose node installed"
    else
        echo "  SCAIL Pose node already present"
    fi

    cd /workspace/ComfyUI/models/diffusion_models
    if [ ! -d "SCAIL-Preview" ]; then
        echo "  Downloading SCAIL-Preview model (28GB)..."
        GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/zai-org/SCAIL-Preview
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
du -sh /workspace/ComfyUI/models/diffusion_models/* 2>/dev/null || true
du -sh /workspace/ComfyUI/models/vibevoice/* 2>/dev/null || true
echo ""
echo "Custom nodes:"
ls -1 /workspace/ComfyUI/custom_nodes/
echo ""
echo "Next steps:"
echo "1. Sync voice reference: scp voice.mp3 runpod:/workspace/ComfyUI/input/"
echo "2. Restart ComfyUI: pkill -f main.py; nohup python /workspace/ComfyUI/main.py --listen 0.0.0.0 > /workspace/comfyui.log 2>&1 &"
echo "3. Verify: curl localhost:8188/system_stats"
```

### 7.2 Execute Installation

```bash
# Copy and run
cat scripts/install_extra_models.sh | ssh runpod "bash -s"

# Or create on pod
ssh runpod "cat > /workspace/install_extra_models.sh" < scripts/install_extra_models.sh
ssh runpod "chmod +x /workspace/install_extra_models.sh && /workspace/install_extra_models.sh"
```

### 7.3 Sync Voice Reference

```bash
# From NAS/local
scp "/mnt/r/Jose Obscura/Documental MACQ/Audio/VO/es-JoseObscura_woman.mp3" \
    runpod:/workspace/ComfyUI/input/

# Verify
ssh runpod "ls -la /workspace/ComfyUI/input/*.mp3"
```

---

## 8. Phase 4: Verification

### 8.1 Health Check Script

```bash
#!/bin/bash
# health_check.sh - Run on pod
echo "=== RunPod Health Check ==="
echo ""

# GPU
echo -n "GPU: "
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# Disk
echo -n "Disk Free: "
df -h /workspace | tail -1 | awk '{print $4}'

# ComfyUI
echo -n "ComfyUI: "
curl -s localhost:8188/system_stats > /dev/null && echo "Running" || echo "NOT RUNNING"

# Models
echo ""
echo "Installed Models:"
du -sh /workspace/ComfyUI/models/diffusion_models/* 2>/dev/null | sort -h

echo ""
echo "Custom Nodes:"
ls -1 /workspace/ComfyUI/custom_nodes/

echo ""
echo "Voice Reference:"
ls -la /workspace/ComfyUI/input/*.mp3 2>/dev/null || echo "NOT FOUND"
```

### 8.2 Verification Checklist

| # | Check | Command | Expected |
|---|-------|---------|----------|
| 1 | GPU Status | `nvidia-smi` | 48GB VRAM |
| 2 | Disk Space | `df -h /workspace` | >200GB free |
| 3 | ComfyUI | `curl localhost:8188/system_stats` | JSON response |
| 4 | WAN Models | `ls models/diffusion_models/*wan*` | Multiple files |
| 5 | VibeVoice | `ls custom_nodes/VibeVoice-ComfyUI` | Directory exists |
| 6 | SteadyDancer | `ls models/diffusion_models/Wan21*` | File exists |
| 7 | Voice Ref | `ls input/*.mp3` | File exists |

### 8.3 Browser UI Tests

1. Navigate to http://localhost:8188
2. Verify ComfyUI loads
3. Click Manager → Check VibeVoice installed
4. Add nodes: LoadAudio, VibeVoiceSingleSpeakerNode
5. Load workflow: `tts-oz-vibevoice-api.json`
6. Queue test generation

---

## 9. Cost Analysis

### Per-Session Costs

| GPU | Base Rate | Download Overhead (~15 min) | Hourly After |
|-----|-----------|------------------------------|--------------|
| L40S | $0.69/hr | ~$0.17 | $0.69/hr |
| L40 | $0.69/hr | ~$0.17 | $0.69/hr |
| A6000 | $0.33/hr | ~$0.08 | $0.33/hr |
| A40 | $0.40/hr | ~$0.10 | $0.40/hr |

### Ephemeral vs Network Volume

| Approach | Fixed Cost/mo | Per-Session | Break-even |
|----------|---------------|-------------|------------|
| **Ephemeral** | $0 | $0.08-0.17 download | - |
| **Network Volume 50GB** | $3.50/mo | $0 (cached) | 35-60 sessions |
| **Network Volume 100GB** | $7/mo | $0 (cached) | 70-120 sessions |

### Monthly Cost Projection

| Sessions/Month | Ephemeral (A6000, 2hr avg) | Network Vol + A6000 |
|----------------|----------------------------|---------------------|
| 5 | $3.50 | $3.50 + $3.30 = $6.80 |
| 15 | $10.50 | $3.50 + $9.90 = $13.40 |
| 30 | $21.00 | $3.50 + $19.80 = $23.30 |

**Recommendation**: Ephemeral for <35 sessions/month.

---

## 10. Risk Assessment

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|------------|--------|------------|
| 1 | **SSH port changes on restart** | High | Low | Always check console for new port; automate with API |
| 2 | **CUDA not initialized** | Medium | High | Run cuda_init.sh; restart pod if needed |
| 3 | **Model download timeout** | Low | Medium | Use `wget -c` for resume; check startup logs |
| 4 | **Out of VRAM** | Medium | Medium | Run one model at a time; use FP8 versions |
| 5 | **Disk space exhausted** | Low | High | Monitor with `df -h`; skip SCAIL if tight |

### Rollback Plan

1. Stop pod (stops billing)
2. Check logs: `tail -500 /var/log/startup.log`
3. Redeploy with different GPU type
4. If persistent issues, create RunPod support ticket

---

## 11. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Total setup time | <25 min | Deploy → first successful generation |
| Model installation | 100% P0/P1 | All critical models present |
| ComfyUI uptime | 100% | No crashes during session |
| TTS generation | Working | Voice clip matches reference |
| Video generation | Working | WAN 720p renders successfully |
| Cost per session | <$2 | 2hr session on L40S |

### Sign-Off Template

```
=== Hearmeman Ephemeral Deployment Sign-Off ===

Date: YYYY-MM-DD
Operator: [name]
Pod ID: [runpod_pod_id]
GPU: [L40S / A6000]

Phase 1 - Template Deploy: [ ] PASS
Phase 2 - SSH Setup: [ ] PASS
Phase 3 - Model Install: [ ] PASS
Phase 4 - Verification: [ ] PASS

Critical Checks (7/7 required):
[ ] GPU 48GB VRAM
[ ] CUDA OK
[ ] ComfyUI HTTP OK
[ ] WAN models OK
[ ] VibeVoice node OK
[ ] Voice reference OK
[ ] TTS test OK

Ready for Production: [ ] YES / [ ] NO

Signed: _________________ Date: _________
```

---

## Appendix A: Environment Variables Reference

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `WAN_480P` | bool | false | Download 480p WAN models |
| `WAN_720P` | bool | false | Download 720p WAN models (recommended) |
| `WAN_FUN` | bool | false | Download WAN Fun creative variants |
| `VACE` | bool | false | Download VACE video animation models |
| `CIVITAI_TOKEN` | string | - | CivitAI API key for LoRA downloads |
| `LORA_IDS` | csv | - | Comma-separated LoRA version IDs |
| `CHECKPOINT_IDS` | csv | - | Comma-separated checkpoint version IDs |
| `PUBLIC_KEY` | string | - | SSH public key (set via account settings) |
| `JUPYTER_PASSWORD` | string | - | Optional: enables JupyterLab |

---

## Appendix B: Troubleshooting Quick Reference

| Symptom | Cause | Solution |
|---------|-------|----------|
| SSH connection refused | Port changed | Re-copy from Console → Connect |
| Permission denied (publickey) | Key not in RunPod | Upload to Settings → SSH Keys |
| Host key verification failed | Normal for ephemeral | Add `StrictHostKeyChecking no` to config |
| CUDA not available | Cold start issue | Run warmup: `python -c "import torch; torch.zeros(1).cuda()"` |
| ComfyUI not responding | Process crashed | `pkill -f main.py && python /workspace/ComfyUI/main.py --listen 0.0.0.0 &` |
| Model not in dropdown | Not downloaded | Check `ls /workspace/ComfyUI/models/diffusion_models/` |
| VibeVoice node missing | Not installed | `cd custom_nodes && git clone https://github.com/AIFSH/VibeVoice-ComfyUI` |
| Out of VRAM | Too many models loaded | Restart ComfyUI; use FP8 versions |
| Download stuck | Network issue | Re-run `wget -c <URL>` to resume |
| Tunnel port in use | Orphan SSH process | `pkill -f "ssh.*8188.*runpod"` |

---

## Appendix C: Related Documentation

### Project Documentation

- `CLAUDE.md` - Project context and RunPod setup notes
- `doc/transcripts/` - Interview transcripts (ES/EN)
- `scripts/runpod/` - CUDA init and startup scripts
- `scripts/generate_voiceover.py` - Batch TTS generation

### External Resources

- [Hearmeman Template](https://console.runpod.io/deploy?template=758dsjwiqz)
- [RunPod Documentation](https://docs.runpod.io/)
- [ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)
- [VibeVoice-ComfyUI](https://github.com/AIFSH/VibeVoice-ComfyUI)
- [SteadyDancer HuggingFace](https://huggingface.co/MCG-NJU/SteadyDancer-14B)
- [SCAIL-Preview HuggingFace](https://huggingface.co/zai-org/SCAIL-Preview)

### Model Comparison Research

- `dev/agents/artifacts/doc/scail-vs-steadydancer.md`
- `dev/agents/artifacts/doc/wan-nsfw-comparison.md`
- `dev/agents/artifacts/doc/runpod-gpu-comparison-research/`

---

*Document generated: 2025-12-24*
*Project: José Obscura - La Maquila Erótica Documentary*
