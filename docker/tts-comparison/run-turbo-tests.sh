#!/bin/bash
# Chatterbox Turbo (Standard English) Tests
# Note: Turbo is English-only, so Spanish tests are skipped

set -e

BASE="/home/oz/projects/2025/oz/12/runpod/docker/tts-comparison"
VOICES="/home/oz/projects/2025/oz/12/runpod/docker/voice-samples"

# Test prompts (same as Multilingual for comparison)
NEUTRAL="Welcome to AF High Definition Car Care. We appreciate your business and look forward to serving you."
EXCITED="Oh wow! This is absolutely incredible! I can't believe how amazing this looks! You're going to love it!"
CALM="Take a deep breath. Everything is going to be alright. Let's review the details together, one step at a time."
PROFESSIONAL="Good afternoon. I'm calling to confirm your appointment for tomorrow at 3 PM. Please let us know if you need to reschedule."

echo "============================================"
echo "=== Chatterbox TURBO (English) Tests ==="
echo "============================================"
echo ""

# Upload voices (container was recreated)
echo "[Setup] Uploading voices for Turbo model..."
curl -s -X POST "http://localhost:8000/voices" -F "voice_file=@$VOICES/celebrity/morgan-freeman.wav" -F "voice_name=morgan" -F "language=en" > /dev/null 2>&1 || true
curl -s -X POST "http://localhost:8000/voices" -F "voice_file=@$VOICES/celebrity/sophie-anderson.wav" -F "voice_name=sophie" -F "language=en" > /dev/null 2>&1 || true
curl -s -X POST "http://localhost:8000/voices" -F "voice_file=@$VOICES/celebrity/david-attenborough.wav" -F "voice_name=attenborough" -F "language=en" > /dev/null 2>&1 || true
sleep 2
echo "  Voices uploaded"
echo ""

# ===========================================
# TEST 4: TURBO BASELINE (Same prompts as Multilingual)
# ===========================================
TEST4="$BASE/test-04-turbo-baseline"
mkdir -p "$TEST4"
echo "[Test 4] Turbo Baseline - Default settings"

curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$NEUTRAL\", \"voice\": \"morgan\"}" \
  -o "$TEST4/morgan-neutral.wav"
echo "  morgan-neutral.wav"

curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$NEUTRAL\", \"voice\": \"sophie\"}" \
  -o "$TEST4/sophie-neutral.wav"
echo "  sophie-neutral.wav"

curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$NEUTRAL\", \"voice\": \"attenborough\"}" \
  -o "$TEST4/attenborough-neutral.wav"
echo "  attenborough-neutral.wav"

echo "[Test 4] Done: 3 files in $TEST4"
echo ""

# ===========================================
# TEST 5: TURBO EXPRESSIVENESS
# ===========================================
TEST5="$BASE/test-05-turbo-expressiveness"
mkdir -p "$TEST5"
echo "[Test 5] Turbo Expressiveness Variations"

# Low emotion, fast pace
echo "  Testing: Low emotion, fast (exag=0.3, cfg=0.3, temp=0.6)..."
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$PROFESSIONAL\", \"voice\": \"morgan\", \"exaggeration\": 0.3, \"cfg_weight\": 0.3, \"temperature\": 0.6}" \
  -o "$TEST5/morgan-low-fast.wav"

# High emotion, slower pace
echo "  Testing: High emotion, slow (exag=1.5, cfg=0.8, temp=1.2)..."
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$EXCITED\", \"voice\": \"sophie\", \"exaggeration\": 1.5, \"cfg_weight\": 0.8, \"temperature\": 1.2}" \
  -o "$TEST5/sophie-high-excited.wav"

# Maximum emotion (dramatic)
echo "  Testing: Maximum emotion (exag=2.0, cfg=0.5, temp=1.5)..."
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$EXCITED\", \"voice\": \"morgan\", \"exaggeration\": 2.0, \"cfg_weight\": 0.5, \"temperature\": 1.5}" \
  -o "$TEST5/morgan-max-dramatic.wav"

# Calm and steady
echo "  Testing: Calm and steady (exag=0.4, cfg=0.7, temp=0.5)..."
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$CALM\", \"voice\": \"sophie\", \"exaggeration\": 0.4, \"cfg_weight\": 0.7, \"temperature\": 0.5}" \
  -o "$TEST5/sophie-calm-steady.wav"

# David Attenborough documentary style
echo "  Testing: Documentary narration (exag=0.6, cfg=0.6, temp=0.7)..."
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"And here we observe the magnificent vehicle, gleaming in the morning light, as our experts begin the intricate process of restoration.\", \"voice\": \"attenborough\", \"exaggeration\": 0.6, \"cfg_weight\": 0.6, \"temperature\": 0.7}" \
  -o "$TEST5/attenborough-documentary.wav"

echo "[Test 5] Done: 5 files in $TEST5"
echo ""

# ===========================================
# TEST 6: TURBO SAME PROMPT COMPARISON
# ===========================================
TEST6="$BASE/test-06-turbo-compare-settings"
mkdir -p "$TEST6"
echo "[Test 6] Same prompt with different settings (Morgan Freeman - Turbo)"

COMPARE_PROMPT="Your vehicle is ready for pickup. The detailing work has been completed to our highest standards."

# Default
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$COMPARE_PROMPT\", \"voice\": \"morgan\"}" \
  -o "$TEST6/01-default.wav"
echo "  01-default.wav (exag=0.5, cfg=0.5, temp=0.8)"

# Low emotion
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$COMPARE_PROMPT\", \"voice\": \"morgan\", \"exaggeration\": 0.25, \"cfg_weight\": 0.3, \"temperature\": 0.5}" \
  -o "$TEST6/02-low-emotion.wav"
echo "  02-low-emotion.wav (exag=0.25, cfg=0.3, temp=0.5)"

# Medium emotion
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$COMPARE_PROMPT\", \"voice\": \"morgan\", \"exaggeration\": 0.8, \"cfg_weight\": 0.5, \"temperature\": 0.8}" \
  -o "$TEST6/03-medium-emotion.wav"
echo "  03-medium-emotion.wav (exag=0.8, cfg=0.5, temp=0.8)"

# High emotion
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$COMPARE_PROMPT\", \"voice\": \"morgan\", \"exaggeration\": 1.5, \"cfg_weight\": 0.6, \"temperature\": 1.2}" \
  -o "$TEST6/04-high-emotion.wav"
echo "  04-high-emotion.wav (exag=1.5, cfg=0.6, temp=1.2)"

# Max emotion
curl -s -X POST "http://localhost:8000/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"$COMPARE_PROMPT\", \"voice\": \"morgan\", \"exaggeration\": 2.0, \"cfg_weight\": 0.7, \"temperature\": 1.5}" \
  -o "$TEST6/05-max-emotion.wav"
echo "  05-max-emotion.wav (exag=2.0, cfg=0.7, temp=1.5)"

echo "[Test 6] Done: 5 files in $TEST6"
echo ""

# ===========================================
# RESULTS SUMMARY
# ===========================================
echo "============================================"
echo "=== Turbo Results Summary ==="
echo "============================================"
echo ""

for testdir in "$TEST4" "$TEST5" "$TEST6"; do
  echo "$(basename $testdir):"
  for f in "$testdir"/*.wav; do
    if [ -f "$f" ]; then
      dur=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$f" 2>/dev/null)
      printf "  %-35s %5.1fs\n" "$(basename $f)" "$dur"
    fi
  done
  echo ""
done

echo "============================================"
echo "=== COMPARISON: Multilingual vs Turbo ==="
echo "============================================"
echo ""
echo "Compare these folders:"
echo "  MULTILINGUAL: test-01-baseline, test-02-expressiveness, test-03-compare-settings"
echo "  TURBO:        test-04-turbo-baseline, test-05-turbo-expressiveness, test-06-turbo-compare-settings"
echo ""
echo "Key differences to listen for:"
echo "  - Speed: Turbo should be faster inference (not necessarily faster speech)"
echo "  - Quality: Multilingual may have better expressiveness range"
echo "  - Turbo: English-only but potentially more consistent"
