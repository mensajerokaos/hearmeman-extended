---
author: oz
model: claude-opus-4-5
date: 2025-12-24 22:20
task: Master Plan Overview for Hearmeman Extended Template PRD
---

# Master Plan: Hearmeman Extended Template

## Overview

Create a custom RunPod template that extends the Hearmeman "One Click - ComfyUI Wan t2v i2v VACE" template with additional AI capabilities for voice cloning, facial expressions, dance video generation, and image generation.

## Phases

| Phase | Name | Description | Deliverables |
|-------|------|-------------|--------------|
| 1 | Dockerfile Creation | Build Docker image with custom nodes | Dockerfile, requirements.txt |
| 2 | Start Script | Model download logic, env var handling | start.sh, download_models.sh |
| 3 | GHCR Setup | Repository creation, CI/CD workflow | GitHub Actions, push commands |
| 4 | Template Registration | RunPod template configuration | Template JSON, env vars doc |
| 5 | Testing & Verification | Local + RunPod deployment tests | Test checklist, verification script |

---

## Phase 1: Dockerfile Creation

### Objectives
- Extend Hearmeman base image with custom nodes baked in
- Install all Python dependencies for nodes
- Keep image size under 15GB (code only, no models)
- Follow Docker best practices for layer caching

### Components to Install
1. **ComfyUI-Manager** - Node management
2. **VibeVoice-ComfyUI** - TTS voice cloning
3. **ComfyUI-SCAIL-Pose** - Facial expressions
4. **comfyui_controlnet_aux** - ControlNet preprocessors
5. **Latest ComfyUI updates** - Z-Image/Lumina2 compatibility

### Dockerfile Structure
```
1. ARG BASE_IMAGE (Hearmeman or runpod/pytorch)
2. System packages (git, wget, ffmpeg)
3. Python dependencies (pip install)
4. Custom nodes (git clone)
5. Node dependencies (per-node requirements.txt)
6. Startup scripts
7. EXPOSE ports
8. ENTRYPOINT
```

---

## Phase 2: Start Script

### Objectives
- Smart storage detection (ephemeral vs persistent)
- On-demand model downloads based on env vars
- Resume support for interrupted downloads
- Model caching and symlinking

### Environment Variables
| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| ENABLE_VIBEVOICE | true/false | true | VibeVoice node + model |
| ENABLE_ZIMAGE | true/false | false | Z-Image Turbo components |
| ENABLE_STEADYDANCER | true/false | false | SteadyDancer model |
| ENABLE_SCAIL | true/false | false | SCAIL model |
| ENABLE_CONTROLNET | true/false | true | ControlNet preprocessors |
| VIBEVOICE_MODEL | 1.5B/Large/Large-Q8 | Large | VibeVoice model variant |
| UPDATE_NODES_ON_START | true/false | false | Git pull custom nodes |
| STORAGE_MODE | auto/ephemeral/persistent | auto | Override storage detection |

### Script Flow
1. Detect storage mode
2. Setup SSH if PUBLIC_KEY set
3. Start JupyterLab if JUPYTER_PASSWORD set
4. Download enabled models (parallel where possible)
5. Update custom nodes if UPDATE_NODES_ON_START
6. Start ComfyUI

---

## Phase 3: GHCR Setup

### Objectives
- Create GHCR repository for image hosting
- Setup GitHub Actions for automated builds
- Document manual push process

### Repository Structure
```
github.com/USERNAME/hearmeman-extended/
├── .github/
│   └── workflows/
│       └── docker-build.yml
├── Dockerfile
├── requirements.txt
├── start.sh
├── download_models.sh
└── README.md
```

### GitHub Actions Workflow
- Trigger: Push to main branch, manual dispatch
- Build: linux/amd64 platform
- Push: ghcr.io/USERNAME/hearmeman-extended:latest

---

## Phase 4: Template Registration

### Objectives
- Create RunPod template with all environment variables
- Document exposed ports
- Set appropriate disk sizes

### Template Configuration
| Setting | Value |
|---------|-------|
| Template Name | Hearmeman Extended |
| Container Image | ghcr.io/USERNAME/hearmeman-extended:latest |
| Container Disk | 50GB (for code + temp) |
| Volume Disk | 100-200GB (optional, for model persistence) |
| Volume Mount | /workspace |
| HTTP Ports | 8188 (ComfyUI), 8888 (Jupyter) |
| TCP Ports | 22 (SSH) |

### Environment Variable Groups
1. **Feature Toggles**: ENABLE_* variables
2. **Model Selection**: VIBEVOICE_MODEL, etc.
3. **Behavior**: UPDATE_NODES_ON_START, STORAGE_MODE
4. **Inherited**: WAN_720P, WAN_480P, VACE, etc.

---

## Phase 5: Testing & Verification

### Objectives
- Test Docker image locally
- Deploy to RunPod and verify all features
- Create health check script

### Test Matrix
| Test | Method | Pass Criteria |
|------|--------|---------------|
| Docker build | Local | Exit 0, size <15GB |
| Container start | Local | ComfyUI accessible on 8188 |
| SSH access | RunPod | SSH connection successful |
| VibeVoice node | RunPod | Node appears in ComfyUI |
| Model download | RunPod | Models appear in dropdown |
| TTS generation | RunPod | Audio file generated |
| Storage detection | RunPod | Correct mode detected |

### Verification Checklist
```bash
# 1. GPU available
nvidia-smi

# 2. ComfyUI running
curl -s localhost:8188/system_stats | jq .

# 3. Custom nodes installed
ls /workspace/ComfyUI/custom_nodes/

# 4. Models downloaded
ls /workspace/ComfyUI/models/*/

# 5. VibeVoice functional
# Run test workflow
```

---

## Timeline Estimate

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Phase 1 | 2-3 hours | Research complete |
| Phase 2 | 1-2 hours | Phase 1 |
| Phase 3 | 30 min | GitHub account |
| Phase 4 | 30 min | Image pushed |
| Phase 5 | 1-2 hours | All phases |
| **Total** | **5-8 hours** | |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Base image changes | Pin Hearmeman version or use runpod/pytorch |
| Model URL changes | Use HuggingFace hub CLI for downloads |
| VRAM exceeded | Document model swapping, use Q8 variants |
| Large download times | Implement resume support, parallel downloads |
| Node compatibility | Test node versions, pin git commits |

---

## Success Criteria

1. **Image builds** in under 30 minutes
2. **Image size** under 15GB
3. **Cold start** (with model downloads) under 20 minutes
4. **All enabled features** functional
5. **Storage detection** works correctly
6. **Documentation** complete and accurate
