#!/bin/bash
# TTS Comparison Tests - XTTS, Chatterbox, VibeVoice
# Output: docker/tts-comparison/

OUT="/home/oz/projects/2025/oz/12/runpod/docker/tts-comparison"
cd "$OUT"

# Test prompts
EN="Welcome to AF High Definition Car Care! We're thrilled to have you. Your vehicle deserves the absolute best treatment, and that's exactly what we deliver."
ES="Bienvenido a AF High Definition Car Care. Estamos muy emocionados de atenderle. Su vehículo merece el mejor tratamiento, y eso es exactamente lo que ofrecemos."
SPANGLISH="Hey, welcome to AF Car Care! Estamos super excited de verte aquí. Your carro is gonna look amazing, te lo prometo!"

echo "=== TTS Comparison Tests ==="
echo "Output: $OUT"
echo ""

# XTTS Tests (female, male)
echo "[XTTS] Testing..."
curl -s -X POST "http://localhost:8020/tts_to_audio/" -H "Content-Type: application/json" \
  -d "{\"text\": \"$EN\", \"speaker_wav\": \"female\", \"language\": \"en\"}" -o xtts-en-female.wav &
curl -s -X POST "http://localhost:8020/tts_to_audio/" -H "Content-Type: application/json" \
  -d "{\"text\": \"$EN\", \"speaker_wav\": \"male\", \"language\": \"en\"}" -o xtts-en-male.wav &
wait
curl -s -X POST "http://localhost:8020/tts_to_audio/" -H "Content-Type: application/json" \
  -d "{\"text\": \"$ES\", \"speaker_wav\": \"female\", \"language\": \"es\"}" -o xtts-es-female.wav &
curl -s -X POST "http://localhost:8020/tts_to_audio/" -H "Content-Type: application/json" \
  -d "{\"text\": \"$ES\", \"speaker_wav\": \"male\", \"language\": \"es\"}" -o xtts-es-male.wav &
wait
curl -s -X POST "http://localhost:8020/tts_to_audio/" -H "Content-Type: application/json" \
  -d "{\"text\": \"$SPANGLISH\", \"speaker_wav\": \"female\", \"language\": \"en\"}" -o xtts-spanglish-female.wav &
curl -s -X POST "http://localhost:8020/tts_to_audio/" -H "Content-Type: application/json" \
  -d "{\"text\": \"$SPANGLISH\", \"speaker_wav\": \"male\", \"language\": \"en\"}" -o xtts-spanglish-male.wav &
wait
echo "[XTTS] Done: 6 files"

# Chatterbox Tests (uses default voice, expressive params)
echo "[Chatterbox] Testing..."
curl -s -X POST "http://localhost:8000/v1/audio/speech" -H "Content-Type: application/json" \
  -d "{\"model\": \"chatterbox\", \"input\": \"$EN\", \"voice\": \"default\"}" -o chatterbox-en.wav
curl -s -X POST "http://localhost:8000/v1/audio/speech" -H "Content-Type: application/json" \
  -d "{\"model\": \"chatterbox\", \"input\": \"$ES\", \"voice\": \"default\"}" -o chatterbox-es.wav
curl -s -X POST "http://localhost:8000/v1/audio/speech" -H "Content-Type: application/json" \
  -d "{\"model\": \"chatterbox\", \"input\": \"$SPANGLISH\", \"voice\": \"default\"}" -o chatterbox-spanglish.wav
echo "[Chatterbox] Done: 3 files"

echo ""
echo "=== Results ==="
ls -la *.wav 2>/dev/null | awk '{print $9, $5}' | column -t
echo ""
echo "Listen: $OUT/*.wav"
