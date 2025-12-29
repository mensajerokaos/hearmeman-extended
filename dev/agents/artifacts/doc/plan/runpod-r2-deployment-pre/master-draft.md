# RunPod R2 Deployment - Master Implementation Plan

## Executive Summary

Deploy the hearmeman-extended ComfyUI template to RunPod with automatic output synchronization to Cloudflare R2, enabling persistent storage for generated images and videos without RunPod's ephemeral storage limitations. Use GHCR for Docker image hosting and configure WAN 2.2 + TurboDiffusion for high-speed video generation.

---

## Implementation Phases

### Phase 1: R2 Sync Infrastructure
**Objective**: Create R2 upload scripts and integrate into Docker image

**Key Tasks**:
- Create `upload_to_r2.py` with boto3 S3 client for R2
- Create `r2_sync.sh` using inotifywait for real-time file watching
- Add inotify-tools to Dockerfile system dependencies
- Add R2 environment variables to Dockerfile
- Add sync daemon startup to start.sh

**Files to Modify/Create**:
- CREATE: `docker/upload_to_r2.py`
- CREATE: `docker/r2_sync.sh`
- MODIFY: `docker/Dockerfile` (Layer 1 + Layer 5)
- MODIFY: `docker/start.sh`

**Dependencies**: None (can start immediately)
**Complexity**: Medium

---

### Phase 2: Model Download Updates
**Objective**: Ensure WAN 2.2 and SteadyDancer models download correctly

**Key Tasks**:
- Verify WAN 2.2 download paths are correct (720p T2V model)
- Add TurboDiffusion model download support
- Test model download on fresh container
- Add download verification (file size checks)

**Files to Modify**:
- MODIFY: `docker/download_models.sh`

**Dependencies**: None (can run in parallel with Phase 1)
**Complexity**: Low

---

### Phase 3: Docker Registry Setup (GHCR)
**Objective**: Configure GitHub Container Registry for image hosting

**Key Tasks**:
- Create GitHub Actions workflow for automated builds
- Configure GHCR authentication
- Add multi-architecture build support (amd64)
- Set up image tagging strategy (latest, version tags)
- Test image pull from RunPod

**Files to Create/Modify**:
- CREATE: `.github/workflows/docker-build.yml`
- MODIFY: `docker/Dockerfile` (labels for GHCR)

**Dependencies**: Phase 1 (needs complete Dockerfile)
**Complexity**: Medium

---

### Phase 4: RunPod Template Configuration
**Objective**: Create and configure RunPod template with R2 credentials

**Key Tasks**:
- Create RunPod template with GHCR image reference
- Configure environment variables (R2 endpoint, bucket)
- Set up RunPod Secrets for R2 credentials
- Configure volume mounts and ports
- Test pod startup and model downloads

**Files to Create**:
- CREATE: `docs/runpod-template-config.md` (documentation)

**Dependencies**: Phase 3 (needs GHCR image available)
**Complexity**: Low

---

### Phase 5: Workflow Testing
**Objective**: Validate WAN 2.2 + TurboDiffusion video generation with R2 sync

**Key Tasks**:
- Deploy test pod on RunPod
- Run WAN 2.2 text-to-video workflow
- Verify TurboDiffusion acceleration working
- Confirm R2 upload of generated video
- Measure generation time and upload latency

**Files to Use**:
- `docker/workflows/wan-2.2-t2v.json` (existing or create)

**Dependencies**: Phase 4 (needs working RunPod template)
**Complexity**: Medium

---

### Phase 6: Documentation & Cleanup
**Objective**: Document the deployment process and clean up

**Key Tasks**:
- Update CLAUDE.md with R2 configuration
- Create user-facing deployment guide
- Document environment variables
- Add troubleshooting section

**Files to Create/Modify**:
- MODIFY: `CLAUDE.md`
- CREATE: `docs/DEPLOYMENT.md`

**Dependencies**: Phase 5 (needs validated workflow)
**Complexity**: Low

---

## Parallel Execution Map

```
Phase 1: [R2 Sync] ─────────────────────┐
                                         │
Phase 2: [Model Downloads] ─────────────┼──▶ Phase 3: [GHCR] ──▶ Phase 4: [RunPod] ──▶ Phase 5: [Testing] ──▶ Phase 6: [Docs]
                                         │
```

**Parallel opportunities**:
- Phase 1 + Phase 2 can run simultaneously
- Phase 3 depends on Phase 1 completion
- Phase 4-6 are sequential

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| R2 upload failures | Medium | Retry logic with exponential backoff |
| inotifywait limits | Low | Selective directory watching |
| GHCR rate limits | Low | Use authenticated pulls |
| Model download failures | Medium | Resume support already implemented |

---

## Success Metrics

1. **R2 Sync**: 100% of generated files uploaded within 30 seconds
2. **Model Downloads**: All enabled models download on first startup
3. **Video Generation**: WAN 2.2 720p video in < 2 minutes with TurboDiffusion
4. **Pod Startup**: Total startup time < 10 minutes (including model download)

---

*Draft v1 - Ready for self-critique*
