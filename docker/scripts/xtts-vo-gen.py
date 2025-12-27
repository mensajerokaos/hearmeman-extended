#!/usr/bin/env python3
"""
XTTS Voice-Over Generator
Batch TTS generation using the XTTS API server.

Usage:
    # Single line
    python xtts-vo-gen.py "Hello world" --output hello.wav

    # From file (one line per output)
    python xtts-vo-gen.py --file script.txt --output-dir ./vo-output

    # Custom voice cloning (provide reference audio)
    python xtts-vo-gen.py "Hello world" --speaker /path/to/reference.wav

    # Stream to stdout
    python xtts-vo-gen.py "Hello world" --stream | ffplay -

API Endpoints:
    - /tts_to_file: Save to server path
    - /tts_to_audio/: Get audio bytes directly
    - /tts_stream: Stream audio chunks
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error


XTTS_API_URL = os.environ.get("XTTS_API_URL", "http://localhost:8020")

# Built-in speakers
SPEAKERS = ["male", "female", "calm_female"]

# Supported languages
LANGUAGES = {
    "ar": "Arabic", "pt": "Brazilian Portuguese", "zh-cn": "Chinese",
    "cs": "Czech", "nl": "Dutch", "en": "English", "fr": "French",
    "de": "German", "it": "Italian", "pl": "Polish", "ru": "Russian",
    "es": "Spanish", "tr": "Turkish", "ja": "Japanese", "ko": "Korean",
    "hu": "Hungarian", "hi": "Hindi"
}


def api_request(endpoint: str, data: dict = None, method: str = "GET") -> bytes:
    """Make API request to XTTS server."""
    url = f"{XTTS_API_URL}{endpoint}"

    if data:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method=method
        )
    else:
        req = urllib.request.Request(url, method=method)

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        print(f"API Error: {e.code} - {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection Error: {e.reason}", file=sys.stderr)
        print(f"Is XTTS server running at {XTTS_API_URL}?", file=sys.stderr)
        sys.exit(1)


def generate_tts(
    text: str,
    speaker: str = "female",
    language: str = "en",
    output_path: Optional[str] = None,
    stream: bool = False
) -> Optional[bytes]:
    """Generate TTS audio from text."""

    data = {
        "text": text,
        "speaker_wav": speaker,
        "language": language
    }

    if output_path:
        # Use tts_to_file for server-side saving
        data["file_name_or_path"] = output_path
        result = api_request("/tts_to_file", data, method="POST")
        response = json.loads(result)
        print(f"Saved: {response.get('output_path', output_path)}")
        return None
    elif stream:
        # Stream endpoint for real-time playback
        return api_request("/tts_stream", data, method="POST")
    else:
        # Return raw audio bytes
        return api_request("/tts_to_audio/", data, method="POST")


def process_script_file(
    script_path: str,
    output_dir: str,
    speaker: str = "female",
    language: str = "en",
    prefix: str = "line"
):
    """Process a script file with multiple lines."""

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    with open(script_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    print(f"Processing {len(lines)} lines...")

    for i, line in enumerate(lines, 1):
        output_file = os.path.join(output_dir, f"{prefix}_{i:03d}.wav")
        print(f"[{i}/{len(lines)}] {line[:50]}...")

        audio = generate_tts(line, speaker, language)
        if audio:
            with open(output_file, 'wb') as f:
                f.write(audio)
            print(f"  -> {output_file}")

        # Brief pause between requests
        time.sleep(0.5)

    print(f"\nDone! Generated {len(lines)} audio files in {output_dir}")


def list_speakers():
    """List available speakers."""
    result = api_request("/speakers_list")
    speakers = json.loads(result)
    print("Available speakers:")
    for speaker in speakers:
        print(f"  - {speaker}")
    return speakers


def list_languages():
    """List supported languages."""
    result = api_request("/languages")
    data = json.loads(result)
    print("Supported languages:")
    for name, code in data.get("languages", {}).items():
        print(f"  {code}: {name}")


def main():
    parser = argparse.ArgumentParser(
        description="XTTS Voice-Over Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument("text", nargs="?", help="Text to synthesize")
    parser.add_argument("-f", "--file", help="Script file (one line per output)")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-d", "--output-dir", default="./vo-output",
                        help="Output directory for batch processing")
    parser.add_argument("-s", "--speaker", default="female",
                        help=f"Speaker voice: {', '.join(SPEAKERS)} or path to .wav")
    parser.add_argument("-l", "--language", default="en",
                        help=f"Language code: {', '.join(LANGUAGES.keys())}")
    parser.add_argument("-p", "--prefix", default="line",
                        help="Filename prefix for batch output")
    parser.add_argument("--stream", action="store_true",
                        help="Stream audio to stdout")
    parser.add_argument("--list-speakers", action="store_true",
                        help="List available speakers")
    parser.add_argument("--list-languages", action="store_true",
                        help="List supported languages")
    parser.add_argument("--api-url", help="XTTS API URL (default: http://localhost:8020)")

    args = parser.parse_args()

    if args.api_url:
        global XTTS_API_URL
        XTTS_API_URL = args.api_url

    if args.list_speakers:
        list_speakers()
        return

    if args.list_languages:
        list_languages()
        return

    if args.file:
        process_script_file(
            args.file,
            args.output_dir,
            args.speaker,
            args.language,
            args.prefix
        )
    elif args.text:
        if args.stream:
            audio = generate_tts(args.text, args.speaker, args.language, stream=True)
            sys.stdout.buffer.write(audio)
        elif args.output:
            audio = generate_tts(args.text, args.speaker, args.language)
            with open(args.output, 'wb') as f:
                f.write(audio)
            print(f"Saved: {args.output}")
        else:
            audio = generate_tts(args.text, args.speaker, args.language)
            sys.stdout.buffer.write(audio)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
