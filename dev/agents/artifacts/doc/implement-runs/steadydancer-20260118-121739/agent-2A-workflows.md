# Agent 2A: Workflow Creation

## Workflows Created

### 1. steadydancer-dance.json
- Basic SteadyDancer dance animation workflow
- 50 sampling steps (vanilla)
- DWPose preprocessing for motion extraction
- Reference attention for identity preservation

### 2. steadydancer-turbo.json
- TurboDiffusion-accelerated workflow
- 4 sampling steps (100-200x speedup)
- All features of basic workflow + turbo loading

## Location
- `/home/oz/projects/2025/oz/12/runpod/docker/workflows/steadydancer-dance.json`
- `/home/oz/projects/2025/oz/12/runpod/docker/workflows/steadydancer-turbo.json`

## Verification
```bash
# Load in ComfyUI and queue prompt
# Verify no validation errors in console
```

## Requirements
- ENABLE_STEADYDANCER=true
- ENABLE_DWPOSE=true (for pose extraction)
- ENABLE_WAN22_DISTILL=true (for turbo variant)
