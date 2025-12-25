---
task: Research RunPod NVIDIA device read-only mount issue causing CUDA initialization failure
agent: hc (headless claude)
model: claude-opus-4-5-20251101
author: oz
timestamp: 2025-12-23T15:30:00Z
status: completed
---

# RunPod NVIDIA Device Read-Only Mount Issue Research

## Problem Summary

- **Environment**: RunPod pod with NVIDIA RTX A6000 GPU (48GB VRAM)
- **Symptom**: `nvidia-smi` works, NVML API works, but CUDA fails with `cuInit error 3` (CUDA_ERROR_NOT_INITIALIZED)
- **Root Cause**: NVIDIA device files mounted as READ-ONLY in container:
  ```
  /dev/nvidia8 ro,nosuid,noexec
  /dev/nvidiactl ro,nosuid,noexec
  /dev/nvidia-uvm ro,nosuid,noexec
  ```
- **Impact**: CUDA requires read-write access to these device files for initialization

## Analysis

### Why This Happens

1. **NVML vs CUDA Distinction**: NVML (nvidia-smi) only needs read access for monitoring. CUDA needs write access for compute operations.

2. **Container Runtime Configuration**: The nvidia-container-runtime controls how device files are mounted. Read-only mounts typically indicate:
   - Host-level security configuration
   - nvidia-container-runtime misconfiguration
   - Intentional restriction by cloud provider

3. **RunPod-Specific Context**: This appears to be a host-side configuration issue, not something controllable from within the pod.

## Solutions (Ranked by Feasibility)

### 1. [HIGH] Contact RunPod Support - RECOMMENDED

**Feasibility: Highest | Effort: Low**

This is a host-level configuration issue that only RunPod can fix.

**Actions:**
- File support ticket at help@runpod.io
- Post in RunPod Discord with Pod ID for staff review
- Include diagnostic output:
  ```bash
  nvidia-smi
  cat /proc/mounts | grep nvidia
  python3 -c "import torch; print(torch.cuda.is_available())"
  ```

**Key Points:**
- Reference the specific pod ID so they can inspect the host
- Note that `nvidia-smi` works but CUDA fails with error 3
- Show the read-only mount evidence from `/proc/mounts`

Sources:
- [RunPod Documentation - Troubleshooting](https://docs.runpod.io/references/troubleshooting/zero-gpus)
- [RunPod Community - Answer Overflow](https://www.answeroverflow.com/c/912829806415085598)

---

### 2. [HIGH] Terminate and Redeploy Pod

**Feasibility: High | Effort: Low**

The issue may be specific to a faulty host machine.

**Actions:**
```bash
# Save any work to network volume first
# Then terminate via RunPod console and create new pod
```

**Why This Works:**
- Different physical machine may have correct device permissions
- RunPod assigns pods to random available machines
- Some hosts may have misconfigurations

**Caveat:** Data on local storage will be lost. Use network volumes.

Sources:
- [RunPod Blog - Avoid Pod Errors](https://www.runpod.io/blog/avoid-pod-errors-runpod-resources)
- [Zero GPU Pods on restart](https://docs.runpod.io/references/faq)

---

### 3. [MEDIUM] Try Different GPU Type

**Feasibility: Medium | Effort: Low-Medium**

**Actions:**
- Deploy on different GPU (RTX 4090, RTX 3090, H100)
- Use CUDA version filter to select 12.2 specifically

**Rationale:**
- A6000 may have specific host configuration issues in some regions
- Different GPU pools may have different host configurations

Sources:
- [Pod is unable to find/use GPU in python - Runpod](https://www.answeroverflow.com/m/1210557591483318282)

---

### 4. [MEDIUM] Use Official RunPod PyTorch Template

**Feasibility: Medium | Effort: Medium**

Custom Docker images may trigger different container runtime behavior.

**Actions:**
- Deploy using `runpod/pytorch:2.4.0-py3.11-cuda12.4.0-devel-ubuntu22.04`
- Test CUDA before installing custom software

**Why:**
> "RunPod's infrastructure ensures the NVIDIA drivers on the host are compatible with CUDA 12.4 in the container"

Sources:
- [Get Started with PyTorch 2.4 and CUDA 12.4 on Runpod](https://www.runpod.io/articles/guides/pytorch-2-4-cuda-12-4)

---

### 5. [LOW] CUDA Version Filter

**Feasibility: Medium | Effort: Low**

**Actions:**
- When deploying, use filter button at top of RunPod pod selection
- Select "Allowed CUDA Versions: 12.2"
- Avoid CUDA 12.3 (reported as "not production ready")

**Quote from RunPod:**
> "because the machine is running CUDA 12.3 which is not production ready... select 12.2 as 'Allowed CUDA Versions'"

Sources:
- [cuda error using official image - Issue #67](https://github.com/runpod/containers/issues/67)

---

### 6. [LOW] Try Different Region

**Feasibility: Low-Medium | Effort: Low**

Different RunPod regions have different host configurations.

**Actions:**
- Deploy in EU-CZ-1, US-GA-1, or other regions
- Avoid the region where the issue occurred

---

## Solutions NOT Possible (User Cannot Control)

### Cannot Modify Device Mount Options
- Device mounts are set by nvidia-container-runtime on host
- No pod-level configuration to override `ro` to `rw`
- This is intentionally not exposed to users for security

### Cannot Use Privileged Mode
- RunPod does not expose `--privileged` flag
- Cannot use `--cap-add=SYS_ADMIN` directly
- Container security model restricts this

### Cannot Modify Host nvidia-container-runtime Config
- `/etc/nvidia-container-runtime/config.toml` is on host
- Users cannot access host filesystem

Sources:
- [Can we support set permission for GPU - Issue #267](https://github.com/NVIDIA/nvidia-container-toolkit/issues/267)
- [NVIDIA Container Toolkit Troubleshooting](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/troubleshooting.html)

---

## Diagnostic Commands

Run these to gather evidence for support ticket:

```bash
# 1. Check GPU detection
nvidia-smi

# 2. Check device mount options (the critical evidence)
cat /proc/mounts | grep nvidia

# 3. Check CUDA from Python
python3 -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('Device count:', torch.cuda.device_count())"

# 4. Check cuInit directly
python3 << 'EOF'
import ctypes
libcuda = ctypes.CDLL("libcuda.so")
result = libcuda.cuInit(0)
print(f"cuInit result: {result}")  # 0=success, 3=NOT_INITIALIZED
EOF

# 5. Check device file permissions
ls -la /dev/nvidia*

# 6. Full mount info
mount | grep -E "(nvidia|/dev)"
```

---

## Background: cuInit Error Codes

| Code | Name | Meaning |
|------|------|---------|
| 0 | CUDA_SUCCESS | Initialization succeeded |
| 1 | CUDA_ERROR_INVALID_VALUE | Invalid value passed |
| 2 | CUDA_ERROR_OUT_OF_MEMORY | Out of memory |
| 3 | CUDA_ERROR_NOT_INITIALIZED | Initialization failed |
| 100 | CUDA_ERROR_NO_DEVICE | No CUDA device found |
| 101 | CUDA_ERROR_INVALID_DEVICE | Invalid device ordinal |

Error 3 specifically means the driver loaded but couldn't initialize. Read-only device files are a known cause.

Sources:
- [CUDA Driver API Documentation](https://docs.nvidia.com/cuda/cuda-driver-api/group__CUDA__INITIALIZE.html)

---

## Known Similar Issues

### NVIDIA Container Toolkit - Containers Losing GPU Access
> "Under specific conditions, containers may be abruptly detached from the GPUs they were initially connected to. This situation occurs when systemd is used to manage the cgroups of the container."

**Fix (host-side):** Create /dev/char symlinks:
```bash
sudo nvidia-ctk system create-dev-char-symlinks --create-all
```

Source: [NVIDIA Container Toolkit Troubleshooting](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/troubleshooting.html)

### Multi-GPU Systems - Fabric Manager
For multi-GPU systems:
```bash
nvidia-smi -r
systemctl restart nvidia-fabricmanager
```

Source: [DigitalOcean GPU Troubleshooting](https://docs.digitalocean.com/support/how-do-i-fix-a-system-not-initialized-error-on-multi-gpu-droplets/)

---

## Recommended Next Steps

1. **Immediate**: Terminate current pod and redeploy (try different region if available)

2. **If issue persists**: File support ticket with:
   - Pod ID
   - Output of diagnostic commands above
   - Screenshot/text of `/proc/mounts | grep nvidia` showing `ro` flag

3. **Workaround**: Try H100 or RTX 4090 instead of A6000

4. **Long-term**: Use network volumes to avoid data loss when redeploying

---

## References

- [RunPod Documentation - Zero GPU Pods](https://docs.runpod.io/references/troubleshooting/zero-gpus)
- [RunPod Blog - Avoid Pod Errors](https://www.runpod.io/blog/avoid-pod-errors-runpod-resources)
- [NVIDIA Container Toolkit Troubleshooting](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/troubleshooting.html)
- [NVIDIA Container Toolkit - Device Permissions Issue #267](https://github.com/NVIDIA/nvidia-container-toolkit/issues/267)
- [RunPod Containers - CUDA Error Issue #67](https://github.com/runpod/containers/issues/67)
- [CUDA Driver API Documentation](https://docs.nvidia.com/cuda/cuda-driver-api/group__CUDA__INITIALIZE.html)
- [PyTorch CUDA Initialization Error](https://discuss.pytorch.org/t/failed-call-to-cuinit-cuda-error-not-initialized-initialization-error/167096)
- [RunPod PyTorch 2.4 Guide](https://www.runpod.io/articles/guides/pytorch-2-4-cuda-12-4)
