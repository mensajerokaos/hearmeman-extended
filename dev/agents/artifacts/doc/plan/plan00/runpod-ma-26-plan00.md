---
task: runpod-ma-26 Vision Fallback Chain Test
agent: hc (headless claude)
model: claude-opus-4-5-20251101
timestamp: 2026-01-20T09:15:00-06:00
status: completed
---

# runpod-ma-26: Vision Fallback Chain Test

## Overview
Simple manual test to verify all 4 vision providers respond correctly.

## Test Script

Execute on devmaster:

```bash
#!/bin/bash
# Test Vision Fallback Chain
# Execute: ssh devmaster 'bash -s' < this_script.sh

TEST_IMAGE="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg?token=6e65f4e151b3f3675e05e712f4e7f9c867d48020870f33f61c0ea3bbcdc64cb5"

echo "=== Testing Vision Providers ==="
echo ""

# Test 1: Qwen3-VL (primary via novita -> phala -> fireworks)
echo -n "[1/4] Qwen3-VL: "
RESP1=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$TEST_IMAGE\", \"prompt\": \"Describe this image briefly\"}")
HTTP1=$(echo "$RESP1" | tail -1)
MODEL1=$(echo "$RESP1" | head -n -1 | jq -r '.model // .error // "unknown"' 2>/dev/null)
echo "HTTP $HTTP1 | Model: $MODEL1"

# Test 2: Gemini 2.5 Flash
echo -n "[2/4] Gemini 2.5 Flash: "
RESP2=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$TEST_IMAGE\", \"prompt\": \"Describe this image briefly\", \"model\": \"gemini-2.5-flash\"}")
HTTP2=$(echo "$RESP2" | tail -1)
MODEL2=$(echo "$RESP2" | head -n -1 | jq -r '.model // .error // "unknown"' 2>/dev/null)
echo "HTTP $HTTP2 | Model: $MODEL2"

# Test 3: GPT-5 Mini
echo -n "[3/4] GPT-5 Mini: "
RESP3=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$TEST_IMAGE\", \"prompt\": \"Describe this image briefly\", \"model\": \"gpt-5-mini\"}")
HTTP3=$(echo "$RESP3" | tail -1)
MODEL3=$(echo "$RESP3" | head -n -1 | jq -r '.model // .error // "unknown"' 2>/dev/null)
echo "HTTP $HTTP3 | Model: $MODEL3"

# Test 4: MiniMax (text-only fallback via /analyze endpoint)
echo -n "[4/4] MiniMax: "
RESP4=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8050/api/media/analyze \
  -H 'Content-Type: application/json' \
  -d "{\"media_type\": \"text\", \"prompt\": \"Say hello in one sentence\"}")
HTTP4=$(echo "$RESP4" | tail -1)
MODEL4=$(echo "$RESP4" | head -n -1 | jq -r '.model // .error // "unknown"' 2>/dev/null)
echo "HTTP $HTTP4 | Model: $MODEL4"

echo ""
echo "=== Test Complete ==="

# Summary
echo ""
echo "Summary:"
[[ "$HTTP1" == "200" ]] && echo "  [PASS] Qwen3-VL" || echo "  [FAIL] Qwen3-VL (HTTP $HTTP1)"
[[ "$HTTP2" == "200" ]] && echo "  [PASS] Gemini 2.5 Flash" || echo "  [FAIL] Gemini 2.5 Flash (HTTP $HTTP2)"
[[ "$HTTP3" == "200" ]] && echo "  [PASS] GPT-5 Mini" || echo "  [FAIL] GPT-5 Mini (HTTP $HTTP3)"
[[ "$HTTP4" == "200" ]] && echo "  [PASS] MiniMax" || echo "  [FAIL] MiniMax (HTTP $HTTP4)"
```

## Quick One-Liner (Copy-Paste)

```bash
ssh devmaster 'TEST_IMAGE="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg?token=6e65f4e151b3f3675e05e712f4e7f9c867d48020870f33f61c0ea3bbcdc64cb5" && echo "Qwen3-VL:" && curl -s -X POST http://localhost:8050/api/media/documents -H "Content-Type: application/json" -d "{\"document_url\": \"$TEST_IMAGE\", \"prompt\": \"Describe briefly\"}" | jq -r ".model" && echo "Gemini:" && curl -s -X POST http://localhost:8050/api/media/documents -H "Content-Type: application/json" -d "{\"document_url\": \"$TEST_IMAGE\", \"prompt\": \"Describe briefly\", \"model\": \"gemini-2.5-flash\"}" | jq -r ".model" && echo "GPT-5:" && curl -s -X POST http://localhost:8050/api/media/documents -H "Content-Type: application/json" -d "{\"document_url\": \"$TEST_IMAGE\", \"prompt\": \"Describe briefly\", \"model\": \"gpt-5-mini\"}" | jq -r ".model" && echo "MiniMax:" && curl -s -X POST http://localhost:8050/api/media/analyze -H "Content-Type: application/json" -d "{\"media_type\": \"text\", \"prompt\": \"Say hello\"}" | jq -r ".model"'
```

## Success Criteria

- [ ] Qwen3-VL returns HTTP 200 with valid model name
- [ ] Gemini 2.5 Flash returns HTTP 200 with valid model name
- [ ] GPT-5 Mini returns HTTP 200 with valid model name
- [ ] MiniMax returns HTTP 200 with valid model name
- [ ] All responses complete in < 30 seconds

## Verification

Run the script, check output shows all 4 providers responding with HTTP 200.

## Notes

- MiniMax is text-only (no vision MCP yet) - tested via /analyze with text prompt
- If Qwen3-VL fails, it falls back through novita -> phala -> fireworks providers
- If Gemini fails, it falls back through google-vertex -> google-ai-studio
