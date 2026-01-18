## Relations
@structure/docker/startup_process.md
@design/infrastructure/datacenter_benchmarks.md

## Raw Concept
**Task:**
RunPod Deployment Documentation

**Changes:**
- Provides production-ready deployment commands for RunPod pods
- Establishes secret management patterns for R2 and CivitAI keys

**Files:**
- docker/docker-compose.yml
- docker/start.sh

**Flow:**
Create secrets in RunPod -> Construct runpodctl command -> Launch pod -> Injected secrets available at runtime

**Timestamp:** 2026-01-18

## Narrative
### Structure
- runpodctl commands
- Secret mapping table
- Port security recommendations

### Dependencies
- runpodctl CLI
- RunPod Secrets (Encrypted)

### Features
- Standardized pod creation commands for different GPU types (4090, A6000, A100)
- Secure credential management via `{{RUNPOD_SECRET_*}}`
- Port configuration for ComfyUI (8188), Jupyter (8888), SSH (22), and XTTS (8000)
- Support for visible and secret environment variables
