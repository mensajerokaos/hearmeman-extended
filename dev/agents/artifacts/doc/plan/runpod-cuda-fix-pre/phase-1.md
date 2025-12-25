---
phase: 1
title: Startup Script Fix
duration: 15 minutes
author: oz
model: claude-opus-4-5-20251101
---

# Phase 1: Startup Script Fix

## Prerequisites

- [ ] SSH access to RunPod pod (`ssh runpod`)
- [ ] Pod is running (`desiredStatus: RUNNING`)
- [ ] Network volume mounted at `/workspace`

## Objective

Create a robust startup script that:
1. Sets CUDA environment variables for device remapping
2. Waits for GPU to be available (retry loop)
3. Warms up CUDA before starting the application
4. Starts ComfyUI with proper error handling

---

## File 1: `/workspace/cuda_init.sh`

### Purpose
Environment setup and GPU initialization script. Called before any CUDA-dependent application.

### Content
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

# Remap whatever GPU device to index 0
# This fixes /dev/nvidia8 appearing instead of /dev/nvidia0
export CUDA_VISIBLE_DEVICES=0

# Use PCI Bus ID ordering for consistency with nvidia-smi
export CUDA_DEVICE_ORDER=PCI_BUS_ID

# NVIDIA container runtime settings
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

# Show GPU info
echo "[$(date -Iseconds)] CUDA Init: GPU Info:"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader

# ============================================
# 3. CUDA Warmup
# ============================================

echo "[$(date -Iseconds)] CUDA Init: Warming up CUDA..."

# Use the venv Python
PYTHON_BIN="${VENV_PATH:-/workspace/venv}/bin/python"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "[$(date -Iseconds)] CUDA Init: WARNING - venv Python not found at $PYTHON_BIN"
    PYTHON_BIN=$(which python3)
fi

# Warmup with retry
for attempt in 1 2 3; do
    if $PYTHON_BIN -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'Device count: {torch.cuda.device_count()}')
    print(f'Device name: {torch.cuda.get_device_name(0)}')
    # Warmup tensor operation
    x = torch.zeros(1).cuda()
    del x
    print('CUDA warmup successful')
else:
    exit(1)
" 2>&1; then
        echo "[$(date -Iseconds)] CUDA Init: Warmup complete"
        break
    else
        echo "[$(date -Iseconds)] CUDA Init: Warmup attempt $attempt failed"
        if [ $attempt -lt 3 ]; then
            sleep 3
        else
            echo "[$(date -Iseconds)] CUDA Init: WARNING - CUDA warmup failed after 3 attempts"
            # Don't exit, let the application try anyway
        fi
    fi
done

echo "[$(date -Iseconds)] CUDA Init: Complete"
```

### Installation
```bash
cat > /workspace/cuda_init.sh << 'SCRIPT_END'
# ... (content above)
SCRIPT_END
chmod +x /workspace/cuda_init.sh
```

---

## File 2: `/workspace/start_comfyui.sh` (Updated)

### Purpose
Start ComfyUI with CUDA initialization. Replaces the original simple starter.

### Content
```bash
#!/bin/bash
# start_comfyui.sh - ComfyUI startup with CUDA initialization
# For RunPod pod: k02604uwhjq6dm

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/workspace/comfyui.log"
VENV_PATH="/workspace/venv"
COMFYUI_PATH="/workspace/ComfyUI"

echo "========================================" >> "$LOG_FILE"
echo "[$(date -Iseconds)] ComfyUI: Starting..." >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Source CUDA initialization
if [ -f "$SCRIPT_DIR/cuda_init.sh" ]; then
    echo "[$(date -Iseconds)] ComfyUI: Running CUDA init..." >> "$LOG_FILE"
    source "$SCRIPT_DIR/cuda_init.sh" >> "$LOG_FILE" 2>&1
else
    echo "[$(date -Iseconds)] ComfyUI: WARNING - cuda_init.sh not found" >> "$LOG_FILE"
    # Set minimal CUDA env vars as fallback
    export CUDA_VISIBLE_DEVICES=0
    export CUDA_DEVICE_ORDER=PCI_BUS_ID
fi

# Activate venv
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo "[$(date -Iseconds)] ComfyUI: Activated venv at $VENV_PATH" >> "$LOG_FILE"
else
    echo "[$(date -Iseconds)] ComfyUI: ERROR - venv not found at $VENV_PATH" >> "$LOG_FILE"
    exit 1
fi

# Start ComfyUI
cd "$COMFYUI_PATH"
echo "[$(date -Iseconds)] ComfyUI: Launching main.py..." >> "$LOG_FILE"
exec "$VENV_PATH/bin/python" main.py --listen 0.0.0.0 --port 8188
```

### Installation
```bash
cat > /workspace/start_comfyui.sh << 'SCRIPT_END'
# ... (content above)
SCRIPT_END
chmod +x /workspace/start_comfyui.sh
```

---

## File 3: `/workspace/check_cuda.py`

### Purpose
Diagnostic script to verify CUDA is working. Run manually for troubleshooting.

### Content
```python
#!/usr/bin/env python3
"""CUDA diagnostics for RunPod pod troubleshooting."""

import os
import sys
import subprocess

def check_environment():
    """Print CUDA-related environment variables."""
    print("=" * 50)
    print("ENVIRONMENT VARIABLES")
    print("=" * 50)
    cuda_vars = [
        'CUDA_VISIBLE_DEVICES',
        'CUDA_DEVICE_ORDER',
        'NVIDIA_VISIBLE_DEVICES',
        'NVIDIA_DRIVER_CAPABILITIES',
    ]
    for var in cuda_vars:
        value = os.environ.get(var, '<not set>')
        print(f"  {var}: {value}")
    print()

def check_nvidia_smi():
    """Run nvidia-smi and show output."""
    print("=" * 50)
    print("NVIDIA-SMI")
    print("=" * 50)
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"ERROR: {result.stderr}")
    except FileNotFoundError:
        print("ERROR: nvidia-smi not found")
    print()

def check_devices():
    """List /dev/nvidia* devices."""
    print("=" * 50)
    print("NVIDIA DEVICES")
    print("=" * 50)
    try:
        result = subprocess.run(['ls', '-la', '/dev/nvidia*'],
                              capture_output=True, text=True, shell=False)
        # Use shell for glob expansion
        result = subprocess.run('ls -la /dev/nvidia* 2>/dev/null || echo "No /dev/nvidia* devices found"',
                              shell=True, capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"ERROR: {e}")
    print()

def check_pytorch():
    """Check PyTorch CUDA support."""
    print("=" * 50)
    print("PYTORCH CUDA")
    print("=" * 50)
    try:
        import torch
        print(f"  PyTorch version: {torch.__version__}")
        print(f"  CUDA available: {torch.cuda.is_available()}")
        print(f"  CUDA version: {torch.version.cuda}")
        print(f"  cuDNN version: {torch.backends.cudnn.version()}")
        print(f"  Device count: {torch.cuda.device_count()}")

        if torch.cuda.is_available():
            print(f"  Current device: {torch.cuda.current_device()}")
            print(f"  Device name: {torch.cuda.get_device_name(0)}")

            # Test tensor creation
            print("\n  Testing tensor creation on GPU...")
            x = torch.zeros(100, 100).cuda()
            print(f"  Created tensor: {x.shape} on {x.device}")
            del x
            print("  SUCCESS: CUDA is working!")
        else:
            print("\n  CUDA NOT AVAILABLE - Check:")
            print("  1. CUDA_VISIBLE_DEVICES environment variable")
            print("  2. GPU device files in /dev/nvidia*")
            print("  3. PyTorch CUDA version vs driver version")

    except ImportError:
        print("ERROR: PyTorch not installed")
    except Exception as e:
        print(f"ERROR: {e}")
    print()

def main():
    print("\n" + "=" * 50)
    print("CUDA DIAGNOSTICS")
    print("=" * 50 + "\n")

    check_environment()
    check_nvidia_smi()
    check_devices()
    check_pytorch()

    print("=" * 50)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()
```

### Installation
```bash
cat > /workspace/check_cuda.py << 'SCRIPT_END'
# ... (content above)
SCRIPT_END
chmod +x /workspace/check_cuda.py
```

### Usage
```bash
source /workspace/venv/bin/activate
python /workspace/check_cuda.py
```

---

## Verification Steps

### 1. SSH into Pod
```bash
ssh runpod
```

### 2. Install Scripts
Copy and paste the installation commands for each script.

### 3. Test CUDA Init
```bash
source /workspace/cuda_init.sh
echo "Exit code: $?"
```

Expected output:
```
[timestamp] CUDA Init: Starting...
[timestamp] CUDA Init: Environment variables set
  CUDA_VISIBLE_DEVICES=0
  CUDA_DEVICE_ORDER=PCI_BUS_ID
[timestamp] CUDA Init: Waiting for GPU...
[timestamp] CUDA Init: GPU detected (attempt 1)
[timestamp] CUDA Init: GPU Info:
NVIDIA RTX A6000, 48685 MiB, 535.xxx
[timestamp] CUDA Init: Warming up CUDA...
PyTorch version: 2.x.x+cuXXX
CUDA available: True
...
[timestamp] CUDA Init: Complete
```

### 4. Test Check Script
```bash
source /workspace/venv/bin/activate
python /workspace/check_cuda.py
```

### 5. Test ComfyUI Start
```bash
pkill -f "python.*main.py" || true
nohup /workspace/start_comfyui.sh > /workspace/comfyui.log 2>&1 &
sleep 10
tail -50 /workspace/comfyui.log
```

---

## Rollback Plan

If scripts cause issues:

### 1. Restore Original Starter
```bash
cat > /workspace/start_comfyui.sh << 'EOF'
#!/bin/bash
cd /workspace/ComfyUI
exec /workspace/venv/bin/python main.py --listen 0.0.0.0 --port 8188
EOF
chmod +x /workspace/start_comfyui.sh
```

### 2. Remove CUDA Init
```bash
rm /workspace/cuda_init.sh
rm /workspace/check_cuda.py
```

### 3. Manual CUDA Fix
If needed, set env vars manually before starting:
```bash
export CUDA_VISIBLE_DEVICES=0
export CUDA_DEVICE_ORDER=PCI_BUS_ID
/workspace/start_comfyui.sh
```

---

## Next Phase

After Phase 1 is verified working:
- Proceed to Phase 2: Pod Template Configuration
- Configure auto-run on cold start
