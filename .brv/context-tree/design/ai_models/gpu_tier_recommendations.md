## Relations
@tts_systems/overview/tts_systems_overview.md

## Raw Concept
**Task:**
SteadyDancer Integration Research

**Changes:**
- Updated VRAM savings calculation to 24GB and added multi-GPU instance strategy

**Files:**
- docker/start.sh

**Flow:**
Detect High-VRAM Workflow -> Disable Voice (~24GB saved) -> Launch ComfyUI Instance(s)

**Timestamp:** 2026-01-18

## Narrative
### Structure
- VRAM optimization strategy table

### Dependencies
- Disable voice models for high-VRAM video workflows

### Features
- VibeVoice, XTTS, and Chatterbox disabled to save ~24GB VRAM
- Critical for A100 80GB workflows (SteadyDancer + TurboDiffusion ~65GB)
- Multi-GPU: Scale via multiple ComfyUI instances rather than distributed inference
