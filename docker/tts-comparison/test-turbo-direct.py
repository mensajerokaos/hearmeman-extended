#!/usr/bin/env python3
"""
Chatterbox Turbo Direct Test
Runs Turbo model directly (not through API) for comparison
"""
import os
import sys
import torch
import torchaudio as ta
from pathlib import Path

# Test configuration
OUTPUT_DIR = Path("/workspace/output/test-07-turbo")
VOICES_DIR = Path("/app/voices")

# Prompts (same as other tests)
NEUTRAL = "Welcome to AF High Definition Car Care. We appreciate your business and look forward to serving you."
EXCITED = "Oh wow! This is absolutely incredible! I can't believe how amazing this looks! You're going to love it!"
CALM = "Take a deep breath. Everything is going to be alright. Let's review the details together, one step at a time."
COMPARE = "Your vehicle is ready for pickup. The detailing work has been completed to our highest standards."

# Turbo special - paralinguistic tags
LAUGH_TEXT = "Hi there, [chuckle] have you got one minute to chat? [laugh] This is amazing!"

def main():
    print("=" * 50)
    print("=== Chatterbox TURBO Direct Test ===")
    print("=" * 50)

    # Import and load model
    print("\n[1] Loading Turbo model...")
    from chatterbox.tts_turbo import ChatterboxTurboTTS

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxTurboTTS.from_pretrained(device=device)
    print(f"    Model loaded on {device}")
    print(f"    Sample rate: {model.sr}")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n[2] Output: {OUTPUT_DIR}")

    # Find voice samples - use the ones we copied
    print("\n[3] Using voice samples...")
    morgan_path = VOICES_DIR / "morgan.wav"
    sophie_path = VOICES_DIR / "sophie.wav"
    friend_path = VOICES_DIR / "friend.mp3"

    print(f"    Morgan: {morgan_path} (exists: {morgan_path.exists()})")
    print(f"    Sophie: {sophie_path} (exists: {sophie_path.exists()})")
    print(f"    Friend: {friend_path} (exists: {friend_path.exists()})")

    if not morgan_path.exists():
        print("    ERROR: Voice samples not found!")
        sys.exit(1)

    # Run tests
    print("\n[4] Running Turbo tests...")

    tests = [
        ("turbo-morgan-neutral.wav", NEUTRAL, morgan_path),
        ("turbo-sophie-excited.wav", EXCITED, sophie_path),
        ("turbo-sophie-calm.wav", CALM, sophie_path),
        ("turbo-morgan-compare.wav", COMPARE, morgan_path),
        ("turbo-morgan-laugh-tags.wav", LAUGH_TEXT, morgan_path),
    ]

    for filename, text, voice_path in tests:
        print(f"    Generating: {filename}")
        try:
            wav = model.generate(
                text=text,
                audio_prompt_path=str(voice_path)
            )
            output_path = OUTPUT_DIR / filename
            ta.save(str(output_path), wav, model.sr)

            # Get duration
            duration = wav.shape[1] / model.sr
            print(f"      -> {duration:.1f}s")
        except Exception as e:
            print(f"      ERROR: {e}")

    # Summary
    print("\n" + "=" * 50)
    print("=== Results ===")
    print("=" * 50)

    for f in sorted(OUTPUT_DIR.glob("*.wav")):
        info = ta.info(str(f))
        duration = info.num_frames / info.sample_rate
        size = f.stat().st_size
        print(f"  {f.name:<35} {size:>8} bytes  {duration:.1f}s")

    print(f"\nFiles saved to: {OUTPUT_DIR}")
    print("\nTurbo special features tested:")
    print("  - Paralinguistic tags: [chuckle], [laugh]")
    print("  - Single-step decoder (faster than base)")

if __name__ == "__main__":
    main()
