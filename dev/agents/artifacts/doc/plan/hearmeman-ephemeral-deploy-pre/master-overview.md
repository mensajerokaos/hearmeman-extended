---
author: oz
model: claude-opus-4-5
date: 2025-12-24 01:38
task: Master implementation plan for Hearmeman ephemeral deployment
---

# Hearmeman Ephemeral Deployment - Master Plan

**Project**: José Obscura - La Maquila Erótica Documentary
**Target**: RunPod ephemeral pod with WAN 2.2 720p + custom models

---

## Executive Summary

This plan outlines a 4-phase deployment strategy for the Hearmeman "One Click - ComfyUI Wan t2v i2v VACE" template on RunPod with ephemeral storage. The approach prioritizes cost efficiency (no network volume fees) while ensuring full capability for documentary AI generation.

**Key Decisions**:
- **Storage**: 450GB ephemeral (free) — sufficient for all models (~160GB)
- **GPU**: L40S or A6000 (48GB VRAM required)
- **Template**: Hearmeman `758dsjwiqz` with `WAN_720P=true`
- **Post-deploy models**: VibeVoice, SteadyDancer, SCAIL (manual install)

**Estimated Total Setup Time**: 15-25 minutes (mostly model downloads)

---

## Architecture Diagram

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

## Phase Breakdown

### Phase 1: Template Deployment

**Objective**: Deploy Hearmeman template via RunPod console with correct environment variables.

**Duration**: 2-3 minutes (deploy) + 5-15 minutes (model download)

#### Steps

| Step | Action | Details |
|------|--------|---------|
| 1.1 | Navigate to deploy URL | https://console.runpod.io/deploy?template=758dsjwiqz |
| 1.2 | Click "Edit Template" | Pencil icon in top-right |
| 1.3 | Set environment variables | See table below |
| 1.4 | Select GPU | Filter: CUDA 12.8, 48GB VRAM → L40S or A6000 |
| 1.5 | Set pod name | `jose-wan-720p` (optional) |
| 1.6 | Click "Deploy" | Wait for status: Running |

#### Environment Variables

```bash
WAN_480P=false        # Skip low resolution
WAN_720P=true         # Enable 720p models ✓
WAN_FUN=false         # Skip Fun variants
VACE=false            # Skip VACE (not needed initially)
CIVITAI_TOKEN=        # Leave empty unless using LoRAs
LORA_IDS=             # Leave empty
CHECKPOINT_IDS=       # Leave empty
```

#### Expected Downloads (Automatic)

| Model | Size | Time |
|-------|------|------|
| WAN 2.2 T2V-14B FP8 | ~15GB | 2-3 min |
| WAN 2.2 I2V-14B FP8 | ~15GB | 2-3 min |
| WAN 2.2 MoE High/Low | ~28GB ea | 5-8 min |
| UMT5 XXL Text Encoder | ~15GB | 2-3 min |
| WAN VAE | ~0.5GB | <10s |

**Success Criteria**: Pod status shows "Running" and logs show model downloads complete.

---

### Phase 2: SSH Setup

**Objective**: Configure SSH connection for command-line access to pod.

**Duration**: 2-5 minutes

#### Prerequisites

- SSH public key configured in RunPod account settings
- Local key: `~/.ssh/id_ed25519` or `~/.ssh/id_rsa`

#### Steps

| Step | Action | Command/Details |
|------|--------|-----------------|
| 2.1 | Get connection details | RunPod Console → Pod → "Connect" button |
| 2.2 | Extract IP and port | Copy from console (e.g., `194.68.245.83:22095`) |
| 2.3 | Update SSH config | See command below |
| 2.4 | Test connection | `ssh runpod "echo OK"` |

#### SSH Config Update

```bash
# Manual update (~/.ssh/config)
Host runpod
    HostName <NEW_IP>
    Port <NEW_PORT>
    User root
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
```

Or use sed:

```bash
# Replace values in existing config
sed -i 's/HostName .*/HostName <NEW_IP>/' ~/.ssh/config
sed -i 's/Port [0-9]*/Port <NEW_PORT>/' ~/.ssh/config
```

#### Verification Commands

```bash
# Test SSH
ssh runpod "nvidia-smi"

# Check model download status
ssh runpod "ls -la /workspace/ComfyUI/models/diffusion_models/"

# Check ComfyUI is running
ssh runpod "curl -s localhost:8188/system_stats | head -c 100"
```

**Success Criteria**: SSH connects and `nvidia-smi` shows 48GB GPU.

---

### Phase 3: Model Installation

**Objective**: Install additional models not included in Hearmeman template.

**Duration**: 10-15 minutes (parallel downloads)

#### Model Priority

| Priority | Model | Size | Use Case |
|----------|-------|------|----------|
| P0 | VibeVoice-ComfyUI | ~20GB | Voice cloning TTS (narrator) |
| P1 | SteadyDancer | ~28GB | Dance/motion video |
| P2 | SCAIL | ~28GB | Facial expressions (optional) |

#### Installation Script

Create on pod: `/workspace/install_extra_models.sh`

```bash
#!/bin/bash
set -e

echo "=== Installing Extra Models for Jose Obscura ==="
START_TIME=$(date +%s)

# ===== 1. VibeVoice (P0 - Critical) =====
echo "[1/3] Installing VibeVoice..."
cd /workspace/ComfyUI/custom_nodes
if [ ! -d "VibeVoice-ComfyUI" ]; then
    git clone https://github.com/AIFSH/VibeVoice-ComfyUI
    cd VibeVoice-ComfyUI
    pip install -r requirements.txt 2>/dev/null || pip install TTS
    echo "✓ VibeVoice installed"
else
    echo "• VibeVoice already present"
fi

# ===== 2. SteadyDancer (P1) =====
echo "[2/3] Downloading SteadyDancer..."
cd /workspace/ComfyUI/models/diffusion_models
if [ ! -f "Wan21_SteadyDancer_fp16.safetensors" ]; then
    wget -c --progress=dot:giga \
        https://huggingface.co/MCG-NJU/SteadyDancer-14B/resolve/main/Wan21_SteadyDancer_fp16.safetensors
    echo "✓ SteadyDancer downloaded"
else
    echo "• SteadyDancer already present"
fi

# ===== 3. SCAIL (P2 - Optional) =====
echo "[3/3] Installing SCAIL..."
cd /workspace/ComfyUI/custom_nodes
if [ ! -d "ComfyUI-SCAIL-Pose" ]; then
    git clone https://github.com/kijai/ComfyUI-SCAIL-Pose
    echo "✓ SCAIL Pose node installed"
else
    echo "• SCAIL Pose already present"
fi

cd /workspace/ComfyUI/models/diffusion_models
if [ ! -d "SCAIL-Preview" ]; then
    echo "Downloading SCAIL model (28GB)..."
    GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/zai-org/SCAIL-Preview
    cd SCAIL-Preview && git lfs pull
    echo "✓ SCAIL model downloaded"
else
    echo "• SCAIL already present"
fi

# ===== Summary =====
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo ""
echo "=== Installation Complete ==="
echo "Duration: ${DURATION}s"
echo ""
echo "Installed models:"
ls -lah /workspace/ComfyUI/models/diffusion_models/ | grep -E "\.safetensors$|SCAIL"
echo ""
echo "Custom nodes:"
ls /workspace/ComfyUI/custom_nodes/
```

#### Run Installation

```bash
# Copy script to pod
scp scripts/install_extra_models.sh runpod:/workspace/

# Execute
ssh runpod "chmod +x /workspace/install_extra_models.sh && /workspace/install_extra_models.sh"
```

#### Sync Voice Reference

```bash
# From NAS or local
scp "R:/Jose Obscura/Documental MACQ/Audio/VO/es-JoseObscura_woman.mp3" \
    runpod:/workspace/ComfyUI/input/
```

**Success Criteria**: All three models installed, voice reference uploaded.

---

### Phase 4: Verification

**Objective**: Confirm all components are operational.

**Duration**: 5-10 minutes

#### Verification Checklist

| # | Check | Command | Expected |
|---|-------|---------|----------|
| 4.1 | GPU Status | `nvidia-smi` | 48GB VRAM available |
| 4.2 | Disk Space | `df -h /workspace` | >200GB free |
| 4.3 | ComfyUI Running | `curl localhost:8188/system_stats` | JSON response |
| 4.4 | WAN Models | `ls models/diffusion_models/*wan*` | Multiple .safetensors |
| 4.5 | VibeVoice Node | `ls custom_nodes/VibeVoice-ComfyUI` | Directory exists |
| 4.6 | SteadyDancer | `ls models/diffusion_models/Wan21_SteadyDancer*` | File exists |
| 4.7 | Voice Reference | `ls input/es-JoseObscura_woman.mp3` | File exists |

#### Health Check Script

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

#### SSH Tunnel for Browser Access

```bash
# Local machine - opens localhost:8188 → pod:8188
ssh -L 8188:localhost:8188 runpod

# Or background tunnel
ssh -fNL 8188:localhost:8188 runpod
```

#### Browser Tests

1. Open http://localhost:8188
2. Verify ComfyUI loads
3. Check Manager → Custom Nodes → VibeVoice visible
4. Load workflow: `tts-oz-vibevoice-api.json`
5. Test generation with voice reference

**Success Criteria**: ComfyUI accessible in browser, test generation completes.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Model download timeout | Low | Medium | Use `wget -c` for resume; check startup logs |
| CUDA not initialized | Medium | High | Run cuda_init.sh; restart pod if needed |
| SSH port changed | High | Low | Always check console for new port on restart |
| Disk space exhausted | Low | High | Monitor with `df -h`; skip SCAIL if tight |
| Out of VRAM | Medium | Medium | Run one model at a time; use FP8 versions |
| Voice reference missing | Low | High | Upload before starting TTS work |

### Rollback Plan

If deployment fails:
1. Stop pod (stops billing)
2. Check logs: `tail -500 /var/log/startup.log`
3. Redeploy with different GPU type
4. If persistent issues, create support ticket

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Total setup time | <25 min | Start → first successful generation |
| Model installation | 100% | All P0/P1 models present |
| ComfyUI uptime | 100% | No crashes during session |
| TTS generation | Working | Voice clip matches reference |
| Cost per session | <$2 | 2hr session on L40S |

---

## Quick Reference Commands

### Deploy (Console)
```
URL: https://console.runpod.io/deploy?template=758dsjwiqz
ENV: WAN_720P=true
GPU: L40S or A6000 (48GB)
```

### Connect
```bash
ssh runpod                              # After updating config
ssh -L 8188:localhost:8188 runpod       # With tunnel
```

### Install Extra Models
```bash
ssh runpod "/workspace/install_extra_models.sh"
```

### Start ComfyUI
```bash
ssh runpod "nohup python /workspace/ComfyUI/main.py --listen 0.0.0.0 > /workspace/comfyui.log 2>&1 &"
```

### Copy Voice Reference
```bash
scp ~/voice/es-JoseObscura_woman.mp3 runpod:/workspace/ComfyUI/input/
```

### Sync Workflows
```bash
scp ~/comfyui/user/default/workflows/tts-oz-vibevoice-api.json \
    runpod:/workspace/ComfyUI/user/default/workflows/
```

---

## Appendix: Cost Calculator

| Sessions/Month | Ephemeral Cost | Network Volume Cost | Savings |
|----------------|----------------|---------------------|---------|
| 5 | $0.50 | $3.50 + $0 = $3.50 | +$3.00 ephemeral |
| 15 | $1.50 | $3.50 | +$2.00 ephemeral |
| 30 | $3.00 | $3.50 | +$0.50 ephemeral |
| 50 | $5.00 | $3.50 | -$1.50 network vol wins |

**Recommendation**: Use ephemeral unless >35 sessions/month expected.

---

*Document generated: 2025-12-24*
*Project: José Obscura - La Maquila Erótica Documentary*
