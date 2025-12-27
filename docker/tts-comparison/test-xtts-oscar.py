#!/usr/bin/env python3
"""
Oscar Voice Cloning - XTTS v2 Tests
"""
import os
import json
import random
import urllib.request
from pathlib import Path

XTTS_URL = "http://localhost:8020"
OUTPUT_DIR = Path("/home/oz/projects/2025/oz/12/runpod/docker/tts-comparison/oscar-cloning-results/xtts-v2")

EN_PROMPT = "Welcome to the demonstration. This is a test of voice cloning technology using my own recorded voice samples."
ES_PROMPT = "Bienvenidos a la demostración. Esta es una prueba de clonación de voz usando mis propias muestras grabadas."

TONES = ["regular", "deep", "troll", "friendly", "casanova"]
SEEDS = [42, 123, 777]

def tts_to_audio(text, speaker, language, output_path):
    """Generate audio using XTTS"""
    data = json.dumps({
        "text": text,
        "speaker_wav": speaker,
        "language": language
    }).encode('utf-8')

    req = urllib.request.Request(f"{XTTS_URL}/tts_to_audio/", data=data)
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            audio_data = response.read()
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            return len(audio_data)
    except Exception as e:
        print(f"Error: {e}")
        return 0

def main():
    print("=" * 60)
    print("=== Oscar Voice Cloning - XTTS v2 ===")
    print("=" * 60)

    # Check XTTS
    try:
        with urllib.request.urlopen(f"{XTTS_URL}/speakers_list", timeout=10) as response:
            speakers = json.loads(response.read())
            print(f"\nAvailable speakers: {len(speakers)}")
            oscar_speakers = [s for s in speakers if 'oscar' in s.lower()]
            print(f"Oscar speakers: {oscar_speakers}")
    except Exception as e:
        print(f"Error: XTTS not accessible - {e}")
        return

    # Clean old failed files
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for f in OUTPUT_DIR.glob("*.wav"):
        if f.stat().st_size < 1000:
            f.unlink()
            print(f"Removed failed file: {f.name}")

    # Seed log
    seed_log = OUTPUT_DIR / "xtts-seeds.log"
    with open(seed_log, "w") as f:
        f.write("Oscar XTTS v2 Voice Cloning Seeds\n")
        f.write("=" * 40 + "\n")

    print(f"\nOutput: {OUTPUT_DIR}")
    print("\n[Generating English samples...]")
    results = []

    for tone in TONES:
        speaker = f"20251227-en-oscar-{tone}-voice-001"
        if speaker not in speakers:
            print(f"  Skipping {tone} - speaker not found")
            continue

        for seed in SEEDS:
            filename = f"xtts-en-{tone}-seed{seed}.wav"
            output_path = OUTPUT_DIR / filename
            print(f"  {tone} (seed={seed})...", end=" ", flush=True)

            size = tts_to_audio(EN_PROMPT, speaker, "en", output_path)
            if size > 1000:
                print(f"OK ({size//1024}KB)")
                with open(seed_log, "a") as f:
                    f.write(f"XTTS | en | {tone} | seed={seed} | {filename}\n")
                results.append(("en", tone, seed, size))
            else:
                print("FAILED")

    # Summary
    print("\n" + "=" * 60)
    print("=== Results ===")
    print("=" * 60)
    print(f"\nGenerated: {len(results)} files")
    for lang, tone, seed, size in results:
        print(f"  {lang} {tone}: seed={seed}, {size//1024}KB")

    print(f"\nSeed log: {seed_log}")
    print(f"Files: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
