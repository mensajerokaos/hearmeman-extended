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
# Start ComfyUI
# ============================================
echo "[ComfyUI] Starting on port ${COMFYUI_PORT:-8188}..."
cd /workspace/ComfyUI
exec python main.py \
    --listen 0.0.0.0 \
    --port ${COMFYUI_PORT:-8188} \
    --enable-cors-header \
    --preview-method auto
