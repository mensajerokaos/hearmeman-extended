---
author: oz
model: claude-haiku-4-5-20251001
date: 2025-12-29
task: Research ComfyUI custom nodes and workflows for Genfocus, Qwen-Image-Edit-2511 GGUF, and MVInverse
---

# ComfyUI Custom Nodes Research: Genfocus, Qwen-Image-Edit, MVInverse

## 1. Genfocus (Generative Refocusing)

### Project Overview
- **GitHub**: https://github.com/rayray9999/Genfocus
- **Paper**: "Generative Refocusing: Flexible Defocus Control from a Single Image" (arXiv:2512.16923, Dec 2025)
- **Authors**: Tuan Mu, Chun-Wei Huang, Jia-Bin Liu, Yu-Lun Liu
- **Official Demo**: https://generative-refocusing.github.io/

### How It Works
Two-stage diffusion-based framework:
1. **DeblurNet**: Recovers all-in-focus image from blurry input
2. **BokehNet**: Synthesizes photorealistic bokeh with controllable parameters

Both stages use FLUX.1-DEV backbone with LoRA fine-tuning for efficiency.

### Model Architecture
- **Base Model**: FLUX.1-dev (requires authentication/access request)
- **Quantization**: Uses LoRA for efficient fine-tuning
- **Primary Models**:
  - `bokehNet.safetensors`
  - `deblurNet.safetensors`
  - `depth_pro.pt` (auxiliary for depth estimation)

### ComfyUI Integration Status

**CURRENT STATUS**: ⚠️ **No official ComfyUI node exists**

The project currently uses a Gradio-based web interface at `http://127.0.0.1:7860`. A dedicated ComfyUI custom node wrapper has not been released.

### Alternative Integration Approaches

#### Option A: Create Custom ComfyUI Node (RECOMMENDED)
Create a wrapper node that:
- Loads bokehNet and deblurNet models from safetensors
- Integrates depth_pro for depth estimation
- Provides nodes for:
  - Image input
  - Focus plane selection
  - Bokeh intensity control
  - Aperture shape customization
  - Two-stage processing pipeline

**Required Files**:
- Custom node Python class
- Model loaders for both FLUX-based models
- Depth estimation integration

#### Option B: API Wrapper (Short-term)
Wrap the Gradio demo as an HTTP service and call it from ComfyUI via external API nodes.

#### Option C: Use Existing Depth/Bokeh Nodes
Interim solution using existing ComfyUI nodes:
- **DepthAnythingV2Preprocessor** (from `comfyui_controlnet_aux`)
- **ComfyUI_Photography_Nodes** (Depth of Field)
- **Nuke Defocus** (from nuke-nodes-comfyui)

These provide similar but lower-quality bokeh effects without Genfocus's generative approach.

### Setup Requirements
```bash
# Clone and prepare
git clone https://github.com/rayray9999/Genfocus.git
cd Genfocus
conda create -n genfocus python=3.12
conda activate genfocus

# Download models to root directory
# - bokehNet.safetensors
# - deblurNet.safetensors
# Create checkpoints/ directory with depth_pro.pt

# Request FLUX.1-dev access and authenticate locally
# Run Gradio demo
python app.py  # http://127.0.0.1:7860
```

### Resources
- [GitHub Repository](https://github.com/rayray9999/Genfocus)
- [ArXiv Paper](https://arxiv.org/abs/2512.16923)
- [Project Demo](https://generative-refocusing.github.io/)

---

## 2. Qwen-Image-Edit-2511 GGUF

### Project Overview
- **Base Model**: Qwen-Image-Edit (20B parameter MMDiT)
- **Latest Version**: Qwen-Image-Edit-2511 (Dec 2025)
- **Format**: GGUF quantized for low-VRAM execution
- **License**: Apache 2.0

### ComfyUI Integration Status

**CURRENT STATUS**: ✅ **FULLY SUPPORTED via ComfyUI-GGUF**

The Qwen-Image-Edit-2511 GGUF model has **native ComfyUI support** through the existing ComfyUI-GGUF custom node by city96.

### Available GGUF Quantization Models

| Quantization | Size | VRAM Requirement |
|-------------|------|-----------------|
| Q2_K | 7.06 GB | ~8GB |
| Q3_K_S | 8.95 GB | ~10GB |
| Q3_K_M | 9.68 GB | ~11GB |
| Q4_K_S | 12.1 GB | ~14GB |
| Q4_K_M | 13.1 GB | ~15GB |
| Q5_K_M | 14.9 GB | ~17GB |
| Q6_K | 16.8 GB | ~19GB |
| Q8_0 | 21.8 GB | ~24GB |

### Installation Steps

#### 1. Install Custom Node
```bash
# Via ComfyUI Manager:
# Manager > Custom Nodes Manager > Search "ComfyUI-GGUF" > Install by city96
```

#### 2. Download Models

**GGUF UNet Model**:
- Source: https://huggingface.co/QuantStack/Qwen-Image-Edit-GGUF (recommended)
- Alt: https://huggingface.co/unsloth/Qwen-Image-Edit-2511-GGUF (newer with Unsloth optimizations)
- Place in: `ComfyUI/models/unet/`

**Text Encoder**:
- File: `qwen_2.5_vl_7b_fp8_scaled.safetensors`
- Place in: `ComfyUI/models/text_encoders/`

**VAE**:
- File: `qwen_image_vae.safetensors`
- Place in: `ComfyUI/models/vae/`

**Optional - Lightning LoRA** (4-step inference):
- File: `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-fp32.safetensors`
- Place in: `ComfyUI/models/loras/`

#### 3. Configuration in Workflow

**With Lightning LoRA** (faster):
```
Steps: 6
CFG Scale: 1.0
```

**Without LoRA** (better quality):
```
Steps: 20+
CFG Scale: 2.5-4.0
```

### Key Features

1. **Bilingual Text Editing**: Precise Chinese/English text editing
   - Add, delete, modify text while preserving style/size/font

2. **Semantic Editing**: Modify object/person properties

3. **Appearance Editing**: Change colors, textures, styles

4. **Multi-Person Fusion** (v2511): Combine two person images into coherent group photo

5. **Integrated LoRA Effects**: Popular LoRA effects built into base model

6. **Advanced Features**:
   - Improved image consistency
   - Better character consistency
   - Enhanced industrial design generation
   - Stronger geometric reasoning

### Known Issues
- **Issue #317**: Some CLIP loader errors reported in city96/ComfyUI-GGUF
- **Feature Request #347**: Native Qwen-Image quantization tools not yet in llama.cpp (users can manually quantize)
- Supports: FLUX, SD1.5, SDXL, SD3, AuraFlow, LTXV, Hunyuan Video, WAN, HiDream, Cosmos

### Supported Architectures in ComfyUI-GGUF
- FLUX
- SD1.5, SDXL, SD3 (3.5)
- AuraFlow
- LTXV
- Hunyuan Video
- WAN
- HiDream
- Cosmos

### Sources
- [QuantStack GGUF Models](https://huggingface.co/QuantStack/Qwen-Image-Edit-GGUF)
- [Unsloth 2511 GGUF](https://huggingface.co/unsloth/Qwen-Image-Edit-2511-GGUF)
- [ComfyUI-GGUF by city96](https://github.com/city96/ComfyUI-GGUF)
- [ComfyUI Native Workflow Docs](https://docs.comfy.org/tutorials/image/qwen/qwen-image-edit)
- [ComfyUI Wiki Guide](https://comfyui-wiki.com/en/tutorial/advanced/image/qwen/qwen-image)
- [How-To Guide](https://www.kombitz.com/2025/12/23/how-to-use-qwen-image-edit-2511-gguf-in-comfyui/)

### Alternative Approaches

If GGUF support encounters issues, consider:
1. **ComfyUI-QwenVL**: Alternative custom node supporting Qwen2.5-VL and Qwen3-VL with GGUF
   - https://github.com/1038lab/ComfyUI-QwenVL

2. **Diffusers Integration**: Use ComfyUI-Diffusers for native model loading
   - Supports HuggingFace Diffusers models
   - Custom Diffusers Pipeline node available

3. **FP8/BF16 Support**: Use original (non-GGUF) quantized models via:
   - Official Qwen models with FP8 quantization
   - Direct safetensors loading (higher VRAM)

---

## 3. MVInverse (Multi-view Inverse Rendering)

### Project Overview
- **GitHub**: https://github.com/Maddog241/mvinverse
- **Paper**: "MVInverse: Feedforward Multi-view Inverse Rendering in Seconds"
- **Release Date**: December 24, 2025
- **Architecture**: Feed-forward framework with alternating attention mechanisms

### What It Does
Performs **inverse rendering** from multiple views:
- Reconstructs scene geometry (normals, depth)
- Estimates surface materials (albedo, roughness, specular)
- Maintains multi-view consistency
- No per-scene optimization required (feedforward)
- Processes multiple views in seconds

### Capabilities
- Material property estimation
- Normal map generation
- Geometry reconstruction
- Multi-view consistency preservation
- State-of-the-art quality on public benchmarks

### ComfyUI Integration Status

**CURRENT STATUS**: ❌ **No official ComfyUI node exists**

No dedicated ComfyUI custom node has been released. The project includes standalone Python inference scripts but no ComfyUI integration.

### Available Installation/Integration Options

#### Option A: Create Custom ComfyUI Node (RECOMMENDED)

Create a wrapper node that:
```python
# Required node inputs:
- Multi-view image sequence (list of images)
- Camera parameters (optional)
- Processing resolution

# Node outputs:
- Material maps (albedo, roughness, metallic, specular)
- Geometry maps (normal, depth)
- Consistency scores
```

**Implementation Steps**:
1. Wrap MVInverse's inference API
2. Handle batch image loading
3. Provide nodes for:
   - Loading multi-view image sequences
   - Running inverse rendering
   - Exporting material maps
   - Exporting geometry maps

#### Option B: Standalone Python Script Integration

MVInverse provides direct Python integration:

```python
# Clone and install
git clone https://github.com/Maddog241/mvinverse.git
cd mvinverse

# Install dependencies
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
  --index-url https://download.pytorch.org/whl/cu118
pip install opencv-python huggingface_hub==0.35.0
```

**Usage**:
```bash
# Process image directory
python inference.py --input_dir ./images --output_dir ./results
```

This generates material and geometry maps for each input frame.

#### Option C: API Wrapper Pattern

1. Run MVInverse as standalone service
2. Create lightweight ComfyUI node that calls HTTP API
3. Return processed material/geometry maps

### Related ComfyUI Multi-View Tools

If you need multi-view capabilities, consider these existing nodes:

1. **ComfyUI-MVAdapter**: Multi-view image generation
   - GitHub: https://github.com/huanngzh/ComfyUI-MVAdapter
   - Generates multi-view consistent images from text/images

2. **ComfyUI-IG2MV**: Image-guided multi-view generation
   - GitHub: https://github.com/hunzmusic/ComfyUI-IG2MV
   - Designed for texture generation from 3D mesh renders

3. **ComfyUI-3D-Pack**: Full 3D processing suite
   - Handles mesh input/output
   - Includes 3DGS and NeRF processing
   - UV mapping and texture support

4. **Hy3DRenderMultiView**: High-quality multi-perspective rendering
   - Part of ComfyUI-Hunyuan3DWrapper

### Setup Requirements (Standalone)

```bash
# Clone repository
git clone https://github.com/Maddog241/mvinverse.git
cd mvinverse

# Create environment
conda create -n mvinverse python=3.10
conda activate mvinverse

# Install PyTorch with CUDA 11.8 support
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
  --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
pip install opencv-python huggingface_hub==0.35.0

# Download models (HuggingFace Hub)
huggingface-cli download [model_id] --local-dir ./models
```

### Resources
- [GitHub Repository](https://github.com/Maddog241/mvinverse)
- [ArXiv Paper](https://arxiv.org/abs/[paper_id])
- Python inference API documentation in repo

---

## Summary & Recommendations

### Quick Status Table

| Model | ComfyUI Node | Recommended Approach | Priority |
|-------|-------------|---------------------|----------|
| **Genfocus** | ❌ No | Create custom node OR use interim bokeh nodes | Medium |
| **Qwen-Image-Edit-2511** | ✅ Yes (GGUF) | Use ComfyUI-GGUF by city96 (existing) | HIGH |
| **MVInverse** | ❌ No | Create custom node OR standalone script | Low |

### Implementation Priority

1. **IMMEDIATE**: Qwen-Image-Edit-2511 GGUF
   - Fully supported via ComfyUI-GGUF
   - Just download models and configure
   - Production-ready

2. **SHORT-TERM**: Genfocus Integration
   - Create ComfyUI custom node wrapper
   - OR use existing bokeh/depth nodes as interim solution
   - High-quality generative refocusing capability

3. **MEDIUM-TERM**: MVInverse Integration
   - Develop custom node for material/geometry extraction
   - Useful for 3D/game asset creation
   - Can be used alongside existing multi-view tools

### Development Notes

**For Custom Node Creation** (Genfocus & MVInverse):
- Use ComfyUI custom node template: https://github.com/comfyanonymous/ComfyUI_examples
- Refer to related nodes:
  - DepthAnythingV2 for depth estimation pattern
  - FLUX integration nodes for transformer loading
  - MVAdapter nodes for multi-view patterns

**Diffusers Integration Option**:
- ComfyUI-Diffusers provides generic HuggingFace Diffusers model loading
- Could potentially wrap Qwen-Image-Edit or similar models
- Less efficient than native nodes but more flexible

### References
- [ComfyUI Official Docs](https://docs.comfy.org/)
- [awesome-comfyui Collection](https://github.com/ComfyUI-Workflow/awesome-comfyui)
- [ComfyUI Custom Node Guide](https://www.bentoml.com/blog/a-guide-to-comfyui-custom-nodes)
- [RunComfy Node Directory](https://www.runcomfy.com/comfyui-nodes)
