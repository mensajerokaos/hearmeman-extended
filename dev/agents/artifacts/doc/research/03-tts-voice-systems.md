# Text-to-Speech and Voice Systems Documentation

**Author**: oz + claude-haiku-4-5
**Date**: 2025-01-17
**Project**: RunPod Custom Templates - AI Model Deployment
**Status**: Research Complete

---

## Table of Contents

1. [VibeVoice-ComfyUI](#1-vibevoice-comfyui)
2. [XTTS v2 API Server](#2-xtts-v2-api-server)
3. [Chatterbox TTS](#3-chatterbox-tts)
4. [VO Generation Scripts](#4-vo-generation-scripts)
5. [Dependencies and Conflicts](#5-dependencies-and-conflicts)
6. [Performance and VRAM Usage](#6-performance-and-vram-usage)
7. [Quick Reference](#7-quick-reference)

---

## 1. VibeVoice-ComfyUI

### Overview

VibeVoice-ComfyUI is a high-quality text-to-speech system integrated as a ComfyUI custom node. It supports multi-speaker TTS, voice cloning from audio references, and LoRA support for voice customization.

**Repository**: https://github.com/AIFSH/VibeVoice-ComfyUI
**Model**: [aoi-ot/VibeVoice-Large](https://huggingface.co/aoi-ot/VibeVoice-Large) (~18GB)
**Status**: Active development, auto-downloads models + Qwen tokenizer

### Installation

```bash
# Clone into ComfyUI custom_nodes directory
cd ComfyUI/custom_nodes
git clone --depth 1 https://github.com/AIFSH/VibeVoice-ComfyUI.git
cd VibeVoice-ComfyUI

# Dependencies are installed automatically by ComfyUI-Manager
# Manual install if needed:
pip install -r requirements.txt
```

### Dependencies

```txt
bitsandbytes>=0.48.1  # Critical - older versions break Q8 model
transformers>=4.51.3
accelerate
peft
librosa
soundfile
torch
torchaudio
```

### Model Variants

| Model | Size | VRAM | Use Case |
|-------|------|------|----------|
| **VibeVoice-Large** | ~18GB | 16GB+ | Maximum quality, 7B parameter model |
| **VibeVoice-1.5B** | ~5.4GB | 8-12GB | Faster inference, lower VRAM |
| **VibeVoice-Large-Q8** | ~10GB | 12GB+ | Quantized version for efficiency |

### Environment Variables

```bash
# Enable VibeVoice in RunPod template
ENABLE_VIBEVOICE=true

# Model selection (Large, 1.5B, or Large-Q8)
VIBEVOICE_MODEL=Large
```

### ComfyUI Nodes

Available nodes in VibeVoice-ComfyUI:

| Node | Description | Inputs |
|------|-------------|--------|
| VibeVoice TTS | Main text-to-speech node | text, speaker, language, speed |
| VibeVoice Voice Cloning | Clone from reference audio | text, reference_audio, language |
| VibeVoice Multi-Speaker | Multi-speaker dialogue | script, speaker_1, speaker_2, ... |
| VibeVoice LoRA | Voice customization | text, lora_path, strength |

### Usage Example (Python)

```python
import torch
from vibevoice import VibeVoiceTTS

# Initialize model
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = VibeVoiceTTS.from_pretrained(
    model_path="microsoft/VibeVoice-Large",
    device=device
)

# Generate speech with voice cloning
text = "Hello, this is a test of VibeVoice TTS."
reference_audio = "path/to/speaker_reference.wav"

audio = tts.generate(
    text=text,
    audio_prompt_path=reference_audio,
    language="en",
    speed=1.0,
    emotion_strength=0.5
)

# Save audio
tts.save(audio, "output.wav", sample_rate=22050)
```

### Features

- **Multi-speaker TTS**: Up to 4 simultaneous speakers
- **Voice cloning**: 10-30 seconds of reference audio
- **LoRA support**: Fine-tuned voice adaptations
- **Speed control**: Adjustable speech rate
- **Emotion control**: Intensity parameters for expressiveness
- **Multilingual**: English, Spanish, French, German, Chinese, Japanese, Korean, and others

---

## 2. XTTS v2 API Server

### Overview

XTTS v2 is a multilingual TTS model from Coqui AI, providing high-quality voice synthesis in 17 languages. The standalone API server runs in a separate Docker container to avoid dependency conflicts.

**Image**: `daswer123/xtts-api-server:latest`
**Status**: Production-ready, separate container due to version conflicts
**Swagger UI**: http://localhost:8020/docs
**VRAM**: 4-8GB

### Docker Deployment

```bash
# Start XTTS service
docker compose --profile xtts up -d

# Or start XTTS only
docker compose --profile xtts up xtts -d

# Verify health
curl http://localhost:8020/health
```

### API Endpoints

#### Base URL
```
http://localhost:8020
```

#### Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tts_to_audio/` | POST | Returns audio bytes directly |
| `/tts_to_file` | POST | Saves to server file path |
| `/tts_stream` | POST | Streams audio chunks |
| `/speakers_list` | GET | List available speakers |
| `/languages` | GET | List supported languages |
| `/health` | GET | Server health check |

### Request/Response Examples

#### Generate Audio (Direct Response)

```bash
curl -X POST "http://localhost:8020/tts_to_audio/" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world",
    "speaker_wav": "female",
    "language": "en"
  }' \
  -o output.wav
```

#### Generate Audio (Save to File)

```bash
curl -X POST "http://localhost:8020/tts_to_file" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Voice over script here",
    "speaker_wav": "male",
    "language": "en",
    "file_name_or_path": "/app/audio/output.wav"
  }'
```

#### Stream Audio

```bash
curl -X POST "http://localhost:8020/tts_stream" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Streaming audio test",
    "speaker_wav": "female",
    "language": "en"
  }' \
  | ffplay -i -
```

#### List Available Speakers

```bash
curl http://localhost:8020/speakers_list
```

Response:
```json
["male", "female", "calm_female"]
```

#### List Supported Languages

```bash
curl http://localhost:8020/languages
```

Response:
```json
{
  "languages": {
    "Arabic": "ar",
    "Brazilian Portuguese": "pt",
    "Chinese": "zh-cn",
    "Czech": "cs",
    "Dutch": "nl",
    "English": "en",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Polish": "pl",
    "Russian": "ru",
    "Spanish": "es",
    "Turkish": "tr",
    "Japanese": "ja",
    "Korean": "ko",
    "Hungarian": "hu",
    "Hindi": "hi"
  }
}
```

### Python Client

```python
import requests
import json

class XTTSClient:
    def __init__(self, base_url="http://localhost:8020"):
        self.base_url = base_url

    def tts_to_audio(self, text, speaker="female", language="en"):
        """Generate audio and return bytes."""
        response = requests.post(
            f"{self.base_url}/tts_to_audio/",
            json={
                "text": text,
                "speaker_wav": speaker,
                "language": language
            }
        )
        return response.content

    def tts_to_file(self, text, output_path, speaker="female", language="en"):
        """Generate audio and save to file."""
        response = requests.post(
            f"{self.base_url}/tts_to_file",
            json={
                "text": text,
                "speaker_wav": speaker,
                "language": language,
                "file_name_or_path": output_path
            }
        )
        return response.json()

    def list_speakers(self):
        """List available speakers."""
        response = requests.get(f"{self.base_url}/speakers_list")
        return response.json()

    def list_languages(self):
        """List supported languages."""
        response = requests.get(f"{self.base_url}/languages")
        return response.json()

# Usage
client = XTTSClient()
audio = client.tts_to_audio("Hello world", speaker="female", language="en")
with open("output.wav", "wb") as f:
    f.write(audio)
```

### Voice Cloning with Custom Reference

```bash
# Use a custom reference audio file
curl -X POST "http://localhost:8020/tts_to_audio/" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Clone my voice saying this text",
    "speaker_wav": "/path/to/my_voice_reference.wav",
    "language": "en"
  }' \
  -o cloned_voice.wav
```

### Streaming Latency

- **First chunk**: ~200ms
- **Full audio**: Proportional to text length
- **Real-time playback**: Supported via streaming endpoint

---

## 3. Chatterbox TTS

### Overview

Chatterbox TTS is an open-source voice cloning system from Resemble AI with zero-shot capabilities and emotion control. It provides an OpenAI-compatible API format.

**Repository**: https://github.com/resemble-ai/chatterbox
**ComfyUI Node**: https://github.com/thefader/ComfyUI-Chatterbox
**VRAM**: 2-4GB
**Status**: Production-ready, Apache 2.0 license

### Features

- **Zero-shot voice cloning**: Clone any voice with ~10 seconds of reference audio
- **Emotion control**: Adjustable exaggeration and temperature parameters
- **Open weights**: Fully open-source, Apache 2.0 license
- **Performance**: Outperforms ElevenLabs in 63.75% of blind preference tests

### Docker Deployment

```bash
# Start Chatterbox service (requires GPU)
docker compose --profile chatterbox up -d

# Access API at http://localhost:8000
# Swagger docs: http://localhost:8000/docs
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Server health check |
| `/v1/models` | GET | List available models |
| `/v1/voices` | GET | List available voices |
| `/v1/audio/speech` | POST | Generate audio (OpenAI-compatible) |
| `/config` | GET | Get current configuration |

### Request Parameters

**POST /v1/audio/speech**

```json
{
  "input": "Text to convert to speech",
  "voice": "default",
  "response_format": "wav",
  "speed": 1.0,
  "exaggeration": 0.7,
  "cfg_weight": 0.4,
  "temperature": 0.9
}
```

#### Parameter Details

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `input` | string | required | 1-3000 chars | Text to synthesize |
| `voice` | string | "default" | - | Voice name or path |
| `exaggeration` | float | 0.5 | 0.25-2.0 | Emotion intensity |
| `cfg_weight` | float | 0.5 | 0.0-1.0 | Pace/speed control |
| `temperature` | float | 0.8 | 0.05-5.0 | Creativity/variation |

### Example Usage

#### cURL

```bash
# Basic usage
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello, this is a test."}' \
  --output speech.wav

# With custom parameters
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Dramatic speech!",
    "exaggeration": 1.2,
    "cfg_weight": 0.3,
    "temperature": 1.0
  }' \
  --output dramatic.wav

# Using custom voice
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello with custom voice!",
    "voice": "my-uploaded-voice"
  }' \
  --output custom_voice.wav
```

#### Python

```python
import httpx

def synthesize(text: str, voice: str = "default", **params) -> bytes:
    """Generate speech using Chatterbox TTS."""
    response = httpx.post(
        "http://localhost:8000/v1/audio/speech",
        json={
            "model": "chatterbox",
            "input": text,
            "voice": voice,
            **params
        }
    )
    return response.content

# Usage
audio = synthesize("Welcome to the system!")
with open("output.wav", "wb") as f:
    f.write(audio)

# With emotion control
audio = synthesize("Exciting news!", exaggeration=1.0, temperature=1.2)
```

#### JavaScript

```javascript
const response = await fetch('http://localhost:8000/v1/audio/speech', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    input: 'Hello world',
    exaggeration: 0.7,
    cfg_weight: 0.4,
    temperature: 0.9
  }),
});

if (response.ok) {
  const audioBuffer = await response.arrayBuffer();
  // Save or play the audio buffer
}
```

### Parameter Effects

#### Exaggeration (0.25-2.0)

| Value | Effect |
|-------|--------|
| 0.3-0.4 | Very neutral, professional |
| 0.5 | Neutral (default) |
| 0.7-0.8 | More expressive |
| 1.0+ | Very dramatic (may be unstable) |

#### CFG Weight (0.0-1.0)

| Value | Effect |
|-------|--------|
| 0.2-0.3 | Faster speech |
| 0.5 | Balanced (default) |
| 0.7-0.8 | Slower, more deliberate |

#### Temperature (0.05-5.0)

| Value | Effect |
|-------|--------|
| 0.4-0.6 | More consistent |
| 0.8 | Balanced (default) |
| 1.0+ | More creative/random |

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cuda",
  "config": {
    "max_chunk_length": 280,
    "max_total_length": 3000,
    "voice_sample_path": "./voice-sample.mp3",
    "default_exaggeration": 0.5,
    "default_cfg_weight": 0.5,
    "default_temperature": 0.8
  }
}
```

### ComfyUI Integration

```bash
# Install ComfyUI node
cd ComfyUI/custom_nodes
git clone https://github.com/thefader/ComfyUI-Chatterbox
cd ComfyUI-Chatterbox
pip install -r requirements.txt
```

#### Available Nodes

| Node | Description |
|------|-------------|
| Chatterbox TTS | Text to audio with voice cloning |
| Chatterbox Voice Conversion | Audio-to-audio cloning |
| Chatterbox Dialog TTS | Multi-speaker dialogue |

---

## 4. VO Generation Scripts

### Overview

The `xtts-vo-gen.py` script provides a command-line interface for batch TTS generation using the XTTS API server. It's designed for voice-over production workflows.

**Location**: `/home/oz/projects/2025/oz/12/runpod/docker/scripts/xtts-vo-gen.py`

### Installation

The script is included in the project and requires no additional installation. Ensure the XTTS API server is running:

```bash
# Start XTTS service first
docker compose --profile xtts up -d
```

### Usage

#### Single Line Generation

```bash
# Basic usage
python xtts-vo-gen.py "Hello world" -o hello.wav

# Custom speaker
python xtts-vo-gen.py "Hello world" -s male -o hello_male.wav

# Different language
python xtts-vo-gen.py "Bonjour le monde" -l fr -o french.wav
```

#### Batch Processing from File

```bash
# Process script file (one line per output)
python xtts-vo-gen.py --file script.txt --output-dir ./vo-output

# With custom prefix
python xtts-vo-gen.py -f script.txt -d ./vo-output -p scene

# Custom speaker for all lines
python xtts-vo-gen.py -f script.txt -s female -l en -d ./vo-output
```

#### Voice Cloning

```bash
# Use custom reference audio
python xtts-vo-gen.py "Clone this voice" --speaker /path/to/reference.wav -o output.wav
```

#### Streaming

```bash
# Stream audio to stdout (pipe to ffplay)
python xtts-vo-gen.py "Hello world" --stream | ffplay -

# With custom speaker
python xtts-vo-gen.py "Streaming test" --stream -s male | ffplay -
```

#### Listing Resources

```bash
# List available speakers
python xtts-vo-gen.py --list-speakers

# List supported languages
python xtts-vo-gen.py --list-languages

# Custom API URL
python xtts-vo-gen.py --api-url http://xtts-server:8020 --list-speakers
```

### Command Options

| Option | Description |
|--------|-------------|
| `text` | Text to synthesize (positional, optional) |
| `-f, --file` | Script file (one line per output) |
| `-o, --output` | Output file path |
| `-d, --output-dir` | Output directory for batch processing |
| `-s, --speaker` | Speaker voice (default: female) |
| `-l, --language` | Language code (default: en) |
| `-p, --prefix` | Filename prefix for batch output |
| `--stream` | Stream audio to stdout |
| `--list-speakers` | List available speakers |
| `--list-languages` | List supported languages |
| `--api-url` | XTTS API URL |

### Built-in Speakers

```
male, female, calm_female
```

### Supported Languages

| Code | Language |
|------|----------|
| ar | Arabic |
| pt | Brazilian Portuguese |
| zh-cn | Chinese |
| cs | Czech |
| nl | Dutch |
| en | English |
| fr | French |
| de | German |
| it | Italian |
| pl | Polish |
| ru | Russian |
| es | Spanish |
| tr | Turkish |
| ja | Japanese |
| ko | Korean |
| hu | Hungarian |
| hi | Hindi |

### Example Script File

```text
# script.txt
Welcome to our automated system.
Your quote is ready for review.
Please upload photos of the damage.
We will process your request shortly.
Thank you for choosing our service.
```

### Batch Processing Example

```bash
# Process script with progress output
$ python xtts-vo-gen.py -f script.txt -d ./vo-output -p message

Processing 5 lines...
[1/5] Welcome to our automated system...
  -> ./vo-output/message_001.wav
[2/5] Your quote is ready for review...
  -> ./vo-output/message_002.wav
[3/5] Please upload photos of the damage...
  -> ./vo-output/message_003.wav
[4/5] We will process your request shortly...
  -> ./vo-output/message_004.wav
[5/5] Thank you for choosing our service...
  -> ./vo-output/message_005.wav

Done! Generated 5 audio files in ./vo-output
```

### API Integration (Programmatic)

```python
import subprocess

def generate_vo(text: str, output_path: str, speaker: str = "female", language: str = "en"):
    """Generate voice-over using xtts-vo-gen.py."""
    result = subprocess.run(
        ["python", "xtts-vo-gen.py", text, "-o", output_path, "-s", speaker, "-l", language],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(f"Saved: {output_path}")
    else:
        print(f"Error: {result.stderr}")

# Usage
generate_vo("Welcome message", "welcome.wav")
```

---

## 5. Dependencies and Conflicts

### Dependency Matrix

| Component | Python | PyTorch | transformers | bitsandbytes | Notes |
|-----------|--------|---------|--------------|--------------|-------|
| **VibeVoice-ComfyUI** | 3.10+ | 2.0+ | >=4.51.3 | >=0.48.1 | Conflicts with XTTS |
| **XTTS v2** | 3.8+ | 2.0+ | ==4.36.2 | - | Separate container |
| **Chatterbox TTS** | 3.10+ | 2.0+ | Any | - | Compatible with both |

### Critical Conflict: transformers Version

**Problem**: VibeVoice requires `transformers>=4.51.3` while XTTS v2 requires `transformers==4.36.2`.

**Solution**: Run XTTS v2 in a separate Docker container with its own isolated Python environment.

### Docker Container Separation

```yaml
# docker-compose.yml
services:
  # VibeVoice + Chatterbox (in ComfyUI container)
  hearmeman-extended:
    build: .
    environment:
      - ENABLE_VIBEVOICE=true
    # Uses transformers>=4.51.3

  # XTTS v2 (separate container)
  xtts:
    image: daswer123/xtts-api-server:latest
    ports:
      - "8020:8020"
    # Uses transformers==4.36.2 (isolated)

  # Chatterbox TTS API
  chatterbox:
    build: ./chatterbox-api
    ports:
      - "8000:4123"
    # Compatible with any transformers version
```

### bitsandbytes Requirement

**VibeVoice-specific**: Requires `bitsandbytes>=0.48.1` for Q8 model quantization support.

```bash
# Install with correct version
pip install bitsandbytes>=0.48.1
```

**Note**: Older versions (<=0.48.0) break Q8 model support and cause import errors.

### VRAM Requirements by System

| System | Minimum VRAM | Recommended VRAM | Notes |
|--------|--------------|------------------|-------|
| VibeVoice-Large | 16GB | 24GB+ | 7B parameters |
| VibeVoice-1.5B | 8GB | 12GB | 1.5B parameters |
| VibeVoice-Large-Q8 | 12GB | 16GB | Quantized |
| XTTS v2 | 4GB | 8GB | Lightweight |
| Chatterbox TTS | 2GB | 4GB | Minimal footprint |

### GPU Memory Allocation

When running multiple systems, allocate VRAM carefully:

```
Total VRAM: 24GB (RTX 4090)

├── VibeVoice-Large:  ~12-14GB
├── ComfyUI base:     ~2-4GB
├── XTTS (optional):  ~4GB (separate container)
└── Chatterbox API:   ~2GB (separate container)

Total usage: ~18-24GB (fits in 24GB)
```

### Python Environment Management

**Best Practice**: Use separate virtual environments or Docker containers for each TTS system.

```bash
# ComfyUI environment (VibeVoice)
pip install transformers>=4.51.3 bitsandbytes>=0.48.1

# XTTS environment (separate)
pip install transformers==4.36.2

# Chatterbox environment (flexible)
pip install transformers  # Any version works
```

---

## 6. Performance and VRAM Usage

### Latency Comparison

| System | First Token | Full Generation | Streaming |
|--------|-------------|-----------------|-----------|
| **VibeVoice-Large** | ~500ms | ~2-5s (varies) | No |
| **VibeVoice-1.5B** | ~300ms | ~1-3s | No |
| **XTTS v2** | ~200ms | ~1-4s | Yes (~200ms chunkChatterbox T) |
| **TS** | ~100ms | ~0.5-2s | No |

### Real-Time Factor (RTF)

| System | RTF (seconds/second) | Notes |
|--------|---------------------|-------|
| **VibeVoice-Large** | ~0.3-0.5 | Higher quality, slower |
| **VibeVoice-1.5B** | ~0.2-0.3 | Faster, slightly lower quality |
| **XTTS v2** | ~0.15-0.3 | Good balance |
| **Chatterbox TTS** | ~0.1-0.2 | Fastest generation |

### VRAM Usage by Configuration

#### VibeVoice (1.5B Model)

```
Input length: 100 chars
VRAM: ~8-10GB
Peak memory: ~12GB
Output: 22050 Hz WAV
```

#### VibeVoice (Large Model)

```
Input length: 100 chars
VRAM: ~14-16GB
Peak memory: ~20GB
Output: 22050 Hz WAV
```

#### XTTS v2

```
Input length: 100 chars
VRAM: ~4-6GB
Peak memory: ~8GB
Output: 22050 Hz WAV
```

#### Chatterbox TTS

```
Input length: 100 chars
VRAM: ~2-4GB
Peak memory: ~6GB
Output: 22050 Hz WAV
```

### Throughput (Parallel Requests)

| System | Concurrent Requests | Notes |
|--------|--------------------|-------|
| **VibeVoice** | 1-2 | GPU memory intensive |
| **XTTS v2** | 3-5 | Lightweight, efficient |
| **Chatterbox TTS** | 2-4 | Good concurrency |

### Model Loading Time

| System | Cold Start | Warm Start |
|--------|-----------|-----------|
| **VibeVoice-Large** | ~60-90s | ~5-10s |
| **VibeVoice-1.5B** | ~30-45s | ~3-5s |
| **XTTS v2** | ~20-30s | ~2-3s |
| **Chatterbox TTS** | ~30-60s | ~5-10s |

### Optimization Tips

1. **Batch processing**: Process multiple lines in sequence for better throughput
2. **Model warmup**: Send a test request before production to warm up models
3. **GPU selection**: Use `CUDA_VISIBLE_DEVICES` to control GPU allocation
4. **Memory management**: Monitor with `nvidia-smi` and adjust batch sizes
5. **CPU offloading**: For 24GB cards, offload to CPU when needed

```bash
# Example: Run with specific GPU
CUDA_VISIBLE_DEVICES=0 python xtts-vo-gen.py "test" -o test.wav

# Example: Monitor GPU usage
watch -n 1 nvidia-smi
```

---

## 7. Quick Reference

### Quick Start Commands

```bash
# 1. Start all services
cd /home/oz/projects/2025/oz/12/runpod/docker
docker compose up -d

# 2. Check XTTS server
curl http://localhost:8020/health

# 3. Test Chatterbox API
curl http://localhost:8000/health

# 4. Generate voice-over
python scripts/xtts-vo-gen.py "Hello world" -o hello.wav

# 5. Check GPU usage
nvidia-smi
```

### Port Reference

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| ComfyUI | 8188 | http://localhost:8188 | Main UI + VibeVoice |
| XTTS API | 8020 | http://localhost:8020/docs | XTTS v2 REST API |
| Chatterbox | 8000 | http://localhost:8000/docs | OpenAI-compatible API |

### Environment Variables

```bash
# VibeVoice (in hearmeman-extended)
ENABLE_VIBEVOICE=true
VIBEVOICE_MODEL=Large  # or 1.5B, Large-Q8

# Storage
STORAGE_MODE=persistent  # or ephemeral
```

### File Locations

```
/home/oz/projects/2025/oz/12/runpod/
├── docker/
│   ├── scripts/
│   │   └── xtts-vo-gen.py           # VO generation script
│   ├── chatterbox-api/              # Chatterbox TTS API
│   ├── custom_nodes/
│   │   └── VibeVoice-ComfyUI/       # VibeVoice node
│   └── docker-compose.yml           # Service configuration
├── models/                          # Shared model storage
└── output/                          # Generated outputs
```

### Model Download Locations

```
/workspace/ComfyUI/models/
├── vibevoice/
│   ├── VibeVoice-Large/            # ~18GB
│   ├── VibeVoice-1.5B/             # ~5.4GB
│   └── VibeVoice-Large-Q8/         # ~10GB
├── whisper/                         # ~150MB
└── rvc/                            # Voice conversion
```

### Troubleshooting

#### XTTS Connection Error

```bash
# Check if XTTS is running
curl http://localhost:8020/health

# Restart XTTS
docker compose --profile xtts restart xtts

# Check logs
docker logs xtts
```

#### VibeVoice Model Not Found

```bash
# Verify model download
ls -la /workspace/ComfyUI/models/vibevoice/

# Re-download
export ENABLE_VIBEVOICE=true
./download_models.sh

# Check environment
echo $ENABLE_VIBEVOICE
```

#### Chatterbox Voice Not Found

```bash
# List available voices
curl http://localhost:8000/v1/voices

# Add voice reference
cp my_voice.wav /path/to/chatterbox-voices/
```

#### GPU Out of Memory

```bash
# Monitor GPU memory
nvidia-smi

# Reduce VRAM usage (for VibeVoice)
export VIBEVOICE_MODEL=1.5B  # Use smaller model

# Restart with CPU fallback
export DEVICE=cpu
```

### Further Resources

- **VibeVoice Repository**: https://github.com/AIFSH/VibeVoice-ComfyUI
- **VibeVoice Models**: https://huggingface.co/aoi-ot/VibeVoice-Large
- **XTTS v2 Docker**: https://github.com/daswer123/xtts-api-server
- **Chatterbox Repository**: https://github.com/resemble-ai/chatterbox
- **ComfyUI-Chatterbox**: https://github.com/thefader/ComfyUI-Chatterbox
- **OpenAI TTS API**: https://platform.openai.com/docs/api-reference/audio

---

**Document Version**: 1.0
**Last Updated**: 2025-01-17
**Next Review**: 2025-02-17
