---
task: runpod-ma-27 MiniMax Vision MCP Research
agent: hc (headless claude)
model: claude-opus-4-5-20251101
timestamp: 2026-01-20T12:00:00Z
status: completed
---

# runpod-ma-27: MiniMax Vision MCP Research

## Overview
Determine if MiniMax API supports vision/image analysis for potential integration into the media-analysis-api fallback chain.

**Current fallback chain reference:**
```
VISION: Qwen3-VL → Gemini 2.5 Flash → GPT-5 Mini → MiniMax (text-only)
```

MiniMax is currently marked as "text-only" - this research validates that assumption.

## Research Steps

### Step 1: Check MiniMax Documentation
```bash
# WebSearch for MiniMax vision/multimodal capabilities
# Keywords: "MiniMax API vision", "MiniMax image analysis", "MiniMax multimodal"

# Check existing MCP config
cat ~/.claude/mcp-servers/*minimax* 2>/dev/null || echo "No MiniMax MCP config found"
```

**Expected findings:**
- Does MiniMax offer vision endpoints?
- Which models support image input (if any)?
- API endpoint structure for vision requests

### Step 2: Test Vision API (if supported)
```bash
# Only run if Step 1 finds vision support
curl -X POST "https://api.minimax.chat/v1/text/chatcompletion_v2" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "abab6.5s-chat",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "image_url", "image_url": {"url": "https://example.com/test.jpg"}},
        {"type": "text", "text": "Describe this image"}
      ]
    }]
  }'
```

**Expected response:**
- 200 OK with description = vision supported
- 400/422 error = vision not supported for this model

### Step 3: Document Findings
Write to: `dev/agents/artifacts/doc/research/minimax-vision-findings.md`

**Required content:**
- Vision supported: YES/NO
- If YES: endpoint, model name, parameters, estimated cost/token
- If NO: confirmed text-only
- Recommendation: INTEGRATE / SKIP (with one-line rationale)

## Output
Single file: `dev/agents/artifacts/doc/research/minimax-vision-findings.md`

## Success Criteria
- [ ] Determined if MiniMax supports vision input
- [ ] Clear GO/NO-GO recommendation for vision fallback integration
