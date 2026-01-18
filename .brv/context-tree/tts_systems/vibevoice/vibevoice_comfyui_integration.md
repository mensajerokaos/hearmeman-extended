## Relations
@structure/models/ai_models_overview.md
@tts_systems/dependency_management/transformers_conflict.md

## Raw Concept
**Task:**
VibeVoice TTS Documentation

**Changes:**
- Adds VibeVoice TTS as ComfyUI custom nodes
- Implements automated VRAM-aware model selection (1.5B vs Large)

**Files:**
- docker/download_models.sh
- docker/workflows/vibevoice-tts-basic.json
- docker/tts-comparison/test-vibevoice-oscar.py

**Flow:**
Reference Audio -> LoadAudio -> VibeVoiceSingleSpeakerNode -> SaveAudio -> Poll History API

**Timestamp:** 2026-01-17

## Narrative
### Structure
- /workspace/ComfyUI/custom_nodes/VibeVoice-ComfyUI
- models/vibevoice/: Model storage (1.5B, Large, Large-Q8)
- docker/workflows/vibevoice-tts-basic.json: Baseline workflow

### Dependencies
- bitsandbytes >= 0.48.1 (Required for Q8 model)
- transformers >= 4.51.3
- Qwen tokenizer (downloaded at startup)

### Features
- High-quality voice cloning from reference audio
- Integration as ComfyUI custom node
- Support for LoRA configurations
- Multi-speaker pipeline support via ComfyUI graph concatenation
