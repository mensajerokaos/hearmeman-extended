#!/bin/bash
# Model download script with resume support

# ============================================
# Helper Functions
# ============================================

# Helper function for downloads
download_model() {
    local URL="$1"
    local DEST="$2"
    local NAME=$(basename "$DEST")

    if [ -f "$DEST" ]; then
        echo "  [Skip] $NAME already exists"
        return 0
    fi

    echo "  [Download] $NAME"
    mkdir -p "$(dirname "$DEST")"
    wget -c -q --show-progress -O "$DEST" "$URL" || {
        echo "  [Error] Failed to download $NAME"
        rm -f "$DEST"
        return 1
    }
}

# HuggingFace download helper
hf_download() {
    local REPO="$1"
    local FILE="$2"
    local DEST="$3"
    download_model "https://huggingface.co/${REPO}/resolve/main/${FILE}" "$DEST"
}

# CivitAI download helper
civitai_download() {
    local VERSION_ID="$1"
    local TARGET_DIR="$2"
    local DESCRIPTION="${3:-CivitAI asset}"

    mkdir -p "$TARGET_DIR"

    echo "  [Download] $DESCRIPTION (version: $VERSION_ID)"
    if [ -n "$CIVITAI_API_KEY" ]; then
        wget -c -q --show-progress \
            "https://civitai.com/api/download/models/${VERSION_ID}?token=${CIVITAI_API_KEY}" \
            --content-disposition \
            -P "$TARGET_DIR" || echo "  [Error] Failed: $VERSION_ID"
    else
        wget -c -q --show-progress \
            "https://civitai.com/api/download/models/${VERSION_ID}" \
            --content-disposition \
            -P "$TARGET_DIR" || echo "  [Error] Failed (may need API key): $VERSION_ID"
    fi
}

MODELS_DIR="/workspace/ComfyUI/models"

# ============================================
# VibeVoice Models
# ============================================
if [ "${ENABLE_VIBEVOICE:-true}" = "true" ]; then
    echo "[VibeVoice] Downloading model: ${VIBEVOICE_MODEL:-Large}"

    case "${VIBEVOICE_MODEL:-Large}" in
        "1.5B")
            python -c "
from huggingface_hub import snapshot_download
snapshot_download('microsoft/VibeVoice-1.5B',
    local_dir='$MODELS_DIR/vibevoice/VibeVoice-1.5B',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] Will download on first use"
            ;;
        "Large")
            python -c "
from huggingface_hub import snapshot_download
snapshot_download('AIFSH/VibeVoice-Large',
    local_dir='$MODELS_DIR/vibevoice/VibeVoice-Large',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] Will download on first use"
            ;;
        "Large-Q8")
            python -c "
from huggingface_hub import snapshot_download
snapshot_download('FabioSarracino/VibeVoice-Large-Q8',
    local_dir='$MODELS_DIR/vibevoice/VibeVoice-Large-Q8',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] Will download on first use"
            ;;
    esac
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
    echo "[WAN] Downloading WAN 2.2 720p models..."
    # Text encoders (shared)
    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
        "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
        "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"

    # CLIP Vision for I2V
    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
        "split_files/clip_vision/clip_vision_h.safetensors" \
        "$MODELS_DIR/clip_vision/clip_vision_h.safetensors"

    # VAE
    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
        "split_files/vae/wan_2.1_vae.safetensors" \
        "$MODELS_DIR/vae/wan_2.1_vae.safetensors"

    # 720p diffusion model (T2V)
    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
        "split_files/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" \
        "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors"

    # 720p I2V model (if I2V enabled)
    if [ "${ENABLE_I2V:-false}" = "true" ]; then
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" \
            "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors"
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
# SteadyDancer
# ============================================
if [ "${ENABLE_STEADYDANCER:-false}" = "true" ]; then
    echo "[SteadyDancer] Downloading model..."
    hf_download "MCG-NJU/SteadyDancer-14B" "Wan21_SteadyDancer_fp16.safetensors" "$MODELS_DIR/diffusion_models/Wan21_SteadyDancer_fp16.safetensors"
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

echo "[Models] Download complete"
