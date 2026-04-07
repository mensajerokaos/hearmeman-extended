---
task: Control-first self-hosted video API on RunPod without ComfyUI in the serving path
author: Codex
model: GPT-5 Codex
date: 2026-04-07
status: draft
topic: runpod-control-first-video-api
---

# RunPod Control-First Video API PRD

**Version:** 0.1  
**Date:** 2026-04-07  
**Status:** Draft  
**Primary Goal:** Deliver a Seedance-like async API over a self-hosted control-first video stack with explicit conditioning inputs and no ComfyUI requirement for serving.

---

## 1. Executive Summary

This PRD defines a second API option for users who want more control than MagiHuman can offer. Instead of focusing on avatar expressiveness first, this option focuses on controllability:

- reference image conditioning
- pose-driven generation
- audio-driven generation
- character animation / replacement workflows

The recommended backend is **official Wan 2.2 direct inference and Diffusers integration**, not ComfyUI. This is a better fit for a self-hosted API because the Wan project already exposes direct runners and structured input surfaces for TI2V, S2V, and Animate.

---

## 2. Why This Option

### 2.1 User Need

The user wants “ControlNet or similar” without dealing with ComfyUI complexity.

### 2.2 Backend Choice

Wan 2.2 is the better fit than MagiHuman for this goal because the official repo supports:

- TI2V direct inference
- S2V direct inference
- pose + audio driven generation
- Animate character animation / replacement
- Diffusers integrations for some workflows

### 2.3 Core Product Position

This option is the **general-purpose control-first endpoint**.

---

## 3. Current State

- The repo currently leans heavily on ComfyUI for generation workflows.
- Existing API and job tracking already exist and can be reused.
- Existing research artifacts already cover WAN 2.2, SteadyDancer, ControlNet, and R2.

---

## 4. Product Scope

### 4.1 In Scope

- Seedance-style async API
- TI2V with prompt + optional image
- speech-to-video with image + audio
- pose-driven generation
- character animation / replacement
- R2-backed artifact delivery

### 4.2 Out of Scope

- ComfyUI workflow execution in the public serving path
- promising every control mode in v1
- low-end GPU support for heavy control modes

---

## 5. Recommended Model Stack

### 5.1 Core Backends

| Capability | Recommended Backend | Notes |
|------------|---------------------|-------|
| prompt + image to video | Wan2.2 TI2V-5B | Official direct inference, 24GB feasible |
| speech + image to video | Wan2.2 S2V-14B | Official direct inference, 80GB-class target |
| character animation/replacement | Wan2.2 Animate-14B | Official preprocessing + Diffusers path |

### 5.2 Why Not Pure ControlNet

Standard ControlNet is image-oriented. For video serving, the practical equivalent is a conditioning-first stack that accepts:

- pose video
- audio
- reference image
- optional background/mask assets

This is more useful than forcing a legacy “ControlNet” label onto a video stack that now has richer official conditioning modes.

---

## 6. API Contract

### 6.1 Primary Endpoints

- `POST /api/v1/control-video/tasks`
- `GET /api/v1/control-video/tasks/{task_id}`
- `GET /api/v1/control-video/tasks?status=...`
- `POST /api/v1/control-video/tasks/{task_id}/cancel`

### 6.2 Request Shape

```json
{
  "model": "wan22",
  "task_type": "animate-14b",
  "input": {
    "prompt": "The subject dances confidently under warm stage lights.",
    "image_url": "https://.../reference.png",
    "pose_video_url": "https://.../pose.mp4",
    "audio_url": "https://.../music.wav",
    "background_video_url": null,
    "mask_video_url": null,
    "size": "1280x720",
    "seed": 42
  }
}
```

### 6.3 Task Types

- `ti2v-5b`
- `s2v-14b`
- `animate-14b`
- optional future: `replace-14b`

---

## 7. Architecture

### 7.1 Control-First Pipeline

```text
Client
  -> FastAPI ingress
  -> job record created
  -> worker selects backend by task_type
  -> optional preprocessing step
  -> model inference
  -> upload outputs to R2
  -> status + output.video returned
```

### 7.2 Preprocessing Layer

The service should own preprocessing instead of outsourcing it to Comfy:

- pose extraction
- frame normalization
- face/background/mask preparation
- audio normalization

### 7.3 Backend Strategy

- use official CLI runners where that path is stronger
- use Diffusers where the official pipeline is stable and easier to maintain
- hide those differences behind one worker abstraction

---

## 8. Hardware Strategy

### 8.1 Practical Tiers

| Tier | Backends | Hardware |
|------|----------|----------|
| entry | TI2V-5B | 4090 / L40S / 24GB class |
| premium | S2V-14B | H100 / A100 80GB |
| premium-control | Animate-14B | H100 / A100 target until proven lower |

### 8.2 Serving Recommendation

Ship `TI2V-5B` first for cost-effective control-first v1, then layer in `S2V-14B` and `Animate-14B`.

---

## 9. Repo Changes Required

- new API schemas for conditioning inputs
- new route group under `/api/v1/control-video`
- worker adapter layer for Wan backends
- preprocessing utility modules
- output asset persistence
- Docker / build path for direct Wan runtime

---

## 10. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| too many modes in v1 create maintenance drag | High | ship TI2V first, keep other modes behind flags |
| preprocessing complexity becomes brittle | High | separate preprocessing modules with strict contracts |
| GPU requirements diverge by task type | Medium | publish capability matrix by backend and hardware tier |
| repo API container path is currently broken | Medium | fix build path before rollout |

---

## 11. Validation

- TI2V request with prompt-only works
- TI2V request with prompt + image works
- S2V request with image + audio works
- animate request with pose video works
- output artifact upload works
- API contract remains uniform across task types

---

## 12. Rollout Plan

### Phase 1

- TI2V-5B only
- async API
- R2 artifact URLs

### Phase 2

- S2V-14B
- webhook completion
- better cancellation and retry semantics

### Phase 3

- Animate-14B
- richer preprocessing and replacement flows

---

## 13. Open Questions

1. Should TI2V be the public default, with heavier control modes private at first?
2. Which preprocessing tools should be bundled in v1 versus deferred?
3. Should control-video tasks share the same tables as analysis + MagiHuman tasks, or get a dedicated schema earlier?

