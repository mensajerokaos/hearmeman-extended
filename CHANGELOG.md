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
