# Chatterbox TTS from Resemble AI - Complete API Reference

**Author**: oz + claude-opus-4-5
**Date**: 2025-12-26
**Research Sources**: GitHub, Hugging Face, ComfyUI Registry

---

## Overview

Chatterbox is an open-source TTS model from Resemble AI that achieves state-of-the-art voice cloning with zero-shot capabilities. Key features:

- **Zero-shot voice cloning**: Clone any voice with ~10 seconds of reference audio
- **Emotion control**: Adjustable exaggeration and temperature parameters
- **Open weights**: Apache 2.0 license, fully open-source
- **Performance**: Outperforms ElevenLabs in 63.75% of blind preference tests (per Resemble AI)

**Official Repository**: https://github.com/resemble-ai/chatterbox

---

## 1. PyTorch API Usage (Programmatic)

### Installation

```bash
pip install chatterbox-tts
```

### Basic Usage

```python
import torch
import torchaudio as ta
from chatterbox import ChatterboxTurboTTS

# Initialize model (downloads automatically on first use)
device = "cuda" if torch.cuda.is_available() else "cpu"
model = ChatterboxTurboTTS.from_pretrained(device=device)

# Generate audio with zero-shot voice cloning
text = "Hello, this is a test of Chatterbox TTS from Resemble AI."
audio_prompt = "path/to/reference_10s_clip.wav"

wav = model.generate(
    text=text,
    audio_prompt_path=audio_prompt
)

# Save output
ta.save("output.wav", wav, model.sr)
```

### Generate Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | str | required | Text to synthesize |
| `audio_prompt_path` | str | required | Path to ~10s reference WAV for voice cloning |
| `exaggeration` | float | 1.0 | Emotional intensity (higher = more expressive) |
| `temperature` | float | 1.0 | Creativity/variation (higher = more varied) |

### Batch Processing Example

```python
import torch
import torchaudio as ta
from chatterbox import ChatterboxTurboTTS
from pathlib import Path

device = "cuda" if torch.cuda.is_available() else "cpu"
model = ChatterboxTurboTTS.from_pretrained(device=device)

texts = [
    "Welcome to AF High Definition Car Care.",
    "Your quote is ready for review.",
    "Please upload photos of the damage.",
]

output_dir = Path("./output")
output_dir.mkdir(exist_ok=True)

for i, text in enumerate(texts):
    wav = model.generate(
        text=text,
        audio_prompt_path="voices/elionn_reference.wav",
        exaggeration=0.8,  # Slightly less expressive for professional tone
        temperature=0.9,
    )
    ta.save(output_dir / f"message_{i}.wav", wav, model.sr)
```

---

## 2. Gradio Interface

Chatterbox includes a native Gradio web UI for interactive use.

### Option A: Hugging Face Space (No Setup)

Visit: https://huggingface.co/spaces/ResembleAI/Chatterbox

### Option B: Local Deployment

```bash
# Clone repository
git clone https://github.com/resemble-ai/chatterbox.git
cd chatterbox

# Install dependencies
pip install -r requirements.txt
pip install gradio

# Launch Gradio interface
python app.py
```

Access at: `http://localhost:7860`

### Gradio Features

- Real-time text-to-speech generation
- Audio file upload for voice cloning
- Pre-set voice selection
- Sliders for:
  - Speed control
  - Emotion/exaggeration
  - Temperature/creativity
- Audio playback and download

---

## 3. ComfyUI Integration

### Primary Node Package

**Repository**: https://github.com/thefader/ComfyUI-Chatterbox

### Installation

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/thefader/ComfyUI-Chatterbox
pip install -r ComfyUI-Chatterbox/requirements.txt
```

### Available Nodes

| Node | Purpose | Inputs |
|------|---------|--------|
| `Chatterbox TTS` | Text to audio | text, audio_prompt, exaggeration, temp |
| `Chatterbox Voice Conversion` | Audio-to-audio cloning | source_audio, target_voice |
| `Chatterbox Dialog TTS` | Multi-speaker dialogue | script, up to 4 voice prompts |

### Key Features

- **Auto-download**: Models download from Hugging Face on first use
- **VRAM Management**: Uses ComfyUI's model patcher for GPU memory optimization
- **Reproducibility**: Adjustable seed for consistent outputs
- **Version Status**: Active development, compatible with latest ComfyUI

### Example Workflow

```
[Text Input] → [Chatterbox TTS] → [Audio Preview] → [Save Audio]
                    ↑
            [Load Audio] (voice reference)
```

---

## 4. Self-Hosted API Deployment

### Option A: OpenAI-Compatible API (Recommended)

**Repository**: https://github.com/travisvn/chatterbox-tts-api

This provides an OpenAI-compatible `/v1/audio/speech` endpoint.

#### Docker Deployment

```bash
# Clone
git clone https://github.com/travisvn/chatterbox-tts-api.git
cd chatterbox-tts-api

# GPU deployment
docker compose -f docker/docker-compose.gpu.yml up -d

# CPU deployment (slower)
docker compose -f docker/docker-compose.yml up -d
```

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Server status |
| `/v1/voices` | GET | List available voices |
| `/v1/audio/speech` | POST | Generate audio (OpenAI-compatible) |

#### Usage Example

```bash
# Check health
curl http://localhost:8000/health

# Generate speech (OpenAI-compatible format)
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "chatterbox",
    "input": "Hello, this is a test.",
    "voice": "default"
  }' \
  --output speech.wav
```

#### Python Client

```python
import httpx

def synthesize(text: str, voice: str = "default") -> bytes:
    response = httpx.post(
        "http://localhost:8000/v1/audio/speech",
        json={
            "model": "chatterbox",
            "input": text,
            "voice": voice,
        }
    )
    return response.content

# Usage
audio = synthesize("Welcome to AF High Definition Car Care!")
with open("output.wav", "wb") as f:
    f.write(audio)
```

### Option B: Streaming API

**Repository**: https://github.com/dwain-barnes/chatterbox-streaming-api-docker

Optimized for low-latency streaming applications.

```bash
git clone https://github.com/dwain-barnes/chatterbox-streaming-api-docker.git
cd chatterbox-streaming-api-docker
docker compose up -d
```

---

## 5. AF Project Integration Guide

Based on existing patterns in the perito project:

### Recommended Architecture

```
/opt/clients/af/services/chatterbox-tts/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── chatterbox_api.py      # FastAPI wrapper
└── voices/                # Voice reference files
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System deps for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "chatterbox_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### requirements.txt

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
chatterbox-tts
torch
torchaudio
python-multipart==0.0.9
httpx>=0.25.0
```

### docker-compose.yml

```yaml
services:
  chatterbox-tts:
    build: .
    container_name: chatterbox-tts
    restart: unless-stopped
    env_file:
      - /opt/clients/af/.env
    ports:
      - "8002:8000"
    volumes:
      - /opt/clients/af/local_files/uploads:/app/uploads
      - ./voices:/app/voices
    networks:
      - af_default
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

networks:
  af_default:
    external: true
```

### API Implementation (chatterbox_api.py)

```python
"""
Chatterbox TTS API for AF High Definition Car Care
Port: 8002 (internal 8000)
"""
import os
import io
import torch
import torchaudio as ta
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from chatterbox import ChatterboxTurboTTS

app = FastAPI(title="Chatterbox TTS API", version="1.0.0")

# Initialize model
device = "cuda" if torch.cuda.is_available() else "cpu"
model = None

class TTSRequest(BaseModel):
    text: str
    voice: str = "default"  # Voice reference file name
    exaggeration: float = 0.8
    temperature: float = 0.9
    output_format: str = "wav"

@app.on_event("startup")
async def startup():
    global model
    model = ChatterboxTurboTTS.from_pretrained(device=device)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model": "chatterbox",
        "device": device,
        "gpu_available": torch.cuda.is_available(),
    }

@app.post("/api/synthesize")
async def synthesize(req: TTSRequest):
    if model is None:
        raise HTTPException(500, "Model not loaded")

    # Resolve voice reference
    voice_path = f"/app/voices/{req.voice}.wav"
    if not os.path.exists(voice_path):
        voice_path = "/app/voices/default.wav"

    # Generate audio
    wav = model.generate(
        text=req.text,
        audio_prompt_path=voice_path,
        exaggeration=req.exaggeration,
        temperature=req.temperature,
    )

    # Convert to bytes
    buffer = io.BytesIO()
    ta.save(buffer, wav, model.sr, format=req.output_format)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type=f"audio/{req.output_format}",
        headers={
            "Content-Disposition": f"attachment; filename=speech.{req.output_format}"
        }
    )

@app.get("/v1/voices")
async def list_voices():
    """List available voice references."""
    voices_dir = "/app/voices"
    if not os.path.exists(voices_dir):
        return {"voices": ["default"]}

    voices = [
        f.replace(".wav", "")
        for f in os.listdir(voices_dir)
        if f.endswith(".wav")
    ]
    return {"voices": voices}
```

### n8n Integration

HTTP Request node configuration:

```json
{
  "method": "POST",
  "url": "http://chatterbox-tts:8000/api/synthesize",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "text": "{{ $json.message }}",
    "voice": "elionn",
    "exaggeration": 0.8,
    "temperature": 0.9,
    "output_format": "ogg"
  }
}
```

---

## 6. Version Compatibility

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.10+ | 3.11 recommended |
| PyTorch | 2.0+ | CUDA 11.8+ for GPU |
| chatterbox-tts | latest | pip install |
| ComfyUI | Latest | Works with current |
| VRAM | 8GB+ | For GPU inference |

### Model Download

Models download automatically from Hugging Face on first use:
- `ResembleAI/chatterbox` - Main checkpoint (~1.5GB)

---

## Sources

- **Official Repository**: https://github.com/resemble-ai/chatterbox
- **Hugging Face Demo**: https://huggingface.co/spaces/ResembleAI/Chatterbox
- **Demo Page**: https://resemble-ai.github.io/chatterbox_demopage/
- **ComfyUI Nodes**: https://github.com/thefader/ComfyUI-Chatterbox
- **OpenAI-Compatible API**: https://github.com/travisvn/chatterbox-tts-api
- **Streaming API**: https://github.com/dwain-barnes/chatterbox-streaming-api-docker

---

## Quick Start Summary

```bash
# 1. Quickest - Hugging Face Space
https://huggingface.co/spaces/ResembleAI/Chatterbox

# 2. Local Python
pip install chatterbox-tts
python -c "from chatterbox import ChatterboxTurboTTS; print('OK')"

# 3. Docker API (OpenAI-compatible)
git clone https://github.com/travisvn/chatterbox-tts-api.git
cd chatterbox-tts-api
docker compose -f docker/docker-compose.gpu.yml up -d
curl http://localhost:8000/health

# 4. ComfyUI
cd ComfyUI/custom_nodes
git clone https://github.com/thefader/ComfyUI-Chatterbox
```
