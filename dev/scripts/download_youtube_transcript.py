#!/usr/bin/env python3
"""
Download YouTube video transcript using youtube-transcript-api.

Usage:
    python download_youtube_transcript.py <video_id> <output_dir>
"""

import os
import sys
import json
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi


def download_transcript(video_id: str, output_dir: str) -> str:
    """
    Download YouTube transcript and save as JSON and TXT.

    Args:
        video_id: YouTube video ID (e.g., 'eHMVifFMq0Q')
        output_dir: Directory to save transcripts

    Returns:
        Path to JSON file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching transcript for video: {video_id}")

    try:
        transcript = YouTubeTranscriptApi().fetch(video_id=video_id)
        transcript_list = list(transcript)

        print(f"  Found {len(transcript_list)} entries")

        # Generate output filename based on video ID
        json_path = output_dir / f"{video_id}.json"
        txt_path = output_dir / f"{video_id}.txt"

        # Save as JSON with timestamps
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump([{
                'text': entry.text,
                'start': entry.start,
                'duration': entry.duration
            } for entry in transcript_list], f, indent=2, ensure_ascii=False)

        print(f"  Saved JSON: {json_path}")

        # Save plain text for reading
        with open(txt_path, 'w', encoding='utf-8') as f:
            for entry in transcript_list:
                f.write(f"{entry.text}\n")

        print(f"  Saved TXT: {txt_path}")

        return str(json_path)

    except Exception as e:
        print(f"ERROR: Failed to fetch transcript: {e}")
        print("\nPossible reasons:")
        print("  - Video has no auto-captions enabled")
        print("  - Video is private or deleted")
        print("  - Transcript is in a language that's blocked")
        sys.exit(1)


def main():
    if len(sys.argv) != 3:
        print("Usage: python download_youtube_transcript.py <video_id> <output_dir>")
        print("\nExample:")
        print("  python download_youtube_transcript.py eHMVifFMq0Q ./transcripts")
        sys.exit(1)

    video_id = sys.argv[1]
    output_dir = sys.argv[2]

    download_transcript(video_id, output_dir)


if __name__ == '__main__':
    main()
