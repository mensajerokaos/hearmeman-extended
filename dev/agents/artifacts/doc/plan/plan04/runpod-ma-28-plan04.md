# Plan04: runpod-ma-28 - Caddyfile Configuration

## Final Approval

| Field | Value |
|-------|-------|
| **Bead ID** | runpod-ma-28 |
| **Priority** | P1 |
| **Status** | READY FOR IMPLEMENTATION |
| **Plan Version** | v1.0 |
| **Complexity** | Low (6 steps) |

## Summary

Create production-ready Caddyfile for external routing of media-analysis.af.automatic.picturelle.com

## Implementation Steps

1. **Pre-Deployment Checks**
   - DNS propagation verification
   - Configuration syntax validation
   - API token availability check

2. **Create Caddyfile**
   - Security headers (CSP, Permissions-Policy, etc.)
   - Health checks with circuit breaker
   - Rate limiting with headers
   - CORS configuration
   - Structured JSON logging
   - Metrics endpoint

3. **Validate Configuration**
   - Syntax validation
   - Format checking

4. **Deploy to Production**
   - Backup current config
   - Copy new configuration
   - Zero-downtime reload

5. **Verify Deployment**
   - HTTPS certificate check
   - Security headers verification
   - Rate limit headers check
   - Health endpoint test
   - API functionality test

6. **Monitor and Alert**
   - Log monitoring
   - Certificate expiry check
   - Rate limit hit tracking

## Key Features

| Feature | Status |
|---------|--------|
| Cloudflare DNS validation | Required |
| HSTS (1 year, preload) | Included |
| CSP header | Included |
| Permissions-Policy | Included |
| CORS configuration | Included |
| Rate limiting (100 req/s) | Included |
| Health checks | Included |
| Circuit breaker | Included |
| Structured JSON logging | Included |
| Metrics endpoint | Included |

## Environment Requirements

- Caddy 2.7+
- Cloudflare API token (from 1Password)
- Log directory: /var/log/caddy
- Config directory: /opt/clients/af/Caddyfile.d/

## Approval

- [x] Plan00: Draft created
- [x] Plan01: Enhanced with security
- [x] Plan02: DevOps review complete
- [x] Plan03: All refinements applied
- [ ] **Plan04**: Ready for implementation

**Ready to Execute**: YES
