# RunPod R2 Deployment - Master Overview (GE-Ready)

## Clarity Score: 9/10

---

## Prerequisites Checklist

Before starting implementation, verify:

```bash
# 1. Docker installed and running
docker --version  # Expected: Docker version 24+

# 2. GitHub CLI authenticated
gh auth status  # Expected: Logged in to github.com

# 3. R2 credentials available
cat ~/.cloudflare/r2-credentials.json 2>/dev/null || echo "Need to create credentials file"

# 4. Working directory correct
cd /home/oz/projects/2025/oz/12/runpod && pwd

# 5. Existing files present
ls docker/Dockerfile docker/start.sh docker/download_models.sh
```

---

## Phase Summary

| Phase | Name | Effort | Dependencies | Parallel With |
|-------|------|--------|--------------|---------------|
| P1 | R2 Sync Infrastructure | 2h | None | P2 |
| P2 | Model Download Updates | 1h | None | P1 |
| P3 | GHCR Registry Setup | 1.5h | P1 | - |
| P4 | RunPod Template Config | 1h | P3 | - |
| P5 | Workflow Testing | 1.5h | P4 | - |
| P6 | Documentation | 0.5h | P5 | - |

**Total Estimated Effort**: 7.5 hours

---

## Terminal Execution Matrix

```
Terminal 1 (T1):  P1 ──────────────────▶ P3 ──▶ P4 ──▶ P5 ──▶ P6
                   │
Terminal 2 (T2):  P2 ─────┘ (joins after P1+P2 complete)
```

| Terminal | Phase | Command | Start After |
|----------|-------|---------|-------------|
| T1 | P1 | See phase-1.md | Immediate |
| T2 | P2 | See phase-2.md | Immediate |
| T1 | P3 | See phase-3.md | P1 complete |
| T1 | P4 | See phase-4.md | P3 complete |
| T1 | P5 | Manual testing | P4 complete |
| T1 | P6 | See phase-6.md | P5 complete |

---

## Phase 1: R2 Sync Infrastructure

**Objective**: Create R2 upload capability with real-time file watching daemon.

**Detailed Specification**: `./phase-1.md`

**Acceptance Criteria**:
1. `upload_to_r2.py` successfully uploads a test file to R2
2. `r2_sync.sh` detects new files in output directory within 2 seconds
3. Docker image builds without errors
4. Container starts with R2 sync daemon running in background

**Rollback**:
```bash
# Revert Dockerfile changes
git checkout docker/Dockerfile docker/start.sh
# Remove new files
rm -f docker/upload_to_r2.py docker/r2_sync.sh
```

---

## Phase 2: Model Download Updates

**Objective**: Add TurboDiffusion model support and verify WAN 2.2 downloads.

**Detailed Specification**: `./phase-2.md`

**Acceptance Criteria**:
1. ENABLE_TURBODIFFUSION=true triggers model download
2. WAN 2.2 720p model path resolves correctly
3. Download verification checks file sizes

**Rollback**:
```bash
git checkout docker/download_models.sh
```

---

## Phase 3: GHCR Registry Setup

**Objective**: Configure GitHub Actions for automated Docker image builds to GHCR.

**Detailed Specification**: `./phase-3.md`

**Acceptance Criteria**:
1. GitHub Actions workflow triggers on push to main
2. Image pushes to ghcr.io/oz/hearmeman-extended:latest
3. Image pullable from RunPod

**Rollback**:
```bash
rm -rf .github/workflows/docker-build.yml
```

---

## Phase 4: RunPod Template Configuration

**Objective**: Create RunPod template with R2 environment variables and secrets.

**Detailed Specification**: `./phase-4.md`

**Acceptance Criteria**:
1. Template accessible in RunPod console
2. Pod starts successfully with GPU detected
3. R2 environment variables visible in container
4. Secrets not exposed in logs

**Rollback**:
```bash
# Delete template via RunPod console
# No local files to revert
```

---

## Phase 5: Workflow Testing

**Objective**: Validate end-to-end video generation with R2 upload.

**Detailed Specification**: `./phase-5.md`

**Acceptance Criteria**:
1. WAN 2.2 generates 720p video
2. TurboDiffusion reduces generation time by 50%+
3. Generated video appears in R2 bucket within 60 seconds
4. Video playable from R2 public URL

**Rollback**:
```bash
# Stop pod, no permanent changes
runpodctl stop pod $POD_ID
```

---

## Phase 6: Documentation

**Objective**: Update project documentation with deployment instructions.

**Detailed Specification**: `./phase-6.md`

**Acceptance Criteria**:
1. CLAUDE.md updated with R2 variables
2. DEPLOYMENT.md created with step-by-step guide
3. All environment variables documented

**Rollback**:
```bash
git checkout CLAUDE.md
rm -f docs/DEPLOYMENT.md
```

---

## Environment Variables Reference

### Build-time (Dockerfile)
```dockerfile
ENV ENABLE_R2_SYNC="false"
ENV R2_BUCKET="runpod"
```

### Runtime (RunPod Template)
| Variable | Value | Type |
|----------|-------|------|
| R2_ENDPOINT | https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com | Visible |
| R2_BUCKET | runpod | Visible |
| R2_ACCESS_KEY | (from secrets) | Secret |
| R2_SECRET_KEY | (from secrets) | Secret |
| ENABLE_R2_SYNC | true | Visible |
| WAN_720P | true | Visible |
| ENABLE_TURBODIFFUSION | true | Visible |

---

## Risk Mitigation

| Risk | Mitigation | Fallback |
|------|------------|----------|
| R2 upload timeout | 3 retries with 5s backoff | Queue failed uploads for batch retry |
| inotifywait crash | Supervisor or systemd restart | Manual upload script |
| GHCR rate limit | Use authenticated pulls | Cache image on network volume |
| Model download fail | wget -c resume support | Manual HuggingFace download |

---

## Success Verification Commands

After full deployment:

```bash
# 1. Verify R2 sync working
ssh runpod "ls /workspace/ComfyUI/output/*.mp4 | head -1 | xargs python /upload_to_r2.py"

# 2. Check R2 bucket
aws s3 ls s3://runpod/outputs/ --endpoint-url https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com

# 3. Verify models loaded
ssh runpod "ls -la /workspace/ComfyUI/models/diffusion_models/ | grep wan"

# 4. Check sync daemon running
ssh runpod "ps aux | grep r2_sync"
```

---

*Master Overview complete - expand phases for detailed implementation*
