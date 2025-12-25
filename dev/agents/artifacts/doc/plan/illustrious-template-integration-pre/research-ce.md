# CivitAI Download Research: Realism Illustrious

**Author**: oz
**Model**: claude-opus-4-5
**Date**: 2025-12-24 23:20
**Task**: Research CivitAI download for Realism Illustrious checkpoint and related assets

---

## 1. Main Model: Realism Illustrious By Stable Yogi

| Property | Value |
|----------|-------|
| Model URL | https://civitai.com/models/974693/realism-illustrious-by-stable-yogi |
| Model ID | 974693 |
| Version ID | **2091367** (v5.0_FP16) |
| File Size | **6.46 GB** |
| Format | SafeTensor (pruned) |
| Base Model | Illustrious XL |

### Download URL
```
https://civitai.com/api/download/models/2091367?token=YOUR_CIVITAI_TOKEN
```

### Recommended Settings
- **Samplers**: DPM++ 2M SDE, Euler A, DPM SDE
- **Steps**: 27+
- **CFG Scale**: 5
- **Clip Skip**: 2
- **Resolution**: 896×1152 (any SDXL resolution)

### V5 Improvements
- Sharper detail across textures, hair strands and fine edges
- Smoother gradients and banding-free color transitions
- Richer dynamic range with balanced highlights and shadows
- Reduced artifacts around complex shapes (hands, glasses, props)

---

## 2. Required Embeddings

### Stable Yogi's Official Embeddings

| Embedding | Model ID | Version ID | File Name | Size |
|-----------|----------|------------|-----------|------|
| **Positive** | 1028256 | **1153237** | `Stable_Yogis_Illustrious_Positives.safetensors` | 352 KB |
| **Negative** | 1028231 | **1153212** | `Stable_Yogis_Illustrious_Negatives.safetensors` | 536 KB |

#### Download URLs
```bash
# Positive Embedding
https://civitai.com/api/download/models/1153237?token=YOUR_CIVITAI_TOKEN

# Negative Embedding
https://civitai.com/api/download/models/1153212?token=YOUR_CIVITAI_TOKEN
```

#### Usage
- Positive: Add at **beginning** of prompt
- Negative: Add at **beginning** of negative prompt
- ComfyUI format: `embedding:Stable_Yogis_Illustrious_Positives`

### Alternative: Lazy Embeddings (Universal)

More flexible option that works across Illustrious/NoobAI/Pony/SDXL:

| Embedding | Version ID | File Name | Purpose |
|-----------|------------|-----------|---------|
| lazypos | 1833157 | `lazypos.safetensors` | Quality boost (positive) |
| lazyneg | 2121199 | `lazyneg.safetensors` | Artifact reduction (negative) |
| lazyreal | 1667494 | `lazyreal.safetensors` | Realism toggle |
| lazyhand | 2268235 | `lazyhand.safetensors` | Hand fix (negative) |

Source: https://civitai.com/models/1302719

---

## 3. Top Recommended LoRAs

### LoRA 1: Realism LoRA By Stable Yogi (Illustrious)

| Property | Value |
|----------|-------|
| Model URL | https://civitai.com/models/1304531/realism-lora-by-stable-yogi-illustrious |
| Version ID | **1472103** |
| File Name | `Realim_Lora_BSY_IL_V1_RA42.safetensors` |
| File Size | **29.4 MB** |
| Strength | 0.3-0.6 (default: 0.6, max: 1.0) |

**Download URL:**
```
https://civitai.com/api/download/models/1472103?token=YOUR_CIVITAI_TOKEN
```

Best for: Hyperrealistic skin tones, freckles, natural lighting

---

### LoRA 2: Illustrious Realism Enhancer

| Property | Value |
|----------|-------|
| Model URL | https://civitai.com/models/1115090/illustrious-realism-enhancer |
| Version ID | **1253047** |
| File Size | **324.98 MB** |
| Strength | 0.7-0.9 |
| Clip Skip | 1 |

**Download URL:**
```
https://civitai.com/api/download/models/1253047?token=YOUR_CIVITAI_TOKEN
```

**Usage Tips:**
- Add "realistic" to positive prompt
- Add "3d, anime, 2d" to negative prompt

---

### LoRA 3: Touch of Realism [SDXL] V2

| Property | Value |
|----------|-------|
| Model URL | https://civitai.com/models/1705430/touch-of-realism-sdxl |
| Trigger Word | `touch-of-realismV2` |
| Strength | 0.5 (subtle enhancement) |
| Best For | Portraits, macro, wildlife, atmospheric landscapes |

Adds cinematic softness and natural bokeh (trained on Sony A7III photography).

---

### LoRA 4: Realism LoRA By Stable Yogi (SDXL)

| Property | Value |
|----------|-------|
| Model URL | https://civitai.com/models/1100721/realism-lora-by-stable-yogi-sdxl |
| Version ID | **1236430** |
| File Size | **42.47 MB** |
| Strength | 0.2-0.3 (default: 0.3, max: 1.0) |

**Download URL:**
```
https://civitai.com/api/download/models/1236430?token=YOUR_CIVITAI_TOKEN
```

---

### LoRA 5: Portrait Detailer/Enhancer

| Property | Value |
|----------|-------|
| Model URL | https://civitai.com/models/646497/portrait-detailerenhancer |
| Best For | Refining textures, sharpening features, vibrant portraits |

---

## 4. CivitAI API Reference

### Authentication Methods

**Method 1: Query Parameter (Recommended)**
```bash
curl -L -o model.safetensors \
  "https://civitai.com/api/download/models/{VERSION_ID}?token=YOUR_TOKEN"
```

**Method 2: Authorization Header**
```bash
curl -L -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  "https://civitai.com/api/download/models/{VERSION_ID}"
```

### Using wget
```bash
wget --content-disposition \
  "https://civitai.com/api/download/models/{VERSION_ID}?token=YOUR_TOKEN"
```

### Get Model Version Info
```bash
curl "https://civitai.com/api/v1/model-versions/{VERSION_ID}"
```

**Important:** Use `--content-disposition` to preserve original filenames.

### Token Setup
1. Go to https://civitai.com/user/account
2. Scroll to "API Keys" section
3. Click "+ Add API key"
4. Copy and store securely

---

## 5. RunPod Integration (Hearmeman Template)

For the Hearmeman Extended Template, add these environment variables:

```bash
CIVITAI_TOKEN=your_token_here
CHECKPOINT_IDS=2091367
LORA_IDS=1472103,1253047,1236430
```

### Manual Download Script
```bash
#!/bin/bash
TOKEN="${CIVITAI_TOKEN}"
MODELS_DIR="/workspace/ComfyUI/models"

# Checkpoint
wget --content-disposition -P "${MODELS_DIR}/checkpoints" \
  "https://civitai.com/api/download/models/2091367?token=${TOKEN}"

# Embeddings
wget --content-disposition -P "${MODELS_DIR}/embeddings" \
  "https://civitai.com/api/download/models/1153237?token=${TOKEN}"
wget --content-disposition -P "${MODELS_DIR}/embeddings" \
  "https://civitai.com/api/download/models/1153212?token=${TOKEN}"

# LoRAs
wget --content-disposition -P "${MODELS_DIR}/loras" \
  "https://civitai.com/api/download/models/1472103?token=${TOKEN}"
wget --content-disposition -P "${MODELS_DIR}/loras" \
  "https://civitai.com/api/download/models/1253047?token=${TOKEN}"
```

---

## 6. Storage Requirements Summary

| Asset | Size | Priority |
|-------|------|----------|
| Realism Illustrious v5.0 FP16 | 6.46 GB | Required |
| Stable Yogi Positive Embedding | 352 KB | Required |
| Stable Yogi Negative Embedding | 536 KB | Required |
| Realism LoRA (Illustrious) | 29.4 MB | Recommended |
| Illustrious Realism Enhancer | 325 MB | Optional |
| Realism LoRA (SDXL) | 42.5 MB | Optional |
| **Total (Required)** | **~6.5 GB** | |
| **Total (All)** | **~6.9 GB** | |

---

## Sources

- [Realism Illustrious By Stable Yogi](https://civitai.com/models/974693/realism-illustrious-by-stable-yogi)
- [CivitAI Guide to Downloading via API](https://education.civitai.com/civitais-guide-to-downloading-via-api/)
- [CivitAI REST API Reference](https://github.com/civitai/civitai/wiki/REST-API-Reference)
- [Stable Yogi's Illustrious Positives](https://civitai.com/models/1028256/stable-yogis-illustrious-positives)
- [Stable Yogi's Illustrious Negatives](https://civitai.com/models/1028231/stable-yogis-illustrious-negatives)
- [Lazy Embeddings](https://civitai.com/models/1302719)
- [Illustrious Realism Enhancer](https://civitai.com/models/1115090/illustrious-realism-enhancer)
- [Realism LoRA (Illustrious)](https://civitai.com/models/1304531/realism-lora-by-stable-yogi-illustrious)
- [Touch of Realism SDXL](https://civitai.com/models/1705430/touch-of-realism-sdxl)
