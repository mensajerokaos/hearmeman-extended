# ComfyUI Workflows

Starter workflow templates for various models.

## Available Workflows

| File | Model | Type | VRAM |
|------|-------|------|------|
| `z-image-turbo-txt2img.json` | Z-Image Turbo | Image | 8-12GB |
| `realism-illustrious-txt2img.json` | Realism Illustrious XL | Image | 8-12GB |
| `wan22-t2v-5b.json` | WAN 2.2 5B | Video | 24GB+ |
| `vibevoice-tts-basic.json` | VibeVoice TTS | Audio | 8-16GB |

## Usage

1. Drag JSON file into ComfyUI canvas
2. Install missing models (see `_metadata.models_required` in each file)
3. Install custom nodes if needed (see `_metadata.custom_nodes_required`)
4. Adjust prompt and generate

## Model Locations

```
ComfyUI/models/
├── checkpoints/           # SDXL models
├── diffusion_models/      # Z-Image, WAN models
├── text_encoders/         # Qwen, UMT5
├── vae/                   # Autoencoders
├── loras/                 # Style adapters
└── vibevoice/             # TTS models
```

## Sources

- Z-Image Turbo: https://docs.comfy.org/tutorials/image/z-image/z-image-turbo
- WAN 2.2: https://docs.comfy.org/tutorials/video/wan/wan2_2
- Realism Illustrious: https://civitai.com/models/1048098/realism-illustrious
- VibeVoice: https://github.com/wildminder/ComfyUI-VibeVoice
