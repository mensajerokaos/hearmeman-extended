---
author: oz
model: claude-opus-4-5
date: 2025-12-24 23:45
task: Integration Plan - Realism Illustrious for Hearmeman Extended Template
---

# Integration Plan: Realism Illustrious

**Target PRD**: `dev/agents/artifacts/doc/plan/hearmeman-extended-template.md`
**Research Sources**: `research-hc.md`, `research-ce.md`

---

## 1. Reuse Existing CivitAI Download Functions

### Current CivitAI Pattern (PRD lines 556-582)

The template already has a working CivitAI download pattern using `wget --content-disposition`. We can reuse this pattern directly.

### Proposed Reuse Strategy

**Option A (Recommended): Dedicated Illustrious Section**

Add a new section in `download_models.sh` between XTTS and CivitAI LoRAs (after line 520):

```bash
# ============================================
# Realism Illustrious (SDXL-based photorealism)
# ============================================
if [ "${ENABLE_ILLUSTRIOUS:-false}" = "true" ]; then
    echo "[Illustrious] Downloading Realism Illustrious..."

    # Model variant selection
    case "${ILLUSTRIOUS_MODEL:-v5.0_FP16}" in
        "v5.0_FP16")
            VERSION_ID="2091367"
            ;;
        # Add more variants as needed
    esac

    # Reuse CivitAI download pattern
    civitai_download "$VERSION_ID" "$MODELS_DIR/checkpoints"

    # Download embeddings (if enabled)
    if [ "${ENABLE_ILLUSTRIOUS_EMBEDDINGS:-true}" = "true" ]; then
        civitai_download "1153237" "$MODELS_DIR/embeddings"  # Positive
        civitai_download "1153212" "$MODELS_DIR/embeddings"  # Negative
    fi
fi
```

**Option B: Refactor into Reusable Function**

Extract the wget pattern into a helper function at the top of `download_models.sh`:

```bash
# ============================================
# Helper Functions
# ============================================
civitai_download() {
    local VERSION_ID="$1"
    local TARGET_DIR="$2"

    mkdir -p "$TARGET_DIR"

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
```

**Recommendation**: Option B (refactor) for cleaner code and consistent download behavior across all CivitAI assets.

---

## 2. Embedding Storage Location

### Directory Structure

Embeddings go in the standard ComfyUI location:

```
/workspace/ComfyUI/models/embeddings/
├── Stable_Yogis_Illustrious_Positives.safetensors  (352 KB)
└── Stable_Yogis_Illustrious_Negatives.safetensors  (536 KB)
```

### Dockerfile Update Required

Add `embeddings/` to the model directory creation (current PRD missing this):

```dockerfile
# Current:
RUN mkdir -p /workspace/ComfyUI/models/{vibevoice,text_encoders,diffusion_models,vae,controlnet,loras}

# Updated:
RUN mkdir -p /workspace/ComfyUI/models/{vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,checkpoints,embeddings}
```

### CivitAI Version IDs for Embeddings

| Embedding | Model ID | Version ID | Filename |
|-----------|----------|------------|----------|
| Positive | 1028256 | **1153237** | `Stable_Yogis_Illustrious_Positives.safetensors` |
| Negative | 1028231 | **1153212** | `Stable_Yogis_Illustrious_Negatives.safetensors` |

---

## 3. ComfyUI Node Compatibility

### Required Nodes (Already in Template)

Realism Illustrious uses standard SDXL workflow. No additional custom nodes required:

| Node | Purpose | Status |
|------|---------|--------|
| CheckpointLoaderSimple | Load checkpoint | Built-in |
| CLIPTextEncode | Encode prompts | Built-in |
| KSampler | Sampling | Built-in |
| VAEDecode | Decode latents | Built-in |
| EmptyLatentImage | Create latent | Built-in |

### Embedding Usage in ComfyUI

In CLIP Text Encode node, reference embeddings with syntax:
```
embedding:Stable_Yogis_Illustrious_Positives, masterpiece, ...
```

### Settings for Optimal Results

| Parameter | Value |
|-----------|-------|
| Clip Skip | 2 |
| Sampler | DPM++ 2M SDE, Euler A |
| Steps | 27+ |
| CFG Scale | 5 |
| Resolution | 896×1152 (SDXL) |

---

## 4. PRD Updates Required

### Section 3: Environment Variables

Add to Feature Toggles table:

```markdown
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_ILLUSTRIOUS` | bool | false | Download Realism Illustrious checkpoint |
| `ENABLE_ILLUSTRIOUS_EMBEDDINGS` | bool | true | Download positive/negative embeddings |
```

Add to Model Selection table:

```markdown
| Variable | Type | Default | Options |
|----------|------|---------|---------|
| `ILLUSTRIOUS_MODEL` | string | v5.0_FP16 | `v5.0_FP16` (more variants TBD) |
```

### Section 4: Dockerfile

Add to model directory creation line:

```dockerfile
RUN mkdir -p /workspace/ComfyUI/models/{...,checkpoints,embeddings}
```

### Section 5: download_models.sh

Add new section (between XTTS and CivitAI LoRAs):

```bash
# ============================================
# Realism Illustrious (SDXL-based photorealism)
# ============================================
if [ "${ENABLE_ILLUSTRIOUS:-false}" = "true" ]; then
    echo "[Illustrious] Downloading Realism Illustrious v5.0 FP16..."
    mkdir -p "$MODELS_DIR/checkpoints"

    civitai_download "2091367" "$MODELS_DIR/checkpoints"

    if [ "${ENABLE_ILLUSTRIOUS_EMBEDDINGS:-true}" = "true" ]; then
        echo "[Illustrious] Downloading embeddings..."
        mkdir -p "$MODELS_DIR/embeddings"
        civitai_download "1153237" "$MODELS_DIR/embeddings"  # Positive
        civitai_download "1153212" "$MODELS_DIR/embeddings"  # Negative
    fi
fi
```

### Section 7: Template Registration

Add to env array:

```json
{"key": "ENABLE_ILLUSTRIOUS", "value": "false"},
{"key": "ILLUSTRIOUS_MODEL", "value": "v5.0_FP16"},
{"key": "ENABLE_ILLUSTRIOUS_EMBEDDINGS", "value": "true"}
```

### Section 1: Executive Summary

Add to Key Features list:

```markdown
- **Realism Illustrious**: SDXL-based photorealistic image generation (~6.5GB)
```

---

## 5. Testing Checklist

### Pre-deployment Verification

- [ ] **Dockerfile builds** - Verify `checkpoints/` and `embeddings/` directories created
- [ ] **civitai_download function** - Works with/without API key
- [ ] **CIVITAI_API_KEY** - Token stored securely at `/workspace/.civitai-token`

### Model Download Tests

- [ ] **Checkpoint downloads** - `realismIllustriousByStableYogi_v50FP16.safetensors` (~6.46GB)
- [ ] **Positive embedding** - `Stable_Yogis_Illustrious_Positives.safetensors` (352KB)
- [ ] **Negative embedding** - `Stable_Yogis_Illustrious_Negatives.safetensors` (536KB)
- [ ] **Resume works** - Interrupt download, verify `-c` flag resumes

### ComfyUI Integration Tests

- [ ] **Checkpoint loads** - CheckpointLoaderSimple finds model in dropdown
- [ ] **Embeddings load** - `embedding:Stable_Yogis_Illustrious_Positives` works
- [ ] **Generation works** - Basic txt2img produces output
- [ ] **Settings verified** - Clip Skip 2, CFG 5, 27+ steps

### Environment Variable Tests

- [ ] **ENABLE_ILLUSTRIOUS=false** - No download occurs (default)
- [ ] **ENABLE_ILLUSTRIOUS=true** - Checkpoint + embeddings download
- [ ] **ENABLE_ILLUSTRIOUS_EMBEDDINGS=false** - Only checkpoint downloads
- [ ] **CIVITAI_API_KEY not set** - Public download still works (model is public)

### Storage Tests

- [ ] **Ephemeral mode** - Downloads to container, works after cold start
- [ ] **Persistent mode** - `/workspace` caches between sessions
- [ ] **File exists check** - Skip download if already present

---

## 6. Optional LoRAs (Future Enhancement)

These can be added via existing `CIVITAI_LORAS` env var:

| LoRA | Version ID | Size | Use |
|------|------------|------|-----|
| Realism LoRA (Illustrious) | 1472103 | 29MB | Hyperrealism boost |
| Illustrious Realism Enhancer | 1253047 | 325MB | Texture detail |
| Realism LoRA (SDXL) | 1236430 | 42MB | Alternative style |

Users can add: `CIVITAI_LORAS=1472103,1253047`

---

## 7. Storage Summary

| Component | Size | Location |
|-----------|------|----------|
| Realism Illustrious v5.0 FP16 | 6.46 GB | `checkpoints/` |
| Positive Embedding | 352 KB | `embeddings/` |
| Negative Embedding | 536 KB | `embeddings/` |
| **Total** | **~6.5 GB** | |

**VRAM**: ~8GB (fits on any GPU in template tier)

---

## 8. Implementation Order

1. **Add helper function** - `civitai_download()` at top of download script
2. **Update Dockerfile** - Add `checkpoints/` and `embeddings/` directories
3. **Add Illustrious section** - In download_models.sh
4. **Update env vars table** - In PRD Section 3
5. **Update template JSON** - In PRD Section 7
6. **Test on RunPod** - Verify full workflow

---

## Sources

- research-hc.md: PRD structure analysis
- research-ce.md: CivitAI version IDs and download URLs
- hearmeman-extended-template.md: Current PRD reference
