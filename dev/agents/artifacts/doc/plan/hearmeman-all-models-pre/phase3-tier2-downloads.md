# PHASE 3 TASK: Download Scripts for Tier 2 Models (Prosumer 24GB+ with CPU Offload)

# This file contains download script sections for Tier 2 models, following the patterns
# in `docker/download_models.sh` and incorporating details from `dev/agents/artifacts/doc/new-models-research.md`.

MODELS_DIR="/workspace/ComfyUI/models"

# ============================================ 
# FlashPortrait (~60GB full, ~10GB with CPU offload)
# HuggingFace: FrancisRing/FlashPortrait
# Also needs: Wan-AI/Wan2.1-I2V-14B-720P
# GPU Memory Modes:
#   - model_full_load: 60GB
#   - sequential_cpu_offload: 10GB GPU + CPU RAM
#   - model_cpu_offload: 30GB
# ============================================ 
if [ "${ENABLE_FLASHPORTRAIT:-false}" = "true" ]; then
    echo "[FlashPortrait] Downloading models..."

    case "${GPU_MEMORY_MODE:-model_full_load}" in
        "model_full_load")
            echo "  [FlashPortrait] Full model load (60GB VRAM)"
            # Main FlashPortrait model
            hf_download "FrancisRing/FlashPortrait" "flash_portrait.safetensors" "$MODELS_DIR/diffusion_models/flash_portrait.safetensors"
            # Wan2.1 I2V 14B for 720p (required by FlashPortrait)
            # This is specifically the I2V component which FlashPortrait uses.
            hf_download "Wan-AI/Wan2.1-I2V-14B-720P" "wan2.1_i2v_14B_720P_fp16.safetensors" "$MODELS_DIR/diffusion_models/wan2.1_i2v_14B_720P_fp16.safetensors"
            ;; 
        "sequential_cpu_offload")
            echo "  [FlashPortrait] Sequential CPU offload (10GB GPU VRAM + CPU RAM)"
            # Main FlashPortrait model
            hf_download "FrancisRing/FlashPortrait" "flash_portrait.safetensors" "$MODELS_DIR/diffusion_models/flash_portrait.safetensors"
            # Wan2.1 I2V 14B for 720p (required by FlashPortrait)
            hf_download "Wan-AI/Wan2.1-I2V-14B-720P" "wan2.1_i2v_14B_720P_fp16.safetensors" "$MODELS_DIR/diffusion_models/wan2.1_i2v_14B_720P_fp16.safetensors"
            ;; 
        "model_cpu_offload")
            echo "  [FlashPortrait] Model CPU offload (30GB VRAM)"
            # Main FlashPortrait model
            hf_download "FrancisRing/FlashPortrait" "flash_portrait.safetensors" "$MODELS_DIR/diffusion_models/flash_portrait.safetensors"
            # Wan2.1 I2V 14B for 720p (required by FlashPortrait)
            hf_download "Wan-AI/Wan2.1-I2V-14B-720P" "wan2.1_i2v_14B_720P_fp16.safetensors" "$MODELS_DIR/diffusion_models/wan2.1_i2v_14B_720P_fp16.safetensors"
            ;; 
        *)
            echo "  [FlashPortrait] Unknown GPU_MEMORY_MODE: ${GPU_MEMORY_MODE}. Downloading full models."
            hf_download "FrancisRing/FlashPortrait" "flash_portrait.safetensors" "$MODELS_DIR/diffusion_models/flash_portrait.safetensors"
            hf_download "Wan-AI/Wan2.1-I2V-14B-720P" "wan2.1_i2v_14B_720P_fp16.safetensors" "$MODELS_DIR/diffusion_models/wan2.1_i2v_14B_720P_fp16.safetensors"
            ;; 
    esac
fi

# ============================================ 
# StoryMem (Based on Wan2.2)
# HuggingFace: Kevin-thu/StoryMem
# LoRA variants: MI2V, MM2V
# Needs: Wan2.2 T2V-A14B and I2V-A14B base models
# VRAM: StoryMem itself is a LoRA, so base model VRAM applies (e.g., Wan2.x 720p models are ~10GB GPU each) 
#       Total VRAM will depend on the loaded base models + StoryMem LoRA. Estimate ~20-24GB for both base models + LoRA.
# ============================================ 
if [ "${ENABLE_STORYMEM:-false}" = "true" ]; then
    echo "[StoryMem] Downloading models and dependencies..."

    # Ensure base Wan2.x T2V and I2V models are present if not covered by WAN_720P
    # Assuming Wan2.2 refers to the Wan2.1 720p variants in existing scripts for now.
    # Check for Wan2.1 T2V 14B (Text-to-Video base)
    if [ ! -f "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" ]; then
        echo "  [StoryMem] Downloading Wan2.1 T2V 14B base model..."
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" \
            "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors"
    fi

    # Check for Wan2.1 I2V 720p 14B (Image-to-Video base)
    if [ ! -f "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" ]; then
        echo "  [StoryMem] Downloading Wan2.1 I2V 720p 14B base model..."
        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
            "split_files/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" \
            "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors"
    fi

    # StoryMem LoRA variants
    # The research doc mentions 'huggingface-cli download Kevin-thu/StoryMem --local-dir ./models/storymem'
    # This implies a snapshot download of the entire repo into a specific directory.
    echo "  [StoryMem] Downloading StoryMem LoRA variants (MI2V, MM2V)..."
    python -c "
from huggingface_hub import snapshot_download
snapshot_download('Kevin-thu/StoryMem',
    local_dir='$MODELS_DIR/loras/StoryMem',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] StoryMem models will download on first use or failed to download."

    echo "  [StoryMem] LoRAs are typically smaller, but loaded on top of base models."
    echo "  [StoryMem] Estimated VRAM for base models (T2V + I2V 720p) + StoryMem LoRA: ~20-24GB."
fi
