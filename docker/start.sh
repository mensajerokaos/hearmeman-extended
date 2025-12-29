#!/bin/bash
set -e

echo "============================================"
echo "=== Hearmeman Extended Template Startup ==="
echo "============================================"
echo "Timestamp: $(date)"
echo ""

# ============================================
# Storage Mode Detection
# ============================================
detect_storage_mode() {
    if [ "$STORAGE_MODE" = "ephemeral" ]; then
        echo "ephemeral"
    elif [ "$STORAGE_MODE" = "persistent" ]; then
        echo "persistent"
    elif [ "$STORAGE_MODE" = "auto" ] || [ -z "$STORAGE_MODE" ]; then
        if [ -d "/workspace" ] && mountpoint -q "/workspace" 2>/dev/null; then
            echo "persistent"
        else
            echo "ephemeral"
        fi
    else
        echo "ephemeral"
    fi
}

DETECTED_STORAGE=$(detect_storage_mode)
export STORAGE_MODE="$DETECTED_STORAGE"
echo "[Storage] Mode: $STORAGE_MODE"

# ============================================
# GPU VRAM Detection & Configuration
# ============================================
detect_gpu_config() {
    # Detect GPU VRAM in MB
    GPU_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -n 1)

    if [ -z "$GPU_VRAM" ]; then
        echo "  [Warning] Could not detect GPU VRAM, using defaults"
        GPU_VRAM=0
    fi

    echo "[GPU] Detected VRAM: ${GPU_VRAM} MB"

    # Auto-detect GPU tier if not set
    if [ -z "$GPU_TIER" ] || [ "$GPU_TIER" = "auto" ]; then
        if (( GPU_VRAM >= 48000 )); then
            export GPU_TIER="datacenter"
        elif (( GPU_VRAM >= 20000 )); then
            export GPU_TIER="prosumer"
        else
            export GPU_TIER="consumer"
        fi
        echo "[GPU] Auto-detected tier: $GPU_TIER"
    else
        echo "[GPU] Configured tier: $GPU_TIER"
    fi

    # Auto-detect memory mode if set to "auto"
    if [ "$GPU_MEMORY_MODE" = "auto" ]; then
        if (( GPU_VRAM >= 48000 )); then
            export GPU_MEMORY_MODE="full"
        elif (( GPU_VRAM >= 24000 )); then
            export GPU_MEMORY_MODE="model_cpu_offload"
        else
            export GPU_MEMORY_MODE="sequential_cpu_offload"
        fi
        echo "[GPU] Auto-detected memory mode: $GPU_MEMORY_MODE"
    fi

    # Auto-detect ComfyUI VRAM flags if not set
    if [ -z "$COMFYUI_ARGS" ]; then
        if (( GPU_VRAM < 8000 )); then
            export COMFYUI_ARGS="--lowvram --cpu-vae --force-fp16"
        elif (( GPU_VRAM < 12000 )); then
            export COMFYUI_ARGS="--lowvram --force-fp16"
        elif (( GPU_VRAM < 16000 )); then
            export COMFYUI_ARGS="--medvram --cpu-text-encoder --force-fp16"
        elif (( GPU_VRAM < 24000 )); then
            export COMFYUI_ARGS="--normalvram --force-fp16"
        else
            export COMFYUI_ARGS=""
        fi

        if [ -n "$COMFYUI_ARGS" ]; then
            echo "[GPU] Auto-detected ComfyUI args: $COMFYUI_ARGS"
        fi
    fi
}

detect_gpu_config

# ============================================
# SSH Setup
# ============================================
if [[ -n "$PUBLIC_KEY" ]]; then
    echo "[SSH] Configuring SSH access..."
    mkdir -p ~/.ssh && chmod 700 ~/.ssh
    echo "$PUBLIC_KEY" >> ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    service ssh start
    echo "[SSH] Ready on port 22"
fi

# ============================================
# JupyterLab Setup
# ============================================
if [[ -n "$JUPYTER_PASSWORD" ]]; then
    echo "[Jupyter] Starting JupyterLab on port 8888..."
    nohup jupyter lab \
        --allow-root \
        --no-browser \
        --port=8888 \
        --ip=0.0.0.0 \
        --ServerApp.token="$JUPYTER_PASSWORD" \
        --ServerApp.allow_origin='*' \
        > /var/log/jupyter.log 2>&1 &
fi

# ============================================
# Update Custom Nodes (if enabled)
# ============================================
if [ "${UPDATE_NODES_ON_START:-false}" = "true" ]; then
    echo "[Nodes] Updating custom nodes..."
    for dir in /workspace/ComfyUI/custom_nodes/*/; do
        if [ -d "$dir/.git" ]; then
            echo "  Updating: $(basename $dir)"
            cd "$dir" && git pull --quiet || true
        fi
    done
fi

# ============================================
# Download Models
# ============================================
echo "[Models] Starting model downloads..."
/download_models.sh

# ============================================
# R2 Sync Daemon Setup
# ============================================
if [ "${ENABLE_R2_SYNC:-false}" = "true" ]; then
    echo "[R2 Sync] Starting background sync daemon..."
    # Ensure output directory exists before watching
    mkdir -p /workspace/ComfyUI/output
    nohup /r2_sync.sh > /var/log/r2_sync_init.log 2>&1 &
    echo "[R2 Sync] Daemon active, monitoring /workspace/ComfyUI/output"
fi

# ============================================
# Start ComfyUI
# ============================================
echo "[ComfyUI] Starting on port ${COMFYUI_PORT:-8188}..."
if [ -n "$COMFYUI_ARGS" ]; then
    echo "[ComfyUI] Using VRAM args: $COMFYUI_ARGS"
fi
cd /workspace/ComfyUI
exec python main.py \
    --listen 0.0.0.0 \
    --port ${COMFYUI_PORT:-8188} \
    --enable-cors-header \
    --preview-method auto \
    $COMFYUI_ARGS
