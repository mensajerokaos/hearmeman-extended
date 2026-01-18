## Relations
@structure/docker/dockerfile_build_process.md

## Raw Concept
**Task:**
Document GitHub Actions CI/CD Workflow

**Changes:**
- Automates the image build and publish pipeline to GHCR
- Ensures build success on restricted-space runners via optimization cleanup

**Files:**
-  .github/workflows/docker-build.yml 

**Flow:**
Push -> Free Disk -> Checkout -> Buildx -> Login -> Tag -> Build & Push -> GHCR

**Timestamp:** 2026-01-18

## Narrative
### Structure
- .github/workflows/docker-build.yml

### Dependencies
- GITHUB_TOKEN (GHCR authentication)
- Docker Buildx
- Disk space optimization (Removing dotnet, ghc, etc.)

### Features
- Automatic build on push to main/master branches (paths: docker/**)
- Manual triggers with model baking options (WAN 720p/480p, Illustrious)
- OCI metadata generation and GHCR publishing
- Layer caching via GitHub Actions cache (type=gha)
