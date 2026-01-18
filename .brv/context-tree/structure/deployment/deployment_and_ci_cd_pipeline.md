## Relations
@structure/infrastructure/docker_infrastructure.md
@structure/docker/startup_process.md

## Raw Concept
**Task:**
Document Deployment and CI/CD Infrastructure

**Changes:**
- Documents the CI/CD pipeline for image building and publishing
- Provides standardized RunPod pod creation commands for various tiers
- Formalizes the container startup sequence and environment detection
- Automates image build/publish and pod deployment lifecycles
- Secures sensitive credentials using native platform secret managers

**Files:**
- docker/start.sh
- .github/workflows/docker-build.yml

**Flow:**
Commit -> GitHub Actions Build -> GHCR Image -> runpodctl Create Pod -> Pod Runtime

**Timestamp:** 2026-01-18

## Narrative
### Structure
- .github/workflows/docker-build.yml: CI/CD workflow
- docker/start.sh: Runtime initialization and orchestration
- RunPod Secrets: r2_access_key, r2_secret_key, civitai_key

- .github/workflows/docker-build.yml: CI pipeline
- RunPod Creation Commands: minimal, standard, full, turbodiffusion
- Datacenter Speed Comparison: US Secure vs Community vs EU

### Dependencies
- GitHub Actions (GHCR)
- RunPod API/CLI (runpodctl)
- RunPod Secrets management

- GitHub Actions (GHCR, Docker Buildx)
- RunPod API (runpodctl)
- RunPod Secrets for credentials

### Features
- Automated Docker builds on push to main/master branches
- Conditional model baking (WAN, Illustrious) via workflow dispatch
- Disk space optimization on GHA runners (~20GB freed)
- Tiered RunPod deployment commands (Minimal, Standard, Full, TurboDiffusion)
- Automated GPU VRAM detection and memory mode assignment
- Integrated SSH (key-based) and JupyterLab access

- Automatic GHCR publishing on push to `docker/`
- Conditional model baking (WAN, Illustrious) via GitHub workflow inputs
- GitHub Actions disk space optimization (removing dotnet, android, etc.)
- RunPod pod creation commands for different GPU tiers
- Datacenter selection guide (US Secure Cloud 51MB/s recommended)
- Secret management via `{{RUNPOD_SECRET_*}}` syntax
