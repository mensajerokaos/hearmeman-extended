#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-help}"
WORKSPACE="${WORKSPACE:-/workspace}"
MODELS_DIR="${MODELS_DIR:-$WORKSPACE/models}"
OUTPUT_DIR="${OUTPUT_DIR:-$WORKSPACE/outputs/tts}"
REFS_DIR="${REFS_DIR:-$WORKSPACE/refs}"
QWEN_DIR="${QWEN_DIR:-$WORKSPACE/Qwen3-TTS}"
FISH_DIR="${FISH_DIR:-$WORKSPACE/fish-speech}"
CUDA_EXTRA="${CUDA_EXTRA:-cu126}"

log() {
  printf '[%s] %s\n' "$(date -Iseconds)" "$*"
}

ensure_dirs() {
  mkdir -p \
    "$MODELS_DIR/qwen3-tts" \
    "$MODELS_DIR/fish-s2" \
    "$OUTPUT_DIR" \
    "$REFS_DIR"
}

check_gpu() {
  log "GPU inventory"
  nvidia-smi || true
  python3 - <<'PY' || true
import torch
print("torch", torch.__version__)
print("cuda_available", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device", torch.cuda.get_device_name(0))
    props = torch.cuda.get_device_properties(0)
    print("total_vram_gb", round(props.total_memory / (1024 ** 3), 2))
PY
}

install_qwen3() {
  ensure_dirs
  if [ ! -d "$QWEN_DIR/.git" ]; then
    git clone https://github.com/QwenLM/Qwen3-TTS.git "$QWEN_DIR"
  fi
  cd "$QWEN_DIR"
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install -U pip setuptools wheel
  pip install -e .
  pip install -U huggingface_hub
  pip install -U flash-attn --no-build-isolation || log "flash-attn install failed; continuing without it"
}

download_qwen3_models() {
  # Start with 1.7B VoiceDesign + CustomVoice because FSF needs auditions and possible cloning.
  huggingface-cli download Qwen/Qwen3-TTS-Tokenizer-12Hz \
    --local-dir "$MODELS_DIR/qwen3-tts/Qwen3-TTS-Tokenizer-12Hz"
  huggingface-cli download Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign \
    --local-dir "$MODELS_DIR/qwen3-tts/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
  huggingface-cli download Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice \
    --local-dir "$MODELS_DIR/qwen3-tts/Qwen3-TTS-12Hz-1.7B-CustomVoice"
}

install_fish_s2() {
  ensure_dirs
  apt-get update
  apt-get install -y ffmpeg portaudio19-dev libsox-dev
  if [ ! -d "$FISH_DIR/.git" ]; then
    git clone https://github.com/fishaudio/fish-speech.git "$FISH_DIR"
  fi
  cd "$FISH_DIR"
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install -U pip setuptools wheel
  pip install -e ".[$CUDA_EXTRA]"
  pip install -U "huggingface_hub[cli]"
}

download_fish_s2_models() {
  cd "$FISH_DIR"
  # shellcheck disable=SC1091
  source .venv/bin/activate
  hf download fishaudio/s2-pro --local-dir "$MODELS_DIR/fish-s2/s2-pro"
}

qwen_smoke() {
  ensure_dirs
  log "Qwen3-TTS smoke placeholder"
  cat > "$OUTPUT_DIR/qwen3-smoke-request.json" <<'JSON'
{
  "text": "Recuerdos Vivos guarda una historia de vida.",
  "style": "voz femenina mexicana, calida, intima, natural, sin tono de anuncio",
  "language": "Spanish",
  "expected_output": "/workspace/outputs/tts/qwen3-smoke.wav"
}
JSON
  log "Wrote $OUTPUT_DIR/qwen3-smoke-request.json"
  log "Use Qwen3-TTS repo inference entrypoint once selected for VoiceDesign or CustomVoice."
}

fish_smoke() {
  ensure_dirs
  log "Fish S2 smoke placeholder"
  cat > "$OUTPUT_DIR/fish-s2-smoke-request.json" <<'JSON'
{
  "text": "[voz suave] Recuerdos Vivos guarda una historia de vida. [pausa larga] La tuya, o la de alguien que amas.",
  "expected_output": "/workspace/outputs/tts/fish-s2-smoke.wav",
  "license_note": "Fish Audio S2 uses Fish Audio Research License; clear commercial use before final production."
}
JSON
  log "Wrote $OUTPUT_DIR/fish-s2-smoke-request.json"
  log "Server skeleton:"
  printf '%s\n' "python tools/api_server.py --llama-checkpoint-path $MODELS_DIR/fish-s2/s2-pro --decoder-checkpoint-path $MODELS_DIR/fish-s2/s2-pro/codec.pth --listen 0.0.0.0:8080 --compile --api-key \"\$TTS_API_KEY\""
}

case "$MODE" in
  install)
    ensure_dirs
    check_gpu
    install_qwen3
    download_qwen3_models
    install_fish_s2
    download_fish_s2_models
    ;;
  qwen-install)
    ensure_dirs
    check_gpu
    install_qwen3
    download_qwen3_models
    ;;
  fish-install)
    ensure_dirs
    check_gpu
    install_fish_s2
    download_fish_s2_models
    ;;
  qwen-smoke)
    qwen_smoke
    ;;
  fish-smoke)
    fish_smoke
    ;;
  gpu)
    check_gpu
    ;;
  help|*)
    cat <<'EOF'
Usage:
  bash runpod-qwen3-fish-tts-startup.sh gpu
  bash runpod-qwen3-fish-tts-startup.sh qwen-install
  bash runpod-qwen3-fish-tts-startup.sh fish-install
  bash runpod-qwen3-fish-tts-startup.sh install
  bash runpod-qwen3-fish-tts-startup.sh qwen-smoke
  bash runpod-qwen3-fish-tts-startup.sh fish-smoke

Recommended first pod: 24GB VRAM. Upgrade to 48GB if Fish S2 OOMs.
EOF
    ;;
esac

