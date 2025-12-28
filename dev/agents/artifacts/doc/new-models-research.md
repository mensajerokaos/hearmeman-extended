# RunPod AI Model Deployment Research

## Table of Contents
1. [Genfocus (Generative Refocusing)](#1-genfocus-generative-refocusing)
2. [InfCam (Camera-Controlled Video Generation)](#2-infcam-camera-controlled-video-generation)
3. [MVInverse (Multi-view Inverse Rendering)](#3-mvinverse-multi-view-inverse-rendering)
4. [ComfyUI Custom Nodes Status](#4-comfyui-custom-nodes-status)
5. [Deployment Checklist](#5-deployment-checklist)
6. [References](#6-references)

---

## 1. Genfocus (Generative Refocusing)

**Description:** A flexible defocus control framework from a single image.

*   **Python Version:** `3.12`
*   **CUDA Version:** Not explicitly stated, but implies compatibility with recent PyTorch versions (likely 12.x).
*   **VRAM Requirements:** Not explicitly specified, but runs standard diffusion-based components (DeblurNet, BokehNet). Estimate >12GB for safety.

**Model Weights:**
| File | Size | URL |
| :--- | :--- | :--- |
| `bokehNet.safetensors` | TBD | `https://huggingface.co/nycu-cplab/Genfocus-Model/resolve/main/bokehNet.safetensors` |
| `deblurNet.safetensors` | TBD | `https://huggingface.co/nycu-cplab/Genfocus-Model/resolve/main/deblurNet.safetensors` |
| `depth_pro.pt` | TBD | `https://huggingface.co/nycu-cplab/Genfocus-Model/resolve/main/checkpoints/depth_pro.pt` |

**Pip Dependencies:**
*   `requirements.txt` (File not directly accessible, but standard command provided)

**Installation Commands:**
```bash
git clone git@github.com:rayray9999/Genfocus.git
cd Genfocus
conda create -n Genfocus python=3.12
conda activate Genfocus
pip install -r requirements.txt
```

**Usage Example:**
```bash
# Download weights
wget https://huggingface.co/nycu-cplab/Genfocus-Model/resolve/main/bokehNet.safetensors
wget https://huggingface.co/nycu-cplab/Genfocus-Model/resolve/main/deblurNet.safetensors
mkdir -p checkpoints
cd checkpoints
wget https://huggingface.co/nycu-cplab/Genfocus-Model/resolve/main/checkpoints/depth_pro.pt
cd ..

# Run Gradio Demo
python demo.py
```

---

## 2. InfCam (Camera-Controlled Video Generation)

**Description:** Infinite-Homography as robust conditioning for camera-controlled video generation.

*   **Python Version:** `3.12`
*   **CUDA Version:** `12.1`
*   **VRAM Requirements:**
    *   **Inference:** > 50 GB (Requires A100/H100 class GPU, e.g., 80GB VRAM).
    *   **Training:** ~52-56 GB per GPU (Multi-GPU setup recommended).

**Model Weights:**
| Model | Source |
| :--- | :--- |
| Wan2.1 | `python download_wan2.1.py` |
| UniDepth-v2-vitl14 | `https://huggingface.co/lpiccinelli/unidepth-v2-vitl14` |
| InfCam Checkpoint | `https://huggingface.co/emjay73/InfCam` |

**Pip Dependencies:**
`torch torchvision (cu121)`, `cupy-cuda12x`, `transformers==4.46.2`, `sentencepiece`, `controlnet-aux==0.0.7`, `imageio[ffmpeg]`, `safetensors`, `einops`, `protobuf`, `modelscope`, `ftfy`, `lpips`, `lightning`, `pandas`, `matplotlib`, `wandb`, `ffmpeg-python`, `numpy`, `opencv-python`.

**Installation Commands:**
```bash
conda create -n infcam python=3.12
conda activate infcam
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install cupy-cuda12x transformers==4.46.2 sentencepiece controlnet-aux==0.0.7 imageio imageio[ffmpeg] safetensors einops protobuf modelscope ftfy lpips lightning pandas matplotlib wandb ffmpeg-python numpy opencv-python
conda install -c conda-forge ffmpeg
```

**Usage Example:**
```bash
# Download models
python download_wan2.1.py
cd models
git clone https://huggingface.co/lpiccinelli/unidepth-v2-vitl14
git clone https://huggingface.co/emjay73/InfCam
cd ..

# Run Inference
bash run_inference.sh
```

---

## 3. MVInverse (Multi-view Inverse Rendering)

**Description:** Feed-forward multi-view inverse rendering.

*   **Python Version:** Compatible with PyTorch 2.5.1 (likely 3.10+).
*   **CUDA Version:** `11.8`
*   **VRAM Requirements:** Not specified.

**Model Weights:**
*   Uses inference checkpoints passed via `--ckpt`.

**Pip Dependencies:**
`torch==2.5.1`, `torchvision==0.20.1`, `torchaudio==2.5.1`, `opencv-python`, `huggingface_hub==0.35.0`

**Installation Commands:**
```bash
git clone https://github.com/Maddog241/mvinverse.git
cd mvinverse
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu118
pip install opencv-python huggingface_hub==0.35.0
```

**Usage Example:**
```bash
python inference.py --data_path examples/Courtroom --save_path output_dir
```

---

## 4. ComfyUI Custom Nodes Status

| Model | ComfyUI Support | Notes |
| :--- | :--- | :--- |
| **Qwen-Image-Edit-2511** | **Native/Workflow** | No single custom node required. Use `CLIPLoader` with the specific CLIP model (`qwen_2.5_vl_7b_fp8_scaled.safetensors`) and instruction-based editing workflows. |
| **Genfocus** | **None Found** | Requires custom node development or wrapping the python inference script. |
| **InfCam** | **None Found** | High VRAM usage makes it a candidate for a dedicated server rather than a simple local node. No existing wrapper found. |
| **MVInverse** | **None Found** | Requires custom node development. |

---

## 5. Deployment Checklist

*   [ ] **GPU Selection:**
    *   **InfCam:** MUST use **A100 80GB** or **H100 80GB** due to >50GB VRAM requirement.
    *   **Genfocus/MVInverse:** Likely compatible with standard 24GB cards (3090/4090) or A6000, but test to confirm.
*   [ ] **Container Setup:**
    *   Base Image: CUDA 12.1 (supports InfCam & Genfocus best). MVInverse requests CUDA 11.8 but PyTorch 2.5.1 often supports newer CUDA; verify backward compatibility or use separate envs.
*   [ ] **Storage:**
    *   Ensure enough disk space for `InfCam` weights (Wan2.1 + UniDepth + Checkpoints). Estimate 50GB+ storage.

---

## 6. FlashPortrait (Portrait Animation)

**Description:** End-to-end video diffusion transformer for ID-preserving, infinite-length portrait videos with 6x inference acceleration.

*   **Python Version:** 3.8+
*   **CUDA Version:** `12.4`
*   **PyTorch:** 2.6.0, torchvision 0.21.0, torchaudio 2.1.1

**VRAM Requirements:**
| Mode | VRAM | Notes |
| :--- | :--- | :--- |
| Full model (720x1280, 10s) | ~60GB | A100 80G required |
| Sequential CPU offload | ~10GB | + CPU swap |
| Model CPU offload | ~30GB | Half of full-load |

**Model Weights:**
| Model | Source |
| :--- | :--- |
| FlashPortrait | `FrancisRing/FlashPortrait` (HuggingFace) |
| Wan2.1-14B-720P | `Wan-AI/Wan2.1-I2V-14B-720P` (HuggingFace) |

**Installation:**
```bash
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.1.1 --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
pip install flash_attn  # Optional acceleration
```

**GPU Memory Modes:**
- `model_full_load` - Full VRAM (60GB)
- `sequential_cpu_offload` - 10GB GPU + CPU
- `model_cpu_offload` - ~30GB GPU

**Supported Resolutions:** 480×832, 832×480, 512×512, 720×720, 720×1280, 1280×720

---

## 7. StoryMem (Multi-Shot Video Storytelling)

**Description:** Memory-conditioned video generation for coherent minute-long multi-shot videos with persistent character consistency.

*   **Python Version:** `3.11`
*   **CUDA Version:** Compatible with Wan2.2 requirements
*   **Framework:** Built on Wan2.2 video diffusion

**Model Weights:**
| Model | Purpose | Source |
| :--- | :--- | :--- |
| Wan2.2 T2V-A14B | Text-to-video | Wan-AI (HuggingFace) |
| Wan2.2 I2V-A14B | Image-to-video | Wan-AI (HuggingFace) |
| StoryMem M2V LoRA | Memory conditioning | Kevin-thu (HuggingFace) |

**LoRA Variants:**
- **MI2V**: Memory + first-frame image conditioning
- **MM2V**: Memory + first 5 motion frames conditioning

**Installation:**
```bash
conda create -n storymem python=3.11
conda activate storymem
pip install -r requirements.txt
pip install flash_attn
huggingface-cli download Kevin-thu/StoryMem --local-dir ./models/storymem
```

**Configuration:**
- Default resolution: 832×480
- Memory buffer: Max 10 shots
- Generation: T2V for first shot, M2V for subsequent

---

## 8. CPU Offloading Options for Low VRAM

### ComfyUI VRAM Management Flags

| Flag | VRAM Use | Description |
| :--- | :--- | :--- |
| `--lowvram` | Minimal | Splits UNet, aggressive CPU-GPU transfers |
| `--novram` | Near-zero | When lowvram isn't enough |
| `--cpu` | 0 | CPU-only (very slow, last resort) |
| `--medvram` | Medium | Balanced performance/memory |
| `--async-offload` | Low | Async weight offloading |
| `--reserve-vram N` | Custom | Reserve N GB for OS |

### Recommended Configurations by GPU VRAM

| VRAM | Flags | Models | Resolution |
| :--- | :--- | :--- | :--- |
| 4GB | `--lowvram` | SD 1.5 only | 512x512 |
| 6GB | `--normalvram --force-fp16` | Pruned SDXL | 768x768 |
| 8GB | `--preview-method auto --force-fp16` | SDXL | 1024x1024 |
| 12GB+ | Default | Most models | Native |
| 24GB+ | `--highvram` | All models | Native |

### RAM Requirements for Offloading

| RAM | Use Case |
| :--- | :--- |
| 16GB | Minimum for `--lowvram` mode |
| 32GB | Comfortable for complex workflows |
| 64GB | Multiple large models in RAM |

### Model-Specific Flags

**FLUX.1:**
```bash
--disable-xformers --use-split-cross-attention --cache-classic --lowvram
```

**SDXL:**
```bash
--disable-xformers --use-split-cross-attention --cache-classic --lowvram
```

**Video Models (Wan2.x, FlashPortrait):**
```bash
--GPU_memory_mode sequential_cpu_offload  # Via model config, not ComfyUI
```

### Progressive Offloading Strategy

1. Start: `--medvram --use-xformers --cpu-text-encoder --fp16`
2. If OOM: Add `--cpu-vae`
3. If still OOM: Switch to `--lowvram`
4. Last resort: `--novram` or `--cpu`

---

## 9. Deployment Checklist (Updated)

### GPU Tiers

| Tier | VRAM | Models |
| :--- | :--- | :--- |
| **Consumer** | 8-12GB | Genfocus, MVInverse, Qwen-Image-Edit |
| **Prosumer** | 16-24GB | Above + FlashPortrait (CPU offload) |
| **Datacenter** | 48-80GB | Above + InfCam, FlashPortrait (full) |

### Minimum Requirements by Model

| Model | Min VRAM | CPU Offload VRAM | Notes |
| :--- | :--- | :--- | :--- |
| Qwen-Image-Edit-2511 | 10GB | N/A | bfloat16 |
| Genfocus | 12GB | N/A | depth_pro.pt |
| MVInverse | 8GB | N/A | DINOv2 encoder |
| FlashPortrait | 60GB | 10GB | sequential_cpu_offload |
| StoryMem | TBD | TBD | Based on Wan2.2 |
| InfCam | 50GB+ | TBD | A100/H100 recommended |

---

## 10. References

*   **Genfocus:** https://github.com/rayray9999/Genfocus
*   **InfCam:** https://github.com/emjay73/InfCam
*   **MVInverse:** https://github.com/Maddog241/mvinverse
*   **FlashPortrait:** https://github.com/Francis-Rings/FlashPortrait
*   **StoryMem:** https://github.com/Kevin-thu/StoryMem
*   **Qwen-Image-Edit-2511:** https://huggingface.co/Qwen/Qwen-Image-Edit-2511
*   **ComfyUI VRAM Guide:** https://apatero.com/blog/vram-optimization-flags-comfyui-explained-guide-2025
