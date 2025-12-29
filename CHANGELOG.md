# Project Changelog - Development Session Log

Use this file to track all development work across sessions.

---

## Session Format

Each session logs:
- Start timestamp (CDMX timezone)
- Tasks completed with status
- End timestamp
- Total duration

---

## 2024-12-29 Session 1: RunPod Deployment Testing

**Start**: 2024-12-29 10:00 CST (CDMX)

**Tasks**:
- [x] Stage 1: EU vs US datacenter speed testing
  - EU-CZ: 4+ min startup (slow, avoid)
  - US: ~1 sec startup (fast, recommended)
- [x] Stage 2: Illustrious image generation test
  - Multiple pod attempts (availability issues in specific US datacenters)
  - Secure Cloud solution: dedicated 25Gbps bandwidth
  - Model download: 51.2 MB/s (6.5GB in ~2 min)
  - Image generation: Success (1024x1024 portrait)
- [x] R2 sync verification
  - Auto-uploaded to `outputs/2024-12-29/runpod-test_00001_.png`
  - 1.30 MB image synced successfully
- [x] Documentation updates
  - Added RunPod Deployment Requirements to CLAUDE.md
  - Updated runpod skill with new learnings
  - Documented port requirements (`--ports "8188/http"`)

**Key Learnings**:
1. Must use `--ports "8188/http"` for web access
2. Secure Cloud preferred for consistent network speeds
3. CivitAI curl fallback works for 307 redirects
4. Model filenames: `model_<id>.safetensors`

**Test Results**:
| Test | Status | Notes |
|------|--------|-------|
| EU datacenter | ✅ Tested | 4+ min startup - avoid |
| US Secure Cloud | ✅ Working | 37 sec startup, 51 MB/s |
| Illustrious model | ✅ Working | 6.5GB download OK |
| Image generation | ✅ Success | 1024x1024 portrait |
| R2 sync | ✅ Working | Auto-upload to bucket |

**Cost**: ~$0.08 (8 min at $0.59/hr)

**Status**: Completed

**End**: 2024-12-29 11:45 CST (CDMX)
**Duration**: 1 hour 45 minutes

**Next Steps**:
- [x] Stage 3: WAN 2.2 video test (~25GB model)
- [ ] Stage 4: VibeVoice TTS test
- [ ] Stage 5: Multi-model workflow test

---

## 2025-12-29 Session 2: WAN Video & VibeVoice Testing

**Start**: 2025-12-29 12:30 CST (CDMX)
**Author**: oz + Claude Opus 4.5

**Tasks**:
- [x] Stage 3: WAN 2.1 14B video generation test
  - CUDA driver issue on RTX 4090 (needed L40S for CUDA 12.8)
  - Manual model downloads required (diffusion, text encoder, VAE)
  - Created working `wan21-t2v-14b-api.json` workflow
  - Generated 17-frame puppy video successfully (219KB WebM)
- [x] Fix download_models.sh logging (bead runpod-n88)
  - Added logging to `/var/log/download_models.log`
  - Created `hf_snapshot_download()` helper with error handling
  - Added download summary at end of script
- [!] Stage 4: VibeVoice TTS test (blocked)
  - Downloaded VibeVoice-Large (~18GB) from aoi-ot/VibeVoice-Large
  - Disk space issue from partial Q8 download (resolved)
  - Missing Qwen tokenizer dependency (bead runpod-6s9)
- [ ] Stage 5: Multi-model workflow test (pending)

**Beads Created**:
- `runpod-n88`: Fix automatic model downloads (closed)
- `runpod-6s9`: VibeVoice needs Qwen tokenizer (open)

**Key Learnings**:
1. RTX 4090 may have older CUDA drivers - L40S safer for CUDA 12.8
2. VibeVoice model repo changed: use `aoi-ot/VibeVoice-Large`
3. WAN workflow needs: CLIPLoader (type=wan), WanVideoTextEmbedBridge, WanVideoVAELoader, WanVideoDecode
4. Use 150GB ephemeral storage for future pods

**Test Results**:
| Test | Status | Notes |
|------|--------|-------|
| WAN 2.1 14B T2V | ✅ Working | 17 frames, 480x320, 15 steps |
| download_models.sh fix | ✅ Fixed | Better logging, error handling |
| VibeVoice-Large | ❌ Blocked | Needs Qwen tokenizer download |

**Cost**: ~$0.86/hr (L40S) - ~45 min testing

**Status**: Partial - WAN working, VibeVoice blocked

**End**: 2025-12-29 13:30 CST (CDMX)
**Duration**: ~1 hour

**Next Steps**:
- [x] Fix VibeVoice Qwen tokenizer (bead runpod-6s9)
- [x] Stage 4: VibeVoice TTS test
- [x] Stage 5: Multi-model workflow test

---

## 2025-12-29 Session 4: Full Auto Mode - Extended Testing

**Start**: 2025-12-29 15:57 CST (CDMX)
**Author**: oz + Claude Opus 4.5

**Tasks**:
- [x] Stage 5: Multi-model workflow test (WAN + VibeVoice verified)
- [x] Extended WAN 2.1 testing
  - 17-frame puppy (480x320, 46.9s) ✅
  - 33-frame eagle (640x384, ~90s) ✅
  - 720p cyberpunk (17 frames, VAE tiling) ✅
  - 25-frame whale (640x384) ✅
- [x] VibeVoice variations
  - English longer text (30 steps, sampling=true) ✅
  - Spanish test ✅
- [x] R2 sync debugging
  - Auto-sync daemon NOT working (secrets not expanding)
  - Manual sync workaround via boto3 ✅
- [x] Added WAN 2.2 distilled models to download_models.sh
  - `ENABLE_WAN22_DISTILL=true` for TurboDiffusion I2V
  - High noise + Low noise expert models (~28GB total)

**Test Results**:
| Test | Status | Details |
|------|--------|---------|
| WAN 2.1 puppy 17f | ✅ | 46.9s, 13.75GB VRAM |
| WAN 2.1 eagle 33f | ✅ | 640x384, ~90s |
| WAN 2.1 cyberpunk 720p | ✅ | VAE tiling enabled |
| WAN 2.1 whale 25f | ✅ | 84.12s |
| VibeVoice English | ✅ | 20.62s |
| VibeVoice Spanish | ✅ | Working |
| TurboDiffusion I2V | ❌ | Needs WAN 2.2 distilled models |

**R2 Outputs Synced**:
- `outputs/2025-12-29/wan21_eagle_33f_00001.webm` (216 KB)
- `outputs/2025-12-29/wan21_cyberpunk_720p_00001.webm` (326 KB)
- `outputs/2025-12-29/wan21_whale_25f_00001.webm` (342 KB)
- `outputs/2025-12-29/vibevoice_longer_00001_.flac` (258 KB)
- `outputs/2025-12-29/vibevoice_spanish_00001_.flac` (274 KB)

**Key Findings**:
1. RunPod Secrets syntax `{{RUNPOD_SECRET_*}}` may not expand in pod creation args
2. TurboDiffusion I2V requires WAN 2.2 distilled models (high/low noise experts)
3. VAE tiling works for higher resolutions
4. Model auto-download via download_models.sh confirmed working

**Pod Info**: `rzb4vbqzuflklo` | L40S GPU | $0.86/hr

**Status**: Completed

**End**: 2025-12-29 16:25 CST (CDMX)
**Duration**: ~30 minutes

---

## 2025-12-29 Session 3: VibeVoice Fixed & Security Hardening

**Start**: 2025-12-29 13:32 CST (CDMX)
**Author**: oz + Claude Opus 4.5

**Tasks**:
- [x] Stage 4: VibeVoice TTS test - SUCCESS
  - Downloaded Qwen tokenizer manually
  - Generated test audio (128KB FLAC)
  - Synced outputs to R2: `runpod/outputs/2024-12-29/`
- [x] Fix download_models.sh for auto-download
  - Corrected VibeVoice repo: `AIFSH/VibeVoice-Large` → `aoi-ot/VibeVoice-Large`
  - Added automatic Qwen tokenizer download
  - Closed bead runpod-6s9
- [x] Security hardening
  - Removed `.env` from git tracking (had exposed CivitAI key)
  - Created `.gitignore` and `.env.example`
  - Rotated CivitAI API key
  - Added RunPod Secrets documentation
- [x] RunPod Secrets setup
  - Created secrets via GraphQL API: `r2_access_key`, `r2_secret_key`, `civitai_key`
  - Updated CLAUDE.md with `{{RUNPOD_SECRET_*}}` syntax
- [x] Docker image pushed to GHCR (11.3GB)

**Session Outputs** (R2 presigned URLs):
- `vibevoice_test_00001_.flac` - TTS audio test
- `wan21_puppy_00001.webm` - Video generation test
- `wan21_puppy_00001.png` - Video thumbnail

**Key Learnings**:
1. GHCR has 10GB/layer limit (our layers are <7GB, OK)
2. RunPod secrets use `{{RUNPOD_SECRET_name}}` syntax
3. Always gitignore `.env` files with real credentials

**Status**: Completed - Ready for Stage 5

**End**: 2025-12-29 14:45 CST (CDMX)
**Duration**: ~1 hour 15 minutes

**Next Steps**:
- [ ] Stage 5: Multi-model workflow test (WAN + VibeVoice together)
- [ ] Test auto-download with fresh pod (150GB ephemeral)
- [ ] Test R2 auto-sync daemon

---

## YYYY-MM-DD Session 1

**Start**: YYYY-MM-DD HH:MM:SS CST (CDMX)

**Tasks**:
- [ ] Task 1 - Brief description
- [ ] Task 2 - Brief description
  - Sub-task 2a (if applicable)
  - Sub-task 2b (if applicable)
- [ ] Task 3 - Brief description

**Status**: In Progress / Completed

**Time Checkpoint**:
- 4.0 hours: First reminder to wrap up
- 4.25 hours: Final 15-minute warning
- 4.5 hours: Hard stop - close session

**End**: YYYY-MM-DD HH:MM:SS CST (CDMX)
**Duration**: X hours Y minutes

---

## Session Guidelines

### Time Tracking Protocol
1. Log session start time in CDMX timezone when beginning work
2. Set reminder for 4 hours into session
3. Set reminder for 4.25 hours (15 minutes warning)
4. Close session at 4.5 hours maximum
5. Log end time and calculate duration

### Task Logging
- Use checkboxes `[ ]` for pending tasks
- Mark complete with `[x]` as work progresses
- Use `[!]` for errored tasks with next steps
- Use `[>]` for currently in-progress tasks
- Add sub-bullets for implementation details
- Reference file paths for traceability

### Summary Statistics (Optional)
Track across all sessions:
- Total hours worked
- Features completed
- Bugs fixed
- Performance improvements

---

## Quick Copy Template

```markdown
## YYYY-MM-DD Session N

**Start**: YYYY-MM-DD HH:MM:SS CST (CDMX)

**Tasks**:
- [x] Task 1 - Description
- [ ] Task 2 - Description
- [!] Task 3 - Description
  - Error: [specific issue]
  - Next step: [how to fix]

**Status**: In Progress / Completed

**End**: YYYY-MM-DD HH:MM:SS CST (CDMX)
**Duration**: X hours Y minutes

---
```

---

## 2025-12-28 Session 1

**Start**: 2025-12-28 03:56:00 CST (CDMX)
**Author**: oz + Claude Opus 4.5

**Tasks**:
- [x] Complete voice cloning tests across 5 TTS models
  - Chatterbox Original (EN): 15 files with CFG & exaggeration
  - Chatterbox Multilingual: 27 files (EN + ES)
  - Chatterbox Turbo: 15 files
  - XTTS v2: 15 files (fixed speaker loading)
  - VibeVoice Q8: 12 files (3 timeouts)
- [x] Fix XTTS v2 empty files - needed speaker folder refresh
- [x] Test VibeVoice Large-Q8 (11GB) as alternative to Large (18GB)
- [x] Commit TTS comparison results (124 files, 84 voice samples)
- [x] Remove XTTS v2 from docker-compose.yml (not needed for project)
- [>] Research new AI models for RunPod template
  - Generative Refocusing (GenFocus)
  - Qwen-Image-Edit-2511
  - InfCam (camera-controlled video)
  - MVInverse (multi-view consistency)
- [x] Research Qwen3-TTS vs Chatterbox comparison
- [x] Create comprehensive PRD for 6 AI models (hearmeman-all-models.md)
  - Phase 1: Environment variables + Dockerfile
  - Phase 2: Tier 1 (Consumer GPU) downloads
  - Phase 3: Tier 2 (Prosumer GPU) downloads
  - Phase 4: Tier 3 (Datacenter GPU) downloads
  - Phase 5: ComfyUI custom node wrappers
  - Phase 6: CPU offloading configuration
- [x] Document CPU offloading options for smaller VRAM GPUs
- [x] Include FlashPortrait and StoryMem in research

**Decisions**:
- XTTS v2 removed from template - limited use case compared to Chatterbox
- Winner for English voice cloning: Chatterbox Original (CFG + exaggeration)
- VibeVoice Q8 viable for 16GB GPU but slower than Chatterbox
- InfCam included for datacenter testing despite 50GB+ VRAM requirement
- Models organized into 3 GPU tiers: Consumer (8-24GB), Prosumer (24GB+), Datacenter (48-80GB)

**Status**: Completed

**End**: 2025-12-28 14:24:42 CST (CDMX)
**Duration**: ~10 hours 28 minutes

---
