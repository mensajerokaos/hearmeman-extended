## Phase 1: Environment Preparation

### Steps
| Step | File:Line | Action | Parallel With |
|------|-----------|--------|---------------|
| 1 | docker/Dockerfile:1 | Backup current Dockerfile | - |
| 2 | N/A | Verify GPU availability and CUDA version | - |
| 3 | N/A | Check base image availability | - |
| 4 | N/A | Check disk space (> 20GB) | - |

### Detailed Implementation

**Step 1: Backup Current Dockerfile**
```bash
# Create backup with timestamp
cp docker/Dockerfile docker/Dockerfile.backup.$(date +%Y%m%d-%H%M%S)

# Verify backup exists
ls -la docker/Dockerfile.backup*
```

**Step 2: Verify GPU and CUDA**
```bash
# Check NVIDIA driver and CUDA version
nvidia-smi

# Expected output: CUDA Version: 12.1 or higher
# If lower, upgrade NVIDIA drivers or use different base image

# Check CUDA toolkit version
nvcc --version 2>/dev/null || echo "CUDA toolkit not installed (optional)"
```

**Step 3: Check Base Image**
```bash
# List available ComfyUI images
docker images | grep -i comfy

# Pull latest if needed
docker pull comfyui/comfyui:latest

# Verify tag
docker images | grep comfyui | awk '{print $2, $3}'
```

**Step 4: Check Disk Space**
```bash
# Check Docker disk usage
docker system df

# Check specific directory
df -h /var/lib/docker

# Expected: > 20GB free space
# If < 20GB:
#   docker system prune -af
#   docker volume prune -f
```

### Verification
```bash
# Run all checks
echo "=== Phase 1 Verification ==="
echo "Backup exists:"
ls -la docker/Dockerfile.backup* | wc -l
echo ""
echo "GPU and CUDA:"
nvidia-smi | grep "CUDA Version"
echo ""
echo "Base image:"
docker images | grep comfyui | head -1
echo ""
echo "Disk space:"
df -h /var/lib/docker | tail -1
echo ""
echo "=== Ready for Phase 2 ==="
```
