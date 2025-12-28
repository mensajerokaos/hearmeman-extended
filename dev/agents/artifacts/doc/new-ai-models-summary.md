# New AI Models for RunPod Template

Research summary for potential additions to the hearmeman-extended template.

---

## 1. Generative Refocusing (GenFocus)

**Purpose**: Depth-of-field adjustment from single images - click to refocus with adjustable aperture.

### How It Works
1. **DeblurNet**: Recovers all-in-focus image from blurry input
2. **BokehNet**: Synthesizes depth-of-field effects with customizable bokeh

### Links
- **GitHub**: https://github.com/rayray9999/Genfocus
- **Demo**: https://huggingface.co/spaces/nycu-cplab/Genfocus-Demo
- **Paper**: arXiv:2512.16923

### Requirements
- TBD (awaiting GitHub research)

### Use Cases
- Post-capture refocusing
- Artistic bokeh effects
- Portrait enhancement

---

## 2. Qwen-Image-Edit-2511

**Purpose**: Conditional image editing with text prompts - character consistency, multi-person fusion, LoRA support.

### Key Capabilities
- **Character Consistency**: Preserves identity when editing portraits
- **Multi-Person Editing**: Fuse multiple people into group shots
- **LoRA Support**: Community lighting, viewpoint LoRAs
- **Industrial Design**: Batch product design, material replacement
- **Geometric Reasoning**: Generate construction lines for design

### Installation
```bash
pip install git+https://github.com/huggingface/diffusers
```

### Usage
```python
import torch
from PIL import Image
from diffusers import QwenImageEditPlusPipeline

pipeline = QwenImageEditPlusPipeline.from_pretrained(
    "Qwen/Qwen-Image-Edit-2511",
    torch_dtype=torch.bfloat16
)
pipeline.to('cuda')

inputs = {
    "image": [image1, image2],
    "prompt": "The magician is on the left, the alchemist on the right",
    "true_cfg_scale": 4.0,
    "num_inference_steps": 40,
    "guidance_scale": 1.0,
}
output = pipeline(**inputs)
```

### Links
- **HuggingFace**: https://huggingface.co/Qwen/Qwen-Image-Edit-2511
- **Demo**: https://chat.qwen.ai/?inputFeature=image_edit
- **License**: Apache 2.0

### Requirements
- CUDA GPU with bfloat16 support
- `diffusers` (latest from GitHub)
- TBD: Exact VRAM requirements

---

## 3. InfCam (Infinite Homography Camera Control)

**Purpose**: Camera-controlled video generation with precise cinematic control - depth-free approach using infinite homography.

### Key Features
- **Depth-free**: Avoids depth estimation inaccuracies
- **Parallax Prediction**: Learns residual parallax relative to plane at infinity
- **Diverse Trajectories**: AugMCV dataset with varied camera paths and focal lengths

### Links
- **GitHub**: https://github.com/emjay73/InfCam
- **Paper**: arXiv:2512.17040
- **License**: CC-BY 4.0

### Requirements
- TBD (awaiting GitHub research)

### Use Cases
- Novel-view video synthesis
- Cinematic camera movements
- Virtual cinematography

---

## 4. MVInverse (Multi-View Inverse Rendering)

**Purpose**: Recover geometry, materials, and illumination consistently across multiple viewpoints in a single forward pass.

### Key Capabilities
- **Intrinsic Decomposition**: Albedo, metallic, roughness, diffuse shading, normals
- **Cross-View Consistency**: Alternating attention across views
- **Real-Time**: Feed-forward (no per-scene optimization)
- **In-the-Wild**: Consistency-based finetuning on unlabeled real videos

### Architecture
- DINOv2 encoders for patch tokenization
- ResNeXt encoder for multi-resolution features
- DPT-style prediction head for pixel-aligned output

### Links
- **GitHub**: https://github.com/Maddog241/mvinverse
- **Paper**: arXiv:2512.21003

### Requirements
- TBD (awaiting GitHub research)

### Use Cases for Consistent Scenes
1. **Multi-view character sheets**: Generate consistent character from multiple angles
2. **Scene relighting**: Decompose materials, relight with new illumination
3. **3D-aware editing**: Edit one view, propagate consistently to others
4. **Asset creation**: Extract PBR materials for game/VFX assets

---

## Integration with Existing Template

### Current Models in hearmeman-extended
| Model | Size | Purpose |
|-------|------|---------|
| WAN 2.2 720p | 25GB | Video generation |
| VibeVoice-Large | 18GB | TTS voice cloning |
| XTTS v2 | 1.8GB | Multilingual TTS |
| Z-Image Turbo | 21GB | Fast image gen |
| Realism Illustrious | 6.5GB | Photorealistic images |

### Potential Additions
| Model | Est. Size | Purpose | Priority |
|-------|-----------|---------|----------|
| Qwen-Image-Edit-2511 | ~10-15GB | Image editing | HIGH |
| GenFocus | TBD | Refocusing/bokeh | MEDIUM |
| InfCam | TBD | Camera control video | MEDIUM |
| MVInverse | TBD | Multi-view consistency | HIGH |

### Synergies
- **MVInverse + WAN 2.2**: Consistent multi-view video
- **Qwen-Image-Edit + Illustrious**: Edit generated images
- **GenFocus + Any image model**: Post-process depth effects
- **InfCam + WAN 2.2**: Combine camera control approaches

---

*Last updated: 2025-12-28*
*Awaiting detailed GitHub research for requirements*
