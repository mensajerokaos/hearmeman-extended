# Plan: runpod-ma-27 - MiniMax Vision MCP Research (Improved)

## Objective
Research MiniMax MCP integration for vision/image analysis capabilities and evaluate as potential fallback/primary provider.

---

## Research Areas

### 1. MiniMax API Capabilities
- [ ] Official MiniMax API documentation (vision/multimodal endpoints)
- [ ] Supported image formats (base64, URLs, file uploads)
- [ ] Model variants with vision support (abab6.5s-chat, abab6.5-chat, etc.)
- [ ] Context window limits for image inputs
- [ ] Rate limits and quotas for vision requests
- [ ] Supported output formats (JSON, plain text, structured)

### 2. MCP Server Configuration
- [ ] Existing MiniMax MCP server at `/home/oz/.claude/mcp-servers/`
- [ ] `understand_image` tool capabilities and parameters
- [ ] Image preprocessing requirements (resizing, compression, format conversion)
- [ ] Required environment variables and secrets
- [ ] Error codes and handling patterns

### 3. Provider Comparison Matrix
| Provider | Model | Input Cost/1K tokens | Output Cost/1K tokens | Latency (avg) | Max Images/Request |
|----------|-------|---------------------|----------------------|---------------|-------------------|
| MiniMax | abab6.5s-chat | ? | ? | ? | ? |
| OpenAI | gpt-4o | $5.00 | $15.00 | ~1s | 1 |
| Anthropic | Claude 3.5 Sonnet | $3.00 | $15.00 | ~1.5s | 1 |
| Google | Gemini 1.5 Pro | $1.25 | $5.00 | ~2s | 16 |

### 4. Integration Requirements
- [ ] API endpoint discovery (chatcompletion_v2 or vision-specific)
- [ ] Required authentication parameters
- [ ] Image encoding requirements (base64 schema, max file size)
- [ ] Prompt engineering for optimal vision results
- [ ] Response parsing logic
- [ ] Fallback mechanism design

---

## Research Steps

### Step 1: Documentation Review
```bash
# Official MiniMax documentation
WebSearch: "MiniMax API vision multimodal documentation 2025"
WebSearch: "MiniMax abab6.5s-chat image input parameters"
WebSearch: "MiniMax API pricing vision tasks"

# MCP server exploration
ls -la /home/oz/.claude/mcp-servers/
cat /home/oz/.claude/mcp-servers/*minimax* 2>/dev/null

# Community implementations
WebSearch: "MiniMax MCP server GitHub vision implementation"
WebSearch: "MiniMax multimodal API examples Python curl"
```

### Step 2: Current Provider Analysis
```bash
# Check current fallback providers in environment
grep -r "OPENAI_API_KEY\|ANTHROPIC_API_KEY\|GOOGLE_API_KEY" /home/oz/projects/2025/oz/12/runpod/.env 2>/dev/null

# Check MCP server configurations
cat /home/oz/.claude/mcp-servers/*.json 2>/dev/null | jq '.[] | select(.name | contains("vision") or contains("image"))'

# Review existing vision workflow configurations
find /home/oz/projects/2025/oz/12/runpod -name "*.json" -path "*/workflows/*" | xargs grep -l "image" 2>/dev/null
```

### Step 3: API Testing Protocol
```bash
# Test 1: Basic vision capability
curl -X POST "https://api.minimax.chat/v1/text/chatcompletion_v2" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "abab6.5s-chat",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this image in detail"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,<BASE64_ENCODED_IMAGE>"}}
      ]
    }]
  }'

# Test 2: Multiple images (if supported)
curl -X POST "https://api.minimax.chat/v1/text/chatcompletion_v2" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "abab6.5s-chat",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Compare these two images"},
        {"type": "image_url", "image_url": {"url": "<IMAGE1_URL>"}},
        {"type": "image_url", "image_url": {"url": "<IMAGE2_URL>"}}
      ]
    }]
  }'

# Test 3: JSON structured output (if supported)
curl -X POST "https://api.minimax.chat/v1/text/chatcompletion_v2" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "abab6.5s-chat",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Analyze this image and return JSON with: description, objects[], colors[], sentiment"},
        {"type": "image_url", "image_url": {"url": "<TEST_IMAGE>"}}
      ]
    }],
    "response_format": {"type": "json_object"}
  }'
```

### Step 4: Latency & Throughput Testing
```bash
# Warm-up request
time curl -s -o /dev/null -w "%{http_code}\n" [...]

# Benchmark (5 requests, measure avg latency)
for i in {1..5}; do
  start=$(date +%s%N)
  curl -X POST [...] -o response_$i.json
  end=$(date +%s%N)
  echo "Request $i: $(( (end - start) / 1000000 ))ms"
done

# Calculate tokens/second throughput
jq -r '.usage.total_tokens' response_*.json | awk '{sum+=$1; count++} END {print "Avg tokens/req: " sum/count}'
```

### Step 5: Comparison Analysis
```bash
# Create test image set (sample images)
TEST_IMAGES=(
  "https://example.com/test1.jpg"
  "https://example.com/test2.png"
  "https://example.com/test3.gif"
)

# Run identical tests against:
# 1. MiniMax (test above)
# 2. OpenAI gpt-4o (if API key available)
# 3. Anthropic Claude 3.5 Sonnet (if API key available)

# Document results in comparison matrix
```

---

## Alternative Approaches to Evaluate

### Approach A: MiniMax as Primary Vision Provider
- **Pros**: Lower cost, 75% cheaper than Anthropic
- **Cons**: Unproven reliability for vision tasks
- **Use Case**: High-volume, cost-sensitive image analysis

### Approach B: MiniMax as Fallback (Current Pattern)
- **Pros**: Risk mitigation, provider redundancy
- **Cons**: Additional complexity in routing logic
- **Use Case**: Production systems requiring SLA guarantees

### Approach C: Hybrid Routing
- **Pros**: Best of both worlds, quality-aware routing
- **Cons**: Complex implementation, requires quality metrics
- **Use Case**: Tiered service (basic → MiniMax, complex → Claude)

### Approach D: Local Vision Model Alternative
- **Pros**: No API costs, privacy-preserving
- **Cons**: Requires GPU resources, lower accuracy
- **Use Case**: Batch processing, non-real-time analysis

---

## Decision Framework

### Go/No-Go Criteria

| Criterion | Threshold | Weight |
|-----------|-----------|--------|
| Vision accuracy | ≥80% of Claude 3.5 | 30% |
| Latency | ≤3 seconds | 25% |
| Cost savings | ≥50% vs current | 25% |
| API stability | 99.9% uptime | 10% |
| Documentation quality | Complete | 10% |

**Recommendation Thresholds:**
- **Strong Recommend**: Score ≥85%
- **Recommend with caveats**: Score 70-84%
- **Hold for later**: Score <70%

---

## Output Deliverables

### 1. Research Summary (`runpod-ma-27-research.md`)
- Executive summary (1 paragraph)
- MiniMax vision capabilities overview
- Current provider landscape

### 2. API Comparison Matrix (`vision-providers-comparison.md`)
- Side-by-side provider comparison
- Cost calculator for typical use cases
- Latency percentile distributions

### 3. Viability Assessment (`runpod-ma-27-viability.md`)
- Go/No-Go recommendation with scoring
- Risk analysis
- Mitigation strategies

### 4. Implementation Plan (Conditional - if viable)
- API integration checklist
- MCP server configuration template
- Migration path from current providers
- Testing protocol

### 5. Cost Estimation (`vision-cost-model.md`)
- Monthly cost projection at different volumes
- Break-even analysis
- Scaling recommendations

---

## Success Criteria

- [ ] MiniMax vision capabilities fully documented
- [ ] At least 3 API tests executed successfully
- [ ] Latency measured and compared against baseline providers
- [ ] Cost analysis complete with savings projection
- [ ] Clear recommendation (Implement / Hold / Reject)
- [ ] Alternative approaches evaluated and documented

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| MiniMax lacks vision support | Medium | High | Test with actual API calls; have backup providers |
| API rate limits too restrictive | Medium | Medium | Implement request queuing; use batching |
| Image quality degradation | Low | Medium | Test with various image sizes/formats |
| Documentation outdated | Medium | Low | Verify with live API tests |

---

## Timeline Estimate

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Documentation Review | 15 min | Source URLs, capability matrix |
| API Testing | 30 min | Test results, latency metrics |
| Comparison Analysis | 15 min | Provider matrix, cost analysis |
| Recommendation | 10 min | Viability score, final report |

**Total Estimated Time: ~70 minutes**

---

**Created:** 2026-01-20
**Version:** 1.0 (Enhanced)
**Author:** Claude Code (Plan Enhancement)
