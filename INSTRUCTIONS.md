# Media Analysis Pipeline Instructions

## Workflow Overview

```
Video File → Extract Frames (3 fps) → Generate Contact Sheet → Send to LLM
              ↓                                              ↓
        YouTube Transcript                         Single analysis request
```

**Key Principle**: Generate a **contact sheet** (grid of frames) instead of analyzing individual images. This is:
- **Much cheaper** - 1 LLM request vs 45+ requests
- **Better context** - LLM sees the full video narrative at once
- **Faster** - Single API call instead of batch processing

---

## Step 1: Extract Frames from Video

```bash
ffmpeg -i "/path/to/video.mp4" -vf fps=3 "/path/to/video_frames/IMG/%04d.png" -y
```

**Output structure**:
```
video_name_frames/
  IMG/
    0001.png
    0002.png
    ...
  DOC/
    contact_sheet.jpg    ← Generated in Step 2
    analysis.json        ← Generated in Step 3
```

**Example**:
```bash
ffmpeg -i "/mnt/m/solar/aria-cruz-ai/01-reto-freelancer/video/video_analysis/cosplayer-frieren-vibe-check-dc-Cody.mp4" -vf fps=3 "/mnt/m/solar/aria-cruz-ai/01-reto-freelancer/video/video_analysis/cosplayer-frieren-vibe-check-dc-Cody_frames/IMG/%04d.png" -y
```

---

## Step 2: Generate Contact Sheet

Create a grid montage of all frames. This combines all extracted frames into a single image for LLM analysis.

```python
from PIL import Image
import os

def create_contact_sheet(frame_dir, output_path, cols=10):
    """Create contact sheet from extracted video frames."""
    frame_files = sorted([f for f in os.listdir(frame_dir) if f.endswith('.png')])
    if not frame_files:
        print("No frames found!")
        return

    # Load first frame to get dimensions
    first_frame = Image.open(os.path.join(frame_dir, frame_files[0]))
    img_width, img_height = first_frame.size

    # Calculate grid dimensions
    num_frames = len(frame_files)
    rows = (num_frames + cols - 1) // cols

    # Create contact sheet
    sheet_width = img_width * cols
    sheet_height = img_height * rows
    contact_sheet = Image.new('RGB', (sheet_width, sheet_height))

    for i, frame_file in enumerate(frame_files):
        frame = Image.open(os.path.join(frame_dir, frame_file))
        row = i // cols
        col = i % cols
        contact_sheet.paste(frame, (col * img_width, row * img_height))

    # Save contact sheet
    contact_sheet.save(output_path, quality=85, optimize=True)
    print(f"Contact sheet saved: {output_path}")
    print(f"  - {num_frames} frames in {rows} rows x {cols} cols")
    print(f"  - Size: {sheet_width}x{sheet_height}")

# Usage
create_contact_sheet(
    frame_dir="/mnt/m/solar/.../video_frames/IMG/",
    output_path="/mnt/m/solar/.../video_frames/DOC/contact_sheet.jpg",
    cols=10
)
```

**Output**: Single contact sheet image containing all frames in a grid layout.

---

## Step 3: Send Contact Sheet + Transcript to LLM

Send **one** request with:
1. Contact sheet image (all frames combined)
2. YouTube transcript (JSON with timestamps)

**Prompt Template**:
```
Analyze this video content. The contact sheet shows key frames at 3 fps.
Also review the transcript for context.

Provide:
1. Main topics/themes discussed
2. Key visual elements and scenes
3. Overall narrative or flow
4. Notable quotes or moments (with timestamps if possible)
```

**Python Example**:
```python
import json

# Load transcript
with open('transcripts/video_name.json', 'r') as f:
    transcript = json.load(f)

transcript_text = "\n".join([t['text'] for t in transcript])

# Prepare prompt
prompt = f"""Analyze this video content.

CONTACT SHEET: See attached image (all frames at 3 fps)
TRANSCRIPT:
{transcript_text[:3000]}  # Truncate if too long

Provide summary, key moments, and themes."""

# Send to LLM (Minimax, OpenAI, etc.)
response = llm.analyze_image(
    image_path="contact_sheet.jpg",
    prompt=prompt
)
```

---

## Step 4: Download YouTube Transcript (Optional but Recommended)

For videos with auto-captions enabled:

```bash
pip install --break-system-packages youtube-transcript-api
```

```python
from youtube_transcript_api import YouTubeTranscriptApi

# Fetch transcript
transcript = YouTubeTranscriptApi().fetch(video_id='VIDEO_ID')
transcript_list = list(transcript)

# Save as JSON with timestamps
import json
with open('transcripts/video_name.json', 'w', encoding='utf-8') as f:
    json.dump([{
        'text': entry.text,
        'start': entry.start,
        'duration': entry.duration
    } for entry in transcript_list], f, indent=2)

# Save plain text
with open('transcripts/video_name.txt', 'w', encoding='utf-8') as f:
    for entry in transcript_list:
        f.write(f"{entry.text}\n")
```

---

## Directory Structure Example

```
M:\solar\aria-cruz-ai\01-reto-freelancer\video\video_analysis\
  cosplayer-frieren-vibe-check-dc-Cody.mp4           # Original video (15 sec)
  cosplayer-frieren-vibe-check-dc-Cody_frames\       # Frame extraction output
    IMG\
      0001.png
      0002.png
      ... (45 frames at 3 fps)
    DOC\
      contact_sheet.jpg                               # Grid montage (STEP 2)
      analysis.json                                   # LLM analysis result

  AI_Search_Realtime_AI_video.mp4                    # Another video
  AI_Search_Realtime_AI_video_frames\
    IMG\
      0001.png
      ... (many frames)
    DOC\
      contact_sheet.jpg
      analysis.json

  transcripts\
    AI_Search_Realtime_AI_video.json                 # 954 entries with timestamps
    AI_Search_Realtime_AI_video.txt                  # Plain text version
```

---

## Complete One-Liner Workflow

```bash
# 1. Extract frames
ffmpeg -i "video.mp4" -vf fps=3 "video_frames/IMG/%04d.png" -y

# 2. Generate contact sheet (run Python script from above)
python create_contact_sheet.py "video_frames/IMG/" "video_frames/DOC/contact_sheet.jpg"

# 3. Download transcript (if YouTube)
python download_transcript.py VIDEO_ID "transcripts/video_name.json"

# 4. Send to LLM (use contact_sheet.jpg + transcript)
python analyze_video.py "video_frames/DOC/contact_sheet.jpg" "transcripts/video_name.json"
```

---

## Notes

- **Always use contact sheet** - never send frames individually to LLM
- **3 fps** provides good balance between coverage and file size
- **YouTube auto-captions** must be enabled for transcript download
- **No per-image analysis** - batch all frames into single contact sheet
- **Store transcripts** alongside frames for reference
