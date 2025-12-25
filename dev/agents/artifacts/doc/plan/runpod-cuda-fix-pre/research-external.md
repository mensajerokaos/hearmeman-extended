---
author: oz
model: claude-opus-4-5-20251101
date: 2025-12-23T22:45:00Z
task: External research for RunPod CUDA initialization fix
sources: web search, RunPod docs, NVIDIA docs, PyTorch forums
---

# External Research: CUDA Initialization Fixes for RunPod

## 1. CUDA_ERROR_NOT_INITIALIZED (Error Code 3)

### What It Means
According to [NVIDIA CUDA Driver API documentation](https://docs.nvidia.com/cuda/cuda-driver-api/group__CUDA__INITIALIZE.html):
> "If cuInit() has not been called, any function from the driver API will return CUDA_ERROR_NOT_INITIALIZED."

### Root Causes in Cloud/Container Environments

1. **Cold Start Race Condition**
   - GPU driver not fully initialized when first task runs
   - Affects ~10% of new nodes on cloud GPU platforms
   - Later tasks on same node succeed
   - Source: [Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/2285401/tasks-fail-to-detect-gpu-on-some-pool-nodes-due-to)

2. **CUDA Runtime vs Driver Mismatch**
   - PyTorch cu118 bundled with CUDA 11.8 runtime
   - Driver supports CUDA 12.7
   - Generally backward compatible, but can cause issues
   - Source: [PyTorch Forums](https://discuss.pytorch.org/t/cuda-versioning-and-pytorch-compatibility/189777)

3. **Device Index Mismatch**
   - `/dev/nvidia8` exists but `/dev/nvidia0` doesn't
   - CUDA expects device 0 by default
   - Multi-GPU hosts assign non-zero indices
   - Source: [NVIDIA Blog](https://developer.nvidia.com/blog/cuda-pro-tip-control-gpu-visibility-cuda_visible_devices/)

---

## 2. GPU Device Mapping Problem

### The Issue
When RunPod assigns a GPU from a multi-GPU host:
- The container sees only the allocated GPU
- But the device keeps its original index (e.g., `/dev/nvidia8`)
- CUDA applications expect `/dev/nvidia0` by default

### Why `nvidia-smi` Works but `torch.cuda.is_available()` Fails
From [PyTorch Forums](https://discuss.pytorch.org/t/torch-cuda-is-available-returns-false-nvidia-smi-is-working/20614):
- `nvidia-smi` uses NVML API (works with any device index)
- PyTorch's CUDA detection may fail with non-zero device indices
- Library conflicts in containers can override CUDA detection

### Device Ordering Issue
From [dask-cuda documentation](https://docs.rapids.ai/api/dask-cuda/nightly/troubleshooting/):
> "While CUDA_VISIBLE_DEVICES indexes GPUs by their PCI Bus ID, nvidia-smi orders by fastest GPUs."

---

## 3. Environment Variable Fixes

### CUDA_VISIBLE_DEVICES
From [NVIDIA CUDA Pro Tips](https://developer.nvidia.com/blog/cuda-pro-tip-control-gpu-visibility-cuda_visible_devices/):

```bash
# Remap device 8 to appear as device 0
export CUDA_VISIBLE_DEVICES=0

# Or use GPU UUID for absolute reliability
export CUDA_VISIBLE_DEVICES=GPU-xxxxx-xxxx-xxxx-xxxx
```

**How it works**: Only devices in the list are visible to CUDA, enumerated in order starting from 0.

### CUDA_DEVICE_ORDER
From [gpustack GitHub issue](https://github.com/gpustack/gpustack/issues/1633):

```bash
export CUDA_DEVICE_ORDER=PCI_BUS_ID
```

**Why**: Ensures GPU ordering matches `nvidia-smi` output instead of using "fastest first" heuristic.

### NVIDIA Container Environment Variables
From [NVIDIA Container Toolkit docs](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/docker-specialized.html):

```bash
# For custom CUDA containers
export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=compute,utility
```

---

## 4. PyTorch CUDA Version Compatibility

### The cu118 vs CUDA 12.7 Driver Situation
From [PyTorch Forums](https://discuss.pytorch.org/t/cuda-versioning-and-pytorch-compatibility/189777):

> "PyTorch bundles its own CUDA runtime, but your driver must support it. If your driver supports CUDA 12.1+, you can use any lower CUDA version."

**This means**: CUDA 12.7 driver IS backward compatible with cu118 (CUDA 11.8).

### Recommended Fix
Upgrade PyTorch to match driver capabilities:

```bash
# Option 1: Use cu121 (CUDA 12.1)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Option 2: Use cu124 (CUDA 12.4) - closest to driver
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

---

## 5. RunPod-Specific Solutions

### Pod Template Configuration
From [RunPod Documentation](https://docs.runpod.io/pods/templates/overview):

Templates support:
- **Startup commands**: Run on pod launch
- **Environment variables**: Pre-configured settings
- **Container start command**: Custom entrypoint

**JSON format for custom entrypoint**:
```json
{ "cmd": ["bash", "/workspace/start.sh"], "entrypoint": ["bash", "-c"] }
```

### FlashBoot (Cold Start Optimization)
From [RunPod Blog](https://www.runpod.io/blog/introducing-flashboot-serverless-cold-start):
- Pre-warms GPU infrastructure
- Reduces cold start time
- More popular endpoints get better FlashBoot

### Active Workers (Eliminate Cold Starts)
From [RunPod Blog](https://www.runpod.io/blog/avoid-pod-errors-runpod-resources):
> "Setting active workers to 1 or higher eliminates cold starts for initial requests."

---

## 6. Retry and Warmup Patterns

### GPU Initialization Retry
From [Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/2285401/tasks-fail-to-detect-gpu-on-some-pool-nodes-due-to):

```python
import time
import torch

def wait_for_gpu(max_retries=10, delay=3):
    for i in range(max_retries):
        try:
            if torch.cuda.is_available():
                # Warmup: Create small tensor on GPU
                torch.zeros(1).cuda()
                print(f"GPU ready after {i+1} attempts")
                return True
        except Exception as e:
            print(f"GPU init attempt {i+1} failed: {e}")
            time.sleep(delay)
    return False
```

### CUDA Warmup Before App Start
From [RunPod Guides](https://www.runpod.io/articles/guides/deploy-fastapi-applications-gpu-cloud):
> "Preload or 'warm up' your model on startup. Call `model(torch.randn(1,10).to(device))` once at launch to ensure CUDA kernels are initialized."

### Reloading nvidia_uvm Module
From [kdave blog](https://kdave.github.io/cuda-unknown-error/):
> "Reloading kernel module nvidia_uvm can solve CUDA initialization errors after resume or cold start."

```bash
sudo modprobe -r nvidia_uvm
sudo modprobe nvidia_uvm
```

---

## 7. Container-Specific Issues

### Docker GPU Access
From [Docker GPU Docs](https://docs.docker.com/compose/how-tos/gpu-support/):

```bash
# Correct way to run container with GPU
docker run --gpus all ...
# or
docker run --runtime=nvidia ...
```

### NVIDIA Container Toolkit
From [NVIDIA docs](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/docker-specialized.html):
- `NVIDIA_VISIBLE_DEVICES` controls GPU access
- `NVIDIA_DRIVER_CAPABILITIES=compute,utility` for CUDA apps

### Library Conflicts
From [PyTorch GitHub](https://github.com/pytorch/pytorch/issues/98885):
> "Installing additional libraries via requirements.txt can override pre-installed PyTorch CUDA libraries, causing torch.cuda.is_available() to return False."

---

## 8. Diagnostic Commands

### Check GPU Device
```bash
# List NVIDIA devices
ls -la /dev/nvidia*

# Get GPU info
nvidia-smi

# Get GPU UUID (useful for CUDA_VISIBLE_DEVICES)
nvidia-smi -L

# Check CUDA version
nvidia-smi | grep "CUDA Version"
```

### Check PyTorch CUDA
```python
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"cuDNN version: {torch.backends.cudnn.version()}")
print(f"Device count: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"Current device: {torch.cuda.current_device()}")
    print(f"Device name: {torch.cuda.get_device_name(0)}")
```

---

## 9. Recommended Fix Strategy

### Phase 1: Environment Variables
```bash
export CUDA_VISIBLE_DEVICES=0
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=compute,utility
```

### Phase 2: Startup Script with Retry
```bash
#!/bin/bash
# Wait for GPU to be ready
MAX_RETRIES=10
RETRY_DELAY=3

for i in $(seq 1 $MAX_RETRIES); do
    if nvidia-smi &>/dev/null; then
        echo "GPU detected on attempt $i"
        break
    fi
    echo "Waiting for GPU... attempt $i"
    sleep $RETRY_DELAY
done

# Warmup CUDA
python3 -c "import torch; torch.zeros(1).cuda(); print('CUDA warmup complete')" || {
    echo "CUDA warmup failed, retrying..."
    sleep 5
    python3 -c "import torch; torch.zeros(1).cuda(); print('CUDA warmup complete')"
}

# Start application
exec /workspace/venv/bin/python /workspace/ComfyUI/main.py --listen 0.0.0.0 --port 8188
```

### Phase 3: PyTorch Upgrade
```bash
source /workspace/venv/bin/activate
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

---

## 10. Sources

### Official Documentation
- [NVIDIA CUDA Driver API](https://docs.nvidia.com/cuda/cuda-driver-api/group__CUDA__INITIALIZE.html)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/docker-specialized.html)
- [RunPod Templates Documentation](https://docs.runpod.io/pods/templates/overview)
- [RunPod GPU Pricing](https://www.runpod.io/gpu-pricing)

### PyTorch Resources
- [PyTorch CUDA Compatibility](https://discuss.pytorch.org/t/cuda-versioning-and-pytorch-compatibility/189777)
- [torch.cuda.is_available() False Issues](https://discuss.pytorch.org/t/torch-cuda-is-available-returns-false-nvidia-smi-is-working/20614)
- [PyTorch GitHub Issue #98885](https://github.com/pytorch/pytorch/issues/98885)

### RunPod Resources
- [Avoid Pod Errors](https://www.runpod.io/blog/avoid-pod-errors-runpod-resources)
- [FlashBoot Cold Start](https://www.runpod.io/blog/introducing-flashboot-serverless-cold-start)
- [Deploy FastAPI with GPU](https://www.runpod.io/articles/guides/deploy-fastapi-applications-gpu-cloud)

### GPU Device Ordering
- [NVIDIA CUDA_VISIBLE_DEVICES](https://developer.nvidia.com/blog/cuda-pro-tip-control-gpu-visibility-cuda_visible_devices/)
- [dask-cuda Troubleshooting](https://docs.rapids.ai/api/dask-cuda/nightly/troubleshooting/)
- [gpustack Device Order Issue](https://github.com/gpustack/gpustack/issues/1633)

### Cold Start Issues
- [Microsoft GPU Cold Start Race Condition](https://learn.microsoft.com/en-us/answers/questions/2285401/tasks-fail-to-detect-gpu-on-some-pool-nodes-due-to)
- [CUDA Unknown Error Fix](https://kdave.github.io/cuda-unknown-error/)
