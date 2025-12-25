---
author: oz
model: claude-opus-4-5-20251101
date: 2025-12-23T22:45:00Z
task: Codebase research for RunPod CUDA initialization fix
---

# Codebase Research: RunPod CUDA Initialization Fix

## 1. Existing RunPod Configuration

### Pod Information
| Property | Value |
|----------|-------|
| Pod ID | `k02604uwhjq6dm` |
| Pod Name | vibevoice |
| GPU | NVIDIA RTX A6000 (48GB VRAM) |
| Network Volume | `ul56y9ya5h` (50GB, EU-SE-1) |
| Cost | $0.33/hr |
| Internal hostname | `k02604uwhjq6dm.runpod.internal` |
| Private IP | `10.0.131.252` |

### SSH Configuration
From `~/.ssh/config`:
```
Host runpod
    HostName 194.68.245.83
    Port 22085  # Changes on each restart
    User root
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
```

**Note**: The external SSH port changes with each pod restart. The current port is 22085 but needs to be updated in SSH config after each cold start.

---

## 2. Existing Scripts

### Setup Script: `/scripts/setup_runpod_vibevoice.sh`
**Current startup script** (creates `/workspace/start_comfyui.sh`):
```bash
#!/bin/bash
cd /workspace/ComfyUI
exec /workspace/venv/bin/python main.py --listen 0.0.0.0 --port 8188
```

**Current issues**:
1. No CUDA environment configuration
2. No GPU initialization check
3. No retry logic for CUDA failures
4. No device mapping/ordering configuration

### Voiceover Generation Scripts
- `scripts/generate_voiceover.py` - Generates 22 VO segments via ComfyUI API
- `scripts/regenerate_voiceovers.py` - Regenerates specific segments with random seeds

Both scripts connect to `http://localhost:8188` (ComfyUI on RunPod via SSH tunnel).

---

## 3. Current venv Setup

From `scripts/setup_runpod_vibevoice.sh`:
```bash
# Venv location
/workspace/venv

# PyTorch installation
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# ComfyUI location
/workspace/ComfyUI

# VibeVoice custom node
/workspace/ComfyUI/custom_nodes/ComfyUI-VibeVoice
```

**Current PyTorch CUDA version**: cu124 (CUDA 12.4)
**Reported issue**: PyTorch 2.1.0+cu118 with driver CUDA 12.7

This indicates a **version mismatch** between:
- Pod image PyTorch (cu118 - CUDA 11.8)
- Installed venv PyTorch (cu124 - CUDA 12.4)
- Driver CUDA (12.7)

---

## 4. Known GPU Device Issue

From user report:
- GPU is on device 8 (`/dev/nvidia8` exists)
- `/dev/nvidia0` doesn't exist
- `nvidia-smi` works
- `torch.cuda.is_available()` returns False

**Root cause**: RunPod multi-GPU hosts assign non-zero device indices. The container sees only the allocated GPU but with its original device number.

---

## 5. RunPod API Reference

From `dev/agents/artifacts/doc/runpod-api/api-reference.md`:
- API uses GraphQL with query parameter authentication
- Pod management: `podResume`, `podStop` mutations
- API key stored in `~/.zshrc` as `RUNPOD_API_KEY`

---

## 6. Related Research Documents

### Docker vs venv on RunPod
From `dev/agents/artifacts/doc/runpod-gpu-comparison-research/docker-vs-venv.md`:
- RunPod pods ARE Docker containers
- Network Volume (`/workspace`) persists across restarts
- venv should be on `/workspace` for persistence
- Startup script pattern: `/workspace/setup.sh`

### GPU Comparison Research
From `dev/agents/artifacts/doc/runpod-gpu-comparison-research/`:
- RTX A6000: 48GB VRAM, $0.33/hr
- VibeVoice-Large requires ~17GB VRAM
- Full precision recommended for RTX A6000

---

## 7. Gaps Identified

### Missing from current setup:
1. **CUDA environment variables** - No `CUDA_VISIBLE_DEVICES`, `CUDA_DEVICE_ORDER`
2. **GPU initialization warmup** - No pre-flight CUDA check
3. **Retry logic** - No handling for cold start race conditions
4. **Device index handling** - No remapping for non-zero GPU indices
5. **PyTorch CUDA version alignment** - cu118 vs cu124 mismatch

### Files to Create/Modify:
1. `/workspace/cuda_init.sh` - CUDA initialization script
2. `/workspace/start_comfyui.sh` - Updated startup with CUDA fixes
3. Pod template configuration - Environment variables

---

## 8. Current Startup Flow

```
Pod Start
    ↓
Container boots (ephemeral storage)
    ↓
/workspace mounts (network volume)
    ↓
[MANUAL] SSH in and run:
    nohup /workspace/start_comfyui.sh > /workspace/comfyui.log 2>&1 &
    ↓
ComfyUI starts (NO CUDA checks)
    ↓
CUDA_ERROR_NOT_INITIALIZED (on cold start)
```

### Desired Startup Flow

```
Pod Start
    ↓
Container boots + CUDA env vars set
    ↓
/workspace mounts
    ↓
[AUTO] Startup script runs:
    1. Set CUDA_VISIBLE_DEVICES=0
    2. Set CUDA_DEVICE_ORDER=PCI_BUS_ID
    3. Wait for GPU availability
    4. Warmup CUDA (test tensor operation)
    5. Start ComfyUI
    ↓
ComfyUI ready with CUDA working
```

---

## 9. Voice File Reference

Voice cloning file location:
```
/workspace/ComfyUI/input/es-JoseObscura_woman.mp3
```

Models:
- VibeVoice-1.5B (Large) - 17GB
- VibeVoice-Large - 18GB

---

## 10. Summary

**Key Issues**:
1. GPU device is `/dev/nvidia8` not `/dev/nvidia0`
2. PyTorch cu118 vs driver CUDA 12.7 mismatch
3. No automatic CUDA initialization on cold start
4. Manual SSH required to start ComfyUI

**Required Fixes**:
1. Set `CUDA_VISIBLE_DEVICES=0` to remap device index
2. Set `CUDA_DEVICE_ORDER=PCI_BUS_ID` for consistent ordering
3. Add retry logic for CUDA initialization
4. Update PyTorch to cu121 or cu124 for driver compatibility
5. Create automated startup script with CUDA warmup
