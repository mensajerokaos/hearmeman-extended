#!/usr/bin/env python3
"""
Oscar Voice Cloning - Chatterbox Turbo Tests
"""
import os
import sys
import random
import torch
import torchaudio as ta
from pathlib import Path

OUTPUT_DIR = Path("/workspace/output/oscar-turbo")
VOICES_DIR = Path("/app/voices")

EN_PROMPT = "Welcome to the demonstration. This is a test of voice cloning technology using my own recorded voice samples."

TONES = ["regular", "deep", "troll", "friendly", "casanova"]

def main():
    print("=" * 60)
    print("=== Oscar Voice Cloning - Chatterbox Turbo ===")
    print("=" * 60)

    # Load Turbo model
    print("\n[1] Loading Turbo model...")
    from chatterbox.tts_turbo import ChatterboxTurboTTS

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxTurboTTS.from_pretrained(device=device)
    print(f"    Model loaded on {device}")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Seed log
    seed_log = OUTPUT_DIR / "turbo-seeds.log"
    with open(seed_log, "w") as f:
        f.write("Oscar Turbo Voice Cloning Seeds\n")
        f.write("=" * 40 + "\n")

    print(f"\n[2] Output: {OUTPUT_DIR}")

    # Run tests
    print("\n[3] Generating samples...")
    results = []

    for tone in TONES:
        voice_path = VOICES_DIR / f"oscar-en-{tone}.wav"
        if not voice_path.exists():
            print(f"    Skipping {tone} - voice not found")
            continue

        for take in range(1, 4):
            seed = random.randint(1, 10000)
            torch.manual_seed(seed)

            filename = f"turbo-en-{tone}-take{take}-seed{seed}.wav"
            print(f"    {tone} take {take} (seed={seed})...")

            try:
                wav = model.generate(
                    text=EN_PROMPT,
                    audio_prompt_path=str(voice_path)
                )
                output_path = OUTPUT_DIR / filename
                ta.save(str(output_path), wav, model.sr)

                duration = wav.shape[1] / model.sr
                with open(seed_log, "a") as f:
                    f.write(f"TURBO | en | {tone} | take={take} seed={seed} | {filename}\n")
                results.append((tone, take, seed, duration))
            except Exception as e:
                print(f"      ERROR: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("=== Results ===")
    print("=" * 60)
    print(f"\nGenerated: {len(results)} files")
    for tone, take, seed, dur in results:
        print(f"  {tone} take {take}: seed={seed}, {dur:.1f}s")

    print(f"\nSeed log: {seed_log}")
    print(f"Files: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
