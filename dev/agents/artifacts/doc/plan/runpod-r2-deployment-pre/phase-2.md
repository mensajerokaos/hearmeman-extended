# Phase 2: Model Download Updates - Implementation Specification

## Overview
This phase focuses on enhancing the model download capabilities of the RunPod environment by adding support for **TurboDiffusion** models and implementing a **Download Verification** system to ensure file integrity.

---

## Step 2.1: Add TurboDiffusion Model Section

### Objective
Enable automatic downloading of TurboDiffusion acceleration models when `ENABLE_TURBODIFFUSION` is set to `true`. These models provide 100-200x speedup for WAN-based video generation.

### File
`/home/oz/projects/2025/oz/12/runpod/docker/download_models.sh`

### BEFORE
```bash
# ============================================ 
# SteadyDancer
# ============================================ 
if [ "${ENABLE_STEADYDANCER:-false}" = "true" ]; then
    echo "[SteadyDancer] Downloading model..."
    hf_download "MCG-NJU/SteadyDancer-14B" "Wan21_SteadyDancer_fp16.safetensors" "$MODELS_DIR/diffusion_models/Wan21_SteadyDancer_fp16.safetensors"
fi
```

### AFTER
```bash
# ============================================ 
# SteadyDancer
# ============================================ 
if [ "${ENABLE_STEADYDANCER:-false}" = "true" ]; then
    echo "[SteadyDancer] Downloading model..."
    hf_download "MCG-NJU/SteadyDancer-14B" "Wan21_SteadyDancer_fp16.safetensors" "$MODELS_DIR/diffusion_models/Wan21_SteadyDancer_fp16.safetensors"
fi

# ============================================ 
# TurboDiffusion (WAN Video Acceleration)
# ============================================ 
if [ "${ENABLE_TURBODIFFUSION:-false}" = "true" ]; then
    echo "[TurboDiffusion] Downloading acceleration models..."
    # High-noise expert (Quantized)
    hf_download "TurboDiffusion/TurboWan2.2-I2V-A14B-720P" \
        "TurboWan2.2-I2V-A14B-high-720P-quant.pth" \
        "$MODELS_DIR/diffusion_models/TurboWan2.2-I2V-A14B-high-720P-quant.pth"
    
    # Low-noise expert (Quantized)
    hf_download "TurboDiffusion/TurboWan2.2-I2V-A14B-720P" \
        "TurboWan2.2-I2V-A14B-low-720P-quant.pth" \
        "$MODELS_DIR/diffusion_models/TurboWan2.2-I2V-A14B-low-720P-quant.pth"
fi
```

### Verification
```bash
grep "ENABLE_TURBODIFFUSION" docker/download_models.sh
```

---

## Step 2.2: Add Download Verification Function

### Objective
Implement a `verify_download()` function to check that downloaded files meet a minimum size requirement, preventing "completed" downloads that resulted in empty files or HTML error pages.

### File
`/home/oz/projects/2025/oz/12/runpod/docker/download_models.sh`

### BEFORE
```bash
# CivitAI download helper
civitai_download() {
    ...
}

MODELS_DIR="${MODELS_DIR:-\/workspace\/ComfyUI\/models}"
```

### AFTER
```bash
# CivitAI download helper
civitai_download() {
    ...
}

# Verify download integrity by size
verify_download() {
    local FILE="$1"
    local MIN_SIZE_MB="$2"
    local BYTES=$((MIN_SIZE_MB * 1024 * 1024))

    if [ ! -f "$FILE" ]; then
        echo "  [Error] Verification failed: $FILE not found"
        return 1
    fi

    local ACTUAL_SIZE=$(stat -c%s "$FILE")
    if [ "$ACTUAL_SIZE" -lt "$BYTES" ]; then
        echo "  [Error] Verification failed: $FILE size $ACTUAL_SIZE bytes < $BYTES bytes"
        return 1
    fi

    echo "  [OK] $FILE verified ($ACTUAL_SIZE bytes)"
    return 0
}

MODELS_DIR="${MODELS_DIR:-\/workspace\/ComfyUI\/models}"
```

### Application to Critical Models
Apply verification to the primary 14B models which are prone to download failures:

**WAN 2.2 Section Update:**
```bash
    # 720p diffusion model (T2V)
    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
        "split_files/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" \
        "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors"
    verify_download "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" 10000 # ~10GB
```

**TurboDiffusion Section Update:**
```bash
    hf_download "TurboDiffusion/TurboWan2.2-I2V-A14B-720P" \
        "TurboWan2.2-I2V-A14B-high-720P-quant.pth" \
        "$MODELS_DIR/diffusion_models/TurboWan2.2-I2V-A14B-high-720P-quant.pth"
    verify_download "$MODELS_DIR/diffusion_models/TurboWan2.2-I2V-A14B-high-720P-quant.pth" 10000 # ~10GB
```

### Verification
```bash
bash -n docker/download_models.sh
```

---

## Step 2.3: Update Dockerfile ENV

### Objective
Expose the `ENABLE_TURBODIFFUSION` environment variable in the Dockerfile so it can be toggled via RunPod environment variables.

### File
`/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile`

### BEFORE
```dockerfile
# Tier 1: Consumer GPU (8-24GB VRAM)
ENV ENABLE_GENFOCUS="false"
ENV ENABLE_QWEN_EDIT="false"
ENV QWEN_EDIT_MODEL="Q4_K_M"
# Options: Q4_K_M (13GB), Q5_K_M (15GB), Q8_0 (22GB), full (54GB)
ENV ENABLE_MVINVERSE="false"
```

### AFTER
```dockerfile
# Tier 1: Consumer GPU (8-24GB VRAM)
ENV ENABLE_GENFOCUS="false"
ENV ENABLE_QWEN_EDIT="false"
ENV QWEN_EDIT_MODEL="Q4_K_M"
# Options: Q4_K_M (13GB), Q5_K_M (15GB), Q8_0 (22GB), full (54GB)
ENV ENABLE_MVINVERSE="false"
ENV ENABLE_TURBODIFFUSION="false"
```

### Verification
```bash
grep "ENABLE_TURBODIFFUSION" docker/Dockerfile
```
