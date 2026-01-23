#!/bin/bash
# Model download script with resume support
set -o pipefail

# ============================================
# Configuration
# ============================================
LOG_FILE="/var/log/download_models.log"
DRY_RUN="${DRY_RUN:-false}"
DOWNLOAD_TIMEOUT="${DOWNLOAD_TIMEOUT:-1800}"  # 30 min default

# Logging setup
mkdir -p "$(dirname "$LOG_FILE")"
exec > >(tee -a "$LOG_FILE") 2>&1

echo ""
echo "============================================"
echo "[$(date -Iseconds)] Model download started"
echo "  DRY_RUN=$DRY_RUN"
echo "  TIMEOUT=${DOWNLOAD_TIMEOUT}s"
echo "============================================"

# ============================================
# Helper Functions
# ============================================

# Helper function for downloads
download_model() {
    local URL="$1"
    local DEST="$2"
    local EXPECTED_SIZE="${3:-}"  # Optional expected size for display
    local NAME=$(basename "$DEST")

    if [ -f "$DEST" ]; then
        local SIZE=$(stat -c%s "$DEST" 2>/dev/null || echo "0")
        if [ "$SIZE" -gt 1000000 ]; then  # >1MB means likely complete
            echo "  [Skip] $NAME already exists ($(numfmt --to=iec $SIZE 2>/dev/null || echo ${SIZE}B))"
            return 0
        fi
        echo "  [Resume] $NAME incomplete ($(numfmt --to=iec $SIZE 2>/dev/null || echo 0B)), resuming..."
    fi

    # Dry run mode - just show what would be downloaded
    if [ "$DRY_RUN" = "true" ]; then
        echo "  [DRY-RUN] Would download: $NAME ${EXPECTED_SIZE:+($EXPECTED_SIZE)}"
        return 0
    fi

    echo "  [Download] $NAME ${EXPECTED_SIZE:+($EXPECTED_SIZE)} from ${URL%%\?*}"
    mkdir -p "$(dirname "$DEST")"

    # Use wget with timeout and progress bar - with HF_TOKEN support
    local WGET_EXIT=0
    if [ -n "$HF_TOKEN" ]; then
        # Use eval to properly handle the header with spaces
        timeout "$DOWNLOAD_TIMEOUT" wget -c --progress=bar:force:noscroll \
            --header="Authorization: Bearer $HF_TOKEN" \
            -O "$DEST" "$URL" 2>&1 || WGET_EXIT=$?
    else
        timeout "$DOWNLOAD_TIMEOUT" wget -c --progress=bar:force:noscroll \
            -O "$DEST" "$URL" 2>&1 || WGET_EXIT=$?
    fi

    if [ $WGET_EXIT -ne 0 ]; then
        echo "  [Warn] wget failed (exit $WGET_EXIT), trying curl..."
        local CURL_EXIT=0
        if [ -n "$HF_TOKEN" ]; then
            timeout "$DOWNLOAD_TIMEOUT" curl -L -C - \
                -H "Authorization: Bearer $HF_TOKEN" \
                --progress-bar -o "$DEST" "$URL" 2>&1 || CURL_EXIT=$?
        else
            timeout "$DOWNLOAD_TIMEOUT" curl -L -C - \
                --progress-bar -o "$DEST" "$URL" 2>&1 || CURL_EXIT=$?
        fi
        if [ $CURL_EXIT -ne 0 ]; then
            # Check for gated model error
            if grep -q "401\|Unauthorized\|gated\|authentication\|Invalid username" "$DEST" 2>/dev/null; then
                echo "  [ERROR] $NAME - Model requires authentication!"
                echo "  [ERROR] This is a gated model on HuggingFace."
                echo "  [ERROR] Solution: Set HF_TOKEN environment variable or accept license at:"
                echo "  [ERROR]   https://huggingface.co/${REPO:-the-model-repo}"
                rm -f "$DEST"
            else
                echo "  [ERROR] Failed to download $NAME after wget and curl attempts"
                rm -f "$DEST"
            fi
            return 1
        fi
    fi

    # Verify download
    if [ -f "$DEST" ]; then
        local FINAL_SIZE=$(stat -c%s "$DEST" 2>/dev/null || echo "0")
        echo "  [OK] $NAME downloaded ($(numfmt --to=iec $FINAL_SIZE 2>/dev/null || echo ${FINAL_SIZE}B))"
    else
        echo "  [ERROR] $NAME not found after download"
        return 1
    fi
}

# HuggingFace download helper
hf_download() {
    local REPO="$1"
    local FILE="$2"
    local DEST="$3"
    local EXPECTED_SIZE="${4:-}"  # Optional size hint
    download_model "https://huggingface.co/${REPO}/resolve/main/${FILE}" "$DEST" "$EXPECTED_SIZE"
}

# CivitAI download helper
civitai_download() {
    local VERSION_ID="$1"
    local TARGET_DIR="$2"
    local DESCRIPTION="${3:-CivitAI asset}"

    mkdir -p "$TARGET_DIR"

    echo "  [Download] $DESCRIPTION (version: $VERSION_ID)"

    # Build URL
    local URL="https://civitai.com/api/download/models/${VERSION_ID}"
    if [ -n "$CIVITAI_API_KEY" ]; then
        URL="${URL}?token=${CIVITAI_API_KEY}"
    fi

    # Try wget with explicit redirect handling first
    if wget --version >/dev/null 2>&1; then
        wget -c -q --show-progress \
            --max-redirect=10 \
            --content-disposition \
            -P "$TARGET_DIR" \
            "$URL" 2>/dev/null && return 0
    fi

    # Fallback to curl if wget fails
    echo "  [Info] Retrying with curl..."
    local FILENAME=$(curl -sI -L "$URL" 2>/dev/null | grep -i "content-disposition" | sed -n 's/.*filename="\?\([^"]*\)"\?.*/\1/p' | tr -d '\r')
    if [ -z "$FILENAME" ]; then
        FILENAME="model_${VERSION_ID}.safetensors"
    fi

    curl -L -C - -o "$TARGET_DIR/$FILENAME" "$URL" || {
        echo "  [Error] Failed: $VERSION_ID"
        return 1
    }
}

MODELS_DIR="${MODELS_DIR:-/workspace/ComfyUI/models}"

# Python download helper with logging
hf_snapshot_download() {
    local REPO="$1"
    local DEST="$2"
    local NAME=$(basename "$DEST")

    if [ -d "$DEST" ] && [ "$(ls -A "$DEST" 2>/dev/null)" ]; then
        echo "  [Skip] $NAME already exists"
        return 0
    fi

    echo "  [Download] $NAME from $REPO..."
    mkdir -p "$DEST"

    python3 -c "
import sys
from huggingface_hub import snapshot_download
try:
    snapshot_download('$REPO',
        local_dir='$DEST',
        local_dir_use_symlinks=False)
    print('  [OK] $NAME downloaded successfully')
except Exception as e:
    print(f'  [Error] Failed to download $NAME: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1

    return $?
}

# ============================================
# VibeVoice Models
# ============================================
if [ "${ENABLE_VIBEVOICE:-false}" = "true" ]; then
    echo ""
    echo "[VibeVoice] Downloading model: ${VIBEVOICE_MODEL:-Large}"

    case "${VIBEVOICE_MODEL:-Large}" in
        "1.5B")
            hf_snapshot_download "microsoft/VibeVoice-1.5B" "$MODELS_DIR/vibevoice/VibeVoice-1.5B"
            ;;
        "Large")
            hf_snapshot_download "aoi-ot/VibeVoice-Large" "$MODELS_DIR/vibevoice/VibeVoice-Large"
            ;;
        "Large-Q8")
            hf_snapshot_download "FabioSarracino/VibeVoice-Large-Q8" "$MODELS_DIR/vibevoice/VibeVoice-Large-Q8"
            ;;
    esac

    # Download Qwen tokenizer (required for VibeVoice)
    TOKENIZER_DIR="$MODELS_DIR/vibevoice/tokenizer"
    if [ ! -f "$TOKENIZER_DIR/tokenizer.json" ]; then
        echo "[VibeVoice] Downloading Qwen tokenizer..."
        mkdir -p "$TOKENIZER_DIR"
        wget -q -O "$TOKENIZER_DIR/tokenizer_config.json" \
            "https://huggingface.co/Qwen/Qwen2.5-1.5B/resolve/main/tokenizer_config.json" && \
        wget -q -O "$TOKENIZER_DIR/vocab.json" \
            "https://huggingface.co/Qwen/Qwen2.5-1.5B/resolve/main/vocab.json" && \
        wget -q -O "$TOKENIZER_DIR/merges.txt" \
            "https://huggingface.co/Qwen/Qwen2.5-1.5B/resolve/main/merges.txt" && \
        wget -q -O "$TOKENIZER_DIR/tokenizer.json" \
            "https://huggingface.co/Qwen/Qwen2.5-1.5B/resolve/main/tokenizer.json" && \
        echo "  [OK] Qwen tokenizer downloaded" || \
        echo "  [Error] Failed to download Qwen tokenizer"
    else
        echo "  [Skip] Qwen tokenizer already exists"
    fi

    echo "[VibeVoice] Download complete"
fi

# ============================================
# Z-Image Turbo
# ============================================
if [ "${ENABLE_ZIMAGE:-false}" = "true" ]; then
    echo "[Z-Image] Downloading components..."
    hf_download "Tongyi-MAI/Z-Image-Turbo" "qwen_3_4b.safetensors" "$MODELS_DIR/text_encoders/qwen_3_4b.safetensors"
    hf_download "Tongyi-MAI/Z-Image-Turbo" "z_image_turbo_bf16.safetensors" "$MODELS_DIR/diffusion_models/z_image_turbo_bf16.safetensors"
    hf_download "Tongyi-MAI/Z-Image-Turbo" "ae.safetensors" "$MODELS_DIR/vae/ae.safetensors"
fi

# ============================================
# WAN 2.2 Video Generation Models
# ============================================
if [ "${WAN_720P:-false}" = "true" ]; then
    echo ""
    echo "[WAN] Downloading WAN 2.1 720p models (~25GB total)..."
    echo "  Text encoder (9.5GB) + CLIP vision (1.4GB) + VAE (335MB) + 14B diffusion (14GB)"
    # Text encoders (shared)
    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
        "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
        "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
        "9.5GB"

    # CLIP Vision for I2V
    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
        "split_files/clip_vision/clip_vision_h.safetensors" \
        "$MODELS_DIR/clip_vision/clip_vision_h.safetensors" \
        "1.4GB"

    # VAE
    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
        "split_files/vae/wan_2.1_vae.safetensors" \
        "$MODELS_DIR/vae/wan_2.1_vae.safetensors" \
        "335MB"

    # 720p diffusion model (T2V)
    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
        "split_files/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" \
        "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" \
        "14GB"

    # 720p I2V model (if I2V enabled)
    if [ "${ENABLE_I2V:-false}" = "true" ]; then
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" \
            "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" \
            "14GB"
    fi
fi

if [ "${WAN_480P:-false}" = "true" ]; then
    echo "[WAN] Downloading WAN 2.2 480p models (~12GB)..."
    # Text encoders (shared - skip if already downloaded)
    if [ ! -f "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" ]; then
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
            "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
    fi

    # VAE (shared)
    if [ ! -f "$MODELS_DIR/vae/wan_2.1_vae.safetensors" ]; then
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/vae/wan_2.1_vae.safetensors" \
            "$MODELS_DIR/vae/wan_2.1_vae.safetensors"
    fi

    # 480p diffusion model (T2V) - smaller, fits 16GB VRAM
    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
        "split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors" \
        "$MODELS_DIR/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors"
fi

# ============================================
# WAN 2.2 Distilled Models (TurboDiffusion I2V)
# High/Low noise expert models for 4-step inference
# VRAM: ~24GB | Size: ~28GB total
# ============================================
if [ "${ENABLE_WAN22_DISTILL:-false}" = "true" ]; then
    echo ""
    echo "[WAN 2.2] Downloading distilled models for TurboDiffusion I2V..."
    echo "  High noise (14GB) + Low noise (14GB) + shared deps = ~28GB total"

    # Text encoder (shared - skip if already exists)
    if [ ! -f "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" ]; then
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
            "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
            "9.5GB"
    else
        echo "  [Skip] Text encoder already exists"
    fi

    # VAE (shared - skip if already exists)
    if [ ! -f "$MODELS_DIR/vae/wan_2.1_vae.safetensors" ]; then
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/vae/wan_2.1_vae.safetensors" \
            "$MODELS_DIR/vae/wan_2.1_vae.safetensors" \
            "335MB"
    else
        echo "  [Skip] VAE already exists"
    fi

    # WAN 2.2 High Noise Expert (I2V) - ~14GB FP8
    hf_download "Comfy-Org/Wan_2.2_ComfyUI_Repackaged" \
        "split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors" \
        "$MODELS_DIR/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors" \
        "14GB"

    # WAN 2.2 Low Noise Expert (I2V) - ~14GB FP8
    hf_download "Comfy-Org/Wan_2.2_ComfyUI_Repackaged" \
        "split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors" \
        "$MODELS_DIR/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors" \
        "14GB"

    # CLIP Vision for I2V (required)
    if [ ! -f "$MODELS_DIR/clip_vision/clip_vision_h.safetensors" ]; then
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/clip_vision/clip_vision_h.safetensors" \
            "$MODELS_DIR/clip_vision/clip_vision_h.safetensors" \
            "1.4GB"
    else
        echo "  [Skip] CLIP vision already exists"
    fi

    echo "[WAN 2.2] Distilled models download complete"
fi

# ============================================
# SteadyDancer (Human Image Animation)
# VRAM: 14-28GB | Size: 14-28GB
# Note: Using smthem/SteadyDancer-14B-diffusers-gguf-dit which has consolidated model files
# ============================================
if [ "${ENABLE_STEADYDANCER:-false}" = "true" ]; then
    echo ""
    echo "[SteadyDancer] Downloading model (~28GB)..."

    STEADYDANCER_VARIANT="${STEADYDANCER_VARIANT:-bf16}"

    case "$STEADYDANCER_VARIANT" in
        "bf16")
            echo "  [Info] Downloading bf16 variant (~28GB) from smthem/SteadyDancer-14B-diffusers-gguf-dit..."
            hf_download "smthem/SteadyDancer-14B-diffusers-gguf-dit" \
                "SteadyDancer-14B-Bf16.safetensors" \
                "$MODELS_DIR/diffusion_models/Wan21_SteadyDancer_fp8.safetensors" \
                "28GB"
            ;;
        "gguf")
            echo "  [Info] Downloading GGUF variant (~8GB)..."
            mkdir -p "$MODELS_DIR/steadydancer"
            python3 -c "
from huggingface_hub import hf_hub_download
import os

GGUF_FILE='SteadyDancer_wan-14B-Q6_K.gguf'
hf_hub_download(
    repo_id='smthem/SteadyDancer-14B-diffusers-gguf-dit',
    filename=GGUF_FILE,
    local_dir='$MODELS_DIR/steadydancer',
    local_dir_use_symlinks=False
)
print('  [OK] GGUF model downloaded')
" 2>&1 || echo "  [Error] GGUF download failed"
            ;;
        *)
            echo "  [Info] Downloading default variant..."
            hf_download "smthem/SteadyDancer-14B-diffusers-gguf-dit" \
                "SteadyDancer-14B-Bf16.safetensors" \
                "$MODELS_DIR/diffusion_models/Wan21_SteadyDancer_fp8.safetensors" \
                "28GB"
            ;;
    esac

    # Download shared dependencies (WAN 2.1)
    echo "  [Info] Ensuring shared dependencies..."

    # Text encoder (9.5GB - skip if exists)
    if [ ! -f "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" ]; then
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
            "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
            "9.5GB"
    fi

    # CLIP Vision (1.4GB - skip if exists)
    if [ ! -f "$MODELS_DIR/clip_vision/clip_vision_h.safetensors" ]; then
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/clip_vision/clip_vision_h.safetensors" \
            "$MODELS_DIR/clip_vision/clip_vision_h.safetensors" \
            "1.4GB"
    fi

    # VAE (335MB - skip if exists)
    if [ ! -f "$MODELS_DIR/vae/wan_2.1_vae.safetensors" ]; then
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/vae/wan_2.1_vae.safetensors" \
            "$MODELS_DIR/vae/wan_2.1_vae.safetensors" \
            "335MB"
    fi

    echo "[SteadyDancer] Download complete"
fi

# ============================================
# DWPose (Pose Estimation for Dance Video)
# VRAM: ~2GB | Size: ~2GB
# Required for dance video generation
# ============================================
if [ "${ENABLE_DWPOSE:-false}" = "true" ]; then
    echo ""
    echo "[DWPose] Downloading pose estimation model (~2GB)..."

    # DWPose weights (yzd-v/DWPose)
    hf_download "yzd-v/DWPose" \
        "dwpose_v2.pth" \
        "$MODELS_DIR/other/dwpose/dwpose_v2.pth" \
        "2GB"

    # ControlNet pose model
    hf_download "lllyasviel/ControlNet-v1-1" \
        "control_v11p_sd15_openpose.pth" \
        "$MODELS_DIR/controlnet/control_v11p_sd15_openpose.pth" \
        "1.2GB"

    echo "[DWPose] Download complete"
fi

# ============================================
# TurboDiffusion (Distilled Model)
# VRAM: ~14GB | Size: ~14GB
# Enables 100-200x speedup
# ============================================
if [ "${ENABLE_WAN22_DISTILL:-false}" = "true" ]; then
    echo ""
    echo "[TurboDiffusion] Downloading distilled model (~14GB)..."

    hf_download "kijai/wan-2.1-turbodiffusion" \
        "wan_2.1_turbodiffusion.safetensors" \
        "$MODELS_DIR/diffusion_models/wan_2.1_turbodiffusion.safetensors" \
        "14GB"

    echo "[TurboDiffusion] Download complete"
fi

# ============================================
# SCAIL
# ============================================
if [ "${ENABLE_SCAIL:-false}" = "true" ]; then
    echo "[SCAIL] Downloading model..."
    cd "$MODELS_DIR/diffusion_models"
    if [ ! -d "SCAIL-Preview" ]; then
        GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/zai-org/SCAIL-Preview
        cd SCAIL-Preview
        git lfs pull
    fi
fi

# ============================================
# ControlNet Models
# ============================================
if [ "${ENABLE_CONTROLNET:-true}" = "true" ]; then
    echo "[ControlNet] Downloading FP16 models..."

    CONTROLNET_LIST="${CONTROLNET_MODELS:-canny,depth,openpose}"
    IFS=',' read -ra MODELS <<< "$CONTROLNET_LIST"

    for model in "${MODELS[@]}"; do
        model=$(echo "$model" | xargs)  # trim whitespace
        case "$model" in
            "canny")
                hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
                    "control_v11p_sd15_canny_fp16.safetensors" \
                    "$MODELS_DIR/controlnet/control_v11p_sd15_canny_fp16.safetensors"
                ;;
            "depth")
                hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
                    "control_v11f1p_sd15_depth_fp16.safetensors" \
                    "$MODELS_DIR/controlnet/control_v11f1p_sd15_depth_fp16.safetensors"
                ;;
            "openpose")
                hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
                    "control_v11p_sd15_openpose_fp16.safetensors" \
                    "$MODELS_DIR/controlnet/control_v11p_sd15_openpose_fp16.safetensors"
                ;;
            "lineart")
                hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
                    "control_v11p_sd15_lineart_fp16.safetensors" \
                    "$MODELS_DIR/controlnet/control_v11p_sd15_lineart_fp16.safetensors"
                ;;
            "normalbae")
                hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
                    "control_v11p_sd15_normalbae_fp16.safetensors" \
                    "$MODELS_DIR/controlnet/control_v11p_sd15_normalbae_fp16.safetensors"
                ;;
        esac
    done
fi

# ============================================
# XTTS v2
# ============================================
if [ "${ENABLE_XTTS:-false}" = "true" ]; then
    echo "[XTTS] Downloading XTTS v2 model..."
    python -c "
from TTS.api import TTS
# This downloads the model on first init
tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=False)
print('XTTS v2 model downloaded successfully')
" 2>&1 || echo "  [Note] XTTS will download on first use"
fi

# ============================================
# CLIP Vision for I2V (Image-to-Video)
# ============================================
if [ "${ENABLE_I2V:-false}" = "true" ]; then
    echo "[I2V] Downloading CLIP Vision model..."
    mkdir -p "$MODELS_DIR/clip_vision"
    hf_download "Comfy-Org/sigclip_vision_384" \
        "sigclip_vision_patch14_384.safetensors" \
        "$MODELS_DIR/clip_vision/sigclip_vision_patch14_384.safetensors"
fi

# ============================================
# WAN VACE (Video All-in-One Creation and Editing)
# ============================================
if [ "${ENABLE_VACE:-false}" = "true" ]; then
    echo "[VACE] Downloading WAN VACE 14B model..."
    hf_download "Wan-AI/Wan2.1-VACE-14B" \
        "wan2.1_vace_14B_fp16.safetensors" \
        "$MODELS_DIR/diffusion_models/wan2.1_vace_14B_fp16.safetensors"
fi

# ============================================
# WAN Fun InP (First-Last Frame Interpolation)
# ============================================
if [ "${ENABLE_FUN_INP:-false}" = "true" ]; then
    echo "[Fun InP] Downloading WAN Fun InP 14B model..."
    hf_download "Wan-AI/Wan2.2-Fun-InP-14B" \
        "wan2.2_fun_inp_14B_fp16.safetensors" \
        "$MODELS_DIR/diffusion_models/wan2.2_fun_inp_14B_fp16.safetensors"
fi

# ============================================
# Realism Illustrious (SDXL-based photorealism)
# ============================================
if [ "${ENABLE_ILLUSTRIOUS:-false}" = "true" ]; then
    echo ""
    echo "[Illustrious] Downloading Realism Illustrious v5.0 FP16..."

    # Checkpoint (6.46GB)
    CHECKPOINT_FILE="$MODELS_DIR/checkpoints/realismIllustriousByStableYogi_v50FP16.safetensors"
    if [ ! -f "$CHECKPOINT_FILE" ]; then
        civitai_download "2091367" "$MODELS_DIR/checkpoints" "Realism Illustrious checkpoint (6.46GB)"
    else
        echo "  [Skip] Checkpoint already exists"
    fi

    # Embeddings (optional but recommended)
    if [ "${ENABLE_ILLUSTRIOUS_EMBEDDINGS:-true}" = "true" ]; then
        echo "[Illustrious] Downloading embeddings..."

        # Positive Embedding (352KB)
        POSITIVE_EMB="$MODELS_DIR/embeddings/Stable_Yogis_Illustrious_Positives.safetensors"
        if [ ! -f "$POSITIVE_EMB" ]; then
            civitai_download "1153237" "$MODELS_DIR/embeddings" "Positive Embedding"
        fi

        # Negative Embedding (536KB)
        NEGATIVE_EMB="$MODELS_DIR/embeddings/Stable_Yogis_Illustrious_Negatives.safetensors"
        if [ ! -f "$NEGATIVE_EMB" ]; then
            civitai_download "1153212" "$MODELS_DIR/embeddings" "Negative Embedding"
        fi
    fi

    echo "[Illustrious] Download complete"
fi

# ============================================
# Illustrious LoRAs (optional)
# ============================================
if [ "${ENABLE_ILLUSTRIOUS:-false}" = "true" ] && [ -n "$ILLUSTRIOUS_LORAS" ]; then
    echo ""
    echo "[Illustrious] Downloading Illustrious-compatible LoRAs..."

    IFS=',' read -ra LORA_IDS <<< "$ILLUSTRIOUS_LORAS"
    for version_id in "${LORA_IDS[@]}"; do
        version_id=$(echo "$version_id" | xargs)  # trim whitespace
        civitai_download "$version_id" "$MODELS_DIR/loras" "LoRA"
    done
fi

# ============================================
# CivitAI LoRAs
# ============================================
if [ "${ENABLE_CIVITAI:-false}" = "true" ] && [ -n "$CIVITAI_LORAS" ]; then
    echo "[CivitAI] Downloading LoRAs..."

    # Store API key if provided
    if [ -n "$CIVITAI_API_KEY" ]; then
        echo "$CIVITAI_API_KEY" > /workspace/.civitai-token
        chmod 600 /workspace/.civitai-token
    fi

    IFS=',' read -ra LORA_IDS <<< "$CIVITAI_LORAS"
    for version_id in "${LORA_IDS[@]}"; do
        version_id=$(echo "$version_id" | xargs)  # trim whitespace
        civitai_download "$version_id" "$MODELS_DIR/loras" "CivitAI LoRA"
    done
fi

# ============================================
# TIER 1: Consumer GPU Models (8-24GB VRAM)
# ============================================

# ============================================
# Qwen-Image-Edit-2511 (Instruction-based Image Editing)
# GGUF quantized versions from unsloth for consumer GPUs
# Full version for datacenter GPUs
# ============================================
if [ "${ENABLE_QWEN_EDIT:-false}" = "true" ]; then
    echo ""
    QWEN_MODEL="${QWEN_EDIT_MODEL:-Q4_K_M}"

    case "$QWEN_MODEL" in
        "full")
            echo "[Qwen-Edit] Downloading FULL model (54GB - datacenter only)..."
            python -c "
from huggingface_hub import snapshot_download
snapshot_download('Qwen/Qwen-Image-Edit-2511',
    local_dir='$MODELS_DIR/qwen/Qwen-Image-Edit-2511',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] Qwen-Edit will download on first use"
            ;;
        "Q4_K_M"|"Q5_K_M"|"Q6_K"|"Q8_0"|"Q2_K"|"Q3_K_M")
            echo "[Qwen-Edit] Downloading GGUF ${QWEN_MODEL} quantized version..."
            GGUF_FILE="qwen-image-edit-2511-${QWEN_MODEL}.gguf"
            GGUF_DEST="$MODELS_DIR/qwen/${GGUF_FILE}"

            if [ ! -f "$GGUF_DEST" ]; then
                mkdir -p "$MODELS_DIR/qwen"
                echo "  [Download] ${GGUF_FILE} from unsloth/Qwen-Image-Edit-2511-GGUF"
                python -c "
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id='unsloth/Qwen-Image-Edit-2511-GGUF',
    filename='${GGUF_FILE}',
    local_dir='$MODELS_DIR/qwen',
    local_dir_use_symlinks=False
)
" 2>&1 || echo "  [Error] Failed to download GGUF model"
            else
                echo "  [Skip] ${GGUF_FILE} already exists"
            fi
            ;;
        *)
            echo "[Qwen-Edit] Unknown model type: $QWEN_MODEL"
            echo "  Valid options: Q4_K_M, Q5_K_M, Q6_K, Q8_0, Q2_K, Q3_K_M, full"
            ;;
    esac

    echo "[Qwen-Edit] Download complete"
fi

# ============================================
# Genfocus (Depth-of-Field Refocusing)
# VRAM: ~12GB | Size: ~12GB
# ============================================
if [ "${ENABLE_GENFOCUS:-false}" = "true" ]; then
    echo ""
    echo "[Genfocus] Downloading model components..."

    hf_download "nycu-cplab/Genfocus-Model" \
        "bokehNet.safetensors" \
        "$MODELS_DIR/genfocus/bokehNet.safetensors"

    hf_download "nycu-cplab/Genfocus-Model" \
        "deblurNet.safetensors" \
        "$MODELS_DIR/genfocus/deblurNet.safetensors"

    hf_download "nycu-cplab/Genfocus-Model" \
        "checkpoints/depth_pro.pt" \
        "$MODELS_DIR/genfocus/depth_pro.pt"

    echo "[Genfocus] Download complete"
fi

# ============================================
# MVInverse (Multi-view Inverse Rendering)
# VRAM: ~8GB | Size: ~8GB
# ============================================
if [ "${ENABLE_MVINVERSE:-false}" = "true" ]; then
    echo ""
    echo "[MVInverse] Cloning repository and downloading checkpoints..."

    MVINVERSE_DIR="$MODELS_DIR/mvinverse"
    if [ ! -d "$MVINVERSE_DIR/mvinverse" ]; then
        git clone --depth 1 https://github.com/Maddog241/mvinverse.git "$MVINVERSE_DIR/mvinverse" || \
            echo "  [Error] Failed to clone MVInverse repo"
        echo "  [Note] Checkpoints auto-download on first inference via --ckpt flag"
    else
        echo "  [Skip] MVInverse repository already exists"
    fi

    echo "[MVInverse] Setup complete"
fi

# ============================================
# TIER 2: Prosumer GPU Models (24GB+ with CPU offload)
# ============================================

# ============================================
# FlashPortrait (Portrait Animation)
# VRAM: 60GB (full) | 30GB (model_cpu_offload) | 10GB (sequential_cpu_offload)
# RAM: 32GB minimum for CPU offload modes
# Size: ~60GB
# ============================================
if [ "${ENABLE_FLASHPORTRAIT:-false}" = "true" ]; then
    echo ""
    echo "[FlashPortrait] Downloading models..."

    case "${GPU_MEMORY_MODE:-auto}" in
        "full"|"model_full_load")
            echo "  [FlashPortrait] Full model load mode (60GB VRAM required)"
            ;;
        "sequential_cpu_offload")
            echo "  [FlashPortrait] Sequential CPU offload mode (10GB VRAM + 32GB+ RAM)"
            ;;
        "model_cpu_offload")
            echo "  [FlashPortrait] Model CPU offload mode (30GB VRAM)"
            ;;
        "auto")
            echo "  [FlashPortrait] Auto mode - will detect VRAM at startup"
            ;;
    esac

    # FlashPortrait main checkpoint
    python -c "
from huggingface_hub import snapshot_download
snapshot_download('FrancisRing/FlashPortrait',
    local_dir='$MODELS_DIR/flashportrait/FlashPortrait',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] FlashPortrait will download on first use"

    # Wan2.1 I2V 14B 720P (required dependency) - check if already exists
    if [ ! -f "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" ]; then
        echo "  [FlashPortrait] Downloading Wan2.1 I2V 720p dependency..."
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" \
            "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors"
    fi

    echo "[FlashPortrait] Download complete"
fi

# ============================================
# StoryMem (Multi-Shot Video Storytelling)
# Based on Wan2.2, uses LoRA variants (MI2V, MM2V)
# VRAM: ~20-24GB (base models + LoRA)
# Size: ~20GB (LoRAs) + Wan2.1 base models
# ============================================
if [ "${ENABLE_STORYMEM:-false}" = "true" ]; then
    echo ""
    echo "[StoryMem] Downloading models and dependencies..."

    # Ensure Wan2.1 T2V base model
    if [ ! -f "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" ]; then
        echo "  [StoryMem] Downloading Wan2.1 T2V 14B base model..."
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" \
            "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors"
    fi

    # Ensure Wan2.1 I2V base model
    if [ ! -f "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" ]; then
        echo "  [StoryMem] Downloading Wan2.1 I2V 720p 14B base model..."
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" \
            "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors"
    fi

    # Ensure text encoder
    if [ ! -f "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" ]; then
        echo "  [StoryMem] Downloading UMT5-XXL text encoder..."
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
            "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
    fi

    # Ensure VAE
    if [ ! -f "$MODELS_DIR/vae/wan_2.1_vae.safetensors" ]; then
        echo "  [StoryMem] Downloading WAN VAE..."
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/vae/wan_2.1_vae.safetensors" \
            "$MODELS_DIR/vae/wan_2.1_vae.safetensors"
    fi

    # StoryMem LoRA variants
    echo "  [StoryMem] Downloading StoryMem LoRA variants..."
    python -c "
from huggingface_hub import snapshot_download
snapshot_download('Kevin-thu/StoryMem',
    local_dir='$MODELS_DIR/storymem/StoryMem',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] StoryMem LoRAs will download on first use"

    echo "[StoryMem] Download complete"
fi

# ============================================
# TIER 3: Datacenter GPU Models (48-80GB VRAM)
# ============================================

# ============================================
# InfCam (Camera-Controlled Video Generation)
# WARNING: EXPERIMENTAL - DATACENTER TIER ONLY
# VRAM: 50GB+ inference, 52-56GB/GPU training
# Requires: A100 80GB or H100 80GB
# Size: ~50GB+
# ============================================
if [ "${ENABLE_INFCAM:-false}" = "true" ]; then
    if [ "${GPU_TIER}" = "datacenter" ]; then
        echo ""
        echo "[InfCam] EXPERIMENTAL - Downloading for datacenter tier..."
        echo "  [Warning] Requires A100 80GB or H100 80GB GPU"

        # InfCam main checkpoint
        python -c "
from huggingface_hub import snapshot_download
snapshot_download('emjay73/InfCam',
    local_dir='$MODELS_DIR/infcam/InfCam',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] InfCam will download on first use"

        # UniDepth-v2-vitl14 (required dependency)
        python -c "
from huggingface_hub import snapshot_download
snapshot_download('lpiccinelli/unidepth-v2-vitl14',
    local_dir='$MODELS_DIR/infcam/unidepth-v2-vitl14',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] UniDepth will download on first use"

        # Wan2.1 base model for InfCam
        if [ ! -f "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" ]; then
            echo "  [InfCam] Downloading Wan2.1 T2V base model..."
            hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
                "split_files/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" \
                "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors"
        fi

        echo "[InfCam] Download complete"
    else
        echo ""
        echo "[InfCam] Skipped - GPU_TIER must be 'datacenter' (current: ${GPU_TIER:-consumer})"
        echo "  [Info] InfCam requires 50GB+ VRAM (A100/H100)"
    fi
fi

echo ""
echo "============================================"
echo "[$(date -Iseconds)] Model download complete"
echo "============================================"
echo ""
echo "Downloaded models summary:"
ls -lh "$MODELS_DIR"/*/  2>/dev/null | grep -E "\.safetensors|\.pt|\.ckpt|\.bin" | head -20 || echo "  No models found"
echo ""
