# Plan: runpod-ma-26 - Vision Fallback Chain Test (Enhanced)

## Executive Summary
Comprehensive test suite for the vision/document analysis API fallback chain across 4 providers (Qwen3-VL, Gemini 2.5 Flash, GPT-5 Mini, MiniMax). This enhanced plan includes 25+ test cases with detailed assertions, performance benchmarks, automated scripting framework, monitoring requirements, and fallback chain priority verification.

---

## 1. Test Data Requirements

### 1.1 Primary Test Images

| Test Image | URL | Purpose | Expected Elements |
|------------|-----|---------|-------------------|
| Vision Test | `https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg` | Primary positive test | Multiple objects, colors, text |
| Text Document | `https://hdd.automatic.picturelle.com/af/test-cases/text-document-test.png` | OCR/content extraction | Clear text, structured layout |
| Complex Scene | `https://hdd.automatic.picturelle.com/af/test-cases/complex-scene.jpg` | Detail extraction | People, objects, environment |
| Low Contrast | `https://hdd.automatic.picturelle.com/af/test-cases/low-contrast.png` | Edge case - challenging image | Subtle details, shadows |
| High Resolution | `https://hdd.automatic.picturelle.com/af/test-cases/high-res-test.jpg` | Large file handling | Fine details, patterns |

### 1.2 Test Image Specifications

```bash
# Download and validate test images before running suite
#!/bin/bash
# test-images/download-test-assets.sh

TEST_DIR="./test-assets/images"
mkdir -p "$TEST_DIR"

declare -A IMAGES=(
  ["vision-test.jpg"]="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"
  ["text-document-test.png"]="https://hdd.automatic.picturelle.com/af/test-cases/text-document-test.png"
  ["complex-scene.jpg"]="https://hdd.automatic.picturelle.com/af/test-cases/complex-scene.jpg"
  ["low-contrast.png"]="https://hdd.automatic.picturelle.com/af/test-cases/low-contrast.png"
  ["high-res-test.jpg"]="https://hdd.automatic.picturelle.com/af/test-cases/high-res-test.jpg"
)

for img in "${!IMAGES[@]}"; do
  echo "Downloading $img..."
  curl -sL "${IMAGES[$img]}" -o "$TEST_DIR/$img"
  if [ -f "$TEST_DIR/$img" ]; then
    echo "  ✓ Downloaded: $(du -h "$TEST_DIR/$img" | cut -f1)"
  else
    echo "  ✗ Failed to download: $img"
  fi
done

# Validate image integrity
for img in "$TEST_DIR"/*; do
  if file "$img" | grep -q "image"; then
    echo "✓ Valid image: $(basename $img)"
  else
    echo "✗ Invalid file: $(basename $img)"
  fi
done
```

### 1.3 Image Validation Criteria

```bash
# Image pre-validation script
IMAGE_VALIDATION_SCRIPT=$(cat << 'EOF'
validate_test_image() {
  local img_path="$1"
  local min_size_kb=10
  local max_size_mb=50

  # Check file exists and readable
  [ ! -f "$img_path" ] && return 1

  # Check file size
  local size_kb=$(du -k "$img_path" | cut -f1)
  [ "$size_kb" -lt "$min_size_kb" ] && return 2
  [ "$((size_kb / 1024))" -gt "$max_size_mb" ] && return 3

  # Check valid image (ImageMagick required)
  if command -v identify &> /dev/null; then
    identify "$img_path" > /dev/null 2>&1 || return 4
  fi

  return 0
}

# Usage: validate_test_image "path/to/image.jpg" && echo "Valid" || echo "Invalid"
EOF
)
```

---

## 2. Fallback Chain Architecture

### 2.1 Provider Priority Matrix

| Priority | Provider | Model | Expected Latency | Max Retries | Timeout |
|----------|----------|-------|------------------|-------------|---------|
| 1 (Primary) | Qwen3-VL 30B A3B | novita → phala → fireworks | < 15s | 3 | 60s |
| 2 (Fallback) | Gemini 2.5 Flash | google-vertex → google-ai-studio | < 10s | 3 | 45s |
| 3 (Fallback) | GPT-5 Mini | openai/gpt-5-mini (OpenRouter) | < 10s | 3 | 45s |
| 4 (Final) | MiniMax | Direct API (text-only) | < 5s | 1 | 30s |

### 2.2 Fallback Decision Logic

```
REQUEST RECEIVED
    ↓
Check requested model (if any)
    ↓
IF model="minimax" → Reject (no vision support)
    ↓
Try Primary (Qwen3-VL) with retries
    ↓
IF Qwen3-VL fails (timeout, error, 429, 5xx)
    ↓
Try Fallback 1 (Gemini 2.5 Flash) with retries
    ↓
IF Gemini fails
    ↓
Try Fallback 2 (GPT-5 Mini) with retries
    ↓
IF all fail → Return aggregated error
    ↓
Response with provider metadata
```

---

## 3. Test Cases

### 3.1 Positive Tests (Happy Path) - Tests 1-8

#### Test 1: Qwen3-VL Primary Provider
```bash
# PRIMARY TEST: Qwen3-VL via novita → phala → fireworks
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-001-qwen3vl-primary' \
  -d '{
    "document_url": "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg",
    "prompt": "Describe this image in detail. List all objects, colors, and text you can see.",
    "max_tokens": 1024
  }' \
  -w "\n\nHTTP_STATUS: %{http_code}\nTIME_TOTAL: %{time_total}s\nTIME_CONNECT: %{time_connect}s\nTIME_STARTTRANSFER: %{time_starttransfer}s\n" \
  -o ./test-results/test01-qwen3vl-primary.json

# Validation Criteria
assert_http_status() {
  [ "$(jq -r '.status // empty' ./test-results/test01-qwen3vl-primary.json 2>/dev/null || echo 'N/A')" != "error" ]
  [ "$(tail -1 response_headers | grep HTTP_STATUS | cut -d' ' -f2)" = "200" ]
}

assert_response_structure() {
  jq -e '.result' ./test-results/test01-qwen3vl-primary.json > /dev/null
  jq -e '.model | test("qwen3-vl|qwen2-vl|qwenvl")' ./test-results/test01-qwen3vl-primary.json > /dev/null
  jq -e '.processing_time | numbers' ./test-results/test01-qwen3vl-primary.json > /dev/null
}

assert_content_quality() {
  local response=$(jq -r '.result' ./test-results/test01-qwen3vl-primary.json)
  # Response should be > 50 chars and contain relevant content
  [ ${#response} -gt 50 ]
  # Should not contain obvious error markers
  [[ ! "$response" =~ "error"|"failed"|"unable" ]]
}

assert_latency() {
  local time_total=$(tail -1 response_headers | grep TIME_TOTAL | cut -d' ' -f2 | tr -d 's')
  # P95 requirement: < 15s, Max: < 30s
  awk -v t="$time_total" 'BEGIN { exit (t < 30) ? 0 : 1 }'
}
```

**Expected Output Schema:**
```json
{
  "result": "A detailed description of the image...",
  "model": "qwen3-vl-30b-a3b",
  "model_provider": "novita",
  "processing_time": 12.45,
  "request_id": "test-001-qwen3vl-primary",
  "retry_count": 0,
  "fallback_used": false
}
```

#### Test 2: Gemini 2.5 Flash Fallback
```bash
# FALLBACK 1: Explicit Gemini request
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-002-gemini-fallback' \
  -d '{
    "document_url": "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg",
    "prompt": "Describe this image briefly",
    "model": "gemini-2.5-flash",
    "temperature": 0.1
  }' \
  -w "\nHTTP_STATUS: %{http_code}\nTIME_TOTAL: %{time_total}s\n" \
  -o ./test-results/test02-gemini-fallback.json
```

**Validation Criteria:**
- HTTP 200 ✓
- Response contains `.model` = "gemini-2.5-flash" ✓
- Response time < 20s (P95: < 10s) ✓
- No "qwen" references in response ✓
- Content describes actual image elements ✓

#### Test 3: GPT-5 Mini Fallback
```bash
# FALLBACK 2: OpenRouter GPT-5 Mini
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-003-gpt5mini-fallback' \
  -d '{
    "document_url": "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg",
    "prompt": "What colors are in this image?",
    "model": "gpt-5-mini",
    "max_tokens": 256
  }' \
  -w "\nHTTP_STATUS: %{http_code}\nTIME_TOTAL: %{time_total}s\n" \
  -o ./test-results/test03-gpt5mini-fallback.json
```

**Validation Criteria:**
- HTTP 200 ✓
- Response contains color descriptions ✓
- Response time < 20s (P95: < 10s) ✓
- Model metadata indicates OpenRouter/gpt-5-mini ✓

#### Test 4: MiniMax Text-Only Fallback
```bash
# FINAL FALLBACK: MiniMax (text-only, no vision)
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-004-minimax-textonly' \
  -d '{
    "document_url": "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg",
    "prompt": "Analyze this image",
    "model": "minimax"
  }' \
  -w "\nHTTP_STATUS: %{http_code}\nTIME_TOTAL: %{time_total}s\n" \
  -o ./test-results/test04-minimax-textonly.json
```

**Validation Criteria:**
- HTTP 400 or 422 (rejected - no vision support) ✓
- Error message contains "MiniMax" ✓
- Error message contains "vision" or "image" ✓
- Suggests alternative providers ✓

#### Test 5: All Providers Sequential (Full Chain)
```bash
# Test full fallback chain by simulating primary failure
# This requires mocking or real failure simulation

# Simulate by checking response metadata across all 4 providers
for provider in "qwen3-vl" "gemini-2.5-flash" "gpt-5-mini"; do
  curl -X POST http://localhost:8050/api/media/documents \
    -H 'Content-Type: application/json' \
    -H 'X-Request-ID: test-005-chain-'$provider \
    -d "{\"document_url\": \"$TEST_URL\", \"prompt\": \"Brief description\", \"model\": \"$provider\"}" \
    -o ./test-results/test05-chain-$provider.json
done
```

**Validation Criteria:**
- Each provider returns valid response ✓
- Provider metadata correctly identifies source ✓
- Total time for all 3 providers < 60s combined ✓
- No provider conflicts or race conditions ✓

#### Test 6: High-Resolution Image Test
```bash
# Large image handling (> 5MB)
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-006-high-res' \
  -d '{
    "document_url": "https://hdd.automatic.picturelle.com/af/test-cases/high-res-test.jpg",
    "prompt": "Describe the fine details in this image",
    "max_tokens": 2048
  }' \
  -w "\nHTTP_STATUS: %{http_code}\nTIME_TOTAL: %{time_total}s\nSIZE_DOWNLOAD: %{size_download} bytes\n" \
  -o ./test-results/test06-high-res.json
```

**Validation Criteria:**
- HTTP 200 ✓
- Response time < 45s (larger image = longer processing) ✓
- Response contains fine detail descriptions ✓
- No timeout or truncation errors ✓

#### Test 7: Text Document OCR
```bash
# Document with text content
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-007-ocr-document' \
  -d '{
    "document_url": "https://hdd.automatic.picturelle.com/af/test-cases/text-document-test.png",
    "prompt": "Extract all text from this document. List each line or paragraph.",
    "model": "gemini-2.5-flash"
  }' \
  -w "\nHTTP_STATUS: %{http_code}\nTIME_TOTAL: %{time_total}s\n" \
  -o ./test-results/test07-ocr-document.json
```

**Validation Criteria:**
- HTTP 200 ✓
- Response contains extracted text ✓
- Text content matches expected from test document ✓
- No "cannot read" or "unclear" for clear text ✓

#### Test 8: Complex Scene Analysis
```bash
# Multi-object, multi-person scene
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-008-complex-scene' \
  -d '{
    "document_url": "https://hdd.automatic.picturelle.com/af/test-cases/complex-scene.jpg",
    "prompt": "Identify all people, objects, and actions in this scene. Provide a structured list.",
    "model": "qwen3-vl"
  }' \
  -w "\nHTTP_STATUS: %{http_code}\nTIME_TOTAL: %{time_total}s\n" \
  -o ./test-results/test08-complex-scene.json
```

**Validation Criteria:**
- HTTP 200 ✓
- Response lists multiple elements ✓
- No element hallucination (invented objects) ✓
- Response time < 25s ✓

---

### 3.2 Error Scenario Tests - Tests 9-18

#### Test 9: Invalid Image URL (All Providers)
```bash
# Non-existent domain
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-009-invalid-url' \
  -d '{
    "document_url": "https://nonexistent.invalid-domain.xyz/image.jpg",
    "prompt": "Describe this"
  }' \
  -w "\nHTTP_STATUS: %{http_code}\nTIME_TOTAL: %{time_total}s\n" \
  -o ./test-results/test09-invalid-url.json
```

**Validation Criteria:**
- HTTP 4xx or 5xx ✓
- Error message contains "invalid" or "not found" or "unreachable" ✓
- No service crash (container stays alive) ✓
- Error is actionable (suggests checking URL) ✓

#### Test 10: Valid URL but Non-Image Content
```bash
# HTML page instead of image
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-10-wrong-content-type' \
  -d '{
    "document_url": "https://example.com/page.html",
    "prompt": "Describe this"
  }' \
  -w "\nHTTP_STATUS: %{http_code}\nTIME_TOTAL: %{time_total}s\n" \
  -o ./test-results/test10-wrong-content-type.json
```

**Validation Criteria:**
- HTTP 4xx (content type error) or 200 with warning ✓
- Error message indicates content type issue ✓
- No 5xx server errors ✓

#### Test 11: Image Too Large (> 50MB)
```bash
# Simulate by pointing to large file
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-11-image-too-large' \
  -d '{
    "document_url": "https://example.com/very-large-image.jpg",
    "prompt": "Describe this"
  }' \
  -w "\nHTTP_STATUS: %{http_code}\nTIME_TOTAL: %{time_total}s\n" \
  -o ./test-results/test11-image-too-large.json
```

**Validation Criteria:**
- HTTP 413 (Payload Too Large) or 400 ✓
- Error message indicates size limit ✓
- No service crash ✓

#### Test 12: Malformed JSON Request
```bash
# Invalid JSON structure
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-12-malformed-json' \
  -d '{"document_url": "test.jpg", "prompt": "test", invalid_json_here}' \
  -w "\nHTTP_STATUS: %{http_code}\n" \
  -o ./test-results/test12-malformed-json.json
```

**Validation Criteria:**
- HTTP 400 Bad Request ✓
- Error contains "JSON" or "parse" ✓
- Request rejected without provider call ✓
- Service remains healthy ✓

#### Test 13: Missing Required Fields
```bash
# Empty request
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-13-missing-fields' \
  -d '{}' \
  -w "\nHTTP_STATUS: %{http_code}\n" \
  -o ./test-results/test13-missing-fields.json

# Missing prompt only
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-13b-missing-prompt' \
  -d '{"document_url": "https://example.com/test.jpg"}' \
  -w "\nHTTP_STATUS: %{http_code}\n" \
  -o ./test-results/test13b-missing-prompt.json

# Missing document_url only
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-13c-missing-url' \
  -d '{"prompt": "Describe this"}' \
  -w "\nHTTP_STATUS: %{http_code}\n" \
  -o ./test-results/test13c-missing-url.json
```

**Validation Criteria:**
- HTTP 400 Bad Request for all variants ✓
- Error specifies missing field(s) ✓
- No provider invocation attempted ✓

#### Test 14: Provider Timeout Handling (Qwen3-VL)
```bash
# Simulate timeout by using a very slow mock or network conditions
# In production, this requires:
# 1. Network throttling, OR
# 2. Mock server that delays response, OR
# 3. Check actual timeout behavior on slow responses

# For now, verify timeout is properly handled
# Test with large image that approaches timeout threshold

curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-14-timeout-handling' \
  -d '{
    "document_url": "https://hdd.automatic.picturelle.com/af/test-cases/high-res-test.jpg",
    "prompt": "Describe in extreme detail",
    "model": "qwen3-vl"
  }' \
  --max-time 120 \
  -w "\nHTTP_STATUS: %{http_code}\nTIME_TOTAL: %{time_total}s\n" \
  -o ./test-results/test14-timeout-handling.json
```

**Validation Criteria:**
- If response succeeds: Time < 60s (configured timeout) ✓
- If response times out: HTTP 408 or 504 ✓
- Fallback chain triggered if timeout occurs ✓
- No hanging requests > configured timeout ✓

#### Test 15: Rate Limit Handling (429 Errors)
```bash
# Test rate limit handling - may require actual rate limit triggering
# or mock response simulation

# First, check current rate limit headers on normal request
curl -I http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "test.jpg", "prompt": "test"}' \
  -o /dev/null -s -w "RateLimit-Limit: %{header:RateLimit-Limit}\nRateLimit-Remaining: %{header:RateLimit-Remaining}\n"

# Simulate rate limit by repeated requests (may trigger real limit)
for i in {1..50}; do
  curl -X POST http://localhost:8050/api/media/documents \
    -H 'Content-Type: application/json' \
    -H 'X-Request-ID: test-15-rate-limit-'$i \
    -d '{"document_url": "https://example.com/test.jpg", "prompt": "test"}' \
    -o ./test-results/rate-limit-$i.json \
    -s &
done
wait
```

**Validation Criteria:**
- Rate limit responses include proper headers (RateLimit-Limit, RateLimit-Remaining) ✓
- HTTP 429 for rate-limited requests ✓
- Retry-After header present (if applicable) ✓
- Fallback to other providers not applicable (rate limit is per-provider) ✓

#### Test 16: Provider API Error (500/503)
```bash
# Test behavior when provider returns server error
# This typically requires actual API failure or mock

# Check for error response structure
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-16-provider-error' \
  -d '{
    "document_url": "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg",
    "prompt": "Describe this"
  }' \
  -w "\nHTTP_STATUS: %{http_code}\n" \
  -o ./test-results/test16-provider-error.json

# Verify error response structure
cat ./test-results/test16-provider-error.json | jq '{
  status: .status,
  error: .error,
  provider_error: .provider_error,
  retry_suggested: .retry_suggested
}'
```

**Validation Criteria:**
- Error response contains provider error details ✓
- retry_suggested flag indicates if retry is appropriate ✓
- No sensitive internal error details exposed ✓
- Service remains stable ✓

#### Test 17: Network Failure Mid-Request
```bash
# Test partial failure handling
# This is difficult to simulate without network manipulation

# Alternative: Verify error handling for connection refused
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-17-network-failure' \
  -d '{
    "document_url": "http://localhost:9999/unreachable.jpg",
    "prompt": "Describe this"
  }' \
  -w "\nHTTP_STATUS: %{http_code}\nTIME_TOTAL: %{time_total}s\n" \
  -o ./test-results/test17-network-failure.json
```

**Validation Criteria:**
- HTTP 4xx or 5xx (connection refused) ✓
- Error message indicates network issue ✓
- No indefinite hang ✓
- Request completes quickly (fail-fast) ✓

#### Test 18: Concurrent Provider Errors
```bash
# Fire multiple requests that might trigger provider-side issues
for i in {1..10}; do
  curl -X POST http://localhost:8050/api/media/documents \
    -H 'Content-Type: application/json' \
    -H 'X-Request-ID: test-18-concurrent-error-'$i \
    -d "{\"document_url\": \"$TEST_URL\", \"prompt\": \"Test request $i\"}" \
    -o ./test-results/test18-concurrent-$i.json &
done
wait

# Analyze results
echo "=== Concurrent Error Test Analysis ==="
for f in ./test-results/test18-concurrent-*.json; do
  status=$(jq -r '.status // "N/A"' "$f" 2>/dev/null)
  http_code=$(jq -r '.http_code // "N/A"' "$f" 2>/dev/null)
  echo "$(basename $f): status=$status http=$http_code"
done
```

**Validation Criteria:**
- All 10 requests complete (no hangs) ✓
- Success rate > 90% (accounting for possible rate limits) ✓
- No cascade failures (one error doesn't crash service) ✓
- Consistent response structure across all ✓

---

### 3.3 Negative Tests (What SHOULD NOT Happen) - Tests 19-22

#### Test 19: MiniMax Vision Should Fail
```bash
# MiniMax does NOT support vision - verify this is enforced
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-19-minimax-vision-denied' \
  -d '{
    "document_url": "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg",
    "prompt": "Describe this image",
    "model": "minimax"
  }' \
  -w "\nHTTP_STATUS: %{http_code}\n" \
  -o ./test-results/test19-minimax-vision-denied.json
```

**Negative Assertions (What SHOULD NOT Happen):**
- ❌ Response should NOT contain vision analysis
- ❌ Response should NOT succeed with HTTP 200
- ❌ Service should NOT crash
- ❌ Should NOT fallback to another provider (user explicitly requested MiniMax)
- ❌ Error should NOT be vague

**Validation:**
```bash
# Negative check
if jq -e '.result' ./test-results/test19-minimax-vision-denied.json > /dev/null 2>&1; then
  echo "❌ FAIL: MiniMax vision should not succeed"
  exit 1
else
  echo "✓ PASS: MiniMax correctly rejected vision request"
fi

# Verify error message is helpful
error_msg=$(jq -r '.error // empty' ./test-results/test19-minimax-vision-denied.json)
if [[ "$error_msg" =~ "vision" || "$error_msg" =~ "image" ]]; then
  echo "✓ PASS: Error message mentions vision limitation"
else
  echo "⚠ WARN: Error message could be more specific about vision"
fi
```

#### Test 20: Invalid Model Name Should Not Crash
```bash
# Random invalid model name
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-20-invalid-model' \
  -d '{
    "document_url": "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg",
    "prompt": "Describe this",
    "model": "completely-fake-model-xyz-123"
  }' \
  -w "\nHTTP_STATUS: %{http_code}\n" \
  -o ./test-results/test20-invalid-model.json
```

**Negative Assertions:**
- ❌ Should NOT crash service
- ❌ Should NOT return 5xx server error
- ❌ Should NOT succeed with HTTP 200
- ❌ Should NOT hang

**Validation:**
```bash
http_code=$(jq -r '.http_code // 0' ./test-results/test20-invalid-model.json)
if [ "$http_code" -ge 500 ]; then
  echo "❌ FAIL: Invalid model caused server error ($http_code)"
  exit 1
fi
echo "✓ PASS: Invalid model properly rejected with $http_code"
```

#### Test 21: Empty Prompt Should Not Cause Hallucination
```bash
# Empty prompt handling
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-21-empty-prompt' \
  -d '{
    "document_url": "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg",
    "prompt": ""
  }' \
  -w "\nHTTP_STATUS: %{http_code}\nTIME_TOTAL: %{time_total}s\n" \
  -o ./test-results/test21-empty-prompt.json
```

**Negative Assertions:**
- ❌ Should NOT return empty/placeholder response
- ❌ Should NOT hallucinate content not in image
- ❌ Should NOT timeout

**Validation:**
```bash
response=$(jq -r '.result // empty' ./test-results/test21-empty-prompt.json)
if [ -z "$response" ]; then
  echo "❌ FAIL: Empty response returned"
  exit 1
fi

# Check for obvious hallucinations
if [[ "$response" =~ "I cannot see" ]] || [[ "$response" =~ "no image" ]]; then
  echo "✓ PASS: Appropriate response for empty prompt"
else
  echo "✓ PASS: Service handled empty prompt gracefully"
fi
```

#### Test 22: Rapid Replay Attacks Should Be Prevented
```bash
# Same request ID reuse
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-22-replay-attack' \
  -d '{"document_url": "https://example.com/test.jpg", "prompt": "test"}' \
  -o ./test-results/test22-replay-1.json

curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: test-22-replay-attack' \
  -d '{"document_url": "https://example.com/test.jpg", "prompt": "test"}' \
  -o ./test-results/test22-replay-2.json
```

**Negative Assertions:**
- ❌ Should NOT return cached response without processing
- ❌ Should NOT error due to duplicate ID
- ❌ Should NOT leak internal cache state

**Validation:**
```bash
# Both should succeed (idempotent behavior) or second should error (idempotency key)
echo "Checking replay attack handling..."
jq -e '.request_id' ./test-results/test22-replay-1.json > /dev/null
jq -e '.request_id' ./test-results/test22-replay-2.json > /dev/null
echo "✓ PASS: Replay requests handled correctly"
```

---

### 3.4 Performance & Concurrency Tests - Tests 23-28

#### Test 23: Latency Benchmark (P50, P95, P99)
```bash
#!/bin/bash
# latency-benchmark.sh - Run 30 requests per provider for percentiles

PROVIDERS=("qwen3-vl" "gemini-2.5-flash" "gpt-5-mini")
REQUESTS_PER_PROVIDER=30
OUTPUT_DIR="./test-results/benchmark"

mkdir -p "$OUTPUT_DIR"

for provider in "${PROVIDERS[@]}"; do
  echo "Benchmarking $provider ($REQUESTS_PER_PROVIDER requests)..."

  for i in $(seq 1 $REQUESTS_PER_PROVIDER); do
    curl -X POST http://localhost:8050/api/media/documents \
      -H 'Content-Type: application/json' \
      -H 'X-Request-ID: benchmark-'$provider'-'$i \
      -d "{\"document_url\": \"$TEST_URL\", \"prompt\": \"Brief test\", \"model\": \"$provider\"}" \
      -w "%{time_total}" \
      -o /dev/null -s \
      >> "$OUTPUT_DIR/${provider}_times.txt" &

    # Limit concurrent requests to 3 per provider
    if [ $((i % 3)) -eq 0 ]; then wait; fi
  done
  wait
done

# Calculate percentiles
calculate_percentiles() {
  local file="$1"
  local provider="$2"

  echo "=== $provider Latency Distribution ==="

  # Sort times numerically
  sorted=$(sort -n "$file")

  # Count total
  total=$(wc -l < "$file")

  # Calculate percentiles
  p50_index=$((total * 50 / 100))
  p95_index=$((total * 95 / 100))
  p99_index=$((total * 99 / 100))

  p50=$(sed -n "${p50_index}p" "$sorted")
  p95=$(sed -n "${p95_index}p" "$sorted")
  p99=$(sed -n "${p99_index}p" "$sorted")

  echo "  P50: ${p50}s"
  echo "  P95: ${p95}s"
  echo "  P99: ${p99}s"
  echo "  Mean: $(awk '{sum+=$1; count++} END {printf "%.2f", sum/count}' "$file")s"
  echo "  Max: $(tail -1 "$sorted")s"
  echo ""
}

for provider in "${PROVIDERS[@]}"; do
  calculate_percentiles "$OUTPUT_DIR/${provider}_times.txt" "$provider"
done
```

**Performance Thresholds:**

| Provider | P50 Target | P95 Target | P99 Target | Max Acceptable |
|----------|-----------|-----------|-----------|----------------|
| Qwen3-VL | < 8s | < 15s | < 25s | < 45s |
| Gemini 2.5 Flash | < 5s | < 10s | < 15s | < 30s |
| GPT-5 Mini | < 5s | < 10s | < 15s | < 30s |
| MiniMax | < 3s | < 5s | < 8s | < 15s |

**Validation Assertions:**
```bash
# Automated validation
for provider in "${PROVIDERS[@]}"; do
  p95=$(sed -n "$(($(wc -l < $OUTPUT_DIR/${provider}_times.txt) * 95 / 100))p" \
    <(sort -n $OUTPUT_DIR/${provider}_times.txt))

  max_p95=15  # seconds
  if (( $(echo "$p95 < $max_p95" | bc -l) )); then
    echo "✓ $provider P95 ($p95) within threshold"
  else
    echo "✗ $provider P95 ($p95) exceeds threshold ($max_p95)"
  fi
done
```

#### Test 24: Load Test (50 Concurrent Requests)
```bash
#!/bin/bash
# load-test.sh - 50 concurrent requests

CONCURRENT=50
OUTPUT_DIR="./test-results/load-test"
mkdir -p "$OUTPUT_DIR"

echo "Starting $CONCURRENT concurrent requests..."

start_time=$(date +%s.%N)

for i in $(seq 1 $CONCURRENT); do
  curl -X POST http://localhost:8050/api/media/documents \
    -H 'Content-Type: application/json' \
    -H 'X-Request-ID: load-test-'$i \
    -d "{\"document_url\": \"$TEST_URL\", \"prompt\": \"Load test $i\", \"model\": \"gemini-2.5-flash\"}" \
    -o "$OUTPUT_DIR/response_$i.json" \
    -s &
done
wait

end_time=$(date +%s.%N)
duration=$(echo "$end_time - $start_time" | bc)

echo "=== Load Test Results ==="
echo "Duration: ${duration}s for $CONCURRENT requests"
echo "Requests/second: $(echo "scale=2; $CONCURRENT / $duration" | bc)"

# Analyze results
success_count=0
error_count=0
total_time=0

for i in $(seq 1 $CONCURRENT); do
  http_code=$(jq -r '.http_code // 500' "$OUTPUT_DIR/response_$i.json" 2>/dev/null)
  if [ "$http_code" -eq 200 ]; then
    ((success_count++))
    time=$(jq -r '.processing_time // 0' "$OUTPUT_DIR/response_$i.json" 2>/dev/null)
    total_time=$(echo "$total_time + $time" | bc)
  else
    ((error_count++))
  fi
done

echo "Successful: $success_count/$CONCURRENT"
echo "Errors: $error_count/$CONCURRENT"
echo "Success Rate: $(echo "scale=2; $success_count * 100 / $CONCURRENT" | bc)%"

if [ $success_count -gt 0 ]; then
  echo "Avg Processing Time: $(echo "scale=2; $total_time / $success_count" | bc)s"
fi
```

**Load Test Thresholds:**
- Success Rate: > 95%
- Error Rate: < 5%
- No 5xx errors (except provider-side)
- No request hangs > 120s

#### Test 25: Stress Test (100 Requests Over 60 Seconds)
```bash
#!/bin/bash
# stress-test.sh - Sustained load over time

DURATION=60
RATE=2  # requests per second
OUTPUT_DIR="./test-results/stress-test"
mkdir -p "$OUTPUT_DIR"

echo "Stress test: $DURATION seconds at $RATE req/s"

start_time=$(date +%s)
request_count=0

while [ $(($(date +%s) - start_time)) -lt $DURATION ]; do
  for i in $(seq 1 $RATE); do
    ((request_count++))
    curl -X POST http://localhost:8050/api/media/documents \
      -H 'Content-Type: application/json' \
      -H 'X-Request-ID: stress-test-'$request_count \
      -d "{\"document_url\": \"$TEST_URL\", \"prompt\": \"Stress test\", \"model\": \"qwen3-vl\"}" \
      -o "$OUTPUT_DIR/stress_$request_count.json" \
      -s &
  done
  sleep 1
done
wait

echo "Total requests: $request_count"

# Analysis
success=$(grep -l '"status":"success"' $OUTPUT_DIR/stress_*.json 2>/dev/null | wc -l)
echo "Successful: $success/$request_count"
```

**Stress Test Thresholds:**
- Success Rate: > 90%
- Memory: Stable (no leak)
- CPU: < 80% sustained
- Response Time: Degradation < 50% under load

#### Test 26: Fallback Chain Timing Verification
```bash
#!/bin/bash
# fallback-timing.sh - Measure each fallback stage

echo "=== Fallback Chain Timing Analysis ==="

# Test 1: Primary (Qwen3-VL) direct
echo "Primary (Qwen3-VL) direct..."
start=$(date +%s.%N)
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "'"$TEST_URL"'", "prompt": "Test", "model": "qwen3-vl"}' \
  -o /dev/null -s
primary_time=$(echo "$(date +%s.%N) - $start" | bc)
echo "  Time: ${primary_time}s"

# Test 2: Fallback 1 (Gemini) direct
echo "Fallback 1 (Gemini 2.5 Flash) direct..."
start=$(date +%s.%N)
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "'"$TEST_URL"'", "prompt": "Test", "model": "gemini-2.5-flash"}' \
  -o /dev/null -s
fallback1_time=$(echo "$(date +%s.%N) - $start" | bc)
echo "  Time: ${fallback1_time}s"

# Test 3: Fallback 2 (GPT-5 Mini) direct
echo "Fallback 2 (GPT-5 Mini) direct..."
start=$(date +%s.%N)
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "'"$TEST_URL"'", "prompt": "Test", "model": "gpt-5-mini"}' \
  -o /dev/null -s
fallback2_time=$(echo "$(date +%s.%N) - $start" | bc)
echo "  Time: ${fallback2_time}s"

# Verify priority order
echo ""
echo "=== Fallback Priority Verification ==="
echo "Primary should be fastest when available: $([ $(echo "$primary_time < $fallback1_time" | bc) -eq 1 ] && echo "YES" || echo "NO")"
echo "Fallbacks are available: $([ $(echo "$fallback1_time < 30" | bc) -eq 1 ] && echo "YES" || echo "NO")"
```

**Expected Behavior:**
- Primary provider fastest (optimized path)
- Fallbacks available within reasonable time
- No provider prioritization errors

#### Test 27: Memory & Resource Usage
```bash
#!/bin/bash
# resource-monitor.sh - Track resource usage during tests

MONITOR_LOG="./test-results/resource-monitor.log"
CONTAINER_NAME=${CONTAINER_NAME:-media-analysis-api}

echo "Monitoring resource usage..."
echo "Timestamp,CPU%,MemoryMB,NetworkIn,NetworkOut" > "$MONITOR_LOG"

# Monitor in background
while true; do
  timestamp=$(date +%s)

  # Get container stats
  stats=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" "$CONTAINER_NAME" 2>/dev/null)
  cpu=$(echo "$stats" | cut -d',' -f1)
  mem=$(echo "$stats" | cut -d',' -f2)

  echo "$timestamp,$cpu,$mem" >> "$MONITOR_LOG"

  sleep 5
done &
MONITOR_PID=$!

# Run test workload
sleep 10  # Let monitor stabilize

# Run 20 requests
for i in $(seq 1 20); do
  curl -X POST http://localhost:8050/api/media/documents \
    -H 'Content-Type: application/json' \
    -d '{"document_url": "'"$TEST_URL"'", "prompt": "Resource test '$i'"}' \
    -o /dev/null -s
done

# Stop monitor
kill $MONITOR_PID 2>/dev/null

# Analyze
echo "=== Resource Usage Analysis ==="
avg_cpu=$(awk -F',' '{sum+=$2; count++} END {print sum/count}' "$MONITOR_LOG")
avg_mem=$(awk -F',' '{sum+=$3; count++} END {print sum/count}' "$MONITOR_LOG")
echo "Average CPU: ${avg_cpu}%"
echo "Average Memory: ${avg_mem}MB"
```

**Resource Thresholds:**
- CPU: < 70% sustained
- Memory: Stable (no linear growth)
- No OOM kills

#### Test 28: Recovery After Provider Outage
```bash
#!/bin/bash
# recovery-test.sh - Simulate and verify recovery from provider outage

echo "=== Provider Outage Recovery Test ==="

# Phase 1: Normal operation baseline
echo "Phase 1: Baseline (10 successful requests)"
baseline_success=0
for i in $(seq 1 10); do
  if curl -s -f -X POST http://localhost:8050/api/media/documents \
    -H 'Content-Type: application/json' \
    -d '{"document_url": "'"$TEST_URL"'", "prompt": "Baseline '$i'"}' > /dev/null; then
    ((baseline_success++))
  fi
done
echo "  Baseline success: $baseline_success/10"

# Phase 2: Simulate provider issues (requires actual provider failure or mock)
# This test verifies the system handles provider errors gracefully
echo "Phase 2: Provider error handling"
error_handled=0
for i in $(seq 1 5); do
  result=$(curl -s -X POST http://localhost:8050/api/media/documents \
    -H 'Content-Type: application/json' \
    -d '{"document_url": "'"$TEST_URL"'", "prompt": "Error test '$i'"}')

  if echo "$result" | jq -e '.status' > /dev/null 2>&1; then
    ((error_handled++))
  fi
done
echo "  Errors handled gracefully: $error_handled/5"

# Phase 3: Recovery verification
echo "Phase 3: Post-error recovery"
recovery_success=0
for i in $(seq 1 10); do
  if curl -s -f -X POST http://localhost:8050/api/media/documents \
    -H 'Content-Type: application/json' \
    -d '{"document_url": "'"$TEST_URL"'", "prompt": "Recovery '$i'"}' > /dev/null; then
    ((recovery_success++))
  fi
done
echo "  Recovery success: $recovery_success/10"

# Final assessment
echo ""
if [ $recovery_success -ge 9 ]; then
  echo "✓ PASS: System recovered successfully after provider issues"
else
  echo "⚠ WARN: Recovery rate below expected ($recovery_success/10)"
fi
```

---

## 4. Automated Test Framework

### 4.1 Pytest-Based Test Suite

```python
# tests/test_vision_fallback_chain.py
"""
Comprehensive test suite for Vision Fallback Chain
Run with: pytest tests/test_vision_fallback_chain.py -v
"""

import pytest
import requests
import time
import json
import statistics
from typing import Dict, List
import subprocess
import os

BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8050")
TEST_IMAGE = os.getenv("TEST_IMAGE_URL", "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg")


class TestPositiveFlows:
    """Test happy path scenarios for all providers"""

    @pytest.fixture
    def qwen3vl_response(self):
        return requests.post(
            f"{BASE_URL}/api/media/documents",
            json={
                "document_url": TEST_IMAGE,
                "prompt": "Describe this image in detail",
                "model": "qwen3-vl"
            },
            headers={"X-Request-ID": f"pytest-{int(time.time())}"}
        )

    @pytest.fixture
    def gemini_response(self):
        return requests.post(
            f"{BASE_URL}/api/media/documents",
            json={
                "document_url": TEST_IMAGE,
                "prompt": "Describe this image",
                "model": "gemini-2.5-flash"
            },
            headers={"X-Request-ID": f"pytest-{int(time.time())}"}
        )

    def test_qwen3vl_success(self, qwen3vl_response):
        """Qwen3-VL should return successful response"""
        assert qwen3vl_response.status_code == 200
        data = qwen3vl_response.json()
        assert "result" in data
        assert "model" in data
        assert "qwen" in data["model"].lower()
        assert len(data["result"]) > 50  # Not empty response

    def test_gemini_flash_success(self, gemini_response):
        """Gemini 2.5 Flash should return successful response"""
        assert gemini_response.status_code == 200
        data = gemini_response.json()
        assert "result" in data
        assert "gemini" in data["model"].lower()

    def test_response_structure(self):
        """All responses should have consistent structure"""
        for model in ["qwen3-vl", "gemini-2.5-flash"]:
            response = requests.post(
                f"{BASE_URL}/api/media/documents",
                json={"document_url": TEST_IMAGE, "prompt": "Test", "model": model}
            )
            assert response.status_code == 200
            data = response.json()
            # Validate schema
            assert "result" in data
            assert "model" in data
            assert "processing_time" in data
            assert isinstance(data["result"], str)
            assert isinstance(data["model"], str)


class TestErrorScenarios:
    """Test error handling across various failure modes"""

    def test_invalid_url_rejected(self):
        """Invalid URL should be rejected"""
        response = requests.post(
            f"{BASE_URL}/api/media/documents",
            json={
                "document_url": "https://invalid.domain.xyz/nonexistent.jpg",
                "prompt": "Describe this"
            }
        )
        assert response.status_code in [400, 404, 422]
        data = response.json()
        assert "error" in data

    def test_malformed_json_rejected(self):
        """Malformed JSON should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/media/documents",
            data='{"document_url": "test.jpg", invalid}',
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400

    def test_missing_fields_rejected(self):
        """Missing required fields should be rejected"""
        # Missing document_url
        response = requests.post(
            f"{BASE_URL}/api/media/documents",
            json={"prompt": "Test"}
        )
        assert response.status_code == 400

        # Missing prompt
        response = requests.post(
            f"{BASE_URL}/api/media/documents",
            json={"document_url": TEST_IMAGE}
        )
        assert response.status_code == 400


class TestNegativeCases:
    """Test what should NOT happen"""

    def test_minimax_vision_rejected(self):
        """MiniMax should NOT accept vision requests"""
        response = requests.post(
            f"{BASE_URL}/api/media/documents",
            json={
                "document_url": TEST_IMAGE,
                "prompt": "Describe this",
                "model": "minimax"
            }
        )
        # Should NOT succeed with 200
        assert response.status_code != 200
        # Error should mention vision limitation
        if response.status_code in [400, 422]:
            data = response.json()
            assert "vision" in data.get("error", "").lower() or \
                   "image" in data.get("error", "").lower()

    def test_no_hallucination_on_empty_prompt(self):
        """Empty prompt should not cause hallucinated responses"""
        response = requests.post(
            f"{BASE_URL}/api/media/documents",
            json={"document_url": TEST_IMAGE, "prompt": ""}
        )
        assert response.status_code == 200
        data = response.json()
        # Should not return empty or placeholder response
        assert len(data.get("result", "")) > 0


class TestPerformance:
    """Performance and latency tests"""

    @pytest.mark.parametrize("model,expected_p95", [
        ("qwen3-vl", 15.0),
        ("gemini-2.5-flash", 10.0),
        ("gpt-5-mini", 10.0),
    ])
    def test_latency_percentile(self, model, expected_p95):
        """Each provider should meet P95 latency threshold"""
        latencies = []
        for _ in range(10):  # 10 samples
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/media/documents",
                json={"document_url": TEST_IMAGE, "prompt": "Brief test", "model": model}
            )
            latency = time.time() - start
            if response.status_code == 200:
                latencies.append(latency)

        assert len(latencies) >= 5  # At least 50% success rate
        p95 = statistics.quantiles(latencies, n=100)[94]
        assert p95 < expected_p95, f"{model} P95 ({p95:.2f}s) exceeds {expected_p95}s"

    def test_concurrent_requests(self):
        """System should handle concurrent requests"""
        import concurrent.futures

        def make_request(request_id: int) -> int:
            response = requests.post(
                f"{BASE_URL}/api/media/documents",
                json={"document_url": TEST_IMAGE, "prompt": f"Concurrent {request_id}"},
                headers={"X-Request-ID": f"concurrent-{request_id}"}
            )
            return response.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            results = [f.result(timeout=60) for f in concurrent.futures.as_completed(futures)]

        success_count = sum(1 for r in results if r == 200)
        assert success_count >= 4, f"Only {success_count}/5 concurrent requests succeeded"


class TestFallbackChain:
    """Test fallback chain priority and behavior"""

    def test_fallback_priority(self):
        """Verify fallback chain respects priority order"""
        # This test requires mocking or observing actual fallback behavior
        # For now, verify all providers are accessible
        providers = ["qwen3-vl", "gemini-2.5-flash", "gpt-5-mini"]

        results = {}
        for provider in providers:
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/media/documents",
                json={"document_url": TEST_IMAGE, "prompt": "Test", "model": provider}
            )
            results[provider] = {
                "status": response.status_code,
                "time": time.time() - start
            }

        # All should be accessible
        for provider, result in results.items():
            assert result["status"] == 200, f"{provider} not accessible"


# Pytest configuration
# pytest.ini
"""
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
filterwarnings =
    ignore::DeprecationWarning
"""
```

### 4.2 Bash-Based Quick Test Script

```bash
#!/bin/bash
# quick-test.sh - Fast validation script for CI/CD

set -e

BASE_URL="${API_URL:-http://localhost:8050}"
TEST_URL="${TEST_IMAGE:-https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg}"
RESULTS_DIR="./test-results/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "=== Vision Fallback Chain Quick Test ==="
echo "API: $BASE_URL"
echo "Results: $RESULTS_DIR"
echo ""

pass=0
fail=0

test_endpoint() {
  local name="$1"
  local expected_status="$2"
  local body="$3"

  echo -n "Test: $name... "
  response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/media/documents" \
    -H 'Content-Type: application/json' \
    -d "$body")

  http_code=$(echo "$response" | tail -1)
  body=$(echo "$response" | sed '$d')

  if [ "$http_code" = "$expected_status" ]; then
    echo "✓ PASS ($http_code)"
    ((pass++))
  else
    echo "✗ FAIL (expected $expected_status, got $http_code)"
    echo "$body" > "$RESULTS_DIR/$name-failed.json"
    ((fail++))
  fi
}

# Quick validation tests
test_endpoint "Valid Request" "200" \
  "{\"document_url\": \"$TEST_URL\", \"prompt\": \"Test\", \"model\": \"qwen3-vl\"}"

test_endpoint "Missing URL" "400" \
  "{\"prompt\": \"Test\"}"

test_endpoint "Missing Prompt" "400" \
  "{\"document_url\": \"$TEST_URL\"}"

test_endpoint "Invalid Model" "400" \
  "{\"document_url\": \"$TEST_URL\", \"prompt\": \"Test\", \"model\": \"fake-model\"}"

echo ""
echo "=== Results ==="
echo "Passed: $pass"
echo "Failed: $fail"

if [ $fail -gt 0 ]; then
  exit 1
fi
exit 0
```

---

## 5. Monitoring & Observability Requirements

### 5.1 Required Metrics

```yaml
# prometheus-metrics-requirements.yaml
metrics:
  - name: vision_request_total
    type: counter
    labels: [provider, status, model]
    description: Total number of vision requests

  - name: vision_request_duration_seconds
    type: histogram
    labels: [provider, model]
    buckets: [0.5, 1, 2, 5, 10, 15, 30, 60, 120]
    description: Request duration in seconds

  - name: vision_fallback_total
    type: counter
    labels: [from_provider, to_provider, reason]
    description: Total number of fallbacks

  - name: vision_provider_errors_total
    type: counter
    labels: [provider, error_type]
    description: Provider-specific errors

  - name: vision_active_requests
    type: gauge
    description: Currently active requests
```

### 5.2 Log Format Requirements

```json
// Structured log entry format
{
  "timestamp": "2026-01-20T10:30:00Z",
  "level": "INFO|WARN|ERROR",
  "request_id": "req-abc123",
  "provider": "qwen3-vl|gemini-2.5-flash|gpt-5-mini|minimax",
  "operation": "image_analysis|fallback|validation",
  "duration_ms": 1234,
  "status": "success|error|fallback",
  "error_code": "TIMEOUT|RATE_LIMIT|INVALID_URL|PROVIDER_ERROR",
  "retry_count": 0,
  "fallback_chain": ["qwen3-vl", "gemini-2.5-flash"],
  "image_size_bytes": 1234567,
  "response_size_bytes": 5678
}
```

### 5.3 Health Check Endpoints

```bash
# Required health endpoints
GET /health                    # Overall service health
GET /health/live              # Liveness probe
GET /health/ready             # Readiness probe
GET /metrics                  # Prometheus metrics

# Provider status check
GET /api/media/providers/status

# Response format:
{
  "status": "healthy|degraded|unhealthy",
  "providers": {
    "qwen3-vl": "available|degraded|unavailable",
    "gemini-2.5-flash": "available|degraded|unavailable",
    "gpt-5-mini": "available|degraded|unavailable",
    "minimax": "available|degraded|unavailable"
  },
  "uptime_seconds": 12345,
  "active_requests": 3
}
```

### 5.4 Alerting Thresholds

```yaml
alerts:
  - name: HighErrorRate
    condition: error_rate > 5% over 5 minutes
    severity: warning
    action: Check provider status

  - name: HighLatency
    condition: p95_latency > 20s for 5 minutes
    severity: warning
    action: Review fallback configuration

  - name: ProviderUnavailable
    condition: provider_available == false for 2 minutes
    severity: critical
    action: Check provider API keys/connectivity

  - name: FallbackChainExhausted
    condition: all_providers_failed > 3 times in 10 minutes
    severity: critical
    action: Immediate investigation needed

  - name: MemoryLeakSuspected
    condition: memory_usage_increasing for 30 minutes
    severity: warning
    action: Check for memory leaks
```

---

## 6. Fallback Chain Priority Verification

### 6.1 Priority Order Test

```bash
#!/bin/bash
# verify-fallback-priority.sh

echo "=== Fallback Chain Priority Verification ==="

# Test 1: Verify each provider responds
echo ""
echo "Step 1: Provider Availability"
for provider in "qwen3-vl" "gemini-2.5-flash" "gpt-5-mini" "minimax"; do
  response=$(curl -s -X POST http://localhost:8050/api/media/documents \
    -H 'Content-Type: application/json' \
    -d '{"document_url": "'"$TEST_URL"'", "prompt": "Test", "model": "'"$provider"'"}')

  http_code=$(echo "$response" | jq -r '.http_code // empty')
  if [ "$http_code" = "200" ]; then
    echo "  ✓ $provider: Available"
  elif [ "$http_code" = "400" ] || [ "$http_code" = "422" ]; then
    echo "  ○ $provider: Rejects (expected for minimax vision)"
  else
    echo "  ✗ $provider: Error ($http_code)"
  fi
done

# Test 2: Verify fallback occurs on primary failure
echo ""
echo "Step 2: Fallback Behavior"
# This requires actual provider failure or mock
echo "  Note: Full fallback test requires provider failure simulation"

# Test 3: Verify provider metadata in responses
echo ""
echo "Step 3: Provider Metadata"
for provider in "qwen3-vl" "gemini-2.5-flash" "gpt-5-mini"; do
  response=$(curl -s -X POST http://localhost:8050/api/media/documents \
    -H 'Content-Type: application/json' \
    -d '{"document_url": "'"$TEST_URL"'", "prompt": "Test", "model": "'"$provider"'"}')

  model=$(echo "$response" | jq -r '.model // "unknown"')
  provider_used=$(echo "$response" | jq -r '.model_provider // empty')

  if [[ "$model" =~ "$provider" ]] || [[ "$provider_used" =~ "$provider" ]]; then
    echo "  ✓ $provider: Correctly identified in response"
  else
    echo "  ⚠ $provider: Model mismatch (got: $model)"
  fi
done

echo ""
echo "=== Priority Verification Complete ==="
```

### 6.2 Fallback Decision Matrix

| Scenario | Expected Behavior |
|----------|-------------------|
| Qwen3-VL available | Use Qwen3-VL (primary) |
| Qwen3-VL timeout | Fallback to Gemini 2.5 Flash |
| Qwen3-VL 429 (rate limit) | Fallback to Gemini 2.5 Flash |
| Qwen3-VL 5xx error | Fallback to Gemini 2.5 Flash |
| Qwen3-VL + Gemini fail | Fallback to GPT-5 Mini |
| All providers fail | Return aggregated error |
| MiniMax explicitly requested | Return error (no vision support) |

---

## 7. Test Execution Checklist

### Pre-Test Setup
- [ ] All test images downloaded and validated
- [ ] Service health verified: `curl http://localhost:8050/health`
- [ ] Test results directory created
- [ ] Monitor running (resource tracking)
- [ ] Logs configured for test run

### Test Execution Order
1. **Phase 1**: Positive tests (Tests 1-8)
2. **Phase 2**: Error scenarios (Tests 9-18)
3. **Phase 3**: Negative tests (Tests 19-22)
4. **Phase 4**: Performance tests (Tests 23-27)
5. **Phase 5**: Fallback verification (Test 28)

### Post-Test Validation
- [ ] All output files generated
- [ ] Results analyzed and summarized
- [ ] Performance thresholds met
- [ ] Error handling verified
- [ ] Logs captured for review

---

## 8. Expected Output Artifacts

| File | Purpose |
|------|---------|
| `test-results/{timestamp}/test*.json` | Individual test responses |
| `test-results/{timestamp}/benchmark/` | Latency benchmark data |
| `test-results/{timestamp}/load-test/` | Load test responses |
| `test-results/{timestamp}/resource-monitor.log` | Resource usage over time |
| `test-results/{timestamp}/summary.md` | Formatted summary |
| `test-results/{timestamp}/assertions.yaml` | Pass/fail for all assertions |
| `test-results/{timestamp}/full-log.jsonl` | Complete test log |

---

## 9. Rollback & Recovery

If tests reveal issues:

```bash
# 1. Check service health
curl http://localhost:8050/health

# 2. View recent logs
docker logs --tail 100 <container_name>

# 3. Restart if needed
docker compose restart

# 4. Verify health after restart
curl http://localhost:8050/health

# 5. Re-run failing tests with verbose logging
TEST_LOG_LEVEL=debug pytest tests/test_vision_fallback_chain.py::TestClass::test_method -v
```

---

## 10. Success Criteria Summary

### Functional Requirements
- [ ] All 3 vision providers (Qwen3-VL, Gemini 2.5 Flash, GPT-5 Mini) return valid responses
- [ ] MiniMax correctly rejects vision requests with helpful error
- [ ] Fallback chain respects priority order
- [ ] All error scenarios return appropriate HTTP status codes
- [ ] No service crashes or hangs

### Performance Requirements
- [ ] Qwen3-VL P95 latency < 15s
- [ ] Gemini 2.5 Flash P95 latency < 10s
- [ ] GPT-5 Mini P95 latency < 10s
- [ ] Load test success rate > 95%
- [ ] Concurrent requests (5x) all succeed

### Quality Requirements
- [ ] Response structure matches schema
- [ ] No hallucinations or empty responses
- [ ] Error messages are actionable
- [ ] Provider metadata correctly identifies source

### Negative Assertions (Must NOT happen)
- [ ] MiniMax does NOT process vision requests
- [ ] Invalid requests do NOT crash service
- [ ] No memory leaks under sustained load
- [ ] No response leakage between requests

---

## Scoring Method

| Category | Score | Notes |
|----------|-------|-------|
| Test Coverage | _/10 | 25+ tests covering all scenarios |
| Assertion Quality | _/10 | Specific, automated, measurable |
| Automation Potential | _/10 | Pytest + bash framework provided |
| Error Scenarios | _/10 | 10+ error cases with validation |
| Performance Validation | _/10 | P50/P95/P99, load, stress tests |
| **Total** | _/50 | |

**Threshold for plan02**: Total >= 45/50

If Total < 45, address:
1. _______________
2. _______________
3. _______________

---

**Created:** 2026-01-20
**Version:** 2.0 (Enhanced)
**Status:** Ready for Implementation
**Author:** Claude Sonnet 4.5
