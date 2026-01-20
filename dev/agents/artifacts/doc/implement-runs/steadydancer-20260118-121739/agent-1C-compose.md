# Agent 1C: Docker Compose Updates

## Changes Applied

Added environment variables (Lines 69-89):
- ENABLE_STEADYDANCER=false
- STEADYDANCER_VARIANT=fp8
- STEADYDANCER_GUIDE_SCALE=5.0
- STEADYDANCER_CONDITION_GUIDE=1.0
- STEADYDANCER_END_CFG=0.4
- STEADYDANCER_SEED=106060
- ENABLE_DWPOSE=false
- DWPOSE_DETECT_HAND=true
- DWPOSE_DETECT_BODY=true
- DWPOSE_DETECT_FACE=true
- DWPOSE_RESOLUTION=512
- ENABLE_WAN22_DISTILL=false
- TURBO_STEPS=4
- TURBO_GUIDE_SCALE=5.0
- TURBO_CONDITION_GUIDE=1.0
- TURBO_END_CFG=0.4

## Verification
```bash
docker compose -f /home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml config > /dev/null && echo "YAML valid"
```

## Files Modified
- `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml` (lines 69-89)
