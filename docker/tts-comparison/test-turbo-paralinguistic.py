#!/usr/bin/env python3
"""
Chatterbox Turbo Paralinguistic Tags Test
Tests ALL 10 supported tags with custom natural prompts
"""
import os
import sys
import torch
import torchaudio as ta
from pathlib import Path

OUTPUT_DIR = Path("/workspace/output/test-08-paralinguistic")
VOICES_DIR = Path("/app/voices")

# All 10 paralinguistic tags with natural prompts
PARALINGUISTIC_TESTS = [
    # Tag 1: [laugh] - Full laughter
    {
        "tag": "laugh",
        "filename": "01-laugh.wav",
        "text": "And then he said, wait for it, [laugh] he actually thought the car was already clean! [laugh] Can you believe that?",
        "voice": "morgan"
    },
    # Tag 2: [chuckle] - Soft laughter
    {
        "tag": "chuckle",
        "filename": "02-chuckle.wav",
        "text": "Well, [chuckle] I suppose we could try that approach. [chuckle] It's certainly unconventional.",
        "voice": "sophie"
    },
    # Tag 3: [cough] - Coughing
    {
        "tag": "cough",
        "filename": "03-cough.wav",
        "text": "Excuse me, [cough] sorry about that. [cough] The dust from the polishing compound always gets me.",
        "voice": "morgan"
    },
    # Tag 4: [sigh] - Sighing
    {
        "tag": "sigh",
        "filename": "04-sigh.wav",
        "text": "[sigh] Another long day at the shop. [sigh] But the results are always worth it.",
        "voice": "sophie"
    },
    # Tag 5: [gasp] - Gasping
    {
        "tag": "gasp",
        "filename": "05-gasp.wav",
        "text": "[gasp] Oh my goodness! Look at that finish! [gasp] I've never seen anything so beautiful!",
        "voice": "sophie"
    },
    # Tag 6: [groan] - Groaning
    {
        "tag": "groan",
        "filename": "06-groan.wav",
        "text": "[groan] Not another scratch to buff out. [groan] This is going to take all afternoon.",
        "voice": "morgan"
    },
    # Tag 7: [sniff] - Sniffling
    {
        "tag": "sniff",
        "filename": "07-sniff.wav",
        "text": "[sniff] This new car smell is incredible. [sniff] Nothing quite like fresh leather and clean air.",
        "voice": "morgan"
    },
    # Tag 8: [shush] - Shushing
    {
        "tag": "shush",
        "filename": "08-shush.wav",
        "text": "[shush] Listen carefully. [shush] Do you hear that? The engine is purring perfectly now.",
        "voice": "sophie"
    },
    # Tag 9: [clear throat] - Throat clearing
    {
        "tag": "clear_throat",
        "filename": "09-clear-throat.wav",
        "text": "[clear throat] Ladies and gentlemen, [clear throat] I'm pleased to present your fully restored vehicle.",
        "voice": "morgan"
    },
    # Tag 10: [pause] - Timing control
    {
        "tag": "pause",
        "filename": "10-pause.wav",
        "text": "The secret to a perfect finish [pause] is patience. [pause] And the right technique.",
        "voice": "sophie"
    },
    # Combination test - multiple tags
    {
        "tag": "combo",
        "filename": "11-combination.wav",
        "text": "[clear throat] Welcome back! [laugh] Your car looks amazing! [sigh] It was quite a job, but [chuckle] we got it done. [pause] Take a look at this shine!",
        "voice": "morgan"
    },
    # Emotional scene - dramatic use
    {
        "tag": "emotional",
        "filename": "12-emotional-scene.wav",
        "text": "[gasp] Is that really my car? [sniff] I can't believe it. [pause] It looks better than the day I bought it. [chuckle] You've outdone yourselves.",
        "voice": "sophie"
    }
]

def main():
    print("=" * 60)
    print("=== Chatterbox TURBO Paralinguistic Tags Test ===")
    print("=" * 60)

    # Load model
    print("\n[1] Loading Turbo model...")
    from chatterbox.tts_turbo import ChatterboxTurboTTS

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxTurboTTS.from_pretrained(device=device)
    print(f"    Model loaded on {device}")
    print(f"    Sample rate: {model.sr}")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n[2] Output: {OUTPUT_DIR}")

    # Voice paths
    voices = {
        "morgan": VOICES_DIR / "morgan.wav",
        "sophie": VOICES_DIR / "sophie.wav"
    }

    print("\n[3] Voice samples:")
    for name, path in voices.items():
        print(f"    {name}: {path} (exists: {path.exists()})")

    if not voices["morgan"].exists():
        print("    ERROR: Voice samples not found!")
        sys.exit(1)

    # Run all tests
    print(f"\n[4] Running {len(PARALINGUISTIC_TESTS)} paralinguistic tests...")
    print("-" * 60)

    results = []
    for i, test in enumerate(PARALINGUISTIC_TESTS, 1):
        tag = test["tag"]
        filename = test["filename"]
        text = test["text"]
        voice = test["voice"]
        voice_path = voices[voice]

        print(f"\n    [{i:2d}/{len(PARALINGUISTIC_TESTS)}] Tag: [{tag}]")
        print(f"         Voice: {voice}")
        print(f"         Text: {text[:60]}...")

        try:
            wav = model.generate(
                text=text,
                audio_prompt_path=str(voice_path)
            )
            output_path = OUTPUT_DIR / filename
            ta.save(str(output_path), wav, model.sr)

            duration = wav.shape[1] / model.sr
            size = output_path.stat().st_size
            print(f"         -> {duration:.1f}s, {size:,} bytes")
            results.append({
                "tag": tag,
                "filename": filename,
                "duration": duration,
                "size": size,
                "success": True
            })
        except Exception as e:
            print(f"         ERROR: {e}")
            results.append({
                "tag": tag,
                "filename": filename,
                "success": False,
                "error": str(e)
            })

    # Summary
    print("\n" + "=" * 60)
    print("=== RESULTS SUMMARY ===")
    print("=" * 60)

    success_count = sum(1 for r in results if r["success"])
    print(f"\nSuccess: {success_count}/{len(results)}")
    print("\nGenerated files:")

    for r in results:
        if r["success"]:
            print(f"  [{r['tag']:<12}] {r['filename']:<25} {r['duration']:>5.1f}s  {r['size']:>8,} bytes")
        else:
            print(f"  [{r['tag']:<12}] {r['filename']:<25} FAILED: {r['error']}")

    print(f"\nFiles saved to: {OUTPUT_DIR}")
    print("\nParalinguistic Tags Reference:")
    print("  [laugh]        - Full laughter")
    print("  [chuckle]      - Soft laughter")
    print("  [cough]        - Coughing sound")
    print("  [sigh]         - Sighing")
    print("  [gasp]         - Gasping/catching breath")
    print("  [groan]        - Groaning")
    print("  [sniff]        - Sniffing/sniffling")
    print("  [shush]        - Shushing sound")
    print("  [clear throat] - Throat clearing")
    print("  [pause]        - Brief pause (timing)")

if __name__ == "__main__":
    main()
