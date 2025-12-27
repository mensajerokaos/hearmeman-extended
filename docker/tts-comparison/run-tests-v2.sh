#!/bin/bash
# TTS Comparison Tests v2 - With Real Voice Samples
# Output: docker/tts-comparison/
# Voices: Morgan Freeman (male), Sophie Anderson (female), Friend (Spanish male)

set -e

OUT="/home/oz/projects/2025/oz/12/runpod/docker/tts-comparison"
cd "$OUT"

# Voice samples (copied from TTS-Audio-Suite)
VOICE_MORGAN="$OUT/morgan-freeman-11s.wav"
VOICE_SOPHIE="$OUT/sophie-female-11s.wav"
VOICE_FRIEND="$OUT/friend-voice-15s.mp3"

# Test prompts
EN="Welcome to AF High Definition Car Care! We're thrilled to have you. Your vehicle deserves the absolute best treatment, and that's exactly what we deliver."
ES="Bienvenido a AF High Definition Car Care. Estamos muy emocionados de atenderle. Su vehículo merece el mejor tratamiento, y eso es exactamente lo que ofrecemos."
SPANGLISH="Hey, welcome to AF Car Care! Estamos super excited de verte aquí. Your carro is gonna look amazing, te lo prometo!"

echo "============================================"
echo "=== TTS Comparison Tests v2 ==="
echo "============================================"
echo "Output: $OUT"
echo ""

# Verify voice files exist
echo "[Setup] Checking voice files..."
for f in "$VOICE_MORGAN" "$VOICE_SOPHIE" "$VOICE_FRIEND"; do
  if [ -f "$f" ]; then
    echo "  OK: $(basename $f)"
  else
    echo "  MISSING: $f"
    exit 1
  fi
done
echo ""

# ===========================================
# CHATTERBOX TESTS (Multilingual Model)
# ===========================================
echo "[Chatterbox] Uploading voices..."

# Upload Morgan Freeman as English male voice
curl -s -X POST "http://localhost:8000/voices" \
  -F "voice_file=@$VOICE_MORGAN" \
  -F "voice_name=morgan-male" \
  -F "language=en" > /dev/null 2>&1 || true

# Upload Sophie as English female voice
curl -s -X POST "http://localhost:8000/voices" \
  -F "voice_file=@$VOICE_SOPHIE" \
  -F "voice_name=sophie-female" \
  -F "language=en" > /dev/null 2>&1 || true

# Upload Friend as Spanish voice
curl -s -X POST "http://localhost:8000/voices" \
  -F "voice_file=@$VOICE_FRIEND" \
  -F "voice_name=friend-spanish" \
  -F "language=es" > /dev/null 2>&1 || true

echo "[Chatterbox] Voices uploaded. Running tests..."

# Wait for uploads to complete
sleep 2

# English tests with Morgan (male) and Sophie (female)
echo "  Testing English with Morgan Freeman..."
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$EN\", \"voice\": \"morgan-male\"}" \
  -o cb-en-morgan.wav

echo "  Testing English with Sophie Anderson..."
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$EN\", \"voice\": \"sophie-female\"}" \
  -o cb-en-sophie.wav

# Spanish test with Friend's voice
echo "  Testing Spanish with Friend's voice..."
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$ES\", \"voice\": \"friend-spanish\"}" \
  -o cb-es-friend.wav

# Spanglish test - try with Spanish language setting
echo "  Testing Spanglish (Spanish mode)..."
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$SPANGLISH\", \"voice\": \"friend-spanish\"}" \
  -o cb-spanglish-friend.wav

echo "[Chatterbox] Done: 4 files"
echo ""

# ===========================================
# XTTS TESTS (v2.0.2 - 17 languages)
# ===========================================
echo "[XTTS] Running tests with custom voice files..."

# XTTS uses full container paths for speaker files
# Files are mounted at ./xtts-speakers:/root/speakers in docker-compose
XTTS_CONTAINER_PATH="/root/speakers"

echo "  Testing English with Morgan Freeman..."
curl -s -X POST "http://localhost:8020/tts_to_audio/" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$EN\", \"speaker_wav\": \"$XTTS_CONTAINER_PATH/morgan.wav\", \"language\": \"en\"}" \
  -o xtts-en-morgan.wav

echo "  Testing English with Sophie Anderson..."
curl -s -X POST "http://localhost:8020/tts_to_audio/" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$EN\", \"speaker_wav\": \"$XTTS_CONTAINER_PATH/sophie.wav\", \"language\": \"en\"}" \
  -o xtts-en-sophie.wav

echo "  Testing Spanish with Friend's voice..."
curl -s -X POST "http://localhost:8020/tts_to_audio/" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$ES\", \"speaker_wav\": \"$XTTS_CONTAINER_PATH/friend.wav\", \"language\": \"es\"}" \
  -o xtts-es-friend.wav

# Spanglish - try Spanish mode since most words are Spanish-ish
echo "  Testing Spanglish (Spanish mode)..."
curl -s -X POST "http://localhost:8020/tts_to_audio/" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$SPANGLISH\", \"speaker_wav\": \"$XTTS_CONTAINER_PATH/friend.wav\", \"language\": \"es\"}" \
  -o xtts-spanglish-es-friend.wav

# Spanglish - also try English mode for comparison
echo "  Testing Spanglish (English mode)..."
curl -s -X POST "http://localhost:8020/tts_to_audio/" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$SPANGLISH\", \"speaker_wav\": \"$XTTS_CONTAINER_PATH/friend.wav\", \"language\": \"en\"}" \
  -o xtts-spanglish-en-friend.wav

echo "[XTTS] Done: 5 files"
echo ""

# ===========================================
# RESULTS
# ===========================================
echo "============================================"
echo "=== Results ==="
echo "============================================"
echo ""
echo "Chatterbox (Multilingual):"
for f in cb-*.wav; do
  if [ -f "$f" ]; then
    dur=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$f" 2>/dev/null || echo "?")
    size=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null)
    printf "  %-30s %6s bytes  %.1fs\n" "$f" "$size" "$dur"
  fi
done

echo ""
echo "XTTS v2:"
for f in xtts-*.wav; do
  if [ -f "$f" ] && [[ "$f" != *"-male.wav" ]] && [[ "$f" != *"-female.wav" ]]; then
    dur=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$f" 2>/dev/null || echo "?")
    size=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null)
    printf "  %-30s %6s bytes  %.1fs\n" "$f" "$size" "$dur"
  fi
done

echo ""
echo "Listen: $OUT/*.wav"
echo ""
echo "Voice samples used:"
echo "  Morgan Freeman: 11s (male, English)"
echo "  Sophie Anderson: 11s (female, English)"
echo "  Friend: 15s (male, Spanish)"
