---
author: $USER
model: Claude-Sonnet-4.5
date: 2026-01-18
task: Research TurboDiffusion dependencies and requirements
status: completed
---

# TurboDiffusion Requirements & Integration Guide

## Overview

TurboDiffusion is a high-performance diffusion acceleration framework developed by thu-ml that achieves **100-200× speedup** in end-to-end video generation on a single RTX 5090 GPU. It integrates with Wan2.1 models (T2V and I2V) and is designed for production deployment on RunPod with ComfyUI-WanVideoWrapper.

## Repository Information

- **GitHub**: https://github.com/thu-ml/TurboDiffusion
- **Paper**: [TurboDiffusion: Fast Diffusion Video Generation via Efficient Denoising](https://arxiv.org/abs/2512.07601)
- **Released**: December 2025

---

## System Requirements

### Python Environment
- **Python Version**: >= 3.9 (3.12 recommended)
- **PyTorch Version**: >= 2.7.0
- **Recommended PyTorch**: 2.8.0 (higher versions may cause OOM)

### GPU Requirements

| GPU Type | Memory | Checkpoint Type | Flags |
|----------|--------|-----------------|-------|
| NVIDIA H100 | >40GB | Unquantized | Remove `--quant_linear` |
| NVIDIA RTX 5090 | 32GB | Quantized | Add `--quant_linear` |
| NVIDIA RTX 4090 | 24GB | Quantized | Add `--quant_linear` |

**Note**: Quantized checkpoints require `--quant_linear` flag; unquantized checkpoints should be used without this flag.

---

## Dependencies

### Core Dependencies

```bash
# Create conda environment
conda create -n turbodiffusion python=3.12
conda activate turbodiffusion

# Install PyTorch (>=2.7.0, 2.8.0 recommended)
pip install torch>=2.7.0
# OR specific version
pip install torch==2.8.0
```

### Installation Methods

#### Method 1: pip install (Recommended)
```bash
pip install turbodiffusion --no-build-isolation
```

#### Method 2: Build from Source
```bash
git clone https://github.com/thu-ml/TurboDiffusion.git
cd TurboDiffusion
git submodule update --init --recursive
pip install -e . --no-build-isolation
```

### SageSLA Acceleration (Recommended for Speed)
```bash
pip install git+https://github.com/thu-ml/SpargeAttn.git --no-build-isolation
```

### Training Dependencies (Optional)
```bash
pip install megatron-core hydra-core wandb webdataset
pip install --no-build-isolation transformer_engine[pytorch]
```

---

## Model Checkpoints

### Required Files

All checkpoints must be downloaded to the `checkpoints/` directory:

```bash
mkdir -p checkpoints
cd checkpoints
```

### Wan2.1 T2V (Text-to-Video)

**For RTX 5090/4090 (Quantized):**
```bash
# Download VAE (required)
wget https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/resolve/main/Wan2.1_VAE.pth

# Download text encoder (required)
wget https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/resolve/main/models_t5_umt5-xxl-enc-bf16.pth

# Download TurboDiffusion model
wget https://huggingface.co/TurboDiffusion/TurboWan2.1-T2V-1.3B-480P/resolve/main/TurboWan2.1-T2V-1.3B-480P-quant.pth
```

**For H100 (Unquantized):**
```bash
# Same VAE and text encoder
wget https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/resolve/main/Wan2.1_VAE.pth
wget https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/resolve/main/models_t5_umt5-xxl-enc-bf16.pth

# Unquantized model (no -quant suffix)
wget https://huggingface.co/TurboDiffusion/TurboWan2.1-T2V-1.3B-480P/resolve/main/TurboWan2.1-T2V-1.3B-480P.pth
```

### Wan2.2 I2V (Image-to-Video)

**For RTX 5090/4090 (Quantized):**
```bash
# Download VAE and text encoder
wget https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/resolve/main/Wan2.1_VAE.pth
wget https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/resolve/main/models_t5_umt5-xxl-enc-bf16.pth

# Download low-noise and high-noise models
wget https://huggingface.co/TurboDiffusion/TurboWan2.2-I2V-A14B-720P/resolve/main/TurboWan2.2-I2V-A14B-low-720P-quant.pth
wget https://huggingface.co/TurboDiffusion/TurboWan2.2-I2V-A14B-720P/resolve/main/TurboWan2.2-I2V-A14B-high-720P-quant.pth
```

---

## Performance Benchmarks

### Speedup Claims

TurboDiffusion achieves **100-200× speedup** in end-to-end diffusion generation on a single RTX 5090 GPU.

### Measured Results (RTX 5090)

**E2E = End-to-End diffusion latency (excluding text encoding and VAE decoding)**

| Model | Resolution | Original E2E | TurboDiffusion E2E | Speedup |
|-------|------------|--------------|-------------------|---------|
| Wan-2.1-T2V-1.3B | 480p | 184s | 1.9s | ~97× |
| Wan-2.1-T2V-14B | 480p | 1676s | 9.9s | ~169× |
| Wan-2.1-T2V-14B | 720p | 4767s | 24s | ~199× |
| Wan-2.2-I2V-A14B | 720p | 4549s | 38s | ~120× |

### Comparison with FastVideo

| Model | FastVideo | TurboDiffusion | Improvement |
|-------|-----------|----------------|-------------|
| Wan-2.1-T2V-1.3B-480P | 5.3s | 1.9s | 2.8× faster |
| Wan-2.1-T2V-14B-720P | 72.6s | 24s | 3.0× faster |
| Wan-2.1-T2V-14B-480P | 26.3s | 9.9s | 2.7× faster |

---

## Usage Examples

### Text-to-Video Inference

```bash
export PYTHONPATH=turbodiffusion

python turbodiffusion/inference/wan2.1_t2v_infer.py \
  --model Wan2.1-1.3B \
  --dit_path checkpoints/TurboWan2.1-T2V-1.3B-480P-quant.pth \
  --resolution 480p \
  --prompt "A stylish woman walks down a Tokyo street filled with warm glowing neon and animated signs. She wears a black leather jacket, long red dress, and high heels." \
  --num_samples 1 \
  --num_steps 4 \
  --quant_linear \
  --attention_type sagesla \
  --sla_topk 0.1
```

**Key Parameters:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--model` | Model name (Wan2.1-1.3B, Wan2.1-14B) | Required |
| `--dit_path` | Path to TurboDiffusion checkpoint | Required |
| `--resolution` | Output resolution (480p, 720p) | Required |
| `--prompt` | Text prompt for generation | Required |
| `--num_samples` | Number of samples to generate | 1 |
| `--num_steps` | Sampling steps (1-4) | 4 |
| `--quant_linear` | Use quantized linear layers | Required for RTX 5090/4090 |
| `--attention_type` | Attention type (original, sla, sagesla) | sagesla |
| `--sla_topk` | Top-k ratio for SLA (0.0-1.0) | 0.1 |
| `--ode` | Use ODE sampling (sharper, less robust) | False |

### Image-to-Video Inference

```bash
export PYTHONPATH=turbodiffusion

python turbodiffusion/inference/wan2.2_i2v_infer.py \
  --model Wan2.2-A14B \
  --low_noise_model_path checkpoints/TurboWan2.2-I2V-A14B-low-720P-quant.pth \
  --high_noise_model_path checkpoints/TurboWan2.2-I2V-A14B-high-720P-quant.pth \
  --resolution 720p \
  --adaptive_resolution \
  --image_path assets/i2v_inputs/i2v_input_0.jpg \
  --prompt "POV selfie video of a person in a moving car, natural lighting, real-world footage, high quality." \
  --num_samples 1 \
  --num_steps 4 \
  --quant_linear \
  --attention_type sagesla \
  --sla_topk 0.1
```

---

## ComfyUI-WanVideoWrapper Integration

### Overview

ComfyUI-WanVideoWrapper is the official ComfyUI extension for Wan2.1 and TurboDiffusion models, enabling workflow-based video generation with visual node interface.

**Repository**: Integration with TurboDiffusion allows:
- 4-step inference (vs 50+ steps in original)
- Real-time workflow preview
- ControlNet integration
- Reference image support

### Integration Architecture

```
ComfyUI UI
    ↓
WanVideoWrapper Nodes
    ↓
TurboDiffusion Inference Engine
    ↓
Wan2.1 Model Checkpoints
    ↓
Output Video
```

### Workflow Nodes

**Core Nodes:**
- `WanVideoLoader` - Load T2V/I2V models
- `WanVideoSampler` - 4-step sampling with TurboDiffusion
- `VAELoader` - Load WAN VAE
- `TextEncoder` - Load T5 text encoder

**Advanced Nodes:**
- `ControlNetLoader` - Load ControlNet for pose/mask control
- `ReferenceAttnProcessor` - Reference image conditioning
- `ControlVideo` - Video ControlNet integration

### Installation in ComfyUI

```bash
# Navigate to ComfyUI custom nodes
cd ComfyUI/custom_nodes/

# Clone WanVideoWrapper
git clone https://github.com/yourmeng-xx/ComfyUI-WanVideoWrapper.git
cd ComfyUI-WanVideoWrapper

# Install dependencies
pip install -r requirements.txt
```

### RunPod Integration

For RunPod deployment with ComfyUI-WanVideoWrapper:

```bash
# In Dockerfile, after ComfyUI installation
RUN cd ComfyUI/custom_nodes && \
    git clone https://github.com/yourmeng-xx/ComfyUI-WanVideoWrapper.git && \
    cd ComfyUI-WanVideoWrapper && \
    pip install -r requirements.txt

# Environment variables
ENV ENABLE_TURBO=true
ENV TURBO_STEPS=4
ENV ATTENTION_TYPE=sagesla
```

### Workflow Configuration

**Text-to-Video Workflow:**
1. `WanVideoLoader` → Loads TurboDiffusion checkpoint
2. `CLIPTextEncode` → Text prompt encoding
3. `WanVideoSampler` → 4-step sampling
4. `VAEDecode` → Decode latent to video
5. `SaveVideo` → Output .mp4 file

**Image-to-Video Workflow:**
1. `WanVideoLoader` → Loads I2V model
2. `LoadImage` → Input image
3. `CLIPTextEncode` → Motion prompt
4. `WanVideoSampler` → I2V sampling
5. `VAEDecode` → Output video

---

## StealthDancer Integration

TurboDiffusion integrates with SteadyDancer for motion-aware video generation:

### Dependencies
- `ComfyUI-WanVideoWrapper`
- DWPose (IDEA-Research) for motion extraction
- TurboDiffusion (100-200× acceleration)

### Workflow
```
Reference Image → DWPose (Pose Extraction) → SteadyDancer → Output Video
```

### VRAM Requirements
- FP16: ~28GB
- FP8: ~14GB
- GGUF: Available for low VRAM

---

## Troubleshooting

### Out of Memory (OOM)

**Problem**: CUDA out of memory errors

**Solutions:**
1. Use quantized checkpoints (`-quant` suffix) with `--quant_linear`
2. Reduce resolution (480p instead of 720p)
3. Use `--attention_type sagesla` with `--sla_topk 0.15`
4. Reduce `--num_samples` to 1

### Slow Inference

**Problem**: Inference slower than expected

**Solutions:**
1. Ensure `--attention_type sagesla` is set
2. Verify `--quant_linear` is used for RTX 5090/4090
3. Check GPU utilization with `nvidia-smi`
4. Use `--num_steps 4` (fewer steps = faster but less quality)

### Import Errors

**Problem**: Module not found errors

**Solutions:**
1. Ensure `PYTHONPATH=turbodiffusion` is set
2. Reinstall with `--no-build-isolation`
3. Update submodules: `git submodule update --init --recursive`

---

## RunPod Deployment Checklist

- [ ] GPU: RTX 4090 (24GB) or RTX 5090 (32GB)
- [ ] Python: >= 3.9, 3.12 recommended
- [ ] PyTorch: >= 2.7.0, 2.8.0 recommended
- [ ] Downloaded model checkpoints
- [ ] Installed `turbodiffusion` package
- [ ] Installed `SpargeAttn` for SageSLA
- [ ] ComfyUI-WanVideoWrapper extension
- [ ] R2 output sync configured (if persistence needed)

---

## References

- **TurboDiffusion GitHub**: https://github.com/thu-ml/TurboDiffusion
- **TurboDiffusion Paper**: https://arxiv.org/abs/2512.07601
- **SpargeAttn**: https://github.com/thu-ml/SpargeAttn
- **Wan2.1 Models**: https://huggingface.co/TurboDiffusion
- **ComfyUI-WanVideoWrapper**: (Check GitHub for latest)
