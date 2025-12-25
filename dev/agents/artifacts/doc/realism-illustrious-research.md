---
task: Research Realism Illustrious By Stable Yogi model
agent: hc (headless claude)
model: claude-opus-4-5-20251101
author: oz
timestamp: 2025-12-24T12:00:00Z
status: completed
---

# Realism Illustrious By Stable Yogi - Research Report

## Model Overview

| Property | Value |
|----------|-------|
| Model Name | Realism Illustrious By Stable Yogi |
| CivitAI URL | https://civitai.com/models/974693/realism-illustrious-by-stable-yogi |
| Base Model | **Illustrious XL** (which is itself a finetune of Kohaku-XL, which is a finetune of SDXL) |
| Creator | Stable Yogi |
| Latest Version | v5.0_FP16 (also available: v5.0_DMD2, v2.2_FP16, v1.6_Hyper) |
| License | Illustrious License |

## What is Illustrious XL?

Illustrious XL is part of the anime-focused SDXL derivative family:

```
SDXL → Kohaku-XL → Illustrious XL → [Various Fine-tunes]
                                  ↓
                              NoobAI-XL (extended dataset)
```

**Key characteristics of Illustrious:**
- Trained on Danbooru2023 dataset (~13M images including anime and e621)
- Superior character knowledge - recognizes virtually all characters with Danbooru artwork
- Excellent prompt adherence using booru-style tags
- Better hand rendering than competing models
- **NOT compatible with standard SDXL LoRAs** - requires Illustrious-specific extensions

## What Makes This Model Special

### 1. **Photorealism on Anime Base**
Unlike pure anime Illustrious models, Realism Illustrious pushes the base toward photographic output while retaining booru tag compatibility.

### 2. **Training Data**
- v1.6_Hyper: Trained on **22,000 images** from diverse datasets
- Focus areas: realism, skin texture, lighting conditions

### 3. **Multiple Speed Variants**
| Version | Steps | CFG | Use Case |
|---------|-------|-----|----------|
| v5.0_FP16 | 20-30 | 5-7 | Standard quality |
| v5.0_DMD2 | 6-8 | 1.01-1.1 | Fast generation |
| v1.6_Hyper | 4+ (min 10) | 1.5+ | Fastest, uses Hyper LoRA |

### 4. **NSFW Capabilities**
Full NSFW support inherited from Illustrious base. The Illustrious family (including NoobAI) has extensive knowledge of:
- Danbooru-style character rendering
- Anatomical accuracy
- Various body types and poses

### 5. **Recommended Settings**
```yaml
Resolution: Any SDXL size (896x1152 recommended, 896x1120 for Instagram)
Clip Skip: 2
Sampler: Euler A or LCM (for DMD2)
Embeddings:
  Positive: Realism_Illustrious_Positive_Embedding
  Negative: Realism_Illustrious_Negative_Embedding
Tags: "Realistic", "Photorealistic" improve results
```

---

## Competing Models Comparison

### Illustrious Ecosystem (Anime-to-Realism)

| Model | CivitAI Link | Strengths |
|-------|--------------|-----------|
| **ILustREAL v5** | https://civitai.com/models/1046064/ilustreal | Fantasy-realism blend, cinematic depth, 225k+ generations |
| **Illustrious Realism by klaabu** | https://civitai.com/models/1412827/illustrious-realism-by-klaabu | High-end realism, dynamic lighting |
| **Reallustrious LoRA** | https://civitai.com/models/949342/reallustrious-photorealism-for-illustrious-xl | Add photorealism to any Illustrious model |
| **Ultra Realistic By Stable Yogi (ILLUS)** | https://civitai.com/models/1584358/ultra-realistic-by-stable-yogi-illus | Merges Realism + Babes aesthetics |
| **CyberIllustrious** | - | Can steer toward 2.5D anime style |

### Pure SDXL Realism Models

| Model | CivitAI Link | Strengths |
|-------|--------------|-----------|
| **Realism Engine SDXL** | https://civitai.com/models/152525/realism-engine-sdxl | Unmatched facial realism, simple prompting |
| **RealVisXL V5.0** | https://civitai.com/models/ | Hyper-realistic portraits, cinematic scenes |
| **DevlishPhotoRealism SDXL** | https://civitai.com/models/156061/devlishphotorealism-sdxl | Cinematic vibes, dramatic lighting |
| **epiCRealism XL** | - | Sharp textures + soft-focus balance |
| **DreamShaper XL** | - | Landscapes, objects, animals, cinematic grading |
| **LEOSAM's HelloWorld XL** | - | Landscapes, humans, objects with depth |
| **ZavyChromaXL** | - | Cinematic lighting, diverse portraiture |
| **AlbedoBase XL** | - | Detailed skin, expressive faces |
| **Ultra Realistic By Stable Yogi (SDXL)** | https://civitai.com/models/1606452/ultra-realistic-by-stable-yogi-sdxl | Improved hands, influencer-style realism |

### Pony-Based Alternatives

| Model | CivitAI Link | Notes |
|-------|--------------|-------|
| **Realism By Stable Yogi (Pony)** | https://civitai.com/models/166609/realism-by-stable-yogi-pony | Same creator, Pony base |
| **Ultra Realistic By Stable Yogi (Pony)** | https://civitai.com/models/167318/ultra-realistic-by-stable-yogi-pony | Fuses Realism + Babes |
| **Asian Realism By Stable Yogi (PONY)** | https://civitai.com/models/168949/asian-realism-by-stable-yogi-pony | Asian-focused realism |

---

## Z-Image Turbo Comparison

### Z-Image Turbo Overview

| Property | Value |
|----------|-------|
| Developer | Alibaba Tongyi Lab |
| Parameters | 6B |
| Architecture | Single-stream diffusion transformer |
| NFE (Steps) | 8 (distilled) |
| HuggingFace | https://huggingface.co/Tongyi-MAI/Z-Image-Turbo |

### Quality vs Speed Tradeoff

| Aspect | Realism Illustrious | Z-Image Turbo |
|--------|---------------------|---------------|
| **Steps Required** | 20-30 (standard), 6-8 (DMD2), 4+ (Hyper) | 6-9 |
| **Parameters** | ~6.6B (SDXL-class) | 6B |
| **Realism Quality** | Excellent, anime-influenced aesthetic | Photography-level, pure photorealism |
| **Character Knowledge** | Extensive (Danbooru) | General (no anime training) |
| **NSFW** | Full support | Limited/None |
| **LoRA Support** | Illustrious ecosystem | No (distilled model) |
| **Negative Prompts** | Supported | NOT supported (distilled) |
| **VRAM** | 8-12GB typical | <16GB |
| **Inference Speed** | Moderate | Fast (<1 sec on H800) |

### Z-Image Quality Assessment

**Strengths:**
- "#1 open-source model" on Artificial Analysis leaderboard
- Beats Flux.1 Dev (12B) in most photorealism benchmarks
- Excellent texture stability even at low steps
- Strong aesthetic quality in composition and mood
- Practical for consumer GPUs

**Weaknesses:**
- "Slightly softer details" vs heavier models
- No negative prompt support (distilled limitation)
- Best for photorealism only - limited stylization
- No character/anime knowledge

### Recommendation

| Use Case | Best Choice |
|----------|-------------|
| **Fast photorealism** | Z-Image Turbo |
| **Anime characters + realism** | Realism Illustrious |
| **NSFW content** | Realism Illustrious |
| **Character-specific generation** | Realism Illustrious |
| **Pure photography simulation** | Z-Image Turbo |
| **LoRA customization** | Realism Illustrious |
| **Production speed** | Z-Image Turbo |

---

## Stable Yogi Model Family

The creator offers realism models across all major base architectures:

| Base | Model | Link |
|------|-------|------|
| Illustrious | Realism Illustrious | https://civitai.com/models/974693 |
| Illustrious | Ultra Realistic (ILLUS) | https://civitai.com/models/1584358 |
| Illustrious | Babes Illustrious | https://civitai.com/models/1134825 |
| SDXL | Ultra Realistic (SDXL) | https://civitai.com/models/1606452 |
| Pony | Realism By Stable Yogi | https://civitai.com/models/166609 |
| Pony | Ultra Realistic (Pony) | https://civitai.com/models/167318 |
| Pony | Asian Realism | https://civitai.com/models/168949 |
| LoRA | Realism Lora (Pony) | https://civitai.com/models/1098033 |

### Embeddings (Work with SDXL/Pony/Illustrious)
- **PDXL Positives**: https://civitai.com/models/1331980
- **PDXL Negatives**: https://civitai.com/models/1331758

---

## Summary

**Realism Illustrious By Stable Yogi** is an Illustrious XL-based checkpoint optimized for photorealistic output while retaining anime character knowledge and booru tag compatibility. It excels at:

1. **Anime-to-realism bridge** - Render known characters realistically
2. **NSFW capabilities** - Full support from Illustrious base
3. **Speed options** - Standard, DMD2, and Hyper variants
4. **Ecosystem compatibility** - Works with Illustrious LoRAs and embeddings

**For pure photorealism without anime features**, consider:
- Z-Image Turbo (fastest, best quality/speed ratio)
- Realism Engine SDXL (best facial realism)
- RealVisXL V5.0 (hyper-realistic portraits)

**For anime-adjacent realism**, this model is among the top choices alongside ILustREAL and CyberIllustrious.

---

## Sources

- [Realism Illustrious By Stable Yogi - CivitAI](https://civitai.com/models/974693/realism-illustrious-by-stable-yogi)
- [9 Best SDXL Models for Realism - ShakersAI](https://shakersai.com/ai-tools/images/stable-diffusion/sdxl-models-for-realism/)
- [ILustREAL - CivitAI](https://civitai.com/models/1046064/ilustreal)
- [Reallustrious LoRA - CivitAI](https://civitai.com/models/949342/reallustrious-photorealism-for-illustrious-xl)
- [ILXL vs NAI-XL Comparison - CivitAI](https://civitai.com/articles/8642/ilxl-illustrious-xl-nai-xl-noobai-xl-model-comparison)
- [Z-Image Turbo - HuggingFace](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
- [Z-Image Blog - Alibaba](https://tongyi-mai.github.io/Z-Image-blog/)
- [Z-Image on ComfyUI - Stable Diffusion Art](https://stable-diffusion-art.com/z-image/)
