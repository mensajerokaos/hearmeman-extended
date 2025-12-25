---
task: Add Realism Illustrious to Hearmeman Extended Template
created: 2025-12-24T23:26:32-06:00
status: ready
model: Realism Illustrious by Stable Yogi v5.0_FP16
civitai_url: https://civitai.com/models/974693?modelVersionId=2091367
author: oz
co-author: claude-opus-4-5
---

# Plan: Illustrious Template Integration

## Summary

Add **Realism Illustrious By Stable Yogi** (best SDXL realism model) to the Hearmeman Extended RunPod Template. This includes CivitAI download support for the checkpoint, required embeddings, and optional LoRAs.

| Property | Value |
|----------|-------|
| Model ID | 974693 |
| Version ID | **2091367** (v5.0_FP16) |
| File Size | 6.46 GB |
| VRAM | ~8GB |
| Base | Illustrious XL (SDXL derivative) |

---

## Environment Variables

Add to PRD Section 3 (Environment Variables):

### Feature Toggles

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_ILLUSTRIOUS` | bool | false | Download Realism Illustrious checkpoint (~6.5GB) |
| `ENABLE_ILLUSTRIOUS_EMBEDDINGS` | bool | true | Download Stable Yogi's positive/negative embeddings |
| `ILLUSTRIOUS_LORAS` | string | - | Comma-separated CivitAI version IDs for Illustrious-compatible LoRAs |

**Notes:**
- Requires `CIVITAI_API_KEY` for NSFW content
- Embeddings are small (<1MB total) and strongly recommended
- Use `ILLUSTRIOUS_LORAS` for optional realism boosters

---

## CivitAI Version IDs Reference

### Required Assets

| Asset | Model ID | Version ID | Size | Target Directory |
|-------|----------|------------|------|------------------|
| Realism Illustrious v5.0 FP16 | 974693 | **2091367** | 6.46GB | `checkpoints/` |
| Stable Yogi Positive Embedding | 1028256 | **1153237** | 352KB | `embeddings/` |
| Stable Yogi Negative Embedding | 1028231 | **1153212** | 536KB | `embeddings/` |

### Optional LoRAs

| LoRA | Version ID | Size | Strength | Purpose |
|------|------------|------|----------|---------|
| Realism LoRA (Illustrious) | **1472103** | 29.4MB | 0.3-0.6 | Hyperrealistic skin, freckles |
| Illustrious Realism Enhancer | **1253047** | 325MB | 0.7-0.9 | Overall realism boost |
| Realism LoRA (SDXL) | **1236430** | 42.5MB | 0.2-0.3 | Alternative SDXL style |

**Example usage:** `ILLUSTRIOUS_LORAS=1472103,1253047`

---

## Implementation Steps

### Step 1: Update Dockerfile (Layer 5)

Add `checkpoints/` and `embeddings/` directories.

**Before:**
```dockerfile
RUN mkdir -p /workspace/ComfyUI/models/{vibevoice,text_encoders,diffusion_models,vae,controlnet,loras}
```

**After:**
```dockerfile
RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras}
```

---

### Step 2: Add Helper Function to download_models.sh

Add at top of script (after shebang and variable declarations):

```bash
# ============================================
# Helper Functions
# ============================================
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
```

---

### Step 3: Add Illustrious Download Section

Add after XTTS section, before CivitAI LoRAs section (~line 520):

```bash
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
```

---

### Step 4: Update Template JSON Configuration

Add to RunPod template `env` array (Section 7):

```json
{"key": "ENABLE_ILLUSTRIOUS", "value": "false"},
{"key": "ENABLE_ILLUSTRIOUS_EMBEDDINGS", "value": "true"},
{"key": "ILLUSTRIOUS_LORAS", "value": ""}
```

---

### Step 5: Update Architecture Diagram

Add to PRD ON-DEMAND MODELS section:

```
ENABLE_ILLUSTRIOUS=true:
├── realismIllustriousByStableYogi_v50FP16.safetensors (~6.5GB)
├── Stable_Yogis_Illustrious_Positives.safetensors (<1MB)
└── Stable_Yogis_Illustrious_Negatives.safetensors (<1MB)

ILLUSTRIOUS_LORAS=1472103,1253047:
├── Realim_Lora_BSY_IL_V1_RA42.safetensors (29MB)
└── [Realism Enhancer] (325MB)
```

---

### Step 6: Add Usage Documentation

Add new section to PRD:

```markdown
## Realism Illustrious Usage

### Recommended Settings

| Parameter | Value |
|-----------|-------|
| Sampler | DPM++ 2M SDE, Euler A, DPM SDE |
| Steps | 27+ |
| CFG Scale | 5 |
| Clip Skip | 2 |
| Resolution | 896×1152 (any SDXL resolution) |

### Embedding Usage (ComfyUI)

Reference embeddings in CLIP Text Encode nodes:

**Positive Prompt:**
```
embedding:Stable_Yogis_Illustrious_Positives, masterpiece, photorealistic, ...
```

**Negative Prompt:**
```
embedding:Stable_Yogis_Illustrious_Negatives, low quality, blurry, ...
```

### LoRA Compatibility

Only Illustrious-compatible LoRAs work with this model:
- ❌ Standard SDXL LoRAs (incompatible)
- ✅ Illustrious LoRAs (use `ILLUSTRIOUS_LORAS` env var)

### V5 Improvements Over V4

- Sharper detail across textures, hair strands, fine edges
- Smoother gradients and banding-free color transitions
- Richer dynamic range with balanced highlights/shadows
- Reduced artifacts around complex shapes (hands, glasses, props)
```

---

## Code Changes Summary

| File | Section | Action | Lines |
|------|---------|--------|-------|
| Dockerfile | Layer 5 | Edit mkdir | ~258 |
| download_models.sh | Top | Add civitai_download() | +20 |
| download_models.sh | After XTTS | Add Illustrious section | +40 |
| PRD Section 3 | Env vars table | Add 3 rows | +3 |
| PRD Section 7 | Template JSON | Add 3 entries | +3 |
| PRD | New section | Add usage docs | +30 |

---

## Storage Requirements

| Component | Size | Priority |
|-----------|------|----------|
| Realism Illustrious v5.0 FP16 | 6.46 GB | Required |
| Positive Embedding | 352 KB | Recommended |
| Negative Embedding | 536 KB | Recommended |
| Realism LoRA (Illustrious) | 29.4 MB | Optional |
| Illustrious Realism Enhancer | 325 MB | Optional |
| **Total (Required + Recommended)** | **~6.5 GB** | |
| **Total (All)** | **~6.9 GB** | |

---

## Testing Checklist

### Build Verification
- [ ] Dockerfile builds with new directories
- [ ] `checkpoints/` directory created
- [ ] `embeddings/` directory created

### Download Tests
- [ ] `ENABLE_ILLUSTRIOUS=false` → No download (default)
- [ ] `ENABLE_ILLUSTRIOUS=true` → Checkpoint downloads (~6.5GB)
- [ ] `ENABLE_ILLUSTRIOUS_EMBEDDINGS=true` → Both embeddings download
- [ ] `ENABLE_ILLUSTRIOUS_EMBEDDINGS=false` → Only checkpoint downloads
- [ ] `ILLUSTRIOUS_LORAS=1472103` → LoRA downloads to loras/
- [ ] Download resumes on interrupt (`-c` flag works)
- [ ] Works without `CIVITAI_API_KEY` (model is public)

### ComfyUI Integration
- [ ] CheckpointLoaderSimple shows model in dropdown
- [ ] `embedding:Stable_Yogis_Illustrious_Positives` resolves
- [ ] `embedding:Stable_Yogis_Illustrious_Negatives` resolves
- [ ] Basic txt2img generation works
- [ ] LoRA loads and applies correctly

### Storage Modes
- [ ] Ephemeral mode: Downloads on cold start
- [ ] Persistent mode: Skips download if exists

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| CivitAI API rate limits | Download failures | Resume support (`-c` flag), retry logic |
| Large file size (6.5GB) | Slow cold starts | File existence check, network volume caching |
| NSFW content gating | Download blocked | `CIVITAI_API_KEY` required message |
| LoRA compatibility | Generation failures | Document "Illustrious-only" requirement |

---

## Sources

- [Realism Illustrious By Stable Yogi](https://civitai.com/models/974693/realism-illustrious-by-stable-yogi)
- [Stable Yogi's Illustrious Positives](https://civitai.com/models/1028256)
- [Stable Yogi's Illustrious Negatives](https://civitai.com/models/1028231)
- [CivitAI API Guide](https://education.civitai.com/civitais-guide-to-downloading-via-api/)
- [Realism LoRA (Illustrious)](https://civitai.com/models/1304531)
- [Illustrious Realism Enhancer](https://civitai.com/models/1115090)
- research-hc.md: PRD structure analysis
- research-ce.md: CivitAI download research
- plan-hc.md: Implementation plan (hc agent)
- plan-ce.md: Integration plan (ce agent)
