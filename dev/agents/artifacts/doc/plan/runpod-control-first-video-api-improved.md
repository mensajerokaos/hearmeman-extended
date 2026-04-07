---
task: Control-first self-hosted video API on RunPod without ComfyUI in the serving path
author: Codex
model: GPT-5 Codex
date: 2026-04-07
status: approved-for-planning
topic: runpod-control-first-video-api
quality_loop_iteration: 1
---

# RunPod Control-First Video API PRD

**Version:** 0.2  
**Date:** 2026-04-07  
**Status:** Quality-loop approved for planning  
**Target Experience:** “Seedance-like async API, but with deeper control inputs and no ComfyUI serving dependency”  
**Primary Backend Family:** `Wan 2.2` official direct inference + Diffusers integrations

---

## 1. Executive Summary

This PRD defines the control-first counterpart to the MagiHuman endpoint. The product goal is not just “generate a human talking to camera.” The goal is a self-hosted API that can accept structured conditioning inputs such as:

- prompt
- reference image
- audio
- pose video
- optional replacement assets

The backend recommendation is to build around the official Wan 2.2 stack rather than ComfyUI, because Wan 2.2 already exposes direct inference and Diffusers paths for the exact categories we need:

- `TI2V-5B` for prompt/image-to-video
- `S2V-14B` for speech-driven video
- `Animate-14B` for character animation and replacement

The endpoint contract should still feel like Seedance:

- async task creation
- immediate `task_id`
- status polling
- stable output URL

But unlike Seedance, the model stack and orchestration are ours.

---

## 2. Problem Statement

### 2.1 User Problem

The user wants a simpler product surface than ComfyUI while retaining strong controllability for video generation.

### 2.2 Technical Problem

The repo already contains:

- RunPod deployment patterns
- job-tracking infrastructure
- R2 persistence tooling
- research on WAN 2.2, SteadyDancer, and ControlNet-adjacent workflows

What it does not yet contain is a direct serving layer that turns those pieces into an API-first product.

### 2.3 Key Insight

For video, “ControlNet or similar” should be interpreted as **conditioning-first generation**, not literally only ControlNet. The official Wan 2.2 stack offers more relevant control surfaces for video than a narrow ControlNet-only design.

---

## 3. Product Goals

### 3.1 Goals

- expose a Seedance-style async API on our own RunPod server
- avoid ComfyUI in the request-serving path
- support practical conditioning inputs for video tasks
- ship an incremental roadmap from lower-cost TI2V to heavier S2V/Animate modes
- return stable artifact URLs from R2

### 3.2 Non-Goals

- replicate every ComfyUI workflow in v1
- expose every Wan capability on day one
- promise one hardware tier for all task types

---

## 4. Evidence and Backend Selection

### 4.1 Official Wan 2.2 Evidence

The official Wan 2.2 project exposes:

- TI2V direct inference
- S2V direct inference
- pose + audio driven generation
- Animate preprocessing and inference
- Diffusers integrations for Animate and other modes

### 4.2 Why Wan 2.2 Wins This Slot

Compared to MagiHuman:

- better conditioning surface
- better match for “control-first” serving
- clearer separation between task types
- official support for direct runners outside ComfyUI

### 4.3 Product Positioning

- **MagiHuman endpoint** = avatar-first
- **Control-first endpoint** = structured conditioning first

These should be treated as complementary products, not as one overloaded endpoint.

---

## 5. Recommended Backend Matrix

| Product Mode | Backend | Inputs | Hardware Target | Role |
|--------------|---------|--------|-----------------|------|
| `ti2v-5b` | Wan2.2 TI2V-5B | prompt, optional image | 24GB+ class | lowest-friction v1 |
| `s2v-14b` | Wan2.2 S2V-14B | prompt, image, audio, optional pose_video | 80GB class | audio-driven premium |
| `animate-14b` | Wan2.2 Animate-14B | reference image, pose/face/background assets, prompt | H100/A100 target | high-control premium |

### 5.1 Initial Shipping Recommendation

Ship `TI2V-5B` first.

Reason:

- lower hardware cost
- simpler input surface
- still satisfies the “no ComfyUI, API-first” goal

### 5.2 Secondary Additions

- `S2V-14B` second
- `Animate-14B` third

This keeps the control-first endpoint from becoming too complex before the basic job system is stable.

---

## 6. API Contract

### 6.1 Endpoints

- `POST /api/v1/control-video/tasks`
- `GET /api/v1/control-video/tasks/{task_id}`
- `GET /api/v1/control-video/tasks?status=&task_type=`
- `POST /api/v1/control-video/tasks/{task_id}/cancel`

### 6.2 Create Task Example

```json
{
  "model": "wan22",
  "task_type": "s2v-14b",
  "input": {
    "prompt": "A presenter speaks confidently while following the motion guide.",
    "image_url": "https://assets.example.com/ref.png",
    "audio_url": "https://assets.example.com/voice.wav",
    "pose_video_url": "https://assets.example.com/pose.mp4",
    "size": "1024x704",
    "seed": 42
  },
  "config": {
    "webhook_url": "https://client.example.com/hooks/video",
    "webhook_secret": "secret"
  }
}
```

### 6.3 Poll Result Example

```json
{
  "code": 200,
  "data": {
    "task_id": "uuid",
    "model": "wan22",
    "task_type": "s2v-14b",
    "status": "completed",
    "input": { "...": "..." },
    "output": {
      "video": "https://r2.example.com/runpod/control-video/2026-04-07/uuid.mp4"
    },
    "meta": {
      "created_at": "2026-04-07T18:10:00Z",
      "started_at": "2026-04-07T18:10:04Z",
      "ended_at": "2026-04-07T18:16:30Z",
      "backend": "wan22-s2v-14b",
      "gpu_type": "H100"
    },
    "error": null
  }
}
```

### 6.4 Required Statuses

- `pending`
- `staged`
- `processing`
- `completed`
- `failed`
- `canceled`

---

## 7. System Architecture

### 7.1 High-Level Flow

```text
Client
  -> FastAPI ingress
  -> task persisted
  -> worker claims task
  -> preprocess inputs if required
  -> backend-specific runner executes
  -> artifact uploaded to R2
  -> task updated + webhook fired
```

### 7.2 Core Modules

- API ingress and validation
- task persistence and status tracking
- backend selector by `task_type`
- preprocessing subsystem
- runner subsystem
- artifact upload subsystem

### 7.3 Why Preprocessing Must Be First-Class

In ComfyUI, preprocessing is hidden in graph nodes. In this product, preprocessing must become explicit service behavior:

- normalize media
- extract or validate pose assets
- validate audio format
- prepare background/mask assets for replacement tasks

Without this, the API surface will be unstable and hard to reason about.

---

## 8. Reuse Strategy Inside This Repo

### 8.1 Reuse

- existing FastAPI app
- existing job endpoints/persistence concepts
- existing PostgreSQL setup
- existing R2 conventions

### 8.2 New Layers

- `/api/v1/control-video` route group
- conditioning-aware schemas
- backend adapters for Wan task families
- preprocessing workers

### 8.3 Schema Strategy

Phase 1 can still reuse the current generic job persistence with strong metadata typing. Unlike the MagiHuman endpoint, however, this control-first path is more likely to justify dedicated generation tables earlier because task shapes diverge more sharply by backend.

---

## 9. Hardware and Cost Strategy

### 9.1 Tiering

| Tier | Hardware | Allowed Task Types |
|------|----------|--------------------|
| Standard | 4090 / L40S / 24GB+ | `ti2v-5b` |
| Premium | H100 / A100 80GB | `s2v-14b`, `animate-14b` |

### 9.2 Product Policy

The API must publish a capability matrix so users understand that:

- not all task types are always available
- hardware tier determines which modes can be queued
- queueing behavior can return `staged` when premium capacity is full

---

## 10. Rollout Plan

### Phase 0: Foundation

- fix API image path and container build drift
- add worker process scaffold
- add common task contract and R2 output handling

### Phase 1: TI2V Public Alpha

- `ti2v-5b`
- prompt + optional image
- polling first
- internal or allowlisted clients

### Phase 2: S2V Premium Beta

- `s2v-14b`
- prompt + image + audio
- optional pose input
- webhook completion

### Phase 3: Animate Premium Control

- `animate-14b`
- preprocessing layer for pose/face/background assets
- animation and replacement modes

---

## 11. Test Plan

### 11.1 Contract Tests

- create -> poll -> complete
- create -> fail on invalid assets
- create -> cancel -> canceled
- webhook signature verification

### 11.2 Backend Tests

- TI2V prompt-only
- TI2V prompt + image
- S2V image + audio
- Animate with prepared pose inputs

### 11.3 Operational Tests

- model cache persistence on Secure volume
- worker recovery after restart
- R2 upload reliability for mp4 outputs

---

## 12. Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| product tries to launch too many backends at once | High | ship TI2V-5B first |
| preprocessing complexity causes fragile failures | High | create explicit preprocess contracts and validation |
| users conflate “control-first” with “all controls” | Medium | publish supported control inputs per task type |
| premium modes require more GPU than expected | Medium | keep premium modes behind hardware and quota flags |
| current repo API container path is broken | High | resolve before any endpoint rollout |

---

## 13. Quality Gate Self-Assessment

| Dimension | Score | Notes |
|-----------|-------|-------|
| Completeness | 9/10 | Covers backend choice, modes, architecture, rollout, risks |
| Clarity | 10/10 | Clear distinction from MagiHuman option and from ComfyUI |
| Actionability | 9/10 | Concrete endpoints, task types, backend matrix |
| Testability | 9/10 | Good coverage, could deepen replacement validation later |
| Safety | 10/10 | Honest hardware gating and phased rollout |

**Total:** `47/50`  
**Quality Result:** Approved for planning

---

## 14. Approval Summary

This option is the stronger fit if the real product need is:

- conditioning and structured control
- multiple backend modes
- broader creative workflows than avatar-only generation
- no ComfyUI in the production request path

It is the right general endpoint to pair with the specialized MagiHuman endpoint.

