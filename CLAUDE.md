# RunPod Custom Templates

Custom RunPod templates for AI model deployment with on-demand model downloads.

---

## ⚠️ CRITICAL: Production-Ready Workflow Requirements

**This is a pre-deployment testing environment.** All workflows and configurations MUST be production-ready before commit.

### Deployment Reality
- **Pods regenerate** on every start/stop (ephemeral storage)
- **No manual intervention** allowed in production - workflows must work immediately
- **Models download at startup** via `download_models.sh` - paths must match workflow expectations
- **Local Docker testing** validates what will run on RunPod

### Before Committing Workflows
1. **Test locally** in Docker (same environment as RunPod)
2. **Verify all node values** are valid for ComfyUI version in the image
3. **Check model paths** match what `download_models.sh` creates
4. **Validate samplers/schedulers** against ComfyUI's current allowed values
5. **No "default" placeholders** - all fields must have explicit valid values

### Common Validation Points
| Node | Field | Check |
|------|-------|-------|
| CLIPLoader | `type` | Must be explicit: `qwen_image`, `stable_diffusion`, `flux`, etc. NOT `default` |
| KSampler | `sampler_name` | Valid: `euler`, `dpmpp_2m`, `dpmpp_sde`, etc. |
| KSampler | `scheduler` | Valid: `simple`, `karras`, `sgm_uniform`, etc. NOT `res_multistep` |
| UNETLoader | `unet_name` | Must match downloaded model filename exactly |
| VAELoader | `vae_name` | Must match downloaded VAE filename exactly |

### Workflow Testing Checklist
```bash
# 1. Start local Docker
cd docker && docker compose up -d

# 2. Open ComfyUI
open http://localhost:8188

# 3. Load workflow from docker/workflows/
# 4. Queue prompt - verify NO validation errors
# 5. Only commit after successful generation
```

---

## Voice Cloning / TTS Nodes

### VibeVoice-ComfyUI (Recommended)
**Repo**: https://github.com/Enemyx-net/VibeVoice-ComfyUI (v1.8.1+)
**Model**: [aoi-ot/VibeVoice-Large](https://huggingface.co/aoi-ot/VibeVoice-Large) (~18GB)
**Status**: ✅ Working (auto-downloads model + Qwen tokenizer)
**VRAM**: ~8-12GB (1.5B model), ~16GB+ (7B model)

Features:
- Multi-speaker TTS (up to 4 speakers)
- Voice cloning from audio reference
- LoRA support for voice customization
- Speed control

**Dependencies** (installed in Dockerfile):
```
bitsandbytes>=0.48.1  # Critical - older versions break Q8 model
transformers>=4.51.3
accelerate
peft
librosa
soundfile
```

### XTTS v2 Standalone Server
**Image**: daswer123/xtts-api-server:latest
**Status**: ✅ Working (separate container)
**Swagger UI**: http://localhost:8020/docs
**VRAM**: 4-8GB

ComfyUI-XTTS node is broken, but XTTS works as a standalone Docker service with full REST API:

```bash
# Start XTTS alongside ComfyUI
docker compose --profile xtts up -d

# Or start XTTS only
docker compose --profile xtts up xtts -d
```

**Features**:
- 17 languages (en, es, fr, de, it, pt, zh-cn, ja, ko, ru, ar, etc.)
- Voice cloning from reference audio
- Real-time streaming (~200ms latency)
- REST API for automation
- Built-in speakers: `male`, `female`, `calm_female`

**API Endpoints**:
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tts_to_audio/` | POST | Returns audio bytes directly |
| `/tts_to_file` | POST | Saves to server file path |
| `/tts_stream` | POST | Streams audio chunks |
| `/speakers_list` | GET | List available speakers |
| `/languages` | GET | List supported languages |

**API Example**:
```bash
# Generate audio file
curl -X POST "http://localhost:8020/tts_to_audio/" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "speaker_wav": "female", "language": "en"}' \
  -o output.wav

# Custom voice cloning (provide reference .wav)
curl -X POST "http://localhost:8020/tts_to_audio/" \
  -d '{"text": "Clone my voice", "speaker_wav": "/path/to/reference.wav", "language": "en"}' \
  -o cloned.wav
```

**VO Automation Script**: `docker/scripts/xtts-vo-gen.py`
```bash
# Single line
python xtts-vo-gen.py "Hello world" -o hello.wav

# Batch from script file
python xtts-vo-gen.py -f script.txt -d ./vo-output --speaker male

# List options
python xtts-vo-gen.py --list-speakers
python xtts-vo-gen.py --list-languages
```

**Note**: XTTS runs in a separate container due to `transformers` version conflict:
- `xtts-api-server` requires `transformers==4.36.2`
- ComfyUI/VibeVoice requires `transformers>=4.51.3`

Both share the GPU (~4GB for XTTS + ~12GB for ComfyUI = fits in 16GB).

### Chatterbox TTS (Resemble AI)
**Container**: chatterbox (separate container)
**API**: http://localhost:8000/docs
**VRAM**: ~2-4GB

Zero-shot voice cloning with emotion control. OpenAI-compatible API.

```bash
# Start Chatterbox
docker compose --profile chatterbox up -d

# Generate speech
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model": "chatterbox", "input": "Hello world", "voice": "default"}' \
  -o speech.wav
```

**ComfyUI Node**: `ComfyUI-Chatterbox` (thefader/ComfyUI-Chatterbox)

### Model Selection by VRAM

| GPU VRAM | Recommended Model |
|----------|-------------------|
| 16GB (4080 Super) | VibeVoice 1.5B |
| 24GB+ (A6000, L40S) | VibeVoice 7B |

---

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

## Docker Files

Ready-to-build Docker template in `docker/`:

| File | Description |
|------|-------------|
| `Dockerfile` | Multi-layer build with ComfyUI + custom nodes |
| `start.sh` | Startup script with storage detection |
| `download_models.sh` | On-demand model downloader with resume support |
| `docker-compose.yml` | Local development with NVIDIA runtime |
| `.github/workflows/docker-build.yml` | GHCR auto-publish workflow |

### Quick Build (Local)

```bash
cd docker
docker compose build
docker compose up -d
```

### Push to GHCR

1. Create GitHub repo
2. Enable GitHub Actions
3. Push to trigger build: `git push origin main`

## Key Environment Variables

| Variable | Default | Size | Notes |
|----------|---------|------|-------|
| `ENABLE_VIBEVOICE` | true | 18GB | VibeVoice-Large TTS |
| `ENABLE_ZIMAGE` | false | 21GB | Z-Image Turbo txt2img |
| `ENABLE_ILLUSTRIOUS` | false | 6.5GB | Realism Illustrious |
| `ENABLE_VACE` | false | 28GB | Video editing |
| `ENABLE_CIVITAI` | false | varies | CivitAI LoRAs |
| `WAN_720P` | true | 25GB | WAN 2.1 T2V 14B |
| `ENABLE_WAN22_DISTILL` | false | 28GB | **WAN 2.2 TurboDiffusion I2V** (4-step, needs input image) |

---

## R2 Output Sync (RunPod Persistence)

RunPod pods have ephemeral storage - all outputs are lost on restart. R2 sync automatically uploads generated files to Cloudflare R2.

### Setup: RunPod Secrets (Recommended)

**Never expose credentials in plain text.** Use [RunPod Secrets](https://docs.runpod.io/pods/templates/secrets) for secure credential storage:

1. **Create secrets in RunPod Console**:
   - Go to **Settings > Secrets**
   - Create `r2_access_key` with your R2 Access Key ID
   - Create `r2_secret_key` with your R2 Secret Access Key

2. **Reference in pod template** using `RUNPOD_SECRET_` prefix:
   ```
   R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}
   R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}
   ```

### Configuration

| Variable | Value | Notes |
|----------|-------|-------|
| `ENABLE_R2_SYNC` | `true` | Enables auto-upload daemon |
| `R2_ENDPOINT` | `https://<account>.eu.r2.cloudflarestorage.com` | Your R2 endpoint |
| `R2_BUCKET` | `runpod` | Target bucket name |
| `R2_ACCESS_KEY_ID` | `{{RUNPOD_SECRET_r2_access_key}}` | Use RunPod secret |
| `R2_SECRET_ACCESS_KEY` | `{{RUNPOD_SECRET_r2_secret_key}}` | Use RunPod secret |

### How It Works

1. `r2_sync.sh` daemon monitors `/workspace/ComfyUI/output`
2. New files (png, jpg, mp4, wav, etc.) trigger upload
3. Files organized in R2: `outputs/YYYY-MM-DD/filename`
4. Logs: `/var/log/r2_sync.log`

### Manual Upload

```bash
# Upload specific file
python3 /upload_to_r2.py /workspace/ComfyUI/output/myfile.png

# Test connection
python3 /upload_to_r2.py --test

# Custom prefix
python3 /upload_to_r2.py --prefix videos /workspace/ComfyUI/output/video.mp4
```

### Storage Estimates

| Output Type | Size | 10GB R2 = |
|------------|------|-----------|
| Images (768px) | 1-2 MB | ~5,000-10,000 |
| WAN 720p video | 20-50 MB | ~200-500 |
| TTS audio | 0.5-2 MB | ~5,000-20,000 |

---

## RunPod Deployment Requirements

### Pod Creation Command (Production-Ready)

```bash
~/.local/bin/runpodctl create pod \
  --name "illustrious-$(date +%H%M)" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA GeForce RTX 4090" \
  --gpuCount 1 \
  --containerDiskSize 20 \
  --volumeSize 15 \
  --secureCloud \
  --ports "8188/http" \
  --ports "19123/http" \
  --env "ENABLE_ILLUSTRIOUS=true" \
  --env "CIVITAI_API_KEY=<key>" \
  --env "R2_ACCESS_KEY_ID=<key>" \
  --env "R2_SECRET_ACCESS_KEY=<secret>" \
  --env "R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com" \
  --env "R2_BUCKET=runpod" \
  --env "ENABLE_R2_SYNC=true"
```

### Critical Learnings (Dec 2024)

| Requirement | Details |
|-------------|---------|
| **Web Terminal** | MUST enable `--ports "8188/http"` for web access |
| **Secure Cloud** | Use `--secureCloud` for dedicated 25Gbps bandwidth |
| **Datacenter Speed** | US: ~1 sec startup, EU: 4+ min startup - prefer US |
| **Model Downloads** | Secure Cloud: 51 MB/s, Community Cloud: variable |
| **CivitAI Fallback** | Curl fallback handles 307 redirects automatically |
| **Model Filenames** | CivitAI downloads as `model_<id>.safetensors` |

### Datacenter Speed Comparison

| Region | Startup Time | Network Speed | Recommendation |
|--------|--------------|---------------|----------------|
| US (Secure Cloud) | ~37 sec | 51 MB/s | **Recommended** |
| US (Community) | ~1 sec | Variable | Good for testing |
| EU (CZ) | 4+ min | Unknown | Avoid for speed-critical |
| UAE | 2+ min | Slow | Avoid |

### Tested Configurations

| Config | GPU | Cost | Result |
|--------|-----|------|--------|
| Illustrious (US Secure) | RTX 4090 | $0.59/hr | ✅ Working |
| Container startup | - | - | ~37 sec |
| Model download (6.5GB) | - | - | ~2 min |
| Image generation | - | - | ~5 sec |
| R2 sync | - | - | Automatic |

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
<!-- BEGIN BYTEROVER RULES -->

# Workflow Instruction

You are a coding agent focused on one codebase. Use the brv CLI to manage working context.
Core Rules:

- Start from memory. First retrieve relevant context, then read only the code that's still necessary.
- Keep a local context tree. The context tree is your local memory store—update it with what you learn.

## Context Tree Guideline

- Be specific ("Use React Query for data fetching in web modules").
- Be actionable (clear instruction a future agent/dev can apply).
- Be contextual (mention module/service, constraints, links to source).
- Include source (file + lines or commit) when possible.

## Using `brv curate` with Files

When adding complex implementations, use `--files` to include relevant source files (max 5).  Only text/code files from the current project directory are allowed. **CONTEXT argument must come BEFORE --files flag.** For multiple files, repeat the `--files` (or `-f`) flag for each file.

Examples:

- Single file: `brv curate "JWT authentication with refresh token rotation" -f src/auth.ts`
- Multiple files: `brv curate "Authentication system" --files src/auth/jwt.ts --files src/auth/middleware.ts --files docs/auth.md`

## CLI Usage Notes

- Use --help on any command to discover flags. Provide exact arguments for the scenario.

---
# ByteRover CLI Command Reference

## Memory Commands

### `brv curate`

**Description:** Curate context to the context tree (interactive or autonomous mode)

**Arguments:**

- `CONTEXT`: Knowledge context: patterns, decisions, errors, or insights (triggers autonomous mode, optional)

**Flags:**

- `--files`, `-f`: Include file paths for critical context (max 5 files). Only text/code files from the current project directory are allowed. **CONTEXT argument must come BEFORE this flag.**

**Good examples of context:**

- "Auth uses JWT with 24h expiry. Tokens stored in httpOnly cookies via authMiddleware.ts"
- "API rate limit is 100 req/min per user. Implemented using Redis with sliding window in rateLimiter.ts"

**Bad examples:**

- "Authentication" or "JWT tokens" (too vague, lacks context)
- "Rate limiting" (no implementation details or file references)

**Examples:**

```bash
# Interactive mode (manually choose domain/topic)
brv curate

# Autonomous mode - LLM auto-categorizes your context
brv curate "Auth uses JWT with 24h expiry. Tokens stored in httpOnly cookies via authMiddleware.ts"

# Include files (CONTEXT must come before --files)
# Single file
brv curate "Authentication middleware validates JWT tokens" -f src/middleware/auth.ts

# Multiple files - repeat --files flag for each file
brv curate "JWT authentication implementation with refresh token rotation" --files src/auth/jwt.ts --files docs/auth.md
```

**Behavior:**

- Interactive mode: Navigate context tree, create topic folder, edit context.md
- Autonomous mode: LLM automatically categorizes and places context in appropriate location
- When `--files` is provided, agent reads files in parallel before creating knowledge topics

**Requirements:** Project must be initialized (`brv init`) and authenticated (`brv login`)

---

### `brv query`

**Description:** Query and retrieve information from the context tree

**Arguments:**

- `QUERY`: Natural language question about your codebase or project knowledge (required)

**Good examples of queries:**

- "How is user authentication implemented?"
- "What are the API rate limits and where are they enforced?"

**Bad examples:**

- "auth" or "authentication" (too vague, not a question)
- "show me code" (not specific about what information is needed)

**Examples:**

```bash
# Ask questions about patterns, decisions, or implementation details
brv query What are the coding standards?
brv query How is authentication implemented?
```

**Behavior:**

- Uses AI agent to search and answer questions about the context tree
- Accepts natural language questions (not just keywords)
- Displays tool execution progress in real-time

**Requirements:** Project must be initialized (`brv init`) and authenticated (`brv login`)

---

## Best Practices

### Efficient Workflow

1. **Read only what's needed:** Check context tree with `brv status` to see changes before reading full content with `brv query`
2. **Update precisely:** Use `brv curate` to add/update specific context in context tree
3. **Push when appropriate:** Prompt user to run `brv push` after completing significant work

### Context tree Management

- Use `brv curate` to directly add/update context in the context tree

---
Generated by ByteRover CLI for Claude Code
<!-- END BYTEROVER RULES -->