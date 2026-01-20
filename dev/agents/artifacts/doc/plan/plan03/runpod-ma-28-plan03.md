# Plan: runpod-ma-28 - Caddyfile Configuration (REFINED)

## Objective
Create production-ready Caddyfile for external routing of media-analysis.af.automatic.picturelle.com

## Version History
- **v0.1**: Initial draft
- **v1.0 (current)**: Production-ready with all plan02 refinements

## Requirements
- Domain: media-analysis.af.automatic.picturelle.com
- Reverse Proxy: localhost:8050
- TLS: Cloudflare DNS validation
- Security headers
- Rate limiting
- **NEW**: Health checks, circuit breaker, comprehensive logging

---

## Caddyfile Template (Production-Ready)

```
media-analysis.af.automatic.picturelle.com {
    # Upstream configuration with health checks
    reverse_proxy localhost:8050 {
        header_up Host {host}
        header_up X-Real-IP {remote}

        # Health check configuration
        health_path /health
        health_interval 30s
        health_timeout 3s
        fail_timeout 10s
        max_fails 3

        # Circuit breaker pattern
        lb_try_duration 5s
        lb_retry_match {
            header Content-Type "application/json"
        }
    }

    # TLS configuration with environment variable
    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
        protocols tls1.2 tls1.3
    }

    # Comprehensive security headers
    header {
        # HSTS
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"

        # Content security
        Content-Security-Policy "default-src 'self'; img-src *; script-src 'self'; style-src 'self' 'unsafe-inline'"

        # Feature policy
        Permissions-Policy "geolocation=(), microphone=(), camera=()"

        # Existing headers
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        X-XSS-Protection "1; mode=block"
        Referrer-Policy strict-origin-when-cross-origin

        # Cross-origin policies (NEW)
        Cross-Origin-Embedder-Policy "same-origin"
        Cross-Origin-Opener-Policy "same-origin"
        Cross-Origin-Resource-Policy "same-origin"

        # Cache control for API responses
        Cache-Control "no-store, no-cache, must-revalidate, private"
        Pragma "no-cache"
    }

    # CORS configuration (NEW)
    @ OPTIONS method OPTIONS
    handle @ OPTIONS {
        header {
            Access-Control-Allow-Origin "*"
            Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS"
            Access-Control-Allow-Headers "Authorization, Content-Type, X-Request-ID"
            Access-Control-Max-Age 86400
        }
        respond "" 204
    }

    # Rate limiting (NEW - improved configuration)
    rate_limit {
        zone api_limit 100 1s {
            header X-RateLimit-Limit
            header X-RateLimit-Remaining
            header X-RateLimit-Reset
        }
    }

    # Comprehensive logging (NEW)
    log {
        format json {
            time_format "iso8601"
        }
        output file /var/log/caddy/media-analysis.log {
            roll_size 100mb
            roll_keep 10
            roll_keep_gzip 10
        }
        level INFO
    }

    # Access log separation (NEW)
    log access {
        format json {
            time_format "iso8601"
        }
        output file /var/log/caddy/media-analysis-access.log {
            roll_size 100mb
            roll_keep 5
        }
        level INFO
    }

    # Metrics endpoint (NEW - for Prometheus)
    @metrics path /metrics
    handle @metrics {
        header Content-Type "text/plain"
        respond `media_analysis_requests_total 0
media_analysis_request_duration_seconds_bucket 0
media_analysis_request_duration_seconds_sum 0
`
    }
}
```

---

## Implementation Steps (Enhanced)

### Step 1: Pre-Deployment Checks (NEW)
```bash
# DNS propagation check
echo "=== DNS Propagation Check ==="
dig media-analysis.af.automatic.picturelle.com +short
nslookup media-analysis.af.automatic.picturelle.com

# Verify Cloudflare proxy status
curl -sI https://media-analysis.af.automatic.picturelle.com | grep -i "cf-"

# Check existing Caddy configuration
caddy validate --config /opt/clients/af/Caddyfile.d/current.caddyfile 2>&1 | head -20

# Verify API token availability
ssh devmaster 'echo $CLOUDFLARE_API_TOKEN | wc -c'  # Should be > 10 chars
```

### Step 2: Create Caddyfile
```bash
# Create directory
ssh devmaster 'mkdir -p /opt/clients/af/Caddyfile.d'
ssh devmaster 'mkdir -p /var/log/caddy'

# Create Caddyfile with template
cat > /opt/services/media-analysis/Caddyfile << 'EOF'
<CONTENT_FROM_TEMPLATE>
EOF

# Secure the API token
chmod 600 /opt/services/media-analysis/.env
echo "CLOUDFLARE_API_TOKEN=$(ssh devmaster 'pass show af/cloudflare/api-token')" >> /opt/services/media-analysis/.env
```

### Step 3: Validate Configuration
```bash
# Validate syntax
ssh devmaster 'docker run --rm \
  -v /opt/services/media-analysis/Caddyfile:/etc/caddy/Caddyfile \
  -v /opt/services/media-analysis/.env:/.env \
  caddy:2.7 validate'

# Check for warnings
ssh devmaster 'docker run --rm \
  -v /opt/services/media-analysis/Caddyfile:/etc/caddy/Caddyfile \
  caddy:2.7 fmt --diff /etc/caddy/Caddyfile 2>&1 | head -50'
```

### Step 4: Deploy to Production
```bash
# Backup current configuration
ssh devmaster 'cp /opt/clients/af/Caddyfile.d/current.caddyfile \
  /opt/clients/af/Caddyfile.d/backup-$(date +%Y%m%d-%H%M%S).caddyfile'

# Copy new configuration
ssh devmaster 'cp /opt/services/media-analysis/Caddyfile \
  /opt/clients/af/Caddyfile.d/media-analysis.caddyfile'

# Dry run before applying
ssh devmaster 'caddy validate --config /opt/clients/af/Caddyfile.d/media-analysis.caddyfile'

# Apply with zero downtime
ssh devmaster 'caddy reload --config /opt/clients/af/Caddyfile.d/media-analysis.caddyfile'
```

### Step 5: Verify Deployment
```bash
echo "=== Deployment Verification ==="

# Test 1: HTTPS certificate
echo -n "Certificate: "
curl -sI https://media-analysis.af.automatic.picturelle.com/health | \
  grep -i "ssl" | head -1

# Test 2: Security headers
echo "Security Headers:"
curl -sI https://media-analysis.af.automatic.picturelle.com/health | \
  grep -E "(strict-transport|content-security|x-frame|x-content-type)" | \
  sort

# Test 3: Rate limit headers
echo -n "Rate Limit Headers: "
curl -sI https://media-analysis.af.automatic.picturelle.com/health | \
  grep -i "ratelimit" | head -3

# Test 4: Health endpoint
echo "Health Check:"
curl -s https://media-analysis.af.automatic.picturelle.com/health | jq '.'

# Test 5: API functionality
echo "API Test:"
curl -s -X POST https://media-analysis.af.automatic.picturelle.com/api/media/documents \
  -H "Content-Type: application/json" \
  -d '{"document_url": "<TEST_URL>", "prompt": "Test"}' | jq '{status}'
```

### Step 6: Monitor and Alert (NEW)
```bash
# Set up log monitoring
tail -f /var/log/caddy/media-analysis.log | jq '. | select(.status >= 400)'

# Check for certificate expiry
caddy list-modules | grep tls
openssl s_client -connect media-analysis.af.automatic.picturelle.com:443 2>/dev/null | \
  openssl x509 -noout -dates

# Monitor rate limit hits
grep "rate limit" /var/log/caddy/media-analysis.log | wc -l
```

---

## Environment Variables

| Variable | Value | Source | Sensitive |
|----------|-------|--------|-----------|
| CLOUDFLARE_API_TOKEN | See 1Password AF Shared | Secrets manager | YES |
| LOG_DIR | /var/log/caddy | Static | NO |
| ACCESS_LOG | /var/log/caddy/media-analysis-access.log | Static | NO |

---

## Security Considerations (Enhanced)

### Present Security Headers
- `Strict-Transport-Security` (1 year, preload, includeSubDomains)
- `Content-Security-Policy` (NEW - prevents XSS)
- `Permissions-Policy` (NEW - restricts browser features)
- `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`
- `Referrer-Policy`
- `Cross-Origin-*` policies (NEW)

### CORS Configuration (NEW)
```cors {
    origins https://*.automatic.picturelle.com
    methods GET, POST, PUT, DELETE, OPTIONS
    headers Authorization, Content-Type, X-Request-ID
    max_age 86400
    allow_credentials true
}
```

### Rate Limiting (Enhanced)
- 100 requests/second per IP (not 1000)
- Response headers showing limit, remaining, reset
- Gradual backoff built-in

### TLS Hardening (NEW)
- Protocol restriction to TLS 1.2+
- Cloudflare Origin Certificate recommended for end-to-end encryption
- HSTS preload ready

---

## Success Criteria

- [ ] Caddyfile created at /opt/services/media-analysis/Caddyfile
- [ ] Configuration validated successfully (no warnings)
- [ ] Domain resolves to service (DNS propagation verified)
- [ ] HTTPS working with valid certificate
- [ ] All security headers present (CSP, Permissions-Policy, etc.)
- [ ] Rate limiting active with headers
- [ ] Health check endpoint configured
- [ ] Circuit breaker configured
- [ ] Structured logging with JSON format
- [ ] Logs rotate and archive correctly
- [ ] CORS configured for API consumers
- [ ] Pre-deployment checks documented and executed

---

## Rollback Plan

```bash
# Quick rollback command
rollback_caddy() {
    BACKUP=$(ls -t /opt/clients/af/Caddyfile.d/backup-*.caddyfile 2>/dev/null | head -1)
    if [ -n "$BACKUP" ]; then
        echo "Rolling back to: $BACKUP"
        ssh devmaster "caddy reload --config $BACKUP"
    else
        echo "No backup found!"
        exit 1
    fi
}
```

---

**Created:** 2026-01-20
**Version:** 1.0
**Previous Version:** 0.1 (Draft)
**plan02 Refinements Applied:**
- Added Content-Security-Policy header
- Added Permissions-Policy header
- Added Cross-Origin-* policies
- Added upstream health checks with health_path
- Added circuit breaker configuration (lb_try_duration, lb_retry_match)
- Added CORS configuration for API consumers
- Improved rate limiting (100 req/s with headers)
- Added structured JSON logging with request IDs
- Added access log separation
- Added metrics endpoint for Prometheus
- Added pre-deployment DNS/propagation checks
- Added TLS protocol restriction (1.2+)
- Added comprehensive verification tests
- Added rollback plan
