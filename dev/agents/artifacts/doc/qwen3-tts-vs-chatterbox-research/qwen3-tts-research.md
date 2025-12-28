# Qwen3-TTS / Qwen2.5-Omni-TTS Research

This document outlines the research findings for Qwen3-TTS (also known as Qwen2.5-Omni-TTS or Qwen3 TTS), focusing on its key features and capabilities.

## 1. Voice Cloning Capabilities and Quality

Qwen3-TTS offers robust voice cloning capabilities. Specifically, the **Qwen3-TTS-VC-Flash** model supports 3-second voice cloning, enabling the generation of speech in 10 major languages using the cloned voice. This feature focuses on replicating the speaker's timbre from a short audio sample.

## 2. Voice Design Feature

The **Qwen3-TTS-VD-Flash** model provides advanced voice design features. Users can create custom voices with fine-grained control over various vocal characteristics, including timbre, prosody, emotion, and persona. This is achieved through complex natural language instructions, allowing for highly customized voice outputs.

## 3. Language Support

Qwen3-TTS boasts extensive language and dialect support:
*   **Major Languages:** Supports 10 major languages, including Chinese, English, German, Italian, Portuguese, Spanish, Japanese, Korean, French, and Russian.
*   **Chinese Dialects:** Supports multiple Chinese dialects, such as Mandarin, Hokkien, Wu, Cantonese, Sichuanese, Beijing, Nanjing, Tianjin, and Shaanxi.

## 4. Model Sizes and VRAM Requirements

### Qwen3 Models

Qwen3 offers a range of dense and Mixture-of-Experts (MoE) models with varying VRAM requirements, which can be significantly reduced through quantization (e.g., 4-bit).

**Dense Models:**
*   **Qwen3-0.6B:** Can run on GPUs with 2GB+ VRAM.
*   **Qwen3-1.7B:** Requires 4GB+ VRAM.
*   **Qwen3-4B:** Needs 8GB+ VRAM.
*   **Qwen3-8B:** Typically requires 16GB+ VRAM. With 4-bit quantization, it might run on a 6GB GPU.
*   **Qwen3-14B:** Demands 24GB+ VRAM. With 4-bit quantization, it can run on an RTX 3080 (10GB VRAM) but with slower responses; 8-bit quantization works well on an RTX 4090 (24GB VRAM).
*   **Qwen3-32B:** Generally requires 32-48GB of VRAM.

**Mixture-of-Experts (MoE) Models:**
*   **Qwen3-30B-A3B (30 billion total parameters, ~3 billion activated):**
    *   Requires 24GB+ VRAM.
    *   A Q4_K_M GGUF version requires approximately 18.6GB.
    *   Recommended GPUs include 3x RTX 4090 (72GB total), 1x A100 (80GB), or 1x M2 Ultra (64GB).
    *   While only 3B parameters are active during inference, the entire model (e.g., 80B parameters for Qwen3-Next-80B-A3B) needs to be loaded into VRAM. Without quantization, this could be 160GB.
*   **Qwen3-235B-A22B (235 billion total parameters, ~22 billion activated):** This model is highly demanding, with GGUF BF16 quantized versions reportedly around 470GB in size.

**General Qwen3 Considerations:**
*   Quantization (e.g., 4-bit or 8-bit) can significantly reduce VRAM requirements, allowing models to run on GPUs with less memory, but may impact performance and accuracy.
*   Additional VRAM is needed for activation memory, especially with long context lengths, and transient buffers; a buffer of ~20% extra VRAM is recommended.

### Qwen2.5-Omni Models

Qwen2.5-Omni is an end-to-end multimodal model. The primary model size discussed in the search results is the 7B parameter version.

*   **Qwen2.5-Omni-7B:**
    *   In full FP16 precision, it requires approximately 17 GB of VRAM.
    *   For FP32 precision, it needs over 32 GB of VRAM.
    *   Running with Flash Attention 2 can help reduce GPU memory usage, allowing it to run within 10GB of VRAM; otherwise, ~12GB is necessary with eager attention.
    *   Disabling audio output can save about ~2GB of GPU memory.
    *   An AWQ (4-bit quantization) version of Qwen2.5-Omni-7B significantly reduces VRAM requirements by over 50%+. For example, for 15-second video processing, the FP32 version needs 93.56 GB, the BF16 version needs 31.11 GB, and the AWQ version needs 11.77 GB.
    *   A local test of Qwen2.5-Omni showed it using about 17-18GB of VRAM, and it was noted that a 24GB card would likely be required for a good experience.
    *   A Google Colab tutorial for Qwen2.5-Omni-7B showed it consuming close to 33GB of VRAM in full mode on an A100 GPU.
*   **Qwen2.5-Omni-3B:** This smaller version was released to enable running on more platforms.

It's important to note that VRAM requirements can vary based on factors like context length, batch size, and specific inference frameworks used. Quantization is a key technique to reduce these requirements for running models on consumer-grade hardware.

## 5. Inference Speed

Both Qwen3-TTS and Qwen2.5-Omni-TTS are designed for high performance and real-time applications:
*   **Qwen3-TTS:** Designed for low-latency speech generation, making it suitable for interactive and conversational AI systems.
*   **Qwen2.5-Omni-TTS:** As part of the Qwen2.5-Omni multimodal model, it is built for real-time streaming responses, supporting chunked input and immediate audio output.

## 6. Artistic Controls (Emotion, Pitch, Speed)

Qwen3-TTS provides significant artistic control over speech synthesis:
*   **Emotion:** Controllable through the voice design feature (Qwen3-TTS-VD-Flash) via natural language instructions, allowing users to specify desired emotional tones.
*   **Prosody and Speech Rates:** The model demonstrates improved ability to adaptively adjust prosody and speech rates to produce more natural and human-like speech. This is also part of the fine-grained control offered by the voice design capabilities.
*   **Pitch:** While not explicitly detailed as a separate control, pitch is inherently part of prosody and timbre control within the voice design features.

## 7. GitHub Repo, Official Documentation

### Qwen3-TTS
Qwen3-TTS appears to be primarily offered as an API service by Alibaba Cloud (Qwen). Direct GitHub repositories specifically for "Qwen3-TTS" were not found, suggesting it's integrated within their broader service offerings. Official documentation would typically be found on Alibaba Cloud's platform or the Qwen official website (qwen.ai) for their API services.

### Qwen2.5-Omni
Qwen2.5-Omni is openly available on multiple platforms:
*   **Hugging Face:** Various versions of Qwen2.5-Omni (e.g., `Qwen/Qwen2.5-Omni-7B`, `Qwen/Qwen2.5-Omni-3B`, and quantized versions) are available on Hugging Face, providing model cards with detailed information and usage examples.
*   **GitHub:** The model is also stated to be available on GitHub. While a direct "Qwen2.5-Omni-TTS" GitHub was not found, the main Qwen GitHub repository or associated project pages (often linked from Hugging Face model cards) would be the place to find the code and further documentation.
*   **ModelScope, DashScope:** Other platforms where Qwen2.5-Omni is available.
