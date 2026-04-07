---
task: Seedance-style self-hosted API for daVinci-MagiHuman on RunPod
author: Codex
model: GPT-5 Codex
date: 2026-04-07
status: approved-for-planning
topic: runpod-magihuman-direct-api
quality_loop_iteration: 1
---

# RunPod MagiHuman Direct API PRD

**Version:** 0.2  
**Date:** 2026-04-07  
**Status:** Quality-loop approved for planning  
**Target Experience:** “Seedance-like API UX, self-hosted on RunPod”  
**Primary Backend:** `daVinci-MagiHuman` official inference pipeline  
**Primary Hardware:** `H100` on RunPod Secure with persistent model cache

---

## 1. Executive Summary

This PRD defines a self-hosted video generation service that exposes `daVinci-MagiHuman` behind a commercial-style async API rather than a node graph. The service is intended to feel like the Seedance endpoints previously used by the team:

1. submit a task with prompt + reference image + optional audio
2. receive a `task_id` immediately
3. poll `GET /api/v1/video/tasks/{id}` or receive a webhook
4. retrieve a stable `output.video` URL once generation completes

The key design choice is to reuse the repo’s existing FastAPI + PostgreSQL job foundation and add a generation runner layer for MagiHuman. This keeps the product boundary simple while avoiding ComfyUI as a serving dependency.

This option is explicitly optimized for **avatar-style, human-centric generation**, not general compositional video control. MagiHuman is a good fit for the first, but not for the second.

---

## 2. Problem Statement

### 2.1 User Problem

The user wants the convenience of hosted video APIs without:

- depending on third-party providers for runtime availability or pricing
- opening ComfyUI for routine generation
- manually wiring workflows for repeatable requests

### 2.2 Technical Problem

The repo already contains an API service and job tracking model, but it is oriented toward media analysis rather than self-hosted video generation. MagiHuman is available as open inference code, but it needs:

- infrastructure wrapping
- request validation
- job orchestration
- artifact storage
- operational lifecycle management

### 2.3 Key Constraint

The official MagiHuman entry surface supports:

- `prompt`
- `image_path`
- optional `audio_path`

It does **not** expose a mature pose/depth/canny/reference conditioning surface. The API we design must reflect that reality instead of promising a control system the backend does not provide.

---

## 3. Goals and Non-Goals

### 3.1 Goals

- Provide Seedance-style async task UX on our own RunPod server.
- Avoid ComfyUI in the production request path.
- Reuse the existing repo’s API and job-tracking foundation where practical.
- Support stable artifact delivery through R2-backed URLs.
- Ship a phased rollout starting with a low-complexity, distill-backed path.

### 3.2 Non-Goals

- general ControlNet-like conditioning
- broad video editing and replacement workflows
- low-VRAM consumer deployment as a primary target
- multiplexing many model families behind one endpoint in v1

---

## 4. Current State and Evidence

### 4.1 Repo Evidence

- Existing FastAPI app: [api/main.py](/home/oz/projects/2025/oz/12/runpod/api/main.py)
- Existing generic jobs API: [api/main.py](/home/oz/projects/2025/oz/12/runpod/api/main.py#L200)
- Existing job schema: [api/schemas/job.py](/home/oz/projects/2025/oz/12/runpod/api/schemas/job.py)
- Existing job repository: [api/repositories/job.py](/home/oz/projects/2025/oz/12/runpod/api/repositories/job.py)
- Existing R2 tooling in repo documentation and scripts

### 4.2 External Evidence

- MagiHuman official repo and README
- stored feasibility note in RLM
- prior Seedance API patterns stored in RLM

### 4.3 Hard Facts Driving Design

- approximate model bundle sizes:
  - base 256p: `~80.8 GB`
  - distill 256p: `~111.4 GB`
  - 540p / 1080p path: `~142.0 GB`
- H100 is the only officially benchmarked path
- gated dependencies require HF auth and accepted licenses
- Secure pods are materially better than Community for cached weights

---

## 5. Product Surface

### 5.1 Public API

- `POST /api/v1/video/tasks`
- `GET /api/v1/video/tasks/{task_id}`
- `GET /api/v1/video/tasks?status=&page=`
- `POST /api/v1/video/tasks/{task_id}/cancel`

### 5.2 Task Types

- `magihuman-distill`
- `magihuman-base`
- `magihuman-sr-540p`
- `magihuman-sr-1080p`

### 5.3 Input Contract

Required:

- `prompt`
- `image_url` or uploaded reference image

Optional:

- `audio_url`
- `duration_seconds`
- `aspect_ratio`
- `seed`
- `webhook_url`
- `webhook_secret`

### 5.4 Status Contract

The service should support:

- `pending`
- `staged`
- `processing`
- `completed`
- `failed`
- `canceled`

`staged` is required so the API can distinguish accepted work that is waiting on GPU or warmup capacity.

---

## 6. Request and Response Shape

### 6.1 Create Task

```json
{
  "model": "magihuman",
  "task_type": "magihuman-distill",
  "input": {
    "prompt": "A woman speaks directly to camera in a quiet studio.",
    "image_url": "https://assets.example.com/ref.png",
    "audio_url": "https://assets.example.com/voice.wav",
    "duration_seconds": 5,
    "aspect_ratio": "16:9",
    "seed": 42
  },
  "config": {
    "webhook_url": "https://client.example.com/hooks/video",
    "webhook_secret": "secret"
  }
}
```

### 6.2 Poll Task

```json
{
  "code": 200,
  "data": {
    "task_id": "uuid",
    "model": "magihuman",
    "task_type": "magihuman-distill",
    "status": "completed",
    "input": { "...": "..." },
    "output": {
      "video": "https://r2.example.com/runpod/video/2026-04-07/uuid.mp4",
      "audio": "https://r2.example.com/runpod/video/2026-04-07/uuid.wav"
    },
    "meta": {
      "created_at": "2026-04-07T18:00:00Z",
      "started_at": "2026-04-07T18:00:05Z",
      "ended_at": "2026-04-07T18:00:26Z",
      "mode": "distill",
      "gpu_type": "H100"
    },
    "error": null
  }
}
```

### 6.3 API Compatibility Goal

The shape should intentionally resemble the Seedance usage pattern the team already understands, even though the backend is fully self-hosted.

---

## 7. System Architecture

### 7.1 Logical Flow

```text
Client
  -> FastAPI ingress
  -> validate request + store task
  -> return task_id immediately
  -> worker claims task
  -> fetch image/audio inputs
  -> run MagiHuman inference
  -> upload outputs to R2
  -> update task + notify webhook
```

### 7.2 Runtime Components

- API container
- worker process
- PostgreSQL
- shared local scratch volume
- persistent model cache volume
- R2 uploader

### 7.3 Why Not ComfyUI

ComfyUI can remain in the repo for experimentation, but the serving path must not depend on:

- workflow JSON loading
- node availability drift
- graph execution semantics
- UI-centric artifact handling

---

## 8. Implementation Strategy

### 8.1 Phase 1: Reuse Existing Job Infrastructure

Use the existing `analysis_job` system as the persistence base for v1, with generation-specific metadata. This avoids spinning up a separate queueing subsystem before product fit is proven.

Proposed metadata additions:

- `job_kind: "video_generation"`
- `task_type`
- `input_payload`
- `webhook_config`
- `output_assets`
- `runner_metrics`

### 8.2 Phase 2: Dedicated Generation Schema If Needed

Only split into dedicated tables if one of these becomes true:

- generation volume materially exceeds analysis volume
- generation-specific indexes and retention rules diverge
- task cancellation, retries, or billing logic become too awkward in shared metadata

---

## 9. Model and Hardware Plan

### 9.1 Recommended Initial Serving Modes

#### V1

- `magihuman-distill`
- 256p draft output
- image + prompt required
- optional audio deferred if startup complexity is high

#### V1.1

- `magihuman-base`
- optional audio path enabled

#### V2

- `magihuman-sr-540p`
- `magihuman-sr-1080p`

### 9.2 Hardware Policy

Production target:

- `H100 Secure Pod`

Experimental only:

- `L40S Secure Pod`

Do not productize around 4090 or lower until validated against the official MagiHuman stack rather than assumptions.

---

## 10. Files and Modules Expected to Change

### 10.1 API

- request/response schemas for video generation
- new `/api/v1/video/tasks` route group
- webhook request signing utilities

### 10.2 Data

- extend job metadata handling
- add output asset persistence conventions
- optional migration for new status values such as `staged` and `canceled`

### 10.3 Worker

- background polling/claim loop
- subprocess runner for MagiHuman CLI
- input downloader
- artifact uploader

### 10.4 Docker / Deployment

- fix missing `docker/Dockerfile.api` reference path
- add MagiHuman-specific image or build stage
- add startup checks for HF auth and accepted licenses
- add RunPod env contract for cached models and R2

---

## 11. Rollout Plan

### Phase 0: Dry Architecture Validation

- confirm direct runner works on target hardware
- confirm model cache survives pod restart on Secure volume
- confirm output upload works outside ComfyUI

### Phase 1: Internal Alpha

- distill-only
- async API only
- polling first, webhook optional
- authenticated internal clients only

### Phase 2: Beta

- base mode
- webhook support
- cancellation and retry policy
- signed R2 delivery or proxy delivery

### Phase 3: Full Product Decision

- decide whether to keep MagiHuman as a specialized avatar endpoint
- decide whether a separate control-first endpoint should be the general product default

---

## 12. Test Plan

### 12.1 Unit

- request validation
- status transitions
- webhook signature verification
- R2 key generation

### 12.2 Integration

- create task -> claim -> process -> upload -> poll
- failed input fetch path
- failed runner path
- restart worker with pending staged tasks

### 12.3 Live Smoke

- one 5-second distill request on H100
- one prompt+image request without audio
- one prompt+image+audio request after audio path is enabled

---

## 13. Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| missing API Dockerfile path causes deployment confusion | High | make image build path explicit in v1 implementation |
| H100 cost is higher than expected | High | distill-first rollout, stable cache volume, low-concurrency alpha |
| model warmup makes first job feel broken | Medium | use `staged` plus warmup status messaging |
| existing job schema becomes messy | Medium | keep metadata isolated and define a clear split trigger |
| users assume this endpoint supports full control graphs | High | explicit product positioning and separate control-first endpoint |

---

## 14. Quality Gate Self-Assessment

| Dimension | Score | Notes |
|-----------|-------|-------|
| Completeness | 9/10 | Covers API, storage, worker, deployment, risks, rollout |
| Clarity | 9/10 | Strong product boundary and non-goals |
| Actionability | 9/10 | Clear endpoint surface and repo touchpoints |
| Testability | 10/10 | Explicit functional and operational checks |
| Safety | 10/10 | Clear hardware constraints, schema reuse policy, rollout guardrails |

**Total:** `47/50`  
**Quality Result:** Approved for planning

---

## 15. Approval Summary

This option is feasible and worthwhile if the product goal is:

- talking avatars
- expressive human-centric generation
- audio-aware generation
- hosted-style API UX on our own infrastructure

It is **not** the right option if the real product goal is broad control-first video generation.

