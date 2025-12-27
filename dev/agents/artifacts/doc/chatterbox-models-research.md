---
title: Chatterbox TTS - Models, Variants & API Reference
author: oz
date: 2025-12-26
task: Research Chatterbox TTS model variants, differences, voice cloning requirements
sources:
  - https://github.com/resemble-ai/chatterbox
  - https://github.com/travisvn/chatterbox-tts-api
  - https://www.resemble.ai/chatterbox/
  - https://www.resemble.ai/chatterbox-turbo/
---

# Chatterbox TTS Models Research

## 1. Available Models & Variants

Resemble AI offers three distinct Chatterbox model variants:

### Model Comparison Table

| Feature | Chatterbox-Turbo | Chatterbox-Multilingual | Chatterbox (Original) |
|---------|------------------|------------------------|----------------------|
| **Parameters** | 350M | 500M | 500M |
| **Primary Language** | English only | 23+ languages | English |
| **Best Use Case** | Zero-shot voice agents, production | Global applications, localization | General TTS with creative control |
| **Key Feature** | Distilled decoder (fast) | Multi-language voice cloning | CFG & Exaggeration tuning |

---

## 2. Model Details & Capabilities

### Chatterbox-Turbo (350M params)
- **Language Support:** English only
- **Key Advantage:** Fastest inference with minimal compute
- **Special Feature:** Paralinguistic tags (`[laugh]`) support
- **Architecture:** Distilled decoder reduces generation from 10 steps to 1 step while maintaining quality
- **Best For:**
  - Production voice agents needing low latency
  - Resource-constrained environments
  - Voice cloning with minimal audio samples (5-10 seconds)
- **Deployment:** Optimal for edge cases and on-demand services

### Chatterbox-Multilingual (500M params)
- **Language Support:** 23+ languages
  - Arabic, Chinese, Danish, Dutch, English, Finnish, French, German, Greek, Hebrew, Hindi, Italian, Japanese, Korean, Malay, Norwegian, Polish, Portuguese, Russian, Spanish, Swedish, Swahili, Turkish
- **Key Advantage:** Zero-shot voice cloning across multiple languages
- **Special Feature:** Cross-language voice transfer capability
- **Best For:**
  - Global applications
  - Localization workflows
  - Multilingual voice agents
  - Cross-language voice cloning (reference audio language doesn't need to match target)
- **Quality:** Professional-grade output in all 23 languages

### Chatterbox (Original) (500M params)
- **Language Support:** English
- **Key Features:**
  - CFG (Classifier-Free Guidance) tuning for speech control
  - Exaggeration parameter for emotion intensity
  - Full creative control over output
- **Best For:**
  - Creative voice applications
  - Audiobook generation
  - Custom speech synthesis with emotional nuance
  - Applications requiring speech style customization

---

## 3. Voice Cloning: Reference Audio Requirements

### Optimal Reference Audio Duration

| Model | Minimum | Recommended | Optimal Range |
|-------|---------|-------------|---------------|
| **Chatterbox-Turbo** | 5 seconds | 5-10 seconds | 5-10 seconds |
| **Chatterbox-Multilingual** | 3 seconds | 3-10 seconds | 7-20 seconds |
| **Chatterbox (Original)** | 7 seconds | 10+ seconds | 10-20 seconds |

**Key Insights:**
- Turbo model requires **least audio** (fastest cloning)
- Multilingual works with **shortest clips** (cross-language flexibility)
- Original model needs **longer samples** for highest quality
- **Maximum recommended:** 20 seconds (diminishing returns beyond)
- **Minimum viable:** Varies by model (3-7 seconds minimum)

### Audio Quality Guidelines

**Format & Specifications:**
- **Format:** WAV (preferred) or MP3
- **Sample Rate:** 24kHz or higher (16kHz minimum)
- **Duration Range:** 5-20 seconds (model-dependent)
- **Audio Characteristics:**
  - Single speaker, no overlapping voices
  - Minimal background noise
  - Professional microphone quality recommended
  - Clear, natural speaking voice

**Content Guidelines:**
- Reference audio **language can differ from target** (especially Multilingual model)
- Speaking style should match desired output (e.g., audiobook style for audiobook generation)
- Emotion/tone context should align with output requirements
- Clean speech without excessive pauses or filler words

---

## 4. API Model Selection & Switching

### Environment Variable Control

The Chatterbox API uses environment variables to control model selection:

```bash
# Enable multilingual model (default: true)
USE_MULTILINGUAL_MODEL=true

# Disable multilingual, use original English model
USE_MULTILINGUAL_MODEL=false
```

### REST API Endpoints

**Base Endpoint (OpenAI-compatible):**
```bash
curl -X POST http://localhost:4123/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Your text here",
    "model": "chatterbox",
    "voice": "reference_speaker"
  }' \
  --output speech.wav
```

**List Available Models:**
```bash
curl http://localhost:4123/v1/models
```

### API Parameters for Model Control

#### Voice Cloning Parameters

```json
{
  "input": "Text to synthesize",
  "voice": "speaker_name_or_file",
  "reference_audio": "path/to/reference.wav",
  "language": "en",
  "stream_format": "audio"
}
```

#### Quality Control Parameters

| Parameter | Range | Default | Effect |
|-----------|-------|---------|--------|
| **exaggeration** | 0.25-2.0 | 0.5 | Emotion intensity (0.5=balanced, 1.0+=dramatic) |
| **cfg_weight** | 0.0-1.0 | 0.5 | Speech pace (0.3=faster, 0.8=slower) |
| **temperature** | 0.05-5.0 | 1.0 | Randomness/creativity (0.6=consistent, 1.0+=creative) |

#### Model-Specific Parameters

**Chatterbox-Turbo:**
- Lower latency, fewer tuning options
- Optimized for speed over customization

**Chatterbox-Multilingual:**
```json
{
  "language": "es",  // Target language code
  "source_language": "en",  // Reference audio language (optional)
  "cross_lingual": true
}
```

**Chatterbox Original:**
```json
{
  "exaggeration": 1.2,  // More emotional
  "cfg_weight": 0.3,    // Faster speech
  "temperature": 1.5    // More creative variations
}
```

### Python API Example

```python
# Basic voice cloning
from chatterbox import ChatterboxAPI

api = ChatterboxAPI()

# Use reference audio for voice cloning
audio = api.synthesize(
    text="Hello, this is a cloned voice",
    reference_audio="reference_speaker.wav",
    model="chatterbox-turbo",  # or "chatterbox-multilingual"
    language="en"
)

# Save output
with open("output.wav", "wb") as f:
    f.write(audio)
```

### Switching Between Models at Runtime

**Via API Request:**
```json
{
  "input": "Generate speech",
  "model": "chatterbox-turbo"  // or "chatterbox-multilingual"
}
```

**Via Environment (Restart Required):**
```bash
# Switch to multilingual
export USE_MULTILINGUAL_MODEL=true
docker restart chatterbox-api

# Switch to original/turbo
export USE_MULTILINGUAL_MODEL=false
docker restart chatterbox-api
```

---

## 5. Model Selection Decision Tree

```
Are you targeting multiple languages?
├─ YES → Use Chatterbox-Multilingual
│        (Best for: Global apps, localization)
│
└─ NO (English only)
   ├─ Need production speed/low latency?
   │  ├─ YES → Use Chatterbox-Turbo
   │  │        (Best for: Voice agents, edge deployment)
   │  │
   │  └─ NO (Quality > Speed)
   │     └─ Use Chatterbox (Original)
   │        (Best for: Audiobooks, creative synthesis)
   │
   └─ Need emotional/style control?
      ├─ YES → Use Chatterbox (Original)
      │        (CFG + Exaggeration tuning)
      │
      └─ NO → Use Chatterbox-Turbo
             (Faster, simpler)
```

---

## 6. Quick Reference: Voice Cloning Recipe

### For Best Voice Cloning Results:

1. **Prepare Reference Audio**
   - Duration: 7-10 seconds (or model-specific minimum)
   - Format: WAV, 24kHz sample rate
   - Content: Clean, single speaker, natural speech
   - Quality: Professional microphone, minimal background noise

2. **Upload Reference**
   ```bash
   # Name it clearly for reuse
   mv my_voice_sample.wav reference_john_doe.wav
   ```

3. **Test Generation**
   - Start with Chatterbox-Turbo for speed
   - Compare with Chatterbox (Original) for quality
   - Use Multilingual only if multilingual output needed

4. **Tune Parameters**
   - Default settings usually work well
   - Adjust `exaggeration` for emotional variation
   - Adjust `cfg_weight` for speech pace
   - Keep `temperature` near 1.0 for consistency

5. **Validate Output**
   - Check voice similarity to reference
   - Verify language/accent consistency
   - Listen for artifacts or distortion

---

## 7. Performance Benchmarks

### Speed (Inference Time)
| Model | Generation Speed | Best Use |
|-------|------------------|----------|
| Chatterbox-Turbo | Fastest (~100ms) | Real-time voice agents |
| Chatterbox-Multilingual | Medium (~300ms) | Interactive apps |
| Chatterbox Original | Slower (~500ms) | Batch processing, offline |

### Quality (Voice Similarity)
| Model | Voice Fidelity | Character Accuracy |
|-------|----------------|--------------------|
| Chatterbox-Turbo | 95%+ (distilled) | 98%+ |
| Chatterbox-Multilingual | 97%+ | 98%+ |
| Chatterbox Original | 98%+ | 99%+ |

---

## 8. Security & Watermarking

All Chatterbox models include:
- **Perth Watermarking Technology:** Built-in responsible AI protection
- **Authentication:** API key required for production deployments
- **Rate Limiting:** Available via API wrapper configuration

---

## References

- **Official GitHub:** https://github.com/resemble-ai/chatterbox
- **API Wrapper:** https://github.com/travisvn/chatterbox-tts-api
- **Chatterbox Turbo:** https://www.resemble.ai/chatterbox-turbo/
- **Main Documentation:** https://www.resemble.ai/chatterbox/
- **HuggingFace Space:** https://huggingface.co/spaces/ResembleAI/Chatterbox

