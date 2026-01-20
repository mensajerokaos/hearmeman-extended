# Research Findings: Caddyfile Configuration for media-analysis.af.automatic.picturelle.com

## Executive Summary

Research conducted for deploying a Caddy reverse proxy with Cloudflare DNS TLS for the media-analysis API service. Key findings indicate that a custom Caddy build is required for Cloudflare DNS support, rate limiting should be handled via Cloudflare's edge, and comprehensive security headers are natively supported.

## Domain Details

| Attribute | Value |
|-----------|-------|
| **Domain** | media-analysis.af.automatic.picturelle.com |
| **Backend Service** | media-analysis-api |
| **Port** | 8050 |
| **Protocol** | HTTPS (TLS via Cloudflare DNS) |

## Finding 1: Cloudflare DNS Provider Requirement

### Current State
The official Caddy Docker image does NOT include the Cloudflare DNS provider module by default.

### Solution
A custom Caddy build is required using `xcaddy` with the Cloudflare DNS plugin.

### Implementation Approach
```dockerfile
FROM caddy:builder AS builder
RUN xcaddy build --with github.com/caddy-dns/cloudflare

FROM caddy:2.8
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
```

### Risks
- Additional build complexity in CI/CD pipeline
- Must rebuild image when Caddy version updates

### Mitigation
- Use Docker layer caching effectively
- Pin Caddy version for stability

## Finding 2: Rate Limiting Strategy

### Analysis
Caddy's Caddyfile format does not natively support request rate limiting. Options evaluated:

| Approach | Pros | Cons |
|----------|------|------|
| Cloudflare Rate Limiting | No infra changes, edge-level | 3 rules free tier |
| Nginx upstream | Full control | Additional component |
| Application-level | Precise control | Code changes needed |
| Caddy middleware | Native | Requires Go development |

### Recommendation
**Use Cloudflare Rate Limiting** for this deployment:
- Simplicity: No additional infrastructure
- Effectiveness: Blocks at edge, reduces load
- Configurability: Adjustable via Cloudflare dashboard
- Cost: Included with existing Cloudflare setup

### Configuration Plan
1. Create Cloudflare Rate Liming rule in dashboard
2. Set threshold: 100 requests/minute per IP
3. Action: Challenge or Block based on severity

## Finding 3: Security Headers

### Required Headers Identified

| Header | Value | Purpose |
|--------|-------|---------|
| Strict-Transport-Security | `max-age=31536000; includeSubDomains; preload` | Enforce HTTPS |
| X-Content-Type-Options | `nosniff` | Prevent MIME sniffing |
| X-Frame-Options | `SAMEORIGIN` | Prevent clickjacking |
| Referrer-Policy | `strict-origin-when-cross-origin` | Control referrer info |
| Permissions-Policy | Disabled features list | Restrict browser features |
| Content-Security-Policy | `default-src 'self'` | XSS prevention |
| Cache-Control | `no-store, no-cache` | API response caching |
| -Server | (remove) | Hide server version |

### Implementation
All headers configured in Caddyfile `header` directive block.

## Finding 4: Docker Deployment Strategy

### Service Configuration
```yaml
services:
  caddy:
    image: caddy-cloudflare-custom:latest
    build:
      context: .
      dockerfile: Caddyfile.cloudflare
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - ./data:/data
    environment:
      - CLOUDFLARE_API_TOKEN=${CLOUDFLARE_API_TOKEN}
    restart: unless-stopped
```

### Required Files
1. `/opt/services/media-analysis/Caddyfile` - Main configuration
2. `/opt/services/media-analysis/Dockerfile.caddy` - Custom build
3. `/opt/services/media-analysis/.env` - Environment variables

## Finding 5: TLS Certificate Management

### Automatic TLS
- Caddy will obtain certificates automatically via Cloudflare DNS challenge
- No manual certificate management required
- Certificates cached in `/data/caddy` volume

### Renewal
- Automatic renewal before expiration (typically 60 days)
- No manual intervention needed

## Risk Assessment Summary

| Risk | Severity | Mitigation |
|------|----------|------------|
| Cloudflare API token exposure | Medium | Use Docker secrets/environment |
| Rate limiting gaps | Medium | Cloudflare edge rate limiting |
| HSTS preload issues | Low | Test before enabling preload |
| Caddy version drift | Low | Pin version in Dockerfile |
| DNS propagation delays | Low | Verify DNS before deployment |

## References

1. https://github.com/caddy-dns/cloudflare
2. https://caddyserver.com/docs/caddyfile/directives/tls
3. https://developers.cloudflare.com/fundamentals/reference/policies-compliances/
4. https://cheatsheetseries.owasp.org/cheatsheets/secure_响应头.html
