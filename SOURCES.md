# Sources & Attribution

This template uses the following open-source projects, models, and resources.

## Core Components

### ComfyUI
- **Repository**: https://github.com/comfyanonymous/ComfyUI
- **License**: GPL-3.0
- **Description**: The most powerful and modular diffusion model GUI and backend

### ComfyUI-Manager
- **Repository**: https://github.com/ltdrdata/ComfyUI-Manager
- **License**: GPL-3.0
- **Description**: Custom node manager for ComfyUI

---

## Custom Nodes

### Image Generation

| Node | Repository | License | Description |
|------|------------|---------|-------------|
| comfyui_controlnet_aux | [Fannovel16/comfyui_controlnet_aux](https://github.com/Fannovel16/comfyui_controlnet_aux) | Apache-2.0 | ControlNet preprocessors |

### Video Generation

| Node | Repository | License | Description |
|------|------------|---------|-------------|
| ComfyUI-WAN | [kijai/ComfyUI-WAN](https://github.com/kijai/ComfyUI-WAN) | GPL-3.0 | WAN 2.1/2.2 video generation nodes |
| Comfyui_turbodiffusion | [anveshane/Comfyui_turbodiffusion](https://github.com/anveshane/Comfyui_turbodiffusion) | MIT | TurboDiffusion video acceleration |
| ComfyUI-SCAIL-Pose | [kijai/ComfyUI-SCAIL-Pose](https://github.com/kijai/ComfyUI-SCAIL-Pose) | GPL-3.0 | SCAIL facial mocap integration |

### Voice / TTS

| Node | Repository | License | Description |
|------|------------|---------|-------------|
| VibeVoice-ComfyUI | [Enemyx-net/VibeVoice-ComfyUI](https://github.com/Enemyx-net/VibeVoice-ComfyUI) | MIT | Microsoft VibeVoice TTS (v1.8.1+) |
| ComfyUI-XTTS | [AIFSH/ComfyUI-XTTS](https://github.com/AIFSH/ComfyUI-XTTS) | AGPL-3.0 | Coqui XTTS v2 (compatibility issues) |

---

## AI Models

### Image Models

| Model | Source | License | Size | Description |
|-------|--------|---------|------|-------------|
| Realism Illustrious v5.0 | [CivitAI](https://civitai.com/models/1048098) | CreativeML Open RAIL-M | 6.5GB | Photorealistic SDXL |
| Z-Image Turbo | [Comfy-Org/z_image_turbo](https://huggingface.co/Comfy-Org/z_image_turbo) | Apache-2.0 | 21GB | Alibaba 6B fast inference |
| Flux VAE (ae.safetensors) | [ffxvs/vae-flux](https://huggingface.co/ffxvs/vae-flux) | Apache-2.0 | 335MB | Flux-compatible VAE |

### Video Models

| Model | Source | License | Size | Description |
|-------|--------|---------|------|-------------|
| WAN 2.2 720p | [Hearmeman Template](https://docs.google.com/spreadsheets/d/1NfbfZLzE9GIAD5B_y6xjK1IdW95c14oS1JuIG9QihL8) | Research | 25GB | Video generation |
| SteadyDancer-14B | [MCG-NJU/SteadyDancer-14B](https://huggingface.co/MCG-NJU/SteadyDancer-14B) | Apache-2.0 | 28GB | Dance/motion transfer |

### Voice Models

| Model | Source | License | Size | Description |
|-------|--------|---------|------|-------------|
| VibeVoice-1.5B | [microsoft/VibeVoice-1.5B](https://huggingface.co/microsoft/VibeVoice-1.5B) | MIT | 5.4GB | Voice cloning TTS |
| VibeVoice-Large | [aoi-ot/VibeVoice-Large](https://huggingface.co/aoi-ot/VibeVoice-Large) | MIT | 18.7GB | High-quality TTS |
| VibeVoice-Large-Q8 | [FabioSarracino/VibeVoice-Large-Q8](https://huggingface.co/FabioSarracino/VibeVoice-Large-Q8) | MIT | 11.6GB | Quantized version |
| Qwen2.5 Tokenizer | [Qwen/Qwen2.5-1.5B](https://huggingface.co/Qwen/Qwen2.5-1.5B) | Apache-2.0 | 11MB | Required for VibeVoice |
| XTTS v2 | [coqui-ai/XTTS-v2](https://huggingface.co/coqui/XTTS-v2) | CPML | 4GB | Multilingual TTS |

---

## Base Docker Images

| Image | Source | Description |
|-------|--------|-------------|
| runpod/pytorch | [RunPod Docker Hub](https://hub.docker.com/r/runpod/pytorch) | PyTorch 2.8.0 + CUDA 12.8 |

---

## External Services (Optional)

### XTTS API Server
- **Repository**: https://github.com/daswer123/xtts-api-server
- **Docker Hub**: daswer123/xtts-api-server
- **License**: AGPL-3.0
- **Port**: 8020
- **Description**: Production-ready XTTS v2 API with FastAPI

### CivitAI Integration
- **Tool**: civitai-downloader
- **PyPI**: https://pypi.org/project/civitai-downloader/
- **Description**: Download models/LoRAs from CivitAI

---

## RunPod Templates

### Hearmeman Extended Template
- **Template ID**: 758dsjwiqz
- **Deploy URL**: https://console.runpod.io/deploy?template=758dsjwiqz
- **Description**: Base template with WAN 2.1/2.2 + VACE support
- **Reference**: [Hearmeman Templates Spreadsheet](https://docs.google.com/spreadsheets/d/1NfbfZLzE9GIAD5B_y6xjK1IdW95c14oS1JuIG9QihL8)

---

## Python Dependencies

Key version constraints for compatibility:

```txt
# Core
torch>=2.0.0
torchaudio>=2.0.0
transformers>=4.51.3  # VibeVoice requirement
# transformers==4.35.0  # XTTS requirement (conflicts with VibeVoice)

# VibeVoice
bitsandbytes>=0.48.1  # Critical - older versions break Q8
accelerate>=1.6.0
peft>=0.17.0
librosa>=0.9.0
soundfile>=0.12.0

# XTTS (if using standalone server)
TTS
pydub
srt
audiotsm
```

---

## Research & Documentation

| Document | Location | Description |
|----------|----------|-------------|
| XTTS v2 Research | `dev/agents/artifacts/doc/xtts-v2-research.md` | Integration options analysis |
| Hearmeman Template PRD | `hearmeman-extended-template.md` | Dockerfile specifications |
| Illustrious Integration | `illustrious-template-integration.md` | Realism Illustrious setup |

---

## License Compatibility

This template combines components with various licenses:
- **GPL-3.0**: ComfyUI, ComfyUI-Manager, Kijai nodes
- **MIT**: VibeVoice, TurboDiffusion
- **Apache-2.0**: Most HuggingFace models, ControlNet aux
- **AGPL-3.0**: XTTS, xtts-api-server
- **CreativeML Open RAIL-M**: Stable Diffusion derivatives

**Note**: When deploying commercially, review individual model licenses, especially for AGPL components.

---

## Contributing

When adding new components:
1. Add source to this file with repository URL and license
2. Update `docker/Dockerfile` with installation commands
3. Add any new workflows to `docker/workflows/`
4. Test locally before committing

---

## Acknowledgments

Special thanks to:
- **Hearmeman** - RunPod template infrastructure
- **Kijai** - WAN, SCAIL-Pose nodes
- **AIFSH** - XTTS ComfyUI integration
- **Enemyx-net** - VibeVoice-ComfyUI maintenance
- **daswer123** - XTTS API server
- **Comfy-Org** - Z-Image Turbo support
