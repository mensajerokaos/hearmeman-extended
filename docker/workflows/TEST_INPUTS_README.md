# Test Input Files for SteadyDancer Workflow

## reference_character.png

**Replace this file** with your reference character image for dance video generation.

### Requirements:
- **Format**: PNG or JPG
- **Resolution**: 512x512 recommended (other sizes work but may crop)
- **Content**: Full-body shot of the character you want to animate
- **Pose**: Standing pose works best

### Test Image Sources:
- Use any 512x512 character image
- Ensure the full body is visible
- Plain background preferred for better results

## driving_dance.mp4

**Replace this file** with a driving dance video that provides the motion reference.

### Requirements:
- **Format**: MP4 (H.264 codec)
- **FPS**: 25-30 FPS
- **Duration**: 5-10 seconds (longer = more VRAM needed)
- **Content**: Full-body dance movement
- **Resolution**: 512x512 or similar square aspect ratio

### Expected Format:
```
Input: driving_dance.mp4
  - 25-30 FPS
  - 5-10 seconds
  - Full-body dance video
  - Character should be clearly visible
```

### Test Video Sources:
- Use any full-body dance video
- Trim to 5-10 seconds for initial testing
- Ensure consistent lighting throughout

## Usage

1. Place `reference_character.png` in this directory
2. Place `driving_dance.mp4` in this directory
3. Load `steadydancer-dance.json` workflow in ComfyUI
4. Queue the prompt

The workflow will automatically use these files as input.
