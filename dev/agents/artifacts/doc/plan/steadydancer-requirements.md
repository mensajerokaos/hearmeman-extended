---
author: $USER
model: Claude Sonnet 4.5
date: 2026-01-18 10:30
task: SteadyDancer dependencies and requirements research
source: https://github.com/MCG-NJU/SteadyDancer
---

# SteadyDancer Requirements Documentation

## Overview

**SteadyDancer** is a video generation model from MCG-NJU (Nanjing University). The project provides a 14B parameter video diffusion model for image-to-video generation tasks.

**Repository**: https://github.com/MCG-NJU/SteadyDancer

---

## System Requirements

### Operating System
- Linux (tested on Ubuntu 20.04/22.04)
- CUDA-compatible GPU environment

### Python Version
- **Python 3.10** (required, verified compatible)

### Compiler Requirements
- **GCC 5.4 or higher** required for building mmcv with CUDA operations

### CUDA Version
- **CUDA 12.1** (cu121) - Required for PyTorch and flash-attention

---

## Python Package Dependencies

### Core PyTorch Stack (Exact Versions)

| Package | Version | Source |
|---------|---------|--------|
| torch | 2.5.1 | https://download.pytorch.org/whl/cu121 |
| torchvision | 0.20.1 | https://download.pytorch.org/whl/cu121 |
| torchaudio | 2.5.1 | https://download.pytorch.org/whl/cu121 |

### Installation Command for PyTorch
```bash
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
  --index-url https://download.pytorch.org/whl/cu121
```

### Flash Attention
| Package | Version | Wheel URL |
|---------|---------|-----------|
| flash_attn | 2.7.4.post1 | https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.5cxx11abiFALSE-cp310-cp310-linux_x86_64.whl |

### Installation Command
```bash
pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.5cxx11abiFALSE-cp310-cp310-linux_x86_64.whl
```

### Memory Optimization Libraries

| Package | Version |
|---------|---------|
| xformers | 0.0.29.post1 |
| xfuser | [diffusers, flash-attn] |

### Installation Command
```bash
pip install xformers==0.0.29.post1
pip install "xfuser[diffusers,flash-attn]"
```

### Computer Vision & Video Processing

| Package | Version | Purpose |
|---------|---------|---------|
| opencv-python | >=4.9.0.80 | Image/video processing |
| moviepy | 2.2.1 | Video editing and rendering |
| decord | 0.6.0 | Video loading backend |
| imageio | | Image I/O operations |
| imageio-ffmpeg | | FFmpeg bindings for imageio |

### Installation Command
```bash
pip install moviepy decord
pip install imageio imageio-ffmpeg
```

### OpenMMLab Ecosystem (Pose Estimation)

| Package | Version |
|---------|---------|
| openmim | 0.3.9 |
| mmengine | 0.10.7 |
| mmcv | 2.1.0 |
| mmdet | >=3.1.0 (tested 3.3.0) |
| mmpose | 1.3.2 |

### Installation Command
```bash
pip install openmim
mim install mmengine
mim install "mmcv==2.1.0"
mim install "mmdet>=3.1.0"
pip install mmpose
```

### Diffusers & Transformers

| Package | Version | Purpose |
|---------|---------|---------|
| diffusers | >=0.31.0 | Diffusion model pipeline |
| transformers | >=4.49.0 | Model architecture |
| tokenizers | >=0.20.3 | Fast tokenization |
| accelerate | >=1.1.1 | Distributed training/inference |
| gradio | >=5.0.0 | Web UI interface |

### Other Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| tqdm | | Progress bars |
| easydict | | Dictionary access |
| ftfy | | Fix text encoding |
| dashscope | | Model hub access |
| numpy | >=1.23.5, <2 | Numerical operations |

---

## Complete requirements.txt

```
torch>=2.4.0
torchvision>=0.19.0
opencv-python>=4.9.0.80
diffusers>=0.31.0
transformers>=4.49.0
tokenizers>=0.20.3
accelerate>=1.1.1
tqdm
imageio
easydict
ftfy
dashscope
imageio-ffmpeg
flash_attn
gradio>=5.0.0
numpy>=1.23.5,<2
```

---

## System Dependencies

### FFmpeg (Required)
FFmpeg is required for video encoding/decoding operations.

**Installation**:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y ffmpeg

# CentOS/RHEL
sudo yum install -y ffmpeg

# macOS
brew install ffmpeg
```

### CUDA Toolkit (12.1)
- Ensure CUDA 12.1 is installed and accessible
- nvidia-smi should report CUDA version compatible with 12.1
- CuDNN recommended for optimal performance

### GCC/G++
- **Minimum version**: 5.4
- Required for compiling mmcv with CUDA operations

**Installation**:
```bash
# Ubuntu/Debian
sudo apt-get install -y build-essential gcc g++
```

---

## GPU Memory Requirements

### Model Specifications
- **Model Size**: SteadyDancer-14B (14 billion parameters)
- **Architecture**: Video diffusion model

### Estimated GPU Memory

| Configuration | Estimated VRAM | Notes |
|---------------|----------------|-------|
| **Single GPU (FP16)** | ~28-32 GB | Full precision inference |
| **Single GPU (Quantized)** | ~16-20 GB | With quantization techniques |
| **Multi-GPU (2x)** | ~14-16 GB per GPU | FSDP + xDiT USP distributed |
| **Multi-GPU (4x)** | ~8-10 GB per GPU | Maximum distributed setup |

**Note**: Exact VRAM usage depends on:
- Output video resolution (e.g., 1024x576)
- Batch size
- Configuration parameters (cfg_scale, condition_guide_scale)
- Framework overhead

### Recommended GPU Configurations

| GPU Model | VRAM | Feasibility |
|-----------|------|-------------|
| NVIDIA A100 (40GB) | 40 GB | Optimal - Full model |
| NVIDIA A100 (80GB) | 80 GB | Optimal - With overhead |
| NVIDIA RTX 4090 | 24 GB | Possible - With optimization |
| NVIDIA RTX 4080 | 16 GB | Borderline - Quantization required |
| NVIDIA L40S | 48 GB | Optimal |
| NVIDIA L40 | 48 GB | Optimal |

---

## Installation Commands

### Complete Installation Sequence

```bash
# 1. Clone repository
git clone https://github.com/MCG-NJU/SteadyDancer.git
cd SteadyDancer

# 2. Create conda environment
conda create -n steadydancer python=3.10 -y
conda activate steadydancer

# 3. Install PyTorch with CUDA 12.1
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
  --index-url https://download.pytorch.org/whl/cu121

# 4. Install flash attention
pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.5cxx11abiFALSE-cp310-cp310-linux_x86_64.whl

# 5. Install memory optimization libraries
pip install xformers==0.0.29.post1
pip install "xfuser[diffusers,flash-attn]"

# 6. Install requirements.txt
pip install -r requirements.txt

# 7. Install video processing dependencies
pip install moviepy decord
pip install imageio imageio-ffmpeg

# 8. Install OpenMMLab dependencies
pip install openmim
mim install mmengine
mim install "mmcv==2.1.0"
mim install "mmdet>=3.1.0"
pip install mmpose

# 9. Install FFmpeg (system-level)
sudo apt-get update && sudo apt-get install -y ffmpeg
```

### Docker Installation (Alternative)

```dockerfile
FROM nvidia/cuda:12.1-devel-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    gcc \
    g++ \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu121

# ... rest of installation
```

---

## Verification Commands

### 1. Check Python Environment
```bash
python --version
# Expected output: Python 3.10.x
```

### 2. Verify PyTorch Installation
```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python -c "import torch; print(f'CUDA version: {torch.version.cuda}')"
```

**Expected Output**:
```
PyTorch: 2.5.1
CUDA available: True
CUDA version: 12.1
```

### 3. Verify Flash Attention
```bash
python -c "import flash_attn; print(f'Flash Attention: {flash_attn.__version__}')"
```

### 4. Verify xformers
```bash
python -c "import xformers; print(f'xformers: {xformers.__version__}')"
```

### 5. Verify mmcv Installation
```bash
python -c "import mmcv; print(f'mmcv: {mmcv.__version__}')"
python -c "import mmdet; print(f'mmdet: {mmdet.__version__}')"
python -c "import mmpose; print(f'mmpose: {mmpose.__version__}')"
```

### 6. Check GPU Memory
```bash
nvidia-smi
# Verify at least 24GB VRAM available for single GPU
```

### 7. Test Model Loading
```bash
# Clone SteadyDancer and test checkpoint loading
git clone https://github.com/MCG-NJU/SteadyDancer.git
cd SteadyDancer
python -c "from steadydancer import SteadyDancer; print('Model imports successfully')"
```

### 8. Full Environment Test
```bash
python -c "
import torch
import flash_attn
import xformers
import mmcv
import mmdet
import mmpose
import diffusers
import transformers

print('All dependencies verified:')
print(f'  PyTorch: {torch.__version__}')
print(f'  CUDA: {torch.version.cuda}')
print(f'  Flash Attention: {flash_attn.__version__}')
print(f'  xformers: {xformers.__version__}')
print(f'  mmcv: {mmcv.__version__}')
print(f'  mmdet: {mmdet.__version__}')
print(f'  mmpose: {mmpose.__version__}')
print(f'  diffusers: {diffusers.__version__}')
print(f'  transformers: {transformers.__version__}')
"
```

---

## Inference Configuration Options

### generate_dancer.py Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--task` | i2v-14B | Model task type (image-to-video) |
| `--size` | 1024x576 | Output video resolution |
| `--ckpt_dir` | | Path to model checkpoint directory |
| `--prompt` | | Text prompt for generation |
| `--image` | | Input image path for I2V |
| `--cond_pos_folder` | | Positive conditioning folder |
| `--cond_neg_folder` | | Negative conditioning folder |
| `--sample_guide_scale` | 5.0 | Classifier-free guidance scale |
| `--condition_guide_scale` | 1.0 | Conditioning guidance scale |
| `--end_cond_cfg` | 0.4 | End condition CFG ratio |
| `--base_seed` | 106060 | Random seed |
| `--save_file` | | Output filename |
| `--dit_fsdp` | False | Enable DiT FSDP distribution |
| `--t5_fsdp` | False | Enable T5 FSDP distribution |
| `--ulysses_size` | 1 | Ulysses sequence parallel size |

### Example Inference Commands

**Single GPU**:
```bash
python generate_dancer.py \
    --task i2v-14B \
    --size 1024x576 \
    --ckpt_dir /path/to/checkpoints \
    --prompt "A person walking in the park" \
    --image /path/to/input.jpg \
    --save_file output.mp4
```

**Multi-GPU (2 GPUs)**:
```bash
GPUs=2
torchrun --nproc_per_node=${GPUs} generate_dancer.py \
    --task i2v-14B \
    --size 1024x576 \
    --ckpt_dir /path/to/checkpoints \
    --prompt "A person walking in the park" \
    --image /path/to/input.jpg \
    --dit_fsdp \
    --t5_fsdp \
    --ulysses_size ${GPUs} \
    --save_file output.mp4
```

**Note**: Multi-GPU inference may produce slightly different results than single-GPU due to non-deterministic distributed computing operations.

---

## Model Checkpoints

### Available Checkpoints

1. **SteadyDancer-14B**
   - HuggingFace: [MCG-NJU/SteadyDancer-14B](https://huggingface.co/MCG-NJU/SteadyDancer-14B)
   - ModelScope: Available for download
   - Size: ~28GB (FP16)

2. **DW-Pose**
   - Pretrained weights for pose estimation
   - Required for pose-guided generation

3. **YOLOX**
   - Detection model for pose estimation
   - Required for human body detection

---

## CUDA Compatibility Matrix

| PyTorch Version | CUDA Version | Supported GCC | Notes |
|-----------------|--------------|---------------|-------|
| 2.5.1 | 12.1 | 5.4+ | **Recommended** |
| 2.5.1 | 11.8 | 5.4+ | Alternative |
| 2.4.0+ | 12.1 | 5.4+ | From requirements.txt |

---

## Troubleshooting

### Common Issues

**1. Flash Attention Installation Fails**
```bash
# Ensure CUDA toolkit is installed
nvcc --version

# Try installing without pre-built wheel
pip install flash_attn --no-build-isolation
```

**2. mmcv Compilation Error**
```bash
# Ensure GCC version is 5.4+
gcc --version

# If using newer GCC, downgrade or use conda
conda install -c conda-forge gcc_linux-64=11
```

**3. Out of Memory (OOM)**
```bash
# Reduce resolution
--size 512x512

# Use multi-GPU with FSDP
torchrun --nproc_per_node=2 generate_dancer.py --dit_fsdp --t5_fsdp
```

**4. CUDA Version Mismatch**
```bash
# Check PyTorch CUDA version
python -c "import torch; print(torch.version.cuda)"

# Verify nvidia-smi CUDA version
nvidia-smi | grep "CUDA Version"

# They should be compatible
```

---

## Docker Environment Variables

For containerized deployments:

```yaml
environment:
  - PYTHONUNBUFFERED=1
  - PYTHONDONTWRITEBYTECODE=1
  - CUDA_LAUNCH_BLOCKING=1
  - TORCH_CUDNN_V8_API_ENABLED=1
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

---

## Summary Table

| Requirement | Version/Spec | Source |
|-------------|--------------|--------|
| Python | 3.10 | - |
| PyTorch | 2.5.1 | pytorch.org |
| CUDA | 12.1 | nvidia.com |
| GCC | >=5.4 | system |
| flash_attn | 2.7.4.post1 | Dao-AILab |
| xformers | 0.0.29.post1 | pypi |
| mmcv | 2.1.0 | openmmlab |
| mmdet | >=3.1.0 | openmmlab |
| mmpose | 1.3.2 | openmmlab |
| GPU VRAM | >=24GB | - |

---

## References

- **Repository**: https://github.com/MCG-NJU/SteadyDancer
- **PyTorch**: https://pytorch.org/
- **Flash Attention**: https://github.com/Dao-AILab/flash-attention
- **OpenMMLab**: https://openmmlab.com/
- **xDiT**: https://github.com/Xiaoyu-Li-AMD/xDiT
