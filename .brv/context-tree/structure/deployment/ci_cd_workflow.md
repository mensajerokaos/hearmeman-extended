## Relations
@structure/docker/dockerfile_build_process.md
@structure/deployment/runpod_deployment.md

## Raw Concept
**Task:**
CI/CD Workflow Documentation

**Changes:**
- Documents the automated CI/CD pipeline for image building
- Explains the model baking logic for production images

**Files:**
-  .github/workflows/docker-build.yml 
- docker/Dockerfile

**Flow:**
Push to main -> Free disk space -> Setup Buildx -> Login to GHCR -> Build and Push with cache

**Timestamp:** 2026-01-18

## Narrative
### Structure
- .github/workflows/docker-build.yml
- Step-by-step build breakdown
- Tag selection matrix

### Dependencies
- GitHub Container Registry (GHCR)
- Docker Buildx
- GITHUB_TOKEN

### Features
- Automated image build and publish on push to `docker/`
- Conditional model baking (WAN, Illustrious) via workflow dispatch
- Disk space optimization for GitHub Actions runners
- Layer caching for faster subsequent builds
- OCI metadata generation for image tagging
