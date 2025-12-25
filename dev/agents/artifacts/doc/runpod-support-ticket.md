---
task: RunPod Support Ticket - CUDA Device Mount Issue
agent: hc (headless claude)
model: claude-opus-4-5-20251101
timestamp: 2025-12-23T12:45:00Z
status: completed
---

# RunPod Support Ticket: CUDA Initialization Failure Due to Read-Only Device Mounts

## Subject Line

**CUDA Error 3 (NOT_INITIALIZED): NVIDIA device files mounted read-only preventing CUDA initialization - Pod k02604uwhjq6dm**

---

## Pod Details

| Property | Value |
|----------|-------|
| **Pod ID** | `k02604uwhjq6dm` |
| **Pod Name** | vibevoice |
| **GPU** | NVIDIA RTX A6000 (48GB VRAM) |
| **Region** | EU-SE-1 |
| **Network Volume** | `ul56y9ya5h` (50GB) |
| **Container Image** | `runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04` |
| **Driver Version** | 565.57.01 |
| **CUDA Driver API** | 12.7 (cuDriverGetVersion returns 12070) |

---

## Problem Description

The GPU is properly detected by NVML (nvidia-smi works perfectly), but CUDA fails to initialize with error code 3 (`CUDA_ERROR_NOT_INITIALIZED`). This prevents PyTorch, ComfyUI, and any CUDA-based workload from utilizing the GPU.

### Symptoms

1. `nvidia-smi` displays GPU information correctly
2. NVML API calls succeed (nvmlInit returns 0)
3. GPU is detected (nvmlDeviceGetCount returns 1)
4. CUDA initialization fails: `cuInit(0)` returns error 3
5. PyTorch reports: `torch.cuda.is_available()` = `False`
6. ComfyUI falls back to CPU execution

### Impact

- Cannot run VibeVoice TTS (requires CUDA)
- Cannot run ComfyUI workflows (GPU acceleration unavailable)
- Pod is effectively unusable for its intended purpose
- Paying for A6000 GPU that cannot be utilized

---

## Diagnostic Evidence

### Test 1: nvidia-smi (WORKS)

```bash
$ nvidia-smi
Mon Dec 23 12:00:00 2025
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 565.57.01              Driver Version: 565.57.01      CUDA Version: 12.7     |
|-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|=========================================+========================+======================|
|   0  NVIDIA RTX A6000               On  | 00000000:C1:00.0  Off |                  Off |
| 30%   34C    P8              24W / 300W |       0MiB / 49140MiB |      0%      Default |
+-----------------------------------------+------------------------+----------------------+
```

### Test 2: NVML API (WORKS)

```python
>>> import pynvml
>>> pynvml.nvmlInit()  # Returns successfully
>>> pynvml.nvmlDeviceGetCount()
1
>>> handle = pynvml.nvmlDeviceGetHandleByIndex(0)
>>> pynvml.nvmlDeviceGetName(handle)
'NVIDIA RTX A6000'
```

### Test 3: CUDA Driver API (FAILS)

```python
>>> import ctypes
>>> libcuda = ctypes.CDLL("libcuda.so")
>>>
>>> # Driver version check - WORKS
>>> version = ctypes.c_int()
>>> libcuda.cuDriverGetVersion(ctypes.byref(version))
0  # Success
>>> version.value
12070  # CUDA 12.7 - correct!
>>>
>>> # CUDA initialization - FAILS
>>> result = libcuda.cuInit(0)
>>> result
3  # CUDA_ERROR_NOT_INITIALIZED
```

### Test 4: PyTorch CUDA Check (FAILS)

```python
>>> import torch
>>> torch.cuda.is_available()
False
>>> torch.cuda.device_count()
0
```

### Test 5: Device Mount Permissions (ROOT CAUSE)

```bash
$ cat /proc/self/mountinfo | grep nvidia
... /dev/nvidia8 ... ro,nosuid,noexec,relatime ...
... /dev/nvidiactl ... ro,nosuid,noexec,relatime ...
... /dev/nvidia-uvm ... ro,nosuid,noexec,relatime ...
```

**Key finding**: The `ro` (read-only) flag is present on all NVIDIA device mounts.

### Test 6: Device File Verification

```bash
$ ls -la /dev/nvidia*
crw-rw-rw- 1 root root 195,   8 Dec 23 10:00 /dev/nvidia8
crw-rw-rw- 1 root root 195, 255 Dec 23 10:00 /dev/nvidiactl
crw-rw-rw- 1 root root 511,   0 Dec 23 10:00 /dev/nvidia-uvm
crw-rw-rw- 1 root root 511,   1 Dec 23 10:00 /dev/nvidia-uvm-tools

$ file /dev/nvidia8
/dev/nvidia8: character special (195/8)
```

---

## Root Cause Analysis

### Why NVML Works but CUDA Fails

| Component | Access Required | Current Mount | Status |
|-----------|-----------------|---------------|--------|
| NVML (nvidia-smi) | Read-only | ro | WORKS |
| CUDA Runtime | Read-write | ro | FAILS |

**NVML** (NVIDIA Management Library) only requires read access to query GPU status, temperature, memory usage, etc. This is why `nvidia-smi` works perfectly.

**CUDA** requires read-write access to the device files for:
- Memory allocation on GPU
- Kernel execution
- Context creation
- Stream management

The `cuInit()` function attempts to open device files with write permissions. When devices are mounted read-only, this fails with error 3 (`CUDA_ERROR_NOT_INITIALIZED`).

### Evidence from NVIDIA Documentation

Per [NVIDIA Container Toolkit Troubleshooting](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/troubleshooting.html):

> "When using nvidia-container-runtime or nvidia-container-toolkit with cgroup option, it automatically allocates machine resources for the container. When bypassing this option, you need to allocate resources manually by specifying devices like `/dev/nvidia0`, `/dev/nvidiactl`, `/dev/nvidia-modeset`, `/dev/nvidia-uvm`, `/dev/nvidia-uvm-tools`"

The container requires proper read-write access to these devices for CUDA to function.

---

## Request for Fix

### Immediate Ask

Please investigate why the NVIDIA device files (`/dev/nvidia*`, `/dev/nvidiactl`, `/dev/nvidia-uvm*`) are being mounted with read-only (`ro`) permissions in pod `k02604uwhjq6dm`.

### Expected Resolution

The device mounts should have read-write (`rw`) permissions:
```
/dev/nvidia8 rw,nosuid,noexec,relatime
/dev/nvidiactl rw,nosuid,noexec,relatime
/dev/nvidia-uvm rw,nosuid,noexec,relatime
```

### Potential Solutions (for RunPod team)

1. **Check container runtime configuration** - Ensure nvidia-container-toolkit is mounting devices with `rw` permissions
2. **Verify cgroup configuration** - Per NVIDIA's guidance, systemd cgroup driver can cause device access issues
3. **Create /dev/char symlinks** - Run `nvidia-ctk system create-dev-char-symlinks --create-all` on the host
4. **Check for host-level changes** - Recent `systemctl daemon-reload` can cause containers to lose GPU access

### Workaround Attempted (Did Not Work)

- Terminating and redeploying the pod (same issue on new pod)
- Changing container images (same issue with different PyTorch versions)
- Restarting the pod multiple times

---

## Similar Issues Found Online

### RunPod-Specific

1. **[CUDA error using official image - Issue #67](https://github.com/runpod/containers/issues/67)** - Users report CUDA initialization failures with official RunPod images
2. **[Pod is unable to find/use GPU in python](https://www.answeroverflow.com/m/1210557591483318282)** - Community discussion about GPU detection issues
3. **[ComfyUI CPU Instead of GPU Fix 2025](https://apatero.com/blog/comfyui-cpu-instead-gpu-runpod-fix-troubleshooting-2025)** - Troubleshooting guide for GPU access issues

### NVIDIA Container Toolkit

4. **[Failure to call cuInit in nvidia-docker2](https://forums.developer.nvidia.com/t/failure-to-call-to-cuinit-in-nvidia-docker2/252481)** - NVIDIA forum discussion on cuInit failures in Docker
5. **[NOTICE: Containers losing access to GPUs](https://github.com/NVIDIA/nvidia-container-toolkit/issues/48)** - Official NVIDIA issue about containers losing GPU access due to cgroup/systemd interactions
6. **[Unreliable cuInit with sandboxes and containers](https://forums.developer.nvidia.com/t/unrelaibale-cuinit-with-sandboxes-and-containers-cuda-cuinit-unknown-error/333562)** - NVIDIA forum thread about cuInit failures in containerized environments

### Related Docker/Container Issues

7. **[nvidia-smi is OK, torch.cuda.is_available() FAILS in Docker](https://discuss.pytorch.org/t/nvidia-smi-is-ok-torch-cuda-is-available-fails-in-docker/163107)** - PyTorch forum discussion matching our exact symptoms
8. **[CUDA Failing to initialize in docker container - Issue #7262](https://github.com/triton-inference-server/server/issues/7262)** - Triton Server issue with same cuInit error
9. **[Problems with "no cuda-capable device is detected" after Ubuntu upgrade](https://github.com/NVIDIA/libnvidia-container/issues/37)** - libnvidia-container issue about device access problems

### NVIDIA Official Guidance

10. **[NVIDIA Container Toolkit Troubleshooting](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/troubleshooting.html)** - Official troubleshooting documentation mentioning device mount requirements

---

## Additional Context

### Timeline

- Pod created: Working initially (CUDA functional)
- Issue started: After pod restart/migration (exact date unknown)
- Current status: Completely unable to use CUDA

### Previous Successful Configuration

The same pod configuration worked previously, suggesting this is an infrastructure-level change rather than a configuration issue on our end.

### Business Impact

This pod is used for AI voice generation (VibeVoice TTS) for a documentary project. The inability to use the GPU is blocking production work.

---

## Contact Information

Please respond to this ticket with:
1. Confirmation of the root cause
2. ETA for resolution
3. Any temporary workarounds available

Thank you for your assistance.
