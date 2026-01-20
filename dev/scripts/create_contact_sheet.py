#!/usr/bin/env python3
"""
Create contact sheet from extracted video frames.

Usage:
    python create_contact_sheet.py <frame_dir> <output_path> [--cols N]
"""

import os
import sys
from pathlib import Path
from PIL import Image
import argparse


def create_contact_sheet(frame_dir: str, output_path: str, cols: int = 10) -> None:
    """
    Create a contact sheet (grid montage) from video frames.

    Args:
        frame_dir: Directory containing extracted frames (PNG files)
        output_path: Path to save the contact sheet image
        cols: Number of columns in the grid (default: 10)
    """
    frame_dir = Path(frame_dir)

    # Find all PNG frames, sorted numerically
    frame_files = sorted(
        [f for f in os.listdir(frame_dir) if f.endswith('.png')],
        key=lambda x: int(x.split('.')[0].lstrip('0') or '0')
    )

    if not frame_files:
        print(f"ERROR: No PNG frames found in {frame_dir}")
        sys.exit(1)

    # Load first frame to get dimensions
    first_frame_path = frame_dir / frame_files[0]
    first_frame = Image.open(first_frame_path)
    img_width, img_height = first_frame.size
    first_frame.close()

    # Calculate grid dimensions
    num_frames = len(frame_files)
    rows = (num_frames + cols - 1) // cols

    print(f"Creating contact sheet from {num_frames} frames...")
    print(f"  Grid: {rows} rows x {cols} cols")
    print(f"  Frame size: {img_width}x{img_height}")
    print(f"  Output size: {img_width * cols}x{img_height * rows}")

    # Create contact sheet
    contact_sheet = Image.new('RGB', (img_width * cols, img_height * rows))

    for i, frame_file in enumerate(frame_files):
        frame_path = frame_dir / frame_file
        frame = Image.open(frame_path)

        row = i // cols
        col = i % cols
        contact_sheet.paste(frame, (col * img_width, row * img_height))

        frame.close()

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save contact sheet
    contact_sheet.save(output_path, quality=85, optimize=True)
    contact_sheet.close()

    print(f"\nSUCCESS: Contact sheet saved to {output_path}")

    # Calculate approximate file size
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  File size: {file_size_mb:.2f} MB")


def main():
    parser = argparse.ArgumentParser(
        description='Create contact sheet from video frames'
    )
    parser.add_argument(
        'frame_dir',
        help='Directory containing extracted PNG frames'
    )
    parser.add_argument(
        'output_path',
        help='Path to save the contact sheet image'
    )
    parser.add_argument(
        '--cols', '-c',
        type=int,
        default=10,
        help='Number of columns in grid (default: 10)'
    )

    args = parser.parse_args()

    create_contact_sheet(args.frame_dir, args.output_path, args.cols)


if __name__ == '__main__':
    main()
