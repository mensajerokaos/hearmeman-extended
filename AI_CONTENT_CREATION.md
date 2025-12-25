# AI Content Creation Guide - fal.ai & KIE.ai Image/Video Generation

Complete guide for image and content generation workflows using fal.ai and KIE.ai generation scripts.

---

## For Subagents (Codex Exec)

**Scripts location**: `~/scripts/ai-generation/` (shared across all projects)

**Quick generation command**:
```bash
# fal.ai (fast & cheap)
python ~/scripts/ai-generation/fal_generate.py flux-schnell "your prompt" --size 1920x1080

# KIE.ai (Midjourney quality)
python ~/scripts/ai-generation/kie_generate.py midjourney "your prompt" --aspect 16:9
```

**Write results to file** (avoid stdout token bloat):
```bash
# After generating, log the result
echo "Generated: agents/artifacts/content/img/fal.ai/flux-schnell_abc123.png" >> agents/artifacts/docs/generation-log.md
```

**Model quick reference**:
| Need | Command |
|------|---------|
| Fast draft | `fal_generate.py flux-schnell "prompt"` |
| High quality | `fal_generate.py flux-dev "prompt"` |
| Artistic | `kie_generate.py midjourney "prompt"` |
| Text in image | `fal_generate.py recraft-v3 "prompt"` |
| Video | `kie_generate.py kling "prompt" --duration 5` |

---

## Quick Start

### 1. Setup Environment
```bash
# Add API keys to your project's .env file
FAL_KEY=your_fal_api_key_here
KIE_API_KEY=your_kie_api_key_here

# Get your keys:
# - fal.ai: https://fal.ai/dashboard/keys
# - KIE.ai: https://kie.ai (dashboard → API keys)
```

### 2. Install Dependencies
```bash
pip install requests
```

### 3. Generate Image
```bash
# Fast & cheap with fal.ai FLUX
python ~/scripts/ai-generation/fal_generate.py flux-schnell "A sunset over mountains"

# High quality with fal.ai FLUX dev
python ~/scripts/ai-generation/fal_generate.py flux-dev "Professional photo" --size 1920x1080

# With KIE.ai Midjourney
python ~/scripts/ai-generation/kie_generate.py midjourney "A professional photo of car damage"
```

### 4. Log
Update `todo.md` and `AGENTS.md` with:
- Image filename
- Generator (agent/human)
- Timestamp
- Status

---

## Available Scripts

Scripts location: `~/scripts/ai-generation/`

### `fal_generate.py` - fal.ai Generation

Supports: FLUX variants, Z-Image, Stable Diffusion 3.5, Recraft, video models

```bash
# List all models
python ~/scripts/ai-generation/fal_generate.py --list-models

# Get model-specific documentation
python ~/scripts/ai-generation/fal_generate.py --help-model z-image-lora

# Generate with FLUX (fast & cheap)
python ~/scripts/ai-generation/fal_generate.py flux-schnell "A sunset over mountains"

# Generate with Z-Image Turbo + LoRA
python ~/scripts/ai-generation/fal_generate.py z-image-lora "Portrait photo" --lora "https://url/style.safetensors,0.8"

# Custom size
python ~/scripts/ai-generation/fal_generate.py flux-dev "Landscape" --size 1920x1080
python ~/scripts/ai-generation/fal_generate.py flux-dev "Landscape" --size landscape_16_9

# Multiple LoRAs (max 3)
python ~/scripts/ai-generation/fal_generate.py z-image-lora "Photo" \
  --lora "https://url/style1.safetensors,0.8" \
  --lora "https://url/style2.safetensors,0.5"
```

**fal.ai Models:**
| Model | Type | Cost | Best For |
|-------|------|------|----------|
| flux-schnell | Image | ~$0.003 | Fast drafts, cheap |
| flux-dev | Image | ~$0.025 | High quality |
| flux-pro | Image | ~$0.05 | 2K resolution |
| flux-lora | Image | ~$0.025 | Custom LoRA styles |
| z-image-lora | Image | ~$0.0085/MP | Fast + LoRA support |
| recraft-v3 | Image | ~$0.04 | Text in images |
| sd35-large | Image | ~$0.035 | General purpose |
| kling-video | Video | ~$0.15 | Text to video |

### `kie_generate.py` - KIE.ai Generation

Supports: Midjourney, Flux, Kling, SUNO, Runway, Hailuo, Pika, Luma, Ideogram, Vidu

```bash
# List available models
python ~/scripts/ai-generation/kie_generate.py --help

# Get model-specific documentation
python ~/scripts/ai-generation/kie_generate.py --help-model midjourney

# Generate image with Midjourney (relaxed = lowest cost)
python ~/scripts/ai-generation/kie_generate.py midjourney "A professional photo of car damage"

# With options
python ~/scripts/ai-generation/kie_generate.py midjourney "prompt" --aspect 1:1 --speed fast

# Generate video with Kling
python ~/scripts/ai-generation/kie_generate.py kling "A car driving on a highway" --duration 5
```

**KIE.ai Models:**
| Model | Type | Best For |
|-------|------|----------|
| midjourney | Image | Photorealistic, artistic (default: relaxed speed) |
| flux | Image | Fast iterations |
| ideogram | Image | Text in images, logos |
| kling | Video | Short clips |
| runway | Video | High quality |
| suno | Audio | Music generation |

---

## Output Locations

Generated files are automatically saved to project's `agents/artifacts/content/`:

```
agents/artifacts/
├── docs/                    ← Documentation (AI_CONTENT_CREATION.md, todo.md)
├── scripts/                 ← Project-specific runnable scripts
└── content/
    ├── img/                 ← Images
    │   ├── kie.ai/          # midjourney_abc123.png
    │   └── fal.ai/          # flux-dev_xyz789.png
    ├── video/               ← Videos
    │   ├── kie.ai/          # kling_abc123.mp4
    │   └── fal.ai/          # kling-video_xyz789.mp4
    └── audio/               ← Audio
        ├── kie.ai/          # suno_abc123.mp3
        └── fal.ai/
```

**Override output path:**
```bash
python ~/scripts/ai-generation/kie_generate.py midjourney "prompt" -o /custom/path/image.png
python ~/scripts/ai-generation/fal_generate.py flux-dev "prompt" -o /custom/path/image.png
```

---

## Common Options

Both scripts support:

| Option | Description |
|--------|-------------|
| `--help-model MODEL` | Show detailed model documentation |
| `-o, --output PATH` | Custom output file path |
| `--no-wait` | Submit job and exit (don't wait for result) |
| `--timeout N` | Timeout in seconds (default: 300-600) |
| `--json` | Output raw JSON response |
| `--seed N` | Seed for reproducibility |

---

## Prompting Guide - Image Structure

Always use this pattern for consistent, brand-aligned outputs:

### 1. General Prompt Structure

Include these elements in order:

1. **Role & Intent**: What the image is for (hero, before/after, thumbnail)
2. **Subject & Action**: What's in the frame and what is happening
3. **Framing & Aspect**: Camera angle, crop, and target resolution
4. **Lighting & Mood**: Time of day, contrast, reflections
5. **Brand Styling**: Palette hex colors (no visible text/logos)

**Essential additions to every prompt**:
- "Premium car detailing / body shop" tone
- Avoid visible brand text inside the image (HTML handles text)
- "High contrast, clean, no clutter, sharp focus" for web use

### 2. Aspect Ratios & Sizes

Canonical sizes for landing pages:

| Purpose | Size | Ratio | Notes |
|---------|------|-------|-------|
| Hero backgrounds | 1920×1080 | 16:9 | Main sections, large display |
| Before/after portraits | 1080×1350 | 4:5 | Vertical, case studies |
| Detail/thumbnail | 1280×720 | 16:9 | Cards, results |
| Results cards (square) | 1080×1080 | 1:1 | Social, cards |

When prompting, always include the aspect explicitly:
> "Generate a 1920×1080 (16:9) background image…"
> "Vertical 1080×1350 (4:5) composition showing…"

### 3. Brand Visual Rules

**Color Palette** (use hex values ONLY):
- Gold: `#CFA248`
- Red: `#B32024`
- Black/Charcoal: `#050608`
- Light Gray: `#D4D7DD`

**Mood & Style**:
- Cinematic, slightly dramatic lighting
- Think "premium studio" or "high-end workshop"
- Wet floors, strong reflections, but avoid busy backgrounds
- Modern vehicles, no visible OEM logos/badges

**Important**: Always reference specific hex values when using brand colors.

### 4. Example Prompts

#### Hero - Body Shop (Hojalatería)
> "Generate a 1920×1080 (16:9) hero background for a premium car body shop in Querétaro, shot like a long‑lens motorsport frame. Use a compressed telephoto look: a dark luxury SUV in a spotless workshop bay at night, background structures stacked and slightly out of focus. Soft overhead light plus warm gold `#CFA248` accent lights reflecting on wet floor, with deep black `#050608` shadows and tiny red `#B32024` highlights. Keep left third of frame cleaner for text overlays. Cinematic, high contrast, no visible text or logos."

#### Hero - Ceramic Protection
> "Generate a 1920×1080 (16:9) hero background for ceramic protection with telephoto racing shot language. Long‑lens compression on a dark coupe, hood and fender filled with tight, glossy water beads under spotlight. Background (garage walls, equipment) flattened and blurred. Subtle warm gold `#CFA248` rim light, cooler shadows, strong reflections on black `#050608` paint, very small red `#B32024` accents. No text or logos."

#### Before/After - Damage (4:5 vertical)
> "Generate a 1080×1350 (4:5 vertical) 'before' photo for car body repair. Moderately wide angle (24–35mm) showing rear quarter of dark sedan with visible dent and scuffed, faded paint, plus workshop floor and wall for context. Perspective dramatic but not distorted. Lighting neutral to slightly cool, revealing damage clearly. No people, no visible logos/text."

#### Results Card (Square - 1:1)
> "Generate a 1080×1080 (1:1 square) results card for ceramic coating. Close telephoto shot of dark hood or fender covered in tight water beads. Diagonal streak of warm gold `#CFA248` light across surface, reflections in black `#050608` paint, small red `#B32024` accents in background bokeh. Soft abstract background, no text or logos."

---

## Workflow Examples

### Photo Damage Guide (Marketing)

```bash
# Generate damage photo examples for infographic
python ~/scripts/ai-generation/fal_generate.py flux-dev "Close-up photo of a car door dent, professional automotive photography, white background, studio lighting" --size square

python ~/scripts/ai-generation/kie_generate.py midjourney "Macro photo of scratched car paint showing deep scratch marks, insurance documentation style" --aspect 1:1
```

### Social Media Content

```bash
# Quick drafts with flux-schnell (cheapest)
python ~/scripts/ai-generation/fal_generate.py flux-schnell "Modern auto body shop interior, clean workspace" --images 4

# Final version with flux-dev
python ~/scripts/ai-generation/fal_generate.py flux-dev "Modern auto body shop interior, clean workspace, professional photography"
```

### Video Content

```bash
# Generate short video clip
python ~/scripts/ai-generation/kie_generate.py kling "Time-lapse of car being repaired in body shop" --duration 5
```

---

## Best Practices

### Image Generation
- **Brand consistency**: Always use hex color values from the palette; avoid vague references
- **Aspect ratios**: State target dimensions in prompts so model composes correctly
- **Negative space**: For hero backgrounds, leave one side cleaner for text overlays
- **Versioning**: Never overwrite existing assets; use `-v2`, `-v3` suffixes for iterations

### File Organization
- Images auto-save to `agents/artifacts/content/img/{provider}/`
- Videos auto-save to `agents/artifacts/content/video/{provider}/`
- Audio auto-saves to `agents/artifacts/content/audio/{provider}/`
- Use descriptive filenames with dimensions when using `-o`: `hero-hojalateria-1920x1080.webp`

### Documentation
- Log every image generation in `agents/artifacts/docs/todo.md` with checkbox, date, and agent
- Update `AGENTS.md` with batch summaries (agent, timestamp, files completed)
- Keep prompts in a reference doc for consistency across batches

### Optimization (Optional)
Convert to WebP/AVIF for better web performance:
```bash
# PNG to WebP
ffmpeg -i original.png -c:v libwebp -quality 80 output.webp

# PNG to AVIF
ffmpeg -i original.png -c:v libaom-av1 -crf 23 output.avif
```

---

## Troubleshooting

### API Key Not Set
Add key to your project's `.env`:
```bash
echo 'FAL_KEY=your_key' >> .env
echo 'KIE_API_KEY=your_key' >> .env
```

### "requests module not found"
```bash
pip install requests
```

### Timeout Errors
Increase timeout or use `--no-wait`:
```bash
python ~/scripts/ai-generation/kie_generate.py midjourney "prompt" --timeout 900
# Or submit and check later
python ~/scripts/ai-generation/kie_generate.py midjourney "prompt" --no-wait --json
```

### Image Quality Issues
- Specify dimensions clearly in prompt (e.g., "1920×1080 (16:9)")
- Use hex color values (not color names)
- Describe lighting and mood explicitly
- Request "high contrast, clean, sharp focus" for web use

---

## Cost Comparison

| Use Case | Cheapest Option | Cost |
|----------|-----------------|------|
| Quick drafts | fal.ai flux-schnell | ~$0.003 |
| Quality images | fal.ai flux-dev | ~$0.025 |
| Premium/artistic | kie.ai midjourney (relaxed) | ~$0.03-0.10 |
| Text in images | fal.ai recraft-v3 | ~$0.04 |
| Custom LoRA | fal.ai z-image-lora | ~$0.0085/MP |
| Video | kie.ai kling | ~$0.10-0.30 |

---

## Summary

1. **Generate**: Use `fal_generate.py` or `kie_generate.py` with structured prompt
2. **Organize**: Files auto-sort to `agents/artifacts/content/{type}/{provider}/`
3. **Log**: Update `todo.md` and `AGENTS.md` with status and agent info
4. **Ship**: Commit images and documentation to project
