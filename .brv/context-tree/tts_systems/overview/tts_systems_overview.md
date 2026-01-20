## Relations
@tts_systems/vibevoice/vibevoice_comfyui_integration.md
@tts_systems/xtts_v2/xtts_v2_rest_api.md
@tts_systems/chatterbox/chatterbox_tts_api_overview.md

## Raw Concept
**Task:**
Document TTS Systems for RunPod Custom Template

**Changes:**
- Consolidated TTS documentation for VibeVoice, XTTS, and Chatterbox

**Files:**
- docker/Dockerfile
- docker/docker-compose.yml

**Flow:**
Enable via ENV -> Download models -> Start API services -> Use in ComfyUI nodes

**Timestamp:** 2026-01-18

## Narrative
### Structure
- tts_systems/chatterbox: Chatterbox API and nodes
- tts_systems/vibevoice: VibeVoice integration
- tts_systems/xtts_v2: XTTS v2 API documentation

### Dependencies
- ComfyUI-Chatterbox custom node
- Chatterbox TTS API container (optional)
- VibeVoice-ComfyUI custom node (requires ~18GB VRAM for Large)
- XTTS v2 API container (port 8020)

### Features
- VibeVoice: 1.5B, Large, Large-Q8 models
- XTTS v2: REST API integration
- Chatterbox: REST API on port 8000
- Multi-model TTS support for diverse voice generation needs
