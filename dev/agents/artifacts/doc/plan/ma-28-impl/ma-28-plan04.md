# Caddyfile Configuration - Implementation Plan

## Executive Summary
Create Caddyfile for reverse proxy and TLS termination in front of media-analysis-api. Enable HTTPS with automatic certificate management.

## Phase 1: Caddyfile Setup

### Step 1.1: Create Caddyfile
- File: /opt/services/media-analysis/Caddyfile
- Code:
```
media-analysis.internal {
    reverse_proxy localhost:8050 {
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
    
    log {
        format json {
            time_format "iso8601"
        }
        output file /var/log/caddy/media-analysis.log {
            roll_size 100mb
            roll_keep 5
        }
    }
}

media-analysis.example.com {
    tls {
        on_demand
    }
    
    reverse_proxy localhost:8050 {
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
    
    rate_limit {
        zone {
            name "api_limit"
            size 1000
            expire 1h
        }
        match {
            path /api/*
        }
    }
}
```

### Step 1.2: Create Docker Compose Integration
- File: /opt/services/media-analysis/docker-compose.yml (update)
- Code:
```yaml
services:
  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_log:/var/log/caddy
    depends_on:
      - media-analysis-api
    environment:
      - ACME_AGREE=true

volumes:
  caddy_data:
  caddy_log:
```

## Phase 2: Security Configuration

### Step 2.1: Create Security Headers
- File: /opt/services/media-analysis/Caddyfile.security
- Code:
```
(security-headers) {
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        Content-Security-Policy "default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
    }
}
```

### Step 2.2: Create Rate Limiting Config
- File: /opt/services/media-analysis/Caddyfile.ratelimit
- Code:
```
(rate-limit-api) {
    rate_limit {
        zone {
            name api_requests
            size 10000
            expire 1m
        }
        match {
            path /api/*
        }
    }
}
```

## Phase 3: Monitoring Integration

### Step 3.1: Create Prometheus Metrics
- File: /opt/services/media-analysis/Caddyfile.metrics
- Code:
```
(prometheus-metrics) {
    metrics /metrics {
        path /metrics
    }
}
```

## Phase 4: Testing

### Step 4.1: Validate Caddyfile Syntax
- Bash: `docker run --rm -v /opt/services/media-analysis/Caddyfile:/etc/caddy/Caddyfile caddy:2-alpine caddy validate`
- Expected: "Validation successful"

### Step 4.2: Test HTTPS Setup
- Bash: `cd /opt/services/media-analysis && docker compose up -d caddy && sleep 10 && curl -I http://localhost:80`
- Expected: 200 OK response

### Step 4.3: Test Security Headers
- Bash: `curl -I http://localhost:80 | grep -i "x-frame-options\|x-content-type"`
- Expected: Security headers present

## Rollback
- Bash: `cd /opt/services/media-analysis && docker compose stop caddy && docker compose rm caddy`
- Verification: Caddy container removed

## Bead Structure
| Phase | Bead Title | Parallel With | Blocked By |
|-------|------------|---------------|------------|
| 1 | [PRD] ma-28 - Caddyfile Setup | - | - |
| 2 | [PRD] ma-28 - Security Config | p1 | - |
| 3 | [PRD] ma-28 - Monitoring | p2 | - |
| 4 | [PRD] ma-28 - Testing | p3 | - |
