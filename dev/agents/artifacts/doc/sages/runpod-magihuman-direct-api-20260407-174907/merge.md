---
topic: runpod-magihuman-direct-api
date: 2026-04-07
status: merged
---

# Merge Notes - RunPod MagiHuman Direct API

## Must Fix

- Clarify that the endpoint is API-first and explicitly not a ComfyUI-serving design.
- Make hardware expectations concrete: H100 first, L40S only experimental.
- Specify that the task contract should mirror Seedance semantics, including `staged`.
- Call out repo drift around missing `docker/Dockerfile.api`.
- Narrow the product promise to MagiHuman’s actual conditioning surface: prompt + image + optional audio.

## Should Fix

- Reuse the existing job system in phase 1 to reduce implementation risk.
- Use R2-backed stable URLs instead of ephemeral output links.
- Split rollout into distill first, then base, then SR.

## Not Fixing In V1

- ControlNet-style controls
- general video editing
- broad low-end GPU support

