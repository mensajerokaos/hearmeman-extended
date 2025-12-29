---
title: RunPod R2 Deployment PRD
version: 1.0
date: 2025-12-29
author: oz + claude-opus-4-5
status: Ready for Implementation
---

# RunPod R2 Deployment - Product Requirements Document

## Executive Summary

Deploy the hearmeman-extended ComfyUI template to RunPod with automatic output synchronization to Cloudflare R2. This enables persistent storage for generated images and videos without RunPod's ephemeral storage limitations. The solution uses GHCR for Docker image hosting and configures WAN 2.2 + TurboDiffusion for high-speed video generation.

### Key Benefits

| Benefit | Impact |
|---------|--------|
| Persistent Output Storage | Generated files survive pod restarts via R2 sync |
| Reduced Startup Time | Models cached on network volume, not re-downloaded |
| Automated CI/CD | GHCR builds on every push to main branch |
| Cost Optimization | Pay only for R2 storage, not RunPod volume disk |

---

## Architecture Overview

```
+------------------+     +------------------+     +------------------+
|   GitHub Repo    |---->|      GHCR       |---->|     RunPod      |
|  (Source Code)   |     | (Docker Image)   |     |    (GPU Pod)    |
+------------------+     +------------------+     +------------------+
        |                                                   |
        | Actions                                           | inotifywait
        v                                                   v
+------------------+                              +------------------+
| Docker Build     |                              | /workspace/      |
| (Multi-layer)    |                              | ComfyUI/output/  |
+------------------+                              +------------------+
                                                            |
                                                            | boto3
                                                            v
                                                  +------------------+
                                                  |  Cloudflare R2   |
                                                  |  (runpod bucket) |
                                                  +------------------+
```

### Data Flow

1. **Code Push**: Developer pushes to GitHub main branch
2. **CI/CD Build**: GitHub Actions builds Docker image, pushes to GHCR
3. **Pod Startup**: RunPod pulls image from GHCR, downloads models
4. **Generation**: ComfyUI generates images/videos to /workspace/ComfyUI/output
5. **R2 Sync**: inotifywait detects new files, boto3 uploads to R2
6. **Access**: Files available via R2 public URL or S3 API

---

## Implementation Phases

### Phase Summary

| Phase | Name | Effort | Dependencies | Terminal |
|-------|------|--------|--------------|----------|
| P1 | R2 Sync Infrastructure | 2h | None | T1 |
| P2 | Model Download Updates | 1h | None | T2 (parallel) |
| P3 | GHCR Registry Setup | 1.5h | P1 | T1 |
| P4 | RunPod Template Config | 1h | P3 | T1 |
| P5 | Workflow Testing | 1.5h | P4 | T1 |
| P6 | Documentation | 0.5h | P5 | T1 |

**Total Estimated Effort**: 7.5 hours

### Parallel Execution Map

```
Terminal 1 (T1):  P1 ──────────────────▶ P3 ──▶ P4 ──▶ P5 ──▶ P6
                   │
Terminal 2 (T2):  P2 ─────┘ (joins after P1+P2 complete)
```

---

## Phase 1: R2 Sync Infrastructure

**Objective**: Create R2 upload capability with real-time file watching daemon.

**Detailed Spec**: `./runpod-r2-deployment-pre/phase-1.md`

### Files to Create/Modify

| Action | File | Description |
|--------|------|-------------|
| CREATE | `docker/upload_to_r2.py` | Python script with boto3 S3 client, retry logic |
| CREATE | `docker/r2_sync.sh` | Bash daemon using inotifywait |
| MODIFY | `docker/Dockerfile` | Add inotify-tools, boto3, copy scripts |
| MODIFY | `docker/start.sh` | Add R2 sync daemon startup |

### Key Implementation: upload_to_r2.py

```python
import boto3
from botocore.config import Config

def get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("R2_ENDPOINT"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4"),
        region_name="auto"
    )

def upload_file(file_path, bucket, retries=3, backoff=2):
    # Retry logic with exponential backoff
    # Organized path: outputs/YYYY-MM-DD/filename
    ...
```

### Key Implementation: r2_sync.sh

```bash
#!/bin/bash
WATCH_DIR="/workspace/ComfyUI/output"
inotifywait -m -e close_write --format '%w%f' "$WATCH_DIR" | while read NEW_FILE
do
    if [[ "$NEW_FILE" =~ \.(png|jpg|mp4|webm|wav)$ ]]; then
        python3 /upload_to_r2.py "$NEW_FILE" &
    fi
done
```

### Acceptance Criteria

- [ ] `upload_to_r2.py` uploads test file to R2 successfully
- [ ] `r2_sync.sh` detects new files within 2 seconds
- [ ] Docker image builds without errors
- [ ] Container starts with R2 sync daemon running

### Rollback

```bash
git checkout docker/Dockerfile docker/start.sh
rm -f docker/upload_to_r2.py docker/r2_sync.sh
```

---

## Phase 2: Model Download Updates

**Objective**: Add TurboDiffusion model support and download verification.

**Detailed Spec**: `./runpod-r2-deployment-pre/phase-2.md`

### Files to Modify

| Action | File | Description |
|--------|------|-------------|
| MODIFY | `docker/download_models.sh` | Add TurboDiffusion section, verify_download() |
| MODIFY | `docker/Dockerfile` | Add ENABLE_TURBODIFFUSION env var |

### Key Implementation: TurboDiffusion Section

```bash
if [ "${ENABLE_TURBODIFFUSION:-false}" = "true" ]; then
    echo "[TurboDiffusion] Downloading acceleration models..."
    hf_download "TurboDiffusion/TurboWan2.2-I2V-A14B-720P" \
        "TurboWan2.2-I2V-A14B-high-720P-quant.pth" \
        "$MODELS_DIR/diffusion_models/TurboWan2.2-I2V-A14B-high-720P-quant.pth"
fi
```

### Key Implementation: verify_download()

```bash
verify_download() {
    local FILE="$1"
    local MIN_SIZE_MB="$2"
    local BYTES=$((MIN_SIZE_MB * 1024 * 1024))

    local ACTUAL_SIZE=$(stat -c%s "$FILE")
    if [ "$ACTUAL_SIZE" -lt "$BYTES" ]; then
        echo "  [Error] Verification failed: $FILE"
        return 1
    fi
    return 0
}
```

### Acceptance Criteria

- [ ] ENABLE_TURBODIFFUSION=true triggers model download
- [ ] verify_download() catches incomplete downloads
- [ ] bash -n download_models.sh passes

### Rollback

```bash
git checkout docker/download_models.sh docker/Dockerfile
```

---

## Phase 3: GHCR Registry Setup

**Objective**: Configure GitHub Actions for automated Docker builds.

**Detailed Spec**: `./runpod-r2-deployment-pre/phase-3.md`

### Files to Create/Modify

| Action | File | Description |
|--------|------|-------------|
| CREATE | `.github/workflows/docker-build.yml` | GitHub Actions workflow |
| MODIFY | `docker/Dockerfile` | Add OCI labels |

### Key Implementation: GitHub Actions Workflow

```yaml
name: Docker Build and Push to GHCR

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: oz/hearmeman-extended

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: ./docker
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          platforms: linux/amd64
```

### Acceptance Criteria

- [ ] GitHub Actions workflow triggers on push to main
- [ ] Image pushes to ghcr.io/oz/hearmeman-extended:latest
- [ ] Image pullable from RunPod

### Rollback

```bash
rm -rf .github/workflows/docker-build.yml
```

---

## Phase 4: RunPod Template Configuration

**Objective**: Create RunPod template with R2 credentials.

**Detailed Spec**: `./runpod-r2-deployment-pre/phase-4.md`

### Template Settings

| Setting | Value |
|---------|-------|
| Template Name | `hearmeman-extended-r2` |
| Container Image | `ghcr.io/oz/hearmeman-extended:latest` |
| Container Disk | 20 GB |
| Volume Disk | 100 GB |
| Volume Mount Path | `/workspace` |
| HTTP Ports | `8188, 8888` |
| TCP Ports | `22` |

### Environment Variables

**Visible Variables**:

| Variable | Value |
|----------|-------|
| R2_ENDPOINT | `https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com` |
| R2_BUCKET | `runpod` |
| ENABLE_R2_SYNC | `true` |
| WAN_720P | `true` |
| ENABLE_TURBODIFFUSION | `true` |
| GPU_TIER | `auto` |

**Secret Variables** (via RunPod Secrets):

| Variable | Source |
|----------|--------|
| R2_ACCESS_KEY_ID | RunPod Secret |
| R2_SECRET_ACCESS_KEY | RunPod Secret |
| CIVITAI_API_KEY | RunPod Secret (optional) |

### GPU Recommendations

| GPU | VRAM | Tier | Recommended For |
|-----|------|------|-----------------|
| RTX 4090 | 24 GB | Consumer | Fast image gen, quantized video |
| A6000 | 48 GB | Prosumer | WAN 2.2 720p, high-res video |
| A100 | 80 GB | Datacenter | Native BF16, batch processing |

### Acceptance Criteria

- [ ] Template accessible in RunPod console
- [ ] Pod starts with GPU detected
- [ ] R2 environment variables visible in container
- [ ] Secrets not exposed in logs

### Rollback

Delete template via RunPod console.

---

## Phase 5: Workflow Testing

**Objective**: Validate end-to-end video generation with R2 upload.

### Test Procedure

1. **Deploy Pod**: Start pod from `hearmeman-extended-r2` template
2. **Verify Startup**: Check logs for model downloads, R2 sync daemon
3. **Run Workflow**: Load WAN 2.2 T2V workflow, generate 5-second video
4. **Verify R2 Upload**: Check R2 bucket for uploaded video
5. **Measure Performance**: Record generation time with TurboDiffusion

### Verification Commands

```bash
# Check R2 sync daemon running
ps aux | grep r2_sync

# List R2 bucket contents
aws s3 ls s3://runpod/outputs/ \
    --endpoint-url https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com

# Verify models loaded
ls -la /workspace/ComfyUI/models/diffusion_models/ | grep wan
```

### Acceptance Criteria

- [ ] WAN 2.2 generates 720p video successfully
- [ ] TurboDiffusion reduces generation time by 50%+
- [ ] Generated video appears in R2 within 60 seconds
- [ ] Video playable from R2 URL

### Rollback

```bash
runpodctl stop pod $POD_ID
```

---

## Phase 6: Documentation

**Objective**: Update project documentation.

### Files to Create/Modify

| Action | File | Description |
|--------|------|-------------|
| MODIFY | `CLAUDE.md` | Add R2 environment variables |
| CREATE | `docs/DEPLOYMENT.md` | Step-by-step deployment guide |
| CREATE | `docs/runpod-template-config.md` | Template configuration reference |

### Acceptance Criteria

- [ ] CLAUDE.md updated with R2 configuration
- [ ] DEPLOYMENT.md provides complete setup guide
- [ ] All environment variables documented

### Rollback

```bash
git checkout CLAUDE.md
rm -f docs/DEPLOYMENT.md docs/runpod-template-config.md
```

---

## Environment Variables Reference

### Build-time (Dockerfile)

```dockerfile
ENV ENABLE_R2_SYNC="false"
ENV R2_BUCKET="runpod"
ENV R2_ENDPOINT="https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com"
ENV ENABLE_TURBODIFFUSION="false"
```

### Runtime (RunPod Template)

| Variable | Value | Type |
|----------|-------|------|
| R2_ENDPOINT | https://...eu.r2.cloudflarestorage.com | Visible |
| R2_BUCKET | runpod | Visible |
| R2_ACCESS_KEY_ID | (from secrets) | Secret |
| R2_SECRET_ACCESS_KEY | (from secrets) | Secret |
| ENABLE_R2_SYNC | true | Visible |
| WAN_720P | true | Visible |
| ENABLE_TURBODIFFUSION | true | Visible |
| GPU_TIER | auto | Visible |

---

## Risk Assessment

| Risk | Severity | Mitigation | Fallback |
|------|----------|------------|----------|
| R2 upload timeout | Medium | 3 retries, 5s backoff | Queue for batch retry |
| inotifywait crash | Low | Log monitoring | Manual upload script |
| GHCR rate limit | Low | Authenticated pulls | Cache on network volume |
| Model download fail | Medium | wget -c resume | Manual HuggingFace download |
| TurboDiffusion incompatible | Low | Test before deploy | Disable, use standard inference |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| R2 Upload Latency | < 30 seconds for 100MB file |
| Model Download Time | < 10 minutes (cached volume) |
| Video Generation (WAN 2.2 720p, 5s) | < 2 minutes with TurboDiffusion |
| Pod Startup Time | < 5 minutes (warm start) |
| Upload Success Rate | > 99% |

---

## Appendix: Quick Start Commands

### Local Docker Build

```bash
cd /home/oz/projects/2025/oz/12/runpod/docker
docker compose build
docker compose up -d
```

### Test R2 Upload Locally

```bash
export R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com
export R2_ACCESS_KEY_ID=your_key
export R2_SECRET_ACCESS_KEY=your_secret
export R2_BUCKET=runpod

python docker/upload_to_r2.py test_file.png
```

### Push to GHCR Manually

```bash
docker tag hearmeman-extended:local ghcr.io/oz/hearmeman-extended:latest
echo $GITHUB_TOKEN | docker login ghcr.io -u oz --password-stdin
docker push ghcr.io/oz/hearmeman-extended:latest
```

---

*PRD Complete - Ready for Implementation*
