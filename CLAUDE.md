# RunPod Custom Templates

Custom RunPod templates for AI model deployment with on-demand model downloads.

## Storage Requirements (Local Docker Lab)

| Component | Size | Notes |
|-----------|------|-------|
| **Docker Image** | ~12GB | Base with custom nodes |
| **WAN 2.2 720p** | ~25GB | Default video gen |
| **WAN 2.2 480p** | ~12GB | Optional |
| **VibeVoice-Large** | ~18GB | TTS voice cloning |
| **XTTS v2** | ~1.8GB | Multilingual TTS |
| **Z-Image Turbo** | ~21GB | Fast image gen |
| **SteadyDancer** | ~33GB | Dance video |
| **SCAIL** | ~28GB | Facial mocap |
| **ControlNet (5)** | ~3.6GB | Preprocessors |
| **VACE 14B** | ~28GB | Video editing |
| **Fun InP 14B** | ~28GB | Frame interpolation |
| **Realism Illustrious** | ~6.5GB | Photorealistic images |
| **Total (ALL)** | **~230GB** | |
| **Typical Config** | **~80-120GB** | |

**Minimum Local Setup**: 250GB SSD, 32GB RAM, 24GB VRAM

## PRD Documents

| Document | Description |
|----------|-------------|
| `hearmeman-extended-template.md` | Main Dockerfile + scripts |
| `illustrious-template-integration.md` | Realism Illustrious |

## Key Environment Variables

| Variable | Default | Size |
|----------|---------|------|
| `ENABLE_VIBEVOICE` | true | 18GB |
| `ENABLE_ZIMAGE` | false | 21GB |
| `ENABLE_ILLUSTRIOUS` | false | 6.5GB |
| `ENABLE_VACE` | false | 28GB |
| `ENABLE_CIVITAI` | false | varies |
| `WAN_720P` | true | 25GB |

---

# Project Context - Task Logging & Agent Delegation

## Task Logging System

Use this system to track work across sessions in CHANGELOG.md:

### Task States
- `[ ]` - Pending (not started)
- `[x]` - Completed (finished successfully)
- `[!]` - Errored (encountered blocker)
- `[>]` - In Progress (currently working on)

### Task Log Format

```markdown
## YYYY-MM-DD Session N

**Start**: YYYY-MM-DD HH:MM:SS CST (CDMX)

**Tasks**:
- [x] Task 1 - Brief description
- [ ] Task 2 - Brief description
  - Sub-task 2a (if applicable)
  - Sub-task 2b (if applicable)
- [!] Task 3 - Brief description
  - Error: Specific blocker or issue
  - Next step: What to do to unblock
- [>] Task 4 - Brief description
  - Currently on: Specific subtask being worked

**Status**: In Progress / Completed

**End**: YYYY-MM-DD HH:MM:SS CST (CDMX)
**Duration**: X hours Y minutes

---
```

### Task Logging Rules

1. **Mark status IMMEDIATELY** as you start/complete each task
2. **One task in Progress at a time** - focus principle
3. **Reference file paths** - add full paths for traceability
4. **Note errors clearly** - document blockers with next steps
5. **Calculate duration** - end timestamp - start timestamp

### Session Time Limits

- **4.0 hours**: First reminder to wrap up
- **4.25 hours**: Final 15-minute warning
- **4.5 hours**: Hard stop - close session, log results

---

## Orchestrator Mode & Agent Delegation

**Role**: You are an orchestrator. Delegate tasks to agents whenever possible.

### Profile Selection

**ALWAYS check `~/.codex/config.toml` for current profiles before delegating.**

```bash
cat ~/.codex/config.toml | grep -A 5 "profiles"
```

### Available Codex Profiles

**Most Powerful (Codex-Max)**:
- `codex-max-xhigh` - Critical architecture/complex algorithms
- `codex-max-high` - Complex code generation
- `codex-max-medium` - Standard tasks
- `codex-max-low` - Simple/fast tasks

**Standard Codex**:
- `gpt5-codex-high`, `gpt5-codex-medium`, `gpt5-codex-low`
- `gpt5-codex-mini-high` - Lightweight tasks

**Multimodal (Non-Code)**:
- `gpt5-high`, `gpt5-medium`, `gpt5-low`, `gpt5-full`

### Delegation Workflow

```bash
# Single task delegation
# IMPORTANT: Always instruct agent to write output to a file to avoid token bloat
codex exec --skip-git-repo-check --full-auto -p codex-max-high \
  "Task description here. Write your output to artifacts/task-result.md"

# Parallel delegation (independent tasks)
codex exec --skip-git-repo-check --full-auto -p codex-max-high \
  "Task 1. Write output to artifacts/task1-result.md" &
codex exec --skip-git-repo-check --full-auto -p codex-max-medium \
  "Task 2. Write output to artifacts/task2-result.md" &
wait

# Then read results from files (keeps orchestrator context clean)
```

**Why write to files?** Stdout bloats the orchestrator's token window. File output keeps context lean.

### Delegation Checklist

1. ✓ Check `~/.codex/config.toml` for available profiles
2. ✓ Identify independent tasks that can run in parallel
3. ✓ Select appropriate profile (prefer `codex-max-*` for complex work)
4. ✓ Execute with `--skip-git-repo-check --full-auto`
5. ✓ Verify results - ALWAYS run a self-test
6. ✓ Iterate if issues found

### When to Use Each Agent Type

| Task | Profile | When |
|------|---------|------|
| Architecture/Complex logic | `codex-max-xhigh` | Critical decisions, complex algorithms |
| Code generation | `codex-max-high` | Implementing features, refactoring |
| Straightforward coding | `codex-max-medium` | Standard development tasks |
| Simple tasks | `codex-max-low` | Formatting, simple edits, linting |
| Non-code work | `gpt5-*` | Screenshots, multimodal, reasoning |

---

## Documentation Sync

**IMPORTANT**: Keep task logging consistent across all project documents.

- **CLAUDE.md** or **PROJECT_TEMPLATE_CLAUDE.md**: Quick reference (this file)
- **AGENTS.md** or **PROJECT_TEMPLATE_AGENTS.md**: Full workflows
- **CHANGELOG.md**: Active session logs
