---
task: Seedance-style self-hosted API for daVinci-MagiHuman on RunPod
author: Codex
model: GPT-5 Codex
date: 2026-04-07
status: draft
topic: runpod-magihuman-direct-api
---

# RunPod MagiHuman Direct API PRD

**Version:** 0.1  
**Date:** 2026-04-07  
**Status:** Draft  
**Primary Goal:** Deliver a Seedance-style async API over a self-hosted `daVinci-MagiHuman` backend on RunPod without requiring ComfyUI in the serving path.

---

## 1. Executive Summary

This PRD defines a production-oriented API service that exposes `daVinci-MagiHuman` through a simple task contract similar to the Seedance endpoints previously used in other projects:

- `POST` a generation request
- receive `task_id` immediately
- poll `GET /task/{id}` for status
- receive a stable `output.video` URL when complete

The service will be built on the existing FastAPI + PostgreSQL job infrastructure already present in this repo and deployed as a RunPod service backed by H100-class hardware. The API will target human-centric generation use cases where MagiHuman is strongest: talking avatars, expressive motion from a reference image, and audio-conditioned lip-sync/video generation.

This option explicitly does **not** attempt to make MagiHuman a broad ControlNet-like control surface. The official model entrypoint accepts `prompt`, `image_path`, and optional `audio_path`; that is enough for a clean commercial-style API, but not enough for deep pose/depth/edge conditioning.

---

## 2. Why This Option

### 2.1 User Need

The desired experience is not “open ComfyUI and wire nodes.” The desired experience is:

1. send a request
2. get back a task id quickly
3. poll or receive a webhook
4. download a stable artifact

### 2.2 Why MagiHuman

`daVinci-MagiHuman` is attractive because it offers:

- native audio-video generation
- strong human/avatar performance
- multilingual support
- very fast published inference on H100

### 2.3 Why Not ComfyUI Here

ComfyUI is valuable for experimentation, but it is the wrong boundary for this serving experience because:

- the user wants API-first operation
- node-graph workflows complicate long-lived product endpoints
- MagiHuman already has an official non-Comfy entry surface

---

## 3. Current State

### 3.1 Existing Repo Assets

- Existing FastAPI app: `/home/oz/projects/2025/oz/12/runpod/api/main.py`
- Existing generic job endpoints: `/api/v1/jobs`
- Existing result storage model: `/api/v1/results`
- Existing PostgreSQL compose service in `docker/docker-compose.yml`
- Existing Cloudflare R2 upload tooling in the repo

### 3.2 Known Repo Drift

`docker/docker-compose.yml` references `docker/Dockerfile.api`, but that file is not present in the repository. The implementation must either create that file or update compose to point to the real API image definition.

### 3.3 MagiHuman Constraints

Based on the repo and stored feasibility analysis:

- base 256p bundle: ~80.8 GB
- distill 256p bundle: ~111.4 GB
- 540p / 1080p pipeline: ~142.0 GB
- H100 is the only officially benchmarked path
- gated dependencies require Hugging Face auth and accepted licenses

---

## 4. Product Scope

### 4.1 In Scope

- Seedance-style async HTTP API
- text + reference-image generation
- optional audio-conditioned generation
- task polling and webhook completion
- R2-backed stable output URLs
- H100-focused deployment path
- mode-specific model download strategy

### 4.2 Out of Scope

- ControlNet-like pose/depth/canny controls
- general-purpose video editing
- ComfyUI workflow execution in the request path
- low-end GPU support as a primary target

---

## 5. API Contract

### 5.1 Primary Endpoints

- `POST /api/v1/video/tasks`
- `GET /api/v1/video/tasks/{task_id}`
- `GET /api/v1/video/tasks?status=...`
- `POST /api/v1/video/tasks/{task_id}/cancel`

### 5.2 Request Shape

```json
{
  "model": "magihuman",
  "task_type": "magihuman-distill",
  "input": {
    "prompt": "A calm woman speaks directly to camera in a softly lit studio.",
    "image_url": "https://.../reference.png",
    "audio_url": "https://.../voice.wav",
    "duration_seconds": 5,
    "aspect_ratio": "16:9",
    "seed": 42
  },
  "config": {
    "webhook_url": "https://client.example.com/hooks/video",
    "webhook_secret": "optional-secret"
  }
}
```

### 5.3 Response Shape

```json
{
  "code": 200,
  "data": {
    "task_id": "uuid",
    "model": "magihuman",
    "task_type": "magihuman-distill",
    "status": "pending",
    "input": { "...": "..." },
    "output": null,
    "meta": {
      "created_at": "2026-04-07T18:00:00Z"
    }
  }
}
```

### 5.4 Status Model

The API should support these task states:

- `pending`
- `staged`
- `processing`
- `completed`
- `failed`
- `canceled`

`staged` is important if concurrency or GPU warm capacity is exhausted and we want Seedance-like queue semantics.

---

## 6. Architecture

### 6.1 Service Layout

```text
Client
  -> FastAPI ingress
  -> PostgreSQL job record
  -> Worker claims task
  -> MagiHuman runner executes
  -> Output saved locally
  -> Artifact uploaded to R2
  -> Job marked completed
  -> Polling/webhook returns stable URL
```

### 6.2 Runner Strategy

Use the official MagiHuman offline entrypoint rather than ComfyUI:

- `inference/pipeline/entry.py`
- required inputs: `--prompt`, `--image_path`
- optional: `--audio_path`
- mode-dependent config file for base, distill, or SR

### 6.3 Storage Strategy

- local scratch: request-scoped working directory
- local model cache: network volume on RunPod Secure
- final artifact: Cloudflare R2
- returned URL: stable R2 object URL or signed proxy URL

---

## 7. Deployment Requirements

### 7.1 Target Hardware

Primary target:

- `H100 NVL` or equivalent H100-class pod on RunPod Secure

Secondary experimentation only:

- `L40S` for limited feasibility checks

### 7.2 Deployment Modes

- `distill` mode for lower-latency draft clips
- `base` mode for higher-fidelity standard output
- `sr_540p` / `sr_1080p` only after the core async API is proven

### 7.3 Model Download Policy

Do **not** mirror the full 216 GB Hugging Face tree. Download only the files needed by the selected mode and its shared dependencies.

---

## 8. Repo Changes Required

### 8.1 API Layer

- add generation request/response schemas
- add `/api/v1/video/tasks` endpoints
- add task cancellation and webhook config handling

### 8.2 Job Layer

Prefer reusing the existing job system in phase 1, with generation-specific metadata, rather than creating a second queueing stack immediately.

### 8.3 Worker Layer

- add background worker command
- add task claiming logic
- add subprocess or in-process runner for MagiHuman

### 8.4 Infra Layer

- add or fix API Dockerfile path
- add MagiHuman model downloader
- add HF auth checks
- wire R2 upload into generation completion

---

## 9. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| H100 requirement drives cost | High | Start with distill mode and cache models on Secure volume |
| gated dependencies fail at startup | High | Add explicit startup validation for HF auth and accepted licenses |
| compile/warmup makes first job slow | Medium | mark early jobs as `staged`/`processing` and surface warmup state |
| existing job schema is analysis-centric | Medium | keep phase 1 metadata-based reuse, revisit dedicated schema after proving demand |
| users expect ControlNet-style control | High | position this endpoint explicitly as avatar/audio/image guided, not control-first |

---

## 10. Validation

### 10.1 Functional

- create task returns within 500 ms
- task transitions through status lifecycle correctly
- completed task returns stable `output.video`
- failed task returns structured error
- webhook fires once with signed verification

### 10.2 Operational

- model cache persists across pod restart when using Secure volume
- R2 upload completes for mp4 and wav outputs
- worker resumes queued jobs after restart

### 10.3 Quality

- 256p distill clip generation works end-to-end
- audio-conditioned clip works end-to-end
- base mode generation produces materially better quality than distill on approved prompts

---

## 11. Rollout Plan

### Phase 1

- direct async API
- distill mode only
- image + prompt required
- no audio

### Phase 2

- add optional audio-driven generation
- add webhook delivery
- add R2 lifecycle policies

### Phase 3

- add base mode
- add 540p or 1080p super-resolution profiles
- add job priority and concurrency controls

---

## 12. Open Questions

1. Should generation jobs reuse `analysis_job`, or should we split into a dedicated generation schema before shipping?
2. Do we want signed R2 URLs or an API proxy route for artifact delivery?
3. Is 1080p worth shipping in v1 given cold-start cost and extra dependencies?
4. Do we want synchronous “draft preview” mode for internal use, or keep all public requests async?

