#!/usr/bin/env python3
"""
Oscar Voice Cloning - Original Chatterbox (English-only with CFG & Exaggeration)
"""
import os
import sys
import random
import torch
import torchaudio as ta
from pathlib import Path

OUTPUT_DIR = Path("/workspace/output/oscar-chatterbox-original")
VOICES_DIR = Path("/app/voices")

EN_PROMPT = "Welcome to the demonstration. This is a test of voice cloning technology using my own recorded voice samples."

TONES = ["regular", "deep", "troll", "friendly", "casanova"]

def main():
    print("=" * 60)
    print("=== Oscar Voice Cloning - Chatterbox Original ===")
    print("=== (English-only with CFG & Exaggeration) ===")
    print("=" * 60)

    # Load Original model (not multilingual)
    print("\n[1] Loading Original Chatterbox model...")
    from chatterbox.tts import ChatterboxTTS

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxTTS.from_pretrained(device=device)
    print(f"    Model loaded on {device}")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Seed log
    seed_log = OUTPUT_DIR / "original-seeds.log"
    with open(seed_log, "w") as f:
        f.write("Oscar Chatterbox Original Voice Cloning Seeds\n")
        f.write("(CFG & Exaggeration enabled)\n")
        f.write("=" * 40 + "\n")

    print(f"\n[2] Output: {OUTPUT_DIR}")

    # Run tests with CFG and exaggeration
    print("\n[3] Generating samples with exaggeration...")
    results = []

    # Test with different exaggeration levels
    exaggeration_levels = [0.3, 0.5, 0.7]  # subtle, medium, expressive

    for tone in TONES:
        voice_path = VOICES_DIR / f"oscar-en-{tone}.wav"
        if not voice_path.exists():
            print(f"    Skipping {tone} - voice not found")
            continue

        for exag in exaggeration_levels:
            seed = random.randint(1, 10000)
            torch.manual_seed(seed)

            exag_label = {0.3: "subtle", 0.5: "medium", 0.7: "expressive"}[exag]
            filename = f"orig-en-{tone}-{exag_label}-seed{seed}.wav"
            print(f"    {tone} ({exag_label}, seed={seed})...", end=" ", flush=True)

            try:
                wav = model.generate(
                    text=EN_PROMPT,
                    audio_prompt_path=str(voice_path),
                    exaggeration=exag,
                    cfg_weight=0.5  # Default CFG weight
                )
                output_path = OUTPUT_DIR / filename
                ta.save(str(output_path), wav, model.sr)

                duration = wav.shape[1] / model.sr
                print(f"OK ({duration:.1f}s)")
                with open(seed_log, "a") as f:
                    f.write(f"ORIG | en | {tone} | exag={exag} seed={seed} | {filename}\n")
                results.append((tone, exag_label, seed, duration))
            except Exception as e:
                print(f"ERROR: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("=== Results ===")
    print("=" * 60)
    print(f"\nGenerated: {len(results)} files")
    for tone, exag, seed, dur in results:
        print(f"  {tone} ({exag}): seed={seed}, {dur:.1f}s")

    print(f"\nSeed log: {seed_log}")
    print(f"Files: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
