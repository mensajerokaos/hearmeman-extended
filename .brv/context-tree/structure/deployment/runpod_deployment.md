## Relations
@structure/generation/wan_video_generation.md

## Raw Concept
**Task:**
SteadyDancer Deployment Setup

**Changes:**
- Added GGUF VRAM specs and mandatory license acceptance steps to deployment guide

**Files:**
- structure/deployment/runpod_deployment.md

**Flow:**
License -> Token -> ENV -> Pod Start -> GGUF Load

**Timestamp:** 2026-01-18

## Narrative
### Structure
- RunPod Secret Management: HF_TOKEN
- Model selection logic in download_models.sh

### Dependencies
- HF_TOKEN (secret)
- ENABLE_STEADYDANCER=true
- STEADYDANCER_VARIANT=gguf (for 16GB cards)

### Features
- Mandatory: Accept license at huggingface.co/MCG-NJU/SteadyDancer-14B
- Low VRAM Support: GGUF variant reduces footprint to 7GB
- Deployment Checklist: Verify HF_TOKEN and license status before pod start
