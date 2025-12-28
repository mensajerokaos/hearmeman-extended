# PHASE 2: Tier 1 Model Download Scripts

This document outlines the download script sections for Tier 1 models (Consumer GPUs 8-24GB) to be integrated into the `download_models.sh` script. These sections follow the established patterns for conditional enablement, progress echoes, and file existence checks.

---

## 1. Qwen-Image-Edit-2511 (~10-15GB)

- **HuggingFace:** `Qwen/Qwen-Image-Edit-2511`
- **CLIP model:** `qwen_2.5_vl_7b_fp8_scaled.safetensors`
- **Description:** For instruction-based image editing

```bash
# ============================================ 
# Qwen-Image-Edit-2511
# ============================================ 
if [ "${ENABLE_QWEN_IMAGE_EDIT:-false}" = "true" ]; then
    echo "[Qwen-Image-Edit] Downloading model components..."

    # CLIP model
    hf_download "Qwen/Qwen-Image-Edit-2511" \
        "qwen_2.5_vl_7b_fp8_scaled.safetensors" \
        "$MODELS_DIR/qwen_image_edit/qwen_2.5_vl_7b_fp8_scaled.safetensors"
fi
```

---

## 2. Genfocus (~12GB)

- **HuggingFace:** `nycu-cplab/Genfocus-Model`
- **Files:** `bokehNet.safetensors`, `deblurNet.safetensors`, `depth_pro.pt`
- **Description:** For depth-of-field refocusing

```bash
# ============================================ 
# Genfocus
# ============================================ 
if [ "${ENABLE_GENFOCUS:-false}" = "true" ]; then
    echo "[Genfocus] Downloading model components..."

    # bokehNet
    hf_download "nycu-cplab/Genfocus-Model" \
        "bokehNet.safetensors" \
        "$MODELS_DIR/genfocus/bokehNet.safetensors"

    # deblurNet
    hf_download "nycu-cplab/Genfocus-Model" \
        "deblurNet.safetensors" \
        "$MODELS_DIR/genfocus/deblurNet.safetensors"

    # depth_pro
    hf_download "nycu-cplab/Genfocus-Model" \
        "depth_pro.pt" \
        "$MODELS_DIR/genfocus/depth_pro.pt"
fi
```

---

## 3. MVInverse (~8GB)

- **GitHub:** `Maddog241/mvinverse`
- **Description:** For multi-view inverse rendering
- **Note:** Checkpoint is typically obtained via `inference.py --ckpt` after cloning.

```bash
# ============================================ 
# MVInverse
# ============================================ 
if [ "${ENABLE_MVINVERSE:-false}" = "true" ]; then
    echo "[MVInverse] Cloning repository..."
    MVINVERSE_DIR="$MODELS_DIR/mvinverse"
    if [ ! -d "$MVINVERSE_DIR" ]; then
        git clone https://github.com/Maddog241/mvinverse "$MVINVERSE_DIR"
        echo "  [Note] MVInverse repository cloned. Checkpoints are typically downloaded via inference.py --ckpt within the repository."
    else
        echo "  [Skip] MVInverse repository already exists."
    fi
fi
```
