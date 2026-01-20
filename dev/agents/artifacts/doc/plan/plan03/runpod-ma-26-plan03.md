# Plan: runpod-ma-26 - Vision Fallback Chain Test (REFINED)

## Objective
Execute comprehensive test of the vision/document analysis fallback chain to verify all providers work correctly, handle edge cases gracefully, and recover from failures.

## Version History
- **v1.0**: Initial draft with 15 tests
- **v1.1**: Enhanced with error scenarios and performance validation
- **v2.0 (current)**: Production-ready with all plan02 refinements

## Test Coverage
| Provider | Model | Expected Behavior |
|----------|-------|-------------------|
| Primary | Qwen3-VL 30B A3B | novita → phala → fireworks |
| Fallback 1 | Gemini 2.5 Flash | google-vertex → google-ai-studio |
| Fallback 2 | GPT-5 Mini | openai/gpt-5-mini via OpenRouter |
| Fallback 3 | MiniMax | Direct API (text-only) |

## Test Environment
- Service URL: http://localhost:8050
- **NEW**: Test Images: Local embedded base64 fixtures (reproducible)
- **NEW**: Expected Output Location: ./dev/agents/artifacts/doc/test/runpod-ma-26/
- **NEW**: CI Integration: JUnit XML output for CI/CD pipelines

---

## Test Cases (Enhanced with plan02 Refinements)

### Positive Tests (Happy Path)

#### Test 1: Qwen3-VL (Primary)
```bash
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "<TEST_URL>", "prompt": "Describe this image in detail"}'
```

**Enhanced Validation:**
```bash
# Assertions:
# 1. HTTP 200
# 2. Response contains "result" field with length > 50 chars
# 3. Response contains "model" field (non-empty)
# 4. Response contains "processing_time" field (number)
# 5. Time < 30s
```

#### Test 2: Gemini 2.5 Flash (Fallback)
```bash
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "<TEST_URL>", "prompt": "Describe this image", "model": "gemini-2.5-flash"}'
```

**Enhanced Validation:**
- All assertions from Test 1
- Model field contains "gemini" (case-insensitive)
- No "qwen" references in response

#### Test 3: GPT-5 Mini (Fallback)
```bash
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "<TEST_URL>", "prompt": "Describe this image", "model": "gpt-5-mini"}'
```

**Enhanced Validation:**
- All assertions from Test 1
- Model field contains "gpt" or "openai"
- No "gemini" or "qwen" references

#### Test 4: MiniMax (Text-Only Fallback)
```bash
curl -X POST http://localhost:8050/api/media/analyze \
  -H 'Content-Type: application/json' \
  -d '{"media_type": "document", "media_url": "<TEST_URL>", "prompt": "Describe this image"}'
```

**Enhanced Validation:**
- HTTP 200
- Response contains "warning" or "not support" (indicates text-only mode)
- Warning logged at INFO level
- Graceful degradation message in response

---

### Error Scenario Tests (Enhanced)

#### Test 5: Invalid Image URL (All Providers)
```bash
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "https://invalid.example.com/image.jpg", "prompt": "Describe this"}'
```

**Enhanced Validation:**
- HTTP 4xx or 5xx
- Error response contains "url", "invalid", or "accessible" (actionable)
- Provider attempts fallback (check logs)
- No service crash or hang

#### Test 6: Malformed JSON Request
```bash
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "<TEST_URL>", "invalid_field": "test"}'
```

**Validation:** HTTP 400 with clear validation error

#### Test 7: Missing Required Fields
```bash
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{}'
```

**Validation:** HTTP 400, specific field error (document_url required)

#### Test 8: Non-Image URL (PDF/Document)
```bash
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "https://example.com/document.pdf", "prompt": "Extract text"}'
```

**Validation:** HTTP 4xx/200 with appropriate handling

---

### Negative Tests (Expected Failures)

#### Test 9: MiniMax Vision Request (Explicitly Unsupported)
```bash
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "<TEST_URL>", "prompt": "Describe", "model": "minimax"}'
```

**Validation:** HTTP 400 or 422, response contains "MiniMax" and "vision"

#### Test 10: Unsupported Model Name
```bash
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "<TEST_URL>", "prompt": "Describe", "model": "non-existent-model-xyz"}'
```

**Validation:** HTTP 400 with "unsupported" or "unknown model" message

#### Test 11: Empty Prompt
```bash
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "<TEST_URL>", "prompt": ""}'
```

**Validation:** HTTP 400 or HTTP 200 with default prompt

---

### **NEW: Provider-Specific Failure Tests (plan02 refinement)**

#### Test 12: Provider Rate Limit (HTTP 429)
```bash
# Mock/simulate 429 response by exhausting provider quota
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "<TEST_URL>", "prompt": "Describe", "model": "qwen3-vl"}'
```

**Validation:**
- HTTP 429 or fallback to next provider
- Response contains "rate limit" or "quota" or "retry"
- Retry-After header respected (if present)

#### Test 13: Provider Timeout (NEW)
```bash
# Test with very slow provider response
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "<TEST_URL>", "prompt": "Describe", "model": "gemini-2.5-flash"}'
```

**Validation:**
- Timeout handled gracefully (< 60s total)
- Fallback to next provider
- No hang or infinite wait

#### Test 14: Chain Cascade Failure (NEW - Critical)
```bash
# Simulate all providers failing except last
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "<TEST_URL>", "prompt": "Describe"}'
```

**Validation:**
- All providers attempted before failing
- Clear error message when all fail
- No partial responses on complete failure
- Appropriate HTTP status (5xx when all fail)

#### Test 15: Network Partition During Request (NEW)
```bash
# Test when provider becomes unreachable mid-request
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "<TEST_URL>", "prompt": "Describe"}'
```

**Validation:**
- Error caught and handled
- Fallback attempted or clear error returned
- No service crash

---

### Performance & Timing Tests

#### Test 16: Latency Benchmark (All Providers)
```bash
# Time each request using curl's -w option
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "<TEST_URL>", "prompt": "Quick description"}' \
  -w "\nTime: %{time_total}s\n" -o response.json
```

**Enhanced Thresholds:**

| Provider | Target P95 | Max Acceptable | Notes |
|----------|-----------|----------------|-------|
| Qwen3-VL | < 15s | < 30s | Multi-provider fallback |
| Gemini 2.5 Flash | < 10s | < 20s | Fast model |
| GPT-5 Mini | < 10s | < 20s | OpenRouter overhead |
| MiniMax | < 5s | < 10s | Direct API, text-only |

**NEW - Circuit Breaker Validation:**
- After 5 failures, circuit opens
- Subsequent requests fail fast (no waiting)
- After 30s, circuit half-open (allows test request)
- After 3 successes, circuit closes

#### Test 17: Concurrent Request Handling
```bash
# Run 5 parallel requests (increased from 3)
for i in {1..5}; do
  curl -X POST http://localhost:8050/api/media/documents \
    -H 'Content-Type: application/json' \
    -d '{"document_url": "<TEST_URL>", "prompt": "Brief description"}' \
    -o "response_$i.json" &
done
wait
```

**Validation:**
- All 5 requests complete successfully
- No 5xx errors
- No timeouts (all < 60s total)
- Responses are distinct (not cached duplicates)

---

### Content Validation Tests

#### Test 18: Response Structure Validation (Enhanced)
```bash
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "<TEST_URL>", "prompt": "List all objects in this image"}'
```

**Schema Validation:**
```json
{
  "type": "object",
  "required": ["result", "model", "processing_time"],
  "properties": {
    "result": {"type": "string", "minLength": 1},
    "model": {"type": "string", "minLength": 1},
    "processing_time": {"type": "number", "minimum": 0},
    "provider": {"type": "string"},
    "prompt_hash": {"type": "string", "pattern": "^[a-f0-9]{64}$"}
  }
}
```

#### Test 19: Response Contains Expected Content
```bash
curl -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d '{"document_url": "<TEST_URL>", "prompt": "What colors appear in this image?"}'
```

**Validation:**
- Response contains relevant color descriptions
- No hallucinations about non-existent elements
- **NEW**: Use ground truth annotations for validation

---

### **NEW: Test Data Management (plan02 refinement)**

#### Test Data Strategy

```bash
# Local test images (embedded in test runner)
TEST_DATA_DIR="./dev/agents/artifacts/doc/test/runpod-ma-26/fixtures"

# Fixtures:
# - simple-scene.jpg: Basic outdoor scene (known colors: blue sky, green grass)
# - text-document.png: Document with legible text (known text: "TEST")
# - complex-scene.jpg: Indoor scene with multiple objects
# - empty-image.jpg: Solid color image (edge case)

# Expected responses stored in:
TEST_DATA_DIR/annotations/
# - simple-scene.json: {"expected_colors": ["blue", "green"], "forbidden": ["red"]}
# - text-document.json: {"expected_text": "TEST", "min_confidence": 0.9}
```

#### Automated Test Runner

```bash
#!/bin/bash
# run_tests.sh - Automated test runner with assertions

TEST_DATA_DIR="./dev/agents/artifacts/doc/test/runpod-ma-26/fixtures"
OUTPUT_DIR="./dev/agents/artifacts/doc/test/runpod-ma-26/outputs/$(date +%Y%m%d-%H%M%S)"

mkdir -p "$OUTPUT_DIR"

# Pre-flight checks
check_service_health() {
  curl -sf http://localhost:8050/health > /dev/null || {
    echo "ERROR: Service unhealthy"
    exit 1
  }
}

check_test_images() {
  for img in "$TEST_DATA_DIR"/*.jpg "$TEST_DATA_DIR"/*.png; do
    [ -f "$img" ] || {
      echo "WARNING: Missing test image: $img"
    }
  done
}

# Run test with assertions
run_test() {
  local test_num=$1
  local name=$2
  local url=$3
  local prompt=$4
  local expected_status=$5

  echo "Running Test $test_num: $name"
  start=$(date +%s%3N)

  response=$(curl -s -w "\n%{http_code}" -X POST \
    "http://localhost:8050/api/media/documents" \
    -H "Content-Type: application/json" \
    -d "{\"document_url\": \"$url\", \"prompt\": \"$prompt\"}")

  status=$(echo "$response" | tail -1)
  body=$(echo "$response" | sed '$d')
  end=$(date +%s%3N)
  latency=$((end - start))

  # Assertions
  if [ "$status" != "$expected_status" ]; then
    echo "FAIL: Expected $expected_status, got $status"
    echo "$body" > "$OUTPUT_DIR/test${test_num}_fail.json"
    return 1
  fi

  # Validate JSON structure
  echo "$body" | jq -e '.result' > /dev/null || {
    echo "FAIL: Missing 'result' field"
    return 1
  }

  echo "$body" | jq -e '.model' > /dev/null || {
    echo "FAIL: Missing 'model' field"
    return 1
  }

  echo "PASS: $name (${latency}ms)"
  echo "$body" > "$OUTPUT_DIR/test${test_num}_pass.json"
  return 0
}

# Main execution
check_service_health
check_test_images

passed=0
failed=0

# Run all tests...
for test in {1..19}; do
  if run_test ...; then
    ((passed++))
  else
    ((failed++))
  fi
done

# Generate JUnit XML
cat > "$OUTPUT_DIR/results.xml" << EOF
<?xml version="1.0"?>
<testsuites>
  <testsuite name="runpod-ma-26" tests="$((passed + failed))" failures="$failed">
    <!-- Test results... -->
  </testsuite>
</testsuites>
EOF

echo "Results: $passed passed, $failed failed"
exit $failed
```

---

## Success Criteria

### Functional Requirements
- [ ] Qwen3-VL returns valid response with image description
- [ ] Gemini 2.5 Flash returns valid response
- [ ] GPT-5 Mini returns valid response
- [ ] MiniMax gracefully falls back to text-only mode
- [ ] All endpoints return HTTP 200 (for valid requests)
- [ ] Error scenarios return appropriate HTTP status codes
- [ ] **NEW**: Rate limit (429) handled gracefully
- [ ] **NEW**: Timeout scenarios handled gracefully
- [ ] **NEW**: Chain cascade failure handled appropriately

### Performance Requirements
- [ ] Qwen3-VL P95 latency < 15s
- [ ] Gemini 2.5 Flash P95 latency < 10s
- [ ] GPT-5 Mini P95 latency < 10s
- [ ] MiniMax P95 latency < 5s
- [ ] Concurrent requests (5x) all succeed without errors
- [ ] **NEW**: Circuit breaker activates within 5 failures

### Quality Requirements
- [ ] Response structure matches expected schema
- [ ] Responses contain relevant, non-hallucinated content
- [ ] Error messages are actionable and clear
- [ ] No service crashes or hangs on invalid input
- [ ] **NEW**: Test data is versioned and reproducible
- [ ] **NEW**: JUnit XML output generated for CI integration

---

## Rollback/Recovery

```bash
# Pre-test snapshot
take_snapshot() {
  docker commit media-analysis-api "media-analysis-api:test-$1"
}

# Restore on failure
restore_snapshot() {
  docker stop media-analysis-api
  docker rm media-analysis-api
  docker run -d --name media-analysis-api \
    "media-analysis-api:test-$1" \
    uvicorn main:app --host 0.0.0.0 --port 8050
}

# Circuit breaker reset
reset_circuit_breaker() {
  curl -X POST http://localhost:8050/api/admin/circuit-breaker/reset
}
```

---

**Created:** 2026-01-20
**Version:** 2.0
**Previous Versions:** 0.1 (Draft), 1.0 (Enhanced)
**plan02 Refinements Applied:**
- Added provider rate limit (429) tests
- Added provider timeout tests
- Added chain cascade failure test
- Added network partition test
- Added test data management with local fixtures
- Added automated test runner with assertions
- Added JUnit XML output for CI integration
- Added circuit breaker validation
- Enhanced validation assertions with specific checks
- Added ground truth annotations for content validation
