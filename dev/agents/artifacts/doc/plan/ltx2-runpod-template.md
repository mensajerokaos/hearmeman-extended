---
title: LTX2 RunPod Template Integration
created: 2026-01-22T19:52:51-06:00
author: $USER
model: claude-haiku-4-5-20251001
phases: 5
---

# PRD: LTX2 RunPod Template Integration

## Executive Summary

Integration of Lightricks' 19B parameter LTX-2 video generation model into the existing RunPod ComfyUI deployment template. The plan modifies 7 files across 5 sequential phases with parallel execution opportunities (P2+P3), spanning approximately 140 minutes of implementation work. Key integration points follow established patterns: conditional enable flags (ENABLE_LTX2), FP8/FP16 quantization variants, Git LFS-based HuggingFace downloads, and ComfyUI custom node installation (ComfyUI-LTXVideo).

LTX-2 is a 19B parameter video generation model capable of producing high-quality video from text or image prompts. It supports up to 800+ frames with sufficient VRAM and shares architectural components with WAN 2.1 when available.

## Architecture

```
LTX2 RunPod Template Architecture
─────────────────────────────────
RunPod Container (hearmeman-extended)
├── ComfyUI Core
│   ├── LTX2 Workflow Loader
│   ├── LTX2 Model Loader
│   ├── VRAM Management (800+ frames)
│   └── LTX2 Custom Node (ComfyUI-LTXVideo)
├── Shared Model Dependencies
│   ├── Text Encoder (Shared with WAN 2.1)
│   ├── VAE (Shared with WAN 2.1)
│   └── CLIP Vision (Shared)
└── External Services
    ├── R2 Storage (outputs/ltx2/)
    ├── HuggingFace (Models, Git LFS)
    └── RunPod Secrets (HF_TOKEN)
```

## Phase Overview

| Phase | Title | Depends On | Parallel | Files | Effort |
|-------|-------|-----------|----------|-------|--------|
| **P1** | Docker Environment Setup | - | - | `docker/Dockerfile:1-620`, `docker/docker-compose.yml:1-180` | 45 min |
| **P2** | Custom Node Installation | P1 | P3 | `docker/Dockerfile:250-280` | 30 min |
| **P3** | Model Download Integration | P1 | P2 | `docker/download_models.sh:700-750` | 30 min |
| **P4** | Workflow Files | P2, P3 | - | `ltx2-text2video.json`, `ltx2-image2video.json` | 20 min |
| **P5** | Documentation | P4 | - | `docker/CLAUDE.md:400-650` | 15 min |

## Detailed Phases

### Phase 1: Docker Environment Setup

**Purpose**: Configure Docker environment to support LTX-2 model installation and execution.

**Files Modified**:
- `docker/Dockerfile:30-31, 97-100, 440-455`
- `docker/docker-compose.yml:145-152, 165-175`

**Steps**:

| Step | File:Line | Action |
|------|-----------|--------|
| 1.1 | `docker-compose.yml:145-152` | Add LTX-2 environment variables |
| 1.2 | `docker-compose.yml:165-175` | Add GPU tier comments |
| 1.3 | `docker/Dockerfile:30-31` | Install Git LFS in Stage 1 |
| 1.4 | `docker/Dockerfile:97-100` | Add BAKE_LTX2 build arg and LTX2_VARIANT |
| 1.5 | `docker/Dockerfile:440-455` | Add conditional LTX-2 build-time download |

**Environment Variables**:
```yaml
# LTX-2 Video Generation (Lightricks 19B parameter model)
# VRAM: 16GB (FP8) / 32GB (FP16) / 48GB+ (full precision)
# Size: 27GB (FP8) / 54GB (FP16)
- ENABLE_LTX2=false
- LTX2_VARIANT=fp8
# VRAM: 800+ frames with 16GB GPU using sequential_cpu_offload
- ENABLE_LTX2_VRAM_MANAGEMENT=false
# Output directory for LTX-2 generated videos
- LTX2_OUTPUT_DIR=/workspace/ComfyUI/output/ltx2
```

**GPU Tier Recommendations**:
- 16GB VRAM: Use `LTX2_VARIANT=fp8` (27GB model, sequential CPU offload)
- 24GB VRAM: Use `LTX2_VARIANT=fp8` (27GB model, supports 400-600 frames)
- 32GB VRAM: Use `LTX2_VARIANT=fp16` (54GB model, supports 800+ frames)
- 48GB+ VRAM: Use `LTX2_VARIANT=full` (full precision, maximum quality)

**Build Arguments**:
```dockerfile
ARG BAKE_LTX2=false
ARG LTX2_VARIANT=fp8
```

**Verification**:
```bash
cd /home/oz/projects/2025/oz/12/runpod/docker && \
grep -n "git-lfs\|LTX2" Dockerfile docker-compose.yml
```

---

### Phase 2: Custom Node Installation

**Purpose**: Install ComfyUI-LTXVideo custom node to enable LTX-2 workflow support.

**Files Modified**: `docker/Dockerfile:325-395`

**Steps**:

| Step | File:Line | Action |
|------|-----------|--------|
| 2.1 | `docker/Dockerfile:325-340` | Insert Stage 3.5 header for LTX2 custom node |
| 2.2 | `docker/Dockerfile:341-355` | Clone ComfyUI-LTXVideo repository |
| 2.3 | `docker/Dockerfile:356-370` | Install Python dependencies |
| 2.4 | `docker/Dockerfile:371-385` | Verify node installation and imports |
| 2.5 | `docker/Dockerfile:386-395` | Add comprehensive verification script |

**Implementation**:
```dockerfile
# Clone ComfyUI-LTXVideo repository
RUN cd /workspace/ComfyUI/custom_nodes && \
    git clone https://github.com/Lightricks/ComfyUI-LTXVideo.git && \
    cd ComfyUI-LTXVideo && \
    git fetch --all --tags && \
    git checkout v0.2.0

# Install Python dependencies
RUN if [ -f /workspace/ComfyUI/custom_nodes/ComfyUI-LTXVideo/requirements.txt ]; then \
    pip install --no-cache-dir -r /workspace/ComfyUI/custom_nodes/ComfyUI-LTXVideo/requirements.txt; \
    fi

# Verify LTX-2 custom node installation
RUN python3 -c "import ltx_video; print('✓ ltx_video module imported successfully')"
```

**Available Nodes** (from ComfyUI-LTXVideo):
- `LTX2Sampler`: Primary sampling node with LTX-2 specific settings
- `LTX2ModelLoader`: Load LTX-2 checkpoint with variant selection
- `LTX2TextEncoder`: Custom text encoder (falls back to shared)
- `LTX2ImageConditioning`: For image-to-video workflows

**Verification**:
```bash
cd /home/oz/projects/2025/oz/12/runpod/docker && \
grep -n "ComfyUI-LTXVideo\|ltx_video" Dockerfile
```

---

### Phase 3: Model Download Integration

**Purpose**: Implement runtime model download with VRAM-aware auto-fallback and HuggingFace authentication.

**Files Modified**: `docker/download_models.sh:690-735, 850-860`

**Steps**:

| Step | File:Line | Action |
|------|-----------|--------|
| 3.1 | `docker/download_models.sh:690-700` | Add VRAM validation with auto-fallback |
| 3.2 | `docker/download_models.sh:705-735` | Add `download_ltx2()` function |
| 3.3 | `docker/download_models.sh:850-860` | Integrate into main download flow |

**VRAM Auto-Fallback Logic**:
- FP16 variant if >=40GB VRAM
- FP8 variant if 24-39GB VRAM
- Error if <24GB VRAM (insufficient)

**Download Function**:
```bash
download_ltx2() {
    local variant="${LTX2_VARIANT:-fp8}"
    local model_path="/workspace/ComfyUI/models/diffusion_models"
    local hf_repo="Lightricks/LTX-2"

    # Validate HuggingFace token
    if [ -z "$HF_TOKEN" ]; then
        error "LTX-2 requires HF_TOKEN. Set via RunPod secret: RUNPOD_SECRET_hf_token"
        return 1
    fi

    # Download model based on variant
    case "$variant" in
        fp16)
            wget -q --show-progress -O "$model_path/ltx2_video_19B_fp16.safetensors" \
                "https://huggingface.co/$hf_repo/resolve/main/ltx2_video_19B_fp16.safetensors"
            ;;
        fp8)
            wget -q --show-progress -O "$model_path/ltx2_video_19B_fp8.safetensors" \
                "https://huggingface.co/$hf_repo/resolve/main/ltx2_video_19B_fp8.safetensors"
            ;;
    esac
}
```

**Verification**:
```bash
cd /home/oz/projects/2025/oz/12/runpod/docker && \
grep -A 50 "^download_ltx2()" download_models.sh | head -55
```

---

### Phase 4: Workflow Files

**Purpose**: Create ComfyUI workflow files for LTX-2 text-to-video and image-to-video generation.

**Files Created**:
- `docker/workflows/ltx2-text2video.json`
- `docker/workflows/ltx2-image2video.json`

**Workflow 1: Text-to-Video** (9 nodes)

| Node | Type | Configuration |
|------|------|---------------|
| 1 | CLIPLoader | `llama3_8b_text_encoder` |
| 2 | UNETLoader | `LTX-Video-19B-v0.9` |
| 3 | VAELoader | `ltx_video_vae` |
| 4 | CLIPTextEncode | Positive prompt |
| 5 | CLIPTextEncode | Negative prompt |
| 6 | EmptyLatentImage | 640x360, 129 frames |
| 7 | LTX2Sampler | 50 steps, euler, `force_offload: true` |
| 8 | VAEDecode | Tiling enabled |
| 9 | VHS_VideoCombine | webm, 24fps, save_output: true |

**Workflow 2: Image-to-Video** (11 nodes)

| Node | Type | Configuration |
|------|------|---------------|
| 1 | LoadImage | `input_image.png` |
| 2-6 | Same as text2video | CLIPLoader, UNETLoader, VAELoader, CLIPTextEncode x2 |
| 7 | LTX2ImageConditioning | `strength: 0.8`, `noise_strength: 0.5` |
| 8 | EmptyLatentImage | 640x360, 129 frames |
| 9 | LTX2Sampler | 50 steps, euler, `force_offload: true`, image conditioning |
| 10 | VAEDecode | Tiling enabled |
| 11 | VHS_VideoCombine | webm, 24fps, save_output: true |

**Key Configuration**:
- VRAM offloading: `force_offload: true` (enables sequential CPU offload)
- VRAM tiling: Enabled for <32GB GPUs
- Default resolution: 640x360, 129 frames, 24fps
- Output format: webm with timestamp prefix (`ltx2_output_[timestamp].webm`)
- Model references: LTX-Video-19B-v0.9 (27GB FP8), llama3_8b_text_encoder (~8GB), ltx_video_vae (~1GB)

**Verification**:
```bash
cd /home/oz/projects/2025/oz/12/runpod/docker/workflows && \
for f in ltx2-*.json; do
    python3 -m json.tool "$f" > /dev/null && echo "✓ $f valid JSON"
done
```

---

### Phase 5: Documentation

**Purpose**: Update CLAUDE.md with LTX-2 integration details and configuration guidance.

**Files Modified**: `docker/CLAUDE.md`

**Steps**:

| Step | File:Line | Action |
|------|-----------|--------|
| 5.1 | `CLAUDE.md:159-166` | Update GPU VRAM recommendation table |
| 5.2 | `CLAUDE.md:225-238` | Update Key Environment Variables table |
| 5.3 | `CLAUDE.md:169-189` | Update Storage Requirements table |
| 5.4 | `CLAUDE.md:48-167` | Add new LTX-2 section |
| 5.5 | `CLAUDE.md:290-296` | Update R2 Storage Estimates table |
| 5.6 | `CLAUDE.md:300-346` | Update HuggingFace Token section |
| 5.7 | `CLAUDE.md:350-373` | Update Pod Creation Command example |

**New LTX-2 Section**:
```markdown
## LTX-2 Video Generation (Lightricks)

**Repository**: [ComfyUI-LTXVideo](https://github.com/Lightricks/ComfyUI-LTXVideo)
**Model**: [LTX-2](https://huggingface.co/Lightricks/LTX-2) (19B parameters)
**Status**: Planned
**VRAM**: 16GB minimum (FP8), 24GB recommended (FP8), 32GB+ optimal (FP16)

Lightricks' LTX-2 is a 19B parameter video generation model that produces high-quality video from text or image prompts. Supports up to 800+ frames with sufficient VRAM.

### Features
- **Text-to-Video (T2V)**: Generate video from prompt
- **Image-to-Video (I2V)**: Animate images with prompt guidance
- **800+ Frame Generation**: With 32GB+ VRAM (FP16)
- **Frame Interpolation**: Smooth temporal consistency
- **Shared Architecture**: Uses WAN 2.1 text encoder and VAE when available

### Model Variants
| Variant | VRAM | Frames | Quality |
|---------|------|--------|---------|
| FP8 (default) | 16-24GB | 300-500 | Good |
| FP16 | 32GB+ | 800+ | Excellent |

### Configuration
```bash
export ENABLE_LTX2=true
export LTX2_VARIANT=fp8
export LTX2_OUTPUT_DIR=/workspace/ComfyUI/output/ltx2
```
```

**Updated Tables**:

*GPU VRAM Recommendation*:
| GPU VRAM | Recommended Model |
|----------|-------------------|
| 16GB (RTX 4080 Super) | VibeVoice 1.5B, LTX-2 (FP8, limited frames) |
| 24GB+ (RTX 4090, A6000) | VibeVoice 7B, LTX-2 (FP8), SteadyDancer (fp8) |
| 32GB+ (A6000 Ada, L40S) | LTX-2 (FP16, 800+ frames) |
| 40GB+ | LTX-2 (FP16), SteadyDancer (fp16) |

*Environment Variables*:
| Variable | Default | Size | Notes |
|----------|---------|------|-------|
| `ENABLE_LTX2` | false | 27-54GB | LTX-2 video generation (FP8/FP16) |
| `LTX2_VARIANT` | fp8 | - | Model quantization: fp8 or fp16 |
| `ENABLE_LTX2_VRAM_MANAGEMENT` | false | - | Enable VRAM optimization for >800 frames |
| `LTX2_OUTPUT_DIR` | (empty) | - | Custom output directory |

*Storage Requirements*:
| Component | Size | Notes |
|-----------|------|-------|
| **LTX-2 (FP8)** | ~27GB | 19B parameter model, 8-bit quantization |
| **LTX-2 (FP16)** | ~54GB | Full precision, 800+ frame generation |

*R2 Storage Estimates*:
| Output Type | Size | 10GB R2 = |
|------------|------|-----------|
| LTX-2 video (720p, 5 sec) | 100-200 MB | ~50-100 |
| LTX-2 video (720p, 10 sec) | 200-400 MB | ~25-50 |
| LTX-2 video (1080p, 5 sec) | 300-500 MB | ~20-33 |

**Verification**:
```bash
grep -n "LTX-2\|ENABLE_LTX2\|LTX2" CLAUDE.md
```

---

## Parallel Execution Map

```
Wave 1: [P1: Docker Environment Setup]
        Duration: 45 min
        Blocking: P2, P3

Wave 2: [P2: Custom Node Installation] ←→ [P3: Model Download Integration]
        Duration: 30 min each (parallel execution)
        Blocking: P4

Wave 3: [P4: Workflow Files]
        Duration: 20 min
        Blocking: P5

Wave 4: [P5: Documentation]
        Duration: 15 min
```

**Total Wall Clock Time**: ~95 minutes (with P2+P3 parallel)

---

## Implementation Order

1. **Phase 1** - Docker Environment Setup
   - Add environment variables to docker-compose.yml
   - Install Git LFS in Dockerfile
   - Add LTX-2 build arguments and download section

2. **Phase 2** - Custom Node Installation (parallel with P3)
   - Clone ComfyUI-LTXVideo repository
   - Install Python dependencies
   - Verify node imports

3. **Phase 3** - Model Download Integration (parallel with P2)
   - Implement VRAM validation with auto-fallback
   - Add download_ltx2() function
   - Integrate into main download flow

4. **Phase 4** - Workflow Files
   - Create ltx2-text2video.json
   - Create ltx2-image2video.json
   - Validate JSON syntax

5. **Phase 5** - Documentation
   - Add LTX-2 section to CLAUDE.md
   - Update environment variables table
   - Update storage requirements
   - Update R2 storage estimates
   - Update HuggingFace token requirements
   - Update pod creation example

---

## Verification Checklist

### Phase 1 Verification
```bash
cd /home/oz/projects/2025/oz/12/runpod/docker && \
grep -n "git-lfs\|LTX2" Dockerfile docker-compose.yml
```

**Expected**: Git LFS in Dockerfile, LTX2 build args, environment variables in docker-compose.yml

### Phase 2 Verification
```bash
cd /home/oz/projects/2025/oz/12/runpod/docker && \
grep -n "ComfyUI-LTXVideo\|ltx_video" Dockerfile
```

**Expected**: Git clone, verification script, module import test

### Phase 3 Verification
```bash
cd /home/oz/projects/2025/oz/12/runpod/docker && \
grep -A 50 "^download_ltx2()" download_models.sh | head -55
```

**Expected**: VRAM detection, HuggingFace token validation, FP8/FP16 download logic

### Phase 4 Verification
```bash
cd /home/oz/projects/2025/oz/12/runpod/docker/workflows && \
for f in ltx2-*.json; do
    python3 -m json.tool "$f" > /dev/null && echo "✓ $f"
done
```

**Expected**: Valid JSON syntax, all required nodes present

### Phase 5 Verification
```bash
grep -n "LTX-2\|ENABLE_LTX2\|LTX2" CLAUDE.md
```

**Expected**: 10+ matches across sections (VRAM table, env vars, section, R2, HF token, pod example)

### Final Integration Tests
```bash
# Build with LTX-2 enabled
docker build --build-arg BAKE_LTX2=true --build-arg LTX2_VARIANT=fp8 -t hearmeman-ltx2:test .

# Local Docker test
cd docker && docker compose up -d
# Open http://localhost:8188, load workflow, queue prompt

# LSP validation
lsp-validate --files docker/Dockerfile docker/docker-compose.yml docker/download_models.sh
```

---

## Blockers & Dependencies

| Phase | Blocker | Resolution |
|-------|---------|------------|
| P1 | None | Git LFS available in apt repos |
| P2 | P1 completion | Requires ComfyUI base installation |
| P3 | P1 completion | Requires base download script structure |
| P4 | P2, P3 completion | Requires custom node and models |
| P5 | P4 completion | Requires workflow files to document |

**External Dependencies**:
- ComfyUI-LTXVideo repository (public, no auth)
- Lightricks/LTX-2 model on HuggingFace (gated, requires HF_TOKEN)

---

## Files Modified/Created Summary

| File | Type | Lines | Purpose |
|------|------|-------|---------|
| `docker/Dockerfile` | Modified | +85 | Git LFS, build args, model download, custom node |
| `docker/docker-compose.yml` | Modified | +20 | Environment variables, GPU tier comments |
| `docker/download_models.sh` | Modified | +80 | LTX-2 download function with VRAM fallback |
| `docker/workflows/ltx2-text2video.json` | Created | +150 | Text-to-video workflow (9 nodes) |
| `docker/workflows/ltx2-image2video.json` | Created | +180 | Image-to-video workflow (11 nodes) |
| `docker/CLAUDE.md` | Modified | +50 | Documentation updates |
| **Total** | | **~565 lines** | |

---

## Model Specifications

| Aspect | Specification |
|--------|---------------|
| Parameters | 19B |
| Variants | FP8 (27GB), FP16 (54GB), Full (~100GB) |
| VRAM Requirements | 16GB minimum (FP8), 32GB+ (FP16) |
| Supported Frames | 300-500 (FP8), 800+ (FP16) |
| Input Types | Text prompts, Image prompts |
| Output Formats | webm, mp4 |
| Repository | https://github.com/Lightricks/ComfyUI-LTXVideo |
| Model Hub | https://huggingface.co/Lightricks/LTX-2 |

---

## Notes for Implementation

1. **VRAM Management**: Enable `ENABLE_LTX2_VRAM_MANAGEMENT=true` for GPUs with <32GB VRAM to use sequential CPU offload
2. **Token Requirement**: LTX-2 is a gated model on HuggingFace. Must configure `HF_TOKEN` via RunPod secret
3. **Datacenter Speed**: Use US datacenter for faster model downloads (EU takes 4+ min)
4. **Shared Dependencies**: LTX-2 shares text encoder (UMT5-XXL) and VAE with WAN 2.1 where available
5. **Output Directory**: Default output is `/workspace/ComfyUI/output/ltx2/` for R2 sync integration

---

*Generated from multi-phase plan: `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/ltx2-runpod-template-pre/`*
<think>
Now I need to analyze this PRD and categorize all changes to understand reversion risks. Let me systematically break down what's being changed:

## Files Modified:
1. `docker/Dockerfile` - Modified (lines 30-31, 97-100, 250-280, 325-395, 440-455)
2. `docker/docker-compose.yml` - Modified (lines 145-152, 165-175)
3. `docker/download_models.sh` - Modified (lines 690-735, 850-860)
4. `docker/workflows/ltx2-text2video.json` - Created (new)
5. `docker/workflows/ltx2-image2video.json` - Created (new)
6. `docker/CLAUDE.md` - Modified (lines 159-166, 169-189, 225-238, 48-167, 290-296, 300-346, 350-373)

Let me categorize each change:

### UNTOUCHED - Files NOT modified:
- None (all files are being touched)

### ENHANCED - Files getting additive changes:
1. `docker/docker-compose.yml` - Adding environment variables and GPU tier comments
2. `docker/download_models.sh` - Adding download_ltx2() function
3. `docker/workflows/ltx2-text2video.json` - New file (additive)
4. `docker/workflows/ltx2-image2video.json` - New file (additive)
5. `docker/CLAUDE.md` - Documentation additions

### REPLACED - Code intentionally replaced:
- None mentioned as replacements, only additions and new code

### REVERSION RISKS - Functionality that could be lost:
1. **Custom Node Installation Overlap** (P2) - The LTX2 custom node installation at lines 325-395 could conflict with or override existing custom node installations


2. **VRAM Management Configuration** introduces potential configuration conflicts
3. **Build Arguments** might interfere with existing build processes
4. **Model Download Mechanism** could create download conflicts
5. **New Workflow Files** might complicate workflow management

The implementation introduces several nuanced reversion risks that require careful navigation to prevent unintended system disruptions.
</think>

## Safety Check

### Risk Level: MEDIUM

### UNTOUCHED
| File | Why |
|------|-----|
| `docker/start.sh` | Not mentioned in PRD - existing startup script untouched |
| `docker/scripts/xtts-vo-gen.py` | Not mentioned - XTTS scripts remain unchanged |
| `.github/workflows/docker-build.yml` | Not mentioned - CI/CD pipeline unchanged |

### ENHANCED
| File | Additions |
|------|-----------|
| `docker/Dockerfile` | Git LFS installation (lines 30-31), LTX2 build args (97-100), custom node section (250-395), build-time model download (440-455) |
| `docker/docker-compose.yml` | LTX2 environment variables (145-175), GPU tier documentation comments |
| `docker/download_models.sh` | VRAM validation logic (690-700), `download_ltx2()` function (705-735), main download integration (850-860) |
| `docker/workflows/ltx2-text2video.json` | New text-to-video workflow (9 nodes, ~150 lines) |
| `docker/workflows/ltx2-image2video.json` | New image-to-video workflow (11 nodes, ~180 lines) |
| `docker/CLAUDE.md` | LTX-2 section (48-167), updated tables (GPU VRAM, env vars, storage, R2 estimates), pod creation example |

### REPLACED
| What | Why | New |
|------|-----|-----|
| None | All changes are additive or new file creation | N/A |

### REVERSION RISKS
| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Custom Node Installation Block** (Dockerfile:325-395) | HIGH | Inserts between existing stages. Reverting would leave orphaned ComfyUI-LTXVideo directory if not cleaned properly. Must verify custom node directory is removed on rollback. |
| **Build-Time Model Download** (Dockerfile:440-455) | MEDIUM | Conditional LTX2 download at build time. Revert may leave partial model downloads in image layers. Should clean up model artifacts during rollback. |
| **Environment Variable Additions** (docker-compose.yml:145-175) | LOW | Adds 30 lines of new variables. No existing variables modified. Easy to remove. |
| **VRAM Validation Logic** (download_models.sh:690-700) | MEDIUM | Auto-fallback logic based on detected GPU VRAM. If existing models use similar validation, could cause conflicts. Verify no overlap with WAN 2.1 VRAM checks. |
| **CLAUDE.md Documentation** | LOW | Pure documentation. Revert just removes documentation - no functional impact. |

### Recommendation: CAUTION

**Rationale**: This is a medium-risk implementation due to:
1. **Dockerfile modifications** are the highest risk - inserting custom node installation and model download sections between existing stages creates potential for orphaned artifacts on rollback
2. **Parallel execution of P2+P3** requires careful coordination to avoid conflicts
3. **VRAM auto-fallback logic** must be tested against existing WAN 2.1 implementation to ensure no conflicts

**Before proceeding, verify**:
- [ ] No existing custom node installations overlap with ComfyUI-LTXVideo directory
- [ ] VRAM validation logic doesn't conflict with WAN 2.1's detection
- [ ] Build-time model download is properly isolated from runtime download
- [ ] Rollback procedure documented for each phase
<think>
The user is asking me to summarize LSP validation status for PRD files. I read the file they mentioned, but it appears to be an LSP validation results file (lsp-raw.txt) that contains errors for two files:
1. docker-compose.yml - "No LSP support for files with extension '.yml'"
2. download_models.sh - "No LSP support for files with extension '.sh'"

These are not actually syntax errors but rather "UNSUPPORTED_LANGUAGE" errors, meaning the LSP tool doesn't support these file types (YAML and Shell script).

The user wants me to format this as a summary table. Since the file doesn't contain PRD files but rather Docker configuration files, I should clarify that in my response and provide the summary based on what's actually in the file.
</think>

## LSP Validation (Final)

| File | Status | Issues |
|------|--------|--------|
| `docker/docker-compose.yml` | Unsupported | No LSP support for `.yml` files |
| `docker/download_models.sh` | Unsupported | No LSP support for `.sh` files |

### Summary
- Total files checked: 2
- Files with errors: 0 (these are tool limitations, not code errors)
- Files with warnings: 0

### Blockers
None. These files are **not validation failures** - they indicate the LSP tool doesn't support YAML and Shell script files.

### Warnings
None.

---

**Note:** The validated files are Docker configuration files (docker-compose.yml, download_models.sh), not PRD files. If you need PRD validation, please specify the PRD file paths you'd like me to check.
<think>
The user is asking me to score the PRD on implementation readiness dimensions. I've read the entire PRD document (it's about LTX2 integration for RunPod). Now I need to evaluate it across the five dimensions and provide a score.

Let me analyze the document systematically:

1. **Completeness** - Does it cover all requirements?
- It has detailed specifications for Dockerfile changes
- Has environment variables listed
- Has download logic specifications
- Has workflow JSON examples
- Has safety checks and reversion risks
- Has implementation phases
- Missing: No explicit test cases mentioned, no rollback procedure explicitly documented step-by-step

2. **Clarity** - Are instructions unambiguous?
- Pretty clear with line number references
- Well-organized sections
- Clear technical specifications
- Could be clearer on some implementation details

3. **Actionability** - Can /implement execute this?
- Very actionable with clear file modifications
- Has code snippets
- Well-structured
- Some ambiguity in how to test

4. **Testability** - Clear verification steps?
- Has LSP validation but shows unsupported file types
- Has verification checkpoints but could be more explicit
- Missing clear testing procedures

5. **Safety** - Reversion risks addressed?
- Has good reversion risk section
- Has categorized changes (ENHANCED, REPLACED, UNTOUCHED)
- Has risk severity ratings
- Could have more explicit rollback procedures

Let me score each dimension:

Completeness: 8/10 - Covers most aspects but missing explicit test cases and more detailed rollback procedures
Clarity: 9/10 - Very well organized with line numbers and clear structure
Actionability: 9/10 - Very actionable with code examples and specifications
Testability: 6/10 - Has some verification but LSP shows unsupported files, could have more explicit testing


Safety: 8/10 - Good reversion risk analysis but could be more detailed on rollback procedures

I'll evaluate the overall implementation readiness and provide a concise summary of the PRD's strengths and potential improvements.
</think>

## Implementation Readiness Score

| Dimension | Score | Notes |
|-----------|-------|-------|
| Completeness | 8/10 | Comprehensive coverage of Dockerfile, env vars, workflows, and safety checks. Missing explicit test cases and detailed rollback procedures. |
| Clarity | 9/10 | Well-organized with line number references, clear section headers, and explicit file specifications. |
| Actionability | 9/10 | Highly actionable with code snippets, clear phase definitions, and specific implementation targets. |
| Testability | 6/10 | LSP validation shows unsupported file types for YAML/shell scripts. Verification checkpoints exist but lack explicit test procedures. |
| Safety | 8/10 | Strong reversion risk analysis with severity ratings. Good categorization of changes (ENHANCED/REPLACED/UNTOUCHED). Could use more detailed rollback commands. |
| **OVERALL** | **40/50** | **Strong PRD with excellent structure and specifications** |

### Ready for Implementation: **YES** (with minor refinements)

### Blockers
- None blocking - all sections are actionable

### Recommendations

**Testability Gaps**:
- Add explicit testing procedure section with commands to verify each phase
- Include syntax validation for workflow JSON files
- Add verification checkpoints for GPU VRAM detection logic
- Document expected outputs at each phase

**Safety Enhancements**:
- Add rollback command examples for each phase (e.g., `git checkout` commands for specific files)
- Document cleanup procedures for orphaned artifacts (ComfyUI-LTXVideo directory)
- Add explicit "before" state verification checklist

**Completeness Gaps**:
- Add integration test scenarios (e.g., text2video workflow end-to-end test)
- Document expected file paths after successful implementation
- Include performance benchmarking expectations (generation time, VRAM usage)

The PRD is well-structured and ready for implementation. The main gaps are around testing procedures and explicit rollback commands, which can be addressed during the `/implement` phase or added as preparatory work.
