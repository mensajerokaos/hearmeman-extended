---
author: oz
model: claude-opus-4-5
date: 2025-12-23
task: RunPod GPU comparison for AI inference - pricing and specifications research
---

# RunPod GPU Comparison for AI Inference

Comprehensive research on RunPod GPU pricing, specifications, and workload suitability for AI inference tasks including image generation, video/animation, and TTS/voice synthesis.

## Table of Contents

1. [RunPod Pricing Summary](#runpod-pricing-summary)
2. [GPU Technical Specifications](#gpu-technical-specifications)
3. [PCIe vs SXM Comparison](#pcie-vs-sxm-comparison)
4. [Workload Requirements](#workload-requirements)
5. [Recommendations](#recommendations)
6. [Cost Optimization Strategies](#cost-optimization-strategies)
7. [Sources](#sources)

---

## RunPod Pricing Summary

### Secure Cloud On-Demand Pricing (December 2024/2025)

| GPU Model | VRAM | On-Demand | 6-Month | 1-Year |
|-----------|------|-----------|---------|--------|
| **H200** | 141GB | $3.59/hr | - | - |
| **H100 SXM** | 80GB | $2.69/hr | ~$1.00/hr | - |
| **H100 PCIe** | 80GB | $1.99/hr | $2.08/hr | $2.03/hr |
| **A100 SXM** | 80GB | $1.39/hr | $1.27/hr | $1.22/hr |
| **A100 PCIe** | 80GB | $1.19/hr | $1.18/hr | $1.14/hr |
| **L40S** | 48GB | $0.79/hr | $0.731/hr | $0.705/hr |
| **RTX 6000 Ada** | 48GB | ~$0.40/hr | - | - |
| **A40** | 48GB | ~$0.40/hr | - | - |
| **RTX 4090** | 24GB | $0.34/hr | $0.51/hr | $0.50/hr |
| **RTX 3090** | 24GB | $0.22/hr | $0.36/hr | $0.34/hr |

*Source: [RunPod GPU Pricing](https://www.runpod.io/gpu-pricing)*

### Community Cloud Pricing (Lower Tier)

Community Cloud offers **20-30% discount** compared to Secure Cloud:

| GPU Model | Secure Cloud | Community Cloud | Savings |
|-----------|--------------|-----------------|---------|
| RTX A5000 (24GB) | $0.29/hr | $0.16/hr | ~45% |
| RTX 3090 (24GB) | $0.43/hr | $0.22/hr | ~49% |
| A100 80GB | ~$1.89/hr | ~$0.79/hr | ~58% |

*Source: [ComputePrices RunPod](https://computeprices.com/providers/runpod)*

### Spot Instance Discounts

Spot instances offer **50-91% discounts** over on-demand pricing:

| Instance Type | On-Demand | Spot | Discount |
|--------------|-----------|------|----------|
| A6000 | $0.491/hr | $0.232/hr | ~53% |
| A100 | $1.99/hr | $1.05/hr | ~47% |
| Average Range | - | - | 50-70% |

**Trade-off**: Spot instances can be interrupted with short notice when capacity is needed.

*Source: [RunPod Spot vs On-Demand](https://www.runpod.io/blog/spot-vs-on-demand-instances-runpod)*

### Secure Cloud vs Community Cloud

| Feature | Secure Cloud | Community Cloud |
|---------|--------------|-----------------|
| **Data Center** | T3/T4 enterprise-grade | Distributed peer providers |
| **Uptime SLA** | 99.99% | High reliability (vetted hosts) |
| **Price Premium** | Standard rates | 20-30% cheaper |
| **Security** | SOC2 compliance options | Basic security |
| **Best For** | Production, enterprise | R&D, hobbyists, budget projects |

*Source: [RunPod Documentation](https://docs.runpod.io/pods/choose-a-pod)*

### Storage Pricing

| Storage Type | Running | Idle |
|--------------|---------|------|
| Container Disk | $0.10/GB/month | $0.20/GB/month |
| Network Volume (<1TB) | $0.07/GB/month | - |
| Network Volume (>1TB) | $0.05/GB/month | - |

**Note**: No ingress/egress fees on RunPod.

*Source: [RunPod Pricing](https://www.runpod.io/pricing)*

---

## GPU Technical Specifications

### Complete Specifications Comparison

| Specification | H100 SXM | A100 SXM | A100 PCIe | L40S |
|---------------|----------|----------|-----------|------|
| **Architecture** | Hopper | Ampere | Ampere | Ada Lovelace |
| **VRAM** | 80GB HBM3 | 80GB HBM2e | 80GB HBM2e | 48GB GDDR6 |
| **Memory Bandwidth** | 3.35 TB/s | 2.04 TB/s | 1.94 TB/s | 864 GB/s |
| **FP32 TFLOPS** | 60 | 19.5 | 19.5 | 91.6 |
| **TF32 Tensor** | 1000+ | 312 | 312 | 183/366* |
| **FP16/BF16** | High | 624 | 624 | 362/733* |
| **INT8 Tensor** | High | High | High | 366/733* |
| **FP8 Support** | Yes | No | No | Yes |
| **FP8 TFLOPS** | 2000+ | N/A | N/A | 733/1466* |
| **TDP (Power)** | 700W | 400W | 300W | 350W |
| **Tensor Cores** | 4th Gen | 3rd Gen | 3rd Gen | 4th Gen |
| **NVLink** | Yes (900 GB/s) | Yes (600 GB/s) | Bridge only (2 GPU) | No |
| **MIG Support** | Yes (7 instances) | Yes (7 instances) | Yes | No |
| **PCIe Gen** | 5.0 | 4.0 | 4.0 | 4.0 |

*\*With sparsity*

### Additional GPU Specs

| Specification | RTX 4090 | RTX 3090 | A40 |
|---------------|----------|----------|-----|
| **Architecture** | Ada Lovelace | Ampere | Ampere |
| **VRAM** | 24GB GDDR6X | 24GB GDDR6X | 48GB GDDR6 |
| **Memory Bandwidth** | 1008 GB/s | 936 GB/s | 696 GB/s |
| **FP32 TFLOPS** | 82.6 | 35.6 | 37.4 |
| **TDP (Power)** | 450W | 350W | 300W |
| **Tensor Cores** | 4th Gen | 3rd Gen | 3rd Gen |
| **FP8 Support** | Yes | No | No |

*Sources: [NVIDIA L40S Datasheet](https://resources.nvidia.com/en-us-l40s/l40s-datasheet-28413), [NVIDIA A100 Datasheet](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/nvidia-a100-datasheet-nvidia-us-2188504-web.pdf)*

---

## PCIe vs SXM Comparison

### Key Differences

| Feature | PCIe | SXM |
|---------|------|-----|
| **Form Factor** | Standard server slot | HGX baseboard module |
| **Memory Bandwidth** | 1.94 TB/s (A100) | 2.04 TB/s (A100) |
| **NVLink** | Bridge for 2 GPUs max | Full NVSwitch (up to 16 GPUs) |
| **GPU-to-GPU Bandwidth** | PCIe 4.0 (~64 GB/s) | NVLink (~600 GB/s) |
| **TDP** | 250-300W | 400-700W |
| **Multi-GPU Scaling** | Limited | Excellent |
| **Flexibility** | Drop-in to any server | Specialized infrastructure |
| **Cost** | Lower | Higher |

### Performance Difference

| Workload | PCIe | SXM | Difference |
|----------|------|-----|------------|
| Single GPU | Baseline | +13% | SXM faster |
| Two GPU (BERT training) | Baseline | +23% | NVLink advantage |
| Multi-GPU scaling | Limited | Linear | SXM far superior |

*Source: [Hyperstack A100 PCIe vs SXM Comparison](https://www.hyperstack.cloud/technical-resources/performance-benchmarks/nvidia-a100-pcie-vs-nvidia-a100-sxm-a-comprehensive-comparison)*

### When to Choose Each

**Choose PCIe when:**
- Single GPU workloads (most inference)
- Budget-conscious deployments
- Standard server infrastructure
- Smaller-scale AI/HPC tasks
- You need flexibility

**Choose SXM when:**
- Multi-GPU training at scale
- Large model training (70B+ parameters)
- Distributed deep learning
- Maximum performance required
- Cost is secondary to speed

---

## Workload Requirements

### Image Generation Models

| Model | Minimum VRAM | Recommended VRAM | Notes |
|-------|--------------|------------------|-------|
| **Stable Diffusion 1.5** | 4GB | 6GB | Fastest, most optimized |
| **Stable Diffusion 2.1** | 4GB | 6GB | Similar to SD 1.5 |
| **SDXL (base)** | 4GB | 12GB | 8GB for basic use |
| **SDXL + Refiner** | 8GB | 16GB | Refiner adds overhead |
| **FLUX** | 6GB* | 12-24GB | *NF4 quantized version |
| **FLUX (full precision)** | 16GB | 24GB+ | Much slower on low VRAM |

**Performance by GPU (SDXL 1024x1024):**

| GPU | Time per Image | Notes |
|-----|----------------|-------|
| RTX 4090 | 4.8 sec | Gold standard consumer |
| RTX 5090 | ~3.5 sec | ~30% faster than 4090 |
| L40S | ~5-6 sec | Close to 4090 |
| A100 | ~6-7 sec | Better for batch/training |

*Sources: [Tom's Hardware Benchmarks](https://www.tomshardware.com/pc-components/gpus/stable-diffusion-benchmarks), [SDXL System Requirements](https://gofind.ai/stable-diffusion/sdxl-system-requirements)*

### Video/Animation Generation

| Workload | Minimum VRAM | Recommended VRAM | GPU Recommendation |
|----------|--------------|------------------|-------------------|
| **AnimateDiff (512x512, 16 frames)** | 8GB | 12-16GB | RTX 3090/4090 |
| **AnimateDiff (512x768)** | 12GB | 16-24GB | RTX 4090, L40S |
| **AnimateDiff (1024p)** | 16GB | 24GB+ | L40S, A100 |
| **Small-scale (5-15s, 720p)** | 12GB | 24GB | RTX 3090/4090/cloud A30 |
| **Medium-scale (30-60s, 1080p)** | 24GB | 48GB | L40S, A100 |
| **Large-scale (multi-min, 4K+)** | 48GB+ | 80GB | H100, A100, multi-GPU |

**AnimateDiff specific notes:**
- Default test: 512x512, 16 frames on RTX 4090 with Torch 2.0
- RTX 3060 (12GB): Takes ~1 hour for 16 frames at 512x768
- Keep prompts under 75 tokens for proper motion

*Source: [Civitai AnimateDiff Guide](https://civitai.com/articles/3518/simple-guide-for-creating-video-with-animatediff)*

### TTS/Voice Synthesis

| Model | VRAM Usage | Notes |
|-------|------------|-------|
| **XTTS-v2 (Coqui)** | ~2.1GB inference | 5GB RAM also needed |
| **XTTS Fine-tuning** | 8GB minimum | Uses CUDA Sysmem fallback |
| **Bark** | ~4-6GB | Unconstrained voice cloning |
| **F5-TTS** | ~4-8GB | High-quality with cloning |

**TTS is lightweight** - most models run comfortably on 8GB VRAM GPUs.

**Performance tip**: When running TTS alongside LLMs (7B = 8GB VRAM), 4GB remaining VRAM is sufficient for XTTS without significant performance issues.

*Source: [Coqui TTS Documentation](https://docs.coqui.ai/en/latest/models/xtts.html)*

---

## Recommendations

### By Workload Type

#### Image Generation (SD, SDXL, Flux)

| Budget | Recommended GPU | Price/hr | Notes |
|--------|-----------------|----------|-------|
| **Minimal** | RTX 3090 (Community) | $0.14-0.22/hr | Best value for SD/SDXL |
| **Balanced** | RTX 4090 | $0.20-0.34/hr | Fast SDXL, good Flux |
| **Professional** | L40S | $0.40-0.79/hr | Best for Flux, FP8 support |
| **Production** | A100 80GB | $0.79-1.39/hr | Batch processing, training |

**Best Value**: RTX 4090 or L40S
- L40S has FP8 support = ~1.2x faster than A100 for Stable Diffusion inference
- RTX 4090 is cheapest for single-image generation

#### Video/Animation (AnimateDiff, etc.)

| Project Scale | Recommended GPU | Price/hr | Notes |
|---------------|-----------------|----------|-------|
| **Small (512p, 16 frames)** | RTX 4090 | $0.20-0.34/hr | 24GB sufficient |
| **Medium (1080p, 30-60s)** | L40S | $0.40-0.79/hr | 48GB headroom |
| **Large (4K, multi-min)** | A100 80GB | $0.79-1.39/hr | Memory bandwidth matters |

**Best Value**: L40S for most video work
- 48GB handles most models + ControlNets
- Cheaper than A100 with similar video gen performance

#### TTS/Voice Synthesis

| Use Case | Recommended GPU | Price/hr | Notes |
|----------|-----------------|----------|-------|
| **Simple TTS** | RTX A4000 | $0.09/hr | 16GB is plenty |
| **Voice Cloning** | RTX 3090 | $0.14-0.22/hr | 24GB for headroom |
| **Combined LLM+TTS** | RTX 4090 | $0.20-0.34/hr | Room for both models |

**Best Value**: RTX A4000 or RTX 3090
- TTS models are small (2-6GB VRAM)
- Overkill to use L40S/A100 for TTS alone

### GPU Selection Decision Tree

```
START
│
├─ Is this TTS/voice only?
│   └─ YES → RTX A4000 ($0.09/hr) or RTX 3090 ($0.14-0.22/hr)
│
├─ Is this image generation?
│   ├─ SD 1.5/2.1 → RTX 3090 ($0.14-0.22/hr)
│   ├─ SDXL → RTX 4090 ($0.20-0.34/hr)
│   └─ Flux → L40S ($0.40-0.79/hr) - FP8 advantage
│
├─ Is this video/animation?
│   ├─ Short clips (<30s) → RTX 4090 ($0.20-0.34/hr)
│   ├─ Medium (30s-2min) → L40S ($0.40-0.79/hr)
│   └─ Long/4K → A100 80GB ($0.79-1.39/hr)
│
├─ Do you need multi-GPU scaling?
│   ├─ YES → A100 SXM ($1.39/hr) or H100 SXM ($2.69/hr)
│   └─ NO → PCIe variants are fine
│
└─ Is this production/enterprise?
    ├─ YES → Secure Cloud + On-Demand
    └─ NO → Community Cloud + Spot instances
```

---

## Cost Optimization Strategies

### 1. Choose Community Cloud for Non-Critical Work

| Scenario | Secure Cloud | Community Cloud | Monthly Savings (100hr) |
|----------|--------------|-----------------|------------------------|
| A100 80GB | $139/month | $79/month | **$60** |
| L40S | $79/month | $40/month | **$39** |
| RTX 4090 | $34/month | $20/month | **$14** |

**Use Community Cloud for**: Development, experimentation, batch processing

### 2. Use Spot Instances for Batch Work

**Savings**: 50-70% off on-demand pricing

**Best for**:
- AI model training (checkpointed)
- Batch image generation
- Non-time-sensitive rendering
- Testing and development

**Not recommended for**:
- Real-time inference APIs
- Production services
- Time-sensitive deadlines

### 3. Right-Size Your GPU

| Mistake | Cost | Correct Choice | Savings |
|---------|------|----------------|---------|
| A100 for XTTS | $1.39/hr | RTX A4000 | **$1.30/hr (93%)** |
| H100 for SD 1.5 | $2.69/hr | RTX 3090 | **$2.47/hr (92%)** |
| A100 for SD images | $1.39/hr | RTX 4090 | **$1.05/hr (76%)** |

### 4. Consider Long-Term Commitments

| GPU | On-Demand | 6-Month | 1-Year | Savings |
|-----|-----------|---------|--------|---------|
| L40S | $0.79/hr | $0.731/hr | $0.705/hr | **11%** |
| A100 SXM | $1.39/hr | $1.27/hr | $1.22/hr | **12%** |
| A100 PCIe | $1.19/hr | $1.18/hr | $1.14/hr | **4%** |

### 5. Use Per-Second Billing

RunPod charges per-second, not per-hour. For bursty workloads:
- Spin up, process, spin down immediately
- No paying for idle time
- Ideal for serverless inference

### 6. Optimize Storage

| Strategy | Savings |
|----------|---------|
| Use Network Volumes over Container Disk | 30-50% for persistent data |
| Clean up stopped pods promptly | $0.20/GB/month → $0 |
| Use >1TB volumes | $0.07 → $0.05/GB (28% off) |

---

## Sources

### RunPod Official

- [RunPod Pricing](https://www.runpod.io/pricing) - Official pricing page
- [RunPod GPU Pricing](https://www.runpod.io/gpu-pricing) - Detailed GPU rates
- [RunPod Documentation - Pricing](https://docs.runpod.io/pods/pricing) - Technical details
- [RunPod Documentation - Choose a Pod](https://docs.runpod.io/pods/choose-a-pod) - Cloud tier comparison
- [Spot vs On-Demand Instances](https://www.runpod.io/blog/spot-vs-on-demand-instances-runpod) - Spot pricing guide
- [Choosing GPUs Guide](https://www.runpod.io/articles/comparison/choosing-gpus) - GPU comparison article
- [A100 Cloud Comparison](https://www.runpod.io/articles/comparison/a100-cloud-comparison) - A100 pricing analysis

### GPU Specifications

- [NVIDIA L40S Datasheet](https://resources.nvidia.com/en-us-l40s/l40s-datasheet-28413) - Official L40S specs
- [NVIDIA A100 Datasheet](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/nvidia-a100-datasheet-nvidia-us-2188504-web.pdf) - Official A100 specs
- [NVIDIA L40S Product Page](https://www.nvidia.com/en-us/data-center/l40s/) - L40S overview
- [NVIDIA A100 Product Page](https://www.nvidia.com/en-us/data-center/a100/) - A100 overview
- [A100 PCIe vs SXM Comparison](https://www.hyperstack.cloud/technical-resources/performance-benchmarks/nvidia-a100-pcie-vs-nvidia-a100-sxm-a-comprehensive-comparison) - Form factor comparison
- [DataCrunch A100 Comparison](https://datacrunch.io/blog/nvidia-a100-pcie-vs-sxm4-comparison) - PCIe vs SXM4 analysis

### Performance & Benchmarks

- [Tom's Hardware SD Benchmarks](https://www.tomshardware.com/pc-components/gpus/stable-diffusion-benchmarks) - 45 GPU comparison
- [L40S vs A100 for Inference](https://medium.com/mkinf/choosing-the-right-gpu-05953d541d48) - Performance analysis
- [L40S Replacing A100 for Inference](https://acecloud.ai/blog/nvidia-l40s-vs-a100-ai-inference/) - Use case comparison
- [L40S GPU Overview](https://gcore.com/learning/nvidia-l40s-overview) - Comprehensive specs

### Workload Requirements

- [SDXL System Requirements](https://gofind.ai/stable-diffusion/sdxl-system-requirements) - VRAM needs
- [SDXL Requirements Discussion](https://github.com/AUTOMATIC1111/stable-diffusion-webui/discussions/11713) - Community insights
- [Flux Low VRAM Guide](https://stable-diffusion-art.com/flux-forge/) - Optimization tips
- [Best GPU for SD/SDXL/Flux](https://techtactician.com/best-gpu-for-stable-diffusion-sdxl-and-flux/) - Buying guide
- [AnimateDiff Guide](https://civitai.com/articles/3518/simple-guide-for-creating-video-with-animatediff) - Video generation
- [AnimateDiff Beginner's Guide](https://education.civitai.com/beginners-guide-to-animatediff/) - Requirements
- [XTTS Documentation](https://docs.coqui.ai/en/latest/models/xtts.html) - TTS VRAM needs
- [XTTS VRAM Discussion](https://github.com/coqui-ai/TTS/discussions/3268) - Community benchmarks

### Pricing Comparisons

- [ComputePrices RunPod](https://computeprices.com/providers/runpod) - Price aggregator
- [FlexPrice RunPod Guide](https://flexprice.io/blog/runprod-pricing-guide-with-gpu-costs) - Pricing breakdown
- [Northflank Cloud GPU Providers](https://northflank.com/blog/cheapest-cloud-gpu-providers) - Market comparison
- [GetDeploying GPU Prices](https://getdeploying.com/gpus) - Multi-provider comparison

---

*Last updated: December 2025*
*Research conducted using web search and official documentation*
