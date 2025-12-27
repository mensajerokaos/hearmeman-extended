#!/bin/bash
# Chatterbox Expressiveness Tests
# Tests Multilingual model with different exaggeration/cfg_weight/temperature

set -e

BASE="/home/oz/projects/2025/oz/12/runpod/docker/tts-comparison"
VOICES="/home/oz/projects/2025/oz/12/runpod/docker/voice-samples"

# Test prompts
NEUTRAL="Welcome to AF High Definition Car Care. We appreciate your business and look forward to serving you."
EXCITED="Oh wow! This is absolutely incredible! I can't believe how amazing this looks! You're going to love it!"
CALM="Take a deep breath. Everything is going to be alright. Let's review the details together, one step at a time."
PROFESSIONAL="Good afternoon. I'm calling to confirm your appointment for tomorrow at 3 PM. Please let us know if you need to reschedule."
SPANISH="Bienvenido a AF High Definition Car Care. Estamos muy emocionados de atenderle hoy."

echo "============================================"
echo "=== Chatterbox Expressiveness Tests ==="
echo "============================================"
echo ""

# Check if voices are uploaded
echo "[Setup] Checking voice library..."
VOICE_COUNT=$(curl -s http://localhost:8000/voices | python3 -c "import sys,json; print(json.load(sys.stdin)['count'])")
if [ "$VOICE_COUNT" -lt 1 ]; then
  echo "  Uploading voices..."
  curl -s -X POST "http://localhost:8000/voices" -F "voice_file=@$VOICES/celebrity/morgan-freeman.wav" -F "voice_name=morgan" -F "language=en" > /dev/null
  curl -s -X POST "http://localhost:8000/voices" -F "voice_file=@$VOICES/celebrity/sophie-anderson.wav" -F "voice_name=sophie" -F "language=en" > /dev/null
  curl -s -X POST "http://localhost:8000/voices" -F "voice_file=@$VOICES/friend/friend-15s.mp3" -F "voice_name=friend" -F "language=es" > /dev/null
  sleep 2
fi
echo "  Voices ready: $VOICE_COUNT"
echo ""

# ===========================================
# TEST 1: BASELINE (Default Settings)
# ===========================================
TEST1="$BASE/test-01-baseline"
mkdir -p "$TEST1"
echo "[Test 1] Baseline - Default settings (exag=0.5, cfg=0.5, temp=0.8)"

curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$NEUTRAL\", \"voice\": \"morgan\"}" \
  -o "$TEST1/morgan-neutral.wav"
echo "  morgan-neutral.wav"

curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$NEUTRAL\", \"voice\": \"sophie\"}" \
  -o "$TEST1/sophie-neutral.wav"
echo "  sophie-neutral.wav"

curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$SPANISH\", \"voice\": \"friend\"}" \
  -o "$TEST1/friend-spanish.wav"
echo "  friend-spanish.wav"

echo "[Test 1] Done: 3 files in $TEST1"
echo ""

# ===========================================
# TEST 2: EXPRESSIVENESS VARIATIONS
# ===========================================
TEST2="$BASE/test-02-expressiveness"
mkdir -p "$TEST2"
echo "[Test 2] Expressiveness Variations"

# Low emotion, fast pace (customer service bot)
echo "  Testing: Low emotion, fast (exag=0.3, cfg=0.3, temp=0.6)..."
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$PROFESSIONAL\", \"voice\": \"morgan\", \"exaggeration\": 0.3, \"cfg_weight\": 0.3, \"temperature\": 0.6}" \
  -o "$TEST2/morgan-low-fast.wav"

# High emotion, slower pace (enthusiastic)
echo "  Testing: High emotion, slow (exag=1.5, cfg=0.8, temp=1.2)..."
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$EXCITED\", \"voice\": \"sophie\", \"exaggeration\": 1.5, \"cfg_weight\": 0.8, \"temperature\": 1.2}" \
  -o "$TEST2/sophie-high-excited.wav"

# Maximum emotion (dramatic)
echo "  Testing: Maximum emotion (exag=2.0, cfg=0.5, temp=1.5)..."
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$EXCITED\", \"voice\": \"morgan\", \"exaggeration\": 2.0, \"cfg_weight\": 0.5, \"temperature\": 1.5}" \
  -o "$TEST2/morgan-max-dramatic.wav"

# Calm and steady (meditation style)
echo "  Testing: Calm and steady (exag=0.4, cfg=0.7, temp=0.5)..."
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$CALM\", \"voice\": \"sophie\", \"exaggeration\": 0.4, \"cfg_weight\": 0.7, \"temperature\": 0.5}" \
  -o "$TEST2/sophie-calm-steady.wav"

# Spanish with emotion
echo "  Testing: Spanish emotional (exag=1.3, cfg=0.5, temp=1.0)..."
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$SPANISH\", \"voice\": \"friend\", \"exaggeration\": 1.3, \"cfg_weight\": 0.5, \"temperature\": 1.0}" \
  -o "$TEST2/friend-spanish-emotional.wav"

echo "[Test 2] Done: 5 files in $TEST2"
echo ""

# ===========================================
# TEST 3: SAME PROMPT, DIFFERENT SETTINGS
# ===========================================
TEST3="$BASE/test-03-compare-settings"
mkdir -p "$TEST3"
echo "[Test 3] Same prompt with different settings (Morgan Freeman)"

COMPARE_PROMPT="Your vehicle is ready for pickup. The detailing work has been completed to our highest standards."

# Default
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$COMPARE_PROMPT\", \"voice\": \"morgan\"}" \
  -o "$TEST3/01-default.wav"
echo "  01-default.wav (exag=0.5, cfg=0.5, temp=0.8)"

# Low emotion
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$COMPARE_PROMPT\", \"voice\": \"morgan\", \"exaggeration\": 0.25, \"cfg_weight\": 0.3, \"temperature\": 0.5}" \
  -o "$TEST3/02-low-emotion.wav"
echo "  02-low-emotion.wav (exag=0.25, cfg=0.3, temp=0.5)"

# Medium emotion
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$COMPARE_PROMPT\", \"voice\": \"morgan\", \"exaggeration\": 0.8, \"cfg_weight\": 0.5, \"temperature\": 0.8}" \
  -o "$TEST3/03-medium-emotion.wav"
echo "  03-medium-emotion.wav (exag=0.8, cfg=0.5, temp=0.8)"

# High emotion
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$COMPARE_PROMPT\", \"voice\": \"morgan\", \"exaggeration\": 1.5, \"cfg_weight\": 0.6, \"temperature\": 1.2}" \
  -o "$TEST3/04-high-emotion.wav"
echo "  04-high-emotion.wav (exag=1.5, cfg=0.6, temp=1.2)"

# Max emotion
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$COMPARE_PROMPT\", \"voice\": \"morgan\", \"exaggeration\": 2.0, \"cfg_weight\": 0.7, \"temperature\": 1.5}" \
  -o "$TEST3/05-max-emotion.wav"
echo "  05-max-emotion.wav (exag=2.0, cfg=0.7, temp=1.5)"

echo "[Test 3] Done: 5 files in $TEST3"
echo ""

# ===========================================
# RESULTS SUMMARY
# ===========================================
echo "============================================"
echo "=== Results Summary ==="
echo "============================================"
echo ""

for testdir in "$TEST1" "$TEST2" "$TEST3"; do
  echo "$(basename $testdir):"
  for f in "$testdir"/*.wav; do
    if [ -f "$f" ]; then
      dur=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$f" 2>/dev/null)
      printf "  %-35s %5.1fs\n" "$(basename $f)" "$dur"
    fi
  done
  echo ""
done

echo "Listen to files in:"
echo "  $TEST1"
echo "  $TEST2"
echo "  $TEST3"
