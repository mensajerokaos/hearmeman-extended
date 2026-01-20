# Enhanced Risk Assessment & Mitigation

## Expanded Risk Scenarios

### R9: Identifier Collision
| Attribute | Value |
|-----------|-------|
| **Risk** | Incomplete identifier rename leaving cotizador references |
| **Impact** | HIGH - Service fails to start or has undefined references |
| **Probability** | MEDIUM - sed patterns may miss edge cases |
| **Severity** | CRITICAL |

**Scenarios:**
1. **Class name collision**: `CotizadorAPI` not fully renamed
   - Manifestation: `NameError: name 'CotizadorAPI' is not defined`
   - Location: Line ~50 in media_analysis_api.py

2. **Module import collision**: `import cotizador` not updated
   - Manifestation: `ModuleNotFoundError: No module named 'cotizador'`
   - Location: Line ~20 in media_analysis_api.py

3. **Logger name collision**: `logging.getLogger("cotizador")` not updated
   - Manifestation: Logger creates duplicate hierarchy
   - Location: Line ~30 in media_analysis_api.py

**Mitigation:**
```bash
# Multi-pass verification with increasing specificity
ssh devmaster 'cd /opt/services/media-analysis && \

# Pass 1: Basic grep
echo "=== Pass 1: Basic cotizador search ===" && \
grep -r "cotizador" api/ --include="*.py" || echo "No basic matches" && \

# Pass 2: Case-sensitive class search
echo "=== Pass 2: Cotizador class search ===" && \
grep -r "Cotizador[A-Z]" api/ --include="*.py" || echo "No class matches" && \

# Pass 3: Module import search
echo "=== Pass 3: Module import search ===" && \
grep -r "^from cotizador\|^import cotizador" api/ --include="*.py" || echo "No import matches" && \

# Pass 4: Endpoint search
echo "=== Pass 4: Endpoint search ===" && \
grep -r "/api/analyze" api/ --include="*.py" || echo "No endpoint matches"'

# Automated fix script
ssh devmaster 'cat > /opt/services/media-analysis/scripts/fix-identifiers.sh << "SCRIPT"
#!/bin/bash
set -e

echo "Running identifier fix..."

# Fix class names
find api/ -name "*.py" -exec sed -i "s/CotizadorAPI/MediaAnalysisAPI/g" {} \;
find api/ -name "*.py" -exec sed -i "s/class Cotizador/class MediaAnalysis/g" {} \;

# Fix imports
find api/ -name "*.py" -exec sed -i "s/from cotizador import/from media_analysis import/g" {} \;
find api/ -name "*.py" -exec sed -i "s/import cotizador/import media_analysis/g" {} \;

# Fix logger
find api/ -name "*.py" -exec sed -i "s/logger = logging.getLogger(\"cotizador\")/logger = logging.getLogger(\"media_analysis\")/g" {} \;

# Fix module references
find api/ -name "*.py" -exec sed -i 's/module="cotizador"/module="media_analysis"/g' {} \;

# Fix variable prefixes
find api/ -name "*.py" -exec sed -i "s/cotizador_/media_analysis_/g" {} \;

echo "Identifier fix complete"
SCRIPT
chmod +x /opt/services/media-analysis/scripts/fix-identifiers.sh'
```

**Verification:**
```bash
ssh devmaster '/opt/services/media-analysis/scripts/fix-identifiers.sh && \
echo "=== Verification ===" && \
grep -r "cotizador\|Cotizador" /opt/services/media-analysis/api/ --include="*.py" | grep -v "^Binary" && \
echo "FAIL: Remaining references" || echo "PASS: No cotizador references"'
```

---

### R10: Network Isolation Failure
| Attribute | Value |
|-----------|-------|
| **Risk** | Container connects to wrong network or has cross-network access |
| **Impact** | MEDIUM - Security boundary violation |
| **Probability** | LOW - Manual configuration error |
| **Severity** | HIGH |

**Scenarios:**
1. **Wrong network assignment**: Container on af-network instead of media-services-network
   - Manifestation: Can resolve cotizador-api hostname
   - Detection: `docker inspect` shows wrong network

2. **External network access**: Container has internet access without Caddy
   - Manifestation: Service responds from external IP
   - Detection: Headers show external IP

**Mitigation:**
```bash
# Pre-deployment network check
ssh devmaster 'cat > /opt/services/media-analysis/scripts/verify-isolation.sh << "SCRIPT"
#!/bin/bash

echo "=== Network Isolation Verification ==="

# Check container exists
if ! docker ps --filter "name=media-analysis-api" | grep -q media-analysis-api; then
    echo "FAIL: Container not running"
    exit 1
fi

# Get container network
CONTAINER_NETWORK=$(docker inspect media-analysis-api --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}')

echo "Container networks: $CONTAINER_NETWORK"

# Check for wrong network
if echo "$CONTAINER_NETWORK" | grep -q "af-network"; then
    echo "FAIL: Container on af-network (security violation)"
    exit 1
fi

# Check for correct network
if echo "$CONTAINER_NETWORK" | grep -q "media-services-network"; then
    echo "PASS: Container on correct network"
else
    echo "FAIL: Container not on media-services-network"
    exit 1
fi

# Test DNS isolation
echo "=== DNS Isolation Test ==="
if docker exec media-analysis-api getent hosts cotizador-api > /dev/null 2>&1; then
    echo "FAIL: Can resolve cotizador-api (isolation broken)"
    exit 1
else
    echo "PASS: Cannot resolve cotizador-api hostname"
fi

# Test connectivity
echo "=== Connectivity Test ==="
if docker exec media-analysis-api ping -c 1 -W 1 cotizador-api > /dev/null 2>&1; then
    echo "FAIL: Can ping cotizador-api (isolation broken)"
    exit 1
else
    echo "PASS: Cannot ping cotizador-api"
fi

echo "=== All Isolation Tests PASSED ==="
SCRIPT
chmod +x /opt/services/media-analysis/scripts/verify-isolation.sh'
```

**Verification:**
```bash
ssh devmaster '/opt/services/media-analysis/scripts/verify-isolation.sh'
```

---

### R11: MiniMax API Failure
| Attribute | Value |
|-----------|-------|
| **Risk** | MiniMax API key invalid, rate limited, or service unavailable |
| **Impact** | MEDIUM - Video analysis degrades to basic processing |
| **Probability** | MEDIUM - API issues are common |
| **Severity** | MEDIUM |

**Scenarios:**
1. **Invalid API key**: 401 Unauthorized response
   - Manifestation: `401 Client Error: Unauthorized`
   - Fix: Update MINIMAX_API_KEY in .env

2. **Rate limiting**: 429 Too Many Requests
   - Manifestation: `429 Client Error: Too Many Requests`
   - Fix: Implement backoff, use fallback

3. **Service outage**: 500 Internal Server Error
   - Manifestation: `500 Server Error`
   - Fix: Fallback to OpenAI/Claude

**Mitigation:**
```python
# In minimax_client.py - Fallback chain implementation

class MiniMaxClient:
    async def chat_with_fallback(self, messages: List[MiniMaxMessage]) -> MiniMaxResponse:
        """Try MiniMax first, then fall back to alternatives."""
        
        # Try MiniMax
        try:
            return await self.chat(messages)
        except MiniMaxAuthenticationError as e:
            logger.error(f"MiniMax auth failed: {e}")
            raise ConfigurationError("Invalid MiniMax API key")
        except MiniMaxRateLimitError as e:
            logger.warning(f"MiniMax rate limited: {e}, falling back")
            return await self.openai_fallback(messages)
        except MiniMaxServerError as e:
            logger.warning(f"MiniMax server error: {e}, falling back")
            return await self.openai_fallback(messages)
    
    async def openai_fallback(self, messages: List[MiniMaxMessage]) -> MiniMaxResponse:
        """Fallback to OpenAI GPT-4."""
        if not self.openai_client:
            raise ServiceUnavailable("No fallback available")
        
        # Convert MiniMax format to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=openai_messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        # Convert back to MiniMax format
        return MiniMaxResponse(
            id=response.id,
            object="chat.completion",
            created=response.created,
            model="gpt-4o-fallback",
            choices=[{"message": {"content": response.choices[0].message.content}}],
            usage={"prompt_tokens": response.usage.prompt_tokens, "completion_tokens": response.usage.completion_tokens}
        )
```

**Verification:**
```bash
ssh devmaster 'cat > /opt/services/media-analysis/scripts/test-minimax.sh << "SCRIPT"
#!/bin/bash

echo "=== MiniMax API Test ==="

# Test 1: Authentication
echo -n "[1/3] Authentication: "
RESPONSE=$(curl -s -X POST "https://api.minimax.chat/v1/chat/completions" \
  -H "Authorization: Bearer ${MINIMAX_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model": "abab6.5s-chat", "messages": [{"role": "user", "content": "test"}]}' \
  -w "%{http_code}" -o /tmp/minimax-response.json)

if [ "$RESPONSE" = "200" ]; then
    echo "PASS"
else
    echo "FAIL ($RESPONSE)"
    cat /tmp/minimax-response.json
fi

# Test 2: Rate limit handling
echo -n "[2/3] Rate limit handling: "
# (Simulated - actual test would require exceeding quota)
echo "SKIP (requires quota exhaustion)"

# Test 3: Fallback chain
echo -n "[3/3] Fallback chain: "
if [ -n "$OPENAI_API_KEY" ]; then
    echo "CONFIGURED"
else
    echo "NOT CONFIGURED (optional)"
fi

echo "=== MiniMax Test Complete ==="
SCRIPT
chmod +x /opt/services/media-analysis/scripts/test-minimax.sh'
```

---

### R12: Frame Extraction Failure
| Attribute | Value |
|-----------|-------|
| **Risk** | FFmpeg fails to extract frames from corrupted/invalid video |
| **Impact** | MEDIUM - Video analysis produces incomplete results |
| **Probability** | MEDIUM - User may upload invalid files |
| **Severity** | MEDIUM |

**Scenarios:**
1. **Corrupted video file**: FFmpeg cannot decode
   - Manifestation: `ffmpeg: Invalid data found when processing input`
   - Fix: Validate file before processing

2. **Unsupported codec**: FFmpeg cannot decode
   - Manifestation: `ffmpeg: unknown decoder`
   - Fix: Reject unsupported formats early

3. **Insufficient frames**: Video too short
   - Manifestation: Zero frames extracted
   - Fix: Validate video duration before extraction

**Mitigation:**
```python
# In media_analysis.py - Video validation and error handling

import ffmpeg
import os

class VideoProcessor:
    async def extract_frames(self, video_path: str, fps: int = 3) -> List[str]:
        """Extract frames with validation and error handling."""
        
        # Validate video file exists
        if not os.path.exists(video_path):
            raise VideoProcessingError(f"Video file not found: {video_path}")
        
        # Validate file size (max 500MB)
        file_size = os.path.getsize(video_path)
        if file_size > 500 * 1024 * 1024:
            raise VideoProcessingError(f"Video file too large: {file_size / 1024 / 1024:.1f}MB (max 500MB)")
        
        # Probe video for validity
        try:
            probe = ffmpeg.probe(video_path)
        except ffmpeg.Error as e:
            raise VideoProcessingError(f"Invalid video file: {e.stderr}")
        
        # Check for video stream
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        if not video_stream:
            raise VideoProcessingError("No video stream found in file")
        
        # Check duration
        duration = float(video_stream.get('duration', 0))
        if duration < 1.0:
            raise VideoProcessingError(f"Video too short: {duration}s (min 1s)")
        
        # Extract frames
        output_pattern = f"/workspace/outputs/frames/frame_%04d.jpg"
        os.makedirs(os.path.dirname(output_pattern), exist_ok=True)
        
        try:
            (
                ffmpeg
                .input(video_path)
                .filter('fps', fps)
                .output(output_pattern, vframes=100)  # Max 100 frames
                .run(quiet=True, capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            raise VideoProcessingError(f"Frame extraction failed: {e.stderr}")
        
        # Return list of extracted frames
        frames = sorted(glob.glob(output_pattern.replace('%04d', '*')))
        return frames
```

**Verification:**
```bash
ssh devmaster 'cat > /opt/services/media-analysis/scripts/test-frame-extraction.sh << "SCRIPT"
#!/bin/bash

echo "=== Frame Extraction Test ==="

# Test 1: Valid video
echo -n "[1/3] Valid video: "
echo "SKIP (requires test video file)"

# Test 2: Corrupted video
echo -n "[2/3] Corrupted video: "
echo "SKIP (requires test corrupted file)"

# Test 3: Short video
echo -n "[3/3] Short video: "
echo "SKIP (requires test short file)"

echo "=== Frame Extraction Test Complete ==="
SCRIPT
chmod +x /opt/services/media-analysis/scripts/test-frame-extraction.sh'
```

---

### R13: Caddyfile Configuration Error
| Attribute | Value |
|-----------|-------|
| **Risk** | Caddyfile has syntax errors or invalid directives |
| **Impact** | LOW - Service won't start, easy to fix |
| **Probability** | MEDIUM - Manual configuration |
| **Severity** | MEDIUM |

**Scenarios:**
1. **Syntax error**: Invalid directive order
   - Manifestation: `Error: adapting config using caddyfile: syntax error`
   - Fix: Validate before deployment

2. **Invalid subdomain**: Domain doesn't exist
   - Manifestation: TLS certificate generation fails
   - Fix: Verify domain DNS before deployment

3. **Reverse proxy misconfiguration**: Wrong upstream
   - Manifestation: 502 Bad Gateway
   - Fix: Verify container name and port

**Mitigation:**
```bash
# Pre-deployment Caddyfile validation
ssh devmaster 'cat > /opt/services/media-analysis/scripts/validate-caddyfile.sh << "SCRIPT"
#!/bin/bash

echo "=== Caddyfile Validation ==="

CADDYFILE="/opt/services/media-analysis/Caddyfile"

# Test 1: Syntax validation
echo -n "[1/3] Syntax check: "
if docker run --rm -v "$CADDYFILE:/etc/caddy/Caddyfile" caddy:2.7 validate 2>&1 | grep -q "validation successful"; then
    echo "PASS"
else
    echo "FAIL"
    docker run --rm -v "$CADDYFILE:/etc/caddy/Caddyfile" caddy:2.7 validate
    exit 1
fi

# Test 2: Subdomain DNS check
echo -n "[2/3] DNS check: "
SUBDOMAIN=$(grep -oP '^\K[a-z-]+\.[a-z.]+' "$CADDYFILE" | head -1)
if host "$SUBDOMAIN" > /dev/null 2>&1; then
    echo "PASS ($SUBDOMAIN resolves)"
else
    echo "WARN ($SUBDOMAIN does not resolve - may be internal DNS)"
fi

# Test 3: Upstream connectivity check
echo -n "[3/3] Upstream check: "
UPSTREAM=$(grep -oP 'reverse_proxy \K[a-z-]+:[0-9]+' "$CADDYFILE")
echo "Configured upstream: $UPSTREAM"
echo "(Verify container name matches: media-analysis-api:8000)"

echo "=== Caddyfile Validation Complete ==="
SCRIPT
chmod +x /opt/services/media-analysis/scripts/validate-caddyfile.sh'
```

**Verification:**
```bash
ssh devmaster '/opt/services/media-analysis/scripts/validate-caddyfile.sh'
```

---

## Risk Matrix Summary

| ID | Risk | Impact | Probability | Severity | Mitigation | Verification |
|----|------|--------|-------------|----------|------------|---------------|
| R1 | Incomplete identifier rename | HIGH | MEDIUM | CRITICAL | Automated grep + sed | grep for cotizador refs |
| R2 | Network isolation failure | MEDIUM | LOW | HIGH | Network inspection | verify-isolation.sh |
| R9 | Identifier collision | HIGH | MEDIUM | CRITICAL | Multi-pass sed | fix-identifiers.sh |
| R10 | Network isolation failure | MEDIUM | LOW | HIGH | Network isolation script | verify-isolation.sh |
| R11 | MiniMax API failure | MEDIUM | MEDIUM | MEDIUM | Fallback chain | test-minimax.sh |
| R12 | Frame extraction failure | MEDIUM | MEDIUM | MEDIUM | Validation + error handling | test-frame-extraction.sh |
| R13 | Caddyfile config error | LOW | MEDIUM | MEDIUM | Pre-deploy validation | validate-caddyfile.sh |
