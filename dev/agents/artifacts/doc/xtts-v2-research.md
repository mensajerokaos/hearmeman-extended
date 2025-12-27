# XTTS v2 & Modern TTS Integration Research (2025)

## 1. Executive Summary
**Status:** Completed
**Verdict:** XTTS v2 remains a reliable workhorse in 2025, but **F5-TTS** has emerged as a superior alternative for ComfyUI workflows due to its non-autoregressive architecture (faster generation) and robust zero-shot cloning capabilities.

For ComfyUI users, direct custom nodes are available and compatible with modern `transformers` libraries. For standalone services, Coqui's official Docker image provides a production-ready API and Web UI.

## 2. ComfyUI Integration Options

### A. XTTS v2 (Standard Choice)
*   **Recommended Node:** `AIFSH/ComfyUI-XTTS`
*   **Repository:** [https://github.com/AIFSH/ComfyUI-XTTS](https://github.com/AIFSH/ComfyUI-XTTS)
*   **Compatibility:**
    *   Verified with `transformers >= 4.51` (specifically `4.51.3` and `4.55.4`).
    *   Supports the standard 17 languages (English, Spanish, French, German, Italian, etc.).
*   **Pros:** Proven quality, stable, excellent fine-tuning ecosystem.
*   **Cons:** Slower than newer diffusion/flow-matching models.

### B. F5-TTS (Recommended for 2025)
*   **Recommended Node:** `ComfyUI-F5-TTS`
*   **Key Features:**
    *   **Zero-Shot Cloning:** Instant voice cloning with ~10s reference audio.
    *   **Speed:** Fully non-autoregressive (Flow Matching), significantly faster inference (RTF ~0.15).
    *   **Architecture:** Diffusion Transformer (DiT) based.
*   **Pros:** State-of-the-art speed/quality ratio, better for real-time or high-volume generation.

### C. CosyVoice (Strong Alternative)
*   **Recommended Node:** `SshunWang/ComfyUI_CosyVoice` or `filliptm/ComfyUI_FL-CosyVoice3`
*   **Features:** Supports CosyVoice 1.0/2.0/3.0, excellent for instruction following and emotion control.

## 3. Docker Service Integration (Standalone)

For users preferring a standalone API service (microservice architecture) over a ComfyUI node.

### Recommended Image
*   **Image:** `ghcr.io/coqui-ai/tts` (Official) or `lojikng/docker-tts-api-ui` (Community optimized with UI)
*   **Features:** Includes XTTS v2 model, REST API, and a Gradio-based Web UI.
*   **Hardware:** Supports NVIDIA GPUs (CUDA).

### Docker Compose Configuration
Save this as `docker-compose.yml` to launch a local TTS service:

```yaml
version: '3.8'
services:
  xtts-service:
    image: lojikng/docker-tts-api-ui:latest
    container_name: xtts-api-ui
    ports:
      - "2902:2902"
    volumes:
      - ./models:/app/models
      - ./voices:/app/voices  # Drop .wav files here for cloning
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      # Agree to Coqui terms if required by specific image version
      - COQUI_TOS_AGREED=1 
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
```

**Setup Steps:**
1.  Create folders: `mkdir models voices`
2.  (Optional) Download XTTS v2 models manually to `./models` or let the container download on first run.
3.  Run: `docker compose up -d`
4.  Access UI: `http://localhost:2902`
5.  API Endpoint: `http://localhost:2902/tts`

## 4. Alternative TTS Models Summary

| Model | Architecture | Best Use Case | ComfyUI Support |
| :--- | :--- | :--- | :--- |
| **XTTS v2** | GPT + HiFi-GAN | Narrative, Long-form, Stability | ✅ Excellent |
| **F5-TTS** | Flow Matching (DiT) | Speed, Instant Cloning, Real-time | ✅ Excellent |
| **CosyVoice** | LLM/Flow | Instruction following, Emotion | ✅ Good |
| **Tortoise** | Autoregressive + Diffusion | Maximum Quality (Slow) | ✅ Good |
| **VoiceVox** | Variational | Japanese Anime/Character Voices | ⚠️ Limited/Manual |

## 5. Key Findings & Recommendations

1.  **Transformers Compatibility:** The fear of `transformers >= 4.51` breaking XTTS nodes is largely mitigated by active maintenance in repos like `AIFSH/ComfyUI-XTTS`.
2.  **Web UI:** The standalone Docker image provides a sufficient Web UI for testing and simple generation.
3.  **Performance:** F5-TTS is significantly more efficient than XTTS v2 for similar quality, making it the top recommendation for new 2025 pipelines.

### Top 3 Recommended Implementation Paths

1.  **The "Modern" Path (F5-TTS):**
    *   Install `ComfyUI-F5-TTS` custom node.
    *   Use for rapid voice cloning and general TTS within ComfyUI workflows.

2.  **The "Stable" Path (XTTS v2 Node):**
    *   Install `AIFSH/ComfyUI-XTTS`.
    *   Best if you rely on specific XTTS fine-tunes or language idiosyncrasies.

3.  **The "Service" Path (Docker):**
    *   Deploy `lojikng/docker-tts-api-ui` via Docker Compose.
    *   Use this if you want a shared TTS server accessible by multiple ComfyUI instances or other apps via API.