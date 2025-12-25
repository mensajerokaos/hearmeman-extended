---
author: oz
model: claude-opus-4-5
date: 2025-12-24 01:39
task: Phase 1 detailed expansion - Hearmeman template deployment
---

# Phase 1: Template Deployment (Detailed Expansion)

**Duration**: 2-3 minutes (deploy) + 5-15 minutes (model download)
**Objective**: Deploy Hearmeman template via RunPod console with correct environment variables for 720p WAN models

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Template Details](#2-template-details)
3. [Step-by-Step Console Walkthrough](#3-step-by-step-console-walkthrough)
4. [Environment Variables Configuration](#4-environment-variables-configuration)
5. [GPU Selection Guide](#5-gpu-selection-guide)
6. [Storage Configuration](#6-storage-configuration)
7. [Expected Output & Timing](#7-expected-output--timing)
8. [Verification](#8-verification)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

Before starting deployment:

| Requirement | How to Verify | Action if Missing |
|-------------|---------------|-------------------|
| RunPod account | Log in at console.runpod.io | Create at runpod.io |
| RunPod credits | Check balance in console | Add funds ($10+ recommended) |
| SSH public key | RunPod Settings → SSH Keys | Add `~/.ssh/id_ed25519.pub` |
| Browser | Any modern browser | Use Chrome/Firefox/Edge |

### SSH Key Setup (If Not Done)

```bash
# Check if key exists
ls -la ~/.ssh/id_ed25519.pub

# If not, generate one
ssh-keygen -t ed25519 -C "runpod-ephemeral"

# Copy to clipboard (Linux/WSL)
cat ~/.ssh/id_ed25519.pub | clip.exe

# Add to RunPod: Settings → SSH Public Keys → Add Key
```

---

## 2. Template Details

### Template Information

| Property | Value |
|----------|-------|
| **Template Name** | One Click - ComfyUI Wan t2v i2v VACE - CUDA 12.8 |
| **Template ID** | `758dsjwiqz` |
| **Deploy URL** | https://console.runpod.io/deploy?template=758dsjwiqz |
| **Author** | Hearmeman (Community template) |
| **Base Image** | PyTorch 2.8.0 + CUDA 12.8 + cuDNN 9 |

### Pre-Installed Components

- ✅ ComfyUI + ComfyUI Manager
- ✅ Kijai's ComfyUI-WanVideoWrapper
- ✅ WAN 2.1/2.2 model download scripts
- ✅ VACE support (optional)
- ✅ 450GB ephemeral storage
- ✅ SSH access on dynamic port
- ✅ HTTP port 8188 for ComfyUI web UI

### NOT Included (Install in Phase 3)

- ❌ VibeVoice TTS
- ❌ SteadyDancer
- ❌ SCAIL
- ❌ Custom voice references

---

## 3. Step-by-Step Console Walkthrough

### Step 1: Navigate to Deploy URL

**Action**: Open browser and go to:
```
https://console.runpod.io/deploy?template=758dsjwiqz
```

**Screenshot Description**:
- Page shows "Deploy Template" header
- Template card displays "One Click - ComfyUI Wan t2v i2v VACE - CUDA 12.8"
- Right panel shows GPU selection and configuration options
- "Edit Template" button (pencil icon) in top-right of template card

**Alternative Path**:
1. Go to https://console.runpod.io
2. Click "Community Cloud" in left sidebar
3. Click "Templates" tab
4. Search for "hearmeman wan"
5. Click "Deploy" on the matching template

---

### Step 2: Edit Template Configuration

**Action**: Click the pencil icon (✏️) labeled "Edit Template" in the top-right of the template card.

**Screenshot Description**:
- Modal opens with environment variable fields
- Each variable has a text input
- "Save" and "Cancel" buttons at bottom
- Variables listed: WAN_480P, WAN_720P, WAN_FUN, VACE, CIVITAI_TOKEN, LORA_IDS, CHECKPOINT_IDS

---

### Step 3: Set Environment Variables

**Action**: Configure each variable as shown in Section 4 below.

**Critical Settings**:
```
WAN_720P = true    ← MUST be "true" (lowercase, no quotes)
```

All other variables can remain default (false or empty).

---

### Step 4: Save Template Changes

**Action**: Click "Save" button to apply environment variable changes.

**Screenshot Description**:
- Modal closes
- Template card updates to show configured state
- Proceed to GPU selection

---

### Step 5: Select GPU

**Action**: In the right panel, configure GPU:

1. **GPU Selection Dropdown**: Click to expand
2. **Filter** (if available):
   - VRAM: 48GB
   - CUDA: 12.8+
3. **Select**: L40S (preferred) or A6000 (cheaper)

**Screenshot Description**:
- GPU cards showing availability, VRAM, price per hour
- Green checkmark on selected GPU
- Estimated cost display updates

---

### Step 6: Configure Pod Settings

**Action**: Set pod name (optional) and verify storage:

| Setting | Value | Notes |
|---------|-------|-------|
| Pod Name | `jose-wan-720p` | Optional, helps identify pod |
| Container Disk | 450 GB | Default, leave unchanged |
| Volume Disk | 0 GB | **NO network volume** |
| Volume Mount | - | Leave empty |

**Screenshot Description**:
- "Container Disk" slider at 450GB
- "Volume" section shows 0GB or empty
- Pod name text field

---

### Step 7: Deploy

**Action**: Click the blue "Deploy" button.

**Screenshot Description**:
- Button changes to "Deploying..."
- Redirect to Pods dashboard
- New pod appears with "Pending" status

---

### Step 8: Wait for Startup

**Action**: Monitor pod status in Pods dashboard.

**Status Progression**:
```
[Pending] → [Downloading] → [Building] → [Running]
           ↓
    ~2-3 min (image)
                    ↓
             ~5-15 min (models, if WAN_720P=true)
```

**Screenshot Description**:
- Pod card shows current status
- Progress bar or spinner during download
- "Running" status with green indicator when complete

---

## 4. Environment Variables Configuration

### Complete Settings Table

| Variable | Value | Purpose | Required |
|----------|-------|---------|----------|
| `WAN_480P` | `false` | Skip 480p models (too low resolution) | Optional |
| `WAN_720P` | **`true`** | Download 720p WAN 2.1/2.2 models | **REQUIRED** |
| `WAN_FUN` | `false` | Skip WAN Fun variants | Optional |
| `VACE` | `false` | Skip VACE models (not needed initially) | Optional |
| `CIVITAI_TOKEN` | *(empty)* | CivitAI API key for LoRAs | Optional |
| `LORA_IDS` | *(empty)* | Comma-separated LoRA version IDs | Optional |
| `CHECKPOINT_IDS` | *(empty)* | Comma-separated checkpoint IDs | Optional |

### Copy-Paste Ready Configuration

```bash
# Set in RunPod console (Edit Template)
WAN_480P=false
WAN_720P=true
WAN_FUN=false
VACE=false
CIVITAI_TOKEN=
LORA_IDS=
CHECKPOINT_IDS=
```

### Variable Details

#### WAN_720P (Critical)

- **What it downloads**:
  - WAN 2.1 T2V-14B FP8 (~15GB) - Text to Video
  - WAN 2.1 I2V-14B FP8 (~15GB) - Image to Video
  - WAN 2.2 MoE variants (~28GB each) - Mixture of Experts
  - UMT5 XXL Text Encoder (~15GB)
  - WAN VAE (~0.5GB)

- **Total download**: ~60-80GB
- **Download time**: 5-15 minutes (depends on datacenter bandwidth)

#### CIVITAI_TOKEN (Optional)

If you plan to use CivitAI LoRAs:
1. Go to https://civitai.com
2. Click profile → API Keys
3. Create new key
4. Paste in this field

---

## 5. GPU Selection Guide

### Recommended GPUs

| GPU | VRAM | Price/hr | Availability | Recommendation |
|-----|------|----------|--------------|----------------|
| **L40S** | 48GB | $0.69/hr | High | ⭐ Best for production |
| **L40** | 48GB | $0.69/hr | Medium | Good alternative |
| **A6000** | 48GB | $0.33/hr | Medium | 💰 Budget option |
| **A40** | 48GB | $0.40/hr | Low | Acceptable |

### GPU Selection Criteria

1. **VRAM**: Must be 48GB for WAN 14B models + VibeVoice
2. **CUDA**: Template requires CUDA 12.8 compatibility
3. **Availability**: L40S typically most available
4. **Cost**: A6000 is half the price of L40S

### Why 48GB VRAM?

| Model | VRAM Usage |
|-------|------------|
| WAN 2.2 I2V-14B | 24-30GB |
| VibeVoice-Large | 16-18GB |
| **Combined** | 35-45GB |

24GB GPUs (A5000, RTX 4090) will work for WAN alone but not with VibeVoice simultaneously.

### Filtering in Console

If GPU selection shows many options:

1. Look for "Filter" option
2. Set: `VRAM >= 48GB`
3. Set: `CUDA >= 12.8` (if available)
4. Sort by: Price or Availability

---

## 6. Storage Configuration

### Ephemeral Storage (Recommended)

| Property | Value |
|----------|-------|
| **Type** | Ephemeral (Container Disk) |
| **Size** | 450GB |
| **Cost** | $0 (included in GPU rental) |
| **Persistence** | Data deleted on pod stop |

### Why NO Network Volume?

| Factor | Ephemeral | Network Volume |
|--------|-----------|----------------|
| Fixed cost | $0/month | $3.50-$7/month |
| Model re-download | Yes (5-15 min) | No |
| Per-session cost | ~$0.10 | $0 |
| Break-even | - | 35-60 sessions/month |

**For José Obscura project**: With <30 sessions/month expected, ephemeral saves money.

### Storage Usage Estimate

| Component | Size | Cumulative |
|-----------|------|------------|
| Base ComfyUI | ~5GB | 5GB |
| WAN 720p models | ~80GB | 85GB |
| VibeVoice (Phase 3) | ~20GB | 105GB |
| SteadyDancer (Phase 3) | ~28GB | 133GB |
| SCAIL (Phase 3) | ~28GB | 161GB |
| Working files | ~40GB | **~200GB** |

**Remaining**: 450 - 200 = **250GB free** ✅

---

## 7. Expected Output & Timing

### Timeline

```
T+0:00  Click Deploy
T+0:30  Pod shows "Pending"
T+1:00  Container image pulled, "Building"
T+2:00  Container ready, model downloads begin
T+5:00  UMT5 text encoder downloaded
T+8:00  WAN T2V model downloaded
T+11:00 WAN I2V model downloaded
T+14:00 WAN MoE models downloaded
T+15:00 VAE downloaded, ComfyUI starts
T+16:00 Pod shows "Running", ready for SSH
```

**Total**: 15-20 minutes from click to fully ready

### What Downloads Automatically

With `WAN_720P=true`:

| Model File | Size | Purpose |
|------------|------|---------|
| `umt5_xxl.safetensors` | ~15GB | Text encoder |
| `wan2.1_t2v_14b_fp8.safetensors` | ~15GB | Text-to-Video |
| `wan2.1_i2v_14b_fp8.safetensors` | ~15GB | Image-to-Video |
| `wan2.2_moe_high.safetensors` | ~14GB | MoE High Noise |
| `wan2.2_moe_low.safetensors` | ~14GB | MoE Low Noise |
| `wan_vae.safetensors` | ~0.5GB | VAE decoder |

### Logs to Monitor

SSH in (after pod running) and check:

```bash
# Startup log (model downloads)
tail -f /var/log/startup.log

# ComfyUI log (once started)
tail -f /workspace/comfyui.log
```

---

## 8. Verification

### Success Criteria

| Check | Expected Result | Command |
|-------|-----------------|---------|
| Pod status | "Running" (green) | RunPod console |
| SSH access | Connection succeeds | `ssh runpod "echo OK"` |
| GPU detected | 48GB VRAM shown | `ssh runpod "nvidia-smi"` |
| Models present | Multiple .safetensors | `ssh runpod "ls /workspace/ComfyUI/models/diffusion_models/"` |
| ComfyUI running | JSON response | `ssh runpod "curl -s localhost:8188/system_stats"` |

### Quick Verification Script

Run locally after pod shows "Running":

```bash
#!/bin/bash
# verify_phase1.sh

echo "=== Phase 1 Verification ==="

# 1. SSH Connection (update config first!)
echo -n "SSH: "
ssh -o ConnectTimeout=10 runpod "echo OK" 2>/dev/null || echo "FAILED - update SSH config"

# 2. GPU
echo -n "GPU: "
ssh runpod "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader" 2>/dev/null || echo "FAILED"

# 3. Models
echo -n "Models: "
ssh runpod "ls /workspace/ComfyUI/models/diffusion_models/*.safetensors 2>/dev/null | wc -l" 2>/dev/null || echo "FAILED"

# 4. ComfyUI
echo -n "ComfyUI: "
ssh runpod "curl -s localhost:8188/system_stats | head -c 50" 2>/dev/null && echo "... OK" || echo "NOT RUNNING"

echo "=== Done ==="
```

### Console Verification

In RunPod console, verify:

1. **Pod Card**:
   - Status: "Running" (green)
   - GPU: Shows selected model (L40S, etc.)
   - Uptime: Shows time since start

2. **Connect Button**:
   - Shows SSH connection info
   - HTTP port 8188 accessible

---

## 9. Troubleshooting

### Issue: Pod Stuck on "Pending"

**Symptoms**: Pod stays in "Pending" for >5 minutes

**Causes & Solutions**:

| Cause | Solution |
|-------|----------|
| No GPU availability | Try different GPU type or datacenter |
| Insufficient credits | Add funds to account |
| Rate limiting | Wait 5 minutes, retry |

**Action**:
```
1. Stop the pending pod
2. Click Deploy again
3. Select different GPU or "Any" datacenter
```

---

### Issue: Model Download Fails

**Symptoms**: Pod running but models missing, ComfyUI shows errors

**Diagnosis**:
```bash
ssh runpod "tail -100 /var/log/startup.log | grep -i error"
```

**Common Causes**:

| Cause | Solution |
|-------|----------|
| HuggingFace rate limit | Wait 10 min, restart pod |
| Disk full | Shouldn't happen with 450GB |
| Network timeout | Restart pod |

**Manual Model Download**:
```bash
ssh runpod "cd /workspace/ComfyUI/models/diffusion_models && \
wget -c https://huggingface.co/city96/WAN2.1-T2V-14B-GGUF/resolve/main/wan2.1_t2v_14b_fp8.safetensors"
```

---

### Issue: SSH Connection Refused

**Symptoms**: `ssh: connect to host ... port ...: Connection refused`

**Cause**: Port/IP changed (ephemeral pods get new ports each restart)

**Solution**:
1. Go to RunPod console → Pods
2. Click on your pod
3. Click "Connect" button
4. Copy SSH command
5. Update `~/.ssh/config`:

```bash
# Extract IP and port from: ssh root@194.68.245.83 -p 22095 -i ~/.ssh/id_ed25519
sed -i 's/HostName .*/HostName 194.68.245.83/' ~/.ssh/config
sed -i 's/Port [0-9]*/Port 22095/' ~/.ssh/config
```

---

### Issue: ComfyUI Not Responding

**Symptoms**: `curl localhost:8188` times out after SSH

**Diagnosis**:
```bash
ssh runpod "ps aux | grep main.py"
ssh runpod "tail -50 /workspace/comfyui.log"
```

**Solutions**:

| Cause | Solution |
|-------|----------|
| Not started yet | Wait for model downloads to complete |
| Crashed | Restart: `python /workspace/ComfyUI/main.py --listen 0.0.0.0 &` |
| Port conflict | Check `netstat -tlnp | grep 8188` |

---

### Issue: Wrong Environment Variables

**Symptoms**: 480p models downloaded instead of 720p, or no models at all

**Cause**: `WAN_720P` not set to `true` before deploy

**Solution**:
1. Stop pod
2. Go back to deploy URL
3. Edit Template → set `WAN_720P=true`
4. Deploy new pod

**Note**: You cannot change environment variables on a running pod. Must redeploy.

---

### Issue: GPU VRAM Lower Than Expected

**Symptoms**: `nvidia-smi` shows 24GB instead of 48GB

**Cause**: Selected wrong GPU during deployment

**Solution**:
1. Stop pod (to stop billing)
2. Delete pod
3. Redeploy with correct GPU selection (L40S, A6000, etc.)

---

## Checklist Summary

Before proceeding to Phase 2:

```
[ ] Pod status shows "Running"
[ ] SSH connection works (`ssh runpod "echo OK"`)
[ ] nvidia-smi shows 48GB VRAM
[ ] Models directory has .safetensors files
[ ] ComfyUI responds on port 8188
[ ] SSH config updated with new IP/port
```

---

## Next Phase

Once Phase 1 verification passes, proceed to:
→ **Phase 2: SSH Setup** - Configure persistent SSH connection and verify ComfyUI web access

---

*Document generated: 2025-12-24*
*Project: José Obscura - La Maquila Erótica Documentary*
