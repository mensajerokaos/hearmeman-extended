---
task: runpod-ma-28 Caddyfile Configuration
agent: hc (headless claude)
model: claude-opus-4-5-20251101
timestamp: 2026-01-20T12:00:00Z
status: completed
---

# runpod-ma-28: Caddyfile Configuration

## Overview
Simple Caddyfile for media-analysis.af.automatic.picturelle.com reverse proxying to FastAPI on port 8050.

## Caddyfile

```caddyfile
media-analysis.af.automatic.picturelle.com {
    reverse_proxy localhost:8050 {
        header_up Host {host}
        header_up X-Real-IP {remote}
    }

    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
    }

    header {
        Strict-Transport-Security "max-age=31536000"
        X-Content-Type-Options nosniff
    }

    rate_limit {
        zone api_limit {
            key {remote_host}
            events 1000
            window 1s
        }
    }
}
```

## Deployment Steps

```bash
# 1. Create Caddyfile
ssh devmaster 'cat > /opt/services/media-analysis/Caddyfile << "EOF"
media-analysis.af.automatic.picturelle.com {
    reverse_proxy localhost:8050 {
        header_up Host {host}
        header_up X-Real-IP {remote}
    }

    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
    }

    header {
        Strict-Transport-Security "max-age=31536000"
        X-Content-Type-Options nosniff
    }

    rate_limit {
        zone api_limit {
            key {remote_host}
            events 1000
            window 1s
        }
    }
}
EOF'

# 2. Validate syntax
ssh devmaster 'caddy validate --config /opt/services/media-analysis/Caddyfile'

# 3. Deploy to Caddy config directory
ssh devmaster 'cp /opt/services/media-analysis/Caddyfile /opt/clients/af/Caddyfile.d/media-analysis.caddyfile'

# 4. Reload Caddy
ssh devmaster 'caddy reload --config /opt/clients/af/Caddyfile'

# 5. Verify HTTPS endpoint
curl -I https://media-analysis.af.automatic.picturelle.com/health
```

## Success Criteria

- [ ] Caddyfile validates without errors
- [ ] HTTPS certificate issued via Cloudflare DNS
- [ ] /health endpoint returns 200
- [ ] Rate limit active (1000 req/s)
