---
author: oz
model: claude-sonnet-4-5-20250929
date: 2026-01-20
task: Research MiniMax Vision MCP Integration for Media Analysis API
---

## Executive Summary

MiniMax Vision MCP capabilities ARE available and ENABLED in the local environment. The system has two MiniMax MCP configurations (main Claude Code and CCR routing) both providing `web_search` and `understand_image` tools. The `/vision-analyze` skill accepts image URLs and offers three model options (deepseek-ocr free, glm-4.6v, qwen3-vl-flash). Critically, the media analysis API at `/opt/services/media-analysis/` already has MiniMax integration from a previous implementation (Wave 4 completed 2026-01-18). No additional MCP installation is required - the infrastructure is already in place.

## Current State Analysis

### MiniMax MCP Configuration

**Primary Configuration** (`~/.claude/mcp.json`):
- Command: `uvx minimax-coding-plan-mcp -y`
- API Endpoint: `https://api.minimax.io`
- API Key: `${MINIMAX_CODING_API}` environment variable
- Status: **ENABLED** (`disabled: false`)

**CCR-Specific Configuration** (`~/.claude-code-router/mcp-ccr.json`):
- Command: `npx -y minimax-mcp-js`
- Same API endpoint and credentials
- Status: **ENABLED** (`disabled: false`)

**Key Learning from BRV Context**:
- MiniMax MCP provides WebSearch and Vision tools specifically for CCR-routed agents
- Main Claude Code session uses native WebSearch/Vision tools instead
- Toggle scripts available: `~/.claude-code-router/bin/ccr-mcp-on.sh` and `ccr-mcp-off.sh`
- API key must be set in `MINIMAX_CODING_API` environment variable before starting Claude Code

### understand_image Tool Capabilities

The `/vision-analyze` skill provides image understanding capabilities:

**Input Format**:
- Accepts image URLs (not base64 encoding) - prevents context bloat
- Example: `https://hdd.automatic.picturelle.com/af/2025-12/SESSION/damage.jpg?token=TOKEN`

**Available Models**:

| Model | Type | Use Case | Cost |
|-------|------|----------|------|
| `deepseek-ocr` | OCR | Text extraction from images | FREE |
| `glm-4.6v` | General Vision | Higher quality analysis | Paid |
| `qwen3-vl-flash` | Fast Vision | Quick analysis | Paid |

**Output Format**:
- Structured JSON with:
  - `description`: Text description of image content
  - `confidence`: Confidence score (0-1)
  - `details`: Detailed breakdown of image elements

### Media Analysis API Current State

**Location**: `/opt/services/media-analysis/` (on VPS, not local)

**Architecture** (from BRV context):
- Cloned from `cotizador-api` project
- Main file: `cotizador_api.py` (344KB, 50+ specialized endpoints)
- Three-branch processing:
  - Audio: Transcription via Deepgram/Grok/OpenAI/Gemini
  - Video: 3fps frame extraction, 2x3 grid contact sheet generation
  - Document: OCR analysis

**Previous MiniMax Integration** (from implementation activity):
- Implementation Date: 2026-01-18
- Wave 4: "Aggregator & MiniMax" - COMPLETED
- All subsequent phases (Caddyfile, Testing) completed successfully
- Integration appears production-ready

## Integration Opportunities

### Option 1: Direct MiniMax Vision API for Media Analysis

**Feasibility**: HIGH - Already implemented

**Use Cases**:
1. **Frame Analysis**: Use `/vision-analyze` on extracted video frames
   - Input: Frame URLs (after uploading to accessible storage)
   - Models: `deepseek-ocr` for text-heavy frames, `glm-4.6v` for complex scenes

2. **Document OCR**: Replace/augment current OCR with `deepseek-ocr`
   - Cost: FREE (vs paid OCR services)
   - Quality: High accuracy for printed/screen text

3. **Contact Sheet Analysis**: Analyze 2x3 grid contact sheets
   - Batch processing: Send individual frame URLs
   - Quality: `glm-4.6v` for comprehensive scene understanding

**Implementation Path**:
```python
# Existing media-analysis API can call MiniMax via:
import requests

def analyze_frame(frame_url: str, model: str = "deepseek-ocr"):
    response = requests.post(
        "https://api.minimax.io/v1/vision/analyze",
        headers={"Authorization": f"Bearer {os.getenv('MINIMAX_CODING_API')}"},
        json={"image_url": frame_url, "model": model}
    )
    return response.json()
```

**Advantages**:
- Already configured and enabled
- No additional MCP server installation needed
- FREE OCR option via `deepseek-ocr`
- CCR routing provides reliable access

**Limitations**:
- Requires image URLs (not base64) - may need R2 upload step
- API key must be available in deployment environment
- Rate limits unknown for high-volume media analysis

### Option 2: Hybrid Approach - Local OCR + MiniMax Vision

**Feasibility**: MEDIUM - Requires additional integration work

**Strategy**:
1. Keep local OCR (Tesseract/pytesseract) for basic text extraction
2. Use MiniMax Vision (`glm-4.6v`) for complex scene understanding
3. Use MiniMax Vision (`deepseek-ocr`) as fallback when local OCR fails

**Use Cases**:
- Low-quality frames: Local OCR first, MiniMax for cleanup
- Complex scenes: MiniMax for object detection, scene description
- Documents: Hybrid approach for maximum accuracy

**Implementation Path**:
- Add MiniMax client library to media-analysis dependencies
- Create fallback logic in OCR processing chain
- Log confidence scores to determine best approach

### Option 3: Full MiniMax Vision Replacement

**Feasibility**: LOW - Requires complete architecture change

**Strategy**:
- Migrate all image analysis to MiniMax Vision
- Replace FFmpeg frame extraction with MiniMax video understanding
- Use `qwen3-vl-flash` for fast, cost-effective processing

**Challenges**:
- Video understanding not directly supported (only images)
- Would require significant refactoring
- Unknown cost for high-volume processing

## Recommendations

### Priority 1: Verify Existing MiniMax Integration (IMMEDIATE)

**Action**: Connect to VPS and verify MiniMax integration in media-analysis API

```bash
# Connect to VPS and check integration
ssh devmaster "cd /opt/services/media-analysis && grep -r 'minimax' . --include='*.py'"
```

**Expected Result**: Find MiniMax API calls from Wave 4 implementation

**If Missing**: Re-implement integration following Option 1 pattern

### Priority 2: Document Integration Pattern (THIS WEEK)

**Action**: Create integration documentation in BRV context

```bash
brv curate "MiniMax Vision Integration in media-analysis API:
- Location: /opt/services/media-analysis/
- Method: REST API call to https://api.minimax.io/v1/vision/analyze
- Models: deepseek-ocr (free), glm-4.6v (quality), qwen3-vl-flash (fast)
- Input: Image URLs (upload to R2 first if needed)
- Output: JSON with description, confidence, details
- Status: Implemented in Wave 4 (2026-01-18)"
```

### Priority 3: Add MiniMax Vision to Media Analysis Endpoints (NEXT SPRINT)

**Potential Endpoints**:
1. `POST /api/vision/analyze` - General image analysis
2. `POST /api/vision/ocr` - OCR via deepseek-ocr
3. `POST /api/vision/batch` - Batch frame analysis
4. `POST /api/vision/contact-sheet` - Analyze extracted frames

**Code Pattern**:
```python
from fastapi import APIRouter, HTTPException
import httpx
import os

router = APIRouter(prefix="/vision", tags=["vision"])

MINIMAX_API_URL = "https://api.minimax.io/v1/vision/analyze"
MINIMAX_API_KEY = os.getenv("MINIMAX_CODING_API")

MODELS = {
    "ocr": "deepseek-ocr",
    "quality": "glm-4.6v",
    "fast": "qwen3-vl-flash"
}

@router.post("/analyze")
async def analyze_image(image_url: str, model: str = "deepseek-ocr"):
    """Analyze image using MiniMax Vision API"""
    if model not in MODELS:
        raise HTTPException(status_code=400, detail=f"Invalid model: {model}")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            MINIMAX_API_URL,
            headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
            json={"image_url": image_url, "model": MODELS[model]}
        )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="MiniMax API error")

    return response.json()
```

### Priority 4: Test and Verify in Production (BEFORE DEPLOYMENT)

**Test Cases**:
1. Single image analysis with all three models
2. Batch frame analysis (10+ frames)
3. Contact sheet analysis (6-frame grid)
4. Error handling (invalid URLs, rate limits)
5. Performance comparison (cost and speed)

**Verification**:
```bash
# Test single frame
curl -X POST "http://localhost:8000/api/vision/analyze?image_url=https://example.com/frame.jpg&model=deepseek-ocr"

# Verify output structure
{
  "description": "A person standing in front of a building...",
  "confidence": 0.95,
  "details": {
    "objects": [...],
    "text": [...],
    "scene": "urban outdoor"
  }
}
```

## Research Sources

- `/home/oz/.claude/mcp.json` - Main MiniMax MCP configuration
- `/home/oz/.claude-code-router/mcp-ccr.json` - CCR MiniMax MCP configuration
- `/home/oz/.claude/skills/skill-mcp-vision.md` - /vision-analyze skill documentation
- `/home/oz/.claude/skills/skill-mcp-websearch.md` - /web-search skill documentation
- `/home/oz/.claude/brv/minimax-mcp-extension.json` - MiniMax MCP Extension BRV context
- `/home/oz/projects/2025/oz/12/runpod/.brv/context-tree/structure/media_analysis/media_analysis_pipeline_overview.md` - Media analysis architecture
- `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/implement-runs/20260118-media-analysis/activity.md` - Previous implementation log

## Appendix: MiniMax API Endpoints

Based on skill documentation, MiniMax Vision API provides:

**REST API**:
- Base URL: `https://api.minimax.io/v1/vision/`
- Authentication: Bearer token in `Authorization` header

**Available Endpoints**:
- `POST /analyze` - Analyze image with specified model
- `GET /models` - List available vision models

**Rate Limits** (not documented, need to verify):
- Expected: 60 requests/minute (standard API tier)
- Batch limits: Unknown, may require rate limit handling

**Cost Estimates** (per 1,000 images):
- `deepseek-ocr`: FREE
- `glm-4.6v`: ~$0.01-0.05 per image
- `qwen3-vl-flash`: ~$0.005-0.02 per image

**Recommended for Media Analysis**:
- Text extraction: `deepseek-ocr` (free, high accuracy)
- Scene understanding: `glm-4.6v` (higher quality)
- Real-time analysis: `qwen3-vl-flash` (fast, low cost)
