---
title: RunPod CUDA Cold Start Fix - PRD
created: 2025-12-23T23:00:00Z
author: oz
model: claude-opus-4-5-20251101
pod_id: k02604uwhjq6dm
gpu: NVIDIA RTX A6000 (48GB)
status: ready-for-implementation
---

# PRD: RunPod CUDA Cold Start Fix

## Executive Summary

Fix persistent CUDA initialization failures on RunPod cold starts for pod `k02604uwhjq6dm` (VibeVoice TTS). The pod experiences `CUDA_ERROR_NOT_INITIALIZED` (error code 3) on cold boot, with GPU appearing as `/dev/nvidia8` instead of `/dev/nvidia0`, causing `torch.cuda.is_available()` to return `False` despite `nvidia-smi` working.

**Solution**: Environment variable configuration + startup script with retry logic and CUDA warmup.

---

## Problem Statement

### Symptoms
1. `cuInit()` returns error code 3: `CUDA_ERROR_NOT_INITIALIZED`
2. GPU device is `/dev/nvidia8` (not `/dev/nvidia0`)
3. `nvidia-smi` works but `torch.cuda.is_available()` returns `False`
4. PyTorch 2.1.0+cu118 with driver CUDA 12.7

### Root Causes
| Cause | Impact | Fix |
|-------|--------|-----|
| GPU device index mismatch | PyTorch can't find device 0 | `CUDA_VISIBLE_DEVICES=0` |
| Cold start race condition | cuInit fails on first call | Retry loop with delay |
| Device ordering inconsistency | nvidia-smi vs CUDA order differs | `CUDA_DEVICE_ORDER=PCI_BUS_ID` |

---

## Solution Overview

```
Pod Cold Start
    ↓
Container boots + ENV VARS SET
    ↓
/workspace mounts (Network Volume)
    ↓
cuda_init.sh runs:
  1. Set CUDA_VISIBLE_DEVICES=0
  2. Set CUDA_DEVICE_ORDER=PCI_BUS_ID
  3. Wait for nvidia-smi (10 retries, 3s delay)
  4. Warmup CUDA (torch.zeros(1).cuda())
    ↓
start_comfyui.sh launches
    ↓
ComfyUI ready with CUDA working
```

---

## Implementation

### Phase 1: Startup Scripts (15 min)

#### File 1: `/workspace/cuda_init.sh`

```bash
#!/bin/bash
# cuda_init.sh - CUDA initialization for RunPod cold starts
# Fixes: CUDA_ERROR_NOT_INITIALIZED (error code 3)
# Fixes: /dev/nvidia8 instead of /dev/nvidia0 device mapping

set -e

echo "[$(date -Iseconds)] CUDA Init: Starting..."

# ============================================
# 1. CUDA Environment Variables
# ============================================

export CUDA_VISIBLE_DEVICES=0
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=compute,utility

echo "[$(date -Iseconds)] CUDA Init: Environment variables set"
echo "  CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
echo "  CUDA_DEVICE_ORDER=$CUDA_DEVICE_ORDER"

# ============================================
# 2. Wait for GPU Availability
# ============================================

MAX_RETRIES=10
RETRY_DELAY=3
GPU_READY=false

echo "[$(date -Iseconds)] CUDA Init: Waiting for GPU..."

for i in $(seq 1 $MAX_RETRIES); do
    if nvidia-smi &>/dev/null; then
        echo "[$(date -Iseconds)] CUDA Init: GPU detected (attempt $i)"
        GPU_READY=true
        break
    fi
    echo "[$(date -Iseconds)] CUDA Init: GPU not ready, attempt $i/$MAX_RETRIES"
    sleep $RETRY_DELAY
done

if [ "$GPU_READY" = false ]; then
    echo "[$(date -Iseconds)] CUDA Init: ERROR - GPU not detected after $MAX_RETRIES attempts"
    exit 1
fi

nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader

# ============================================
# 3. CUDA Warmup
# ============================================

echo "[$(date -Iseconds)] CUDA Init: Warming up CUDA..."

PYTHON_BIN="${VENV_PATH:-/workspace/venv}/bin/python"
[ ! -f "$PYTHON_BIN" ] && PYTHON_BIN=$(which python3)

for attempt in 1 2 3; do
    if $PYTHON_BIN -c "
import torch
print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    torch.zeros(1).cuda()
    print('CUDA warmup successful')
else:
    exit(1)
" 2>&1; then
        echo "[$(date -Iseconds)] CUDA Init: Warmup complete"
        break
    else
        echo "[$(date -Iseconds)] CUDA Init: Warmup attempt $attempt failed"
        [ $attempt -lt 3 ] && sleep 3
    fi
done

echo "[$(date -Iseconds)] CUDA Init: Complete"
```

#### File 2: `/workspace/start_comfyui.sh`

```bash
#!/bin/bash
# start_comfyui.sh - ComfyUI startup with CUDA initialization

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/workspace/comfyui.log"
VENV_PATH="/workspace/venv"
COMFYUI_PATH="/workspace/ComfyUI"

echo "========================================" >> "$LOG_FILE"
echo "[$(date -Iseconds)] ComfyUI: Starting..." >> "$LOG_FILE"

# Source CUDA initialization
if [ -f "$SCRIPT_DIR/cuda_init.sh" ]; then
    source "$SCRIPT_DIR/cuda_init.sh" >> "$LOG_FILE" 2>&1
else
    export CUDA_VISIBLE_DEVICES=0
    export CUDA_DEVICE_ORDER=PCI_BUS_ID
fi

# Activate venv and start
source "$VENV_PATH/bin/activate"
cd "$COMFYUI_PATH"
exec "$VENV_PATH/bin/python" main.py --listen 0.0.0.0 --port 8188
```

#### File 3: `/workspace/check_cuda.py`

```python
#!/usr/bin/env python3
"""CUDA diagnostics for RunPod troubleshooting."""

import os
import subprocess

def main():
    print("=" * 50)
    print("CUDA DIAGNOSTICS")
    print("=" * 50)

    # Environment
    for var in ['CUDA_VISIBLE_DEVICES', 'CUDA_DEVICE_ORDER']:
        print(f"{var}: {os.environ.get(var, '<not set>')}")

    # Devices
    subprocess.run('ls -la /dev/nvidia* 2>/dev/null || echo "No devices"', shell=True)

    # PyTorch
    try:
        import torch
        print(f"\nPyTorch: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"Device: {torch.cuda.get_device_name(0)}")
            torch.zeros(1).cuda()
            print("CUDA TEST: PASSED")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()
```

#### Installation Commands

```bash
ssh runpod

# Create cuda_init.sh
cat > /workspace/cuda_init.sh << 'EOF'
#!/bin/bash
# ... (content above)
EOF
chmod +x /workspace/cuda_init.sh

# Create start_comfyui.sh
cat > /workspace/start_comfyui.sh << 'EOF'
#!/bin/bash
# ... (content above)
EOF
chmod +x /workspace/start_comfyui.sh

# Create check_cuda.py
cat > /workspace/check_cuda.py << 'EOF'
#!/usr/bin/env python3
# ... (content above)
EOF
chmod +x /workspace/check_cuda.py

# Test
source /workspace/cuda_init.sh
```

---

### Phase 2: Pod Template Configuration (10 min)

#### Option A: Environment Variables (Recommended)

In RunPod console (https://runpod.io/console/pods):
1. Edit pod `k02604uwhjq6dm`
2. Add environment variables:

| Variable | Value |
|----------|-------|
| `CUDA_VISIBLE_DEVICES` | `0` |
| `CUDA_DEVICE_ORDER` | `PCI_BUS_ID` |
| `NVIDIA_VISIBLE_DEVICES` | `all` |
| `NVIDIA_DRIVER_CAPABILITIES` | `compute,utility` |

#### Option B: Auto-Start Script

Create `/workspace/auto_start.sh`:
```bash
#!/bin/bash
export CUDA_VISIBLE_DEVICES=0
export CUDA_DEVICE_ORDER=PCI_BUS_ID

[ -d "/workspace/ComfyUI" ] && nohup /workspace/start_comfyui.sh >> /workspace/comfyui.log 2>&1 &
sleep infinity
```

Set Container Start Command: `/bin/bash /workspace/auto_start.sh`

---

### Phase 3: Validation (20 min)

#### Cold Start Test

```bash
# 1. Stop pod
RUNPOD_API_KEY=$(grep RUNPOD_API_KEY ~/.zshrc | cut -d= -f2 | tr -d '"')
curl -s --request POST \
  --header 'content-type: application/json' \
  --url "https://api.runpod.io/graphql?api_key=$RUNPOD_API_KEY" \
  --data '{"query": "mutation { podStop(input: { podId: \"k02604uwhjq6dm\" }) { id desiredStatus } }"}'

sleep 60

# 2. Start pod
curl -s --request POST \
  --header 'content-type: application/json' \
  --url "https://api.runpod.io/graphql?api_key=$RUNPOD_API_KEY" \
  --data '{"query": "mutation { podResume(input: { podId: \"k02604uwhjq6dm\" }) { id desiredStatus } }"}'

sleep 90

# 3. Get new SSH port and update ~/.ssh/config

# 4. Verify
ssh runpod "source /workspace/venv/bin/activate && python /workspace/check_cuda.py"
```

#### Success Criteria

| Check | Expected |
|-------|----------|
| `echo $CUDA_VISIBLE_DEVICES` | `0` |
| `python -c "import torch; print(torch.cuda.is_available())"` | `True` |
| `curl localhost:8188/system_stats` | JSON response |
| TTS generation | Audio file created |

---

## Quick Reference

### Startup Commands
```bash
# Manual start (after SSH)
nohup /workspace/start_comfyui.sh > /workspace/comfyui.log 2>&1 &

# Check status
curl localhost:8188/system_stats

# View logs
tail -f /workspace/comfyui.log
```

### Troubleshooting
```bash
# Full diagnostics
source /workspace/venv/bin/activate
python /workspace/check_cuda.py

# Manual CUDA fix
export CUDA_VISIBLE_DEVICES=0
export CUDA_DEVICE_ORDER=PCI_BUS_ID
```

### Pod Management
```bash
# API key
RUNPOD_API_KEY=$(grep RUNPOD_API_KEY ~/.zshrc | cut -d= -f2 | tr -d '"')

# Stop pod
curl -s --request POST \
  --header 'content-type: application/json' \
  --url "https://api.runpod.io/graphql?api_key=$RUNPOD_API_KEY" \
  --data '{"query": "mutation { podStop(input: { podId: \"k02604uwhjq6dm\" }) { id desiredStatus } }"}'

# Start pod
curl -s --request POST \
  --header 'content-type: application/json' \
  --url "https://api.runpod.io/graphql?api_key=$RUNPOD_API_KEY" \
  --data '{"query": "mutation { podResume(input: { podId: \"k02604uwhjq6dm\" }) { id desiredStatus } }"}'
```

---

## Files Summary

| File | Location | Purpose |
|------|----------|---------|
| `cuda_init.sh` | `/workspace/` | CUDA environment + GPU wait |
| `start_comfyui.sh` | `/workspace/` | ComfyUI launcher |
| `check_cuda.py` | `/workspace/` | Diagnostics |
| Pod env vars | RunPod console | CUDA_VISIBLE_DEVICES, etc. |

---

## Appendix: Research Sources

- [NVIDIA CUDA_VISIBLE_DEVICES](https://developer.nvidia.com/blog/cuda-pro-tip-control-gpu-visibility-cuda_visible_devices/)
- [RunPod Templates](https://docs.runpod.io/pods/templates/overview)
- [PyTorch CUDA Compatibility](https://discuss.pytorch.org/t/cuda-versioning-and-pytorch-compatibility/189777)
- [GPU Device Ordering](https://docs.rapids.ai/api/dask-cuda/nightly/troubleshooting/)
- [Cold Start Race Conditions](https://learn.microsoft.com/en-us/answers/questions/2285401/tasks-fail-to-detect-gpu-on-some-pool-nodes-due-to)

---

*PRD created: 2025-12-23*
*Estimated implementation time: 45 minutes*
*Pod: k02604uwhjq6dm (vibevoice)*
