# Hearmeman Extended Template - Codebase Analysis

## Overview

This document analyzes the patterns used in the hearmeman-extended RunPod template for adding new AI models. The template follows consistent conventions for environment variables, Dockerfile layers, model downloads, and directory structure.

---

## 1. Environment Variable Naming Conventions

### ENABLE_* Pattern (Boolean Toggles)

Feature flags use `ENABLE_<FEATURE>` naming with `true`/`false` string values:

```bash
# Pattern: ENABLE_<FEATURE>={true|false}
ENABLE_VIBEVOICE=true      # Default: true
ENABLE_ZIMAGE=false        # Default: false
ENABLE_ILLUSTRIOUS=false   # Default: false
ENABLE_CONTROLNET=true     # Default: true
ENABLE_XTTS=false          # Default: false
ENABLE_STEADYDANCER=false  # Default: false
ENABLE_SCAIL=false         # Default: false
ENABLE_VACE=false          # Default: false
ENABLE_FUN_INP=false       # Default: false
ENABLE_I2V=false           # Default: false
ENABLE_CIVITAI=false       # Default: false

# Sub-features (nested toggles)
ENABLE_ILLUSTRIOUS_EMBEDDINGS=true  # Only checked when ENABLE_ILLUSTRIOUS=true
```

### *_MODEL Pattern (Model Variant Selection)

Model variant selectors use `<FEATURE>_MODEL` naming:

```bash
# Pattern: <FEATURE>_MODEL=<variant>
VIBEVOICE_MODEL=Large      # Options: "1.5B", "Large", "Large-Q8"
```

### Resolution-Based Toggles

Some features use resolution-specific toggles instead of generic enable:

```bash
WAN_720P=false             # T2V 14B model (~25GB)
WAN_480P=false             # T2V 1.3B model (~12GB)
```

### List-Based Configuration

Multiple items use comma-separated lists:

```bash
CONTROLNET_MODELS=canny,depth,openpose    # Comma-separated model names
CIVITAI_LORAS=123456,789012               # Comma-separated version IDs
ILLUSTRIOUS_LORAS=123456,789012           # Comma-separated version IDs
```

### API Keys & Credentials

```bash
CIVITAI_API_KEY=your_key_here
PUBLIC_KEY=your_ssh_public_key
JUPYTER_PASSWORD=your_password
```

### System Configuration

```bash
STORAGE_MODE=auto          # Options: auto, ephemeral, persistent
COMFYUI_PORT=8188          # Default port
UPDATE_NODES_ON_START=false
```

---

## 2. Dockerfile Layer Patterns

### Layer Structure

The Dockerfile uses 5 clearly-marked layers:

```dockerfile
# ============================================
# Layer N: Description
# ============================================
```

| Layer | Purpose | Caching Notes |
|-------|---------|---------------|
| 1 | System Dependencies | Rarely changes |
| 2 | ComfyUI Base | Changes on ComfyUI updates |
| 3 | Custom Nodes | Most frequently modified |
| 4 | Additional Dependencies | Changes with new nodes |
| 5 | Scripts and Configuration | Changes per deployment |

### Custom Node Installation Pattern

**Standard Pattern** (with requirements.txt):

```dockerfile
WORKDIR /workspace/ComfyUI/custom_nodes

# NodeName (description)
RUN git clone --depth 1 https://github.com/<org>/<repo>.git && \
    cd <repo> && \
    pip install --no-cache-dir -r requirements.txt || true
```

**Minimal Pattern** (no requirements):

```dockerfile
# ComfyUI-SCAIL-Pose
RUN git clone --depth 1 https://github.com/kijai/ComfyUI-SCAIL-Pose.git
```

**Custom Dependencies Pattern** (specific packages):

```dockerfile
# ComfyUI-XTTS (Coqui XTTS v2)
RUN git clone --depth 1 https://github.com/AIFSH/ComfyUI-XTTS.git && \
    cd ComfyUI-XTTS && \
    pip install --no-cache-dir TTS pydub srt audiotsm || true
```

### Key Conventions

1. **Always use `--depth 1`** - Shallow clones reduce image size
2. **Use `|| true`** - Prevent build failures from optional dependencies
3. **Use `--no-cache-dir`** - Reduce layer size by not caching pip downloads
4. **Add comments** - Document purpose and any compatibility notes

### Standalone Pip Installs

For tools without ComfyUI nodes:

```dockerfile
# CivitAI integration
RUN pip install --no-cache-dir civitai-downloader
```

### Additional Dependencies Layer

Shared dependencies across multiple nodes:

```dockerfile
WORKDIR /workspace
RUN pip install --no-cache-dir \
    huggingface_hub \
    accelerate \
    safetensors \
    sentencepiece \
    protobuf
```

---

## 3. download_models.sh Patterns

### Helper Functions

#### hf_download() - Single File Downloads

```bash
hf_download() {
    local REPO="$1"      # e.g., "Tongyi-MAI/Z-Image-Turbo"
    local FILE="$2"      # e.g., "qwen_3_4b.safetensors"
    local DEST="$3"      # e.g., "$MODELS_DIR/text_encoders/qwen_3_4b.safetensors"
    download_model "https://huggingface.co/${REPO}/resolve/main/${FILE}" "$DEST"
}

# Usage examples:
hf_download "Tongyi-MAI/Z-Image-Turbo" "qwen_3_4b.safetensors" "$MODELS_DIR/text_encoders/qwen_3_4b.safetensors"
hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
    "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
    "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
```

#### snapshot_download - Full Repository Clones

For models requiring multiple files (configs, tokenizers, etc.):

```bash
python -c "
from huggingface_hub import snapshot_download
snapshot_download('microsoft/VibeVoice-1.5B',
    local_dir='$MODELS_DIR/vibevoice/VibeVoice-1.5B',
    local_dir_use_symlinks=False)
" 2>&1 || echo "  [Note] Will download on first use"
```

#### civitai_download() - CivitAI Assets

```bash
civitai_download() {
    local VERSION_ID="$1"        # CivitAI version ID (NOT model ID)
    local TARGET_DIR="$2"        # Directory to save to
    local DESCRIPTION="${3:-CivitAI asset}"  # Optional description
    # Uses wget with --content-disposition for proper filename
}

# Usage:
civitai_download "2091367" "$MODELS_DIR/checkpoints" "Realism Illustrious checkpoint (6.46GB)"
```

#### Git LFS Clone - Large Repos

For repositories requiring Git LFS:

```bash
cd "$MODELS_DIR/diffusion_models"
if [ ! -d "SCAIL-Preview" ]; then
    GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/zai-org/SCAIL-Preview
    cd SCAIL-Preview
    git lfs pull
fi
```

### Conditional Download Block Structure

**Simple Feature Toggle**:

```bash
if [ "${ENABLE_FEATURE:-false}" = "true" ]; then
    echo "[Feature] Downloading components..."
    hf_download "org/repo" "file.safetensors" "$MODELS_DIR/subdir/file.safetensors"
fi
```

**Model Variant Selection (case statement)**:

```bash
if [ "${ENABLE_VIBEVOICE:-true}" = "true" ]; then
    echo "[VibeVoice] Downloading model: ${VIBEVOICE_MODEL:-Large}"

    case "${VIBEVOICE_MODEL:-Large}" in
        "1.5B")
            python -c "snapshot_download('microsoft/VibeVoice-1.5B', ...)"
            ;;
        "Large")
            python -c "snapshot_download('AIFSH/VibeVoice-Large', ...)"
            ;;
        "Large-Q8")
            python -c "snapshot_download('FabioSarracino/VibeVoice-Large-Q8', ...)"
            ;;
    esac
fi
```

**Multi-Model Selection (list iteration)**:

```bash
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
            # ... more cases
        esac
    done
fi
```

**Shared Model Optimization**:

```bash
# Skip download if already present from another feature
if [ ! -f "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" ]; then
    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
        "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
        "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
fi
```

**Nested Feature Dependencies**:

```bash
if [ "${WAN_720P:-false}" = "true" ]; then
    # Base downloads...

    # Nested conditional
    if [ "${ENABLE_I2V:-false}" = "true" ]; then
        hf_download "..." "wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" "..."
    fi
fi
```

### Section Comment Pattern

```bash
# ============================================
# Feature Name
# ============================================
```

---

## 4. Model Directory Conventions

### Standard ComfyUI Model Directories

```
/workspace/ComfyUI/models/
├── checkpoints/          # Full model checkpoints (SDXL, SD1.5, etc.)
├── diffusion_models/     # Diffusion UNet weights (WAN, VACE, etc.)
├── text_encoders/        # T5, CLIP, Qwen text encoders
├── vae/                  # VAE models
├── controlnet/           # ControlNet weights
├── loras/                # LoRA adapters
├── clip_vision/          # CLIP vision encoders for I2V
├── embeddings/           # Textual inversion embeddings
└── vibevoice/            # VibeVoice TTS models (custom)
```

### Directory Creation in Dockerfile

```dockerfile
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision}
```

### Directory References in download_models.sh

```bash
MODELS_DIR="/workspace/ComfyUI/models"

# Use subdirectories consistently:
$MODELS_DIR/checkpoints/
$MODELS_DIR/diffusion_models/
$MODELS_DIR/text_encoders/
$MODELS_DIR/vae/
$MODELS_DIR/controlnet/
$MODELS_DIR/loras/
$MODELS_DIR/clip_vision/
$MODELS_DIR/embeddings/
$MODELS_DIR/vibevoice/   # Custom for TTS
```

### Model File Naming Conventions

| Type | Naming Pattern | Examples |
|------|----------------|----------|
| Diffusion | `<model>_<variant>_<precision>.safetensors` | `wan2.1_t2v_14B_fp8_e4m3fn.safetensors` |
| Text Encoder | `<encoder>_<size>_<precision>.safetensors` | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` |
| VAE | `<model>_vae.safetensors` or `ae.safetensors` | `wan_2.1_vae.safetensors` |
| ControlNet | `control_<version>_<type>_<precision>.safetensors` | `control_v11p_sd15_canny_fp16.safetensors` |
| Checkpoint | `<name>_<version>_<precision>.safetensors` | `realismIllustriousByStableYogi_v50FP16.safetensors` |

---

## 5. Python Dependency Patterns

### In Dockerfile (Layer 3 - Custom Nodes)

**With requirements.txt**:
```dockerfile
RUN git clone --depth 1 https://github.com/<org>/<repo>.git && \
    cd <repo> && \
    pip install --no-cache-dir -r requirements.txt || true
```

**Specific packages**:
```dockerfile
RUN git clone --depth 1 https://github.com/AIFSH/ComfyUI-XTTS.git && \
    cd ComfyUI-XTTS && \
    pip install --no-cache-dir TTS pydub srt audiotsm || true
```

### In Dockerfile (Layer 4 - Shared Dependencies)

```dockerfile
RUN pip install --no-cache-dir \
    huggingface_hub \
    accelerate \
    safetensors \
    sentencepiece \
    protobuf
```

### Version Conflict Documentation

When dependencies conflict, document in Dockerfile:

```dockerfile
# NOTE: XTTS API Server runs in separate container (docker compose --profile xtts)
# Cannot bundle due to transformers version conflict:
# - xtts-api-server requires transformers==4.36.2
# - ComfyUI/VibeVoice requires transformers>=4.51.3 (for Qwen2Tokenizer)
```

### Critical Dependencies from CLAUDE.md

```
bitsandbytes>=0.48.1  # Critical for VibeVoice Q8 model
transformers>=4.51.3  # Required for Qwen2Tokenizer
accelerate
peft
librosa
soundfile
```

---

## 6. Startup Flow (start.sh)

### Execution Order

1. **Storage Mode Detection** - Detects ephemeral vs persistent storage
2. **SSH Setup** - Configures SSH if `PUBLIC_KEY` provided
3. **JupyterLab Setup** - Starts Jupyter if `JUPYTER_PASSWORD` provided
4. **Custom Node Updates** - Updates nodes if `UPDATE_NODES_ON_START=true`
5. **Model Downloads** - Runs `/download_models.sh`
6. **ComfyUI Start** - Starts ComfyUI server

### Key Pattern

```bash
# Download models before starting ComfyUI
echo "[Models] Starting model downloads..."
/download_models.sh

# Start ComfyUI with exec (replaces shell)
exec python main.py \
    --listen 0.0.0.0 \
    --port ${COMFYUI_PORT:-8188} \
    --enable-cors-header \
    --preview-method auto
```

---

## 7. Adding a New Model - Checklist

Based on the analyzed patterns, here's the checklist for adding a new model:

### 1. Define Environment Variables

```bash
# In docker-compose.yml and documentation:
ENABLE_NEWMODEL=false           # Feature toggle (default false for new models)
NEWMODEL_VARIANT=default        # Optional variant selector
```

### 2. Add Custom Node (if needed)

```dockerfile
# In Dockerfile Layer 3:
# NewModel-ComfyUI (description)
RUN git clone --depth 1 https://github.com/<org>/NewModel-ComfyUI.git && \
    cd NewModel-ComfyUI && \
    pip install --no-cache-dir -r requirements.txt || true
```

### 3. Create Model Directory (if non-standard)

```dockerfile
# In Dockerfile Layer 5:
RUN mkdir -p /workspace/ComfyUI/models/{...,newmodel}
```

### 4. Add Download Block

```bash
# In download_models.sh:
# ============================================
# NewModel
# ============================================
if [ "${ENABLE_NEWMODEL:-false}" = "true" ]; then
    echo "[NewModel] Downloading model..."
    hf_download "org/repo" "model.safetensors" "$MODELS_DIR/subdir/model.safetensors"
fi
```

### 5. Update docker-compose.yml

```yaml
environment:
  - ENABLE_NEWMODEL=false
```

### 6. Update CLAUDE.md

Document in the appropriate sections:
- Storage requirements table
- Environment variables section
- Any compatibility notes

---

## 8. Pattern Summary Table

| Component | Pattern | Example |
|-----------|---------|---------|
| Enable toggle | `ENABLE_<FEATURE>` | `ENABLE_VIBEVOICE=true` |
| Model variant | `<FEATURE>_MODEL` | `VIBEVOICE_MODEL=Large` |
| Default value | `${VAR:-default}` | `${ENABLE_VIBEVOICE:-true}` |
| Node install | `git clone + pip install` | See Layer 3 |
| Single file DL | `hf_download repo file dest` | See examples above |
| Full repo DL | `snapshot_download()` | See VibeVoice example |
| CivitAI DL | `civitai_download id dir desc` | See Illustrious example |
| Model dir | `$MODELS_DIR/<type>/` | `/workspace/ComfyUI/models/diffusion_models/` |
| Section marker | `# ====... <Name> ====...` | See all sections |
