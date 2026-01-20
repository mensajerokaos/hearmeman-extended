# Plan: runpod-ma-28 - Caddyfile Configuration (Enhanced)

## Objective
Create Caddyfile for external routing of media-analysis.af.automatic.picturelle.com

## Requirements
- Domain: media-analysis.af.automatic.picturelle.com
- Reverse Proxy: localhost:8050
- TLS: Cloudflare DNS validation
- Security headers (enhanced)
- Rate limiting (tuned)
- CORS support
- Health check endpoints
- Logging and monitoring

## Architecture

```
Internet → Cloudflare → Caddy (devmaster:443) → media-analysis:8050
                    ↓
              Rate Limiting
              Security Headers
              CORS Headers
              Request Logging
```

## Caddyfile Template

```
media-analysis.af.automatic.picturelle.com {
    # Reverse proxy to upstream service
    reverse_proxy localhost:8050 {
        header_up Host {host}
        header_up X-Real-IP {remote}
        header_up X-Forwarded-For {remote}
        header_up X-Forwarded-Proto {scheme}
    }

    # TLS with Cloudflare DNS validation
    tls {
        dns cloudflare <CLOUDFLARE_API_TOKEN>
    }

    # Security Headers (OWASP recommended)
    header {
        # HSTS - Enforce HTTPS (1 year, include subdomains, preload)
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"

        # MIME type sniffing protection
        X-Content-Type-Options "nosniff"

        # Clickjacking protection
        X-Frame-Options "DENY"

        # Legacy XSS protection (still useful for older browsers)
        X-XSS-Protection "1; mode=block"

        # Referrer policy for privacy
        Referrer-Policy "strict-origin-when-cross-origin"

        # Content Security Policy (API-friendly, allows inline for some use cases)
        Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self' https://api.automatic.picturelle.com; frame-ancestors 'none'"

        # Permissions policy (restrict browser features)
        Permissions-Policy "geolocation=(), microphone=(), camera=()"

        # Cross-Origin isolation headers (if needed for shared arrays/web workers)
        # Cross-Origin-Embedder-Policy "require-corp"
        # Cross-Origin-Opener-Policy "same-origin"

        # Cache control for API responses
        Cache-Control "no-store, no-cache, must-revalidate, private"
        Pragma "no-cache"
    }

    # CORS Configuration (for browser-based clients)
    @cors_preflight method OPTIONS {
        method OPTIONS
    }
    handle @cors_preflight {
        header Access-Control-Allow-Origin "*"
        header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS"
        header Access-Control-Allow-Headers "Authorization, Content-Type, X-Request-ID"
        header Access-Control-Max-Age "86400"
        header Content-Length "0"
        header Content-Type "text/plain"
        respond "" 204
    }

    handle /api/* {
        # CORS for API routes (restrict Origin in production)
        header Access-Control-Allow-Origin "https://af.automatic.picturelle.com"
        header Access-Control-Allow-Credentials "true"
        reverse_proxy localhost:8050 {
            header_up Host {host}
            header_up X-Real-IP {remote}
        }
    }

    # Rate Limiting (tuned for API usage)
    # API: 100 req/min per IP (reasonable for most use cases)
    # Burst: Allow short spikes up to 200
    @api_limit {
        path /api/*
    }
    rate_limit @api_limit {
        zone api_rate 100 1m
        zone burst_limit 200 1m
    }

    # WebSocket support (for real-time features)
    @websocket {
        header Connection *Upgrade*
        header Upgrade *websocket*
    }
    handle @websocket {
        reverse_proxy localhost:8050 {
            header_up Host {host}
            header_up X-Real-IP {remote}
        }
    }

    # Health Check Endpoints
    handle /health {
        header Content-Type "application/json"
        respond `{"status": "healthy", "service": "media-analysis", "timestamp": "${time.now}"}` 200 {
            time_format "2006-01-02T15:04:05Z07:00"
        }
    }

    handle /health/ready {
        header Content-Type "application/json"
        # Check upstream is responsive
        reverse_proxy localhost:8050 {
            header_up Host {host}
            transport http {
                health_uri /internal/health
                health_interval 10s
                health_timeout 5s
            }
        }
        respond `{"status": "ready", "service": "media-analysis"}` 200
    }

    handle /health/live {
        header Content-Type "application/json"
        respond `{"status": "alive", "service": "media-analysis"}` 200
    }

    handle /metrics {
        header Content-Type "text/plain"
        # Caddy doesn't have native Prometheus metrics, log-based monitoring instead
        respond "Metrics available via log aggregation" 200
    }

    # Request Logging (structured JSON)
    log {
        format json {
            time_format "iso8601"
        }
        output file /var/log/caddy/media-analysis-access.log {
            roll_size 100mb
            roll_keep 10
            roll_keep_gzip 5
        }
        level INFO
    }

    # Error logging (separate file for debugging)
    log /var/log/caddy/media-analysis-error.log {
        format json {
            time_format "iso8601"
        }
        output file /var/log/caddy/media-analysis-error.log {
            roll_size 50mb
            roll_keep 5
        }
        level ERROR
    }
}
```

## Enhanced Configuration Notes

### Security Headers Detail

| Header | Value | Purpose |
|--------|-------|---------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | Enforce HTTPS, protect against downgrade attacks |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME type sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking via iframe embedding |
| `X-XSS-Protection` | `1; mode=block` | XSS filter for older browsers |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer information leakage |
| `Content-Security-Policy` | `default-src 'self'; ...` | Mitigate XSS and data injection |
| `Permissions-Policy` | `geolocation=(), ...` | Restrict browser features |
| `Cache-Control` | `no-store, no-cache, ...` | Prevent caching of sensitive responses |

### Rate Limiting Tiers

| Endpoint Type | Rate Limit | Burst | Rationale |
|---------------|------------|-------|-----------|
| `/api/*` | 100 req/min | 200 | Standard API client |
| `/health/*` | Unlimited | Unlimited | Health checks must pass |
| WebSocket | 50 conn/min | 100 | Connection establishment |

### CORS Configuration

| Scenario | Origin | Credentials |
|----------|--------|-------------|
| Production API | `https://af.automatic.picturelle.com` | true |
| Development | `*` | true |
| OPTIONS preflight | `*` | N/A (no credentials) |

### Health Check Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `/health` | Basic health check | `{"status": "healthy"}` |
| `/health/ready` | Readiness probe (checks upstream) | `{"status": "ready"}` |
| `/health/live` | Liveness probe | `{"status": "alive"}` |
| `/metrics` | Metrics endpoint (placeholder) | Prometheus-style metrics |

### Logging Configuration

| Log File | Level | Rotation | Purpose |
|----------|-------|----------|---------|
| `media-analysis-access.log` | INFO | 100mb x 10 | Request access logs |
| `media-analysis-error.log` | ERROR | 50mb x 5 | Error and warning logs |

**Log fields captured:**
- `timestamp`: ISO8601 formatted time
- `request.id`: Unique request ID for tracing
- `remote.ip`: Client IP address
- `request.method`: HTTP method
- `request.uri`: Full request URI
- `status`: Response status code
- `duration_ms`: Request duration in milliseconds
- `bytes_sent`: Response size in bytes

## Implementation Steps

### Step 1: Create Caddyfile
```bash
# Create directory on server
ssh devmaster 'mkdir -p /opt/clients/af/Caddyfile.d /var/log/caddy'

# Create Caddyfile from template
cat > /opt/services/media-analysis/Caddyfile << 'EOF'
<CONTENT_FROM_TEMPLATE>
EOF

# Set permissions
ssh devmaster 'chmod 600 /opt/services/media-analysis/Caddyfile'
```

### Step 2: Validate Configuration
```bash
# Validate syntax
ssh devmaster 'docker run --rm -v /opt/services/media-analysis/Caddyfile:/etc/caddy/Caddyfile caddy:2.7 validate'

# Check for common issues
ssh devmaster 'docker run --rm -v /opt/services/media-analysis/Caddyfile:/etc/caddy/Caddyfile caddy:2.7 fmt --check'
```

### Step 3: Deploy to Production
```bash
# Backup existing configuration
ssh devmaster 'cp /opt/clients/af/Caddyfile.d/media-analysis.caddyfile /opt/clients/af/Caddyfile.d/media-analysis.caddyfile.backup 2>/dev/null || true'

# Copy new Caddyfile
ssh devmaster 'cp /opt/services/media-analysis/Caddyfile /opt/clients/af/Caddyfile.d/media-analysis.caddyfile'

# Validate before reload
ssh devmaster 'caddy validate --config /opt/clients/af/Caddyfile.d/media-analysis.caddyfile'

# Reload Caddy (zero-downtime)
ssh devmaster 'caddy reload --config /opt/clients/af/Caddyfile.d/media-analysis.caddyfile'
```

### Step 4: Verify Configuration
```bash
# Test HTTPS and headers
curl -sI https://media-analysis.af.automatic.picturelle.com/health

# Verify security headers present
echo "=== Security Headers ==="
curl -sI https://media-analysis.af.automatic.picturelle.com/health | grep -iE "(strict-transport|x-content-type|x-frame|x-xss|content-security|referrer-policy)"

# Verify rate limiting (make multiple requests)
echo -e "\n=== Rate Limit Test ==="
for i in {1..5}; do
    curl -sI https://media-analysis.af.automatic.picturelle.com/health | grep -iE "(ratelimit|retry-after)" || echo "Request $i: OK"
done

# Test CORS preflight
echo -e "\n=== CORS Preflight Test ==="
curl -X OPTIONS https://media-analysis.af.automatic.picturelle.com/api/test \
    -H "Origin: https://af.automatic.picturelle.com" \
    -H "Access-Control-Request-Method: POST" \
    -sI | grep -iE "(access-control|allow-origin)"

# Test health endpoints
echo -e "\n=== Health Endpoints ==="
echo "Basic: $(curl -s https://media-analysis.af.automatic.picturelle.com/health)"
echo "Live: $(curl -s https://media-analysis.af.automatic.picturelle.com/health/live)"
```

### Step 5: Monitor Logs
```bash
# Tail access logs
ssh devmaster 'tail -f /var/log/caddy/media-analysis-access.log | jq .'

# Check for errors
ssh devmaster 'tail -50 /var/log/caddy/media-analysis-error.log | jq .'
```

## Environment Variables

| Variable | Value | Source | Sensitive |
|----------|-------|--------|-----------|
| `CLOUDFLARE_API_TOKEN` | See 1Password AF Shared | secrets manager | YES |
| `CADDY_LOG_LEVEL` | `INFO` | environment | no |

## Security Considerations

1. **TLS Configuration**
   - Cloudflare DNS challenge (no port 80 needed)
   - Automatic certificate renewal
   - Minimum TLS 1.2+ enforced by Cloudflare

2. **Rate Limiting**
   - Prevents DDoS and brute force attacks
   - Different limits for API vs health endpoints
   - Burst allowance for legitimate spikes

3. **CORS**
   - Strict origin validation in production
   - Preflight caching (86400s = 24 hours)
   - Explicit allowed methods and headers

4. **Logging**
   - JSON format for easy parsing
   - Request IDs for distributed tracing
   - Separate error log for debugging

5. **Headers**
   - Defense in depth with multiple security headers
   - CSP allows necessary sources for API functionality
   - X-Frame-Options prevents embedding

## Monitoring Integration

### Log Aggregation (ELK/Loki)
```json
{
  "index": "caddy-logs",
  "fields": ["@timestamp", "request.id", "remote.ip", "request.method", "request.uri", "status", "duration_ms"]
}
```

### Alert Rules (Prometheus-style)
```yaml
- alert: HighErrorRate
  expr: rate(caddy_response_status_code_bucket{code=~"5.."}[5m]) > 0.1
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High error rate on media-analysis API"

- alert: RateLimitHit
  expr: rate(caddy_http_response_size_count{handler="rate_limit"}[5m]) > 10
  for: 1m
  labels:
    severity: warning
  annotations:
    summary: "Rate limiting triggered frequently"
```

## Success Criteria

- [ ] Caddyfile created at `/opt/services/media-analysis/Caddyfile`
- [ ] Configuration validated successfully (`caddy validate`)
- [ ] Domain resolves to service with valid TLS certificate
- [ ] Security headers present in all responses
- [ ] CORS working correctly for allowed origins
- [ ] Rate limiting active (100 req/min per IP for API)
- [ ] Health endpoints responding correctly
- [ ] Logs writing to `/var/log/caddy/media-analysis-*.log`
- [ ] Zero configuration errors in first 24 hours

## Rollback Plan

If issues occur:

```bash
# Revert to previous config
ssh devmaster 'caddy reload --config /opt/clients/af/Caddyfile.d/media-analysis.caddyfile.backup'

# Or restart container if needed
ssh devmaster 'docker restart caddy-proxy'
```

## Cost Considerations

| Resource | Estimate | Notes |
|----------|----------|-------|
| Cloudflare DNS API | Free | No additional cost |
| Disk (logs) | ~1-5GB/month | 100MB x 10 files, rotated |
| Bandwidth | Included | Cloudflare edge handles SSL |

---
**Created:** 2026-01-20
**Version:** 1.0 (Enhanced)
**Author:** $USER
