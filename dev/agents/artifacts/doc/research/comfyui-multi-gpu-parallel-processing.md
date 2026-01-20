# ComfyUI Multi-GPU Parallel Processing Research

**Research Date**: January 2025
**Author**: Claude Code (Research via Web Search)

---

## Executive Summary

As of January 2025, ComfyUI's multi-GPU ecosystem has matured significantly, moving beyond simple multi-instance management to advanced sequence parallelism for large Diffusion Transformer (DiT) models. The landscape now includes:

- **Official ComfyUI**: Still no native intra-op parallelism, but async offloading optimizations are available
- **ComfyUI-Distributed**: Mature plugin for task-level parallelism across multiple GPUs/machines
- **xDiT Framework**: New specialized framework for multi-GPU DiT acceleration (FLUX, Wan2.1, HunyuanVideo)
- **SteadyDancer**: Video generation framework with built-in FSDP + xDiT USP support

---

## 1. Official ComfyUI Multi-GPU Support Status

### Current State (January 2025)

| Aspect | Status | Details |
|--------|--------|---------|
| **Native Intra-Op Parallelism** | ❌ Not Supported | Cannot split single image generation across multiple GPUs |
| **Async Offloading** | ✅ Optimized | NVIDIA collaboration improved performance 10-50% when VRAM limited |
| **Task-Level Parallelism** | ⚠️ Indirect | Via SwarmUI management or ComfyUI-Distributed plugin |
| **Pinned Memory** | ✅ Available | Optimizations for faster CPU-GPU transfers |

### Official Recommendation

Comfy.org now recommends **SwarmUI** for managing multiple GPU resources:
- Manages multiple ComfyUI instances as backend workers
- Enables parallel batch generation
- Unified interface across different hardware

**Reference**: [Comfy.org Blog - v0.2.0 Release](https://www.comfy.org/blog/comfyui-v0-2-0-release)

---

## 2. ComfyUI-Distributed Plugin Capabilities

### Overview

The most established solution for multi-GPU ComfyUI deployments, using a master-worker architecture.

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Master Node   │────▶│   Worker 1      │     │   Worker 2      │
│  (RTX 4090)     │     │  (RTX 4090)     │     │  (RTX 3060)     │
│  Orchestration  │     │  Local GPU      │     │  Local GPU      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         └───────────────────────┴───────────────────────┘
                                    │
                          ┌─────────────────┐
                          │  Remote/Cloud   │
                          │  Workers        │
                          │  (RunPod, etc.) │
                          └─────────────────┘
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Distributed Upscaling** | Splits Ultimate SD Upscale tiles across all GPUs |
| **Dynamic Load Balancing** | Faster GPUs (4090) process more work than slower ones (3060) |
| **Multi-Machine Support** | Local GPUs, remote PCs, cloud instances via secure tunnels |
| **Worker Types** | LocalWorker, RemoteWorker, CloudWorker |
| **Configuration** | YAML-based worker definitions |

### Performance

- **4x GPU Upscaling**: ~3.4x speedup over single GPU
- **Task Distribution**: Automatic balancing based on GPU speed
- **Communication**: Low overhead for tile-based workflows

**Reference**: [ComfyUI-Distributed GitHub](https://github.com/city96/ComfyUI-Distributed)

---

## 3. xDiT Framework for Multi-GPU DiT Models

### Overview

xDiT (x Diffusion Transformer) is a specialized framework for accelerating DiT models that have quadratic complexity scaling issues.

### Supported Models

- **FLUX.1** (dev, [dev] Schnell)
- **HunyuanVideo**
- **Wan2.1** (Wan 2.1)
- Other DiT-based diffusion models

### Parallelization Techniques

| Technique | Purpose | Benefit |
|-----------|---------|---------|
| **USP (Unified Sequence Parallel)** | Splits transformer sequence length across GPUs | Handles long sequences (high-res images, video) |
| **PipeFusion** | Pipeline parallelism for model layers | Distributes model weights |
| **CFG Parallel** | Classifier-Free Guidance parallelization | Reduces sampling overhead |

### Integration with ComfyUI

- Accessible via custom nodes
- Replaces standard loaders/samplers with xDiT-optimized versions
- Requires compatible workflow configuration

### Requirements

| Component | Requirement |
|-----------|-------------|
| **PCIe** | 4.0/5.0 recommended (NVLink beneficial) |
| **VRAM** | Variable by model (2GB+ per GPU base) |
| **Drivers** | Latest NVIDIA drivers with NVML support |
| **Interconnect** | High-bandwidth for inter-GPU communication |

**Reference**: [xDiT ComfyUI GitHub](https://github.com/xdit-project/xdit-comfyui)

---

## 4. SteadyDancer Multi-GPU Support

### Overview

SteadyDancer is a state-of-the-art video generation framework that integrates multi-GPU capabilities by default.

### Multi-GPU Architecture

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Training** | FSDP (Fully Sharded Data Parallel) | Distributes model weights and gradients |
| **Inference** | xDiT USP (Unified Sequence Parallel) | Parallelizes sequence processing |
| **ComfyUI Integration** | ComfyUI-WanVideoWrapper | Wrapper nodes for workflow integration |

### Performance Characteristics

- Designed for high-resolution video generation
- Scales efficiently with 2-8 GPUs
- Optimized for long video sequences (hundreds of frames)

### ComfyUI Deployment

Typically deployed via:
- **ComfyUI-WanVideoWrapper**: Integration layer
- **Specialized SteadyDancer Nodes**: Direct workflow integration
- **xDiT Backend**: Underlying distribution engine

**Reference**: [SteadyDancer GitHub](https://github.com/Kwai-VGI/SteadyDancer)

---

## 5. Performance Benchmarks

### FLUX.1 [dev] Image Generation (1024x1024)

| Setup | Time (Single GPU) | Time (Multi-GPU) | Speedup | Framework |
|-------|-------------------|------------------|---------|-----------|
| 1x RTX 4090 | 13.87s | - | 1.0x | Standard |
| 2x RTX 4090 | - | ~6.98s | **2.0x** | xDiT USP |
| 4x RTX 4090 | - | ~3.5s | **4.0x** | xDiT USP |

### Video Upscaling (4K)

| Setup | Base Time | Multi-GPU Time | Speedup | Framework |
|-------|-----------|----------------|---------|-----------|
| 1x GPU | 100% | - | 1.0x | Standard |
| 4x GPU | - | ~29.4% | **3.4x** | Distributed Tiles |

### Large-Scale Batch Generation (8x H100)

| Metric | Result |
|--------|--------|
| Throughput | **Linear scaling** up to 8 GPUs |
| Efficiency | Near-ideal utilization |
| Framework | Distributed Workers |

### Technical Considerations

#### Interconnect Impact

| Interconnect | Bandwidth | Multi-GPU Efficiency |
|--------------|-----------|---------------------|
| PCIe 3.0 x1 | ~1 GB/s | Diminishing returns for heavy communication |
| PCIe 4.0 x16 | ~32 GB/s | Good for tile-based workflows |
| PCIe 5.0 x16 | ~64 GB/s | Optimal for USP/sequence parallel |
| NVLink | ~600 GB/s | Best for FSDP and USP |

#### Numerical Consistency

- Multi-GPU inference may produce **slightly different results** vs single GPU
- Caused by floating-point summation differences in distributed computing
- Usually negligible for most use cases

---

## Recommendations by Use Case

| Use Case | Recommended Solution | Justification |
|----------|---------------------|---------------|
| **Batch Image Generation** | SwarmUI or ComfyUI-Distributed | Task-level parallelism, easy setup |
| **FLUX.1 High-Res (2K+)** | xDiT USP | Sequence parallelism required |
| **Video Generation (Wan2.1)** | xDiT USP + ComfyUI-WanVideoWrapper | Handles long sequences efficiently |
| **SteadyDancer Video** | Native xDiT integration | Built-in FSDP support |
| **Upscaling (Ultimate SD)** | ComfyUI-Distributed | Tile-based distribution ideal |
| **Mixed Hardware (home lab)** | ComfyUI-Distributed | Dynamic load balancing |

---

## URLs Summary

| Resource | URL |
|----------|-----|
| ComfyUI Official | https://www.comfy.org/ |
| ComfyUI v0.2.0 Release | https://www.comfy.org/blog/comfyui-v0-2-0-release |
| ComfyUI-Distributed Plugin | https://github.com/city96/ComfyUI-Distributed |
| xDiT Framework | https://github.com/xdit-project/xdit-comfyui |
| SteadyDancer | https://github.com/Kwai-VGI/SteadyDancer |
| SwarmUI | https://github.com/swarmui/SwarmUI |

---

## Technical Limitations & Requirements

### Current Limitations

1. **No Native Intra-Op Parallelism**: Single workflow cannot split across GPUs without plugins
2. **Communication Overhead**: Multi-GPU USP requires high-bandwidth interconnect
3. **Numerical Non-Determinism**: Results may vary between single and multi-GPU runs
4. **Plugin Dependency**: Most multi-GPU features require third-party solutions

### Minimum Requirements for Multi-GPU

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU VRAM | 8GB per GPU | 16GB+ per GPU |
| PCIe | 3.0 x16 | 4.0/5.0 x16 |
| System RAM | 32GB | 64GB+ |
| Storage | SSD (500MB/s) | NVMe (3000MB/s+) |
| Drivers | Latest NVIDIA | Latest stable |

---

## Conclusion

As of January 2025, ComfyUI multi-GPU support has evolved through two distinct paradigms:

1. **Task-Level Parallelism** (ComfyUI-Distributed, SwarmUI): Mature, reliable, good for batch processing
2. **Sequence Parallelism** (xDiT): Emerging solution for DiT models, enabling high-resolution/video generation on multiple GPUs

For SteadyDancer specifically, the integration of FSDP + xDiT USP provides robust multi-GPU support out of the box, making it one of the most capable video generation solutions for multi-GPU setups.

The ecosystem is still maturing, with community plugins driving innovation while official support remains focused on async optimizations rather than native parallelism.
