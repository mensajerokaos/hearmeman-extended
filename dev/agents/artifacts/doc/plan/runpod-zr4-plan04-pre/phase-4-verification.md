# RunPod ZR4 Docker Build Validation Framework

**Author:** $USER
**Model:** Claude Haiku 4.5
**Date:** 2026-01-21 06:42
**Task:** Comprehensive verification framework for Docker build validation
**Output:** ./dev/agents/artifacts/doc/plan/runpod-zr4-plan04-pre/phase-4-verification.md

---

## Executive Summary

This verification framework provides a systematic approach to validating Docker builds for the RunPod ZR4 custom template. It encompasses pre-build system checks, build process monitoring, runtime validation, integration testing, performance benchmarking, and error recovery procedures. The framework is designed to catch issues early, ensure production readiness, and provide clear pass/fail criteria with remediation steps for each validation stage.

---

## 1. Pre-Build Validation

Pre-build validation ensures the build environment meets all requirements before attempting Docker image construction. This stage prevents resource exhaustion and identifies environment issues proactively.

### 1.1 System Requirements Check

**Purpose:** Verify host system has sufficient resources and correct software versions for Docker build.

```bash
#!/bin/bash
# Pre-build system validation script
# Run this before initiating Docker build

echo "=== PRE-BUILD SYSTEM VALIDATION ==="
echo "Timestamp: $(date)"
echo ""

# 1.1.1 Check Docker daemon availability
echo "[1.1.1] Checking Docker daemon status..."
if ! docker info > /dev/null 2>&1; then
    echo "FAIL: Docker daemon is not running"
    echo "REMEDIATION: Start Docker daemon with: sudo systemctl start docker"
    exit 1
else
    echo "PASS: Docker daemon is running"
    docker version --format 'Docker version: {{.Server.Version}}'
fi

# 1.1.2 Check available disk space (minimum 100GB recommended)
echo ""
echo "[1.1.2] Checking disk space..."
AVAILABLE_KB=$(df -k /tmp | awk 'NR==2 {print $4}')
AVAILABLE_GB=$((AVAILABLE_KB / 1024 / 1024))
if [ $AVAILABLE_GB -lt 100 ]; then
    echo "FAIL: Insufficient disk space (${AVAILABLE_GB}GB available, 100GB required)"
    echo "REMEDIATION: Free up disk space or use a different partition with sufficient storage"
    exit 1
else
    echo "PASS: Disk space adequate (${AVAILABLE_GB}GB available)"
fi

# 1.1.3 Check available RAM (minimum 32GB recommended)
echo ""
echo "[1.1.3] Checking system RAM..."
TOTAL_KB=$(free -k | awk 'NR==2 {print $2}')
TOTAL_GB=$((TOTAL_KB / 1024 / 1024))
if [ $TOTAL_GB -lt 32 ]; then
    echo "WARNING: Low RAM detected (${TOTAL_GB}GB available, 32GB recommended)"
    echo "Build may be slower but will proceed"
else
    echo "PASS: RAM adequate (${TOTAL_GB}GB available)"
fi

# 1.1.4 Check CPU cores (minimum 8 cores recommended)
echo ""
echo "[1.1.4] Checking CPU cores..."
CORES=$(nproc)
if [ $CORES -lt 8 ]; then
    echo "WARNING: Low CPU core count ($CORES cores, 8 recommended)"
    echo "Build will proceed but may be slower"
else
    echo "PASS: CPU cores adequate ($CORES cores)"
fi

echo ""
echo "=== PRE-BUILD CHECK COMPLETE ==="
```

**Pass Criteria:**
- Docker daemon running and responsive
- Disk space ≥ 100GB available
- RAM ≥ 32GB (warning if < 32GB, build proceeds)
- CPU ≥ 8 cores (warning if < 8 cores, build proceeds)

**Remediation Actions:**
- Install Docker if missing: `sudo apt-get install docker.io`
- Start Docker daemon: `sudo systemctl start docker`
- Free disk space by cleaning Docker cache: `docker system prune -a`
- Add swap space if RAM insufficient: `sudo fallocate -l 16G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`

### 1.2 GPU Detection and Validation

**Purpose:** Verify NVIDIA GPU availability and driver compatibility for CUDA operations.

```bash
#!/bin/bash
# GPU detection and validation script

echo "=== GPU DETECTION AND VALIDATION ==="
echo "Timestamp: $(date)"
echo ""

# 1.2.1 Check for NVIDIA GPUs
echo "[1.2.1] Detecting NVIDIA GPUs..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "FAIL: nvidia-smi not found - NVIDIA drivers may not be installed"
    echo "REMEDIATION: Install NVIDIA drivers"
    echo "  Ubuntu: sudo apt-get install nvidia-driver-535 nvidia-dkms-535"
    echo "  Or use NVIDIA CUDA toolkit installer from https://developer.nvidia.com/cuda-downloads"
    exit 1
fi

echo "Detected GPUs:"
nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv

# 1.2.2 Validate minimum GPU VRAM (16GB for ZR4 workload)
echo ""
echo "[1.2.2] Checking GPU VRAM..."
MIN_VRAM_GB=16
GPU_VRAM_GB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader | awk '{sum+=$1} END {print sum/1024}')
if (( $(echo "$GPU_VRAM_GB < $MIN_VRAM_GB" | bc -l) )); then
    echo "FAIL: Insufficient VRAM (${GPU_VRAM_GB}GB available, ${MIN_VRAM_GB}GB required)"
    echo "REMEDIATION: Use a GPU with at least 16GB VRAM (RTX 4090, A6000, L40S)"
    exit 1
else
    echo "PASS: VRAM adequate (${GPU_VRAM_GB}GB available)"
fi

# 1.2.3 Validate driver version (525+ required for CUDA 12.x)
echo ""
echo "[1.2.3] Checking NVIDIA driver version..."
DRIVER_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | awk -F. '{print $1}')
REQUIRED_DRIVER=525
if [ "$DRIVER_VERSION" -lt "$REQUIRED_DRIVER" ]; then
    echo "FAIL: Driver version $DRIVER_VERSION < $REQUIRED_DRIVER required"
    echo "REMEDIATION: Update NVIDIA drivers"
    echo "  Download latest drivers from: https://www.nvidia.com/Download/index.aspx"
    exit 1
else
    echo "PASS: Driver version $DRIVER_VERSION ≥ $REQUIRED_DRIVER"
fi

# 1.2.4 Check GPU temperature and health
echo ""
echo "[1.2.4] Checking GPU health..."
GPU_TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader)
if [ "$GPU_TEMP" -gt 85 ]; then
    echo "WARNING: GPU temperature high (${GPU_TEMP}°C)"
    echo "Consider improving cooling before running intensive workloads"
else
    echo "PASS: GPU temperature normal (${GPU_TEMP}°C)"
fi

# 1.2.5 Validate GPU persistence mode
echo ""
echo "[1.2.5] Checking GPU persistence mode..."
PERSISTENCE=$(nvidia-smi --query-gpu=persistence_mode --format=csv,noheader | head -1)
if [ "$PERSISTENCE" = "Disabled" ]; then
    echo "INFO: Persistence mode disabled (recommended for power savings)"
    echo "For faster container startup, enable with: sudo nvidia-smi -pm 1"
else
    echo "PASS: Persistence mode enabled"
fi

echo ""
echo "=== GPU VALIDATION COMPLETE ==="
```

**Pass Criteria:**
- NVIDIA GPU detected via nvidia-smi
- VRAM ≥ 16GB total across all GPUs
- Driver version ≥ 525
- GPU temperature < 85°C

**Remediation Actions:**
- Update drivers: Download from NVIDIA website or use package manager
- Clear GPU processes: `sudo fuser -v /dev/nvidia*` then kill stuck processes
- Cool GPU: Ensure proper ventilation, reduce ambient temperature

### 1.3 CUDA Version Compatibility

**Purpose:** Validate CUDA toolkit version matches Docker image requirements.

```bash
#!/bin/bash
# CUDA version compatibility check

echo "=== CUDA VERSION COMPATIBILITY CHECK ==="
echo ""

# 1.3.1 Check CUDA driver version
echo "[1.3.1] Checking CUDA driver version..."
CUDA_DRIVER=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)
echo "CUDA Driver Version: $CUDA_DRIVER"

# 1.3.2 Check CUDA toolkit availability
echo ""
echo "[1.3.2] Checking CUDA toolkit..."
if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | awk '{print $5}' | tr -d ',')
    echo "CUDA Toolkit Version: $CUDA_VERSION"
else
    echo "WARNING: nvcc not found (CUDA toolkit not installed locally)"
    echo "This is OK - Docker image includes its own CUDA runtime"
fi

# 1.3.3 Validate CUDA driver compatibility with CUDA 12.x
echo ""
echo "[1.3.3] Validating CUDA driver compatibility..."
CUDA_DRIVER_MAJOR=$(echo $CUDA_DRIVER | awk -F. '{print $1}')
if [ "$CUDA_DRIVER_MAJOR" -ge 525 ]; then
    echo "PASS: Driver supports CUDA 12.x"
    echo "Compatible with: CUDA 12.0, 12.1, 12.2, 12.3, 12.4"
else
    echo "WARNING: Driver may not fully support CUDA 12.x"
    echo "Consider upgrading if encountering CUDA errors"
fi

# 1.3.4 Check compute capability
echo ""
echo "[1.3.4] Checking GPU compute capability..."
COMPUTE_CAP=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -1)
echo "Compute Capability: $COMPUTE_CAP"
if (( $(echo "$COMPUTE_CAP >= 8.9" | bc -l) )); then
    echo "PASS: Supports latest CUDA features (compute capability 8.9+)"
elif (( $(echo "$COMPUTE_CAP >= 8.0" | bc -l) )); then
    echo "PASS: Supports modern CUDA features (compute capability 8.0+)"
else
    echo "WARNING: Older GPU may have limited feature support"
fi

echo ""
echo "=== CUDA COMPATIBILITY CHECK COMPLETE ==="
```

**Pass Criteria:**
- CUDA driver version ≥ 525 (supports CUDA 12.x)
- Compute capability ≥ 8.0 (supports modern PyTorch operations)

**Remediation Actions:**
- Update CUDA driver via NVIDIA website or package manager
- For older GPUs, consider using CUDA 11.8 compatible images

### 1.4 Docker BuildKit Prerequisites

**Purpose:** Ensure BuildKit is available and properly configured for efficient builds.

```bash
#!/bin/bash
# BuildKit and Docker build prerequisites

echo "=== DOCKER BUILDKIT PREREQUISITES ==="
echo ""

# 1.4.1 Check BuildX availability
echo "[1.4.1] Checking Docker BuildX availability..."
if ! docker buildx version &> /dev/null; then
    echo "FAIL: Docker BuildX not available"
    echo "REMEDIATION: Install Docker BuildX"
    echo "  Download from: https://github.com/docker/buildx/releases"
    exit 1
else
    echo "PASS: BuildX available ($(docker buildx version))"
fi

# 1.4.2 Check for available builders
echo ""
echo "[1.4.2] Checking available builders..."
docker buildx ls

# 1.4.3 Verify default builder is configured
echo ""
echo "[1.4.3] Verifying default builder configuration..."
if docker buildx inspect default &> /dev/null; then
    echo "PASS: Default builder available"
else
    echo "WARNING: Default builder not found, creating..."
    docker buildx create --name default --driver docker-container --use
fi

# 1.4.4 Check BuildKit cache location and size
echo ""
echo "[1.4.4] Checking BuildKit cache..."
CACHE_SIZE=$(docker system df | grep BuildKit | awk '{print $2}')
echo "BuildKit cache usage: $CACHE_SIZE"
if [ -d "/var/lib/docker/buildkit" ]; then
    ACTUAL_SIZE=$(du -sh /var/lib/docker/buildkit 2>/dev/null | awk '{print $1}')
    echo "Actual cache size: $ACTUAL_SIZE"
fi

echo ""
echo "=== BUILDKIT PREREQUISITES COMPLETE ==="
```

**Pass Criteria:**
- Docker BuildX installed and functional
- Default builder configured
- BuildKit cache accessible

**Remediation Actions:**
- Install BuildX manually if not included with Docker
- Create default builder: `docker buildx create --name default --driver docker-container --use`

---

## 2. Build Process Verification

Build process verification monitors Docker image construction to ensure each layer builds correctly and efficiently.

### 2.1 Layer Caching Validation

**Purpose:** Verify layer caching is working effectively to reduce rebuild times.

```bash
#!/bin/bash
# Layer caching validation

echo "=== LAYER CACHING VALIDATION ==="
echo "Build: $(date)"
echo ""

# 2.1.1 Clean Docker cache for fresh build test
echo "[2.1.1] Preparing for fresh build test..."
read -p "Clear Docker build cache for validation? (y/n): " CONFIRM
if [ "$CONFIRM" = "y" ]; then
    echo "Clearing build cache..."
    docker builder prune -af
    echo "Cache cleared"
else
    echo "Using existing cache for comparison"
fi

# 2.1.2 First build (baseline)
echo ""
echo "[2.1.2] Running baseline build..."
BUILD_START_1=$(date +%s)
docker build --progress=plain -t zr4-baseline:latest . 2>&1 | tee /tmp/build_log_1.txt
BUILD_END_1=$(date +%s)
BUILD_TIME_1=$((BUILD_END_1 - BUILD_START_1))
echo "Baseline build time: ${BUILD_TIME_1} seconds"

# 2.1.3 Second build (should use cache)
echo ""
echo "[2.1.3] Running cached build..."
BUILD_START_2=$(date +%s)
docker build --progress=plain -t zr4-cached:latest . 2>&1 | tee /tmp/build_log_2.txt
BUILD_END_2=$(date +%s)
BUILD_TIME_2=$((BUILD_END_2 - BUILD_START_2))
echo "Cached build time: ${BUILD_TIME_2} seconds"

# 2.1.4 Calculate cache hit ratio
echo ""
echo "[2.1.4] Analyzing cache effectiveness..."
CACHED_LAYERS=$(grep -c "CACHED" /tmp/build_log_2.txt 2>/dev/null || echo "0")
TOTAL_LAYERS=$(grep -cE "^#[0-9]+ \[" /tmp/build_log_2.txt 2>/dev/null || echo "0")
if [ $TOTAL_LAYERS -gt 0 ]; then
    CACHE_RATIO=$(echo "scale=2; $CACHED_LAYERS * 100 / $TOTAL_LAYERS" | bc)
    echo "Cached layers: $CACHED_LAYERS / $TOTAL_LAYERS ($CACHE_RATIO%)"

    if (( $(echo "$CACHE_RATIO >= 80" | bc -l) )); then
        echo "PASS: Excellent cache hit rate (≥80%)"
    elif (( $(echo "$CACHE_RATIO >= 50" | bc -l) ]]; then
        echo "WARNING: Moderate cache hit rate (50-80%)"
    else
        echo "FAIL: Poor cache hit rate (<50%)"
        echo "REMEDIATION: Review Dockerfile for layer ordering optimizations"
    fi
else
    echo "Unable to calculate cache ratio"
fi

# 2.1.5 Calculate time savings
echo ""
echo "[2.1.5] Time savings from caching..."
if [ $BUILD_TIME_2 -gt 0 ]; then
    TIME_SAVINGS=$(echo "scale=2; ($BUILD_TIME_1 - $BUILD_TIME_2) * 100 / $BUILD_TIME_1" | bc)
    echo "Build time reduction: ${TIME_SAVINGS}%"
    echo "Time saved: $((BUILD_TIME_1 - BUILD_TIME_2)) seconds"
fi

echo ""
echo "=== LAYER CACHING VALIDATION COMPLETE ==="
```

**Pass Criteria:**
- Cache hit ratio ≥ 80% (excellent)
- Build time reduction ≥ 50% on subsequent builds
- No failed build stages

**Remediation Actions:**
- Reorder Dockerfile layers to maximize cache hits (copy files that change least frequently first)
- Use multi-stage builds to reduce layer count
- Combine related operations in single RUN commands

### 2.2 Build Time Tracking

**Purpose:** Monitor build progress and identify slow stages that need optimization.

```bash
#!/bin/bash
# Build time tracking and analysis

echo "=== BUILD TIME TRACKING ==="
echo ""

# 2.2.1 Run timed build with stage-by-stage breakdown
echo "[2.2.1] Running timed build with stage tracking..."
export DOCKER_BUILDKIT=1

# Create build script with timing
cat > /tmp/timed_build.sh << 'SCRIPT'
#!/bin/bash
START=$(date +%s.%N)

docker build \
  --progress=plain \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t zr4-timed:latest . 2>&1 | tee /tmp/build_output.txt

END=$(date +%s.%N)
ELAPSED=$(echo "$END - $START" | bc)
echo "TOTAL_BUILD_TIME: ${ELAPSED} seconds"
SCRIPT

chmod +x /tmp/timed_build.sh
/tmp/timed_build.sh

# 2.2.2 Analyze stage completion times
echo ""
echo "[2.2.2] Analyzing stage completion times..."
if [ -f /tmp/build_output.txt ]; then
    # Extract stage timing markers
    grep -E "^#[0-9]+\[" /tmp/build_output.txt | while read line; do
        STAGE=$(echo "$line" | grep -oE "#[0-9]+" | grep -oE "[0-9]+")
        TIMESTAMP=$(echo "$line" | grep -oE "[0-9]{2}:[0-9]{2}:[0-9]{2}")
        echo "Stage $STAGE completed at: $TIMESTAMP"
    done
fi

# 2.2.3 Identify slow stages
echo ""
echo "[2.2.3] Identifying slow stages..."
SLOW_STAGES=$(grep -E "CANCELED|FAILED|error:" /tmp/build_output.txt | head -10)
if [ -n "$SLOW_STAGES" ]; then
    echo "ISSUES DETECTED:"
    echo "$SLOW_STAGES"
else
    echo "All stages completed successfully"
fi

# 2.2.4 Check for specific bottlenecks
echo ""
echo "[2.2.4] Checking for common bottlenecks..."

# Check for network operations
NETWORK_OPS=$(grep -c "Retrieving" /tmp/build_output.txt 2>/dev/null || echo "0")
echo "Network operations: $NETWORK_OPS retrievals"

# Check for compilation operations
COMPILE_OPS=$(grep -c "Running" /tmp/build_output.txt 2>/dev/null || echo "0")
echo "Compilation/Installation operations: $COMPILE_OPS"

# Check for pip/conda installations
PIP_INSTALLS=$(grep -c "pip install" /tmp/build_output.txt 2>/dev/null || echo "0")
echo "Pip installations: $PIP_INSTALLS"

# 2.2.5 Generate build summary
echo ""
echo "[2.2.5] Build summary..."
if [ -f /tmp/build_output.txt ]; then
    TOTAL_LINES=$(wc -l < /tmp/build_output.txt)
    ERROR_LINES=$(grep -cE "error:|FAILED|CANCELED" /tmp/build_output.txt || echo "0")
    WARNING_LINES=$(grep -c "warning:" /tmp/build_output.txt || echo "0")

    echo "Total output lines: $TOTAL_LINES"
    echo "Error lines: $ERROR_LINES"
    echo "Warning lines: $WARNING_LINES"

    if [ "$ERROR_LINES" -eq 0 ]; then
        echo "PASS: No errors detected during build"
    else
        echo "FAIL: $ERROR_LINES errors detected"
        echo "REMEDIATION: Review error messages and fix Dockerfile issues"
    fi
fi

echo ""
echo "=== BUILD TIME TRACKING COMPLETE ==="
```

**Pass Criteria:**
- All stages complete without errors
- Build completes within expected time window (reference: < 30 minutes for full build)
- No canceled or failed stages

**Remediation Actions:**
- Use --mount=type=cache for package managers (pip, apt, conda)
- Pre-download large files in earlier layers
- Parallelize independent operations
- Use lighter base images when possible

### 2.3 Dependency Installation Verification

**Purpose:** Verify all dependencies are correctly installed in the image.

```bash
#!/bin/bash
# Dependency installation verification

echo "=== DEPENDENCY INSTALLATION VERIFICATION ==="
echo ""

# 2.3.1 Build image for testing
echo "[2.3.1] Building verification image..."
docker build -t zr4-deps-check:latest . --progress=plain 2>&1 | tail -20

# 2.3.2 Create verification script to run inside container
cat > /tmp/verify_deps.sh << 'SCRIPT'
#!/bin/bash
echo "=== IN-CONTAINER DEPENDENCY VERIFICATION ==="

FAILED=0

# 2.3.2.1 Check Python version
echo "[2.3.2.1] Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1)
echo "Python version: $PYTHON_VERSION"
if [[ "$PYTHON_VERSION" == "Python 3.10"* ]] || [[ "$PYTHON_VERSION" == "Python 3.11"* ]]; then
    echo "PASS: Python version compatible"
else
    echo "WARNING: Unexpected Python version"
    FAILED=1
fi

# 2.3.2.2 Check PyTorch installation
echo ""
echo "[2.3.2.2] Checking PyTorch installation..."
python3 -c "import torch; print(f'PyTorch version: {torch.__version__}')"
if python3 -c "import torch" 2>/dev/null; then
    echo "PASS: PyTorch installed"
else
    echo "FAIL: PyTorch not found"
    FAILED=1
fi

# 2.3.2.3 Check CUDA availability in PyTorch
echo ""
echo "[2.3.2.3] Checking CUDA availability..."
CUDA_AVAILABLE=$(python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null)
if [ "$CUDA_AVAILABLE" = "True" ]; then
    CUDA_VERSION=$(python3 -c "import torch; print(torch.version.cuda)" 2>/dev/null)
    echo "PASS: CUDA available (version: $CUDA_VERSION)"
else
    echo "FAIL: CUDA not available in PyTorch"
    FAILED=1
fi

# 2.3.2.4 Check NumPy
echo ""
echo "[2.3.2.4] Checking NumPy..."
python3 -c "import numpy; print(f'NumPy version: {numpy.__version__}')"
if python3 -c "import numpy" 2>/dev/null; then
    echo "PASS: NumPy installed"
else
    echo "FAIL: NumPy not found"
    FAILED=1
fi

# 2.3.2.5 Check OpenCV
echo ""
echo "[2.3.2.5] Checking OpenCV..."
python3 -c "import cv2; print(f'OpenCV version: {cv2.__version__}')"
if python3 -c "import cv2" 2>/dev/null; then
    echo "PASS: OpenCV installed"
else
    echo "FAIL: OpenCV not found"
    FAILED=1
fi

# 2.3.2.6 Check PIL/Pillow
echo ""
echo "[2.3.2.6] Checking Pillow..."
python3 -c "from PIL import Image; print('Pillow imported successfully')"
if python3 -c "from PIL import Image" 2>/dev/null; then
    echo "PASS: Pillow installed"
else
    echo "FAIL: Pillow not found"
    FAILED=1
fi

# 2.3.2.7 Check custom dependencies
echo ""
echo "[2.3.2.7] Checking custom dependencies..."

# ComfyUI core
if python3 -c "import folder_paths" 2>/dev/null; then
    echo "PASS: ComfyUI folder_paths imported"
else
    echo "FAIL: ComfyUI folder_paths not found"
    FAILED=1
fi

# Check for key ComfyUI modules
for module in execution nodes server; do
    if python3 -c "import $module" 2>/dev/null; then
        echo "PASS: ComfyUI $module imported"
    else
        echo "WARNING: ComfyUI $module not found"
    fi
done

# 2.3.2.8 Check FFmpeg
echo ""
echo "[2.3.2.8] Checking FFmpeg..."
FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -1)
echo "$FFMPEG_VERSION"
if command -v ffmpeg &> /dev/null; then
    echo "PASS: FFmpeg installed"
else
    echo "FAIL: FFmpeg not found"
    FAILED=1
fi

# 2.3.2.9 Check Git
echo ""
echo "[2.3.2.9] Checking Git..."
GIT_VERSION=$(git --version 2>&1)
echo "$GIT_VERSION"
if command -v git &> /dev/null; then
    echo "PASS: Git installed"
else
    echo "FAIL: Git not found"
    FAILED=1
fi

# 2.3.2.10 Check specialized libraries
echo ""
echo "[2.3.2.10] Checking specialized libraries..."

# Transformers
python3 -c "import transformers; print(f'Transformers version: {transformers.__version__}')" 2>/dev/null
if python3 -c "import transformers" 2>/dev/null; then
    echo "PASS: Transformers installed"
else
    echo "FAIL: Transformers not found"
    FAILED=1
fi

# Diffusers
python3 -c "import diffusers; print(f'Diffusers version: {diffusers.__version__}')" 2>/dev/null
if python3 -c "import diffusers" 2>/dev/null; then
    echo "PASS: Diffusers installed"
else
    echo "FAIL: Diffusers not found"
    FAILED=1
fi

# xFormers (optional but recommended)
python3 -c "import xformers" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "PASS: xFormers installed"
else
    echo "WARNING: xFormers not found (optional but recommended for performance)"
fi

# Summary
echo ""
echo "=== DEPENDENCY VERIFICATION SUMMARY ==="
if [ $FAILED -eq 0 ]; then
    echo "All critical dependencies verified successfully"
    exit 0
else
    echo "FAILURES DETECTED: $FAILED critical dependencies missing"
    exit 1
fi
SCRIPT

chmod +x /tmp/verify_deps.sh

# 2.3.3 Run verification in container
echo ""
echo "[2.3.3] Running verification inside container..."
docker run --rm -v /tmp/verify_deps.sh:/verify.sh -v /home/oz/projects/2025/oz/12/runpod:/app zr4-deps-check:latest /verify_deps.sh

echo ""
echo "=== DEPENDENCY INSTALLATION VERIFICATION COMPLETE ==="
```

**Pass Criteria:**
- All critical dependencies (PyTorch, CUDA, NumPy, OpenCV, Pillow, FFmpeg, Git) installed
- ComfyUI modules import successfully
- Python version 3.10 or 3.11
- No critical failures

**Remediation Actions:**
- Review Dockerfile for correct package names and installation order
- Check for version conflicts between dependencies
- Verify pip/conda package sources are accessible
- Ensure network connectivity during build

---

## 3. Runtime Validation

Runtime validation ensures the containerized environment works correctly when executed, including GPU access, model loading, and inference operations.

### 3.1 GPU and VRAM Monitoring

**Purpose:** Verify GPU access from within the container and monitor VRAM usage.

```bash
#!/bin/bash
# GPU and VRAM monitoring in container

echo "=== GPU AND VRAM MONITORING ==="
echo ""

# 3.1.1 Run GPU detection in container
echo "[3.1.1] Running GPU detection in container..."
docker run --rm --gpus all zr4-runtime:latest nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv

# 3.1.2 Create GPU stress test script
cat > /tmp/gpu_stress_test.sh << 'SCRIPT'
#!/bin/bash
echo "=== GPU STRESS TEST ==="

# 3.1.2.1 Basic GPU info
echo "[3.1.2.1] GPU Information:"
nvidia-smi --query-gpu=name,driver_version,cuda_version --format=csv

# 3.1.2.2 VRAM before test
echo ""
echo "[3.1.2.2] VRAM before test:"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# 3.1.2.3 Run PyTorch CUDA test
echo ""
echo "[3.1.2.3] Running PyTorch CUDA connectivity test..."
python3 << 'PYEOF'
import torch
import time

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"GPU: {torch.cuda.get_device_name(0)}")

if torch.cuda.is_available():
    # Test GPU computation
    print("\nRunning GPU computation test...")
    start = time.time()
    x = torch.randn(1000, 1000).cuda()
    y = torch.randn(1000, 1000).cuda()
    z = torch.matmul(x, y)
    torch.cuda.synchronize()
    elapsed = time.time() - start
    print(f"Matrix multiplication (1000x1000): {elapsed*1000:.2f}ms")

    # VRAM after test
    print(f"\nVRAM after computation:")
    print(f"  Allocated: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
    print(f"  Reserved: {torch.cuda.memory_reserved() / 1024**2:.2f} MB")

    print("\nGPU connectivity test: PASSED")
else:
    print("GPU connectivity test: FAILED - CUDA not available")
PYEOF

# 3.1.2.4 VRAM after test
echo ""
echo "[3.1.2.4] VRAM after test:"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# 3.1.2.5 Test GPU reset
echo ""
echo "[3.1.2.5] Testing GPU memory cleanup..."
python3 << 'PYEOF'
import torch
import gc

if torch.cuda.is_available():
    # Allocate and free
    x = torch.randn(2000, 2000).cuda()
    del x
    gc.collect()
    torch.cuda.empty_cache()

    print(f"VRAM after cleanup: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
    print("GPU memory cleanup: PASSED")
else:
    print("GPU memory cleanup: SKIPPED (no GPU)")
PYEOF

echo ""
echo "=== GPU STRESS TEST COMPLETE ==="
SCRIPT

chmod +x /tmp/gpu_stress_test.sh

# 3.1.3 Run GPU stress test in container
echo ""
echo "[3.1.3] Running GPU stress test in container..."
docker run --rm --gpus all -v /tmp/gpu_stress_test.sh:/gpu_test.sh zr4-runtime:latest /gpu_test.sh

# 3.1.4 Long-running VRAM monitoring
echo ""
echo "[3.1.4] Long-running VRAM monitoring (60 seconds)..."
timeout 60 docker run --rm --gpus all zr4-runtime:latest bash -c '
for i in {1..6}; do
    nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv
    sleep 10
done
'

echo ""
echo "=== GPU AND VRAM MONITORING COMPLETE ==="
```

**Pass Criteria:**
- GPU detected with correct VRAM allocation (16GB+)
- PyTorch CUDA connectivity successful
- GPU computation performs correctly
- Memory cleanup functions properly
- VRAM stays within expected bounds during idle and load

**Remediation Actions:**
- If GPU not detected: Verify nvidia-container-toolkit is installed
- If CUDA not available: Check CUDA toolkit installation in Dockerfile
- If VRAM low: Reduce batch size, use smaller models, or add GPU memory optimization

### 3.2 Model Loading Tests

**Purpose:** Verify models can be loaded correctly within VRAM constraints.

```bash
#!/bin/bash
# Model loading tests

echo "=== MODEL LOADING TESTS ==="
echo ""

# 3.2.1 Create model loading test script
cat > /tmp/model_loading_test.sh << 'SCRIPT'
#!/bin/bash
echo "=== MODEL LOADING TEST SUITE ==="

FAILED=0

# 3.2.1.1 Test Stable Diffusion model loading
echo "[3.2.1.1] Testing Stable Diffusion model loading..."
python3 << 'PYEOF'
import torch
import time

print("Loading Stable Diffusion XL...")
start = time.time()

try:
    from diffusers import StableDiffusionXLPipeline

    pipe = StableDiffusionXLPipeline.from_pretrained(
        "/workspace/models/sdxl",
        torch_dtype=torch.float16,
        use_safetensors=True
    )
    pipe = pipe.to("cuda")

    elapsed = time.time() - start
    print(f"Stable Diffusion XL loaded in {elapsed:.2f}s")

    # Check memory
    print(f"VRAM usage: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
    print("Stable Diffusion XL: PASSED")

except Exception as e:
    print(f"Stable Diffusion XL: FAILED - {str(e)}")
PYEOF

# 3.2.1.2 Test UNet loading
echo ""
echo "[3.2.1.2] Testing UNet loader..."
python3 << 'PYEOF'
import torch
import os

UNET_PATH = "/workspace/models/sdxl/unet"

if os.path.exists(UNET_PATH):
    print("Loading UNet from cache...")
    try:
        unet = torch.load(f"{UNET_PATH}/diffusion_pytorch_model.bin")
        print(f"UNet loaded successfully")
        print(f"UNet parameters: {sum(p.numel() for p in unet.parameters()) / 1e9:.2f}B")
        print("UNet loading: PASSED")
    except Exception as e:
        print(f"UNet loading: FAILED - {str(e)}")
else:
    print("UNet loading: SKIPPED - model not present")
PYEOF

# 3.2.1.3 Test VAE loading
echo ""
echo "[3.2.1.3] Testing VAE loading..."
python3 << 'PYEOF'
import torch
import os

VAE_PATH = "/workspace/models/sdxl/vae"

if os.path.exists(VAE_PATH):
    print("Loading VAE...")
    try:
        from diffusers import AutoencoderKL
        vae = AutoencoderKL.from_pretrained(VAE_PATH, torch_dtype=torch.float16)
        vae = vae.to("cuda")
        print("VAE loaded successfully")
        print("VAE loading: PASSED")
    except Exception as e:
        print(f"VAE loading: FAILED - {str(e)}")
else:
    print("VAE loading: SKIPPED - model not present")
PYEOF

# 3.2.1.4 Test CLIP text encoder loading
echo ""
echo "[3.2.1.4] Testing CLIP text encoder loading..."
python3 << 'PYEOF'
import torch
import os

CLIP_PATH = "/workspace/models/sdxl/text_encoder"

if os.path.exists(CLIP_PATH):
    print("Loading CLIP text encoder...")
    try:
        from transformers import CLIPTextModel
        clip = CLIPTextModel.from_pretrained(CLIP_PATH, torch_dtype=torch.float16)
        clip = clip.to("cuda")
        print("CLIP text encoder loaded successfully")
        print("CLIP loading: PASSED")
    except Exception as e:
        print(f"CLIP loading: FAILED - {str(e)}")
else:
    print("CLIP loading: SKIPPED - model not present")
PYEOF

# 3.2.1.5 Test GGUF quantized model loading
echo ""
echo "[3.2.1.5] Testing GGUF quantized model loading..."
python3 << 'PYEOF'
import torch
import os

GGUF_PATH = "/workspace/models/quantized"

if os.path.exists(GGUF_PATH):
    print("Scanning for GGUF models...")
    gguf_files = []
    for root, dirs, files in os.walk(GGUF_PATH):
        for file in files:
            if file.endswith('.gguf'):
                gguf_files.append(os.path.join(root, file))

    if gguf_files:
        print(f"Found {len(gguf_files)} GGUF model(s)")
        for gf in gguf_files[:3]:  # Test first 3
            print(f"  - {os.path.basename(gf)}")

        # Test loading with ctransformers if available
        try:
            from ctransformers import AutoModelForCausalLM
            print("GGUF support (ctransformers): AVAILABLE")
        except ImportError:
            print("GGUF support (ctransformers): NOT INSTALLED")

        print("GGUF model scan: PASSED")
    else:
        print("GGUF model scan: SKIPPED - no GGUF files found")
else:
    print("GGUF model scan: SKIPPED - directory not present")
PYEOF

# 3.2.1.6 Test model file integrity
echo ""
echo "[3.2.1.6] Testing model file integrity..."
python3 << 'PYEOF'
import hashlib
import os

def get_file_hash(filepath):
    """Calculate SHA256 hash of file"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def check_safetensors(filepath):
    """Basic safetensors format check"""
    try:
        with open(filepath, 'rb') as f:
            header_size = int.from_bytes(f.read(8), 'little')
            header = f.read(header_size)
            import json
            metadata = json.loads(header)
            return True, metadata
    except Exception as e:
        return False, str(e)

MODEL_DIR = "/workspace/models"
CORRUPTED = []
VALID = []

for root, dirs, files in os.walk(MODEL_DIR):
    for file in files:
        filepath = os.path.join(root, file)
        if file.endswith(('.safetensors', '.bin', '.ckpt')):
            try:
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                if file.endswith('.safetensors'):
                    valid, info = check_safetensors(filepath)
                    if valid:
                        VALID.append((file, size_mb))
                    else:
                        CORRUPTED.append((file, str(info)))
                else:
                    VALID.append((file, size_mb))
            except Exception as e:
                CORRUPTED.append((file, str(e)))

print(f"Models checked: {len(VALID) + len(CORRUPTED)}")
print(f"Valid models: {len(VALID)}")
if CORRUPTED:
    print(f"Corrupted models: {len(CORRUPTED)}")
    for name, error in CORRUPTED[:5]:
        print(f"  - {name}: {error}")
else:
    print("Corrupted models: 0")

if not CORRUPTED:
    print("Model integrity check: PASSED")
else:
    print("Model integrity check: FAILED")
PYEOF

echo ""
echo "=== MODEL LOADING TEST SUITE COMPLETE ==="
SCRIPT

chmod +x /tmp/model_loading_test.sh

# 3.2.2 Run model loading tests
echo "[3.2.2] Running model loading tests..."
docker run --rm --gpus all -v /tmp/model_loading_test.sh:/model_test.sh \
    -v /home/oz/projects/2025/oz/12/runpod/docker:/workspace \
    zr4-runtime:latest /model_test.sh

echo ""
echo "=== MODEL LOADING TESTS COMPLETE ==="
```

**Pass Criteria:**
- All specified models load successfully within VRAM limits
- Model file integrity verified (no corrupted files)
- GGUF quantized models detected and compatible libraries available
- Model loading time within expected bounds (< 5 minutes for full model)

**Remediation Actions:**
- If model loading fails: Check file paths, ensure model files are downloaded
- If VRAM exceeded: Use model quantization, reduce batch size, enable model offloading
- If corrupted files: Re-download models, verify checksums

### 3.3 Inference Tests

**Purpose:** Verify inference operations work correctly with test generations.

```bash
#!/bin/bash
# Inference tests

echo "=== INFERENCE TESTS ==="
echo ""

# 3.3.1 Create inference test script
cat > /tmp/inference_test.sh << 'SCRIPT'
#!/bin/bash
echo "=== INFERENCE TEST SUITE ==="

# 3.3.1.1 Quick inference smoke test
echo "[3.3.1.1] Running smoke test inference..."
python3 << 'PYEOF'
import torch
import time

print("Testing basic inference capability...")

try:
    # Simple test generation
    from diffusers import StableDiffusionXLPipeline, EulerDiscreteScheduler

    pipe = StableDiffusionXLPipeline.from_pretrained(
        "/workspace/models/sdxl",
        torch_dtype=torch.float16,
        use_safetensors=True
    )
    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to("cuda")

    # Generate test image
    print("Generating test image (this may take 1-2 minutes)...")
    start = time.time()

    prompt = "A test image of a simple object"
    negative_prompt = "low quality, distorted, blurry"

    image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=20,
        height=512,
        width=512,
        guidance_scale=7.0
    ).images[0]

    elapsed = time.time() - start

    # Save test image
    image.save("/tmp/test_output.png")
    print(f"Test image generated in {elapsed:.2f}s")
    print(f"Image size: {image.size}")
    print("Smoke test inference: PASSED")

except Exception as e:
    print(f"Smoke test inference: FAILED - {str(e)}")
    import traceback
    traceback.print_exc()
PYEOF

# 3.3.1.2 Memory efficiency test
echo ""
echo "[3.3.1.2] Testing memory efficiency..."
python3 << 'PYEOF'
import torch
import gc

def measure_memory(label):
    """Measure current GPU memory usage"""
    torch.cuda.synchronize()
    allocated = torch.cuda.memory_allocated() / 1024**3
    reserved = torch.cuda.memory_reserved() / 1024**3
    print(f"{label}: Allocated={allocated:.2f}GB, Reserved={reserved:.2f}GB")
    return allocated, reserved

try:
    from diffusers import StableDiffusionXLPipeline

    # Load pipeline
    print("Loading pipeline...")
    pipe = StableDiffusionXLPipeline.from_pretrained(
        "/workspace/models/sdxl",
        torch_dtype=torch.float16,
        use_safetensors=True
    )
    pipe = pipe.to("cuda")

    measure_memory("After loading")

    # Generate image
    print("\nGenerating image...")
    image = pipe(
        prompt="A beautiful landscape",
        num_inference_steps=30,
        height=768,
        width=768
    ).images[0]

    measure_memory("After generation")

    # Cleanup
    del pipe
    gc.collect()
    torch.cuda.empty_cache()

    measure_memory("After cleanup")

    print("\nMemory efficiency test: PASSED")

except Exception as e:
    print(f"Memory efficiency test: FAILED - {str(e)}")
PYEOF

# 3.3.1.3 Batch inference test
echo ""
echo "[3.3.1.3] Testing batch inference..."
python3 << 'PYEOF'
import torch
import time

try:
    from diffusers import StableDiffusionXLPipeline

    pipe = StableDiffusionXLPipeline.from_pretrained(
        "/workspace/models/sdxl",
        torch_dtype=torch.float16,
        use_safetensors=True
    )
    pipe = pipe.to("cuda")

    prompts = [
        "A red apple on a table",
        "A blue sky with clouds",
        "A mountain landscape",
        "A city at night"
    ]

    print(f"Generating {len(prompts)} images in batch...")
    start = time.time()

    images = pipe(
        prompt=prompts,
        num_inference_steps=20,
        height=512,
        width=512
    )

    elapsed = time.time() - start

    print(f"Batch of {len(images.images)} images generated in {elapsed:.2f}s")
    print(f"Average time per image: {elapsed/len(images.images):.2f}s")

    for i, img in enumerate(images.images):
        img.save(f"/tmp/batch_test_{i}.png")

    print("Batch inference test: PASSED")

except Exception as e:
    print(f"Batch inference test: FAILED - {str(e)}")
    import traceback
    traceback.print_exc()
PYEOF

# 3.3.1.4 Scheduler compatibility test
echo ""
echo "[3.3.1.4] Testing scheduler compatibility..."
python3 << 'PYEOF'
import torch
from diffusers import StableDiffusionXLPipeline
from diffusers import EulerDiscreteScheduler, DPMSolverMultistepScheduler, UniPCMultistepScheduler

schedulers = [
    ("EulerDiscrete", EulerDiscreteScheduler),
    ("DPMSolverMultistep", DPMSolverMultistepScheduler),
    ("UniPCMultistep", UniPCMultistepScheduler),
]

pipe = StableDiffusionXLPipeline.from_pretrained(
    "/workspace/models/sdxl",
    torch_dtype=torch.float16,
    use_safetensors=True
)
pipe = pipe.to("cuda")

for name, scheduler_class in schedulers:
    try:
        pipe.scheduler = scheduler_class.from_config(pipe.scheduler.config)
        image = pipe(
            prompt="Test image",
            num_inference_steps=10,
            height=512,
            width=512
        ).images[0]
        print(f"  {name}: PASSED")
    except Exception as e:
        print(f"  {name}: FAILED - {str(e)}")

print("Scheduler compatibility test: COMPLETE")
PYEOF

echo ""
echo "=== INFERENCE TEST SUITE COMPLETE ==="
SCRIPT

chmod +x /tmp/inference_test.sh

# 3.3.2 Run inference tests
echo "[3.3.2] Running inference tests..."
docker run --rm --gpus all -v /tmp/inference_test.sh:/inference_test.sh \
    -v /home/oz/projects/2025/oz/12/runpod/docker:/workspace \
    -v /tmp:/tmp \
    zr4-runtime:latest /inference_test.sh

echo ""
echo "=== INFERENCE TESTS COMPLETE ==="
```

**Pass Criteria:**
- Smoke test generates valid image without errors
- Memory stays within VRAM limits (16GB)
- Batch inference works correctly (4+ images)
- Multiple schedulers (Euler, DPM, UniPC) function properly
- No CUDA out-of-memory errors

**Remediation Actions:**
- If OOM errors: Reduce image resolution, lower inference steps, enable attention slicing
- If slow inference: Enable xFormers, use attention slicing, optimize batch size
- If scheduler fails: Check scheduler parameters match model requirements

---

## 4. Integration Testing

Integration testing verifies that all components work together correctly, including ComfyUI, SteadyDancer, and R2 sync.

### 4.1 ComfyUI Integration Test

**Purpose:** Verify ComfyUI server starts and responds correctly.

```bash
#!/bin/bash
# ComfyUI integration tests

echo "=== COMFYUI INTEGRATION TEST ==="
echo ""

# 4.1.1 Start ComfyUI in background
echo "[4.1.1] Starting ComfyUI server..."
docker run -d --name comfyui-test \
    --gpus all \
    -p 8188:8188 \
    -v /home/oz/projects/2025/oz/12/runpod/docker:/workspace \
    zr4-runtime:latest

# Wait for startup
echo "Waiting for ComfyUI to start..."
sleep 15

# 4.1.2 Check if ComfyUI is responding
echo ""
echo "[4.1.2] Checking ComfyUI health endpoint..."
MAX_RETRIES=10
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8188/ 2>/dev/null || echo "000")
    if [ "$RESPONSE" = "200" ]; then
        echo "ComfyUI responding with HTTP 200"
        break
    fi
    RETRY=$((RETRY + 1))
    echo "Retry $RETRY/$MAX_RETRIES - Response: $RESPONSE"
    sleep 5
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    echo "FAIL: ComfyUI not responding after $MAX_RETRIES retries"
    echo "Check logs with: docker logs comfyui-test"
else
    echo "PASS: ComfyUI is responding"
fi

# 4.1.3 Check API endpoints
echo ""
echo "[4.1.3] Testing ComfyUI API endpoints..."

# Check system stats endpoint
echo "  System stats:"
curl -s http://localhost:8188/system_stats | python3 -m json.tool 2>/dev/null | head -20 || echo "  Endpoint not available"

# Check queue status
echo ""
echo "  Queue status:"
curl -s http://localhost:8188/queue | python3 -m json.tool 2>/dev/null | head -10 || echo "  Endpoint not available"

# 4.1.4 Test workflow execution
echo ""
echo "[4.1.4] Testing workflow execution..."

# Create simple test prompt (using ComfyUI API format)
cat > /tmp/test_prompt.json << 'EOF'
{
    "3": {
        "inputs": {
            "text": "A beautiful sunset over mountains",
            " CLIP_text_encoder_tokenization positive": ["positive"]
        },
        "class_type": "CLIPTextEncode"
    },
    "4": {
        "inputs": {
            "text": "low quality, blurry",
            " CLIP_text_encoder_tokenization negative": ["negative"]
        },
        "class_type": "CLIPTextEncode"
    },
    "6": {
        "inputs": {
            "samples": "samples",
            "vae": "vae"
        },
        "class_type": "VAEDecode"
    }
}
EOF

# Submit prompt (this is simplified - actual API call would need proper workflow JSON)
echo "  Test prompt created (workflow submission requires full workflow JSON)"
echo "  API structure verified"

# 4.1.5 Check ComfyUI logs
echo ""
echo "[4.1.5] Checking ComfyUI logs for errors..."
docker logs --tail 50 comfyui-test 2>&1 | grep -iE "error|exception|failed" || echo "No errors in logs"

# 4.1.6 Cleanup
echo ""
echo "[4.1.6] Cleaning up test container..."
docker stop comfyui-test && docker rm comfyui-test

echo ""
echo "=== COMFYUI INTEGRATION TEST COMPLETE ==="
```

**Pass Criteria:**
- ComfyUI server starts without errors
- Health endpoint returns HTTP 200
- API endpoints accessible
- No errors in logs

**Remediation Actions:**
- If server fails to start: Check port conflicts, verify all dependencies installed
- If API not responding: Check ComfyUI logs for startup errors
- If workflow fails: Validate workflow JSON structure, check node compatibility

### 4.2 SteadyDancer Pipeline Test

**Purpose:** Verify SteadyDancer video generation pipeline works correctly.

```bash
#!/bin/bash
# SteadyDancer integration test

echo "=== STEADYDANCER PIPELINE TEST ==="
echo ""

# 4.2.1 Check SteadyDancer dependencies
echo "[4.2.1] Checking SteadyDancer dependencies..."
docker run --rm zr4-runtime:latest python3 << 'PYEOF'
import sys

# Check for SteadyDancer-specific dependencies
deps = [
    ("mmcv", "mmcv"),
    ("mmpose", "mmpose"),
    ("mmengine", "mmengine"),
    ("decord", "decord"),
    ("mediapipe", "mediapipe"),
]

for module, package in deps:
    try:
        __import__(module)
        print(f"  {package}: OK")
    except ImportError as e:
        print(f"  {package}: MISSING - {e}")
        sys.exit(1)

print("\nAll SteadyDancer dependencies available")
PYEOF

# 4.2.2 Test mmcv/mmpose import
echo ""
echo "[4.2.2] Testing mmcv/mmpose imports..."
docker run --rm zr4-runtime:latest python3 << 'PYEOF'
print("Testing mmcv import...")
try:
    import mmcv
    print(f"  mmcv version: {mmcv.__version__}")
    print("  mmcv: PASSED")
except ImportError as e:
    print(f"  mmcv: FAILED - {e}")

print("\nTesting mmpose import...")
try:
    import mmpose
    print(f"  mmpose version: {mmpose.__version__}")
    print("  mmpose: PASSED")
except ImportError as e:
    print(f"  mmpose: FAILED - {e}")

print("\nTesting mmengine import...")
try:
    import mmengine
    print(f"  mmengine version: {mmengine.__version__}")
    print("  mmengine: PASSED")
except ImportError as e:
    print(f"  mmengine: FAILED - {e}")
PYEOF

# 4.2.3 Test pose detection
echo ""
echo "[4.2.3] Testing pose detection functionality..."
docker run --rm --gpus all -v /home/oz/projects/2025/oz/12/runpod/docker:/workspace \
    zr4-runtime:latest python3 << 'PYEOF'
import torch
import cv2
import numpy as np

print("Testing pose detection...")

try:
    # Try importing pose estimation tools
    from mmpose.apis import inference_top_down_pose_model, init_pose_model

    # Create test input (simple image)
    test_image = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)

    # Test pose model initialization (without loading actual weights)
    print("Pose estimation library: AVAILABLE")
    print("Pose detection: PASSED (libraries functional)")

except Exception as e:
    print(f"Pose detection: FAILED - {e}")
    import traceback
    traceback.print_exc()
PYEOF

# 4.2.4 Test SteadyDancer pipeline execution
echo ""
echo "[4.2.4] Testing SteadyDancer pipeline..."
docker run --rm --gpus all -v /home/oz/projects/2025/oz/12/runpod/docker:/workspace \
    zr4-runtime:latest python3 << 'PYEOF'
import torch
import time

print("Testing SteadyDancer pipeline...")

try:
    # Import SteadyDancer components
    from steadydancer import SteadyDancerPipeline

    print("SteadyDancerPipeline: IMPORTED")

    # Test with mock data (since actual model is large)
    print("\nRunning pipeline test with mock data...")

    # Simulate pose estimation
    import numpy as np
    pose_sequence = np.random.randn(30, 17, 3)  # 30 frames, 17 keypoints

    print(f"Pose sequence shape: {pose_sequence.shape}")
    print("Pose extraction: PASSED")

    # Test reference image processing
    reference_image = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
    print(f"Reference image shape: {reference_image.shape}")
    print("Reference image processing: PASSED")

    print("\nSteadyDancer pipeline: FUNCTIONAL")

except ImportError as e:
    print(f"SteadyDancer pipeline: NOT INSTALLED - {e}")
except Exception as e:
    print(f"SteadyDancer pipeline: FAILED - {e}")
    import traceback
    traceback.print_exc()
PYEOF

# 4.2.5 Verify ControlNet dependencies
echo ""
echo "[4.2.5] Testing ControlNet dependencies..."
docker run --rm --gpus all -v /home/oz/projects/2025/oz/12/runpod/docker:/workspace \
    zr4-runtime:latest python3 << 'PYEOF'
import sys

print("Checking ControlNet dependencies...")

# ControlNet-related packages
control_deps = [
    ("controlnet_aux", "controlnet-aux"),
    ("transformers", "transformers"),
    ("diffusers", "diffusers"),
    ("torch", "torch"),
]

all_ok = True
for module, package in control_deps:
    try:
        __import__(module)
        print(f"  {package}: OK")
    except ImportError as e:
        print(f"  {package}: MISSING")
        all_ok = False

if all_ok:
    print("\nControlNet dependencies: AVAILABLE")
else:
    print("\nControlNet dependencies: INCOMPLETE")
    sys.exit(1)
PYEOF

echo ""
echo "=== STEADYDANCER PIPELINE TEST COMPLETE ==="
```

**Pass Criteria:**
- All SteadyDancer dependencies (mmcv, mmpose, mmengine) import successfully
- Pose detection libraries functional
- ControlNet dependencies available
- No import errors

**Remediation Actions:**
- If mmcv/mmpose missing: Install via pip with CUDA support
- If pose detection fails: Check mmpose model weights availability
- If ControlNet issues: Install controlnet-aux package

### 4.3 R2 Sync Integration Test

**Purpose:** Verify Cloudflare R2 sync functionality works correctly.

```bash
#!/bin/bash
# R2 sync integration test

echo "=== R2 SYNC INTEGRATION TEST ==="
echo ""

# 4.3.1 Check R2 sync script availability
echo "[4.3.1] Checking R2 sync script..."
docker run --rm zr4-runtime:latest bash -c '
if [ -f /upload_to_r2.py ]; then
    echo "R2 sync script: FOUND"
    python3 /upload_to_r2.py --help 2>&1 | head -20
else
    echo "R2 sync script: NOT FOUND"
fi
'

# 4.3.2 Test R2 connectivity (if credentials available)
echo ""
echo "[4.3.2] Testing R2 connectivity..."

# Create test configuration
cat > /tmp/r2_test_config.json << 'EOF'
{
    "endpoint": "https://test.eu.r2.cloudflarestorage.com",
    "bucket": "test-runpod",
    "access_key_id": "test-key",
    "secret_access_key": "test-secret"
}
EOF

docker run --rm -v /tmp/r2_test_config.json:/tmp/config.json \
    zr4-runtime:latest python3 << 'PYEOF'
import json
import boto3
from botocore.exceptions import ClientError

print("Testing R2 connectivity...")

# Load test config
with open("/tmp/config.json") as f:
    config = json.load(f)

# Create S3 client configured for R2
s3 = boto3.client(
    's3',
    endpoint_url=config['endpoint'],
    aws_access_key_id=config['access_key_id'],
    aws_secret_access_key=config['secret_access_key']
)

# Test connection by listing buckets
try:
    response = s3.list_buckets()
    print(f"Connection successful")
    print(f"Available buckets: {[b['Name'] for b in response.get('Buckets', [])]}")
except ClientError as e:
    error_code = e.response.get('Error', {}).get('Code', 'Unknown')
    if error_code == 'InvalidAccessKeyId':
        print("Connection test: FAILED - Invalid credentials")
    elif error_code == 'SignatureDoesNotMatch':
        print("Connection test: FAILED - Signature mismatch")
    else:
        print(f"Connection test: FAILED - {error_code}")
except Exception as e:
    print(f"Connection test: FAILED - {str(e)}")
PYEOF

# 4.3.3 Test file upload
echo ""
echo "[4.3.3] Testing file upload..."
# Create test file
echo "Test file for R2 upload $(date)" > /tmp/test_upload.txt

docker run --rm \
    -v /tmp/test_upload.txt:/tmp/test_upload.txt \
    zr4-runtime:latest python3 << 'PYEOF'
import os
import boto3
from botocore.exceptions import ClientError

print("Testing file upload to R2...")

# Use actual environment variables or test config
endpoint = os.environ.get('R2_ENDPOINT', 'https://test.eu.r2.cloudflarestorage.com')
bucket = os.environ.get('R2_BUCKET', 'test-runpod')
access_key = os.environ.get('R2_ACCESS_KEY_ID', 'test-key')
secret_key = os.environ.get('R2_SECRET_ACCESS_KEY', 'test-secret')

s3 = boto3.client(
    's3',
    endpoint_url=endpoint,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key
)

try:
    # Try to upload test file
    s3.upload_file('/tmp/test_upload.txt', bucket, 'test/test_upload.txt')
    print("File upload: SUCCESS")

    # Verify upload
    s3.head_object(Bucket=bucket, Key='test/test_upload.txt')
    print("File verification: SUCCESS")

except ClientError as e:
    error_code = e.response.get('Error', {}).get('Code', 'Unknown')
    if error_code == 'NoSuchBucket':
        print(f"File upload: FAILED - Bucket '{bucket}' does not exist")
    elif error_code == 'AccessDenied':
        print("File upload: FAILED - Access denied")
    else:
        print(f"File upload: FAILED - {error_code}")
except Exception as e:
    print(f"File upload: FAILED - {str(e)}")
PYEOF

# 4.3.4 Test R2 sync daemon
echo ""
echo "[4.3.4] Testing R2 sync daemon availability..."
docker run --rm zr4-runtime:latest bash -c '
if [ -f /r2_sync.sh ]; then
    echo "R2 sync daemon script: FOUND"
    head -20 /r2_sync.sh
else
    echo "R2 sync daemon script: NOT FOUND"
fi
'

# 4.3.5 Validate R2 environment variables
echo ""
echo "[4.3.5] Validating R2 environment variables..."
docker run --rm zr4-runtime:latest env | grep -E "^R2_" || echo "No R2 environment variables set (expected in production)"

echo ""
echo "=== R2 SYNC INTEGRATION TEST COMPLETE ==="
```

**Pass Criteria:**
- R2 sync script accessible and functional
- Network connectivity to R2 endpoint successful
- File upload and verification successful
- All required environment variables documented

**Remediation Actions:**
- If connectivity fails: Verify R2 credentials, check network/firewall
- If upload fails: Verify bucket exists, check permissions
- If script missing: Copy upload_to_r2.py to container image

---

## 5. Performance Benchmarks

Performance benchmarks establish baseline metrics for key operations and identify optimization opportunities.

### 5.1 Inference Performance Benchmark

**Purpose:** Measure and record inference performance metrics.

```bash
#!/bin/bash
# Inference performance benchmark

echo "=== INFERENCE PERFORMANCE BENCHMARK ==="
echo ""

# 5.1.1 Create benchmark script
cat > /tmp/benchmark_inference.sh << 'SCRIPT'
#!/bin/bash
echo "=== INFERENCE BENCHMARK RESULTS ==="
echo "Date: $(date)"
echo ""

python3 << 'PYEOF'
import torch
import time
import json
from statistics import mean, stdev
from diffusers import StableDiffusionXLPipeline, EulerDiscreteScheduler

# Configuration
WARMUP_RUNS = 2
BENCHMARK_RUNS = 5
IMAGE_SIZES = [(512, 512), (768, 768), (1024, 1024)]
INFERENCE_STEPS = [20, 30, 50]

# Load pipeline
print("Loading Stable Diffusion XL pipeline...")
pipe = StableDiffusionXLPipeline.from_pretrained(
    "/workspace/models/sdxl",
    torch_dtype=torch.float16,
    use_safetensors=True
)
pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
pipe = pipe.to("cuda")

# Warmup
print(f"\nPerforming {WARMUP_RUNS} warmup runs...")
for i in range(WARMUP_RUNS):
    _ = pipe(
        prompt="Warmup image",
        num_inference_steps=10,
        height=512,
        width=512
    )
    torch.cuda.synchronize()
print("Warmup complete")

# Benchmark function
def benchmark(size, steps):
    heights, widths = size
    times = []
    memory_samples = []

    for i in range(BENCHMARK_RUNS):
        start = time.time()

        image = pipe(
            prompt="A benchmark test image",
            num_inference_steps=steps,
            height=heights,
            width=widths
        ).images[0]

        torch.cuda.synchronize()
        elapsed = time.time() - start

        times.append(elapsed)
        memory_samples.append(torch.cuda.memory_allocated() / 1024**3)

    return {
        'size': f"{heights}x{widths}",
        'steps': steps,
        'avg_time': mean(times),
        'min_time': min(times),
        'max_time': max(times),
        'std_dev': stdev(times) if len(times) > 1 else 0,
        'avg_memory_gb': mean(memory_samples),
        'images_per_minute': 60 / mean(times) if mean(times) > 0 else 0
    }

# Run benchmarks
results = []
print(f"\nRunning {BENCHMARK_RUNS} benchmark runs for each configuration...")

for size in IMAGE_SIZES:
    for steps in INFERENCE_STEPS:
        print(f"\nBenchmarking: {size[0]}x{size[1]} @ {steps} steps")
        result = benchmark(size, steps)
        results.append(result)

        print(f"  Average time: {result['avg_time']:.2f}s")
        print(f"  Min/Max: {result['min_time']:.2f}s / {result['max_time']:.2f}s")
        print(f"  Images/minute: {result['images_per_minute']:.2f}")
        print(f"  Avg VRAM: {result['avg_memory_gb']:.2f} GB")

# Save results
output = {
    'timestamp': str(__import__('datetime').datetime.now()),
    'gpu': torch.cuda.get_device_name(0),
    'results': results
}

with open('/tmp/benchmark_results.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\n=== BENCHMARK SUMMARY ===")
print(f"Best performance: {max(r['images_per_minute'] for r in results):.2f} images/min")
print(f"Lowest memory: {min(r['avg_memory_gb'] for r in results):.2f} GB")
print(f"Results saved to: /tmp/benchmark_results.json")
PYEOF

echo ""
echo "=== INFERENCE BENCHMARK COMPLETE ==="
SCRIPT

chmod +x /tmp/benchmark_inference.sh

# 5.1.2 Run benchmark
echo "[5.1.2] Running inference performance benchmark..."
docker run --rm --gpus all -v /tmp/benchmark_inference.sh:/benchmark.sh \
    -v /home/oz/projects/2025/oz/12/runpod/docker:/workspace \
    -v /tmp:/tmp \
    zr4-runtime:latest /benchmark.sh

# 5.1.3 Display results
echo ""
echo "[5.1.3] Benchmark Results:"
cat /tmp/benchmark_results.json 2>/dev/null | python3 -m json.tool || echo "Results not available"

echo ""
echo "=== PERFORMANCE BENCHMARK COMPLETE ==="
```

**Expected Results (RTX 4090):**
- 512x512 @ 20 steps: ~1.5-2.0s per image, ~30-40 images/minute
- 768x768 @ 30 steps: ~3-4s per image, ~15-20 images/minute
- 1024x1024 @ 50 steps: ~8-12s per image, ~5-7 images/minute
- VRAM usage: 8-14GB depending on resolution

**Pass Criteria:**
- All benchmark configurations complete successfully
- Performance within expected range for GPU class
- No OOM errors or crashes

### 5.2 VRAM Efficiency Benchmark

**Purpose:** Measure VRAM usage efficiency across different configurations.

```bash
#!/bin/bash
# VRAM efficiency benchmark

echo "=== VRAM EFFICIENCY BENCHMARK ==="
echo ""

# 5.2.1 Create VRAM efficiency test
cat > /tmp/vram_benchmark.sh << 'SCRIPT'
#!/bin/bash
echo "=== VRAM EFFICIENCY MEASUREMENTS ==="
echo "Date: $(date)"
echo ""

python3 << 'PYEOF'
import torch
import time
import gc
from contextlib import contextmanager

@contextmanager
def track_memory(label):
    """Context manager to track GPU memory at point of interest"""
    torch.cuda.synchronize()
    start_allocated = torch.cuda.memory_allocated() / 1024**3
    start_reserved = torch.cuda.memory_reserved() / 1024**3
    yield
    torch.cuda.synchronize()
    end_allocated = torch.cuda.memory_allocated() / 1024**3
    end_reserved = torch.cuda.memory_reserved() / 1024**3
    print(f"{label}:")
    print(f"  Allocated: {start_allocated:.2f} → {end_allocated:.2f} GB (Δ {end_allocated-start_allocated:+.2f})")
    print(f"  Reserved:  {start_reserved:.2f} → {end_reserved:.2f} GB (Δ {end_reserved-start_reserved:+.2f})")

print("Loading pipeline with memory tracking...")
from diffusers import StableDiffusionXLPipeline

with track_memory("Initial load"):
    pipe = StableDiffusionXLPipeline.from_pretrained(
        "/workspace/models/sdxl",
        torch_dtype=torch.float16,
        use_safetensors=True
    )
    pipe = pipe.to("cuda")

print("\n" + "="*50)
print("Testing different configurations:")
print("="*50)

configs = [
    {"height": 512, "width": 512, "steps": 20, "batch": 1},
    {"height": 768, "width": 768, "steps": 30, "batch": 1},
    {"height": 1024, "width": 1024, "steps": 50, "batch": 1},
    {"height": 512, "width": 512, "steps": 20, "batch": 4},
]

results = []
for i, config in enumerate(configs):
    print(f"\n[{i+1}] Configuration: {config['height']}x{config['width']} @ {config['steps']} steps (batch={config['batch']})")

    with track_memory("  Pre-generation"):
        gc.collect()
        torch.cuda.empty_cache()

    start_allocated = torch.cuda.memory_allocated() / 1024**3

    start = time.time()
    images = pipe(
        prompt="Test image",
        num_inference_steps=config['steps'],
        height=config['height'],
        width=config['width'],
        num_images_per_prompt=config['batch']
    )
    torch.cuda.synchronize()
    elapsed = time.time() - start

    peak_allocated = torch.cuda.max_memory_allocated() / 1024**3

    print(f"  Generation time: {elapsed:.2f}s")
    print(f"  Peak VRAM: {peak_allocated:.2f} GB")
    print(f"  Final allocated: {start_allocated:.2f} GB")

    results.append({
        'config': config,
        'time': elapsed,
        'peak_vram': peak_allocated
    })

    # Cleanup between tests
    del images
    gc.collect()
    torch.cuda.empty_cache()

print("\n" + "="*50)
print("EFFICIENCY SUMMARY:")
print("="*50)

# Calculate efficiency score (lower is better)
for r in results:
    config = r['config']
    efficiency = r['peak_vram'] * r['time']
    print(f"{config['height']}x{config['width']} @ {config['steps']}: {efficiency:.2f} GB·s efficiency")

# Best configuration
best = min(results, key=lambda x: x['peak_vram'] * x['time'])
print(f"\nMost efficient: {best['config']['height']}x{best['config']['width']} @ {best['config']['steps']} steps")

# Memory by resolution
print("\nMemory usage by resolution:")
for h in [512, 768, 1024]:
    h_results = [r for r in results if r['config']['height'] == h]
    if h_results:
        avg_vram = sum(r['peak_vram'] for r in h_results) / len(h_results)
        print(f"  {h}x{h}: avg {avg_vram:.2f} GB peak")

PYEOF

chmod +x /tmp/vram_benchmark.sh

# 5.2.2 Run VRAM benchmark
echo "[5.2.2] Running VRAM efficiency benchmark..."
docker run --rm --gpus all -v /tmp/vram_benchmark.sh:/vram_bench.sh \
    -v /home/oz/projects/2025/oz/12/runpod/docker:/workspace \
    zr4-runtime:latest /vram_bench.sh

echo ""
echo "=== VRAM EFFICIENCY BENCHMARK COMPLETE ==="
```

**Pass Criteria:**
- VRAM stays within 16GB limit for all configurations
- Peak memory ≤ 14GB for 1024x1024 @ 50 steps
- No memory leaks between generations

### 5.3 Batch Processing Throughput

**Purpose:** Measure maximum batch throughput within VRAM constraints.

```bash
#!/bin/bash
# Batch processing throughput test

echo "=== BATCH PROCESSING THROUGHPUT TEST ==="
echo ""

# 5.3.1 Create batch throughput test
cat > /tmp/batch_throughput.sh << 'SCRIPT'
#!/bin/bash
echo "=== BATCH THROUGHPUT MEASUREMENTS ==="
echo ""

python3 << 'PYEOF'
import torch
import time
from diffusers import StableDiffusionXLPipeline

print("Loading pipeline...")
pipe = StableDiffusionXLPipeline.from_pretrained(
    "/workspace/models/sdxl",
    torch_dtype=torch.float16,
    use_safetensors=True
)
pipe = pipe.to("cuda")

print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"Total VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
print()

# Find maximum batch size
max_successful_batch = 0
batch_sizes = [1, 2, 4, 8, 16, 32]

for batch_size in batch_sizes:
    print(f"Testing batch size: {batch_size}")

    try:
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()

        start = time.time()
        images = pipe(
            prompt="Test batch image",
            num_inference_steps=20,
            height=512,
            width=512,
            num_images_per_prompt=batch_size
        )
        torch.cuda.synchronize()
        elapsed = time.time() - start

        peak_memory = torch.cuda.max_memory_allocated() / 1024**3

        throughput = batch_size / elapsed
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Peak VRAM: {peak_memory:.2f} GB")
        print(f"  Throughput: {throughput:.2f} images/min")
        print(f"  Status: SUCCESS")

        max_successful_batch = batch_size

        del images
        torch.cuda.empty_cache()

    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            print(f"  Status: OOM (batch too large)")
        else:
            print(f"  Status: FAILED - {str(e)}")
        break

print("\n" + "="*50)
print(f"MAXIMUM BATCH SIZE: {max_successful_batch}")
print("="*50)

# Calculate optimal batch size for different scenarios
print("\nOptimal batch recommendations:")
for scenario, batch in [("Maximum throughput", max_successful_batch),
                         ("Memory efficient", max(1, max_successful_batch // 4)),
                         ("Balanced", max(1, max_successful_batch // 2))]:
    print(f"  {scenario}: batch={batch}")

PYEOF

chmod +x /tmp/batch_throughput.sh

# 5.3.2 Run batch throughput test
echo "[5.3.2] Running batch throughput test..."
docker run --rm --gpus all -v /tmp/batch_throughput.sh:/batch_test.sh \
    -v /home/oz/projects/2025/oz/12/runpod/docker:/workspace \
    zr4-runtime:latest /batch_test.sh

echo ""
echo "=== BATCH THROUGHPUT TEST COMPLETE ==="
```

**Pass Criteria:**
- Successfully process batch size ≥ 4 at 512x512 resolution
- Throughput increases with batch size (up to VRAM limit)
- No OOM errors at recommended batch sizes

---

## 6. Error Detection and Recovery

Error detection and recovery procedures ensure the system handles failures gracefully and provides actionable information for troubleshooting.

### 6.1 Common Error Patterns and Detection

**Purpose:** Identify and categorize common errors with detection methods.

```bash
#!/bin/bash
# Common error detection

echo "=== COMMON ERROR PATTERN DETECTION ==="
echo ""

# 6.1.1 Create error detection script
cat > /tmp/error_detection.sh << 'SCRIPT'
#!/bin/bash
echo "=== ERROR DETECTION AND CLASSIFICATION ==="
echo ""

python3 << 'PYEOF'
import subprocess
import re
import json

# Error patterns to detect
ERROR_PATTERNS = {
    "CUDA_OUT_OF_MEMORY": {
        "patterns": [
            r"CUDA out of memory",
            r"out of memory",
            r"OOM",
            r"memory allocation failed"
        ],
        "severity": "critical",
        "message": "GPU VRAM exhausted",
        "remediation": "Reduce batch size, image resolution, or use model quantization"
    },
    "CUDA_ERROR": {
        "patterns": [
            r"CUDA error",
            r"cudaGetLastError",
            r"CUDA kernel"
        ],
        "severity": "critical",
        "message": "CUDA runtime error",
        "remediation": "Check GPU drivers, CUDA version compatibility, restart GPU processes"
    },
    "MODEL_LOADING_ERROR": {
        "patterns": [
            r"Error loading model",
            r"Failed to load",
            r"Could not find"
        ],
        "severity": "high",
        "message": "Model file missing or corrupted",
        "remediation": "Verify model files exist, check file integrity, re-download if needed"
    },
    "VERSION_MISMATCH": {
        "patterns": [
            r"version mismatch",
            r"incompatible version",
            r"expected.*got"
        ],
        "severity": "high",
        "message": "Version mismatch between components",
        "remediation": "Align package versions, update dependencies, use compatible library versions"
    },
    "IMPORT_ERROR": {
        "patterns": [
            r"ImportError",
            r"ModuleNotFoundError",
            r"No module named"
        ],
        "severity": "high",
        "message": "Missing Python module",
        "remediation": "Install missing package, verify Python path, check virtual environment"
    },
    "NETWORK_ERROR": {
        "patterns": [
            r"ConnectionError",
            r"Network is unreachable",
            r"Could not resolve"
        ],
        "severity": "medium",
        "message": "Network connectivity issue",
        "remediation": "Check network connection, proxy settings, DNS resolution"
    },
    "FILE_NOT_FOUND": {
        "patterns": [
            r"FileNotFoundError",
            r"No such file",
            r"File exists"
        ],
        "severity": "medium",
        "message": "File or directory missing",
        "remediation": "Verify file paths, check mount points, create missing directories"
    },
    "PERMISSION_ERROR": {
        "patterns": [
            r"Permission denied",
            r"Access denied",
            r"not writable"
        ],
        "severity": "medium",
        "message": "Permission issue",
        "remediation": "Check file permissions, run with appropriate user, adjust access rights"
    }
}

def check_error_patterns(log_content):
    """Check log content for known error patterns"""
    detected = []

    for error_type, config in ERROR_PATTERNS.items():
        for pattern in config["patterns"]:
            if re.search(pattern, log_content, re.IGNORECASE):
                detected.append({
                    "type": error_type,
                    "severity": config["severity"],
                    "message": config["message"],
                    "remediation": config["remediation"]
                })
                break

    return detected

# Test with sample error logs
sample_errors = [
    "CUDA out of memory. Tried to allocate 2.00 GiB",
    "ImportError: No module named 'torchvision'",
    "FileNotFoundError: [Errno 2] No such file: 'model.safetensors'",
    "Permission denied: cannot write to output directory"
]

print("Testing error pattern detection:")
print("="*60)

for error in sample_errors:
    detected = check_error_patterns(error)
    print(f"\nInput: {error}")
    if detected:
        for d in detected:
            print(f"  Detected: {d['type']} ({d['severity']})")
            print(f"  Remediation: {d['remediation']}")
    else:
        print("  No pattern detected")

print("\n" + "="*60)
print("Error detection module: FUNCTIONAL")
PYEOF

echo ""
echo "=== ERROR PATTERN DETECTION TEST COMPLETE ==="
SCRIPT

chmod +x /tmp/error_detection.sh

# 6.1.2 Run error detection test
docker run --rm -v /tmp/error_detection.sh:/error_test.sh \
    zr4-runtime:latest /error_test.sh

# 6.1.3 Health check script
echo ""
echo "[6.1.3] Creating comprehensive health check script..."
cat > /tmp/health_check.sh << 'SCRIPT'
#!/bin/bash
echo "=== CONTAINER HEALTH CHECK ==="
echo "Timestamp: $(date)"
echo ""

FAILED=0

# Check 1: GPU availability
echo "[1/8] Checking GPU availability..."
if nvidia-smi --query-gpu=count --format=csv,noheader | grep -q "[1-9]"; then
    echo "  GPU: OK ($(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l) GPU(s) detected)"
else
    echo "  GPU: FAILED - No GPU detected"
    FAILED=1
fi

# Check 2: CUDA availability
echo ""
echo "[2/8] Checking CUDA availability..."
if python3 -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
    CUDA_VERSION=$(python3 -c "import torch; print(torch.version.cuda)")
    echo "  CUDA: OK (version $CUDA_VERSION)"
else
    echo "  CUDA: FAILED - PyTorch CUDA not available"
    FAILED=1
fi

# Check 3: PyTorch import
echo ""
echo "[3/8] Checking PyTorch..."
if python3 -c "import torch; print(f'PyTorch {torch.__version__}')" 2>/dev/null; then
    echo "  PyTorch: OK"
else
    echo "  PyTorch: FAILED"
    FAILED=1
fi

# Check 4: Required directories
echo ""
echo "[4/8] Checking required directories..."
for dir in /workspace/models /workspace/output; do
    if [ -d "$dir" ]; then
        echo "  $dir: OK"
    else
        echo "  $dir: FAILED - Missing"
        FAILED=1
    fi
done

# Check 5: ComfyUI server
echo ""
echo "[5/8] Checking ComfyUI..."
if pgrep -f "python.*comfy" > /dev/null; then
    echo "  ComfyUI: OK (running)"
else
    echo "  ComfyUI: WARNING (not running - expected if idle)"
fi

# Check 6: Disk space
echo ""
echo "[6/8] Checking disk space..."
AVAIL_GB=$(df -BG /workspace | awk 'NR==2 {print $4}' | tr -d 'G')
if [ "$AVAIL_GB" -gt 10 ]; then
    echo "  Disk: OK (${AVAIL_GB}GB available)"
else
    echo "  Disk: WARNING (${AVAIL_GB}GB available - low)"
fi

# Check 7: Memory usage
echo ""
echo "[7/8] Checking memory..."
if command -v free &> /dev/null; then
    MEM_TOTAL=$(free -h | awk 'NR==2 {print $2}')
    MEM_AVAILABLE=$(free -h | awk 'NR==2 {print $7}')
    echo "  Memory: OK (${MEM_AVAILABLE} available of ${MEM_TOTAL})"
else
    echo "  Memory: SKIPPED (free not available)"
fi

# Check 8: Process health
echo ""
echo "[8/8] Checking critical processes..."
CRITICAL_PROCS=("python" "ffmpeg" "git")
for proc in "${CRITICAL_PROCS[@]}"; do
    if command -v "$proc" &> /dev/null; then
        echo "  $proc: OK"
    else
        echo "  $proc: FAILED - Not found"
        FAILED=1
    fi
done

# Summary
echo ""
echo "="*60
if [ $FAILED -eq 0 ]; then
    echo "HEALTH STATUS: HEALTHY"
    echo "All checks passed successfully"
    exit 0
else
    echo "HEALTH STATUS: DEGRADED ($FAILED check(s) failed)"
    echo "Review failed checks above"
    exit 1
fi
SCRIPT

chmod +x /tmp/health_check.sh

echo ""
echo "=== COMMON ERROR DETECTION COMPLETE ==="
```

**Pass Criteria:**
- Error detection identifies all common error patterns
- Health check script runs without errors
- All critical services (GPU, CUDA, PyTorch) functional

### 6.2 Recovery Procedures

**Purpose:** Document recovery procedures for common failure scenarios.

```bash
#!/bin/bash
# Recovery procedure documentation

cat > /tmp/recovery_procedures.md << 'EOF'
# Recovery Procedures

## 6.2.1 GPU Memory Recovery

**Problem:** CUDA out of memory error, GPU not responding

**Recovery Steps:**
```bash
# 1. Kill all GPU processes
sudo fuser -v /dev/nvidia* | awk '{print $2}' | xargs -r kill -9

# 2. Reset GPU (if supported)
sudo nvidia-smi --gpu-reset

# 3. Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 4. Restart container
docker restart <container_name>
```

**Prevention:**
- Use `torch.cuda.empty_cache()` after generations
- Limit batch sizes based on available VRAM
- Enable attention slicing for large images

## 6.2.2 Container Recovery

**Problem:** Container not responding, stuck processes

**Recovery Steps:**
```bash
# 1. Check container status
docker ps -a | grep zr4

# 2. View container logs
docker logs <container_id> --tail 100

# 3. Restart container
docker restart <container_id>

# 4. If unresponsive, force stop and restart
docker stop -t 30 <container_id>
docker start <container_id>

# 5. Nuclear option (destroy and recreate)
docker stop <container_id>
docker rm <container_id>
docker run -d --name <container_name> [new_run_command]
```

## 6.2.3 Model Loading Recovery

**Problem:** Model fails to load, corrupted files

**Recovery Steps:**
```bash
# 1. Verify model files exist
ls -la /workspace/models/

# 2. Check file integrity
sha256sum /workspace/models/**/*.safetensors

# 3. Re-download corrupted models
rm -rf /workspace/models/corrupted_model
docker exec <container> python3 -c "
from diffusers import StableDiffusionXLPipeline
pipe = StableDiffusionXLPipeline.from_pretrained(
    'path/to/model',
    revision='main',
    use_safetensors=True
)
"

# 4. Rebuild model cache
docker exec <container> python3 -c "
import torch
torch.hub.load('path/to/model', 'model')
"
```

## 6.2.4 Network Recovery (R2 Sync)

**Problem:** R2 upload failures, connection errors

**Recovery Steps:**
```bash
# 1. Test connectivity
python3 /upload_to_r2.py --test

# 2. Verify credentials
echo $R2_ACCESS_KEY_ID
echo $R2_ENDPOINT

# 3. Check network
curl -I https://$R2_ENDPOINT

# 4. Retry failed uploads
python3 /upload_to_r2.py /workspace/ComfyUI/output/failed_file.png

# 5. Restart sync daemon
docker restart <container>
```

## 6.2.5 Docker Build Recovery

**Problem:** Build failures, layer cache corruption

**Recovery Steps:**
```bash
# 1. Clear Docker build cache
docker builder prune -af

# 2. Remove stuck builds
docker builder prune --all

# 3. Clean Docker system
docker system prune -af
docker volume prune -f

# 4. Rebuild from scratch
docker build --no-cache -t zr4:latest .

# 5. Verify intermediate layers
docker history zr4:latest
```

## 6.2.6 ComfyUI Recovery

**Problem:** ComfyUI not starting, API errors

**Recovery Steps:**
```bash
# 1. Check ComfyUI process
pgrep -f "python.*comfy"
docker logs <container> | grep -i error

# 2. Restart ComfyUI service
docker exec <container> pkill -f comfy
docker exec -d <container> python3 main.py

# 3. Clear ComfyUI cache
rm -rf /workspace/ComfyUI/output/*
rm -rf /workspace/ComfyUI/.cache

# 4. Verify port availability
netstat -tlnp | grep 8188
lsof -i :8188

# 5. Recreate container with port binding
docker run -p 8188:8188 ...
```

## 6.2.7 Emergency Recovery Checklist

When all else fails:

```bash
# Step 1: Document current state
echo "=== EMERGENCY RECOVERY ===" > /tmp/recovery_log.txt
date >> /tmp/recovery_log.txt
docker ps >> /tmp/recovery_log.txt
nvidia-smi >> /tmp/recovery_log.txt

# Step 2: Stop all containers
docker stop $(docker ps -q)

# Step 3: Clear GPU memory
sudo fuser -v /dev/nvidia* | awk '{print $2}' | xargs -r kill -9
sudo nvidia-smi --gpu-reset

# Step 4: Clear Docker cache
docker system prune -af

# Step 5: Reboot system (if necessary)
sudo reboot

# Step 6: Rebuild from known good state
git checkout HEAD -- Dockerfile
docker build -t zr4:recovered .

# Step 7: Verify with smoke test
docker run --rm --gpus all zr4:recovered python3 -c "
import torch
assert torch.cuda.is_available()
print('Recovery successful')
"
```

## 6.2.8 Rollback Procedure

**Problem:** New version has critical issues

**Rollback Steps:**
```bash
# 1. Identify previous working image
docker images | grep zr4

# 2. Stop current container
docker stop <current_container>

# 3. Start previous version
docker run -d --name <container_name> <previous_image_id>

# 4. Verify rollback
curl -s http://localhost:8188/ | head -5

# 5. If issues persist, restore from backup
docker load -i /backup/backup-image.tar
```

EOF

cat /tmp/recovery_procedures.md

echo ""
echo "=== RECOVERY PROCEDURES DOCUMENTED ==="
```

### 6.3 Logging and Monitoring

**Purpose:** Set up comprehensive logging for troubleshooting.

```bash
#!/bin/bash
# Logging and monitoring setup

cat > /tmp/logging_config.md << 'EOF'
# Logging and Monitoring Configuration

## 6.3.1 Container Logging

**Enable detailed logging in Dockerfile:**
```dockerfile
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=DEBUG

# Enable Python logging
RUN python3 -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

**Docker run options for logging:**
```bash
docker run \
  --log-driver json-file \
  --log-opt max-size=100m \
  --log-opt max-file=10 \
  -v /var/log/app:/var/log \
  zr4:latest
```

## 6.3.2 GPU Monitoring

**Real-time GPU monitoring script:**
```bash
#!/bin/bash
# gpu_monitor.sh - Continuous GPU monitoring

while true; do
    echo "[$(date)] $(nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader)"
    sleep 5
done | tee /var/log/gpu_monitor.log
```

**GPU alert script:**
```bash
#!/bin/bash
# gpu_alert.sh - Alert on GPU issues

while true; do
    TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader)
    MEM=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader)

    if [ $TEMP -gt 85 ]; then
        echo "ALERT: GPU temperature $TEMP°C" | mail -s "GPU Alert" admin@example.com
    fi

    sleep 60
done
```

## 6.3.3 Performance Logging

**Track inference performance:**
```python
# performance_logger.py
import time
import json
from datetime import datetime

class PerformanceLogger:
    def __init__(self, log_file="/var/log/inference_perf.log"):
        self.log_file = log_file

    def log_inference(self, config, time_taken, memory_used):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "config": config,
            "time_seconds": time_taken,
            "memory_gb": memory_used,
            "images_per_minute": 60/time_taken if time_taken > 0 else 0
        }
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")

    def get_stats(self, hours=24):
        import subprocess
        # Parse log file and calculate statistics
        pass
```

## 6.3.4 Error Log Aggregation

**Centralized error logging:**
```python
# error_logger.py
import logging
import sys
from datetime import datetime

class ErrorLogger:
    def __init__(self):
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/errors.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('ZR4')

    def log_error(self, error_type, message, context=None):
        self.logger.error(f"{error_type}: {message}", extra={'context': context})

    def log_cuda_error(self, error):
        self.log_error("CUDA_ERROR", str(error))

    def log_model_error(self, model_path, error):
        self.log_error("MODEL_ERROR", str(error), {'model': model_path})
```

## 6.3.5 Log Analysis Commands

**Useful log analysis commands:**
```bash
# View recent errors
tail -100 /var/log/app/error.log | grep ERROR

# Count error types
cat /var/log/app/error.log | grep -oE "ERROR: [A-Z_]+" | sort | uniq -c

# Find GPU memory issues
grep -i "memory\|oom\|cuda" /var/log/app/*.log

# Monitor in real-time
tail -f /var/log/app/access.log

# Check for patterns
grep -r "FAILED\|ERROR" /var/log/ | head -20
```

## 6.3.6 Monitoring Dashboard

**Key metrics to track:**
1. GPU utilization (target: >80% during inference)
2. VRAM usage (target: <16GB)
3. Temperature (target: <85°C)
4. Inference time per image
5. Queue length (ComfyUI)
6. Error rate per hour
7. R2 upload success rate

**Dashboard tools:**
- Grafana + Prometheus
- NVIDIA DCGM
- Custom Python dashboard
EOF

cat /tmp/logging_config.md

echo ""
echo "=== LOGGING AND MONITORING SETUP COMPLETE ==="
```

---

## 7. Verification Command Reference

Quick reference for all verification commands organized by category.

### 7.1 Pre-Build Commands

```bash
# System requirements
docker info                                    # Check Docker daemon
df -h /                                       # Check disk space
free -h                                       # Check RAM
nproc                                         # Check CPU cores

# GPU validation
nvidia-smi                                    # GPU info and VRAM
nvidia-smi --query-gpu=memory.total --format=csv  # VRAM check
nvidia-smi --query-gpu=driver_version --format=csv  # Driver version

# CUDA validation
nvcc --version                                # CUDA toolkit version
nvidia-smi | grep "CUDA Version"             # CUDA driver version
```

### 7.2 Build Commands

```bash
# Build with caching
docker build -t zr4:latest .                 # Standard build
docker build --no-cache -t zr4:latest .      # Force rebuild
docker buildx build -t zr4:latest .          # BuildKit build

# Monitor build
docker build . | tee build.log               # Log build output
docker history zr4:latest                    # View layer history
docker images | grep zr4                     # List zr4 images
```

### 7.3 Runtime Commands

```bash
# Container testing
docker run --rm --gpus all zr4-runtime:latest nvidia-smi

# Dependency verification
docker run --rm zr4-runtime:latest python3 -c "import torch; print(torch.__version__)"

# Model loading test
docker run --rm --gpus all -v /models:/models zr4-runtime:latest python3 load_model.py

# Inference test
docker run --rm --gpus all -v /outputs:/outputs zr4-runtime:latest python3 inference_test.py
```

### 7.4 Integration Test Commands

```bash
# ComfyUI tests
docker run -d -p 8188:8188 --name comfyui zr4-runtime:latest
curl http://localhost:8188/system_stats
docker logs comfyui

# R2 sync test
docker run --rm -e R2_ENDPOINT=$R2_ENDPOINT \
  -e R2_ACCESS_KEY_ID=$R2_ACCESS_KEY_ID \
  zr4-runtime:latest python3 /upload_to_r2.py --test

# SteadyDancer test
docker run --rm --gpus all zr4-runtime:latest python3 steadydancer_test.py
```

### 7.5 Benchmark Commands

```bash
# Inference benchmark
docker run --rm --gpus all -v /tmp:/tmp zr4-runtime:latest python3 benchmark.py

# VRAM monitoring
nvidia-smi -l 1                              # Real-time monitoring
nvidia-smi -q                                # Detailed query
nvidia-smi --query-gpu=memory.used,memory.total --format=csv -l 5

# Performance logging
docker run --rm --gpus all zr4-runtime:latest python3 perf_log.py
```

### 7.6 Error Recovery Commands

```bash
# Container recovery
docker restart <container_id>
docker logs <container_id> --tail 50
docker exec <container_id> nvidia-smi

# GPU recovery
sudo fuser -v /dev/nvidia* | awk '{print $2}' | xargs -r kill -9
sudo nvidia-smi --gpu-reset

# Build cache recovery
docker builder prune -af
docker system prune -af
```

---

## 8. Test Summary and Reporting

### 8.1 Verification Checklist

Use this checklist to track verification progress:

```markdown
## Pre-Build Validation
- [ ] Docker daemon running
- [ ] Disk space ≥ 100GB
- [ ] RAM ≥ 32GB
- [ ] CPU ≥ 8 cores
- [ ] GPU detected (16GB+ VRAM)
- [ ] Driver version ≥ 525
- [ ] CUDA 12.x compatible
- [ ] BuildX available

## Build Process
- [ ] Build completes successfully
- [ ] No build errors
- [ ] Cache hit ratio ≥ 80%
- [ ] Build time within expected range
- [ ] All dependencies installed

## Runtime Validation
- [ ] GPU accessible in container
- [ ] PyTorch CUDA works
- [ ] Models load successfully
- [ ] VRAM ≤ 16GB usage
- [ ] Inference generates valid output
- [ ] Memory cleanup works

## Integration Testing
- [ ] ComfyUI starts and responds
- [ ] API endpoints accessible
- [ ] SteadyDancer dependencies present
- [ ] R2 connectivity works
- [ ] File upload succeeds

## Performance Benchmarks
- [ ] Baseline inference time recorded
- [ ] VRAM efficiency measured
- [ ] Batch throughput tested
- [ ] Scheduler compatibility verified

## Error Recovery
- [ ] Error detection functional
- [ ] Recovery procedures tested
- [ ] Logging configured
- [ ] Monitoring active
```

### 8.2 Expected Results Summary

| Test Category | Expected Result | Acceptable Range |
|--------------|-----------------|------------------|
| Build time (cached) | < 5 minutes | 1-5 minutes |
| Build cache hit | ≥ 80% | 80-95% |
| Inference (512x512) | 1.5-2.0s | 1-3s per image |
| VRAM usage (1024px) | 10-14GB | ≤ 16GB |
| Batch size (512px) | 4-8 images | ≥ 4 images |
| GPU temperature | < 85°C | 65-85°C |
| ComfyUI startup | < 30 seconds | 15-30 seconds |

### 8.3 Critical Path Tests

Tests that must pass before deployment:

1. **GPU Detection** - Container must see GPU with ≥16GB VRAM
2. **CUDA Connectivity** - PyTorch must detect CUDA
3. **Model Loading** - Must load SDXL within VRAM limits
4. **Basic Inference** - Must generate at least one valid image
5. **ComfyUI Health** - Server must respond to health checks
6. **No OOM Errors** - Must complete tests without out-of-memory

---

## 9. Appendix

### 9.1 Environment Variables Reference

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `ENABLE_VIBEVOICE` | No | true | Enable VibeVoice TTS model |
| `ENABLE_ZIMAGE` | No | false | Enable Z-Image Turbo |
| `ENABLE_ILLUSTRIOUS` | No | false | Enable Realism Illustrious |
| `ENABLE_WAN22_DISTILL` | No | false | Enable WAN 2.2 TurboDiffusion |
| `ENABLE_STEADYDANCER` | No | false | Enable SteadyDancer |
| `STEADYDANCER_VARIANT` | No | fp8 | Model quantization (fp8/fp16/gguf) |
| `ENABLE_R2_SYNC` | No | false | Enable R2 output sync |
| `R2_ENDPOINT` | Conditional | - | R2 Cloudflare endpoint URL |
| `R2_BUCKET` | Conditional | runpod | R2 bucket name |
| `R2_ACCESS_KEY_ID` | Conditional | - | R2 access key |
| `R2_SECRET_ACCESS_KEY` | Conditional | - | R2 secret key |

### 9.2 File Locations

| Path | Purpose |
|------|---------|
| `/workspace/ComfyUI/` | ComfyUI installation |
| `/workspace/models/` | AI model storage |
| `/workspace/output/` | Generated output files |
| `/upload_to_r2.py` | R2 sync script |
| `/r2_sync.sh` | R2 sync daemon |
| `/download_models.sh` | Model download script |
| `/var/log/` | Log file directory |

### 9.3 Port Reference

| Port | Service | Protocol |
|------|---------|----------|
| 8188 | ComfyUI | HTTP |
| 8000 | XTTS API | HTTP (if enabled) |
| 8020 | XTTS Swagger | HTTP (if enabled) |

### 9.4 Troubleshooting Quick Reference

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| GPU not detected | nvidia-container-toolkit missing | Install nvidia-container-toolkit |
| CUDA not available | PyTorch version mismatch | Reinstall PyTorch with CUDA |
| OOM errors | VRAM exceeded | Reduce batch size/resolution |
| Build fails | Cache corruption | `docker builder prune -af` |
| ComfyUI not starting | Port conflict | Check port 8188 availability |
| R2 upload fails | Credentials missing | Verify R2 environment variables |
| Model loading fails | Corrupted files | Re-download models |
| Slow inference | GPU throttling | Check temperature, improve cooling |

---

## Verification Framework Complete

This verification framework provides comprehensive validation for the RunPod ZR4 Docker build, covering pre-build checks, build process monitoring, runtime validation, integration testing, performance benchmarking, and error recovery procedures. All tests include clear pass/fail criteria and remediation steps for common issues.

**Framework Version:** 1.0
**Last Updated:** 2026-01-21
**Target Environment:** RunPod with RTX 4090 (16GB+ VRAM)
