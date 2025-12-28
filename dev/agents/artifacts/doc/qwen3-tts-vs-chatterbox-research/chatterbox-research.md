# Chatterbox TTS Research Findings

This document summarizes research findings on Chatterbox TTS, covering voice cloning, CFG controls, exaggeration parameters, language support, model sizes, VRAM requirements, and inference speed.

## 1. Voice Cloning Quality and Approach (3-second reference audio)

*   **Quality:** Chatterbox TTS offers high-quality, "production-grade," and "state-of-the-art" voice cloning. In blind tests, 63.75% of listeners preferred Chatterbox TTS over ElevenLabs for naturalness and clarity.
*   **Approach:** It utilizes a zero-shot voice cloning approach, meaning it can clone a voice with a minimal audio sample.
*   **Reference Audio:** While some descriptions vaguely mention "a few seconds," the most consistent and explicit requirement for effective, production-ready voice ID creation is **5 seconds** of reference audio.

## 2. CFG (Classifier-Free Guidance) Controls

*   **Purpose:** CFG in Chatterbox TTS (exposed as `cfg_weight` or `cfg`) adjusts how closely synthesized speech adheres to a reference voice and influences pacing and emotional expressiveness.
*   **Mechanism:** Adapted from diffusion models, CFG works by amplifying the effect of conditioning (input text or reference voice) on the model's predictions during speech generation.
*   **Parameter:** The `cfg_weight` parameter typically ranges from 0.0 to 1.0, with a default value often around 0.5.
*   **Effects of `cfg_weight`:**
    *   **Lower values:** Can result in slower, more deliberate speech, potentially improving clarity. This can be particularly useful when aiming for expressive or dramatic speech, often in conjunction with "exaggeration" settings.
    *   **Higher values:** The model follows the input prompt (including reference voice characteristics and text) more strictly.
*   **Role in TTS:** CFG is crucial for managing the trade-off between maintaining the fidelity of a target speaker's voice and ensuring the synthesized speech accurately reflects the input text in zero-shot TTS.
*   **Computational Cost:** While effective, CFG can increase computational cost as it often requires multiple forward passes during inference, prompting ongoing research into more efficient alternatives.

## 3. Exaggeration Parameter for Artistic Expression

*   **Mechanism:** The "exaggeration parameter" or "artistic expression" in Chatterbox TTS is primarily controlled through textual instructions and system prompts rather than a single numerical dial.
    *   **`TTSModelSettings.instructions`:** A textual field within model settings that allows users to provide instructions to control the tone or artistic expression of the audio output.
    *   **`StepAudioTTS` System Prompts:** The `StepAudioTTS` class uses a `sys_prompt_dict` containing various prompts (e.g., for rap, vocal styles, specific emotions, languages, dialects, humming). These detailed prompts guide the TTS model's output.
    *   **Instruction Detection:** A `detect_instruction_name` method helps interpret specific keywords in the input text (e.g., "RAP", "humming") to trigger appropriate system prompts and model adjustments (`cosy_model`).
*   **Purpose:** To enable fine-grained control over the tone, emotional states, pacing, and overall artistic expression of the synthesized speech.

## 4. Language Support Differences (Original vs. Multilingual)

*   **Chatterbox Multilingual:** Supports 23 languages, enabling zero-shot voice cloning and cross-language voice transfer across all supported languages. The supported languages include: Arabic, Danish, German, Greek, English, Spanish, Finnish, French, Hebrew, Hindi, Italian, Japanese, Korean, Malay, Dutch, Norwegian, Polish, Portuguese, Russian, Swedish, Swahili, Turkish, and Chinese.
*   **Original Chatterbox:** Primarily focused on English text-to-speech. It served as the foundational model upon which the multilingual version was developed.

## 5. Model Sizes and VRAM Requirements

*   **Chatterbox-Turbo:** Requires **6GB** of VRAM.
*   **Original Chatterbox Model:** Can run comfortably on an **8GB VRAM** GPU.
*   **General Recommendation:** A minimum of 4GB of VRAM is suggested for running Chatterbox TTS, with 8GB or more recommended for optimal performance.

## 6. Inference Speed Benchmarks

*   **General Performance:** Chatterbox TTS is designed for real-time applications, generally offering sub-200ms latency. Chatterbox Turbo is specifically highlighted as "Blazing Fast" with "Faster than real-time inference."
*   **Real-Time Factor (RTF):** An RTF less than 1 indicates faster-than-real-time generation.
    *   **Streaming Implementation (RTX 4090):** Achieved an RTF of 0.499, with a latency to the first audio chunk of approximately 0.472 seconds.
    *   **CPU-based Generation:** Resulted in an RTF of approximately 6.7x (meaning it took 288 seconds to generate 43 seconds of audio).
    *   **GPU (CUDA)-based Generation:** Significantly improved performance to an RTF of approximately 1.2x (generating 42 seconds of audio in 52 seconds).
    *   **Optimized vLLM Port (3090 GPU):** Achieved an impressive speed of almost 16 times faster than real-time, generating 40 minutes of audio in about 2 minutes and 30 seconds.
*   **Conversational AI Context Metrics:**
    *   **Time-to-First-Chunk (TTFB):** Observed at 0.519 seconds.
    *   **Real-Time Factor:** Measured at 0.814, indicating audio generation approximately 1.23 times faster than real-time.
    *   **Total TTS Latency:** For a 63-character response, total latency was 2.996 seconds.
    *   **Practical Latency:** User feedback suggests that practical latency, even with streaming implementations, can range from 500ms to 1 second.

## 7. GitHub Repository

The primary GitHub repository for Chatterbox is `https://github.com/resemble-ai/chatterbox`. This repository hosts the open-source models and associated tools.
