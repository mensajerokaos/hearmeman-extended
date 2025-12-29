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
echo "[Models] Download complete"
