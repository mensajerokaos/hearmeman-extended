# Chatterbox TTS API Research - Local Findings

**Date**: 2025-12-26
**Author**: oz
**Task**: Research existing TTS/audio implementations in perito codebase

## Summary

The perito project has extensive audio **processing** and **transcription (STT)** infrastructure, but **no existing TTS (Text-to-Speech) implementations**. There are no references to XTTS, Coqui, or any other TTS library in the codebase.

## Existing Audio Infrastructure

### 1. Speech-to-Text (STT) Pipeline

The project uses a multi-provider STT system with fallback logic:

#### Providers (Priority Order)
| Provider | Model | Use Case |
|----------|-------|----------|
| Groq | whisper-large-v3-turbo | Primary - Fast, accurate Spanish |
| Deepgram | nova-3 | Portal fallback |
| OpenAI | whisper-1 | API fallback |
| Gemini | Flash | Vision-based fallback |

#### Implementation Locations
- **Cotizador API**: `dev/services/cotizador-api/cotizador_api.py:77-97`
  - Provides `/api/transcribe` endpoint
  - Uses Groq Whisper primarily
  - OpenAI and Gemini as fallbacks

- **Portal API**: `mi-af-portal/src/app/api/transcribe/route.ts`
  - Groq → Deepgram fallback chain
  - Handles webm/opus audio from browser

- **Diarization Script**: `dev/scripts/diarize_audio.py`
  - Uses Deepgram Nova-2 with speaker labels
  - Spanish language support

### 2. Audio Recording (Browser)

The portal has sophisticated browser-based audio recording:

#### `mi-af-portal/src/hooks/use-audio-recording.ts`
- MediaRecorder wrapper
- Format: webm/opus @ 16kHz mono
- Auto-chunking at 2 minutes
- IndexedDB persistence for offline resilience
- Duration tracking

#### `mi-af-portal/src/lib/audioStorage.ts`
- IndexedDB storage for audio chunks
- Session management
- Chunk combining logic

### 3. Audio Processing (FFmpeg)

The cotizador API has detailed FFmpeg audio processing:

```python
AUDIO_CONFIG = {
    "codec": "libopus",
    "format": "ogg",
    "bitrate_kbps": 16,
    "sample_rate": 16000,
    "mono": True,
    "highpass_hz": 180,  # Noise reduction
    "compressor": {
        "threshold": "-20.3dB",
        "ratio": 20,
        "attack": 20,
        "release": 500,
        "makeup": 12,
    },
    "max_file_size_mb": 24,
    "chunk_duration_sec": 300,
}
```

## Docker/API Patterns

### Service Architecture

All services follow a consistent pattern:

1. **Dockerfile**: Python 3.11 slim with FFmpeg
2. **docker-compose.yml**:
   - Uses external `af_default` network
   - Mounts `/opt/clients/af/.env` for credentials
   - Mounts volumes for file storage
3. **Health checks**: Built into Dockerfile
4. **Port mapping**: Internal 8000 → External 8001

### Example: Cotizador API

```yaml
# dev/services/cotizador-api/docker-compose.yml
services:
  cotizador-api:
    build: .
    container_name: cotizador-api
    restart: unless-stopped
    env_file:
      - /opt/clients/af/.env
    ports:
      - "8001:8000"
    volumes:
      - /opt/clients/af/local_files/uploads:/app/uploads
      - /opt/clients/af/local_files/templates:/app/templates
    networks:
      - af_default

networks:
  af_default:
    external: true
```

### VPS Infrastructure

```
/opt/clients/af/
├── .env                        # API keys (OPENROUTER, GROQ, etc.)
├── docker-compose.yml          # Main stack (n8n, postgres, gotenberg)
├── services/
│   └── cotizador-api/          # Quote API (port 8001)
└── local_files/
    ├── uploads/                # CDN-mounted storage
    └── templates/              # PDF templates
```

### Dependencies Pattern

```txt
# dev/services/cotizador-api/requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
requests==2.31.0
pydantic==2.6.0
python-multipart==0.0.9
httpx>=0.25.0
psycopg2-binary==2.9.9
jinja2>=3.0.0
```

## Recommendations for Chatterbox TTS Integration

### Deployment Approach

Based on existing patterns, a Chatterbox TTS service should:

1. **New service directory**: `dev/services/chatterbox-tts/`
2. **Same Dockerfile pattern**: Python 3.11 + any required system deps
3. **Port**: 8002 (next available)
4. **Network**: Join `af_default` for internal communication
5. **Storage**: Mount `/app/output` to HDD CDN path for audio files

### Suggested API Design

```python
# Endpoints (matching existing patterns)
POST /api/synthesize    # Generate TTS audio
GET  /health            # Health check

# Request format
{
    "text": "Hola, bienvenido a AF High Definition",
    "voice": "default",      # or voice clone reference
    "language": "es-MX",
    "output_format": "ogg"   # or wav, mp3
}

# Response
{
    "audio_url": "https://hdd.automatic.picturelle.com/af/tts/...",
    "duration_sec": 3.5,
    "model": "chatterbox"
}
```

### Environment Variables Needed

Based on project patterns, add to `/opt/clients/af/.env`:
```bash
# Chatterbox TTS (if using API)
CHATTERBOX_API_KEY=xxx
CHATTERBOX_API_URL=http://chatterbox-tts:8000
```

### Integration Points

1. **n8n workflow**: HTTP Request node to `http://chatterbox-tts:8000/api/synthesize`
2. **WhatsApp delivery**: Use Kommo/WhatsApp audio message API
3. **Staff portal**: Add voice preview to HITL review

## Files Examined

| File | Purpose | Relevant Patterns |
|------|---------|-------------------|
| `dev/scripts/diarize_audio.py` | Deepgram STT | API pattern, audio handling |
| `mi-af-portal/src/hooks/use-audio-recording.ts` | Browser recording | Audio format, chunking |
| `mi-af-portal/src/lib/audioStorage.ts` | IndexedDB storage | Chunk persistence |
| `mi-af-portal/src/app/api/transcribe/route.ts` | Portal STT API | Multi-provider fallback |
| `dev/services/cotizador-api/cotizador_api.py` | Main API | FFmpeg, transcription |
| `dev/services/cotizador-api/docker-compose.yml` | Docker config | Service pattern |
| `dev/services/cotizador-api/Dockerfile` | Container | Build pattern |
| `dev/services/cotizador-api/requirements.txt` | Python deps | Dependency pattern |
| `dev/vps-config/docker-compose.yml` | VPS stack | Network, volumes |

## No Existing TTS

Confirmed: **No TTS implementations found**
- No XTTS, Coqui, Chatterbox, or similar
- No ComfyUI workflows or configs
- No voice synthesis code

The project is ready for TTS integration following the established patterns.
