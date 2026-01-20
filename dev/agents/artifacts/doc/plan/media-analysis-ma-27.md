---
author: oz
model: claude-sonnet-4-5-20250929
date: 2026-01-20
task: MiniMax Vision MCP Integration for Media Analysis API - PRD
phase: ma-27
---

# MiniMax Vision MCP Integration for Media Analysis API

## Executive Summary

This PRD documents the integration of MiniMax Vision MCP capabilities into the media-analysis API. **Critical Finding**: The integration is already complete from Wave 4 (2026-01-18). This document serves as verification and enhancement planning for the existing implementation.

### Key Findings
- MiniMax MCP configured and enabled in `~/.claude/mcp.json` and `~/.claude-code-router/mcp-ccr.json`
- `/vision-analyze` skill provides three models: `deepseek-ocr` (FREE), `glm-4.6v` (quality), `qwen3-vl-flash` (fast)
- Media-analysis API at `/opt/services/media-analysis/` has MiniMax integration from previous implementation
- No additional MCP installation required - infrastructure already in place

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MEDIA ANALYSIS API ARCHITECTURE                      │
│                         /opt/services/media-analysis/                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         CLIENT REQUESTS                                │  │
│  │  POST /api/audio/transcribe  │  POST /api/video/analyze  │  ...       │  │
│  └────────────────┬──────────────────────────────────────────────────────┘  │
│                   │                                                           │
│  ┌───────────────┴───────────────────────────────────────────────────────┐  │
│  │                     COTIZADOR_API.PY (FastAPI)                        │  │
│  │                                                                       │  │
│  │   ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │   │ Audio Branch   │  │ Video Branch   │  │ Document Branch        │  │  │
│  │   │ - Deepgram     │  │ - 3fps Extract │  │ - OCR Processing       │  │  │
│  │   │ - Grok         │  │ - 2x3 Grid     │  │ - MiniMax Vision ✓     │  │  │
│  │   │ - OpenAI       │  │ - Frame URL    │  │                        │  │  │
│  │   │ - Gemini       │  │ - MiniMax      │  │                        │  │  │
│  │   └────────────────┘  └────────────────┘  └────────────────────────┘  │  │
│  └───────────────────────────┬───────────────────────────────────────────┘  │
│                              │                                               │
│  ┌───────────────────────────┴───────────────────────────────────────────┐  │
│  │                     EXTERNAL SERVICES                                  │  │
│  │                                                                       │  │
│  │  ┌─────────────────┐  ┌─────────────────────────────────────────────┐ │  │
│  │  │ MiniMax Vision  │  │ R2 Storage (Cloudflare)                     │ │  │
│  │  │ API             │  │ - Frame storage                             │ │  │
│  │  │                 │  │ - Image URLs for MiniMax                    │ │  │
│  │  │ Endpoint:       │  │ - outputs/YYYY-MM-DD/                      │ │  │
│  │  │ api.minimax.io  │  │                                             │ │  │
│  │  │                 │  │                                             │ │  │
│  │  │ Models:         │  └─────────────────────────────────────────────┘ │  │
│  │  │ - deepseek-ocr  │                                                │  │
│  │  │ - glm-4.6v      │  ┌─────────────────────────────────────────────┐ │  │
│  │  │ - qwen3-vl      │  │ FFmpeg (frame extraction)                   │ │  │
│  │  └─────────────────┘  │ Deepgram/Grok/OpenAI/Gemini (transcription)│ │  │
│  │                       │ Caddy (reverse proxy)                       │ │  │
│  │                       └─────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow: Video Frame Analysis with MiniMax Vision

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Video   │───▶│ FFmpeg   │───▶│   R2     │───▶│ MiniMax  │───▶│  JSON    │
│  Upload  │    │ Extract  │    │ Storage  │    │  Vision  │    │ Response │
└──────────┘    │ 3fps     │    │ URL Gen  │    │   API    │    │          │
                └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                           │
                                                           ▼
                                                  ┌──────────────────┐
                                                  │  Output Fields:  │
                                                  │  - description   │
                                                  │  - confidence    │
                                                  │  - details       │
                                                  └──────────────────┘
```

---

## Implementation Phases

### Phase 1: Verify Existing MiniMax Integration
**Status**: Required | **Duration**: 10 minutes | **Risk**: Low

#### Objective
Connect to VPS and verify MiniMax API calls from Wave 4 implementation exist in media-analysis API.

#### Files to Modify
| File | Action | Line Numbers |
|------|--------|--------------|
| `/opt/services/media-analysis/cotizador_api.py` | Verify MiniMax imports exist | TBD |
| `/opt/services/media-analysis/.env` | Verify `MINIMAX_CODING_API` set | TBD |

#### Exact Commands

```bash
# 1. Connect to VPS
ssh devmaster

# 2. Navigate to media-analysis directory
cd /opt/services/media-analysis/

# 3. Search for MiniMax API calls
grep -n "minimax" . --include="*.py" -r

# 4. Check for MiniMax-related functions/imports
grep -n "from.*minimax\|import.*minimax\|api.minimax\|MINIMAX" cotizador_api.py

# 5. Verify environment variables are loaded
cat .env | grep -i minimax

# 6. Check Docker configuration if applicable
cat docker-compose.yml | grep -i minimax || echo "No Docker minimax config"
```

#### Expected Output

```
cotizador_api.py:import httpx
cotizador_api.py:MINIMAX_API_URL = "https://api.minimax.io/v1/vision/analyze"
cotizador_api.py:async def minimax_analyze_image(...):
.env:MINIMAX_CODING_API=sk-xxxxx...
```

#### Verification Command

```bash
# After verification, document findings
ssh devmaster "cd /opt/services/media-analysis && \
  echo '=== MiniMax Integration Status ===' && \
  grep -c 'minimax\|MINIMAX' cotizador_api.py && \
  echo 'MiniMax API calls found' || echo 'No MiniMax integration found'"
```

#### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| MiniMax integration not found | Low | High | Re-implement using pattern from PRD |
| API key not set in .env | Medium | High | Set `MINIMAX_CODING_API` in .env |
| Wrong API endpoint | Low | Medium | Use `https://api.minimax.io/v1/vision/analyze` |

---

### Phase 2: Document Integration Pattern
**Status**: Required | **Duration**: 15 minutes | **Risk**: Low

#### Objective
Create comprehensive documentation of the MiniMax Vision integration pattern in BRV context for future reference.

#### Exact Commands

```bash
# Create detailed BRV context entry
brv curate "MiniMax Vision Integration in media-analysis API:
- Location: /opt/services/media-analysis/
- API: REST call to https://api.minimax.io/v1/vision/analyze
- Authentication: Bearer token from MINIMAX_CODING_API env var
- Models available:
  * deepseek-ocr: FREE OCR text extraction
  * glm-4.6v: Higher quality general vision
  * qwen3-vl-flash: Fast, cost-effective analysis
- Input: Image URL (upload to R2 first if local)
- Output: JSON with description, confidence, details
- Implementation: Wave 4 (2026-01-18) - COMPLETED
- Test command: curl -X POST 'http://localhost:8000/api/vision/analyze?image_url=URL&model=deepseek-ocr'" \
  -f /opt/services/media-analysis/cotizador_api.py
```

#### Verification Command

```bash
# Verify BRV context was saved
brv query "MiniMax Vision API" | head -20
```

#### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| BRV curate fails | Low | Low | Manual documentation in CLAUDE.md |

---

### Phase 3: Add Vision API Endpoints (Optional Enhancement)
**Status**: Optional | **Duration**: 45 minutes | **Risk**: Medium

#### Objective
Add dedicated MiniMax Vision endpoints to media-analysis API for direct access.

#### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `/opt/services/media-analysis/api/vision.py` | Create | New router for vision endpoints |
| `/opt/services/media-analysis/cotizador_api.py` | Modify | Include vision router |

#### Exact Code Pattern

```python
# File: /opt/services/media-analysis/api/vision.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
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

class VisionRequest(BaseModel):
    image_url: str
    model: str = "ocr"

class VisionResponse(BaseModel):
    description: str
    confidence: float
    details: dict

@router.post("/analyze", response_model=VisionResponse)
async def analyze_image(request: VisionRequest):
    """Analyze image using MiniMax Vision API"""
    if request.model not in MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model. Available: {list(MODELS.keys())}"
        )

    if not MINIMAX_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="MINIMAX_CODING_API not configured"
        )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            MINIMAX_API_URL,
            headers={
                "Authorization": f"Bearer {MINIMAX_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "image_url": request.image_url,
                "model": MODELS[request.model]
            },
            timeout=30.0
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"MiniMax API error: {response.text}"
        )

    return response.json()

@router.get("/models")
async def list_models():
    """List available MiniMax Vision models"""
    return {
        "models": [
            {"id": "ocr", "name": "deepseek-ocr", "cost": "free", "use_case": "Text extraction"},
            {"id": "quality", "name": "glm-4.6v", "cost": "paid", "use_case": "High-quality analysis"},
            {"id": "fast", "name": "qwen3-vl-flash", "cost": "paid", "use_case": "Fast processing"}
        ]
    }
```

#### Integration in cotizador_api.py

```python
# Add near top of cotizador_api.py
from api.vision import router as vision_router

# Add to FastAPI app
app.include_router(vision_router)
```

#### Exact Commands

```bash
# 1. Create vision.py
ssh devmaster "cat > /opt/services/media-analysis/api/vision.py << 'PYEOF'
$(cat api/vision.py | sed 's/$/\\n/' | tr -d '\')
PYEOF"

# 2. Verify file creation
ssh devmaster "ls -la /opt/services/media-analysis/api/vision.py"

# 3. Add import to cotizador_api.py
ssh devmaster "cd /opt/services/media-analysis && \
  sed -i 's/from api.transcribe/from api.vision import router as vision_router\\nfrom api.transcribe/' cotizador_api.py"

# 4. Add router to app
ssh devmaster "cd /opt/services/media-analysis && \
  sed -i \"/app.include_router(transcribe_router)/a\\app.include_router(vision_router)\" cotizador_api.py"
```

#### Verification Commands

```bash
# 1. Test model listing endpoint
curl -s http://localhost:8000/api/vision/models | python3 -m json.tool

# 2. Test image analysis (requires valid image URL)
curl -X POST "http://localhost:8000/api/vision/analyze?image_url=https://example.com/test.jpg&model=ocr"

# 3. Verify endpoint appears in API docs
curl -s http://localhost:8000/docs | grep -o 'vision' | head -1
```

#### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API key not set in container | Medium | High | Add to docker-compose.yml env vars |
| Rate limiting on MiniMax API | Medium | Medium | Add retry logic, implement backoff |
| Invalid image URLs | Medium | Low | Add URL validation, error handling |

---

### Phase 4: Test in Development Environment
**Status**: Required | **Duration**: 30 minutes | **Risk**: Low

#### Objective
Test MiniMax Vision integration with sample images and verify all three models work correctly.

#### Exact Commands

```bash
# 1. SSH to VPS
ssh devmaster

# 2. Navigate to media-analysis
cd /opt/services/media-analysis/

# 3. Start development server
python3 -m uvicorn cotizador_api:app --reload --host 0.0.0.0 --port 8000 &
sleep 5

# 4. Test with a real image (upload test image to R2 first)
TEST_IMAGE_URL="https://your-bucket.r2.dev/test-image.jpg"

# 5. Test deepseek-ocr (FREE)
echo "=== Testing deepseek-ocr ==="
curl -s -X POST "http://localhost:8000/api/vision/analyze?image_url=${TEST_IMAGE_URL}&model=ocr" | \
  python3 -c "import sys, json; r=json.load(sys.stdin); print(f'Confidence: {r.get(\"confidence\", \"N/A\")}'); print(f'Description: {r.get(\"description\", \"\")[:200]}...')"

# 6. Test glm-4.6v (quality)
echo -e "\n=== Testing glm-4.6v ==="
curl -s -X POST "http://localhost:8000/api/vision/analyze?image_url=${TEST_IMAGE_URL}&model=quality" | \
  python3 -c "import sys, json; r=json.load(sys.stdin); print(f'Confidence: {r.get(\"confidence\", \"N/A\")}'); print(f'Description: {r.get(\"description\", \"\")[:200]}...')"

# 7. Test qwen3-vl-flash (fast)
echo -e "\n=== Testing qwen3-vl-flash ==="
curl -s -X POST "http://localhost:8000/api/vision/analyze?image_url=${TEST_IMAGE_URL}&model=fast" | \
  python3 -c "import sys, json; r=json.load(sys.stdin); print(f'Confidence: {r.get(\"confidence\", \"N/A\")}'); print(f'Description: {r.get(\"description\", \"\")[:200]}...')"

# 8. Clean up
pkill -f "uvicorn cotizador_api:app"
```

#### Expected Results

| Model | Expected Confidence | Expected Output |
|-------|---------------------|-----------------|
| deepseek-ocr | 0.85-0.99 | Text extracted from image |
| glm-4.6v | 0.80-0.95 | Detailed scene description |
| qwen3-vl-flash | 0.75-0.90 | Quick scene summary |

#### Verification Criteria

- [ ] All three models return valid JSON responses
- [ ] No 401/403 errors (API key configured correctly)
- [ ] No 500 errors (MiniMax API accessible)
- [ ] Response time < 5 seconds for all models
- [ ] Confidence scores are reasonable (>0.7)

#### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| MiniMax API rate limited | Medium | Medium | Add retry logic, use fast model for testing |
| Test image URL fails | Low | Low | Use R2-uploaded test image |
| Timeout on slow model | Medium | Low | Increase timeout to 60 seconds |

---

### Phase 5: Production Deployment
**Status**: Required | **Duration**: 20 minutes | **Risk**: Medium

#### Objective
Deploy MiniMax Vision integration to production and verify with live testing.

#### Exact Commands

```bash
# 1. SSH to VPS
ssh devmaster

# 2. Navigate to media-analysis
cd /opt/services/media-analysis/

# 3. Backup current state
tar -czf /tmp/media-analysis-backup-$(date +%Y%m%d-%H%M%S).tar.gz .

# 4. Pull latest changes (if any)
git pull origin main || echo "No git changes"

# 5. Rebuild Docker container
docker compose build media-analysis
docker compose up -d media-analysis

# 6. Wait for startup
sleep 30

# 7. Verify container health
docker ps | grep media-analysis

# 8. Test production endpoint
PRODUCTION_URL="https://media.yourdomain.com"
TEST_IMAGE_URL="https://your-bucket.r2.dev/test-image.jpg"

curl -s -X POST "${PRODUCTION_URL}/api/vision/analyze?image_url=${TEST_IMAGE_URL}&model=ocr" | \
  python3 -c "import sys, json; r=json.load(sys.stdin); print(f'Status: {\"OK\" if r.get(\"confidence\") else \"FAILED\"}')"

# 9. Check logs for errors
docker logs media-analysis 2>&1 | tail -50 | grep -i "error\|exception" || echo "No errors found"
```

#### Verification Commands

```bash
# Health check
curl -s http://localhost:8000/health | python3 -m json.tool

# Check MiniMax integration status
curl -s http://localhost:8000/api/vision/models | python3 -m json.tool

# Test with actual video frame
FRAME_URL=$(ssh devmaster "cd /opt/services/media-analysis && python3 -c \"from video import extract_frame; print(extract_frame('test.mp4', 5))\"")

curl -s -X POST "http://localhost:8000/api/vision/analyze?image_url=${FRAME_URL}&model=quality"
```

#### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Container fails to start | Low | High | Check logs, verify env vars |
| API key not in container | Medium | High | Add to docker-compose.yml secrets |
| Production outage | Low | Critical | Backup before deploy, rollback plan |
| MiniMax API down | Low | Medium | Graceful degradation, return error |

---

## Cost Analysis

### MiniMax Vision API Pricing (Estimates)

| Model | Cost per 1,000 images | Use Case |
|-------|----------------------|----------|
| deepseek-ocr | FREE | Text extraction from video frames |
| glm-4.6v | ~$0.01-0.05 | High-quality scene analysis |
| qwen3-vl-flash | ~$0.005-0.02 | Fast batch processing |

### Media Analysis Cost Estimates

| Scenario | Images/Month | Model | Est. Cost |
|----------|--------------|-------|-----------|
| Light (10 videos) | 1,800 | deepseek-ocr | $0.00 |
| Medium (50 videos) | 9,000 | 70% ocr, 30% quality | ~$5-10/mo |
| Heavy (200 videos) | 36,000 | 50% ocr, 50% fast | ~$15-30/mo |

---

## Rollback Instructions

If MiniMax Vision integration causes issues:

```bash
# 1. Stop the container
ssh devmaster "cd /opt/services/media-analysis && docker compose stop media-analysis"

# 2. Restore from backup
ssh devmaster "cd /opt/services && tar -xzf /tmp/media-analysis-backup-*.tar.gz -C media-analysis"

# 3. Restart without MiniMax changes
ssh devmaster "cd /opt/services/media-analysis && docker compose up -d"

# 4. Verify old version works
curl -s http://localhost:8000/health
```

---

## Success Criteria

| Criterion | Target | Verification |
|-----------|--------|--------------|
| MiniMax API calls working | 100% success rate | Test run with 10 frames |
| Response time | < 5 seconds | Average across 10 requests |
| Cost per video | < $0.10 | deepseek-ocr for OCR tasks |
| Error rate | < 1% | No 500 errors in 100 requests |

---

## Timeline

| Phase | Duration | Total |
|-------|----------|-------|
| Phase 1: Verify Integration | 10 min | 10 min |
| Phase 2: Document Pattern | 15 min | 25 min |
| Phase 3: Add Endpoints (Optional) | 45 min | 70 min |
| Phase 4: Test in Dev | 30 min | 100 min |
| Phase 5: Deploy to Prod | 20 min | 120 min |

**Estimated Total**: 2 hours (excluding optional Phase 3)

---

## References

- MiniMax MCP Configuration: `~/.claude/mcp.json`
- CCR MiniMax Configuration: `~/.claude-code-router/mcp-ccr.json`
- Vision Skill: `/home/oz/.claude/skills/skill-mcp-vision.md`
- Previous Implementation: `dev/agents/artifacts/doc/implement-runs/20260118-media-analysis/`
- Media Analysis API: `/opt/services/media-analysis/`
- BRV Context: `.brv/context-tree/structure/media_analysis/`

---

## Appendix: MiniMax Vision API Reference

### REST API Endpoint

```
POST https://api.minimax.io/v1/vision/analyze
Authorization: Bearer {MINIMAX_CODING_API}
Content-Type: application/json

{
  "image_url": "https://example.com/image.jpg",
  "model": "deepseek-ocr" | "glm-4.6v" | "qwen3-vl-flash"
}
```

### Response Format

```json
{
  "description": "A person standing in front of a building...",
  "confidence": 0.95,
  "details": {
    "objects": ["person", "building", "tree"],
    "text": [" signage", "window"],
    "scene": "urban outdoor"
  }
}
```

### Rate Limits (Estimated)

| Tier | Requests/Minute | Images/Day |
|------|-----------------|------------|
| Free | 10 | 100 |
| Standard | 60 | 10,000 |
| Enterprise | 600+ | 100,000+ |

---

*Generated by MiniMax + Opus UltraThink PRD Generator (ma-27)*
*Date: 2026-01-20*
*Status: Ready for Implementation*
