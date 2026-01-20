# SteadyDancer with TurboDiffusion Acceleration Research

**Date**: 2026-01-18
**Author**: Research Summary
**Topic**: Video Generation Acceleration using TurboDiffusion

---

## Executive Summary

TurboDiffusion is a recently released acceleration framework (Dec 2025) that achieves **100-200× speedup** for end-to-end video diffusion generation. While SteadyDancer is built on the Wan 2.1 architecture and could theoretically benefit from TurboDiffusion, **there is currently no documented integration or forum discussion specifically about combining these two technologies**. TurboDiffusion is designed to work with Wan 2.1/2.2 models and could potentially accelerate SteadyDancer, but this requires custom implementation.

---

## TurboDiffusion Overview

### Core Technology
- **Paper**: [TurboDiffusion: Accelerating Video Diffusion Models by 100-200 Times](https://arxiv.org/html/2512.16093v1)
- **GitHub**: https://github.com/thu-ml/TurboDiffusion
- **Release Date**: December 18, 2025
- **Performance**: 100-205× acceleration on RTX 5090

### Technical Approach
1. **SageAttention** - Low-bit attention acceleration
2. **SLA (Sparse-Linear Attention)** - Trainable sparse attention mechanism
3. **rCM (reversed continuous-time diffusion model)** - Timestep distillation
4. **SageSLA** - Combined attention optimization via SpargeAttn

### VRAM Requirements
| GPU Type | Configuration | Notes |
|----------|---------------|-------|
| H100 (>40GB) | Unquantized checkpoints, no `--quant_linear` | Maximum performance |
| RTX 5090/4090 | Quantized checkpoints with `--quant_linear` | Optimized for consumer cards |
| General | PyTorch ≥2.7.0 (2.8.0 recommended) | Avoid higher versions to prevent OOM |

### Installation
```bash
pip install turbodiffusion --no-build-isolation
```

### Key Parameters
- `--attention_type`: original/sla/sagesla (default: sagesla)
- `--sla_topk`: Default 0.1, recommended 0.15 for quality
- `--num_steps`: 1-4 sampling steps

---

## Performance Benchmarks (TurboDiffusion)

### Wan 2.1 Model Performance

| Model | Resolution | Original Time | TurboDiffusion | Speedup |
|-------|-----------|---------------|----------------|---------|
| Wan-2.1-T2V-1.3B | 480P | 184s | 1.9s | ~97× |
| Wan-2.1-T2V-14B | 480P | 1676s | 9.9s | ~169× |
| Wan-2.1-T2V-14B | 720P | 4767s | 24s | ~198× |
| Wan-2.2-I2V-A14B | 720P | 4549s | 38s | ~120× |

**Source**: [TurboDiffusion GitHub](https://github.com/thu-ml/TurboDiffusion)

---

## SteadyDancer Overview

### Model Information
- **Parameters**: 14B
- **Architecture**: Image-to-Video (I2V) paradigm
- **Purpose**: Human image animation with pose control
- **Key Feature**: First-frame preservation (solves identity drift)

### Technical Approach
1. **I2V Paradigm** - Conditions on first frame rather than pose sequences
2. **Condition Reconciliation** - Harmonizes motion and appearance
3. **X-Dance Benchmark** - Specialized evaluation dataset

### Resource Efficiency
- Uses "Staged Decoupled-Objective Training Pipeline"
- Supports multi-GPU inference via FSDP + xDiT USP
- Single-GPU inference recommended for reproducibility

### Repository Links
- **GitHub**: https://github.com/MCG-NJU/SteadyDancer
- **Hugging Face**: https://huggingface.co/MCG-NJU/SteadyDancer-14B

**Sources**:
- [SteadyDancer Overview](https://comfyuiweb.com/posts/steady-dancer-unveiled)
- [Video Generation Survey](https://github.com/yzhang2016/video-generation-survey/blob/main/video-generation.md)
- [Hugging Face Papers](https://huggingface.co/papers?q=Human%20image%20animation)

---

## Wan 2.1 VRAM Requirements (Reference)

### General VRAM Usage
| Configuration | VRAM | Notes |
|---------------|------|-------|
| 10s at 720p | 8GB | Using Wan2GP optimization |
| 10s at 1080p | 12GB | - |
| 20s at 1080p | 16GB | - |
| 4GB (special workflow) | 4GB | Requires GGUF + custom nodes |

**Source**: [Wan2GP GitHub](https://github.com/deepbeepmeep/Wan2GP)

### Reported Benchmarks
- **16GB VRAM (RTX 3080 Ti Laptop)**: 49 frames at 480×368 in ~3 minutes
- **4GB VRAM (RTX 3050 Laptop)**: Special GGUF workflow available

**Sources**:
- [Reddit: Wan 2.1 on 16GB VRAM](https://www.reddit.com/r/StableDiffusion/comments/1j4x73y/wan_21_on_16gb_vram/)
- [CivitAI: Wan2.1 GGUF 4GB VRAM Workflow](https://civitai.com/models/1309674/wan21gguf-only-4gb-vram-comfyui-workflow)

---

## Related Acceleration Techniques for Wan 2.1

### 1. FastWan (3-Step Distillation)
- **Release**: August 2025
- **Method**: "Sparse distillation" via FastVideo
- **Speed**: 3-step generation
- **Link**: [Reddit: FastWan Announcement](https://www.reddit.com/r/StableDiffusion/comments/1mhq6z5/wan_just_got_another_speed_boost_fastwan_3step/)

### 2. Teacache + Sage Attention
- **Speed Improvement**: ~30% faster than standard workflow
- **Implementation**: Custom nodes in ComfyUI
- **Link**: [Stable Diffusion Art: Wan 2.1 Teacache](https://stable-diffusion-art.com/wan-2-1-teacache/)

### 3. Step-Distilled Models
- **Source**: [Hugging Face: Wan2.1-T2V-14B-StepDistill-CfgDistill](https://huggingface.co/lightx2v/Wan2.1-T2V-14B-StepDistill-CfgDistill)

---

## Integration Possibilities & Workarounds

### Potential TurboDiffusion + SteadyDancer Integration

**Current Status**: NO documented integration exists

**Why**: TurboDiffusion was designed for Wan 2.1/2.2 base models. SteadyDancer, while built on Wan 2.1 architecture, uses a different I2V conditioning approach that may require custom adaptation.

**Required Work**:
1. Test TurboDiffusion's attention mechanisms with SteadyDancer's I2V paradigm
2. Validate timestep distillation compatibility
3. Benchmark quality vs. speed tradeoffs

### Alternative Acceleration Approaches for SteadyDancer

1. **Use distilled Wan 2.1 models** as base for SteadyDancer
2. **Apply Teacache + SageAttention** (30% speedup)
3. **Implement GGUF quantization** for lower VRAM
4. **Use mixed precision** (FP8, BF16) if available

---

## Forum Discussions & Community Activity

### Reddit Threads
1. [TurboDiffusion Discussion](https://www.reddit.com/r/StableDiffusion/comments/1pvx6cu/turbodiffusion_100200_acceleration_for_video/)
2. [FastWan Announcement](https://www.reddit.com/r/StableDiffusion/comments/1mhq97j/wan_just_got_another_speed_boost_fastwan_3step/)
3. [WAN 2.1 VRAM Discussion](https://www.reddit.com/r/StableDiffusion/comments/1j4x73y/wan_21_on_16gb_vram/)

### Hacker News
- [TurboDiffusion Release Discussion](https://news.ycombinator.com/item?id=46388907)

### YouTube
- [TurboDiffusion Overview](https://www.youtube.com/watch?v=NaxoESXgf-g) (Dec 24, 2025)

---

## Research Gaps & Missing Information

### Not Found
1. **Direct SteadyDancer + TurboDiffusion integration documentation**
2. **Specific VRAM benchmarks for SteadyDancer alone**
3. **Performance comparisons between acceleration methods on SteadyDancer**
4. **ComfyUI workflow configurations for TurboDiffusion + SteadyDancer**
5. **Quality degradation metrics for accelerated SteadyDancer**

### Recommended Next Steps
1. Check TurboDiffusion GitHub issues for user-reported integrations
2. Test TurboDiffusion inference scripts with SteadyDancer checkpoint
3. Benchmark VRAM usage with TurboDiffusion on 16GB vs 24GB VRAM cards
4. Compare quality metrics between original and accelerated generation

---

## Quick Reference Links

| Resource | URL |
|----------|-----|
| TurboDiffusion GitHub | https://github.com/thu-ml/TurboDiffusion |
| TurboDiffusion Paper | https://arxiv.org/html/2512.16093v1 |
| SteadyDancer GitHub | https://github.com/MCG-NJU/SteadyDancer |
| SteadyDancer HF Model | https://huggingface.co/MCG-NJU/SteadyDancer-14B |
| Wan2GP (Wan Optimizer) | https://github.com/deepbeepmeep/Wan2GP |
| Wan 2.1 Teacache Guide | https://stable-diffusion-art.com/wan-2-1-teacache/ |
| ComfyUI Wiki TurboDiffusion | https://comfyui-wiki.com/en/news/2025-12-16-turbodiffusion-video-acceleration |

---

## Conclusion

TurboDiffusion represents a significant breakthrough in video diffusion acceleration (100-200× speedup), but **there is currently no documented evidence of successful integration with SteadyDancer**. SteadyDancer's I2V paradigm and first-frame preservation approach would require custom validation with TurboDiffusion's attention mechanisms.

For immediate implementation, consider:
1. Testing TurboDiffusion with Wan 2.1 base models before SteadyDancer
2. Using alternative acceleration (Teacache + SageAttention) for SteadyDancer
3. Monitoring TurboDiffusion GitHub for community integration reports

**Priority**: Monitor both repositories for integration updates as the technologies mature.

---

*Research completed: 2026-01-18*
