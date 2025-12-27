# Chatterbox TTS from Resemble AI - Research Findings

## 1. PyTorch API / Programmatic Usage
Chatterbox can be used directly in Python via the `chatterbox-tts` library.

### Installation
```bash
pip install chatterbox-tts
```

### Basic Usage Example
```python
import torch
import torchaudio as ta
from chatterbox import ChatterboxTurboTTS

# Initialize model (automatically handles downloading if not present)
device = "cuda" if torch.cuda.is_available() else "cpu"
model = ChatterboxTurboTTS.from_pretrained(device=device)

# Generate Audio (Zero-shot cloning via audio_prompt_path)
text = "Hello, this is a test of Chatterbox TTS from Resemble AI."
audio_prompt = "path/to/reference_10s_clip.wav"

wav = model.generate(
    text=text,
    audio_prompt_path=audio_prompt
)

# Save output
ta.save("output.wav", wav, model.sr)
```

### Key Parameters for `generate()`
- `text`: String to synthesize.
- `audio_prompt_path`: Path to a ~10s reference wav file for voice cloning.
- `exaggeration`: Float (e.g., 1.0) to control emotional intensity.
- `temperature`: Float (e.g., 1.0) for creativity/variation.

---

## 2. Gradio Interface
Chatterbox includes a native Gradio interface for web-based interaction.

### Setup & Launch
1. **Clone Repo:** `git clone https://github.com/resemble-ai/chatterbox.git`
2. **Install Deps:** `pip install -r requirements.txt && pip install gradio`
3. **Run:** `python app.py` (or `python gradio_tts_app.py` depending on version)

### Features
- Real-time text-to-speech.
- Audio file upload for zero-shot cloning.
- Pre-set voices selection.
- Controls for speed, emotion, and creativity.
- Hosted version available on [Hugging Face Spaces](https://huggingface.co/spaces/ResembleAI/Chatterbox).

---

## 3. ComfyUI Implementation
Multiple custom node implementations exist for ComfyUI.

### Primary Repository: [ComfyUI-Chatterbox](https://github.com/thefader/ComfyUI-Chatterbox)
- **Nodes Included:**
    - `Chatterbox TTS`: Text to audio with prompt support.
    - `Chatterbox Voice Conversion`: Audio-to-audio voice cloning.
    - `Chatterbox Dialog TTS`: Multi-speaker dialogue generation (up to 4 speakers).
- **Key Features:**
    - Automatic model downloading from Hugging Face.
    - VRAM Management: Uses ComfyUI's model patcher to load/offload from GPU.
    - Adjustable seed for reproducible generations.
- **Version Status:** Active and compatible with latest ComfyUI versions.

---

## 4. Self-Hosted API Deployment
Deployment is typically handled via FastAPI wrappers, often providing OpenAI-compatible endpoints.

### Recommended Docker Implementations
1. **[travisvn/chatterbox-tts-api](https://github.com/travisvn/chatterbox-tts-api)**
    - OpenAI-compatible `/v1/audio/speech` endpoint.
    - Supports voice cloning via the `voice` parameter.
    - Profile support for GPU (CUDA).
2. **[dwain-barnes/chatterbox-streaming-api-docker](https://github.com/dwain-barnes/chatterbox-streaming-api-docker)**
    - Optimized for low-latency streaming.
    - Docker Compose ready.

### Deployment Commands (Example)
```bash
# Clone API repo
git clone https://github.com/travisvn/chatterbox-tts-api.git
cd chatterbox-tts-api

# Start with Docker Compose (GPU version)
docker compose -f docker/docker-compose.gpu.yml up -d
```

### API Endpoints
- `GET /health`: Server status.
- `GET /v1/voices`: List available/pre-cached voices.
- `POST /v1/audio/speech`: Synthesize audio (OpenAI standard).

---

## Sources
- **GitHub Repository:** https://github.com/resemble-ai/chatterbox
- **Gradio Demo:** https://resemble-ai.github.io/chatterbox_demopage/
- **ComfyUI Nodes:** https://github.com/thefader/ComfyUI-Chatterbox
- **Docker API:** https://github.com/travisvn/chatterbox-tts-api
- **Benchmarks:** Resemble AI claims Chatterbox outperforms ElevenLabs in 63.75% of blind preference tests for realism.
