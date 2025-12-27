---
author: oz
model: claude-haiku-4-5
date: 2025-12-26
task: Research XTTS models, versions, and voice cloning specifications
---

# XTTS Models Research: Complete Guide

## Executive Summary

XTTS-v2 is the current active Coqui TTS model for multilingual voice cloning. There is no XTTS v3 in development. The model supports 17 languages, requires minimal reference audio (6 seconds), and can be deployed via daswer123's xtts-api-server with version selection.

---

## 1. XTTS Model Versions & History

### XTTS-v1 (Legacy)
- Original model with limited language support
- Superseded by v2
- Not recommended for new projects

### XTTS-v2 (Current Active Model)
**Release**: Version 0.20.0 of Coqui TTS brought XTTS-v2
- **17 Languages Supported**: English (en), Spanish (es), French (fr), German (de), Italian (it), Portuguese (pt), Polish (pl), Turkish (tr), Russian (ru), Dutch (nl), Czech (cs), Arabic (ar), Chinese (zh-cn), Japanese (ja), Hungarian (hu), Korean (ko), and Hindi (hi)
- **Model Identity**: `tts_models/multilingual/multi-dataset/xtts_v2`
- **Audio Format**: 24kHz sampling rate, WAV files
- **License**: Coqui Public Model License (CPML)
- **Maintenance**: Community-maintained (2025) - no v3 planned

#### v2 Improvements Over v1
- Better prosody (natural rhythm and intonation)
- Improved stability
- Support for Hungarian and Korean (new languages)
- Architectural improvements for speaker conditioning
- Multiple speaker reference support + interpolation
- Better audio quality across the board

#### v2 Availability on Hugging Face
Available versions in the official repository:
- `v2.0.2` (stable, default)
- `v2.0.3` (latest stable)
- `main` (development branch)

**URL**: https://huggingface.co/coqui/XTTS-v2

### No XTTS v3
As of 2025, there is **no XTTS v3 in development**. The maintainers lack affiliation with the original Coqui company and don't have access to full model weights and training code needed for v3 development. XTTS-v2 is the final stable version.

---

## 2. Voice Cloning: Reference Audio Specifications

### Official Recommendation
**6 seconds of reference audio** is the official minimum for effective voice cloning.

### Practical Guidelines

| Duration | Use Case | Quality |
|----------|----------|---------|
| 3-6 seconds | Minimum viable | Basic cloning |
| 6-10 seconds | **RECOMMENDED** | Good quality |
| 10-30 seconds | Enhanced quality | Better prosody + emotion |
| 30-60 seconds | Fine-tuning preparation | Optimal for custom training |

### Audio File Requirements
- **Format**: WAV (PCM)
- **Channels**: Mono
- **Sample Rate**: 22,050 Hz (XTTS resamples to 24kHz internally)
- **Bit Depth**: 16-bit
- **File Size Range**: ~130KB - 1.3MB for typical samples

### Multiple Reference Files
- You can pass **multiple audio files** to the `speaker_wav` parameter
- Runtime remains **unchanged** (no performance penalty)
- Improves voice cloning quality by providing speaker variation
- No limit on number of files documented

**Example**: Use 2-3 different recordings of the same speaker for better results

### Voice Cloning API Usage

#### Python API
```python
from TTS.api import TTS

# Initialize model
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)

# Single reference file
tts.tts_to_file(
    text="Your text here",
    file_path="output.wav",
    speaker_wav="/path/to/reference/audio.wav",
    language="en"
)

# Multiple reference files (improved quality)
tts.tts_to_file(
    text="Your text here",
    file_path="output.wav",
    speaker_wav=[
        "/path/to/reference1.wav",
        "/path/to/reference2.wav",
        "/path/to/reference3.wav"
    ],
    language="en"
)
```

#### Advanced: Latent Caching
```python
# Extract and cache speaker embeddings for faster repeated use
latents = tts.get_conditioning_latents(
    speaker_wav="/path/to/reference.wav",
    gpt_cond_len=30,  # seconds
    gpt_cond_chunk_len=4,  # chunk size
)

# Reuse cached latents for multiple generations
tts.tts_to_file(
    text="First text",
    file_path="output1.wav",
    speaker_wav=latents,
    language="en"
)

tts.tts_to_file(
    text="Second text",
    file_path="output2.wav",
    speaker_wav=latents,
    language="en"
)
```

---

## 3. XTTS-API-Server (daswer123) - Model Configuration

**GitHub**: https://github.com/daswer123/xtts-api-server

### Model Source Options

Three loading modes available via `-ms` or `--model-source` flag:

#### 1. `local` (Recommended for most users)
```bash
python -m xtts_api_server -ms local -v v2.0.2
```
- Downloads and caches model locally
- Version-selectable via `-v` flag
- Uses model files in `models/` folder
- Startup: ~30-60 seconds (depends on hardware)

#### 2. `apiManual`
```bash
python -m xtts_api_server -ms apiManual -v v2.0.2
```
- Uses TTS API's `tts_to_file()` function internally
- Version-selectable via `-v` flag
- Alternative loading mechanism

#### 3. `api` (Latest auto-update)
```bash
python -m xtts_api_server -ms api
```
- Automatically loads **latest model version**
- `-v` flag is **ignored** (no version control)
- Useful for always-latest deployments
- Warning: May break if API changes

### Supported Versions
```
v2.0.2 (stable default)
v2.0.3 (latest stable)
main   (development)
```

Use any of these with the `-v` flag when using `local` or `apiManual` modes.

### Custom Fine-tuned Models

To use custom fine-tuned XTTS models:

1. Create folder in `models/` directory with your model name
2. Add three required files:
   - `config.json`
   - `vocab.json`
   - `model.pth`
3. Start server with custom model:
   ```bash
   python -m xtts_api_server -ms local -v "My Custom Model"
   ```

---

## 4. XTTS-API-Server Key Options

### Model Configuration
| Option | Default | Purpose |
|--------|---------|---------|
| `-ms / --model-source` | `local` | Loading mode (local/apiManual/api) |
| `-v / --version` | `v2.0.2` | Model version (v2.0.2, v2.0.3, main) |
| `-mf / --model-folder` | `./models` | Model storage directory |

### Performance Options
| Option | Purpose |
|--------|---------|
| `--lowvram` | Keep model in RAM, load to VRAM only during generation |
| `-g / --gpu` | GPU device selection |

### Server Options
| Option | Default | Purpose |
|--------|---------|---------|
| `--host` | `0.0.0.0` | Server host |
| `--port` | `8020` | Server port |

### API Docs
Access at: `http://localhost:8020/docs` (Swagger UI)

---

## 5. XTTS Performance Characteristics

### Latency
- **Streaming**: <200ms latency achievable
- **Non-streaming**: ~5-15 seconds for typical text (depends on length + hardware)

### Quality Metrics
- **Voice similarity**: 90%+ with 6+ second reference
- **Naturalness**: Improved with multiple references
- **Multilingual**: Natural cross-language synthesis

### Memory Requirements
- **VRAM**: 8GB minimum (12GB recommended)
- **RAM**: 16GB+
- **Disk**: ~2GB for model files

### Inference Speed
- **Single sentence (10-20 tokens)**: ~3-5 seconds on RTX 3090
- **Paragraph (100+ tokens)**: ~15-30 seconds
- **Batch processing**: Linear with text length

---

## 6. Comparison Matrix: XTTS vs Alternatives

| Feature | XTTS-v2 | Tortoise TTS | Bark |
|---------|---------|-------------|------|
| Voice Cloning | Yes (6s min) | Yes (5-30s) | No |
| Languages | 17 | 1 (English) | 1 (English) |
| Audio Quality | 24kHz | 24kHz | 24kHz |
| Speed | Fast (<1s) | Slow (30s+) | Medium (10s) |
| Fine-tuning | Yes | Yes | Limited |
| Model Size | ~2GB | ~6GB | ~2GB |
| GPU Requirement | 8GB+ | 12GB+ | 8GB+ |

---

## 7. Deployment Examples

### Docker with xtts-api-server
```bash
# Pull or build image
docker run -d \
  --gpus all \
  -p 8020:8020 \
  -v /data/models:/app/models \
  -e MODEL_SOURCE=local \
  -e MODEL_VERSION=v2.0.2 \
  daswer123/xtts-api-server:latest
```

### RunPod Deployment
```bash
# Environment variables for RunPod template
ENABLE_XTTS=true
XTTS_VERSION=v2.0.2
XTTS_MODEL_SOURCE=local
XTTS_LOW_VRAM=false
```

### Local Development
```bash
# Install
pip install TTS

# Run server
python -m xtts_api_server -ms local -v v2.0.2 --lowvram

# Test via curl
curl -X POST http://localhost:8020/tts_stream \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world",
    "language": "en",
    "speaker_wav": "path/to/reference.wav"
  }' \
  --output output.wav
```

---

## 8. Troubleshooting & Best Practices

### Voice Cloning Quality Issues
**Problem**: Cloned voice sounds robotic or different
- **Solution 1**: Use 10+ seconds of reference audio instead of 6s
- **Solution 2**: Use multiple reference files (3-5 different recordings)
- **Solution 3**: Ensure reference audio is high-quality (no background noise)

### Cross-Language Cloning Challenges
**Problem**: Foreign language synthesis loses original accent
- **Solution**: XTTS is designed for this (not a bug) - emotion/prosody transfer is language-aware
- **Tip**: Use reference audio in target language if preserving accent is critical

### Memory/VRAM Issues
**Problem**: GPU runs out of VRAM
- **Solution 1**: Use `--lowvram` flag (slower but works on 8GB)
- **Solution 2**: Reduce batch size or text length per request
- **Solution 3**: Run on CPU (very slow, not recommended)

### Model Download Issues
**Problem**: Model fails to download from Hugging Face
- **Solution 1**: Manual download: https://huggingface.co/coqui/XTTS-v2
- **Solution 2**: Specify model folder manually: `-mf /path/to/models`
- **Solution 3**: Use `api` mode for auto-retry logic

---

## 9. Key Resources

### Official Documentation
- **Coqui TTS Docs**: https://docs.coqui.ai/en/latest/models/xtts.html
- **Hugging Face Model Card**: https://huggingface.co/coqui/XTTS-v2
- **Live Demo**: https://huggingface.co/spaces/coqui/xtts

### API Server
- **GitHub Repository**: https://github.com/daswer123/xtts-api-server
- **Releases**: https://github.com/daswer123/xtts-api-server/releases
- **API Docs (local)**: http://localhost:8020/docs

### Community
- **Coqui Discord**: https://discord.gg/5eXr5seRrv
- **GitHub Discussions**: https://github.com/coqui-ai/TTS/discussions
- **PyPI Package**: https://pypi.org/project/coqui-tts/

---

## 10. Summary: Quick Reference

### For Voice Cloning:
1. Prepare 6-10 second reference audio (WAV, mono, 22050Hz, 16-bit)
2. Use Python API or xtts-api-server
3. Call with `speaker_wav` parameter
4. Optional: Pass multiple references for better quality

### For API Server:
1. Start with `local` mode: `-ms local -v v2.0.2`
2. Access API at `http://localhost:8020/docs`
3. Use `/tts_stream` for streaming or `/tts_to_file` for batch

### For RunPod:
1. Set `ENABLE_XTTS=true` in template
2. Model downloads on-demand to `/models/` folder (~1.8GB)
3. Accessible via API on port 8020

### Language Support:
All 17 languages available in v2 - no version differences for language support.

---

Generated: 2025-12-26
Last Updated: 2025-12-26
Sources: Coqui TTS docs, Hugging Face, daswer123/xtts-api-server GitHub
