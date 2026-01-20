---
author: $USER
model: claude-sonnet-4-5-20250929
date: 2026-01-20
task: PRD for Vision Fallback Chain Testing (Qwen3-VL → Gemini 2.5 Flash → GPT-5 Mini → MiniMax)
---

# Vision Fallback Chain Testing - Product Requirements Document

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-20 | $USER | Initial PRD creation for runpod-ma-26 |

---

# Executive Summary

## Project Overview

This document defines the comprehensive testing protocol for the Vision Fallback Chain in the `media-analysis-api` service. The fallback chain provides resilience for image/document analysis by attempting providers in order until successful response or exhaustion.

## Test URL

```
https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg
```

## Provider Chain (Priority Order)

| Priority | Provider | Model | Access Path | Vision Support |
|----------|----------|-------|-------------|----------------|
| 1 | Qwen3-VL | qwen3-vl-30b-a3b-instruct | novita → phala → fireworks (OpenRouter) | ✅ Native |
| 2 | Gemini 2.5 Flash | gemini-2.5-flash-exp | google-vertex → google-ai-studio | ✅ Native |
| 3 | GPT-5 Mini | gpt-5-mini | OpenRouter | ✅ Native |
| 4 | MiniMax | abab6.5s-chat | Direct API | ❌ Text-only (fallback) |

## Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Provider Availability | 3/4 (75%) | At least 3 providers respond successfully |
| Response Quality | Valid JSON | All responses parse correctly |
| Fallback Behavior | Chain complete | All 4 providers tested sequentially |
| Performance | < 30s per provider | Each provider responds within timeout |
| Error Handling | Graceful degradation | Failed providers logged with reasons |

---

# Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        media-analysis-api:8050                                   │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                     Vision Fallback Chain                                   │  │
│  │                                                                           │  │
│  │    ┌──────────────────────────────────────────────────────────────────┐   │  │
│  │    │  POST /api/media/documents                                        │   │  │
│  │    │  POST /api/media/analyze (aggregator)                             │   │  │
│  │    └──────────────────────────────────────────────────────────────────┘   │  │
│  │                              │                                              │  │
│  │                              ▼                                              │  │
│  │    ┌──────────────────────────────────────────────────────────────────┐   │  │
│  │    │              prompt_router.py - Fallback Orchestrator             │   │  │
│  │    │                                                               │   │   │  │
│  │    │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │   │   │  │
│  │    │   │ Provider 1  │───▶│ Provider 2  │───▶│ Provider 3  │       │   │   │  │
│  │    │   │ Qwen3-VL    │    │ Gemini 2.5  │    │ GPT-5 Mini  │       │   │   │  │
│  │    │   │ (Primary)   │    │ Flash       │    │             │       │   │   │  │
│  │    │   └─────────────┘    └─────────────┘    └─────────────┘       │   │   │  │
│  │    │          │                 │                 │                 │   │   │  │
│  │    │          ▼                 ▼                 ▼                 │   │   │  │
│  │    │   ┌─────────────────────────────────────────────────────┐      │   │   │  │
│  │    │   │              Provider 4: MiniMax                    │      │   │   │  │
│  │    │   │         (Text-Only Fallback - Limited Vision)       │      │   │   │  │
│  │    │   └─────────────────────────────────────────────────────┘      │   │   │  │
│  │    └──────────────────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                     │                                            │
│     ┌──────────────────────────────┼──────────────────────────────┐            │
│     ▼                              ▼                              ▼            │
┌─────────────┐            ┌─────────────────┐            ┌────────────────┐     │
│   novita    │            │ google-vertex   │            │   OpenRouter   │     │
│   (primary) │            │ (fallback)      │            │ (backup)       │     │
│             │            │                 │            │                │     │
│ Fallback:   │            │ Fallback:       │            │ Fallback:      │     │
│ → phala     │            │ → google-ai-    │            │ → Direct MiniMax│    │
│ → fireworks │            │   studio        │            │   (text-only)  │     │
└─────────────┘            └─────────────────┘            └────────────────┘     │
```

## Data Flow Through Fallback Chain

```
Request: POST /api/media/documents
    │
    ├─► Input Processing
    │       │
    │       ├─► Validate document_url
    │       ├─► Download image to temp storage
    │       └─► Prepare prompt
    │
    ├─► Provider 1: Qwen3-VL (novita → phala → fireworks)
    │       │
    │       ├─► OpenRouter API call
    │       │   Endpoint: https://openrouter.ai/api/v1/chat/completions
    │       │   Model: qwen3-vl-30b-a3b-instruct
    │       │   Auth: Bearer OPENROUTER_API_KEY
    │       │
    │       └─► SUCCESS → Return response
    │           FAIL → Continue to Provider 2
    │
    ├─► Provider 2: Gemini 2.5 Flash (google-vertex → google-ai-studio)
    │       │
    │       ├─► Google Vertex AI API (preferred)
    │       │   Endpoint: https://{region}-aiplatform.googleapis.com/v1/projects/{project}/locations/{region}/publishers/google/models/{model}:generateContent
    │       │   Model: gemini-2.5-flash-exp
    │       │   Auth: Bearer GOOGLE_ACCESS_TOKEN
    │       │
    │       └─► FAIL → Continue to Provider 3
    │
    ├─► Provider 3: GPT-5 Mini (OpenRouter)
    │       │
    │       ├─► OpenRouter API call
    │       │   Endpoint: https://openrouter.ai/api/v1/chat/completions
    │       │   Model: openai/gpt-5-mini
    │       │   Auth: Bearer OPENROUTER_API_KEY
    │       │
    │       └─► FAIL → Continue to Provider 4
    │
    ├─► Provider 4: MiniMax (Direct API - Text Only)
    │       │
    │       ├─► MiniMax API call
    │       │   Endpoint: https://api.minimax.chat/v1/chat/completions
    │       │   Model: abab6.5s-chat
    │       │   Auth: Bearer MINIMAX_API_KEY
    │       │
    │       └─► Note: MiniMax does not support vision natively
    │               Returns text-only fallback message
    │
    └─► Response
            ├─► provider_used: str
            ├─► response_text: str
            ├─► latency_ms: int
            ├─► tokens_used: int
            └─► cost_usd: float
```

---

# Provider Details

## Provider 1: Qwen3-VL 30B A3B

### Overview

| Attribute | Value |
|-----------|-------|
| Model ID | qwen3-vl-30b-a3b-instruct |
| Provider | Alibaba Cloud (Qwen Team) |
| Access | OpenRouter (novita → phala → fireworks) |
| Vision Support | Native (128K context, 4K resolution) |
| Parameters | 30B (A3B: Alternating 3B expert) |
| Context Length | 128K tokens |
| Image Resolution | Up to 4K (4096x4096) |

### API Configuration

```python
# OpenRouter Format
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "qwen3-vl-30b-a3b-instruct"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://media-analysis-api.automatic.picturelle.com",
    "X-Title": "Media Analysis API"
}
BODY = {
    "model": "qwen3-vl-30b-a3b-instruct",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }
    ],
    "temperature": 0.7,
    "max_tokens": 4096
}
```

### Response Format

```json
{
  "id": "gen-1234567890",
  "object": "chat.completion",
  "created": 1706745600,
  "model": "qwen3-vl-30b-a3b-instruct",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "This image shows..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 1500,
    "completion_tokens": 350,
    "total_tokens": 1850
  }
}
```

### Pricing (OpenRouter)

| Input | Output |
|-------|--------|
| $0.0001 / 1K tokens | $0.0002 / 1K tokens |

---

## Provider 2: Gemini 2.5 Flash

### Overview

| Attribute | Value |
|-----------|-------|
| Model ID | gemini-2.5-flash-exp |
| Provider | Google |
| Access | google-vertex (primary) → google-ai-studio (fallback) |
| Vision Support | Native (1M context, native image support) |
| Context Length | 1M tokens |
| Image Resolution | Native (auto-handled) |

### API Configuration (Google Vertex AI)

```python
# Vertex AI Format
PROJECT_ID = "your-project-id"
LOCATION = "us-central1"
ENDPOINT = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/gemini-2.5-flash-exp:generateContent"
HEADERS = {
    "Authorization": f"Bearer {GOOGLE_ACCESS_TOKEN}",
    "Content-Type": "application/json"
}
BODY = {
    "contents": [
        {
            "role": "user",
            "parts": [
                {"text": prompt},
                {
                    "file_data": {
                        "mime_type": "image/jpeg",
                        "file_uri": image_url
                    }
                }
            ]
        }
    ],
    "generation_config": {
        "temperature": 0.7,
        "max_output_tokens": 4096
    }
}
```

### Response Format

```json
{
  "candidates": [
    {
      "content": {
        "role": "model",
        "parts": [
          {
            "text": "This image shows..."
          }
        ]
      },
      "finish_reason": "STOP",
      "safety_ratings": [...]
    }
  ],
  "usageMetadata": {
    "prompt_token_count": 1200,
    "candidates_token_count": 400,
    "total_token_count": 1600
  }
}
```

### Pricing (Vertex AI)

| Input | Output |
|-------|--------|
| $0.0001 / 1K tokens | $0.0004 / 1K tokens |

### Fallback: Google AI Studio

```python
# If Vertex AI fails, use AI Studio
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-exp:generateContent"
PARAMS = {"key": GOOGLE_API_KEY}
```

---

## Provider 3: GPT-5 Mini

### Overview

| Attribute | Value |
|-----------|-------|
| Model ID | gpt-5-mini |
| Provider | OpenAI |
| Access | OpenRouter |
| Vision Support | Native (128K context) |
| Context Length | 128K tokens |

### API Configuration

```python
# OpenRouter Format (same as Qwen3-VL)
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-5-mini"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://media-analysis-api.automatic.picturelle.com",
    "X-Title": "Media Analysis API"
}
BODY = {
    "model": "openai/gpt-5-mini",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }
    ],
    "temperature": 0.7,
    "max_tokens": 4096
}
```

### Response Format

```json
{
  "id": "gen-0987654321",
  "object": "chat.completion",
  "created": 1706745601,
  "model": "openai/gpt-5-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "This image shows..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 1400,
    "completion_tokens": 300,
    "total_tokens": 1700
  }
}
```

### Pricing (OpenRouter)

| Input | Output |
|-------|--------|
| $0.00015 / 1K tokens | $0.0006 / 1K tokens |

---

## Provider 4: MiniMax (Text-Only Fallback)

### Overview

| Attribute | Value |
|-----------|-------|
| Model ID | abab6.5s-chat |
| Provider | MiniMax |
| Access | Direct API |
| Vision Support | **NONE** (text-only) |
| Context Length | 64K tokens |

### API Configuration

```python
ENDPOINT = "https://api.minimax.chat/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {MINIMAX_API_KEY}",
    "Content-Type": "application/json"
}
BODY = {
    "model": "abab6.5s-chat",
    "messages": [
        {
            "role": "user",
            "content": f"[Image Analysis Not Supported]\n\nPrompt: {prompt}\nImage URL: {image_url}\n\nNote: MiniMax API does not support vision/image analysis natively."
        }
    ],
    "temperature": 0.7,
    "max_tokens": 2048
}
```

### Response Format

```json
{
  "id": "gen-minimax-12345",
  "object": "chat.completion",
  "created": 1706745602,
  "model": "abab6.5s-chat",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "I cannot analyze images directly. For image analysis, please use a vision-capable model like Qwen3-VL, Gemini, or GPT-5 Mini."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
  }
}
```

### Pricing

| Input | Output |
|-------|--------|
| $0.0001 / 1K tokens | $0.0001 / 1K tokens |

---

# Test Implementation

## Test Environment

| Component | Value |
|-----------|-------|
| Service | media-analysis-api |
| Port | 8050 |
| Container | media-analysis-api (devmaster) |
| Test Image | vision-test.jpg |
| Image URL | https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg |

## Test Prompts

### Standard Prompt

```
"Describe this image in detail. Include: main subject, composition, colors, style, mood, and any notable elements."
```

### Alternative Prompts (for variety testing)

```
"A concise one-sentence description of this image."
"What's happening in this image? Provide a detailed narrative."
"List all objects visible in this image."
"What is the mood or atmosphere of this image?"
```

## Expected Outputs Per Provider

### Qwen3-VL (Primary - Expected: SUCCESS)

```json
{
  "status": "success",
  "provider": "qwen3-vl-30b-a3b-instruct",
  "model_used": "qwen3-vl-30b-a3b-instruct",
  "response": "The image shows a [detailed description]",
  "latency_ms": 2500,
  "tokens": {
    "prompt": 1500,
    "completion": 350,
    "total": 1850
  },
  "cost_usd": 0.00057
}
```

### Gemini 2.5 Flash (Expected: SUCCESS)

```json
{
  "status": "success",
  "provider": "gemini-2.5-flash-exp",
  "model_used": "gemini-2.5-flash-exp",
  "response": "The image shows a [detailed description]",
  "latency_ms": 1800,
  "tokens": {
    "prompt": 1200,
    "completion": 400,
    "total": 1600
  },
  "cost_usd": 0.00052
}
```

### GPT-5 Mini (Expected: SUCCESS)

```json
{
  "status": "success",
  "provider": "gpt-5-mini",
  "model_used": "openai/gpt-5-mini",
  "response": "The image shows a [detailed description]",
  "latency_ms": 3000,
  "tokens": {
    "prompt": 1400,
    "completion": 300,
    "total": 1700
  },
  "cost_usd": 0.00129
}
```

### MiniMax (Expected: TEXT-ONLY FALLBACK)

```json
{
  "status": "fallback",
  "provider": "minimax",
  "model_used": "abab6.5s-chat",
  "response": "I cannot analyze images directly. For image analysis, please use a vision-capable model.",
  "latency_ms": 500,
  "tokens": {
    "prompt": 100,
    "completion": 50,
    "total": 150
  },
  "cost_usd": 0.000015,
  "warning": "MiniMax does not support vision capabilities"
}
```

---

# Phased Implementation Plan

## Phase 1: Pre-Test Verification

**Duration**: 5 minutes
**Objective**: Verify test environment is ready

### Tasks

#### 1.1: Verify Container Status

```bash
# SSH to devmaster
ssh devmaster

# Check container is running
docker ps --filter "name=media-analysis-api" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Expected output:
# NAMES                STATUS          PORTS
# media-analysis-api   Up 2 hours      0.0.0.0:8050->8000/tcp
```

#### 1.2: Verify Service Health

```bash
# Test health endpoint
curl -s http://localhost:8050/health | jq .

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "features": {
#     "vision": true,
#     "transcription": true,
#     "fallback_chain": true
#   }
# }
```

#### 1.3: Verify API Keys Configuration

```bash
# Check environment variables are set
ssh devmaster 'docker exec media-analysis-api env | grep -E "(OPENROUTER|GOOGLE|MINIMAX)" | sort'

# Expected (keys masked):
# GOOGLE_API_KEY=****************************
# GOOGLE_VERTEX_ACCESS_TOKEN=****************************
# MINIMAX_API_KEY=****************************
# OPENROUTER_API_KEY=****************************
```

#### 1.4: Test Image URL Accessibility

```bash
# Verify test image is accessible
curl -I "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"

# Expected response:
# HTTP/2 200
# content-type: image/jpeg
# content-length: [file_size]
```

### Phase 1 Output

Create file: `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-26-pre/phase1-verification.json`

```json
{
  "phase": "pre-test-verification",
  "timestamp": "2026-01-20T00:00:00Z",
  "checks": {
    "container_status": {
      "status": "passed|failed",
      "details": "Container running on port 8050"
    },
    "health_endpoint": {
      "status": "passed|failed",
      "details": "Health check returns OK"
    },
    "api_keys": {
      "status": "passed|failed",
      "providers": ["openrouter", "google", "minimax"]
    },
    "test_image": {
      "status": "passed|failed",
      "url": "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"
    }
  }
}
```

### Phase 1 Verification Commands

```bash
# Run all verification checks
ssh devmaster << 'EOF'
echo "=== Phase 1: Pre-Test Verification ==="

# 1. Container status
echo -n "[1/4] Container Status: "
if docker ps --filter name=media-analysis-api | grep -q "Up"; then
    echo "PASS"
else
    echo "FAIL"
fi

# 2. Health endpoint
echo -n "[2/4] Health Check: "
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8050/health)
if [ "$HEALTH" = "200" ]; then
    echo "PASS"
else
    echo "FAIL (HTTP $HEALTH)"
fi

# 3. API keys
echo -n "[3/4] API Keys: "
KEYS=$(docker exec media-analysis-api env | grep -c "OPENROUTER_API_KEY\|GOOGLE_API_KEY\|MINIMAX_API_KEY")
if [ "$KEYS" -ge 3 ]; then
    echo "PASS"
else
    echo "FAIL ($KEYS/3 keys found)"
fi

# 4. Test image
echo -n "[4/4] Test Image: "
IMG_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg")
if [ "$IMG_STATUS" = "200" ]; then
    echo "PASS"
else
    echo "FAIL (HTTP $IMG_STATUS)"
fi

echo "=== Verification Complete ==="
EOF
```

---

## Phase 2: Provider 1 - Qwen3-VL Test

**Duration**: 30-60 seconds
**Objective**: Test primary vision provider

### Tasks

#### 2.1: Execute Qwen3-VL Request

```bash
ssh devmaster << 'EOF'
CDN_URL="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"

echo "=== Testing Qwen3-VL (Primary Provider) ==="
echo "Timestamp: $(date -Iseconds)"

START_TIME=$(date +%s%N)

RESPONSE=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{
    \"document_url\": \"$CDN_URL\",
    \"prompt\": \"Describe this image in detail. Include: main subject, composition, colors, style, mood, and any notable elements.\"
  }")

END_TIME=$(date +%s%N)
LATENCY_MS=$(( (END_TIME - START_TIME) / 1000000 ))

# Parse and display results
echo "Latency: ${LATENCY_MS}ms"
echo "Response:"
echo "$RESPONSE" | jq '.'

# Extract key metrics
PROVIDER=$(echo "$RESPONSE" | jq -r '.model_used // "unknown"')
STATUS=$(echo "$RESPONSE" | jq -r '.status // "unknown"')
TOKENS=$(echo "$RESPONSE" | jq -r '.tokens.total // 0')

echo ""
echo "Summary:"
echo "  Provider: $PROVIDER"
echo "  Status: $STATUS"
echo "  Total Tokens: $TOKENS"
echo "  Latency: ${LATENCY_MS}ms"
EOF
```

#### 2.2: Capture Qwen3-VL Response Details

```bash
ssh devmaster << 'EOF'
# Detailed Qwen3-VL test with full metrics
CDN_URL="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"

curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{
    \"document_url\": \"$CDN_URL\",
    \"prompt\": \"Describe this image in detail. Include: main subject, composition, colors, style, mood, and any notable elements.\",
    \"options\": {
      \"capture_metrics\": true,
      \"capture_cost\": true
    }
  }" | jq '{
  provider: .model_used,
  status: .status,
  response_length: (.response | length),
  latency_ms: .latency_ms,
  tokens: .tokens,
  cost_usd: .cost_usd,
  response_preview: (.response[:200] + "...") | select(length > 200),
  raw: .
}'
EOF
```

### Phase 2 Output

Create file: `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-26-pre/phase2-qwen3-vl.json`

```json
{
  "phase": "qwen3-vl-test",
  "timestamp": "2026-01-20T00:00:00Z",
  "provider": "qwen3-vl-30b-a3b-instruct",
  "provider_id": 1,
  "request": {
    "url": "http://localhost:8050/api/media/documents",
    "document_url": "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg",
    "prompt": "Describe this image in detail. Include: main subject, composition, colors, style, mood, and any notable elements."
  },
  "response": {
    "model_used": "qwen3-vl-30b-a3b-instruct",
    "status": "success",
    "response": "[full response text]",
    "response_preview": "[first 200 chars]",
    "latency_ms": 2500,
    "tokens": {
      "prompt": 1500,
      "completion": 350,
      "total": 1850
    },
    "cost_usd": 0.00057
  },
  "validation": {
    "status": "passed",
    "checks": {
      "model_correct": true,
      "status_success": true,
      "response_non_empty": true,
      "latency_acceptable": true
    }
  }
}
```

### Phase 2 Verification Commands

```bash
# Quick verification
ssh devmaster << 'EOF'
CDN_URL="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"

echo -n "[Qwen3-VL] Response Status: "
STATUS=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\"}" \
  | jq -r '.status')

if [ "$STATUS" = "success" ]; then
    echo "PASS (success)"
else
    echo "FAIL (got: $STATUS)"
fi

echo -n "[Qwen3-VL] Model Name: "
MODEL=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\"}" \
  | jq -r '.model_used')

if [[ "$MODEL" == *"qwen3"* ]]; then
    echo "PASS ($MODEL)"
else
    echo "FAIL (unexpected model: $MODEL)"
fi
EOF
```

---

## Phase 3: Provider 2 - Gemini 2.5 Flash Test

**Duration**: 30-60 seconds
**Objective**: Test Google Vertex AI fallback

### Tasks

#### 3.1: Execute Gemini 2.5 Flash Request

```bash
ssh devmaster << 'EOF'
CDN_URL="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"

echo "=== Testing Gemini 2.5 Flash (Fallback Provider 2) ==="
echo "Timestamp: $(date -Iseconds)"

START_TIME=$(date +%s%N)

RESPONSE=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{
    \"document_url\": \"$CDN_URL\",
    \"prompt\": \"Describe this image in detail. Include: main subject, composition, colors, style, mood, and any notable elements.\",
    \"model\": \"gemini-2.5-flash\"
  }")

END_TIME=$(date +%s%N)
LATENCY_MS=$(( (END_TIME - START_TIME) / 1000000 ))

# Parse and display results
echo "Latency: ${LATENCY_MS}ms"
echo "Response:"
echo "$RESPONSE" | jq '.'

# Extract key metrics
PROVIDER=$(echo "$RESPONSE" | jq -r '.model_used // "unknown"')
STATUS=$(echo "$RESPONSE" | jq -r '.status // "unknown"')
TOKENS=$(echo "$RESPONSE" | jq -r '.tokens.total // 0')

echo ""
echo "Summary:"
echo "  Provider: $PROVIDER"
echo "  Status: $STATUS"
echo "  Total Tokens: $TOKENS"
echo "  Latency: ${LATENCY_MS}ms"
EOF
```

#### 3.2: Force Provider Selection Test

```bash
ssh devmaster << 'EOF'
# Test forcing specific provider
CDN_URL="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"

echo "=== Force Gemini 2.5 Flash via Prompt Router ==="

curl -s -X POST http://localhost:8050/api/media/analyze \
  -H 'Content-Type: application/json' \
  -d "{
    \"media_type\": \"document\",
    \"media_url\": \"$CDN_URL\",
    \"prompt\": \"Describe this image\",
    \"model\": \"gemini-2.5-flash\",
    \"force_provider\": true
  }" | jq '{
  provider: .model_used,
  status: .status,
  latency_ms: .latency_ms,
  tokens: .tokens
}'
EOF
```

### Phase 3 Output

Create file: `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-26-pre/phase3-gemini-flash.json`

```json
{
  "phase": "gemini-2.5-flash-test",
  "timestamp": "2026-01-20T00:00:00Z",
  "provider": "gemini-2.5-flash-exp",
  "provider_id": 2,
  "request": {
    "url": "http://localhost:8050/api/media/documents",
    "document_url": "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg",
    "prompt": "Describe this image in detail. Include: main subject, composition, colors, style, mood, and any notable elements.",
    "model": "gemini-2.5-flash"
  },
  "response": {
    "model_used": "gemini-2.5-flash-exp",
    "status": "success",
    "response": "[full response text]",
    "response_preview": "[first 200 chars]",
    "latency_ms": 1800,
    "tokens": {
      "prompt": 1200,
      "completion": 400,
      "total": 1600
    },
    "cost_usd": 0.00052
  },
  "validation": {
    "status": "passed",
    "checks": {
      "model_correct": true,
      "status_success": true,
      "response_non_empty": true,
      "latency_acceptable": true
    }
  }
}
```

### Phase 3 Verification Commands

```bash
# Quick verification
ssh devmaster << 'EOF'
CDN_URL="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"

echo -n "[Gemini 2.5] Response Status: "
STATUS=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\", \"model\": \"gemini-2.5-flash\"}" \
  | jq -r '.status')

if [ "$STATUS" = "success" ]; then
    echo "PASS (success)"
else
    echo "FAIL (got: $STATUS)"
fi

echo -n "[Gemini 2.5] Model Name: "
MODEL=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\", \"model\": \"gemini-2.5-flash\"}" \
  | jq -r '.model_used')

if [[ "$MODEL" == *"gemini"* ]]; then
    echo "PASS ($MODEL)"
else
    echo "FAIL (unexpected model: $MODEL)"
fi
EOF
```

---

## Phase 4: Provider 3 - GPT-5 Mini Test

**Duration**: 30-60 seconds
**Objective**: Test OpenRouter GPT-5 Mini

### Tasks

#### 4.1: Execute GPT-5 Mini Request

```bash
ssh devmaster << 'EOF'
CDN_URL="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"

echo "=== Testing GPT-5 Mini (Fallback Provider 3) ==="
echo "Timestamp: $(date -Iseconds)"

START_TIME=$(date +%s%N)

RESPONSE=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{
    \"document_url\": \"$CDN_URL\",
    \"prompt\": \"Describe this image in detail. Include: main subject, composition, colors, style, mood, and any notable elements.\",
    \"model\": \"gpt-5-mini\"
  }")

END_TIME=$(date +%s%N)
LATENCY_MS=$(( (END_TIME - START_TIME) / 1000000 ))

# Parse and display results
echo "Latency: ${LATENCY_MS}ms"
echo "Response:"
echo "$RESPONSE" | jq '.'

# Extract key metrics
PROVIDER=$(echo "$RESPONSE" | jq -r '.model_used // "unknown"')
STATUS=$(echo "$RESPONSE" | jq -r '.status // "unknown"')
TOKENS=$(echo "$RESPONSE" | jq -r '.tokens.total // 0')

echo ""
echo "Summary:"
echo "  Provider: $PROVIDER"
echo "  Status: $STATUS"
echo "  Total Tokens: $TOKENS"
echo "  Latency: ${LATENCY_MS}ms"
EOF
```

### Phase 4 Output

Create file: `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-26-pre/phase4-gpt5-mini.json`

```json
{
  "phase": "gpt-5-mini-test",
  "timestamp": "2026-01-20T00:00:00Z",
  "provider": "openai/gpt-5-mini",
  "provider_id": 3,
  "request": {
    "url": "http://localhost:8050/api/media/documents",
    "document_url": "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg",
    "prompt": "Describe this image in detail. Include: main subject, composition, colors, style, mood, and any notable elements.",
    "model": "gpt-5-mini"
  },
  "response": {
    "model_used": "openai/gpt-5-mini",
    "status": "success",
    "response": "[full response text]",
    "response_preview": "[first 200 chars]",
    "latency_ms": 3000,
    "tokens": {
      "prompt": 1400,
      "completion": 300,
      "total": 1700
    },
    "cost_usd": 0.00129
  },
  "validation": {
    "status": "passed",
    "checks": {
      "model_correct": true,
      "status_success": true,
      "response_non_empty": true,
      "latency_acceptable": true
    }
  }
}
```

### Phase 4 Verification Commands

```bash
# Quick verification
ssh devmaster << 'EOF'
CDN_URL="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"

echo -n "[GPT-5 Mini] Response Status: "
STATUS=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\", \"model\": \"gpt-5-mini\"}" \
  | jq -r '.status')

if [ "$STATUS" = "success" ]; then
    echo "PASS (success)"
else
    echo "FAIL (got: $STATUS)"
fi

echo -n "[GPT-5 Mini] Model Name: "
MODEL=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\", \"model\": \"gpt-5-mini\"}" \
  | jq -r '.model_used')

if [[ "$MODEL" == *"gpt-5"* ]]; then
    echo "PASS ($MODEL)"
else
    echo "FAIL (unexpected model: $MODEL)"
fi
EOF
```

---

## Phase 5: Provider 4 - MiniMax Fallback Test

**Duration**: 10-30 seconds
**Objective**: Test text-only MiniMax fallback

### Tasks

#### 5.1: Execute MiniMax Request (Expect Text-Only)

```bash
ssh devmaster << 'EOF'
CDN_URL="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"

echo "=== Testing MiniMax (Text-Only Fallback Provider 4) ==="
echo "Timestamp: $(date -Iseconds)"
echo "WARNING: MiniMax does not support vision - expect text-only fallback"

START_TIME=$(date +%s%N)

RESPONSE=$(curl -s -X POST http://localhost:8050/api/media/analyze \
  -H 'Content-Type: application/json' \
  -d "{
    \"media_type\": \"document\",
    \"media_url\": \"$CDN_URL\",
    \"prompt\": \"Describe this image in detail. Include: main subject, composition, colors, style, mood, and any notable elements.\"
  }")

END_TIME=$(date +%s%N)
LATENCY_MS=$(( (END_TIME - START_TIME) / 1000000 ))

# Parse and display results
echo "Latency: ${LATENCY_MS}ms"
echo "Response:"
echo "$RESPONSE" | jq '.'

# Extract key metrics
PROVIDER=$(echo "$RESPONSE" | jq -r '.model_used // "unknown"')
STATUS=$(echo "$RESPONSE" | jq -r '.status // "unknown"')
WARNING=$(echo "$RESPONSE" | jq -r '.warning // "none"')

echo ""
echo "Summary:"
echo "  Provider: $PROVIDER"
echo "  Status: $STATUS (expected: fallback)"
echo "  Warning: $WARNING"
echo "  Latency: ${LATENCY_MS}ms"
EOF
```

#### 5.2: Verify MiniMax Text-Only Behavior

```bash
ssh devmaster << 'EOF'
# Test that MiniMax correctly reports no vision support
CDN_URL="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"

echo "=== Verifying MiniMax Text-Only Fallback Behavior ==="

RESPONSE=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\"}")

STATUS=$(echo "$RESPONSE" | jq -r '.status')
PROVIDER=$(echo "$RESPONSE" | jq -r '.model_used')
WARNING=$(echo "$RESPONSE" | jq -r '.warning // empty')

echo "Provider: $PROVIDER"
echo "Status: $STATUS"
echo "Warning present: $([ -n "$WARNING" ] && echo "YES" || echo "NO")"
echo "Warning text: $WARNING"

# Expected: status = "fallback", warning contains "vision"
if [[ "$STATUS" == "fallback" ]] && [[ "$WARNING" == *"vision"* || "$WARNING" == *"cannot"* ]]; then
    echo ""
    echo "VERIFICATION: PASS - MiniMax correctly falls back to text-only"
else
    echo ""
    echo "VERIFICATION: REVIEW - Check MiniMax behavior"
fi
EOF
```

### Phase 5 Output

Create file: `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-26-pre/phase5-minimax.json`

```json
{
  "phase": "minimax-fallback-test",
  "timestamp": "2026-01-20T00:00:00Z",
  "provider": "abab6.5s-chat",
  "provider_id": 4,
  "request": {
    "url": "http://localhost:8050/api/media/analyze",
    "media_type": "document",
    "document_url": "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg",
    "prompt": "Describe this image in detail. Include: main subject, composition, colors, style, mood, and any notable elements."
  },
  "response": {
    "model_used": "abab6.5s-chat",
    "status": "fallback",
    "response": "[text-only fallback message]",
    "warning": "MiniMax API does not support vision capabilities",
    "latency_ms": 500,
    "tokens": {
      "prompt": 100,
      "completion": 50,
      "total": 150
    },
    "cost_usd": 0.000015
  },
  "validation": {
    "status": "passed",
    "checks": {
      "model_correct": true,
      "status_fallback": true,
      "warning_present": true,
      "latency_acceptable": true
    }
  }
}
```

### Phase 5 Verification Commands

```bash
# Quick verification
ssh devmaster << 'EOF'
CDN_URL="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"

echo -n "[MiniMax] Response Status: "
STATUS=$(curl -s -X POST http://localhost:8050/api/media/analyze \
  -H 'Content-Type: application/json' \
  -d "{\"media_type\": \"document\", \"media_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\"}" \
  | jq -r '.status')

if [ "$STATUS" = "fallback" ]; then
    echo "PASS (fallback - expected for MiniMax)"
else
    echo "UNEXPECTED (got: $STATUS)"
fi

echo -n "[MiniMax] Warning Present: "
WARNING=$(curl -s -X POST http://localhost:8050/api/media/analyze \
  -H 'Content-Type: application/json' \
  -d "{\"media_type\": \"document\", \"media_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\"}" \
  | jq -r '.warning // empty')

if [ -n "$WARNING" ]; then
    echo "PASS ($WARNING)"
else
    echo "FAIL (no warning returned)"
fi
EOF
```

---

## Phase 6: Comprehensive Fallback Chain Test

**Duration**: 2-5 minutes
**Objective**: Test full chain sequentially

### Tasks

#### 6.1: Execute Full Chain Test (From Handoff Lines 223-254)

```bash
ssh devmaster << 'EOF'
CDN_URL="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"

echo "=============================================="
echo "=== VISION FALLBACK CHAIN COMPREHENSIVE TEST ==="
echo "=============================================="
echo "Test Image: $CDN_URL"
echo "Start Time: $(date -Iseconds)"
echo ""

# Test 1: Qwen3-VL (Primary)
echo -n "[1/4] Qwen3-VL (primary): "
Qwen_STATUS=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image in detail\"}" \
  -w "%{http_code}" -o /tmp/qwen_response.json)
echo "HTTP $Qwen_STATUS"
Qwen_MODEL=$(cat /tmp/qwen_response.json | jq -r '.model_used')
echo "      Model: $Qwen_MODEL"

# Test 2: Gemini 2.5 Flash
echo -n "[2/4] Gemini 2.5 Flash: "
GEMINI_STATUS=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\", \"model\": \"gemini-2.5-flash\"}" \
  -w "%{http_code}" -o /tmp/gemini_response.json)
echo "HTTP $GEMINI_STATUS"
GEMINI_MODEL=$(cat /tmp/gemini_response.json | jq -r '.model_used')
echo "      Model: $GEMINI_MODEL"

# Test 3: GPT-5 Mini
echo -n "[3/4] GPT-5 Mini: "
GPT_STATUS=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\", \"model\": \"gpt-5-mini\"}" \
  -w "%{http_code}" -o /tmp/gpt_response.json)
echo "HTTP $GPT_STATUS"
GPT_MODEL=$(cat /tmp/gpt_response.json | jq -r '.model_used')
echo "      Model: $GPT_MODEL"

# Test 4: MiniMax (text-only fallback)
echo -n "[4/4] MiniMax (text-only fallback): "
MINIMAX_STATUS=$(curl -s -X POST http://localhost:8050/api/media/analyze \
  -H 'Content-Type: application/json' \
  -d "{\"media_type\": \"document\", \"media_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\"}" \
  -w "%{http_code}" -o /tmp/minimax_response.json)
echo "HTTP $MINIMAX_STATUS"
MINIMAX_MODEL=$(cat /tmp/minimax_response.json | jq -r '.model_used')
echo "      Model: $MINIMAX_MODEL"

echo ""
echo "=============================================="
echo "=== TEST COMPLETE ==="
echo "End Time: $(date -Iseconds)"
echo "=============================================="
EOF
```

#### 6.2: Aggregate Results

```bash
ssh devmaster << 'EOF'
# Aggregate all test results
echo "=== AGGREGATED TEST RESULTS ==="

echo ""
echo "Qwen3-VL (Primary):"
cat /tmp/qwen_response.json | jq '{model: .model_used, status: .status, latency_ms: .latency_ms, tokens: .tokens, cost_usd: .cost_usd}'

echo ""
echo "Gemini 2.5 Flash:"
cat /tmp/gemini_response.json | jq '{model: .model_used, status: .status, latency_ms: .latency_ms, tokens: .tokens, cost_usd: .cost_usd}'

echo ""
echo "GPT-5 Mini:"
cat /tmp/gpt_response.json | jq '{model: .model_used, status: .status, latency_ms: .latency_ms, tokens: .tokens, cost_usd: .cost_usd}'

echo ""
echo "MiniMax (Text-Only Fallback):"
cat /tmp/minimax_response.json | jq '{model: .model_used, status: .status, warning: .warning, latency_ms: .latency_ms, tokens: .tokens, cost_usd: .cost_usd}'

echo ""
echo "=== SUMMARY ==="
echo "Providers Tested: 4/4"
echo "Successful (success): $(cat /tmp/qwen_response.json /tmp/gemini_response.json /tmp/gpt_response.json | jq -r '.status' | grep -c success) vision providers"
echo "Fallback (text-only): $(cat /tmp/minimax_response.json | jq -r '.status' | grep -c fallback) providers"
echo "Total Latency: $(($(cat /tmp/qwen_response.json | jq -r '.latency_ms') + $(cat /tmp/gemini_response.json | jq -r '.latency_ms') + $(cat /tmp/gpt_response.json | jq -r '.latency_ms') + $(cat /tmp/minimax_response.json | jq -r '.latency_ms')))ms"
EOF
```

### Phase 6 Output

Create file: `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-26-pre/phase6-chain-summary.json`

```json
{
  "phase": "comprehensive-chain-test",
  "timestamp": "2026-01-20T00:00:00Z",
  "test_run": {
    "test_image": "https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg",
    "start_time": "2026-01-20T00:00:00Z",
    "end_time": "2026-01-20T00:00:00Z"
  },
  "providers": {
    "qwen3-vl": {
      "provider_id": 1,
      "model": "qwen3-vl-30b-a3b-instruct",
      "status": "success",
      "latency_ms": 2500,
      "tokens": 1850,
      "cost_usd": 0.00057
    },
    "gemini-2-5-flash": {
      "provider_id": 2,
      "model": "gemini-2.5-flash-exp",
      "status": "success",
      "latency_ms": 1800,
      "tokens": 1600,
      "cost_usd": 0.00052
    },
    "gpt-5-mini": {
      "provider_id": 3,
      "model": "openai/gpt-5-mini",
      "status": "success",
      "latency_ms": 3000,
      "tokens": 1700,
      "cost_usd": 0.00129
    },
    "minimax": {
      "provider_id": 4,
      "model": "abab6.5s-chat",
      "status": "fallback",
      "warning": "MiniMax does not support vision capabilities",
      "latency_ms": 500,
      "tokens": 150,
      "cost_usd": 0.000015
    }
  },
  "summary": {
    "providers_tested": 4,
    "vision_success": 3,
    "text_only_fallback": 1,
    "total_latency_ms": 7800,
    "total_cost_usd": 0.002395,
    "success_rate": "75%"
  },
  "chain_validation": {
    "all_providers_responded": true,
    "fallback_behavior_correct": true,
    "provider_order_preserved": true
  }
}
```

### Phase 6 Verification Commands

```bash
# Final comprehensive verification
ssh devmaster << 'EOF'
CDN_URL="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"

echo "=============================================="
echo "=== FINAL CHAIN VERIFICATION ==="
echo "=============================================="

PASS_COUNT=0
FAIL_COUNT=0

# Test 1: Qwen3-VL
echo -n "[1] Qwen3-VL: "
STATUS=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\"}" \
  | jq -r '.status')
if [ "$STATUS" = "success" ]; then
    echo "PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo "FAIL (status: $STATUS)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 2: Gemini 2.5 Flash
echo -n "[2] Gemini 2.5: "
STATUS=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\", \"model\": \"gemini-2.5-flash\"}" \
  | jq -r '.status')
if [ "$STATUS" = "success" ]; then
    echo "PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo "FAIL (status: $STATUS)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 3: GPT-5 Mini
echo -n "[3] GPT-5 Mini: "
STATUS=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\", \"model\": \"gpt-5-mini\"}" \
  | jq -r '.status')
if [ "$STATUS" = "success" ]; then
    echo "PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo "FAIL (status: $STATUS)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 4: MiniMax (expected fallback)
echo -n "[4] MiniMax: "
STATUS=$(curl -s -X POST http://localhost:8050/api/media/analyze \
  -H 'Content-Type: application/json' \
  -d "{\"media_type\": \"document\", \"media_url\": \"$CDN_URL\", \"prompt\": \"Describe this image\"}" \
  | jq -r '.status')
if [ "$STATUS" = "fallback" ]; then
    echo "PASS (fallback expected)"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo "FAIL (expected fallback, got: $STATUS)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

echo ""
echo "=============================================="
echo "VERIFICATION RESULTS: $PASS_COUNT passed, $FAIL_COUNT failed"
echo "Chain Status: $([ $FAIL_COUNT -eq 0 ] && echo "ALL PASSED" || echo "NEEDS REVIEW")"
echo "=============================================="
EOF
```

---

# Test Script Automation

## Complete Test Script

Create file: `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-26-pre/test-vision-fallback-chain.sh`

```bash
#!/bin/bash
# Vision Fallback Chain Comprehensive Test
# Task: runpod-ma-26

set -e

CDN_URL="https://hdd.automatic.picturelle.com/af/test-cases/vision-test.jpg"
OUTPUT_DIR="/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-26-pre"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "=============================================="
echo "=== VISION FALLBACK CHAIN TEST ==="
echo "=============================================="
log_info "Test Image: $CDN_URL"
log_info "Output Directory: $OUTPUT_DIR"
log_info "Start Time: $(date -Iseconds)"
echo ""

# Initialize results
RESULTS='{"test_run": {"timestamp": "'$(date -Iseconds)'", "image_url": "'$CDN_URL'"}, "providers": {}}'

# Test Qwen3-VL
log_info "Testing Qwen3-VL (Primary)..."
Qwen_START=$(date +%s%3N)
Qwen_RESPONSE=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image in detail\"}")
Qwen_END=$(date +%s%3N)
Qwen_LATENCY=$((Qwen_END - Qwen_START))
Qwen_STATUS=$(echo "$Qwen_RESPONSE" | jq -r '.status')
Qwen_MODEL=$(echo "$Qwen_RESPONSE" | jq -r '.model_used')
Qwen_TOKENS=$(echo "$Qwen_RESPONSE" | jq -r '.tokens.total')
Qwen_COST=$(echo "$Qwen_RESPONSE" | jq -r '.cost_usd')

echo "  Model: $Qwen_MODEL"
echo "  Status: $Qwen_STATUS"
echo "  Latency: ${Qwen_LATENCY}ms"
echo "  Tokens: $Qwen_TOKENS"
echo "  Cost: $Qwen_COST USD"

RESULTS=$(echo "$RESULTS" | jq ".providers[\"qwen3-vl\"] = {model: \"$Qwen_MODEL\", status: \"$Qwen_STATUS\", latency_ms: $Qwen_LATENCY, tokens: $Qwen_TOKENS, cost_usd: $Qwen_COST}")
echo ""

# Test Gemini 2.5 Flash
log_info "Testing Gemini 2.5 Flash..."
GEMINI_START=$(date +%s%3N)
GEMINI_RESPONSE=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image in detail\", \"model\": \"gemini-2.5-flash\"}")
GEMINI_END=$(date +%s%3N)
GEMINI_LATENCY=$((GEMINI_END - GEMINI_START))
GEMINI_STATUS=$(echo "$GEMINI_RESPONSE" | jq -r '.status')
GEMINI_MODEL=$(echo "$GEMINI_RESPONSE" | jq -r '.model_used')
GEMINI_TOKENS=$(echo "$GEMINI_RESPONSE" | jq -r '.tokens.total')
GEMINI_COST=$(echo "$GEMINI_RESPONSE" | jq -r '.cost_usd')

echo "  Model: $GEMINI_MODEL"
echo "  Status: $GEMINI_STATUS"
echo "  Latency: ${GEMINI_LATENCY}ms"
echo "  Tokens: $GEMINI_TOKENS"
echo "  Cost: $GEMINI_COST USD"

RESULTS=$(echo "$RESULTS" | jq ".providers[\"gemini-2-5-flash\"] = {model: \"$GEMINI_MODEL\", status: \"$GEMINI_STATUS\", latency_ms: $GEMINI_LATENCY, tokens: $GEMINI_TOKENS, cost_usd: $GEMINI_COST}")
echo ""

# Test GPT-5 Mini
log_info "Testing GPT-5 Mini..."
GPT_START=$(date +%s%3N)
GPT_RESPONSE=$(curl -s -X POST http://localhost:8050/api/media/documents \
  -H 'Content-Type: application/json' \
  -d "{\"document_url\": \"$CDN_URL\", \"prompt\": \"Describe this image in detail\", \"model\": \"gpt-5-mini\"}")
GPT_END=$(date +%s%3N)
GPT_LATENCY=$((GPT_END - GPT_START))
GPT_STATUS=$(echo "$GPT_RESPONSE" | jq -r '.status')
GPT_MODEL=$(echo "$GPT_RESPONSE" | jq -r '.model_used')
GPT_TOKENS=$(echo "$GPT_RESPONSE" | jq -r '.tokens.total')
GPT_COST=$(echo "$GPT_RESPONSE" | jq -r '.cost_usd')

echo "  Model: $GPT_MODEL"
echo "  Status: $GPT_STATUS"
echo "  Latency: ${GPT_LATENCY}ms"
echo "  Tokens: $GPT_TOKENS"
echo "  Cost: $GPT_COST USD"

RESULTS=$(echo "$RESULTS" | jq ".providers[\"gpt-5-mini\"] = {model: \"$GPT_MODEL\", status: \"$GPT_STATUS\", latency_ms: $GPT_LATENCY, tokens: $GPT_TOKENS, cost_usd: $GPT_COST}")
echo ""

# Test MiniMax (text-only fallback)
log_info "Testing MiniMax (Text-Only Fallback)..."
MINIMAX_START=$(date +%s%3N)
MINIMAX_RESPONSE=$(curl -s -X POST http://localhost:8050/api/media/analyze \
  -H 'Content-Type: application/json' \
  -d "{\"media_type\": \"document\", \"media_url\": \"$CDN_URL\", \"prompt\": \"Describe this image in detail\"}")
MINIMAX_END=$(date +%s%3N)
MINIMAX_LATENCY=$((MINIMAX_END - MINIMAX_START))
MINIMAX_STATUS=$(echo "$MINIMAX_RESPONSE" | jq -r '.status')
MINIMAX_MODEL=$(echo "$MINIMAX_RESPONSE" | jq -r '.model_used')
MINIMAX_WARNING=$(echo "$MINIMAX_RESPONSE" | jq -r '.warning // "none"')
MINIMAX_TOKENS=$(echo "$MINIMAX_RESPONSE" | jq -r '.tokens.total')
MINIMAX_COST=$(echo "$MINIMAX_RESPONSE" | jq -r '.cost_usd')

echo "  Model: $MINIMAX_MODEL"
echo "  Status: $MINIMAX_STATUS"
echo "  Warning: $MINIMAX_WARNING"
echo "  Latency: ${MINIMAX_LATENCY}ms"
echo "  Tokens: $MINIMAX_TOKENS"
echo "  Cost: $MINIMAX_COST USD"

RESULTS=$(echo "$RESULTS" | jq ".providers[\"minimax\"] = {model: \"$MINIMAX_MODEL\", status: \"$MINIMAX_STATUS\", warning: \"$MINIMAX_WARNING\", latency_ms: $MINIMAX_LATENCY, tokens: $MINIMAX_TOKENS, cost_usd: $MINIMAX_COST}")
echo ""

# Calculate summary
TOTAL_LATENCY=$((Qwen_LATENCY + GEMINI_LATENCY + GPT_LATENCY + MINIMAX_LATENCY))
TOTAL_COST=$(echo "$Qwen_COST + $GEMINI_COST + $GPT_COST + $MINIMAX_COST" | bc -l)
SUCCESS_COUNT=$(echo "$Qwen_STATUS $GEMINI_STATUS $GPT_STATUS" | grep -o "success" | wc -l)
FALLBACK_COUNT=$(echo "$MINIMAX_STATUS" | grep -o "fallback" | wc -l)

RESULTS=$(echo "$RESULTS" | jq ".summary = {providers_tested: 4, vision_success: $SUCCESS_COUNT, text_only_fallback: $FALLBACK_COUNT, total_latency_ms: $TOTAL_LATENCY, total_cost_usd: $TOTAL_COST}")

# Save results
echo "$RESULTS" | jq . > "${OUTPUT_DIR}/test-results-${TIMESTAMP}.json"

echo "=============================================="
log_info "TEST COMPLETE"
echo "=============================================="
echo "Results saved to: ${OUTPUT_DIR}/test-results-${TIMESTAMP}.json"
echo ""
echo "Summary:"
echo "  Providers Tested: 4"
echo "  Vision Success: $SUCCESS_COUNT"
echo "  Text-Only Fallback: $FALLBACK_COUNT"
echo "  Total Latency: ${TOTAL_LATENCY}ms"
echo "  Total Cost: $TOTAL_COST USD"
echo "  Success Rate: $((SUCCESS_COUNT * 25))%"
echo ""

# Exit with appropriate code
if [ $SUCCESS_COUNT -eq 3 ]; then
    log_info "CHAIN TEST PASSED"
    exit 0
else
    log_error "CHAIN TEST NEEDS REVIEW - $((3 - SUCCESS_COUNT)) provider(s) failed"
    exit 1
fi
```

### Run Test Script

```bash
# Make executable
chmod +x /home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-26-pre/test-vision-fallback-chain.sh

# Execute (requires SSH to devmaster)
scp /home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-26-pre/test-vision-fallback-chain.sh devmaster:/tmp/
ssh devmaster 'chmod +x /tmp/test-vision-fallback-chain.sh && /tmp/test-vision-fallback-chain.sh'
```

---

# Risk Assessment

## Risk Register

| ID | Risk | Impact | Probability | Severity | Mitigation |
|----|------|--------|-------------|----------|------------|
| R1 | Qwen3-VL API timeout | High | Low | Medium | Fallback to Gemini 2.5 Flash |
| R2 | Google Vertex AI auth failure | Medium | Medium | Medium | Fallback to Google AI Studio |
| R3 | OpenRouter rate limiting | Medium | Medium | Medium | Add retry with backoff |
| R4 | MiniMax returns unexpected format | Low | Low | Low | Parse with flexible schema |
| R5 | Test image URL inaccessibility | High | Low | High | Verify URL before testing |
| R6 | Network latency affecting results | Medium | Medium | Low | Record actual latency for comparison |

## Contingency Plans

### R1: Qwen3-VL Timeout

**Trigger:** Qwen3-VL takes > 30 seconds

**Recovery:**
```python
# In prompt_router.py
async def call_qwen3_vl(image_url, prompt, timeout=30):
    try:
        return await asyncio.wait_for(
            openrouter_call("qwen3-vl-30b-a3b-instruct", prompt, image_url),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning("Qwen3-VL timeout, falling back to Gemini")
        return await call_gemini_2_5_flash(image_url, prompt)
```

### R2: Google Vertex AI Auth Failure

**Trigger:** 401 Unauthorized from Vertex AI

**Recovery:**
```python
# In gemini_provider.py
async def call_gemini(image_url, prompt):
    try:
        return await vertex_ai_call(image_url, prompt)
    except UnauthorizedError:
        logger.warning("Vertex AI auth failed, falling back to AI Studio")
        return await ai_studio_call("gemini-2.5-flash-exp", prompt, image_url)
```

### R5: Test Image Inaccessible

**Trigger:** HTTP 404 or 403 from CDN

**Recovery:**
```bash
# Use backup test image
BACKUP_URL="https://hdd.automatic.picturelle.com/af/test-cases/vision-test-backup.jpg"

# Or generate test image locally
ssh devmaster 'docker exec media-analysis-api python3 -c "
from PIL import Image
import base64
img = Image.new('RGB', (640, 480), color='red')
img.save('/tmp/test-image.jpg')
with open('/tmp/test-image.jpg', 'rb') as f:
    print(base64.b64encode(f.read()).decode())
"'
```

---

# Verification Checklist

## Pre-Test Checklist

- [ ] Container running on port 8050
- [ ] Health endpoint returns OK
- [ ] All API keys configured (OpenRouter, Google, MiniMax)
- [ ] Test image URL accessible (HTTP 200)
- [ ] Temporary directory created for test outputs

## Provider Test Checklist

### Qwen3-VL (Primary)
- [ ] HTTP 200 response
- [ ] Model name matches "qwen3-vl-30b-a3b-instruct"
- [ ] Status is "success"
- [ ] Response contains image description
- [ ] Latency < 30 seconds

### Gemini 2.5 Flash
- [ ] HTTP 200 response
- [ ] Model name matches "gemini-2.5-flash-exp"
- [ ] Status is "success"
- [ ] Response contains image description
- [ ] Latency < 30 seconds

### GPT-5 Mini
- [ ] HTTP 200 response
- [ ] Model name contains "gpt-5-mini"
- [ ] Status is "success"
- [ ] Response contains image description
- [ ] Latency < 30 seconds

### MiniMax (Text-Only)
- [ ] HTTP 200 response
- [ ] Model name matches "abab6.5s-chat"
- [ ] Status is "fallback"
- [ ] Warning indicates no vision support
- [ ] Latency < 10 seconds

## Post-Test Checklist

- [ ] All results saved to output directory
- [ ] Summary metrics calculated
- [ ] Chain behavior validated
- [ ] Cost analysis completed
- [ ] Recommendations documented

---

# Output Artifacts

## Files Generated

| File | Description | Phase |
|------|-------------|-------|
| `phase1-verification.json` | Pre-test environment checks | Phase 1 |
| `phase2-qwen3-vl.json` | Qwen3-VL test results | Phase 2 |
| `phase3-gemini-flash.json` | Gemini 2.5 Flash test results | Phase 3 |
| `phase4-gpt5-mini.json` | GPT-5 Mini test results | Phase 4 |
| `phase5-minimax.json` | MiniMax fallback test results | Phase 5 |
| `phase6-chain-summary.json` | Complete chain summary | Phase 6 |
| `test-results-{TIMESTAMP}.json` | Automated test output | Phase 6 |
| `test-vision-fallback-chain.sh` | Test automation script | N/A |

## Final Report

Create file: `/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-26.md`

This document serves as the comprehensive PRD for vision fallback chain testing.

---

# Document End

**PRD Version:** 1.0
**Created:** 2026-01-20
**Author:** $USER
**Model:** claude-sonnet-4-5-20250929
**Task ID:** runpod-ma-26

---

**Next Actions:**
1. Execute Phase 1: Pre-Test Verification
2. Execute Phases 2-5: Individual Provider Tests
3. Execute Phase 6: Comprehensive Chain Test
4. Generate Final Report
5. Close bead runpod-ma-26

