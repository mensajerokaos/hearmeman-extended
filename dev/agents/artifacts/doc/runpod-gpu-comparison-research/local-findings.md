---
author: oz
model: claude-opus-4-5-20251101
date: 2025-12-23
task: Local research findings for RunPod GPU comparison
---

# Local Findings: RunPod GPU Research Context

## 1. Existing RunPod Documentation

### Primary Resource Found
**Path**: `/home/oz/comfyui/dev/agents/artifacts/doc/runpod-vibevoice-research.md`
**Date**: 2025-12-21

This is a comprehensive 700+ line research document on RunPod deployment for VibeVoice TTS. Key excerpts:

#### RTX A5000 Pricing
| Cloud Type | Hourly Rate | Monthly (24/7) |
|------------|-------------|----------------|
| Community Cloud | **$0.16/hr** | ~$115/month |
| Secure Cloud | $0.27/hr | ~$194/month |

#### GPU Upgrade Path for VibeVoice
| GPU | VRAM | Community Price | Best For |
|-----|------|-----------------|----------|
| RTX A5000 | 24GB | $0.16/hr | VibeVoice-Large full precision |
| RTX 4090 | 24GB | ~$0.44/hr | Faster inference |
| RTX A6000 | 48GB | $0.33/hr | Multiple models loaded |
| L40 | 48GB | $0.39/hr | Production workloads |
| A100 80GB | 80GB | ~$1.99/hr | Enterprise/batch |

#### Storage Pricing
| Size | Rate | Monthly Cost |
|------|------|--------------|
| <=1TB | $0.07/GB/mo | 17GB = $1.19/mo |
| >1TB | $0.05/GB/mo | Bulk discount |

**Note**: Document does NOT contain A100 vs L40S comparison or PCIe vs SXM analysis.

---

## 2. Current Project Context: Documentary TTS Voiceover

### Project: La Maquila Erotica Documentary
**Path**: `/home/oz/projects/2025/jose-obscura/12/documental-macq/`

#### TTS Voiceover Already in Use
From `scripts/generate_voiceover.py`:
- Uses ComfyUI VibeVoice TTS
- Voice: Jose Obscura (spanish_female cloned voice)
- 22 voiceover segments to generate
- Output: FLAC files to NAS path

#### Voiceover Script
From `dev/agents/artifacts/doc/la-maquila-erotica-soul/voiceover-script.md`:
- Language: Spanish (primary)
- Total VO segments: ~25
- Estimated VO duration: 3-4 minutes
- Uses Jose's cloned voice as narrative conductor

### Current TTS Infrastructure
From `auto-video-editor/doc/comfyUI-integration-tts.md`:
- Local ComfyUI with VibeVoice
- API endpoint: `http://localhost:8188/prompt`
- Model: VibeVoice-Large (17GB)
- Hardware: RTX 4080 (local) - ~2 min for 90s audio

---

## 3. Related AI Model Research

### Z-Image API Research
**Path**: `/home/oz/projects/2025/dnd/12/cohors-cthulu/tactics-app/dev/agents/artifacts/doc/z-image-api-research-20251216.md`

Found research on Kie.ai, AIML API, fal.ai for image generation. Pricing model:
- Kie.ai: $0.004 per image
- fal.ai: $0.005 per megapixel

This indicates user experience with cloud API pricing models.

---

## 4. API Key Locations

### Checked Locations
- `~/.config/runpod*` - **NOT FOUND**
- `~/.config/*runpod*` - **NOT FOUND**
- `/home/oz/projects/**/.env*` - No RunPod keys found in grep

### Related API Keys Found (do NOT contain RunPod)
- Various `.env.local` files exist but for other services
- Pyannote key in WORKFLOW.md: `PYANNOTE_API_KEY` (for speaker diarization)
- Groq key mentioned for transcription

**Conclusion**: No RunPod API key currently configured. User needs to create account.

---

## 5. RunPod Python SDK Installed

**Path**: `/home/oz/projects/2025/12/auto-video-editor/.venv/lib/python3.12/site-packages/runpod/`

Files found:
- `runpod/api/queries/gpus.py` - GPU query API
- `runpod/cli/` - CLI utilities
- Tests for runpodignore

The SDK is already installed in the auto-video-editor environment, indicating prior exploration.

---

## 6. Model Requirements (from existing research)

### VibeVoice TTS
| Model | Size | VRAM Required |
|-------|------|---------------|
| VibeVoice-1.5B (Large) | ~17GB | ~18GB (full), ~12GB (8-bit), ~8GB (4-bit) |

### Recommendation from existing doc
"For RTX A5000 (24GB): Full precision recommended"

---

## 7. Gaps Requiring Web Research

### A100 vs L40S Comparison
**NOT FOUND** in local files. Need to research:
- A100 specifications (SXM vs PCIe variants)
- L40S specifications (Ada Lovelace)
- Price comparison on RunPod
- Performance benchmarks for inference

### PCIe vs SXM Differences
**NOT FOUND** in local files. Need to research:
- What SXM means (Server GPU Module)
- NVLink bandwidth differences
- When SXM matters vs PCIe
- Price premium justification

### Steady Dancer Model
**NOT FOUND** in local files. Need to research:
- What is Steady Dancer (video-to-video animation?)
- VRAM requirements
- RunPod compatibility

### Current December 2025 Pricing
Existing doc is from 2025-12-21 but prices may have changed:
- Verify A100 pricing
- Check L40S availability and pricing
- Check for new GPU options

---

## 8. Connection to Documentary Project

### Current Workflow
1. TTS voiceover generation uses **local RTX 4080** via ComfyUI
2. 22 Spanish voiceover segments planned
3. Voice cloning with Jose Obscura sample

### Why RunPod GPU Research?
User may be exploring:
1. **Cloud GPU for faster TTS batch processing** - Generate all 22 segments faster
2. **Steady Dancer for animation** - Video animation effects for documentary
3. **Z-Image for promotional materials** - Marketing images
4. **Scale beyond local GPU** - RTX 4080 is sufficient but may want redundancy

### Recommended GPU for TTS Only
Based on existing research:
- **RTX A5000** ($0.16/hr) - Best value for VibeVoice
- **L40** ($0.39/hr) - Production grade, 48GB headroom

For combined TTS + animation models:
- **A100 80GB** (~$1.99/hr) - If running multiple models simultaneously

---

## 9. Files Discovered (Key Paths)

| File | Relevance |
|------|-----------|
| `/home/oz/comfyui/dev/agents/artifacts/doc/runpod-vibevoice-research.md` | PRIMARY - Comprehensive RunPod deployment guide |
| `/home/oz/projects/2025/12/auto-video-editor/doc/comfyUI-integration-tts.md` | TTS API integration docs |
| `/home/oz/projects/2025/jose-obscura/12/documental-macq/scripts/generate_voiceover.py` | VO generation script |
| `/home/oz/projects/2025/jose-obscura/12/documental-macq/dev/agents/artifacts/doc/la-maquila-erotica-soul/voiceover-script.md` | 22 VO segments to generate |
| `/home/oz/projects/2025/12/auto-video-editor/.venv/.../runpod/` | RunPod SDK installed |

---

## 10. Summary for Web Research Phase

### Questions to Answer
1. **A100 specs**: 40GB vs 80GB, PCIe vs SXM, tensor cores, NVLink
2. **L40S specs**: How it compares to L40, Ada Lovelace features
3. **RunPod December 2025 pricing**: Current rates for A100, L40S
4. **PCIe vs SXM**: Technical differences, when SXM is worth premium
5. **Steady Dancer**: Model requirements, VRAM needs
6. **Best GPU for mixed workload**: TTS + image gen + animation

### User's Likely Use Case
- Spanish documentary voiceover (22 segments)
- Possible video animation (Steady Dancer)
- Budget-conscious (user tracks pricing carefully)
- Existing ComfyUI familiarity

---

*Local research complete. Web research phase needed for A100 vs L40S comparison and Steady Dancer requirements.*
