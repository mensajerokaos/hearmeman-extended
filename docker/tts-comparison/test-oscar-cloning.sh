#!/bin/bash
# Oscar Voice Cloning Test
# Tests all TTS models with Oscar's recorded voices

set -e

BASE="/home/oz/projects/2025/oz/12/runpod/docker/tts-comparison"
VOICES="/home/oz/projects/2025/oz/12/runpod/docker/voice-samples/oscar"
OUTPUT="$BASE/oscar-cloning-results"
SEED_LOG="$OUTPUT/seeds.log"

# Test prompts
EN_PROMPT="Welcome to the demonstration. This is a test of voice cloning technology using my own recorded voice samples."
ES_PROMPT="Bienvenidos a la demostración. Esta es una prueba de clonación de voz usando mis propias muestras grabadas."

# Create output directory
mkdir -p "$OUTPUT"
echo "Oscar Voice Cloning Test - $(date)" > "$SEED_LOG"
echo "========================================" >> "$SEED_LOG"

echo "============================================"
echo "=== Oscar Voice Cloning Test ==="
echo "============================================"
echo ""
echo "Voice samples: $VOICES"
echo "Output: $OUTPUT"
echo ""

# List available voices
echo "[Setup] Available Oscar voices:"
ls "$VOICES"/*.wav | grep -E "(regular|deep|troll|friendly|casanova)" | xargs -n1 basename
echo ""

# ============================================
# XTTS v2 Tests
# ============================================
echo ""
echo "============================================"
echo "=== XTTS v2 Tests ==="
echo "============================================"

XTTS_OUT="$OUTPUT/xtts-v2"
mkdir -p "$XTTS_OUT"

# Upload voices to XTTS
echo "[XTTS] Uploading voices..."
for voice in "$VOICES"/*-en-oscar-*.wav; do
    name=$(basename "$voice" .wav | sed 's/.*-oscar-/oscar-en-/' | sed 's/-001//')
    echo "  Uploading: $name"
    curl -s -X POST "http://localhost:8020/clone_speaker/custom_speakers/$name.wav" \
        -F "wav_file=@$voice" > /dev/null 2>&1 || true
done

for voice in "$VOICES"/*-es-oscar-*.wav; do
    name=$(basename "$voice" .wav | sed 's/.*-oscar-/oscar-es-/' | sed 's/-00[12]//')
    echo "  Uploading: $name"
    curl -s -X POST "http://localhost:8020/clone_speaker/custom_speakers/$name.wav" \
        -F "wav_file=@$voice" > /dev/null 2>&1 || true
done

sleep 2

# XTTS English tests
echo "[XTTS] Generating English samples..."
for tone in regular deep troll friendly casanova; do
    for seed in 42 123 777; do
        outfile="$XTTS_OUT/xtts-en-${tone}-seed${seed}.wav"
        echo "  $tone (seed=$seed)..."

        curl -s -X POST "http://localhost:8020/tts_to_audio/" \
            -H "Content-Type: application/json" \
            -d "{\"text\": \"$EN_PROMPT\", \"speaker_wav\": \"oscar-en-${tone}-voice\", \"language\": \"en\"}" \
            -o "$outfile" 2>/dev/null || echo "    Failed"

        if [ -f "$outfile" ] && [ -s "$outfile" ]; then
            echo "XTTS | en | $tone | seed=$seed | $outfile" >> "$SEED_LOG"
        fi
    done
done

# XTTS Spanish tests
echo "[XTTS] Generating Spanish samples..."
for tone in deep troll friendly casanova; do
    for seed in 42 123 777; do
        outfile="$XTTS_OUT/xtts-es-${tone}-seed${seed}.wav"
        echo "  $tone (seed=$seed)..."

        curl -s -X POST "http://localhost:8020/tts_to_audio/" \
            -H "Content-Type: application/json" \
            -d "{\"text\": \"$ES_PROMPT\", \"speaker_wav\": \"oscar-es-${tone}-voice\", \"language\": \"es\"}" \
            -o "$outfile" 2>/dev/null || echo "    Failed"

        if [ -f "$outfile" ] && [ -s "$outfile" ]; then
            echo "XTTS | es | $tone | seed=$seed | $outfile" >> "$SEED_LOG"
        fi
    done
done

echo "[XTTS] Done: $(ls $XTTS_OUT/*.wav 2>/dev/null | wc -l) files"

# ============================================
# Chatterbox Multilingual Tests
# ============================================
echo ""
echo "============================================"
echo "=== Chatterbox Multilingual Tests ==="
echo "============================================"

CB_ML_OUT="$OUTPUT/chatterbox-multilingual"
mkdir -p "$CB_ML_OUT"

# Upload voices to Chatterbox
echo "[Chatterbox-ML] Uploading voices..."
for voice in "$VOICES"/*-en-oscar-*.wav; do
    name=$(basename "$voice" .wav | sed 's/.*-oscar-/oscar-en-/' | sed 's/-001//')
    echo "  Uploading: $name"
    curl -s -X POST "http://localhost:8000/voices" \
        -F "voice_file=@$voice" -F "voice_name=$name" -F "language=en" > /dev/null 2>&1 || true
done

for voice in "$VOICES"/*-es-oscar-*-001.wav; do
    name=$(basename "$voice" .wav | sed 's/.*-oscar-/oscar-es-/' | sed 's/-001//')
    echo "  Uploading: $name"
    curl -s -X POST "http://localhost:8000/voices" \
        -F "voice_file=@$voice" -F "voice_name=$name" -F "language=es" > /dev/null 2>&1 || true
done

sleep 2

# Chatterbox English tests with random seeds
echo "[Chatterbox-ML] Generating English samples..."
for tone in regular deep troll friendly casanova; do
    for i in 1 2 3; do
        seed=$((RANDOM % 10000))
        outfile="$CB_ML_OUT/cb-ml-en-${tone}-take${i}-seed${seed}.wav"
        echo "  $tone take $i (seed=$seed)..."

        curl -s -X POST "http://localhost:8000/audio/speech" \
            -H "Content-Type: application/json" \
            -d "{\"input\": \"$EN_PROMPT\", \"voice\": \"oscar-en-${tone}-voice\", \"seed\": $seed}" \
            -o "$outfile" 2>/dev/null || echo "    Failed"

        if [ -f "$outfile" ] && [ -s "$outfile" ]; then
            echo "CB-ML | en | $tone | take=$i seed=$seed | $outfile" >> "$SEED_LOG"
        fi
    done
done

# Chatterbox Spanish tests
echo "[Chatterbox-ML] Generating Spanish samples..."
for tone in deep troll friendly casanova; do
    for i in 1 2 3; do
        seed=$((RANDOM % 10000))
        outfile="$CB_ML_OUT/cb-ml-es-${tone}-take${i}-seed${seed}.wav"
        echo "  $tone take $i (seed=$seed)..."

        curl -s -X POST "http://localhost:8000/audio/speech" \
            -H "Content-Type: application/json" \
            -d "{\"input\": \"$ES_PROMPT\", \"voice\": \"oscar-es-${tone}-voice\", \"seed\": $seed}" \
            -o "$outfile" 2>/dev/null || echo "    Failed"

        if [ -f "$outfile" ] && [ -s "$outfile" ]; then
            echo "CB-ML | es | $tone | take=$i seed=$seed | $outfile" >> "$SEED_LOG"
        fi
    done
done

echo "[Chatterbox-ML] Done: $(ls $CB_ML_OUT/*.wav 2>/dev/null | wc -l) files"

# ============================================
# Summary
# ============================================
echo ""
echo "============================================"
echo "=== Results Summary ==="
echo "============================================"
echo ""
echo "Output directory: $OUTPUT"
echo ""
echo "Files generated:"
find "$OUTPUT" -name "*.wav" -type f | wc -l
echo ""
echo "Seed log: $SEED_LOG"
echo ""
echo "To listen, check:"
echo "  $OUTPUT/xtts-v2/"
echo "  $OUTPUT/chatterbox-multilingual/"
echo ""
cat "$SEED_LOG"
