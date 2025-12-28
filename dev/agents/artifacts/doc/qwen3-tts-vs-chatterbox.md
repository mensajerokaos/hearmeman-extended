---
author: oz
model: claude-opus-4-5
date: 2025-12-28
task: TTS comparison research - Qwen3-TTS vs Chatterbox
sources:
  - https://qwen.ai/blog?id=qwen3-tts-vc-voicedesign
  - https://github.com/resemble-ai/chatterbox
  - https://www.resemble.ai/introducing-chatterbox-multilingual-open-source-tts-for-23-languages/
  - https://www.alibabacloud.com/help/en/model-studio/qwen-tts-voice-cloning
  - https://huggingface.co/ResembleAI/chatterbox
---

# Qwen3-TTS vs Chatterbox TTS: Comprehensive Comparison

## Executive Summary

This document compares three leading TTS systems for voice cloning and expressive speech synthesis:

| System | Best For | Key Strength |
|--------|----------|--------------|
| **Qwen3-TTS** | Voice design, Chinese dialects, API users | Create voices from text descriptions |
| **Chatterbox Original** | English projects, maximum control | CFG/exaggeration controls, open-source |
| **Chatterbox Multilingual** | Multi-language self-hosting | 23 languages, MIT license |

**Quick Recommendation:**
- **Need voice design from text descriptions?** -> Qwen3-TTS-VD
- **Need English with maximum artistic control?** -> Chatterbox Original
- **Need open-source multilingual?** -> Chatterbox Multilingual
- **Need Chinese dialects?** -> Qwen3-TTS
- **Need self-hosting?** -> Chatterbox (any variant)

---

## 1. Model Overview

### 1.1 Qwen3-TTS Family (Alibaba Cloud)

The Qwen3-TTS family is a closed-source, API-based TTS system with three specialized variants:

| Model | Purpose | Availability |
|-------|---------|--------------|
| **Qwen3-TTS-Flash** | Standard TTS with 49+ voices | DashScope API |
| **Qwen3-TTS-VC-Flash** | Voice cloning from 3s audio | DashScope API |
| **Qwen3-TTS-VD-Flash** | Voice design from text | DashScope API |
| **Qwen3-Omni-30B** | Multimodal with TTS | HuggingFace (30B MoE) |

**Key characteristics:**
- Closed weights (no local deployment for TTS-specific models)
- API-based pricing ($0.01 per voice creation, per-character synthesis)
- Parameter counts not publicly disclosed
- 49+ expressive voice presets

### 1.2 Chatterbox Family (Resemble AI)

Chatterbox is an open-source TTS system with multiple variants:

| Model | Parameters | Languages | License |
|-------|------------|-----------|---------|
| **Chatterbox Original** | 500M | English | MIT |
| **Chatterbox-Turbo** | 350M | English | MIT |
| **Chatterbox Multilingual** | 500M | 23 languages | MIT |

**Key characteristics:**
- Fully open-source weights on HuggingFace
- Self-hostable with Docker, ComfyUI, or Python
- Built on 0.5B Llama backbone, CosyVoice architecture
- Trained on 500,000 hours of speech data

---

## 2. Voice Cloning Comparison

### 2.1 Qwen3-TTS-VC-Flash

**Reference Audio Requirements:**
- Minimum: 3 seconds of continuous, clear speech
- Recommended: 10-20 seconds
- Maximum: 60 seconds
- Formats: WAV (16-bit), MP3, M4A
- Sample rate: 24kHz+, mono only
- No background noise, music, or singing

**Quality Metrics:**
- 15% lower Word Error Rate (WER) than ElevenLabs and GPT-4o-Audio
- Strong multilingual preservation of speech patterns
- Natural pacing across 10 output languages

**API Workflow:**
1. Create voice via `qwen-voice-enrollment` model
2. Use cloned voice with `qwen3-tts-vc-realtime-2025-11-27`
3. Voice auto-deletes after 1 year of inactivity

**Limitations:**
- API-only (no local deployment)
- Voice creation costs $0.01 each
- Must use dedicated VC synthesis model
- Cannot mix cloned voices with preset voices

### 2.2 Chatterbox Voice Cloning

**Reference Audio Requirements:**
- Recommended: 5-10 seconds
- Minimum viable: ~3 seconds
- Format: WAV (any standard format)
- Quality: Clear speech, minimal background noise

**Quality Metrics:**
- 63.75% listener preference over ElevenLabs (Podonos blind test)
- Zero-shot cloning (no fine-tuning required)
- Excellent speaker similarity with short samples

**Local Workflow:**
```python
from chatterbox import ChatterboxTurboTTS

model = ChatterboxTurboTTS.from_pretrained(device="cuda")
wav = model.generate(
    text="Hello world",
    audio_prompt_path="reference.wav",
    exaggeration=0.5,
    cfg_weight=0.5
)
```

**Advantages:**
- Fully local processing
- No API costs
- Adjustable parameters (CFG, exaggeration)
- Open-source and auditable

---

## 3. Language Support

### 3.1 Qwen3-TTS Languages

**10 Major Languages:**
- Chinese (Mandarin)
- English
- German
- Italian
- Portuguese
- Spanish
- Japanese
- Korean
- French
- Russian

**9 Chinese Dialects:**
- Mandarin, Cantonese, Hokkien, Sichuanese
- Shaanxi, Wu, Beijing, Tianjin, Nanjing

**Unique strength:** Best-in-class Chinese dialect support for regional applications.

### 3.2 Chatterbox Languages

**Original Version:**
- English only
- Highest quality and expressiveness

**Multilingual Version (23 Languages):**
- Arabic, Danish, German, Greek, English, Spanish
- Finnish, French, Hebrew, Hindi, Italian, Japanese
- Korean, Malay, Dutch, Norwegian, Polish, Portuguese
- Russian, Swedish, Swahili, Turkish, Chinese

**Note:** English produces the most natural results. Other languages may lack some nuance. Reference audio language should match target language for best results.

---

## 4. Artistic Controls

### 4.1 Qwen3-TTS Controls

**Voice Design (VD-Flash):**
The unique feature of Qwen3-TTS is creating voices from text descriptions:

```
"Male, middle-aged, booming baritone - hyper-energetic infomercial
voice with rapid-fire delivery and exaggerated pitch rises"
```

```
"Warm storyteller voice with gentle pacing and calm emotion"
```

This eliminates the need for reference audio when you can describe the desired voice.

**Preset Voices (49+):**
| Voice | Personality |
|-------|-------------|
| Momo | Energetic, playful |
| Vivian | Confident, proud |
| Eldric Sage | Older, wiser |
| Chelsie | Warm, emotional |
| Ryan | Professional, authoritative |

**Prosody:** Natural pacing based on meaning, adaptive speech rate, emotional emphasis.

**Limitations:**
- No CFG-style fine-tuning
- No explicit exaggeration control
- Expressiveness locked to voice selection

### 4.2 Chatterbox Controls

**CFG (Classifier-Free Guidance):**
- Range: 0.0 - 1.0 (default: 0.5)
- Lower values: Slower, clearer, more expressive speech
- Higher values: Stricter adherence to input, faster pacing
- Use case: Balance speaker fidelity vs. text accuracy

**Exaggeration Parameter:**
- Range: 0.0 - 1.0 (default: 0.5)
- Controls emotional intensity
- Higher values: More dramatic, expressive delivery
- Lower values: Subtle, professional tone

**Temperature:**
- Controls creativity/variation
- Higher: More varied outputs
- Lower: More consistent outputs

**Paralinguistic Tags (Turbo only):**
```
"I just can't believe it! [laugh] That's incredible! [cough]"
```
Supported: `[cough]`, `[laugh]`, `[chuckle]`

**Recommended Settings:**
| Use Case | CFG | Exaggeration |
|----------|-----|--------------|
| General purpose | 0.5 | 0.5 |
| Expressive speech | 0.3 | 0.7+ |
| Fast speakers | 0.3 | 0.5 |
| Professional/formal | 0.5 | 0.3 |

---

## 5. Technical Specifications

### 5.1 Model Sizes

| Model | Parameters | Architecture |
|-------|------------|--------------|
| Chatterbox Original | 500M | Llama + CosyVoice |
| Chatterbox-Turbo | 350M | Distilled decoder |
| Chatterbox Multilingual | 500M | Llama + CosyVoice |
| Qwen3-TTS | Not disclosed | Proprietary |
| Qwen3-Omni | 30B (MoE, 3B active) | Thinker-Talker |

### 5.2 VRAM Requirements

| Model | Minimum | Recommended | Notes |
|-------|---------|-------------|-------|
| Chatterbox Original | 4GB | 8GB | Runs comfortably on 8GB |
| Chatterbox-Turbo | 6GB | 8GB | Optimized for lower VRAM |
| Chatterbox Multilingual | 8GB | 16-24GB | For multi-tenant hosting |
| Qwen3-TTS | N/A | N/A | API-only |
| Qwen3-Omni-30B | 70GB | 80GB+ | Full multimodal |

### 5.3 Inference Speed

| Model | Latency | RTF | Notes |
|-------|---------|-----|-------|
| Chatterbox (RTX 4090) | 472ms TTFC | 0.499 | Streaming mode |
| Chatterbox (CUDA) | ~52s/42s audio | 1.2x | Standard GPU |
| Chatterbox (CPU) | ~288s/43s audio | 6.7x | Fallback only |
| Chatterbox + vLLM (3090) | 2.5min/40min audio | 16x faster | Optimized port |
| Qwen3-TTS API | <200ms | N/A | Commercial SLA |
| Qwen3-Omni local | Slow | N/A | MoE overhead |

**RTF (Real-Time Factor):** <1 means faster than real-time generation.

### 5.4 Hardware Compatibility

**Chatterbox:**
- NVIDIA CUDA (primary)
- AMD ROCm
- Apple Silicon MPS
- CPU fallback (slow)
- Supports RTX 5090 / CUDA 12.8

**Qwen3-TTS:**
- API-only (no local hardware)

---

## 6. Deployment Options

### 6.1 Qwen3-TTS Deployment

**Only Option: Alibaba Cloud API**
```python
from dashscope.audio.tts import SpeechSynthesizer

synthesizer = SpeechSynthesizer(
    model="qwen3-tts-flash",
    voice="Chelsie"
)
audio = synthesizer.call(text="Hello world")
```

**Pricing:**
- Voice creation: $0.01 per voice
- Synthesis: Per-character billing
- Free tier: 1,000 voices over 90 days

**Regions:** Beijing, Singapore

### 6.2 Chatterbox Deployment

**Option 1: Python Package**
```bash
pip install chatterbox-tts
```

**Option 2: Docker (OpenAI-compatible)**
```bash
git clone https://github.com/travisvn/chatterbox-tts-api.git
docker compose -f docker/docker-compose.gpu.yml up -d
curl http://localhost:8000/v1/audio/speech
```

**Option 3: ComfyUI**
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/thefader/ComfyUI-Chatterbox
```

**Option 4: Hugging Face Space**
- https://huggingface.co/spaces/ResembleAI/Chatterbox

**Option 5: vLLM (high-performance)**
```bash
git clone https://github.com/randombk/chatterbox-vllm
```

---

## 7. Unique Capabilities

### 7.1 Qwen3-TTS Exclusive Features

1. **Voice Design from Text Descriptions**
   - Create any voice by describing it
   - No reference audio needed
   - Outperforms GPT-4o-mini-tts on role-play benchmarks

2. **Chinese Dialect Support**
   - 9 distinct dialects
   - Regional accent preservation
   - Best-in-class for Chinese applications

3. **Lower WER in Multilingual Tests**
   - 15% fewer errors than competitors
   - Stronger multilingual consistency

4. **Qwen3-Omni Integration**
   - Unified multimodal pipeline
   - Text, audio, image, video understanding
   - Real-time streaming responses

### 7.2 Chatterbox Exclusive Features

1. **Open-Source Weights (MIT License)**
   - Full model weights on HuggingFace
   - Auditable, modifiable, redistributable
   - No API dependencies

2. **CFG-Based Expressiveness Control**
   - Fine-grained control over delivery
   - Unique artistic tuning capability
   - Adapted from diffusion models

3. **Paralinguistic Tags (Turbo)**
   - `[laugh]`, `[cough]`, `[chuckle]`
   - Natural non-speech vocalizations
   - First open-source TTS with this feature

4. **Perth Watermarking**
   - Neural watermark in all generated audio
   - Inaudible but detectable
   - Open-source detector available

5. **Self-Hosting Freedom**
   - No cloud dependency
   - Data privacy
   - Unlimited usage

---

## 8. Use Case Recommendations

### When to Choose Qwen3-TTS

| Scenario | Why Qwen3-TTS |
|----------|---------------|
| **Voice from description** | Only option with Voice Design |
| **Chinese dialects** | Best regional dialect support |
| **API simplicity** | No infrastructure to manage |
| **Lowest WER priority** | 15% fewer errors in tests |
| **Commercial SLA needed** | Enterprise reliability |

### When to Choose Chatterbox Original

| Scenario | Why Chatterbox |
|----------|----------------|
| **English-only projects** | Highest quality English output |
| **Maximum artistic control** | CFG + exaggeration tuning |
| **Self-hosting required** | Fully local deployment |
| **Open-source requirement** | MIT license |
| **Cost-sensitive** | No per-use fees |

### When to Choose Chatterbox Multilingual

| Scenario | Why Multilingual |
|----------|------------------|
| **Multi-language projects** | 23 languages in one model |
| **Self-hosted localization** | No API per-language costs |
| **Open-source + global** | MIT + wide language coverage |

### When to Choose Chatterbox-Turbo

| Scenario | Why Turbo |
|----------|-----------|
| **Lower VRAM available** | 350M vs 500M |
| **Need paralinguistic tags** | [laugh], [cough] support |
| **Real-time applications** | Single-step decoder |

---

## 9. Comprehensive Comparison Table

| Feature | Qwen3-TTS | Chatterbox | Chatterbox Multi |
|---------|-----------|------------|------------------|
| **Voice Cloning** | Yes (3-20s) | Yes (5-10s) | Yes (5-10s) |
| **Voice Design** | Yes | No | No |
| **Languages** | 10 + 9 dialects | English | 23 |
| **Open Source** | No | Yes (MIT) | Yes (MIT) |
| **Self-Host** | No | Yes | Yes |
| **CFG Control** | No | Yes (0-1) | Yes (0-1) |
| **Exaggeration** | Via voice | Yes (0-1) | Yes (0-1) |
| **Parameters** | Undisclosed | 500M | 500M |
| **VRAM** | N/A (API) | 8-16GB | 8-16GB |
| **Latency** | <200ms | <300ms | <300ms |
| **Watermarking** | Unknown | Perth | Perth |
| **ComfyUI** | No | Yes | Yes |
| **Docker** | No | Yes | Yes |
| **Pricing** | Per-use | Free | Free |

---

## 10. Conclusion

### Summary of Findings

**Qwen3-TTS** excels at:
- Creating voices from text descriptions (unique capability)
- Chinese dialect support (unmatched)
- API simplicity with strong multilingual WER

**Chatterbox** excels at:
- Open-source self-hosting (MIT license)
- Artistic control via CFG and exaggeration
- Cost-effective high-volume usage

### Final Recommendations

1. **For maximum flexibility and control**: Use Chatterbox Original (English) or Multilingual (23 languages). The CFG and exaggeration parameters provide unparalleled artistic control.

2. **For voice design from descriptions**: Use Qwen3-TTS-VD-Flash. No other system offers this capability.

3. **For Chinese applications**: Use Qwen3-TTS. The dialect support is unmatched.

4. **For production self-hosting**: Use Chatterbox with Docker or vLLM. The 4-10x speedup from vLLM makes it production-ready.

5. **For ComfyUI workflows**: Use Chatterbox. Full integration with custom nodes available.

6. **For cost-sensitive projects**: Use Chatterbox. Zero per-use fees after hardware investment.

---

## Sources

- [Qwen3-TTS Voice Cloning & Design Blog](https://qwen.ai/blog?id=qwen3-tts-vc-voicedesign)
- [Qwen TTS Voice Cloning API Reference](https://www.alibabacloud.com/help/en/model-studio/qwen-tts-voice-cloning)
- [Chatterbox GitHub Repository](https://github.com/resemble-ai/chatterbox)
- [Chatterbox Multilingual Announcement](https://www.resemble.ai/introducing-chatterbox-multilingual-open-source-tts-for-23-languages/)
- [Qwen3-TTS-Flash Review](https://www.analyticsvidhya.com/blog/2025/12/qwen3-tts-flash-review/)
- [Chatterbox HuggingFace](https://huggingface.co/ResembleAI/chatterbox)
- [Qwen3-Omni GitHub](https://github.com/QwenLM/Qwen3-Omni)
- [Chatterbox TTS Server](https://github.com/devnen/Chatterbox-TTS-Server)
