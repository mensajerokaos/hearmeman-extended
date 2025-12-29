# Phase 3: GHCR Registry Setup - Implementation Specification

This document details the configuration for automating Docker builds and pushing to the GitHub Container Registry (GHCR).

## Step 3.1: Create GitHub Actions Workflow

**File Path:** `/home/oz/projects/2025/oz/12/runpod/.github/workflows/docker-build.yml`

This workflow automates the build and push process to GHCR on every push to the `main` branch or when a new tag is created.

```yaml
name: Docker Build and Push to GHCR

on:
  push:
    branches:
      - main
    tags:
      - 'v*'

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
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to the Container registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata (tags, labels) for Docker
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}
            type=sha,format=long
            type=ref,event=tag

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./docker
          file: ./docker/Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          platforms: linux/amd64
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Verification
Run the following command to verify the YAML syntax:
```bash
yamllint .github/workflows/docker-build.yml
```

## Step 3.2: Add GHCR Labels to Dockerfile

**File Path:** `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile`

Adding OCI (Open Container Initiative) labels helps GHCR link the image to the repository and provide metadata in the GitHub UI.

### BEFORE
```dockerfile
# ============================================
# Hearmeman Extended Template
# ============================================
ARG BASE_IMAGE=runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04
FROM ${BASE_IMAGE}

# Build arguments
```

### AFTER
```dockerfile
# ============================================
# Hearmeman Extended Template
# ============================================
ARG BASE_IMAGE=runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04
FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.title="Hearmeman Extended"
LABEL org.opencontainers.image.description="Extended ComfyUI environment for Hearmeman with advanced AI models"
LABEL org.opencontainers.image.source="https://github.com/oz/runpod"
LABEL org.opencontainers.image.licenses="MIT"

# Build arguments
```

## Step 3.3: Create GitHub PAT Secret

To allow the workflow to push to GHCR if using a Personal Access Token (though `GITHUB_TOKEN` is preferred for standard actions), or for local CLI access, a PAT is required.

### Required Permissions
- `write:packages`: To upload images to GHCR.
- `read:packages`: To download images from GHCR.

### Create Secret via GitHub CLI
If you need to store a custom PAT for specific cross-repository needs:
```bash
gh secret set GHCR_PAT --body "YOUR_TOKEN_HERE"
```

### Verification
Check if the secret is configured:
```bash
gh secret list
```
