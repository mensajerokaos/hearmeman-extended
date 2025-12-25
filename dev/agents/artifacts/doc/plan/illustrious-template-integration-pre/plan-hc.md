---
author: oz
model: claude-opus-4-5
date: 2025-12-24 23:35
task: Implementation Plan - Realism Illustrious Template Integration
status: ready-for-review
---

# Implementation Plan: Realism Illustrious Integration

## Executive Summary

Add Realism Illustrious By Stable Yogi to the Hearmeman Extended Template PRD. This SDXL-based photorealistic model goes to `checkpoints/` (not `diffusion_models/` like WAN/Z-Image).

**Total Download Size**: ~6.5GB required, ~7GB with optional LoRA
**VRAM Requirement**: ~8GB (fits L40S/A6000/A40)

---

## 1. Environment Variables

### Add to PRD Section 3 (Environment Variables)

**Feature Toggles Table:**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_ILLUSTRIOUS` | bool | false | Download Realism Illustrious checkpoint (~6.5GB) |
| `ILLUSTRIOUS_LORAS` | string | - | Comma-separated CivitAI version IDs for Illustrious-compatible LoRAs |

**Notes:**
- Embeddings download automatically with checkpoint (bundled behavior)
- LoRAs are optional and user-specified via `ILLUSTRIOUS_LORAS`
- Requires `CIVITAI_API_KEY` for NSFW content

---

## 2. Dockerfile Changes

### Add to Layer 5 (model directory creation)

**Current line (~258):**
```dockerfile
RUN mkdir -p /workspace/ComfyUI/models/{vibevoice,text_encoders,diffusion_models,vae,controlnet,loras}
```

**Replace with:**
```dockerfile
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras}
```

**Changes:**
- Added `checkpoints/` (for SDXL-class models like Illustrious)
- Added `embeddings/` (for textual inversions)

---

## 3. download_models.sh Additions

### Add new section after CivitAI LoRAs section (~line 600)

```bash
# ============================================
# Realism Illustrious (SDXL photorealism)
# ============================================
if [ "${ENABLE_ILLUSTRIOUS:-false}" = "true" ]; then
    echo ""
    echo "[Illustrious] Downloading Realism Illustrious v5.0 FP16..."

    # Checkpoint (6.46GB)
    CHECKPOINT_FILE="$MODELS_DIR/checkpoints/realismIllustriousByStableYogi_v50FP16.safetensors"
    if [ ! -f "$CHECKPOINT_FILE" ]; then
        echo "  [Download] Realism Illustrious checkpoint (6.46GB)"
        if [ -n "$CIVITAI_API_KEY" ]; then
            wget -c -q --show-progress \
                "https://civitai.com/api/download/models/2091367?token=${CIVITAI_API_KEY}" \
                --content-disposition \
                -P "$MODELS_DIR/checkpoints/" || echo "  [Error] Failed to download checkpoint"
        else
            wget -c -q --show-progress \
                "https://civitai.com/api/download/models/2091367" \
                --content-disposition \
                -P "$MODELS_DIR/checkpoints/" || echo "  [Error] Failed (may need CIVITAI_API_KEY)"
        fi
    else
        echo "  [Skip] Checkpoint already exists"
    fi

    # Positive Embedding (352KB)
    POSITIVE_EMB="$MODELS_DIR/embeddings/Stable_Yogis_Illustrious_Positives.safetensors"
    if [ ! -f "$POSITIVE_EMB" ]; then
        echo "  [Download] Stable Yogi Positive Embedding"
        wget -c -q --show-progress \
            "https://civitai.com/api/download/models/1153237${CIVITAI_API_KEY:+?token=$CIVITAI_API_KEY}" \
            --content-disposition \
            -P "$MODELS_DIR/embeddings/" || echo "  [Error] Failed to download positive embedding"
    fi

    # Negative Embedding (536KB)
    NEGATIVE_EMB="$MODELS_DIR/embeddings/Stable_Yogis_Illustrious_Negatives.safetensors"
    if [ ! -f "$NEGATIVE_EMB" ]; then
        echo "  [Download] Stable Yogi Negative Embedding"
        wget -c -q --show-progress \
            "https://civitai.com/api/download/models/1153212${CIVITAI_API_KEY:+?token=$CIVITAI_API_KEY}" \
            --content-disposition \
            -P "$MODELS_DIR/embeddings/" || echo "  [Error] Failed to download negative embedding"
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
        echo "  [Download] CivitAI LoRA version: $version_id"

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

---

## 4. Template JSON Config Updates

### RunPod Template Environment Variables

Add to template JSON `env` array:

```json
{
  "key": "ENABLE_ILLUSTRIOUS",
  "value": "false"
},
{
  "key": "ILLUSTRIOUS_LORAS",
  "value": ""
}
```

### Recommended LoRA Version IDs

For documentation/user guidance:

| LoRA | Version ID | Size | Purpose |
|------|------------|------|---------|
| Realism LoRA (Illustrious) | 1472103 | 29.4MB | Hyperrealistic skin |
| Illustrious Realism Enhancer | 1253047 | 325MB | Overall realism boost |
| Realism LoRA (SDXL) | 1236430 | 42.5MB | Alternative SDXL LoRA |

**Example usage:**
```
ILLUSTRIOUS_LORAS=1472103,1253047
```

---

## 5. PRD Documentation Updates

### Add to Architecture Diagram

Update the ON-DEMAND MODELS box:

```
ENABLE_ILLUSTRIOUS=true:
├── realismIllustriousByStableYogi_v50FP16.safetensors (~6.5GB)
├── Stable_Yogis_Illustrious_Positives.safetensors (<1MB)
└── Stable_Yogis_Illustrious_Negatives.safetensors (<1MB)
```

### Add Usage Notes Section

```markdown
## Realism Illustrious Usage

**Recommended Settings:**
- Sampler: DPM++ 2M SDE, Euler A
- Steps: 27+
- CFG Scale: 5
- Clip Skip: 2
- Resolution: 896×1152 (any SDXL resolution)

**Embedding Usage (ComfyUI):**
- Positive prompt: Add `embedding:Stable_Yogis_Illustrious_Positives` at start
- Negative prompt: Add `embedding:Stable_Yogis_Illustrious_Negatives` at start

**Compatible LoRAs:**
- Only Illustrious-compatible LoRAs work (NOT standard SDXL LoRAs)
- Use `ILLUSTRIOUS_LORAS` env var with CivitAI version IDs
```

---

## 6. File Changes Summary

| File | Action | Lines Affected |
|------|--------|----------------|
| `Dockerfile` | Edit | ~258 (mkdir line) |
| `download_models.sh` | Add | ~50 new lines after line 600 |
| PRD Section 3 | Add | 2 new env var rows |
| PRD Architecture | Add | 3 new lines in diagram |
| Template JSON | Add | 2 new env entries |

---

## 7. CivitAI Version IDs Reference

| Asset | Model ID | Version ID | Size |
|-------|----------|------------|------|
| Realism Illustrious v5.0 FP16 | 974693 | **2091367** | 6.46GB |
| Stable Yogi Positive Embedding | 1028256 | **1153237** | 352KB |
| Stable Yogi Negative Embedding | 1028231 | **1153212** | 536KB |
| Realism LoRA (Illustrious) | 1304531 | **1472103** | 29.4MB |
| Illustrious Realism Enhancer | 1115090 | **1253047** | 325MB |

---

## 8. Testing Checklist

- [ ] Dockerfile builds successfully with new directories
- [ ] `ENABLE_ILLUSTRIOUS=true` downloads checkpoint + embeddings
- [ ] Files land in correct directories (`checkpoints/`, `embeddings/`)
- [ ] `ILLUSTRIOUS_LORAS` downloads to `loras/`
- [ ] Download resumes on interruption (`-c` flag)
- [ ] Works with and without `CIVITAI_API_KEY`
- [ ] ComfyUI loads checkpoint and embeddings correctly

---

## Sources

- research-hc.md: PRD structure analysis
- research-ce.md: CivitAI API and version IDs
- NSFW.md: Model reference
- hearmeman-extended-template.md: Current PRD
