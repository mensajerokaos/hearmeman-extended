---
topic: runpod-control-first-video-api
date: 2026-04-07
status: merged
---

# Merge Notes - RunPod Control-First Video API

## Must Fix

- Replace vague “ControlNet” language with a realistic control-first video stack based on official Wan 2.2 capabilities.
- Separate task types by backend and hardware tier so the product promise is honest.
- Make TI2V-5B the first shippable control-first surface rather than trying to launch all modes at once.
- Explicitly state that preprocessing moves into the service layer, not ComfyUI.

## Should Fix

- Reuse the existing FastAPI and job framework where possible.
- Keep the polling contract uniform across TI2V, S2V, and Animate.
- Add rollout sequencing and a capability matrix by task type.

## Not Fixing In V1

- every control mode exposed publicly
- low-end GPU support for S2V and Animate
- full replacement workflow polish

