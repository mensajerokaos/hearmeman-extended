# Plan: runpod-ma-27 - MiniMax Vision MCP Research (REFINED)

## Objective
Research MiniMax MCP integration for vision/image analysis capabilities and produce actionable recommendation.

## Version History
- **v0.1**: Initial draft
- **v1.0 (current)**: Production-ready with all plan02 refinements

## Research Areas

### 1. MiniMax API Capabilities
- Check official MiniMax documentation via WebFetch
- Verify if vision/image analysis is supported
- Identify any vision-specific endpoints or models
- **NEW**: Check model versioning and deprecation policy

### 2. MCP Server Configuration
- Check `/home/oz/.claude/mcp-servers/` for existing MiniMax configuration
- Review understand_image tool capabilities
- Document required API parameters for vision tasks
- **NEW**: Check if existing MCP server supports vision or needs extension

### 3. Integration Viability Assessment
- Cost comparison vs current fallback providers
- Latency expectations
- Accuracy benchmarks (if available)
- **NEW**: Define explicit decision thresholds (not subjective High/Medium/Low)
- **NEW**: Add Qwen3-VL baseline comparison

### 4. Implementation Requirements
- API endpoint for vision requests
- Required parameters (image URL/base64, prompt)
- Response format
- Error handling
- **NEW**: Risk assessment framework

---

## Research Steps (Enhanced with plan02 Refinements)

### Step 1: Documentation Review
```bash
# Fetch official MiniMax API documentation (NOT just search)
WebFetch: "https://api.minimax.chat/docs/"

# Search for vision-related capabilities
WebSearch: "MiniMax API vision image analysis 2025"

# Check MCP servers for existing configuration
ls -la /home/oz/.claude/mcp-servers/

# Check for MiniMax MCP configuration
cat /home/oz/.claude/mcp-servers/*minimax* 2>/dev/null || echo "No MiniMax MCP config found"

# Review current MiniMax provider configuration
grep -r "minimax" /home/oz/projects/2025/oz/12/runpod/.env 2>/dev/null | head -20
```

### Step 2: Current Capability Analysis
```bash
# Test MiniMax text-only API (current state)
curl -X POST "https://api.minimax.chat/v1/text/chatcompletion_v2" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "abab6.5s-chat",
    "messages": [{"role": "user", "content": "Hello, what is MiniMax?"}]
  }' | jq '.'
```

**NEW - Baseline Measurement:**
```bash
# Establish Qwen3-VL baseline for comparison
echo "=== Qwen3-VL Baseline ==="
time curl -X POST "http://localhost:8050/api/media/documents" \
  -H "Content-Type: application/json" \
  -d '{"document_url": "<TEST_IMAGE>", "prompt": "Describe this image"}' \
  | jq '{latency: .processing_time, model: .model}'
```

### Step 3: Direct API Vision Test
```bash
# Test MiniMax with image input (vision capability test)
curl -X POST "https://api.minimax.chat/v1/text/chatcompletion_v2" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "abab6.5s-chat",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this image"},
        {"type": "image_url", "image_url": {"url": "<TEST_IMAGE>"}}
      ]
    }]
  }'
```

**Record Results:**
- Does API accept image_url content type?
- What error message (if any)?
- What is the response format?
- What are rate limits for vision requests?

### Step 4: Cost Comparison Analysis

**NEW - Explicit Cost Comparison Table:**

| Provider | Model | Cost/1K tokens (input) | Cost/1K tokens (output) | Cost/image (est.) |
|----------|-------|------------------------|-------------------------|-------------------|
| MiniMax | abab6.5s-chat (vision?) | TBD | TBD | TBD |
| Qwen3-VL | qwen3-vl-30b-a3b | ~$0.001 | ~$0.002 | ~$0.01 |
| OpenAI | gpt-4o-mini | $0.15 | $0.60 | ~$0.01 |
| Google | gemini-1.5-flash | $0.075 | $0.30 | ~$0.003 |

**Cost Analysis Methodology:**
1. Fetch current pricing from official sources
2. Calculate per-image cost for typical request (500 input tokens, 1000 output tokens)
3. Compare at 100/1000/10000 images/month volume tiers
4. Account for any minimum charges or free tiers

### Step 5: Integration Complexity Assessment

**NEW - Weighted Decision Framework:**

| Criterion | Weight | MiniMax Score (1-5) | Weighted Score |
|-----------|--------|---------------------|----------------|
| Vision capability exists | 30% | _/5 | _/1.5 |
| Cost per image | 25% | _/5 | _/1.25 |
| Latency (speed) | 20% | _/5 | _/1.0 |
| Documentation quality | 10% | _/5 | _/0.5 |
| MCP integration ease | 10% | _/5 | _/0.5 |
| Stability/reliability | 5% | _/5 | _/0.25 |

**Decision Thresholds:**
- **GO (Proceed)**: Weighted score >= 4.0 AND vision capability confirmed
- **CONDITIONAL GO**: Weighted score 3.0-3.9 (mitigate risks first)
- **NO GO**: Weighted score < 3.0 OR no vision capability

### Step 6: Risk Assessment (NEW)

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| MiniMax vision API not available | Medium | High | Use as text-only fallback only |
| Pricing higher than expected | Low | Medium | Recalculate cost comparison |
| Latency too high | Medium | Medium | Set higher timeout, use only as last resort |
| API stability issues | Low | High | Maintain current provider chain |
| Model deprecation | Low | Medium | Version pinning, fallback plan |
| Vendor lock-in | Medium | Low | Keep provider chain flexible |

### Step 7: Findings Documentation

**Deliverable Structure:**

```markdown
## MiniMax Vision Research Report

### 1. Executive Summary
- Vision capability: CONFIRMED / NOT CONFIRMED / UNCERTAIN
- Recommendation: PROCEED / CONDITIONAL PROCEED / DO NOT PROCEED
- Overall Score: _/5.0

### 2. Capabilities Analysis
- Supported models: [...]
- Vision endpoints: [...]
- Input formats: [...]
- Rate limits: [...]

### 3. Cost Analysis
- Per-image cost estimate: $_
- Comparison with Qwen3-VL: _% cheaper / _% more expensive
- Volume discount availability: [...]

### 4. Implementation Requirements
- API endpoint: [...]
- Required parameters: [...]
- Response format: [...]
- Error codes: [...]

### 5. Integration Complexity
- Estimated implementation time: _ hours
- MCP server changes required: YES / NO
- Testing requirements: [...]

### 6. Risk Assessment
- [Risk matrix from above]

### 7. Recommendation
[Detailed recommendation with conditions if any]

### Appendices
- A: API documentation excerpts
- B: Cost calculation details
- C: Test results logs
```

---

## Success Criteria

- [ ] MiniMax vision capabilities documented (confirmed/denied)
- [ ] Integration feasibility determined with explicit score
- [ ] API requirements identified (endpoints, parameters, format)
- [ ] Cost comparison complete with actual numbers
- [ ] Implementation recommendation provided (GO/CONDITIONAL/NO-GO)
- [ ] **NEW**: Qwen3-VL baseline measurement for comparison
- [ ] **NEW**: Weighted decision score calculated
- [ ] **NEW**: Risk assessment with mitigation strategies

---

## Output Deliverables

1. **Research Summary** (`dev/agents/artifacts/doc/research/minimax-vision-summary.md`)
   - One-page executive summary with recommendation

2. **Viability Assessment** (`dev/agents/artifacts/doc/research/minimax-vision-viability.md`)
   - Detailed capabilities analysis
   - Weighted decision framework results

3. **Cost Analysis** (`dev/agents/artifacts/doc/research/minimax-vision-cost.md`)
   - Per-image cost estimates
   - Comparison tables with all providers

4. **Implementation Plan** (if viable) (`dev/agents/artifacts/doc/plan/minimax-vision-impl.md`)
   - API integration steps
   - MCP server modifications
   - Testing requirements

5. **Decision Report** (`dev/agents/artifacts/doc/decision/minimax-vision-decision.md`)
   - GO/CONDITIONAL/NO-GO recommendation
   - Required actions for each decision type

---

**Created:** 2026-01-20
**Version:** 1.0
**Previous Version:** 0.1 (Draft)
**plan02 Refinements Applied:**
- Added WebFetch of official docs (not just WebSearch)
- Added Qwen3-VL baseline measurement
- Added weighted decision framework with explicit thresholds
- Added explicit cost comparison methodology
- Added risk assessment framework
- Added structured deliverable templates
- Added decision criteria (GO/CONDITIONAL/NO-GO with scores)
