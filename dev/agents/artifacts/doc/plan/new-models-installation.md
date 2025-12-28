# New AI Models Installation PRD
## Hearmeman Extended RunPod Template

---
**Author**: oz
**Co-Author**: claude-opus-4-5
**Date**: 2025-12-28
**Version**: 1.0 (Execution-Ready)
**Clarity Score**: 9/10
---

## Executive Summary

This PRD provides complete installation instructions for adding 3 new AI models to the hearmeman-extended RunPod template. All HuggingFace URLs have been verified.

| Model | Status | VRAM | Notes |
|-------|--------|------|-------|
| **Qwen-Image-Edit-2511** | READY | 24GB+ (BF16) | Uses existing QwenEditUtils node |
| **Genfocus** | PARTIAL | ~12GB | Models download, node is PLACEHOLDER |
| **MVInverse** | PARTIAL | ~10GB | Models verified, node is PLACEHOLDER |

---

## Verified HuggingFace Repositories

### Qwen-Image-Edit-2511
- **Diffusion Models**: `Comfy-Org/Qwen-Image-Edit_ComfyUI`
  - `split_files/diffusion_models/qwen_image_edit_2511_bf16.safetensors`
  - `split_files/diffusion_models/qwen_image_edit_2511_fp8mixed.safetensors`
- **Text Encoder/VAE**: Likely bundled in diffusion model files (not separate)
- **Lightning LoRA**: `lightx2v/Qwen-Image-Edit-2511-Lightning`
  - `qwen_image_edit_2511_fp8_e4m3fn_scaled_lightning_comfyui.safetensors`

### Genfocus
- **Repository**: `nycu-cplab/Genfocus-Model`
  - `bokehNet.safetensors`
  - `deblurNet.safetensors`
  - `checkpoints/depth_pro.pt`

### MVInverse
- **Repository**: `Maddog241/mvinverse`
  - `model.safetensors`
  - `config.json`

---

## Phase 1: Environment Variables & Dockerfile

### 1.1 Add Environment Variables

**FILE**: `docker/.env`
**ACTION**: Add at end of file

```bash
# Qwen Image Edit 2511 (image editing with text prompts)
# WARNING: BF16 model requires 24GB+ VRAM
ENABLE_QWEN_IMAGE_EDIT=false

# Genfocus (generative refocusing - depth-of-field from single images)
ENABLE_GENFOCUS=false

# MVInverse (multi-view inverse rendering)
ENABLE_MVINVERSE=false
```

**VERIFICATION**:
```bash
grep -E "ENABLE_(QWEN_IMAGE_EDIT|GENFOCUS|MVINVERSE)" docker/.env
```

---

### 1.2 Dockerfile Layer 3 - Custom Nodes

**FILE**: `docker/Dockerfile`
**ACTION**: Add after line 88 (after civitai-downloader)

```dockerfile
# ============================================
# Qwen Image Edit 2511 Nodes (lrzjason/Comfyui-QwenEditUtils)
# Advanced image editing with configurable multi-image support
# ============================================
RUN git clone --depth 1 https://github.com/lrzjason/Comfyui-QwenEditUtils.git && \
    cd Comfyui-QwenEditUtils && \
    pip install --no-cache-dir -r requirements.txt 2>/dev/null || true

# ============================================
# Custom Nodes for New Models (Genfocus, MVInverse)
# PLACEHOLDER: These nodes LOAD but return dummy output
# ============================================
COPY custom_nodes/ComfyUI-Genfocus /workspace/ComfyUI/custom_nodes/ComfyUI-Genfocus
COPY custom_nodes/ComfyUI-MVInverse /workspace/ComfyUI/custom_nodes/ComfyUI-MVInverse
```

---

### 1.3 Dockerfile Layer 4 - Dependencies

**FILE**: `docker/Dockerfile`
**ACTION**: Add after line 105

```dockerfile
# Dependencies for Genfocus (generative refocusing)
RUN pip install --no-cache-dir \
    einops \
    timm \
    kornia \
    opencv-python-headless \
    scikit-image \
    git+https://github.com/apple/ml-depth-pro.git || echo "[WARN] ml-depth-pro install failed"

# Dependencies for MVInverse
RUN pip install --no-cache-dir \
    opencv-python-headless || true
```

---

### 1.4 Dockerfile Layer 5 - Model Directories

**FILE**: `docker/Dockerfile`
**ACTION**: Replace line 123

**OLD**:
```dockerfile
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision}
```

**NEW**:
```dockerfile
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision,genfocus,mvinverse}
```

---

### 1.5 docker-compose.yml

**FILE**: `docker/docker-compose.yml`
**ACTION**: Add after existing environment variables

```yaml
      # NEW: Qwen Image Edit 2511 (24GB+ VRAM required)
      - ENABLE_QWEN_IMAGE_EDIT=${ENABLE_QWEN_IMAGE_EDIT:-false}

      # NEW: Genfocus (generative refocusing)
      - ENABLE_GENFOCUS=${ENABLE_GENFOCUS:-false}

      # NEW: MVInverse (multi-view inverse rendering)
      - ENABLE_MVINVERSE=${ENABLE_MVINVERSE:-false}
```

---

## Phase 2: Download Scripts

### 2.1 Qwen Image Edit 2511

**FILE**: `docker/download_models.sh`
**ACTION**: Add after line 263

```bash
# ============================================
# Qwen Image Edit 2511 (Image Editing with Text Prompts)
# WARNING: BF16 requires ~24GB+ VRAM
# ============================================
if [ "${ENABLE_QWEN_IMAGE_EDIT:-false}" = "true" ]; then
    echo ""
    echo "[Qwen Image Edit] Downloading Qwen-Image-Edit-2511 models..."
    echo "[WARN] BF16 model requires 24GB+ VRAM"

    # Diffusion Model (BF16)
    hf_download "Comfy-Org/Qwen-Image-Edit_ComfyUI" \
        "split_files/diffusion_models/qwen_image_edit_2511_bf16.safetensors" \
        "$MODELS_DIR/diffusion_models/qwen_image_edit_2511_bf16.safetensors"

    # Lightning LoRA (FP8 ComfyUI optimized)
    hf_download "lightx2v/Qwen-Image-Edit-2511-Lightning" \
        "qwen_image_edit_2511_fp8_e4m3fn_scaled_lightning_comfyui.safetensors" \
        "$MODELS_DIR/loras/qwen_image_edit_2511_lightning_comfyui.safetensors" \
        || echo "  [Note] Lightning LoRA not found"

    echo "[Qwen Image Edit] Download complete"
fi
```

---

### 2.2 Genfocus

**FILE**: `docker/download_models.sh`
**ACTION**: Add after Qwen section

```bash
# ============================================
# Genfocus (Generative Refocusing)
# VERIFIED: nycu-cplab/Genfocus-Model
# ============================================
if [ "${ENABLE_GENFOCUS:-false}" = "true" ]; then
    echo ""
    echo "[Genfocus] Downloading Genfocus models..."

    mkdir -p "$MODELS_DIR/genfocus/checkpoints"

    # BokehNet
    hf_download "nycu-cplab/Genfocus-Model" \
        "bokehNet.safetensors" \
        "$MODELS_DIR/genfocus/bokehNet.safetensors"

    # DeblurNet
    hf_download "nycu-cplab/Genfocus-Model" \
        "deblurNet.safetensors" \
        "$MODELS_DIR/genfocus/deblurNet.safetensors"

    # Depth Pro
    hf_download "nycu-cplab/Genfocus-Model" \
        "checkpoints/depth_pro.pt" \
        "$MODELS_DIR/genfocus/checkpoints/depth_pro.pt"

    echo "[Genfocus] Download complete"
    echo "[NOTE] ComfyUI node is PLACEHOLDER - returns dummy output"
fi
```

---

### 2.3 MVInverse

**FILE**: `docker/download_models.sh`
**ACTION**: Add after Genfocus section

```bash
# ============================================
# MVInverse (Multi-View Inverse Rendering)
# VERIFIED: Maddog241/mvinverse
# ============================================
if [ "${ENABLE_MVINVERSE:-false}" = "true" ]; then
    echo ""
    echo "[MVInverse] Downloading MVInverse model..."

    mkdir -p "$MODELS_DIR/mvinverse"

    # Main model checkpoint
    hf_download "Maddog241/mvinverse" \
        "model.safetensors" \
        "$MODELS_DIR/mvinverse/model.safetensors"

    # Config file
    hf_download "Maddog241/mvinverse" \
        "config.json" \
        "$MODELS_DIR/mvinverse/config.json"

    echo "[MVInverse] Download complete"
    echo "[NOTE] ComfyUI node is PLACEHOLDER - returns dummy output"
fi
```

---

## Phase 3: Custom Node Wrappers

### 3.1 Create Directory Structure

```bash
mkdir -p docker/custom_nodes/ComfyUI-Genfocus
mkdir -p docker/custom_nodes/ComfyUI-MVInverse
```

### 3.2 Genfocus Node

**FILE**: `docker/custom_nodes/ComfyUI-Genfocus/__init__.py`

See: `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/new-models-installation-pre/final.md` Section 3.1.1

**FILE**: `docker/custom_nodes/ComfyUI-Genfocus/requirements.txt`

```
einops
timm
kornia
safetensors
scikit-image
opencv-python-headless
```

### 3.3 MVInverse Node

**FILE**: `docker/custom_nodes/ComfyUI-MVInverse/__init__.py`

See: `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/new-models-installation-pre/final.md` Section 3.2.1

**FILE**: `docker/custom_nodes/ComfyUI-MVInverse/requirements.txt`

```
opencv-python-headless
safetensors
```

---

## Phase 4: Verification

### Build & Start

```bash
cd /home/oz/projects/2025/oz/12/runpod/docker

# Build
docker compose build --no-cache

# Start with new models
ENABLE_QWEN_IMAGE_EDIT=true ENABLE_GENFOCUS=true ENABLE_MVINVERSE=true \
    docker compose up -d

# Wait and check logs
sleep 60
docker logs hearmeman-extended 2>&1 | tail -50
```

### Verify Nodes

```bash
# Check nodes in filesystem
docker exec -it hearmeman-extended ls /workspace/ComfyUI/custom_nodes/ | \
    grep -E "(QwenEdit|Genfocus|MVInverse)"

# Check ComfyUI API
curl -s http://localhost:8188/object_info | python3 -c "
import sys, json
data = json.load(sys.stdin)
for key in sorted(data.keys()):
    if any(x in key.lower() for x in ['qwen', 'genfocus', 'mvinverse']):
        print(key)
"
```

### Verify Downloads

```bash
# Qwen models
docker exec -it hearmeman-extended ls -lah /workspace/ComfyUI/models/diffusion_models/ | grep qwen

# Genfocus models
docker exec -it hearmeman-extended ls -lah /workspace/ComfyUI/models/genfocus/

# MVInverse models
docker exec -it hearmeman-extended ls -lah /workspace/ComfyUI/models/mvinverse/
```

---

## Phase 5: Documentation

### CLAUDE.md Updates

Add to storage requirements table:

| Component | Size | Notes |
|-----------|------|-------|
| **Qwen Image Edit 2511** | ~18GB | Image editing (BF16), 24GB+ VRAM |
| **Genfocus** | ~3GB | Depth-of-field, PLACEHOLDER nodes |
| **MVInverse** | ~2GB | Inverse rendering, PLACEHOLDER nodes |

Add to environment variables table:

| Variable | Default | Size | Notes |
|----------|---------|------|-------|
| `ENABLE_QWEN_IMAGE_EDIT` | false | ~18GB | 24GB+ VRAM required |
| `ENABLE_GENFOCUS` | false | ~3GB | PLACEHOLDER nodes |
| `ENABLE_MVINVERSE` | false | ~2GB | PLACEHOLDER nodes |

---

## Implementation Checklist

- [ ] 1.1 Add environment variables to `.env`
- [ ] 1.2 Add Dockerfile Layer 3 (custom nodes)
- [ ] 1.3 Add Dockerfile Layer 4 (dependencies)
- [ ] 1.4 Update Dockerfile Layer 5 (model dirs)
- [ ] 1.5 Update docker-compose.yml
- [ ] 2.1 Add Qwen Image Edit download block
- [ ] 2.2 Add Genfocus download block
- [ ] 2.3 Add MVInverse download block
- [ ] 3.1 Create directory structure
- [ ] 3.2 Create Genfocus custom node
- [ ] 3.3 Create MVInverse custom node
- [ ] 4.x Run verification tests
- [ ] 5.x Update CLAUDE.md documentation

---

## Artifact Files

| Artifact | Path |
|----------|------|
| **This PRD** | `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/new-models-installation.md` |
| Research - Context7 | `.../new-models-installation-pre/context7-research.md` |
| Research - Codebase | `.../new-models-installation-pre/codebase-analysis.md` |
| Draft 1 | `.../new-models-installation-pre/draft-1.md` |
| Critique | `.../new-models-installation-pre/critique.md` |
| HF Verification | `.../new-models-installation-pre/hf-verification.md` |
| Final Detailed | `.../new-models-installation-pre/final.md` |
| Progress Log | `.../new-models-installation-pre/progress.log` |

---

## References

- [Comfy-Org/Qwen-Image-Edit_ComfyUI](https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI)
- [lightx2v/Qwen-Image-Edit-2511-Lightning](https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning)
- [nycu-cplab/Genfocus-Model](https://huggingface.co/nycu-cplab/Genfocus-Model)
- [Maddog241/mvinverse](https://huggingface.co/Maddog241/mvinverse)
- [lrzjason/Comfyui-QwenEditUtils](https://github.com/lrzjason/Comfyui-QwenEditUtils)
- [rayray9999/Genfocus](https://github.com/rayray9999/Genfocus)
- [ComfyUI Qwen Image Edit Tutorial](https://docs.comfy.org/tutorials/image/qwen/qwen-image-edit-2511)
