#!/usr/bin/env python3
"""
Oscar Voice Cloning - VibeVoice Large Tests via ComfyUI API
"""
import os
import json
import random
import time
import urllib.request
import urllib.parse
from pathlib import Path

COMFYUI_URL = "http://localhost:8188"
OUTPUT_DIR = Path("/home/oz/projects/2025/oz/12/runpod/docker/tts-comparison/oscar-cloning-results/vibevoice-q8")
VOICES_DIR = Path("/workspace/ComfyUI/input/oscar-voices")

EN_PROMPT = "Welcome to the demonstration. This is a test of voice cloning technology using my own recorded voice samples."

TONES = ["regular", "deep", "troll", "friendly", "casanova"]

# ComfyUI workflow template for VibeVoice single speaker
WORKFLOW_TEMPLATE = {
    "3": {
        "class_type": "LoadAudio",
        "inputs": {
            "audio": ""  # Will be set per voice
        }
    },
    "4": {
        "class_type": "VibeVoiceSingleSpeakerNode",
        "inputs": {
            "text": EN_PROMPT,
            "model": "VibeVoice-Large-Q8",
            "attention_type": "auto",
            "quantize_llm": "full precision",
            "free_memory_after_generate": False,  # Keep loaded for batch
            "diffusion_steps": 20,
            "seed": 42,
            "cfg_scale": 1.3,
            "use_sampling": False,
            "voice_to_clone": ["3", 0],
            "temperature": 0.95,
            "top_p": 0.95,
            "max_words_per_chunk": 250,
            "voice_speed_factor": 1.0
        }
    },
    "5": {
        "class_type": "SaveAudio",
        "inputs": {
            "audio": ["4", 0],
            "filename_prefix": "vibevoice-oscar"
        }
    }
}

def queue_prompt(prompt):
    """Send a prompt to ComfyUI and wait for result"""
    data = json.dumps({"prompt": prompt}).encode('utf-8')
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data)
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Error queuing prompt: {e}")
        return None

def get_history(prompt_id):
    """Get the history for a prompt"""
    try:
        with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}", timeout=30) as response:
            return json.loads(response.read())
    except:
        return {}

def wait_for_completion(prompt_id, timeout=300):
    """Wait for a prompt to complete"""
    start = time.time()
    while time.time() - start < timeout:
        history = get_history(prompt_id)
        if prompt_id in history:
            return history[prompt_id]
        time.sleep(2)
    return None

def list_audio_files():
    """Get list of audio files in ComfyUI input"""
    try:
        with urllib.request.urlopen(f"{COMFYUI_URL}/object_info/LoadAudio", timeout=30) as response:
            data = json.loads(response.read())
            audio_info = data.get("LoadAudio", {}).get("input", {}).get("required", {}).get("audio", [])
            # Format: ["COMBO", {"options": [...], ...}]
            if len(audio_info) >= 2 and isinstance(audio_info[1], dict):
                return audio_info[1].get("options", [])
            return []
    except Exception as e:
        print(f"Error getting audio files: {e}")
        return []

def main():
    print("=" * 60)
    print("=== Oscar Voice Cloning - VibeVoice Large-Q8 ===")
    print("=" * 60)

    # Check ComfyUI is running
    try:
        with urllib.request.urlopen(f"{COMFYUI_URL}/system_stats", timeout=10) as response:
            stats = json.loads(response.read())
            print(f"\nComfyUI version: {stats['system']['comfyui_version']}")
            print(f"GPU: {stats['devices'][0]['name']}")
    except Exception as e:
        print(f"Error: ComfyUI not accessible at {COMFYUI_URL}")
        print(f"Details: {e}")
        return

    # List available audio files
    audio_files = list_audio_files()
    print(f"\nAvailable audio files: {len(audio_files)}")
    oscar_files = [f for f in audio_files if 'oscar' in f.lower()]
    print(f"Oscar voice files: {len(oscar_files)}")
    for f in oscar_files:
        print(f"  - {f}")

    if not oscar_files:
        print("\nNo Oscar voice files found in ComfyUI input.")
        print("Copy voice files to: hearmeman-extended:/workspace/ComfyUI/input/")
        return

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Seed log
    seed_log = OUTPUT_DIR / "vibevoice-q8-seeds.log"
    with open(seed_log, "w") as f:
        f.write("Oscar VibeVoice Large-Q8 Voice Cloning Seeds\n")
        f.write("=" * 40 + "\n")

    print(f"\nOutput: {OUTPUT_DIR}")

    # Run tests
    print("\n[Generating samples...]")
    results = []

    for tone in TONES:
        # Find matching voice file
        voice_file = None
        for f in oscar_files:
            if f"-en-oscar-{tone}" in f or f"-oscar-{tone}" in f:
                voice_file = f
                break

        if not voice_file:
            print(f"  Skipping {tone} - voice not found")
            continue

        for take in range(1, 4):
            seed = random.randint(1, 10000)

            # Create workflow
            workflow = json.loads(json.dumps(WORKFLOW_TEMPLATE))
            workflow["3"]["inputs"]["audio"] = voice_file
            workflow["4"]["inputs"]["seed"] = seed
            workflow["5"]["inputs"]["filename_prefix"] = f"vv-en-{tone}-take{take}-seed{seed}"

            print(f"  {tone} take {take} (seed={seed})...", end=" ", flush=True)

            # Queue prompt
            result = queue_prompt(workflow)
            if not result or "prompt_id" not in result:
                print("FAILED (queue)")
                continue

            prompt_id = result["prompt_id"]

            # Wait for completion
            history = wait_for_completion(prompt_id)
            if history and "outputs" in history:
                print("OK")
                with open(seed_log, "a") as f:
                    f.write(f"VIBEVOICE | en | {tone} | take={take} seed={seed}\n")
                results.append((tone, take, seed))
            else:
                print("FAILED (timeout)")

    # Summary
    print("\n" + "=" * 60)
    print("=== Results ===")
    print("=" * 60)
    print(f"\nGenerated: {len(results)} samples")
    for tone, take, seed in results:
        print(f"  {tone} take {take}: seed={seed}")

    print(f"\nSeed log: {seed_log}")
    print(f"Files: Check ComfyUI output folder")

if __name__ == "__main__":
    main()
