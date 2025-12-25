---
task: Research - Add Realism Illustrious to Hearmeman Extended Template
agent: hc (headless claude)
model: claude-opus-4-5-20251101
author: oz
timestamp: 2025-12-24T23:30:00Z
status: completed
---

# Realism Illustrious Integration - Research Report

## Executive Summary

This report documents the findings from exploring the existing Hearmeman Extended Template PRD to understand how to integrate Realism Illustrious By Stable Yogi. The research covers:
1. Existing PRD structure and patterns
2. CivitAI download mechanisms
3. Environment variable patterns
4. Model directory structure
5. Embedding storage patterns

---

## 1. Existing PRD Structure

### Location
```
dev/agents/artifacts/doc/plan/hearmeman-extended-template.md
```

### Architecture Pattern

The template follows a **code baked, models on-demand** design:
- Docker image: ~12GB (custom nodes pre-installed)
- Models: Downloaded at runtime based on `ENABLE_*` environment variables
- Storage: Supports ephemeral (450GB container disk) or persistent (/workspace network volume)

### Feature Toggle Pattern

Each model capability has:
1. **ENABLE_[FEATURE]**: Boolean toggle (true/false), defaults typically to false
2. **[FEATURE]_MODEL**: Model variant selector (optional)
3. **Download section**: In `download_models.sh`

### Existing Features

| Feature | Env Var | Default | Download Size |
|---------|---------|---------|---------------|
| VibeVoice | ENABLE_VIBEVOICE | true | ~18GB |
| Z-Image | ENABLE_ZIMAGE | false | ~21GB |
| SteadyDancer | ENABLE_STEADYDANCER | false | ~32GB |
| SCAIL | ENABLE_SCAIL | false | ~28GB |
| ControlNet | ENABLE_CONTROLNET | true | ~3.6GB |
| XTTS | ENABLE_XTTS | false | ~1.8GB |
| TurboDiffusion | ENABLE_TURBODIFFUSION | false | ~500MB |
| CivitAI | ENABLE_CIVITAI | false | varies |
| I2V | ENABLE_I2V | false | ~1.5GB |
| VACE | ENABLE_VACE | false | ~28GB |
| Fun InP | ENABLE_FUN_INP | false | ~28GB |

---

## 2. CivitAI Download Patterns

### Current Implementation

**Location in PRD**: `download_models.sh` lines 556-582

```bash
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
        echo "  [Download] CivitAI model version: $version_id"

        if [ -n "$CIVITAI_API_KEY" ]; then
            wget -c -q --show-progress \
                "https://civitai.com/api/download/models/${version_id}?token=${CIVITAI_API_KEY}" \
                --content-disposition \
                -P "$MODELS_DIR/loras/" || echo "  [Error] Failed: $version_id"
        else
            wget -c -q --show-progress \
                "https://civitai.com/api/download/models/${version_id}" \
                --content-disposition \
                -P "$MODELS_DIR/loras/" || echo "  [Error] Failed (may need API key): $version_id"
        fi
    done
fi
```

### Key Implementation Details

1. **Version IDs**: CivitAI uses `modelVersionId` for downloads, not model IDs
2. **API Token**: Required for NSFW/gated models, optional for public
3. **Content-Disposition**: `wget --content-disposition` preserves original filename
4. **Resume Support**: `-c` flag enables resume on interrupted downloads
5. **Target Directory**: `/workspace/ComfyUI/models/loras/`

### CivitAI Download URL Pattern

```
https://civitai.com/api/download/models/{versionId}?token={apiKey}
```

For **Realism Illustrious v5.0_FP16**:
- Model ID: 974693
- Version ID: **2091367** (from NSFW.md)
- URL: `https://civitai.com/api/download/models/2091367`

### Pre-installed Python Package

```dockerfile
# CivitAI integration
RUN pip install --no-cache-dir civitai-downloader
```

Alternative CLI usage:
```bash
civitai-downloader download --model-version-id 2091367 --output-dir /workspace/ComfyUI/models/checkpoints
```

---

## 3. Environment Variable Patterns

### Naming Conventions

| Pattern | Example | Purpose |
|---------|---------|---------|
| `ENABLE_*` | ENABLE_VIBEVOICE | Boolean feature toggle |
| `*_MODEL` | VIBEVOICE_MODEL | Model variant selector |
| `*_MODELS` | CONTROLNET_MODELS | Comma-separated list |
| `*_API_KEY` | CIVITAI_API_KEY | API authentication |

### Type Definitions

```
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| ENABLE_* | bool | false | true/false string |
| *_MODEL | string | varies | Model variant name |
| *_MODELS | string | varies | Comma-separated list |
```

### Bash Pattern for Boolean Check

```bash
if [ "${ENABLE_FEATURE:-false}" = "true" ]; then
    # Feature enabled
fi
```

### Proposed Environment Variables for Illustrious

```bash
# Feature toggle
ENABLE_ILLUSTRIOUS=false           # Enable Realism Illustrious checkpoint

# Model variant (optional - if multiple versions offered)
ILLUSTRIOUS_MODEL=v5.0_FP16        # Options: v5.0_FP16, v5.0_DMD2, v1.6_Hyper

# Embeddings (optional - bundled by default)
ENABLE_ILLUSTRIOUS_EMBEDDINGS=true # Download positive/negative embeddings
```

---

## 4. Model Directory Structure

### Standard ComfyUI Layout

```
/workspace/ComfyUI/models/
├── checkpoints/          # Main models (.safetensors, .ckpt)
├── clip/                 # CLIP text encoders
├── clip_vision/          # CLIP vision models (for I2V)
├── controlnet/           # ControlNet models
├── diffusion_models/     # Diffusion transformer models (WAN, Z-Image)
├── embeddings/           # Textual inversions / embeddings
├── loras/                # LoRA adapters
├── text_encoders/        # Text encoder models (Qwen, T5, etc.)
├── vae/                  # VAE models
└── vibevoice/            # VibeVoice TTS models (custom)
```

### Model Type Mapping for Illustrious

| File Type | Directory | Notes |
|-----------|-----------|-------|
| Realism Illustrious checkpoint | `checkpoints/` | SDXL-class model (~6.5GB) |
| Positive embedding | `embeddings/` | Realism_Illustrious_Positive_Embedding.safetensors |
| Negative embedding | `embeddings/` | Realism_Illustrious_Negative_Embedding.safetensors |
| Compatible LoRAs | `loras/` | Illustrious-specific LoRAs only |

### Dockerfile Model Directory Creation

```dockerfile
RUN mkdir -p /workspace/ComfyUI/models/{vibevoice,text_encoders,diffusion_models,vae,controlnet,loras}
```

**Note**: `embeddings/` and `checkpoints/` are not explicitly created in current PRD.
Should add:
```dockerfile
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings}
```

---

## 5. Embedding Storage Patterns

### Existing References

From NSFW.md:
```
- Add `Realism_Illustrious_Positive_Embedding` to positive prompt
- Add `Realism_Illustrious_Negative_Embedding` to negative prompt
```

From realism-illustrious-research.md:
```yaml
Embeddings:
  Positive: Realism_Illustrious_Positive_Embedding
  Negative: Realism_Illustrious_Negative_Embedding
```

### Related Embedding Sources

From research:
- **PDXL Positives**: https://civitai.com/models/1331980
- **PDXL Negatives**: https://civitai.com/models/1331758

These work with SDXL/Pony/Illustrious models.

### Embedding Download Pattern

Embeddings are typically small (.pt or .safetensors, ~1-50KB) and can be:
1. Downloaded via CivitAI API (same pattern as LoRAs)
2. Downloaded via direct HuggingFace links
3. Bundled with the checkpoint (rare)

**Proposed approach**: Download embeddings alongside checkpoint if `ENABLE_ILLUSTRIOUS_EMBEDDINGS=true`

---

## 6. Proposed Implementation

### Environment Variables

Add to PRD Section 3 (Environment Variables):

```
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_ILLUSTRIOUS` | bool | false | Download Realism Illustrious checkpoint |
| `ILLUSTRIOUS_MODEL` | string | v5.0_FP16 | Model variant: v5.0_FP16, v5.0_DMD2, v1.6_Hyper |
| `ENABLE_ILLUSTRIOUS_EMBEDDINGS` | bool | true | Download positive/negative embeddings |
```

### Download Script Section

Add to `download_models.sh`:

```bash
# ============================================
# Realism Illustrious (SDXL-based photorealism)
# ============================================
if [ "${ENABLE_ILLUSTRIOUS:-false}" = "true" ]; then
    echo "[Illustrious] Downloading Realism Illustrious checkpoint..."

    # Model variant selection
    case "${ILLUSTRIOUS_MODEL:-v5.0_FP16}" in
        "v5.0_FP16")
            VERSION_ID="2091367"
            FILENAME="realismIllustriousByStableYogi_v50FP16.safetensors"
            ;;
        "v5.0_DMD2")
            VERSION_ID="TBD"  # Look up version ID for DMD2 variant
            FILENAME="realismIllustriousByStableYogi_v50DMD2.safetensors"
            ;;
        "v1.6_Hyper")
            VERSION_ID="TBD"  # Look up version ID for Hyper variant
            FILENAME="realismIllustriousByStableYogi_v16Hyper.safetensors"
            ;;
    esac

    # Download checkpoint
    if [ ! -f "$MODELS_DIR/checkpoints/$FILENAME" ]; then
        echo "  [Download] Realism Illustrious ${ILLUSTRIOUS_MODEL:-v5.0_FP16}"
        if [ -n "$CIVITAI_API_KEY" ]; then
            wget -c -q --show-progress \
                "https://civitai.com/api/download/models/${VERSION_ID}?token=${CIVITAI_API_KEY}" \
                --content-disposition \
                -P "$MODELS_DIR/checkpoints/" || echo "  [Error] Failed to download checkpoint"
        else
            wget -c -q --show-progress \
                "https://civitai.com/api/download/models/${VERSION_ID}" \
                --content-disposition \
                -P "$MODELS_DIR/checkpoints/" || echo "  [Error] Failed (may need API key)"
        fi
    else
        echo "  [Skip] Checkpoint already exists"
    fi

    # Download embeddings
    if [ "${ENABLE_ILLUSTRIOUS_EMBEDDINGS:-true}" = "true" ]; then
        echo "[Illustrious] Downloading embeddings..."

        # Positive embedding (version ID from CivitAI)
        if [ ! -f "$MODELS_DIR/embeddings/Realism_Illustrious_Positive_Embedding.safetensors" ]; then
            wget -c -q --show-progress \
                "https://civitai.com/api/download/models/POSITIVE_VERSION_ID" \
                --content-disposition \
                -P "$MODELS_DIR/embeddings/" || echo "  [Error] Failed to download positive embedding"
        fi

        # Negative embedding (version ID from CivitAI)
        if [ ! -f "$MODELS_DIR/embeddings/Realism_Illustrious_Negative_Embedding.safetensors" ]; then
            wget -c -q --show-progress \
                "https://civitai.com/api/download/models/NEGATIVE_VERSION_ID" \
                --content-disposition \
                -P "$MODELS_DIR/embeddings/" || echo "  [Error] Failed to download negative embedding"
        fi
    fi
fi
```

### Dockerfile Updates

Add to model directory creation:

```dockerfile
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings}
```

### Template Configuration

Add to RunPod template JSON:

```json
{"key": "ENABLE_ILLUSTRIOUS", "value": "false"},
{"key": "ILLUSTRIOUS_MODEL", "value": "v5.0_FP16"},
{"key": "ENABLE_ILLUSTRIOUS_EMBEDDINGS", "value": "true"}
```

---

## 7. Model Size Reference

| Component | Size | VRAM |
|-----------|------|------|
| Realism Illustrious v5.0_FP16 | ~6.46GB | ~8GB |
| Positive Embedding | <1MB | N/A |
| Negative Embedding | <1MB | N/A |
| **Total** | **~6.5GB** | **~8GB** |

### Compatibility Notes

- **Base**: Illustrious XL (SDXL derivative)
- **LoRAs**: Only Illustrious-compatible LoRAs work (NOT standard SDXL LoRAs)
- **Resolution**: 896x1152 recommended, any SDXL size supported
- **Clip Skip**: 2
- **Sampler**: Euler A or DPM++ 2M Karras

---

## 8. Outstanding Research

### Version IDs Needed

Before implementation, need to look up CivitAI version IDs for:
1. v5.0_DMD2 variant
2. v1.6_Hyper variant
3. Positive embedding (Realism_Illustrious_Positive_Embedding)
4. Negative embedding (Realism_Illustrious_Negative_Embedding)

### API Verification

Need to verify:
1. Whether embeddings are bundled with model or separate downloads
2. Exact filenames from CivitAI downloads

---

## 9. Comparison with Existing Models

| Model | Storage | Source | NSFW | LoRAs |
|-------|---------|--------|------|-------|
| Z-Image Turbo | diffusion_models/ | HuggingFace | Limited | No |
| Realism Illustrious | checkpoints/ | CivitAI | Full | Illustrious |
| WAN 2.2 | diffusion_models/ | HuggingFace | Yes | WAN |

**Key Difference**: Realism Illustrious goes to `checkpoints/` (SDXL-class), while transformer models (Z-Image, WAN) go to `diffusion_models/`.

---

## Sources

- PRD: `dev/agents/artifacts/doc/plan/hearmeman-extended-template.md`
- NSFW.md: Model reference and CivitAI URLs
- realism-illustrious-research.md: Detailed model analysis
- civitai-vs-huggingface-loras.md: CivitAI download patterns
- runpod-custom-template-guide.md: Directory structure reference
