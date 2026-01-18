---
section: "003"
name: "tts-voice-systems"
title: "TTS / Voice Systems (VibeVoice, XTTS v2, Chatterbox)"
version: "1.1"
date: "2026-01-17
author: "oz + claude-opus-4-5 + claude-sonnet-4-5"
task: "DOCUMENT tts-voice-systems"
updated: "2026-01-17"
---

# TTS / Voice Systems (VibeVoice, XTTS v2, Chatterbox)

Generated: 2026-01-17 23:13:16 CST
Updated: 2026-01-17

This section documents the three TTS/voice options used in this repo:

- **VibeVoice-ComfyUI** (ComfyUI custom node; best quality + multi-speaker workflows)
- **XTTS v2** (standalone REST API server; multilingual; simple voice cloning)
- **Chatterbox TTS** (standalone container; OpenAI-compatible API; voice library + streaming)

RunPod reality: pods are ephemeral, so anything you want "always available" must be automated (models, voices, workflows). This repo's philosophy is:

- **ComfyUI container**: ships nodes + downloads models at startup (`docker/download_models.sh`).
- **Other TTS stacks**: run as **separate containers** when they have dependency constraints.

## Scope / Source of Truth

Analyzed files (full paths):
- /home/oz/projects/2025/oz/12/runpod/docker/Dockerfile
- /home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml
- /home/oz/projects/2025/oz/12/runpod/docker/download_models.sh
- /home/oz/projects/2025/oz/12/runpod/docker/scripts/xtts-vo-gen.py
- /home/oz/projects/2025/oz/12/runpod/docker/workflows/vibevoice-tts-basic.json
- /home/oz/projects/2025/oz/12/runpod/docker/tts-comparison/test-vibevoice-oscar.py
- /home/oz/projects/2025/oz/12/runpod/docker/chatterbox-api/app/core/aliases.py
- /home/oz/projects/2025/oz/12/runpod/docker/chatterbox-api/app/api/endpoints/speech.py
- /home/oz/projects/2025/oz/12/runpod/docker/chatterbox-api/app/api/endpoints/voices.py
- /home/oz/projects/2025/oz/12/runpod/docker/chatterbox-api/app/api/endpoints/health.py
- /home/oz/projects/2025/oz/12/runpod/docker/chatterbox-api/app/core/mtl.py
- /home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/xtts-models-research.md
- /home/oz/projects/2025/oz/12/runpod/CHANGELOG.md

## At a Glance

| System | How you run it | Primary API/UI | Strengths | Planning VRAM |
|---|---|---|---|---:|
| VibeVoice-ComfyUI | Inside `hearmeman-extended` (ComfyUI) | http://localhost:8188 | Highest quality; ComfyUI workflows; (optional) LoRA; multi-speaker pipelines | ~8-16GB (depends on model) |
| XTTS v2 (Coqui) | Separate container (`daswer123/xtts-api-server`) | http://localhost:8020/docs | Simple REST API; multilingual (17 langs); voice cloning from short samples; audio streaming | ~4-8GB |
| Chatterbox TTS | Separate container (repo-local build) | http://localhost:8000/docs | OpenAI-compatible endpoints; voice library; aliases; raw streaming + SSE | ~2-6GB (model-dependent) |

**Ports (local docker defaults)**:
- ComfyUI: `8188`
- Chatterbox API: `8000` (host) -> `4123` (container)
- XTTS API: `8020` (if you run it)

## Environment requirements

### Hardware

- **GPU (recommended)**: NVIDIA CUDA-capable GPU.
- **VRAM planning**:
  - VibeVoice: ~8-16GB+ depending on model/quantization.
  - XTTS v2: ~4-8GB.
  - Chatterbox: ~2-6GB depending on model variant.

### Local Docker requirements

- Docker Engine + Docker Compose plugin.
- NVIDIA drivers + `nvidia-container-toolkit` (to use `--gpus all` / `runtime: nvidia`).
- Ports available on localhost: `8188` (ComfyUI), `8000` (Chatterbox), `8020` (XTTS if enabled).
- `ffmpeg` is useful for playback/inspection (`ffplay`, `ffprobe`).

### RunPod requirements (production template)

- **No manual steps**: models must be downloaded automatically at startup.
- For persistence across restarts, mount a volume to `/workspace` (otherwise models/voices will be re-downloaded/re-uploaded per pod lifecycle).

## Performance metrics (best-effort)

This repo does not hardcode benchmarks because TTS performance depends heavily on:
- GPU model + driver/CUDA stack
- cold vs warm model
- input length + chunking settings
- streaming mode and client buffering

Still, the following planning numbers are useful for capacity planning:

| System | Latency / speed notes | VRAM notes | Where it comes from |
|---|---|---|---|
| VibeVoice | Repo history recorded a single English run at **~20.62s** (for that workflow/prompt) on an L40S pod | ~8-16GB+ depending on model | `CHANGELOG.md` |
| XTTS v2 | Repo research notes: **~3-5s** for a short sentence on RTX 3090; streaming reduces perceived latency | ~4-8GB typical | `dev/agents/artifacts/doc/xtts-models-research.md` + repo notes |
| Chatterbox | Use `/audio/speech/stream` or SSE (`stream_format="sse"`) to reduce perceived latency; measure with `time` in your target hardware | ~2-6GB depending on model | planning + measure via `/health` + `/status` |

Quick way to measure "time to first byte" for streaming endpoints:

```bash
time curl -sS -o /dev/null -X POST http://localhost:8000/audio/speech/stream \
  -H "Content-Type: application/json" \
  -d '{"input":"Quick latency probe","voice":"default"}'
```

---

## 1) VibeVoice-ComfyUI

### 1.1 What it is

VibeVoice is used here as a **ComfyUI custom node** (repo cloned during image build). In practice:

- You use it via **ComfyUI workflows** (UI) or via the **ComfyUI HTTP API** (automation).
- It performs **voice cloning** from a reference audio file.

**Repository**: https://github.com/Enemyx-net/VibeVoice-ComfyUI (v1.8.1+)
**Model**: [aoi-ot/VibeVoice-Large](https://huggingface.co/aoi-ot/VibeVoice-Large) (~18GB)

### 1.2 Installation (this repo)

In the image build (`docker/Dockerfile`), the node repo is cloned into:

`/workspace/ComfyUI/custom_nodes/VibeVoice-ComfyUI`

and its Python requirements are installed (best-effort).

If you are installing manually (outside this Docker image):

```bash
cd /workspace/ComfyUI/custom_nodes
git clone --depth 1 https://github.com/Enemyx-net/VibeVoice-ComfyUI.git
cd VibeVoice-ComfyUI
pip install -r requirements.txt
```

### 1.3 Models, tokenizer, and expected paths

Startup download is handled by `docker/download_models.sh` when:

- `ENABLE_VIBEVOICE=true`
- `VIBEVOICE_MODEL` is one of: `1.5B`, `Large`, `Large-Q8`

**Downloaded to (default)**:
- `MODELS_DIR=/workspace/ComfyUI/models`
- VibeVoice models:
  - `vibevoice/VibeVoice-1.5B/`
  - `vibevoice/VibeVoice-Large/`
  - `vibevoice/VibeVoice-Large-Q8/`
- Qwen tokenizer required by VibeVoice:
  - `vibevoice/tokenizer/{tokenizer.json,merges.txt,vocab.json,tokenizer_config.json}`

### 1.4 Critical Dependencies

**Version requirements (CRITICAL)**:

```txt
bitsandbytes>=0.48.1  # Critical - older versions break Q8 model
transformers>=4.51.3
accelerate
peft
librosa
soundfile
```

**Verification**:
```bash
pip show bitsandbytes transformers | grep -E "Name:|Version:"
# Expected: bitsandbytes >= 0.48.1, transformers >= 4.51.3
```

### 1.5 Environment Variables

| Variable | Default | Size Impact | Notes |
|----------|---------|-------------|-------|
| `ENABLE_VIBEVOICE` | `true` | 18GB | Enable VibeVoice-Large TTS |
| `VIBEVOICE_MODEL` | `Large` | 18GB | Options: `1.5B`, `Large`, `Large-Q8` |

### 1.6 ComfyUI workflow node: `VibeVoiceSingleSpeakerNode`

The repo includes a working baseline workflow:

- `docker/workflows/vibevoice-tts-basic.json`

The node's API (as used in `docker/tts-comparison/test-vibevoice-oscar.py`) is:

```json
{
  "class_type": "VibeVoiceSingleSpeakerNode",
  "inputs": {
    "text": "...",
    "model": "VibeVoice-Large-Q8",
    "attention_type": "auto",
    "quantize_llm": "full precision",
    "free_memory_after_generate": false,
    "diffusion_steps": 20,
    "seed": 42,
    "cfg_scale": 1.3,
    "use_sampling": false,
    "voice_to_clone": ["<LoadAudioNodeId>", 0],
    "temperature": 0.95,
    "top_p": 0.95,
    "max_words_per_chunk": 250,
    "voice_speed_factor": 1.0
  }
}
```

**Field notes (operational)**:

| Field | Meaning | Typical values |
|---|---|---|
| `model` | Which VibeVoice variant to load | `VibeVoice-1.5B`, `VibeVoice-Large`, `VibeVoice-Large-Q8` |
| `voice_to_clone` | Reference audio for cloning | Output of `LoadAudio` |
| `diffusion_steps` | Quality vs speed | 20-42 |
| `cfg_scale` | Guidance scale | ~1.0-2.0 (start at `1.3`) |
| `seed` | Determinism | any int |
| `use_sampling` | Enables stochastic sampling | `false` to start |
| `temperature`, `top_p` | Sampling controls | ~0.9-1.0 |
| `max_words_per_chunk` | Chunk long text | 150-300 |
| `voice_speed_factor` | Speech speed | ~0.8-1.2 |
| `free_memory_after_generate` | If true, unload aggressively | `false` for batches |

### 1.7 VibeVoice via ComfyUI API (automation)

VibeVoice is invoked by sending the workflow graph to ComfyUI's `/prompt` endpoint, then polling `/history/{prompt_id}`.

**Key ComfyUI endpoints used (minimal set)**:

| Endpoint | Method | Purpose |
|---|---:|---|
| `/prompt` | POST | Queue a workflow prompt |
| `/history/{prompt_id}` | GET | Poll for completion + outputs |
| `/system_stats` | GET | Check server is alive + version/device |
| `/object_info/<NodeClass>` | GET | Inspect node input schema/options (useful for validation) |

**Example: queue a VibeVoice prompt (curl)**
(use the included workflow template as a starting point)

```bash
curl -sS http://localhost:8188/prompt \
  -H 'Content-Type: application/json' \
  -d @- <<'JSON'
{
  "prompt": {
    "1": {"class_type":"LoadAudio","inputs":{"audio":"reference_voice.mp3"}},
    "2": {"class_type":"VibeVoiceSingleSpeakerNode","inputs":{
      "text":"Hello from ComfyUI API.",
      "model":"VibeVoice-1.5B",
      "attention_type":"auto",
      "quantize_llm":"full precision",
      "free_memory_after_generate":true,
      "diffusion_steps":20,
      "seed":42,
      "cfg_scale":1.3,
      "use_sampling":false,
      "voice_to_clone":["1",0],
      "temperature":0.95,
      "top_p":0.95,
      "max_words_per_chunk":250,
      "voice_speed_factor":1.0
    }},
    "3": {"class_type":"SaveAudio","inputs":{"audio":["2",0],"filename_prefix":"vibevoice-api"}}
  }
}
JSON
```

**Example: queue + poll (Python)**
(adapted from `docker/tts-comparison/test-vibevoice-oscar.py`)

```python
import json
import time
import urllib.request

COMFYUI_URL = "http://localhost:8188"

workflow = {
  "1": {"class_type":"LoadAudio","inputs":{"audio":"reference_voice.mp3"}},
  "2": {"class_type":"VibeVoiceSingleSpeakerNode","inputs":{
    "text":"Hello from Python!",
    "model":"VibeVoice-1.5B",
    "attention_type":"auto",
    "quantize_llm":"full precision",
    "free_memory_after_generate":True,
    "diffusion_steps":20,
    "seed":123,
    "cfg_scale":1.3,
    "use_sampling":False,
    "voice_to_clone":["1",0],
    "temperature":0.95,
    "top_p":0.95,
    "max_words_per_chunk":250,
    "voice_speed_factor":1.0
  }},
  "3": {"class_type":"SaveAudio","inputs":{"audio":["2",0],"filename_prefix":"vibevoice-python"}}
}

req = urllib.request.Request(
    f"{COMFYUI_URL}/prompt",
    data=json.dumps({"prompt": workflow}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
prompt_id = resp["prompt_id"]

while True:
    hist = json.loads(urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}").read())
    if prompt_id in hist:
        print("Done:", hist[prompt_id].get("outputs", {}).keys())
        break
    time.sleep(1)
```

### 1.8 Voice reference file placement

The `LoadAudio` node's dropdown is populated from ComfyUI's input folder.

Common approaches:

```bash
# Copy a reference into the running ComfyUI container
docker cp ./reference_voice.mp3 hearmeman-extended:/workspace/ComfyUI/input/reference_voice.mp3
```

Or upload via the ComfyUI UI.

### 1.9 LoRA support (VibeVoice)

The workflow `docker/workflows/vibevoice-tts-basic.json` exposes an optional `lora` input of type `LORA_CONFIG` on `VibeVoiceSingleSpeakerNode`.

**Wiring pattern (in ComfyUI UI)**:
1. Add the VibeVoice LoRA config/loader node (search "VibeVoice" + "LoRA").
2. Select the LoRA file and strength(s).
3. Connect its output to `VibeVoiceSingleSpeakerNode.lora`.

**File placement (recommended)**:
- Put LoRAs under `MODELS_DIR=/workspace/ComfyUI/models/loras/` unless the node explicitly expects a different folder.

### 1.10 Multi-speaker (VibeVoice)

This repo only ships a **single-speaker** example workflow. In practice, multi-speaker can be done in two ways:

1) **Native multi-speaker node (if provided by your VibeVoice-ComfyUI version)**
Use ComfyUI to search for nodes containing "VibeVoice" and "Multi". To validate the exact schema via API:

```bash
curl -sS http://localhost:8188/object_info/VibeVoiceSingleSpeakerNode | jq .
```

2) **ComfyUI pipeline approach (always works)**
Generate each speaker's line separately (each with its own `LoadAudio` -> `VibeVoiceSingleSpeakerNode`) and then concatenate the resulting audio files (via ComfyUI audio nodes if available, or via `ffmpeg` externally).

### 1.11 Performance notes (VibeVoice)

Planning numbers:

- **VibeVoice-1.5B**: ~8-12GB VRAM (quality/throughput sweet spot for 16GB cards)
- **VibeVoice-Large**: typically needs 16GB+ VRAM
- **VibeVoice-Large-Q8**: lower disk/VRAM than Large, but can be slower

Observed (repo history):

- `CHANGELOG.md` records a **VibeVoice English** test at **~20.62s** on an L40S pod for the specific test prompt/workflow configuration used at the time.

### 1.12 GPU Selection by VRAM

| GPU VRAM | Recommended Model |
|----------|-------------------|
| 8-12GB | VibeVoice 1.5B |
| 16GB+ | VibeVoice 7B/Large |

---

## 2) XTTS v2 API (Coqui) via `daswer123/xtts-api-server`

### 2.1 What it is

XTTS v2 is a multilingual (17 language) voice cloning TTS system. In this repo it is treated as a **standalone service** because its dependency pins conflict with ComfyUI/VibeVoice.

**Image**: `daswer123/xtts-api-server:latest`
**Swagger UI**: http://localhost:8020/docs
**VRAM**: 4-8GB

### 2.2 Deployment (recommended: standalone container)

This repo no longer includes an `xtts` service in `docker/docker-compose.yml`. Run it separately:

```bash
docker run -d --name xtts \
  --gpus all \
  -p 8020:8020 \
  -v ./xtts-models:/app/models \
  -v ./xtts-speakers:/root/speakers \
  daswer123/xtts-api-server:latest
```

Notes:
- The **model cache** lives under `/app/models` in the container (mount it for persistence).
- If you pass a **file path** in `speaker_wav`, it must be a path **inside the container** (example above mounts `./xtts-speakers` to `/root/speakers`).

### 2.3 Endpoints (XTTS API)

Base URL: `http://localhost:8020`

| Endpoint | Method | Description |
|---|---:|---|
| `/health` | GET | Health check (if exposed by the server build) |
| `/tts_to_audio/` | POST | Generate audio and return bytes |
| `/tts_to_file` | POST | Generate audio and save to server path |
| `/tts_stream` | POST | Stream audio bytes (chunked) |
| `/speakers_list` | GET | List available speakers |
| `/languages` | GET | List supported languages |
| `/docs` | GET | Swagger UI |

### 2.4 Request schema (common fields)

All generation endpoints accept JSON like:

```json
{
  "text": "Hello world",
  "speaker_wav": "female",
  "language": "en"
}
```

Additional field for `/tts_to_file`:

```json
{
  "file_name_or_path": "/app/output/hello.wav"
}
```

**Field notes**:
- `speaker_wav` can be one of the built-in speakers (see `/speakers_list`) or a **path to a reference audio file** inside the container.
- Reference audio: internal docs in this repo recommend **6-10s** of clean speech for cloning (see `dev/agents/artifacts/doc/xtts-models-research.md`).

### 2.5 Speaker list (XTTS)

Built-in speaker names used throughout this repo:
- `male`
- `female`
- `calm_female`

To list what the server currently exposes:

```bash
curl -sS http://localhost:8020/speakers_list | jq .
```

### 2.6 Language list (XTTS v2: 17 languages)

| Code | Language |
|---|---|
| `ar` | Arabic |
| `cs` | Czech |
| `de` | German |
| `en` | English |
| `es` | Spanish |
| `fr` | French |
| `hi` | Hindi |
| `hu` | Hungarian |
| `it` | Italian |
| `ja` | Japanese |
| `ko` | Korean |
| `nl` | Dutch |
| `pl` | Polish |
| `pt` | Brazilian Portuguese |
| `ru` | Russian |
| `tr` | Turkish |
| `zh-cn` | Chinese (Simplified) |

Also available from the server:

```bash
curl -sS http://localhost:8020/languages | jq .
```

### 2.7 Usage examples (curl)

Generate bytes:

```bash
curl -sS -X POST http://localhost:8020/tts_to_audio/ \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","speaker_wav":"female","language":"en"}' \
  -o output.wav
```

Voice cloning with a mounted reference file:

```bash
curl -sS -X POST http://localhost:8020/tts_to_audio/ \
  -H "Content-Type: application/json" \
  -d '{"text":"Cloned voice test","speaker_wav":"/root/speakers/myvoice.wav","language":"en"}' \
  -o cloned.wav
```

Stream audio (pipe to `ffplay`):

```bash
curl -sS -X POST http://localhost:8020/tts_stream \
  -H "Content-Type: application/json" \
  -d '{"text":"Streaming test","speaker_wav":"female","language":"en"}' \
  | ffplay -autoexit -i -
```

### 2.8 Usage examples (Python)

```python
import requests

base = "http://localhost:8020"
payload = {"text": "Hello from XTTS", "speaker_wav": "female", "language": "en"}

audio = requests.post(f"{base}/tts_to_audio/", json=payload, timeout=120).content
open("xtts.wav", "wb").write(audio)
```

Streaming (chunked):

```python
import requests

base = "http://localhost:8020"
payload = {"text": "Streaming from Python", "speaker_wav": "female", "language": "en"}

with requests.post(f"{base}/tts_stream", json=payload, stream=True, timeout=120) as r:
    r.raise_for_status()
    with open("xtts-stream.wav", "wb") as f:
        for chunk in r.iter_content(chunk_size=64 * 1024):
            if chunk:
                f.write(chunk)
```

### 2.9 Performance notes (XTTS)

Planning numbers:
- VRAM: ~4-8GB typical
- Streaming: repo notes cite ~200ms "first chunk" in favorable conditions (hardware + warm model dependent)

---

## 3) Chatterbox TTS (standalone container)

### 3.1 What it is (in this repo)

This repo includes a complete FastAPI server under `docker/chatterbox-api/`.

Key properties:
- Provides **short "clean" endpoints** and **OpenAI-compatible `/v1/*` aliases**.
- Supports a **voice library** (upload voices, name them, add aliases, set default voice).
- Supports **two streaming styles**:
  - raw WAV chunk streaming
  - Server-Sent Events (SSE) with base64 audio deltas (OpenAI-like)

**Official Repository**: https://github.com/resemble-ai/chatterbox
**ComfyUI Node**: https://github.com/thefader/ComfyUI-Chatterbox
**OpenAI-Compatible API**: https://github.com/travisvn/chatterbox-tts-api

### 3.2 Model Variants

| Model | Parameters | Languages | License |
|-------|------------|-----------|---------|
| **Chatterbox Original** | 500M | English | MIT |
| **Chatterbox-Turbo** | 350M | English | MIT |
| **Chatterbox Multilingual** | 500M | 23 languages | MIT |

### 3.3 Container setup (local)

From `docker/docker-compose.yml`, the Chatterbox service is optional:

```bash
cd docker
docker compose --profile chatterbox up -d
```

Ports / volumes (compose defaults):

- Host `8000` -> container `4123`
- `./chatterbox-voices` -> `/app/voices` (voice library persistence)
- `./output` -> `/app/output` (server-side outputs if used)

Docs UI:
- `http://localhost:8000/docs`

### 3.4 Complete API endpoint map (primary + aliases)

Base URL (host): `http://localhost:8000`

The server includes an endpoint that enumerates everything:

```bash
curl -sS http://localhost:8000/endpoints | jq .
```

Below is the full alias map as configured in `docker/chatterbox-api/app/core/aliases.py` (primary endpoints shown; aliases in parentheses):

#### Core TTS endpoints

| Endpoint | Aliases | Method | Description |
|---|---|---:|---|
| `/audio/speech` | `/v1/audio/speech`, `/tts` | POST | Generate WAV audio (or SSE if `stream_format="sse"`) |
| `/audio/speech/upload` | `/v1/audio/speech/upload`, `/tts/upload` | POST | Multipart: optional voice file upload + generate |
| `/audio/speech/stream` | `/v1/audio/speech/stream`, `/tts/stream` | POST | Chunked WAV streaming |
| `/audio/speech/stream/upload` | `/v1/audio/speech/stream/upload`, `/tts/stream/upload` | POST | Multipart: optional voice file upload + chunked streaming |

#### Voice library endpoints

| Endpoint | Aliases | Method | Description |
|---|---|---:|---|
| `/voices` | `/v1/voices`, `/voice-library`, `/voice_library` | GET/POST | List voices / upload a voice |
| `/voices/default` | `/v1/voices/default`, `/default-voice` | GET/POST/DELETE | Get/set/reset default voice |
| `/voices/{voice_name}` | `/v1/voices/{voice_name}` | GET/PUT/DELETE | Voice info / rename / delete |
| `/voices/{voice_name}/download` | `/v1/voices/{voice_name}/download` | GET | Download original voice file |
| `/voices/{voice_name}/aliases` | `/v1/voices/{voice_name}/aliases` | GET/POST | List or add aliases |
| `/voices/{voice_name}/aliases/{alias}` | `/v1/voices/{voice_name}/aliases/{alias}` | DELETE | Remove alias |
| `/voices/all-names` | `/v1/voices/all-names` | GET | List all names + aliases |
| `/voices/cleanup` | `/v1/voices/cleanup` | POST | Remove metadata for missing files |
| `/languages` | (none) | GET | Supported languages (depends on model) |

#### Health / configuration / compatibility

| Endpoint | Aliases | Method | Description |
|---|---|---:|---|
| `/health` | `/v1/health`, `/status` | GET | Health + initialization + memory |
| `/ping` | (none) | GET | Simple connectivity check |
| `/models` | `/v1/models` | GET | OpenAI-style model list |
| `/config` | `/v1/config` | GET | Current server/model defaults |
| `/endpoints` | `/v1/endpoints`, `/routes` | GET | Endpoint + alias listing |
| `/memory` | `/v1/memory` | GET | Memory info + optional cleanup |
| `/memory/config` | `/v1/memory/config` | GET/POST | Memory thresholds |
| `/memory/reset` | `/v1/memory/reset` | POST | Aggressive cleanup (confirm required) |
| `/memory/recommendations` | `/v1/memory/recommendations` | GET | Heuristics-based recommendations |
| `/status` | `/v1/status`, `/processing`, `/processing/status` | GET | Current request status |
| `/status/progress` | `/v1/status/progress`, `/progress` | GET | Lightweight progress |
| `/status/history` | `/v1/status/history`, `/history` | GET | Recent request history |
| `/status/statistics` | `/v1/status/statistics`, `/stats` | GET | Aggregate statistics |
| `/status/history/clear` | `/v1/status/history/clear` | POST | Clear request history (confirm required) |
| `/info` | `/v1/info`, `/api/info` | GET | Combined info (version/status/memory/history) |

#### Long text TTS (job queue)

These endpoints are also aliased under `/v1/...` equivalents.

| Endpoint | Method | Description |
|---|---:|---|
| `/audio/speech/long` | POST | Create long-text job (async) |
| `/audio/speech/long` | GET | List active jobs |
| `/audio/speech/long/{job_id}` | GET/PATCH/DELETE | Inspect/update/cancel job |
| `/audio/speech/long/{job_id}/download` | GET | Download job audio |
| `/audio/speech/long/{job_id}/pause` | PUT | Pause job |
| `/audio/speech/long/{job_id}/resume` | PUT | Resume job |
| `/audio/speech/long/{job_id}/retry` | POST | Retry job |
| `/audio/speech/long/{job_id}/sse` | GET | SSE stream job status/events |
| `/audio/speech/long-history` | GET | List historical jobs |
| `/audio/speech/long-history/stats` | GET | Job history stats |
| `/audio/speech/long/{job_id}/details` | GET | Extended job details |
| `/audio/speech/long/history` | DELETE | Clear long-text history |
| `/audio/speech/long/bulk` | POST | Bulk job actions |

### 3.5 Request schema: `POST /audio/speech` (JSON)

From `docker/chatterbox-api/app/models/requests.py`:

```json
{
  "input": "Text to speak (1..3000 chars)",
  "voice": "alloy",
  "response_format": "wav",
  "speed": 1.0,
  "stream_format": "audio",
  "exaggeration": 0.5,
  "cfg_weight": 0.5,
  "temperature": 0.8,
  "streaming_chunk_size": 250,
  "streaming_strategy": "sentence",
  "streaming_buffer_size": 3,
  "streaming_quality": "balanced"
}
```

**Parameter ranges**

| Parameter | Range | Meaning |
|---|---|---|
| `exaggeration` | 0.25-2.0 | Expressiveness/emotion strength |
| `cfg_weight` | 0.0-1.0 | Pace/consistency control |
| `temperature` | 0.05-5.0 | Sampling randomness |
| `stream_format` | `audio` or `sse` | Raw WAV vs SSE events |
| `streaming_chunk_size` | 50-500 | Chunk size for streaming |
| `streaming_strategy` | `sentence`/`paragraph`/`fixed`/`word` | How to split input for streaming |
| `streaming_quality` | `fast`/`balanced`/`high` | Speed vs quality preset |

### 3.6 Artistic Controls

#### CFG (Classifier-Free Guidance)

| Value | Effect |
|-------|--------|
| 0.0 | Slower, clearer, more expressive |
| 0.5 | Default balance |
| 1.0 | Stricter adherence to input, faster |

#### Exaggeration

| Value | Effect |
|-------|-------|
| 0.0 | Subtle, professional tone |
| 0.5 | General purpose |
| 1.0+ | More dramatic, expressive delivery |

#### Recommended Settings

| Use Case | CFG | Exaggeration |
|----------|-----|--------------|
| General purpose | 0.5 | 0.5 |
| Expressive speech | 0.3 | 0.7+ |
| Fast speakers | 0.3 | 0.5 |
| Professional/formal | 0.5 | 0.3 |

### 3.7 Usage examples (curl)

Health check:

```bash
curl -sS http://localhost:8000/health | jq .
```

Basic TTS (OpenAI-compatible path):

```bash
curl -sS -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"chatterbox-tts-1","input":"Hello world","voice":"default"}' \
  -o cb.wav
```

Upload a voice into the library:

```bash
curl -sS -X POST http://localhost:8000/voices \
  -F "voice_file=@./myvoice.wav" \
  -F "voice_name=my-voice" \
  -F "language=en" | jq .
```

Generate with that voice (primary endpoint):

```bash
curl -sS -X POST http://localhost:8000/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input":"This should sound like my voice.","voice":"my-voice","exaggeration":0.6,"cfg_weight":0.5}' \
  -o myvoice.wav
```

Raw audio streaming:

```bash
curl -sS -X POST http://localhost:8000/audio/speech/stream \
  -H "Content-Type: application/json" \
  -d '{"input":"Streaming test","voice":"my-voice"}' \
  -o streamed.wav
```

SSE streaming (base64 deltas):

```bash
curl -N -sS -X POST http://localhost:8000/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input":"SSE streaming test","voice":"my-voice","stream_format":"sse"}'
```

### 3.8 Usage examples (Python)

```python
import requests

base = "http://localhost:8000"
payload = {"input": "Hello from Chatterbox", "voice": "default", "exaggeration": 0.6}

audio = requests.post(f"{base}/audio/speech", json=payload, timeout=300).content
open("chatterbox.wav", "wb").write(audio)
```

### 3.9 Speaker/voice list + language list (Chatterbox)

**Voices** are not hardcoded; they are whatever exists in the voice library directory.

List voices:

```bash
curl -sS http://localhost:8000/voices | jq .
```

List all voice names + aliases:

```bash
curl -sS http://localhost:8000/voices/all-names | jq .
```

Supported languages are exposed via:

```bash
curl -sS http://localhost:8000/languages | jq .
```

If `USE_MULTILINGUAL_MODEL=true` (default), the repo's supported language codes (from `docker/chatterbox-api/app/core/mtl.py`) are:

| Code | Language |
|---|---|
| `ar` | Arabic |
| `da` | Danish |
| `de` | German |
| `el` | Greek |
| `en` | English |
| `es` | Spanish |
| `fi` | Finnish |
| `fr` | French |
| `he` | Hebrew |
| `hi` | Hindi |
| `it` | Italian |
| `ja` | Japanese |
| `ko` | Korean |
| `ms` | Malay |
| `nl` | Dutch |
| `no` | Norwegian |
| `pl` | Polish |
| `pt` | Portuguese |
| `ru` | Russian |
| `sv` | Swedish |
| `sw` | Swahili |
| `tr` | Turkish |

Note: Chinese (`zh`) is commented out in this repo because `pkuseg` compatibility is currently an issue.

### 3.10 Performance notes (Chatterbox)

Planning numbers:
- VRAM: ~2-6GB depending on model (standard vs multilingual vs turbo)
- Streaming: best measured via `/status` and `/health` (both expose memory + progress)

Operationally:
- `GET /health` includes `memory_info` with GPU allocated MB (useful for VRAM tracking).

### 3.11 Reference Audio Requirements

| Parameter | Value |
|-----------|-------|
| Recommended length | 5-10 seconds |
| Minimum viable | ~3 seconds |
| Format | WAV (any standard format) |
| Quality | Clear speech, minimal background noise |

---

## 4) `xtts-vo-gen.py` (CLI for XTTS voice-over)

### 4.1 What it is

`docker/scripts/xtts-vo-gen.py` is a small CLI wrapper around the XTTS REST API. It is intended for voice-over automation:

- single line generation
- batch generation from a script file (one line per output)
- optional streaming to stdout for piping to a player

### 4.2 Requirements

- Python 3 (stdlib only; uses `urllib`)
- XTTS server reachable at `XTTS_API_URL` (default: `http://localhost:8020`)

### 4.3 Commands and options

```bash
python3 docker/scripts/xtts-vo-gen.py --help
```

Important flags (from the script):

| Flag | Meaning |
|---|---|
| `TEXT` | Positional text to synthesize |
| `-f, --file` | Script file; non-empty lines become separate outputs |
| `-o, --output` | Output WAV path (single-line mode) |
| `-d, --output-dir` | Output directory (batch mode) |
| `-s, --speaker` | Speaker name (`male`, `female`, `calm_female`) or a reference audio path |
| `-l, --language` | Language code (e.g. `en`, `es`) |
| `-p, --prefix` | Output filename prefix for batch |
| `--stream` | Write streaming audio bytes to stdout |
| `--list-speakers` | Query `/speakers_list` |
| `--list-languages` | Query `/languages` |
| `--api-url` | Override server URL (or set `XTTS_API_URL`) |

### 4.4 Examples

Single line:

```bash
python3 docker/scripts/xtts-vo-gen.py "Hello world" -o hello.wav
```

Batch:

```bash
python3 docker/scripts/xtts-vo-gen.py -f script.txt -d ./vo-output -p scene --speaker female --language en
```

Stream to a player:

```bash
python3 docker/scripts/xtts-vo-gen.py "Streaming test" --stream | ffplay -autoexit -i -
```

List speakers/languages:

```bash
python3 docker/scripts/xtts-vo-gen.py --list-speakers
python3 docker/scripts/xtts-vo-gen.py --list-languages
```

---

## 5) Dependencies and version conflicts

### 5.1 Critical Conflict: transformers

| System | Required Version | Conflict |
|--------|-----------------|----------|
| XTTS v2 API | `transformers==4.36.2` | **CONFLICTS** |
| VibeVoice-ComfyUI | `transformers>=4.51.3` | **CONFLICTS** |
| Chatterbox | Compatible with both | No conflict |

**Solution**: Run XTTS in a **separate container** from ComfyUI/VibeVoice.

### 5.2 Dependency Matrix

| Package | VibeVoice | XTTS | Chatterbox |
|---------|-----------|------|------------|
| torch | 2.x CUDA | 2.x CUDA | 2.x CUDA |
| torchaudio | Required | Required | Required |
| transformers | >=4.51.3 | ==4.36.2 | Compatible |
| accelerate | Required | Compatible | Compatible |
| bitsandbytes | >=0.48.1 | Compatible | Compatible |
| peft | Required | Compatible | Compatible |
| librosa | Required | Compatible | Compatible |
| soundfile | Required | Compatible | Compatible |

### 5.3 GPU Memory Allocation

| System | VRAM | Notes |
|--------|------|-------|
| XTTS v2 | ~4GB | Separate container |
| ComfyUI + VibeVoice | ~12GB | Main container |
| **Total (both running)** | ~16GB | Fits on 16GB GPU |

### 5.4 Complete Dependency Matrix (Planning)

| Component | Runs where | Notable constraints |
|---|---|---|
| VibeVoice-ComfyUI | inside ComfyUI container | `transformers>=4.51.3`, `bitsandbytes>=0.48.1`, GPU recommended |
| Chatterbox API | separate container (`docker/chatterbox-api`) | independent of ComfyUI's Python env; uses Chatterbox libs |
| XTTS API | separate container (`daswer123/xtts-api-server`) | `transformers` pin; GPU recommended |

### 5.5 Co-running (VRAM + throughput)

If you run ComfyUI + Chatterbox + XTTS on the same GPU:

- Expect aggregate VRAM usage to be additive.
- Prefer sequential/batched usage for stability (especially on 16GB cards).
- Use these monitoring hooks:
  - `nvidia-smi`
  - ComfyUI: `GET /system_stats`
  - Chatterbox: `GET /health`, `GET /status`

---

## 6) Quick Start Reference

### 6.1 Starting All TTS Services

```bash
cd /home/oz/projects/2025/oz/12/runpod/docker

# Start all services
docker compose up -d

# Or start individual profiles
docker compose --profile xtts up -d      # XTTS only
docker compose --profile chatterbox up -d  # Chatterbox only
```

### 6.2 Service URLs

| Service | URL | Notes |
|---------|-----|-------|
| ComfyUI | http://localhost:8188 | Main UI |
| XTTS Swagger | http://localhost:8020/docs | API docs |
| Chatterbox API | http://localhost:8000/health | Health check |

### 6.3 Health Checks

```bash
# Check XTTS
curl http://localhost:8020/speakers_list

# Check Chatterbox
curl http://localhost:8000/health

# Check ComfyUI
curl http://localhost:8188/system_stats
```

### 6.4 Testing Voice Generation

```bash
# Test XTTS
curl -X POST "http://localhost:8020/tts_to_audio/" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "speaker_wav": "female", "language": "en"}' \
  -o test_xtts.wav

# Test Chatterbox (OpenAI-compatible)
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model": "chatterbox", "input": "Hello world", "voice": "default"}' \
  -o test_chatterbox.wav
```

---

## Appendix: Quick start

Start ComfyUI (VibeVoice inside):

```bash
cd docker
docker compose up -d
open http://localhost:8188
```

Start Chatterbox:

```bash
cd docker
docker compose --profile chatterbox up -d
open http://localhost:8000/docs
```

Run XTTS (standalone) + test:

```bash
docker run -d --name xtts --gpus all -p 8020:8020 daswer123/xtts-api-server:latest
curl -sS http://localhost:8020/languages | jq .
```

---

## Sources

- [VibeVoice-ComfyUI GitHub](https://github.com/Enemyx-net/VibeVoice-ComfyUI)
- [VibeVoice-Large Model](https://huggingface.co/aoi-ot/VibeVoice-Large)
- [XTTS-API-Server GitHub](https://github.com/daswer123/xtts-api-server)
- [Chatterbox GitHub](https://github.com/resemble-ai/chatterbox)
- [ComfyUI-Chatterbox](https://github.com/thefader/ComfyUI-Chatterbox)
- [Chatterbox-TTS-API](https://github.com/travisvn/chatterbox-tts-api)
