---
author: oz
model: claude-opus-4-5
date: 2025-12-28
task: TTS comparison research outline
---

# Qwen3-TTS vs Chatterbox TTS Comparison - Outline

## 1. Executive Summary
- Purpose of comparison
- Quick recommendation matrix by use case
- Key differentiators

## 2. Model Overview

### 2.1 Qwen3-TTS Family
- Qwen3-TTS-Flash (standard TTS)
- Qwen3-TTS-VC-Flash (voice cloning)
- Qwen3-TTS-VD-Flash (voice design)
- Qwen3-Omni (multimodal with TTS)

### 2.2 Chatterbox Family
- Chatterbox Original (English, 500M params)
- Chatterbox-Turbo (English, 350M params)
- Chatterbox Multilingual (23 languages, 500M params)

## 3. Voice Cloning Comparison

### 3.1 Qwen3-TTS-VC
- Reference audio: 3+ seconds (10-20s recommended)
- 10 language output support
- API-only (not open-source weights)
- 15% lower WER than competitors

### 3.2 Chatterbox
- Reference audio: ~5-10 seconds
- Zero-shot cloning
- Open-source (MIT license)
- 63.75% preference over ElevenLabs

## 4. Language Support

### 4.1 Qwen3-TTS
- 10 major languages
- 9 Chinese dialects
- Strong multilingual performance

### 4.2 Chatterbox
- Original: English only
- Multilingual: 23 languages
- English quality highest

## 5. Artistic Controls

### 5.1 Qwen3-TTS
- Voice Design: Create voices from text descriptions
- 49+ preset voices with distinct personalities
- Prosody control (natural pacing)
- Emotion/tone via voice selection

### 5.2 Chatterbox
- CFG (Classifier-Free Guidance): 0.0-1.0
- Exaggeration parameter: Emotion intensity
- Temperature: Creativity/variation
- Paralinguistic tags (Turbo): [cough], [laugh]

## 6. Technical Specifications

### 6.1 Model Sizes
| Model | Parameters |
|-------|------------|
| Chatterbox Original | 500M |
| Chatterbox Turbo | 350M |
| Chatterbox Multilingual | 500M |
| Qwen3-TTS | Not disclosed (API) |
| Qwen3-Omni | 30B (MoE) |

### 6.2 VRAM Requirements
| Model | VRAM |
|-------|------|
| Chatterbox | 8GB min, 16GB recommended |
| Chatterbox Turbo | Lower than 500M models |
| Qwen3-TTS | N/A (API-only) |

### 6.3 Inference Speed
| Model | Speed |
|-------|-------|
| Chatterbox | Sub-300ms latency |
| Chatterbox vLLM | 4-10x speedup |
| Qwen3-TTS | Sub-200ms (commercial) |

## 7. Deployment Options

### 7.1 Qwen3-TTS
- Alibaba Cloud API (DashScope)
- Hugging Face demo (no local weights)
- Billing per character/voice creation

### 7.2 Chatterbox
- Local deployment (GPU/CPU)
- Docker containers
- ComfyUI integration
- OpenAI-compatible API servers
- Hugging Face Spaces

## 8. Unique Capabilities

### 8.1 Qwen3-TTS Unique
- Voice Design from text descriptions
- Dialect support (Chinese regional)
- Lower WER in multilingual tests
- Integrated with Qwen3-Omni multimodal

### 8.2 Chatterbox Unique
- Open-source weights (MIT)
- Perth watermarking
- CFG-based expressiveness control
- Paralinguistic tags (Turbo)
- Self-hostable

## 9. Use Case Recommendations

### When to use Qwen3-TTS
- Need Chinese dialect support
- Want voice design from descriptions
- Prefer API simplicity
- Need lowest WER

### When to use Chatterbox Original
- English-only projects
- Maximum expressive control (CFG)
- Self-hosting required
- Open-source requirement

### When to use Chatterbox Multilingual
- Multi-language projects
- Self-hosting with many languages
- Open-source requirement

## 10. Comparison Table

| Feature | Qwen3-TTS | Chatterbox | Chatterbox Multi |
|---------|-----------|------------|------------------|
| Voice Cloning | Yes (3s) | Yes (5s) | Yes (5s) |
| Voice Design | Yes | No | No |
| Languages | 10+9 dialects | English | 23 |
| Open Source | No | Yes (MIT) | Yes (MIT) |
| Self-Host | No | Yes | Yes |
| CFG Control | No | Yes | Yes |
| VRAM | N/A | 8-16GB | 8-16GB |
| Latency | <200ms | <300ms | <300ms |

## 11. Conclusion
- Summary of findings
- Final recommendations by use case
