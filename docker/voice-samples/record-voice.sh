#!/bin/bash
# Voice Recording Script for Chatterbox Voice Cloning
# Format: YYYYMMDD-[en|es]-oscar-voice-NNN.wav

# Connect to Windows PulseAudio
export PULSE_SERVER=tcp:$(grep nameserver /etc/resolv.conf | awk '{print $2}')

# Verify connection
if ! pactl info &>/dev/null; then
    echo "ERROR: PulseAudio not running."
    echo "Start whisper-vtt.ahk on Windows or run:"
    echo "  cmd.exe /c \"C:\\PulseAudio\\start-pulseaudio.bat\""
    exit 1
fi

OUTPUT_DIR="$(dirname "$0")/oscar"
mkdir -p "$OUTPUT_DIR"

LANGUAGE="${1:-es}"  # es or en
DURATION="${2:-15}"
SAMPLE_RATE=24000

# Validate language
if [[ "$LANGUAGE" != "es" && "$LANGUAGE" != "en" ]]; then
    echo "Usage: $0 [es|en] [duration]"
    echo "  es = Spanish recording"
    echo "  en = English recording"
    exit 1
fi

# Generate filename: YYYYMMDD-es-oscar-voice-001.wav
DATE_PREFIX=$(date +%Y%m%d)
BASE_NAME="${DATE_PREFIX}-${LANGUAGE}-oscar-voice"

# Find next increment
COUNTER=1
while [ -f "$OUTPUT_DIR/${BASE_NAME}-$(printf '%03d' $COUNTER).wav" ]; do
    ((COUNTER++))
done
INCREMENT=$(printf '%03d' $COUNTER)

OUTPUT_FILE="$OUTPUT_DIR/${BASE_NAME}-${INCREMENT}.wav"

echo "============================================"
echo "  Voice Recording for Chatterbox Cloning"
echo "============================================"
echo ""
echo "Language:     $LANGUAGE"
echo "Duration:     $DURATION seconds"
echo "Sample rate:  $SAMPLE_RATE Hz"
echo "Output:       $OUTPUT_FILE"
echo ""
echo "Using MixPre-D via PulseAudio"
echo ""

if [[ "$LANGUAGE" == "es" ]]; then
    echo "Suggested Spanish text to read:"
    echo "---"
    echo "Hola, bienvenidos. Hoy vamos a hablar sobre un tema"
    echo "muy interesante. Me llamo Oscar y estoy muy emocionado"
    echo "de compartir este contenido con ustedes. Espero que"
    echo "les guste y no olviden suscribirse."
    echo "---"
else
    echo "Suggested English text to read:"
    echo "---"
    echo "Hello and welcome. Today we're going to talk about"
    echo "something really interesting. My name is Oscar and I'm"
    echo "excited to share this content with you. I hope you"
    echo "enjoy it and don't forget to subscribe."
    echo "---"
fi

echo ""
echo ">>> Press ENTER when ready, then wait for countdown <<<"
read -r

echo ""
echo "Get ready..."
sleep 1
echo "3..."
sleep 1
echo "2..."
sleep 1
echo "1..."
sleep 1
echo ""
echo "RECORDING NOW! (speak for $DURATION seconds)"
echo ""

# Record using parecord (Windows PulseAudio)
TEMP_FILE="${OUTPUT_FILE%.wav}_raw.wav"
timeout "$((DURATION + 2))" parecord --channels=1 --rate="$SAMPLE_RATE" --file-format=wav "$TEMP_FILE"

# Minimal noise reduction: just highpass at 70Hz to remove rumble
ffmpeg -i "$TEMP_FILE" -af "highpass=f=70" -ar "$SAMPLE_RATE" -y "$OUTPUT_FILE" 2>/dev/null
rm -f "$TEMP_FILE"

echo ""
echo "============================================"

if [ -f "$OUTPUT_FILE" ]; then
    SIZE=$(stat -c%s "$OUTPUT_FILE" 2>/dev/null || stat -f%z "$OUTPUT_FILE")
    DURATION_ACTUAL=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTPUT_FILE" 2>/dev/null)

    echo "Recording saved!"
    echo ""
    echo "File:     $(basename "$OUTPUT_FILE")"
    echo "Path:     $OUTPUT_FILE"
    echo "Size:     $SIZE bytes"
    echo "Duration: ${DURATION_ACTUAL}s"
    echo ""

    if (( $(echo "$DURATION_ACTUAL < 10" | bc -l) )); then
        echo "WARNING: Recording is under 10 seconds. Run again for another take."
    else
        echo "Duration OK (10+ seconds)"
    fi

    echo ""
    echo "To record another take, run:"
    echo "  ./record-voice.sh $LANGUAGE $DURATION"
else
    echo "Recording failed. Check microphone permissions."
    echo ""
    echo "Try:"
    echo "  pactl info"
    echo "  pactl list sources short"
fi
