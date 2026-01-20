# Product Requirements Document: Caddyfile Configuration for media-analysis.af.automatic.picturelle.com

**Document ID**: media-analysis-ma-28
**Date**: 2026-01-20
**Author**: Claude Sonnet 4.5
**Version**: 1.0

---

## 1. Executive Summary

This document specifies the requirements and implementation plan for deploying a Caddy reverse proxy configuration to serve the media-analysis API at `media-analysis.af.automatic.picturelle.com`. The configuration will provide:

- **Reverse proxy** from domain to localhost:8050
- **Automatic TLS** via Cloudflare DNS challenge
- **Security headers** compliant with OWASP recommendations
- **Rate limiting** via Cloudflare edge (recommended approach)

---

## 2. System Architecture

### 2.1 Architecture Diagram

```
                                    ┌─────────────────────────────────────┐
                                    │         Cloudflare CDN              │
                                    │                                     │
                                    │  ┌─────────────────────────────┐    │
                                    │  │     Rate Limiting Rules     │    │
                                    │  │   (100 req/min per IP)      │    │
                                    │  └─────────────────────────────┘    │
                                    │                 ↓                   │
                                    │  ┌─────────────────────────────┐    │
                                    │  │     TLS Termination         │    │
                                    │  │   (Cloudflare Origin Cert)  │    │
                                    │  └─────────────────────────────┘    │
                                    │                 ↓                   │
                                    │  ┌─────────────────────────────┐    │
  Internet ──HTTPS──→  media-analysis.af.automatic.picturelle.com      │
                                    │  │         Caddy Proxy         │    │
                                    │  │    (Cloudflare DNS TLS)     │    │
                                    │  └─────────────────────────────┘    │
                                    │          ↓                  ↓       │
                                    │  ┌──────────────┐  ┌─────────────┐ │
                                    │  │   :80 HTTP   │  │  :443 HTTPS │ │
                                    │  │  (redirect)  │  │   (proxy)   │ │
                                    │  └──────────────┘  └─────────────┘ │
                                    │          ↓                  ↓       │
                                    │  ┌────────────────────────────────┐│
                                    │  │     media-analysis-api         ││
                                    │  │        localhost:8050          ││
                                    │  │                                ││
                                    │  │  ┌──────────────────────────┐  ││
                                    │  │  │  FastAPI Application     │  ││
                                    │  │  │  - Video analysis        │  ││
                                    │  │  │  - Transcription         │  ││
                                    │  │  │  - Frame extraction      │  ││
                                    │  │  └──────────────────────────┘  ││
                                    │  └────────────────────────────────┘│
                                    └─────────────────────────────────────┘
```

### 2.2 Component Inventory

| Component | Location | Purpose |
|-----------|----------|---------|
| `Caddyfile` | `/opt/services/media-analysis/Caddyfile` | Main reverse proxy configuration |
| `Dockerfile.caddy` | `/opt/services/media-analysis/Dockerfile.caddy` | Custom Caddy build with Cloudflare plugin |
| `docker-compose.yml` | `/opt/services/media-analysis/docker-compose.yml` | Service orchestration |
| `.env` | `/opt/services/media-analysis/.env` | Environment variables (tokens) |

### 2.3 Network Flow

```
[Client] → [Cloudflare CDN] → [Rate Limiting] → [TLS Termination] → [Caddy:443] → [API:8050]
                                              ↑                                           ↓
                                    [Cloudflare DNS Challenge] ← [Let's Encrypt] ← [Certificate Auto-Renewal]
```

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | Reverse proxy requests from `media-analysis.af.automatic.picturelle.com` to `localhost:8050` | P0 |
| FR-02 | Automatic TLS certificate generation via Cloudflare DNS challenge | P0 |
| FR-03 | HTTP to HTTPS redirect | P1 |
| FR-04 | Security headers as per OWASP recommendations | P1 |
| FR-05 | Rate limiting (via Cloudflare edge) | P2 |
| FR-06 | Server info header removal | P2 |

### 3.2 Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-01 | TLS 1.2+ minimum | P0 |
| NFR-02 | Certificate auto-renewal | P0 |
| NFR-03 | Startup time < 30 seconds | P1 |
| NFR-04 | Zero-downtime reload capability | P1 |
| NFR-05 | Configuration as code | P1 |

### 3.3 Security Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| SR-01 | HSTS header with 1-year max-age | P0 |
| SR-02 | X-Content-Type-Options: nosniff | P0 |
| SR-03 | X-Frame-Options: SAMEORIGIN | P1 |
| SR-04 | Content-Security-Policy (restrictive) | P1 |
| SR-05 | No server version disclosure | P1 |
| SR-06 | Cloudflare API token stored securely | P0 |

---

## 4. Implementation Plan

### Phase 1: Directory Structure and Environment Setup

**Objective**: Create project directory structure and prepare environment

**Files Created**:
```
/opt/services/media-analysis/
├── .env                    # Environment variables
├── .gitignore             # Git ignore rules
├── Dockerfile.caddy       # Custom Caddy build
├── Caddyfile             # Main configuration
└── docker-compose.yml     # Docker orchestration
```

**Exact Commands**:
```bash
# 1. Create directory structure
mkdir -p /opt/services/media-analysis/{data,certs,logs}

# 2. Set directory ownership
chown -R 1000:1000 /opt/services/media-analysis

# 3. Create .env file
cat > /opt/services/media-analysis/.env << 'EOF'
# Cloudflare DNS Challenge
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token_here
CLOUDFLARE_ZONE_ID=your_zone_id_here

# Service Configuration
CADDY_ADMIN=false
LOG_LEVEL=info
EOF

# 4. Create .gitignore
cat > /opt/services/media-analysis/.gitignore << 'EOF'
.env
data/
certs/
logs/
.DS_Store
*.log
EOF
```

**Verification Commands**:
```bash
# Verify directory structure
ls -la /opt/services/media-analysis/

# Verify .env template exists
cat /opt/services/media-analysis/.env
```

**Risk Assessment**:
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Directory permissions issue | Low | High | Use 1000:1000 UID for volume mounts |
| Token leak via git | Medium | High | .gitignore must include .env |

---

### Phase 2: Dockerfile for Custom Caddy Build

**Objective**: Build Caddy with Cloudflare DNS provider plugin

**File**: `/opt/services/media-analysis/Dockerfile.caddy`

**Exact Content**:
```dockerfile
# syntax=docker/dockerfile:1.4

# ============================================
# Stage 1: Builder - Compile Caddy with plugins
# ============================================
FROM caddy:2.8-alpine AS builder

# Install xcaddy
RUN apk add --no-cache git && \
    go install github.com/caddyserver/xcaddy/cmd/xcaddy@v0.4.2

# Build Caddy with Cloudflare DNS plugin
WORKDIR /src
RUN xcaddy build v2.8.4 \
    --with github.com/caddy-dns/cloudflare

# ============================================
# Stage 2: Runtime - Production image
# ============================================
FROM caddy:2.8-alpine

# Install common utilities
RUN apk add --no-cache curl jq

# Copy compiled Caddy from builder
COPY --from=builder /go/bin/caddy /usr/bin/caddy

# Copy custom Caddyfile
COPY Caddyfile /etc/caddy/Caddyfile

# Create data directory for certificates
RUN mkdir -p /data/caddy && chown caddy:caddy /data/caddy

# Non-root user
USER caddy

# Expose ports
EXPOSE 80 443

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:2019/metrics || exit 1

# Default command
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
```

**Exact Commands**:
```bash
# 1. Create Dockerfile.caddy
cat > /opt/services/media-analysis/Dockerfile.caddy << 'DOCKERFILE_EOF'
# syntax=docker/dockerfile:1.4

# Stage 1: Builder - Compile Caddy with plugins
FROM caddy:2.8-alpine AS builder

RUN apk add --no-cache git && \
    go install github.com/caddyserver/xcaddy/cmd/xcaddy@v0.4.2

WORKDIR /src
RUN xcaddy build v2.8.4 \
    --with github.com/caddy-dns/cloudflare

# Stage 2: Runtime - Production image
FROM caddy:2.8-alpine

RUN apk add --no-cache curl jq
COPY --from=builder /go/bin/caddy /usr/bin/caddy
COPY Caddyfile /etc/caddy/Caddyfile
RUN mkdir -p /data/caddy && chown caddy:caddy /data/caddy

USER caddy
EXPOSE 80 443

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:2019/metrics || exit 1

CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
DOCKERFILE_EOF

# 2. Build test (optional, verify syntax)
docker build -f /opt/services/media-analysis/Dockerfile.caddy \
    --target builder /opt/services/media-analysis \
    --dry-run
```

**Verification Commands**:
```bash
# Verify Dockerfile syntax
hadolint /opt/services/media-analysis/Dockerfile.caddy

# Verify all required lines exist
grep -c "github.com/caddy-dns/cloudflare" /opt/services/media-analysis/Dockerfile.caddy  # Should return 1
grep -c "FROM caddy:2.8-alpine" /opt/services/media-analysis/Dockerfile.caddy  # Should return 2
```

**Risk Assessment**:
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Plugin build failure | Medium | High | Test build locally before deployment |
| xcaddy version mismatch | Low | Medium | Pin xcaddy version (v0.4.2) |
| Build time increase | Medium | Low | ~3 min build, acceptable for security |

---

### Phase 3: Caddyfile Configuration

**Objective**: Create comprehensive Caddyfile with all requirements

**File**: `/opt/services/media-analysis/Caddyfile`

**Exact Content**:
```caddyfile
# ============================================
# Caddyfile Configuration
# media-analysis.af.automatic.picturelle.com
# Generated: 2026-01-20
# ============================================

{
    # Global options
    admin off
    log {
        level info
        format json
    }
    # Pin to specific Caddyfile format version
    format auto {
        column_threshold 80
    }
}

# HTTP to HTTPS redirect (port 80)
http:// {
    # Redirect all HTTP to HTTPS
    redir https://{host}{uri} permanent
}

# HTTPS site configuration (port 443)
https:// {
    # TLS configuration with Cloudflare DNS
    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
        # Certificate caching directory
        ca https://acme-v02.api.letsencrypt.org/directory
        # Resolver for DNS challenge
        resolver 1.1.1.1:53
    }

    # Domain configuration
    # Change 'media-analysis.af.automatic.picturelle.com' if different
    # If using multiple domains, add them here
    # For now, handle all requests to this domain
    @hostcheck {
        host media-analysis.af.automatic.picturelle.com
    }

    # Apply configuration only to matching host
    handle @hostcheck {
        # ====================================
        # Security Headers Block
        # ====================================
        header {
            # HSTS - Enforce HTTPS for 1 year
            # IncludeSubDomains for all subdomains
            # Preload for browser HSTS preload lists
            Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"

            # Prevent MIME type sniffing attacks
            X-Content-Type-Options "nosniff"

            # Prevent clickjacking via iframes
            # SAMEORIGIN allows same-site framing
            X-Frame-Options "SAMEORIGIN"

            # Control referrer information leakage
            Referrer-Policy "strict-origin-when-cross-origin"

            # Disable browser features not needed by API
            # accelerometer, camera, geolocation, etc.
            Permissions-Policy "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"

            # Content Security Policy
            # Restrictive policy for API-only usage
            # Allow self, inline scripts/styles for API console
            # Allow data: and https: for images
            Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'"

            # Cache control for API responses
            # no-store: Don't cache anywhere
            # no-cache: Must revalidate with server
            # must-revalidate: Once stale, don't serve without validation
            # proxy-revalidate: proxies must revalidate too
            Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate"
            Pragma "no-cache"
            Expires "0"

            # Remove server version disclosure
            -Server
        }

        # ====================================
        # Reverse Proxy Configuration
        # ====================================
        # Proxy to media-analysis-api backend
        reverse_proxy localhost:8050 {
            # Health check
            header_up X-Forwarded-Host {host}
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-Proto {scheme}

            # Connection settings
            transport http {
                # Read timeout for large video uploads
                read_timeout 300s
                # Write timeout for large responses
                write_timeout 300s
                # Buffer sizes
                buffer_size 8192
            }

            # Health check configuration
            health_path /health
            health_interval 30s
            health_timeout 5s
            health_status 200
        }

        # ====================================
        # Optional: Access Log
        # ====================================
        log {
            format json {
                time_format "iso8601"
            }
            output file /var/log/caddy/access.log {
                roll_size 100mb
                roll_keep 5
                roll_keep_gzip 3
            }
        }
    }

    # Fallback: Return 404 for unmatched hosts
    handle {
        respond "Not Found" 404
    }
}

# ============================================
# Metrics Endpoint (optional, for monitoring)
# ============================================
:2019/metrics {
    # Only allow internal network
    @internal {
        remote_ip 192.168.0.0/16 172.16.0.0/12 10.0.0.0/8
    }
    respond @internal "200 OK" 200 {
        mime text/plain
    }
    respond "Forbidden" 403
}
```

**Exact Commands**:
```bash
# 1. Create Caddyfile
cat > /opt/services/media-analysis/Caddyfile << 'CADDYFILE_EOF'
# Caddyfile Configuration
# media-analysis.af.automatic.picturelle.com

{
    admin off
    log {
        level info
        format json
    }
    format auto {
        column_threshold 80
    }
}

http:// {
    redir https://{host}{uri} permanent
}

https:// {
    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
        ca https://acme-v02.api.letsencrypt.org/directory
        resolver 1.1.1.1:53
    }

    @hostcheck {
        host media-analysis.af.automatic.picturelle.com
    }

    handle @hostcheck {
        header {
            Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
            X-Content-Type-Options "nosniff"
            X-Frame-Options "SAMEORIGIN"
            Referrer-Policy "strict-origin-when-cross-origin"
            Permissions-Policy "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
            Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'"
            Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate"
            Pragma "no-cache"
            Expires "0"
            -Server
        }

        reverse_proxy localhost:8050 {
            header_up X-Forwarded-Host {host}
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-Proto {scheme}

            transport http {
                read_timeout 300s
                write_timeout 300s
                buffer_size 8192
            }

            health_path /health
            health_interval 30s
            health_timeout 5s
            health_status 200
        }

        log {
            format json {
                time_format "iso8601"
            }
            output file /var/log/caddy/access.log {
                roll_size 100mb
                roll_keep 5
                roll_keep_gzip 3
            }
        }
    }

    handle {
        respond "Not Found" 404
    }
}

:2019/metrics {
    @internal {
        remote_ip 192.168.0.0/16 172.16.0.0/12 10.0.0.0/8
    }
    respond @internal "200 OK" 200 {
        mime text/plain
    }
    respond "Forbidden" 403
}
CADDYFILE_EOF

# 2. Validate Caddyfile syntax
docker run --rm -v /opt/services/media-analysis/Caddyfile:/Caddyfile:ro \
    caddy:2.8-alpine caddy validate --adapter caddyfile --config /Caddyfile

# 3. Check for required directives
grep -c "dns cloudflare" /opt/services/media-analysis/Caddyfile  # Should be 1
grep -c "Strict-Transport-Security" /opt/services/media-analysis/Caddyfile  # Should be 1
grep -c "reverse_proxy localhost:8050" /opt/services/media-analysis/Caddyfile  # Should be 1
```

**Verification Commands**:
```bash
# 1. Validate Caddyfile syntax
docker run --rm -v /opt/services/media-analysis/Caddyfile:/Caddyfile:ro \
    caddy:2.8-alpine caddy validate --adapter caddyfile --config /Caddyfile
# Expected: Configuration is valid

# 2. Check all required headers present
echo "Checking security headers..."
for header in "Strict-Transport-Security" "X-Content-Type-Options" "X-Frame-Options" "Referrer-Policy" "Permissions-Policy" "Content-Security-Policy" "Cache-Control"; do
    if grep -q "$header" /opt/services/media-analysis/Caddyfile; then
        echo "✓ $header present"
    else
        echo "✗ $header MISSING"
    fi
done

# 3. Check TLS configuration
grep "dns cloudflare" /opt/services/media-analysis/Caddyfile && echo "✓ Cloudflare DNS configured"

# 4. Check reverse proxy target
grep "reverse_proxy localhost:8050" /opt/services/media-analysis/Caddyfile && echo "✓ Backend proxy configured"
```

**Risk Assessment**:
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| CSP too restrictive | Medium | Medium | Test with API; may need to allow external domains |
| Health check path wrong | Low | Medium | Verify /health endpoint exists in API |
| DNS challenge timeout | Low | High | Use 1.1.1.1 resolver; ensure API token has DNS:Edit |
| Log volume exhaustion | Low | Medium | Configure log rotation (already included) |

---

### Phase 4: Docker Compose Configuration

**Objective**: Create Docker Compose file for orchestration

**File**: `/opt/services/media-analysis/docker-compose.yml`

**Exact Content**:
```yaml
version: "3.8"

services:
  # ========================================
  # Caddy Reverse Proxy
  # ========================================
  caddy:
    build:
      context: .
      dockerfile: Dockerfile.caddy
      target: builder
    container_name: media-analysis-caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_logs:/var/log/caddy
    environment:
      - CLOUDFLARE_API_TOKEN=${CLOUDFLARE_API_TOKEN}
    networks:
      - media-analysis-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:2019/metrics"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"

  # ========================================
  # Media Analysis API (existing service)
  # ========================================
  media-analysis-api:
    image: media-analysis-api:latest
    container_name: media-analysis-api
    restart: unless-stopped
    ports:
      - "8050:8050"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - API_KEY=${API_KEY}
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    networks:
      - media-analysis-network
    depends_on:
      - caddy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8050/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  media-analysis-network:
    driver: bridge

volumes:
  caddy_data:
    driver: local
  caddy_logs:
    driver: local
```

**Exact Commands**:
```bash
# 1. Create docker-compose.yml
cat > /opt/services/media-analysis/docker-compose.yml << 'COMPOSE_EOF'
version: "3.8"

services:
  caddy:
    build:
      context: .
      dockerfile: Dockerfile.caddy
      target: builder
    container_name: media-analysis-caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_logs:/var/log/caddy
    environment:
      - CLOUDFLARE_API_TOKEN=${CLOUDFLARE_API_TOKEN}
    networks:
      - media-analysis-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:2019/metrics"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"

  media-analysis-api:
    image: media-analysis-api:latest
    container_name: media-analysis-api
    restart: unless-stopped
    ports:
      - "8050:8050"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - API_KEY=${API_KEY}
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    networks:
      - media-analysis-network
    depends_on:
      - caddy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8050/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  media-analysis-network:
    driver: bridge

volumes:
  caddy_data:
    driver: local
  caddy_logs:
    driver: local
COMPOSE_EOF

# 2. Validate docker-compose syntax
docker-compose -f /opt/services/media-analysis/docker-compose.yml config --quiet

# 3. Verify volume definitions
docker-compose -f /opt/services/media-analysis/docker-compose.yml config --volumes
```

**Verification Commands**:
```bash
# 1. Validate docker-compose syntax
docker-compose -f /opt/services/media-analysis/docker-compose.yml config --quiet
# Expected: No output (success) or displays config

# 2. Check service definitions
docker-compose -f /opt/services/media-analysis/docker-compose.yml config | grep -A2 "services:"
# Expected: Lists caddy and media-analysis-api services

# 3. Check volume mappings
docker-compose -f /opt/services/media-analysis/docker-compose.yml config | grep -A5 "volumes:"
# Expected: caddy_data and caddy_logs defined

# 4. Verify network exists
docker-compose -f /opt/services/media-analysis/docker-compose.yml config | grep "media-analysis-network"
# Expected: Network defined
```

**Risk Assessment**:
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Volume permission issues | Low | Medium | Use named volumes with local driver |
| Circular dependency | Low | High | Caddy doesn't depend on API; API depends on Caddy |
| Port conflict (80/443) | Medium | High | Check for existing services before binding |

---

### Phase 5: Cloudflare Rate Limiting Configuration

**Objective**: Configure rate limiting via Cloudflare edge (not Caddy)

**Cloudflare Dashboard Configuration**:

1. **Navigate to**: Cloudflare Dashboard → Security → WAF → Rate Limiting Rules
2. **Create New Rule**:
   - **Name**: `media-analysis-api-rate-limit`
   - **Path**: `*`
   - **Condition**: `Hostname equals media-analysis.af.automatic.picturelle.com`
   - **Requests per minute**: `100`
   - **Matching traffic from**: `All`
   - **Response type**: `Challenge` (or `Block` for aggressive limiting)
   - **Ban duration**: `60 seconds`

3. **Advanced Configuration** (optional):
   - **By**: `IP` (default)
   - **With response type**: `JS Challenge` for browser clients

**Configuration JSON (Terraform)**:
```hcl
resource "cloudflare_rate_limit" "media_analysis" {
  zone_id        = var.cloudflare_zone_id
  threshold      = 100
  window         = 60  # seconds
  description    = "Rate limit for media-analysis API"
  
  match {
    request {
      methods = ["_ALL_"]
      schemes = ["HTTP", "HTTPS"]
      url     = "media-analysis.af.automatic.picturelle.com/*"
    }
  }
  
  action {
    mode    = "challenge"
    timeout = 60
  }
}
```

**Exact Commands**:
```bash
# 1. Create Terraform configuration for Cloudflare (optional)
cat > /opt/services/media-analysis/cloudflare-rate-limit.tf << 'TF_EOF'
resource "cloudflare_rate_limit" "media_analysis" {
  zone_id     = var.cloudflare_zone_id
  threshold   = 100
  window      = 60
  description = "Rate limit for media-analysis API"

  match {
    request {
      methods = ["_ALL_"]
      schemes = ["HTTP", "HTTPS"]
      url     = "media-analysis.af.automatic.picturelle.com/*"
    }
  }

  action {
    mode    = "challenge"
    timeout = 60
  }
}
TF_EOF

# 2. Verify Cloudflare DNS is configured for domain
dig media-analysis.af.automatic.picturelle.com +short
# Expected: Cloudflare IP addresses

# 3. Check Cloudflare proxy status (should be orange cloud)
nslookup media-analysis.af.automatic.picturelle.com
# Verify A/AAAA records point to Cloudflare
```

**Verification Commands**:
```bash
# 1. Verify domain DNS resolves to Cloudflare
dig media-analysis.af.automatic.picturelle.com +short
# Expected: Cloudflare IPs (e.g., 104.x.x.x, 172.x.x.x)

# 2. Verify proxy status (orange cloud)
curl -sI https://media-analysis.af.automatic.picturelle.com | grep -i "cf-ray"
# Expected: CF-Ray header present (traffic going through Cloudflare)

# 3. Test rate limiting (after deployment)
# Send 101 requests quickly and verify challenge/block
for i in {1..101}; do
    curl -s -o /dev/null -w "%{http_code}\n" https://media-analysis.af.automatic.picturelle.com/health
done | sort | uniq -c
# Expected: 100x 200, 1x Challenge (429/403)
```

**Risk Assessment**:
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Rate limit too aggressive | Low | High | Start with 100 req/min, adjust based on usage |
| False positives | Medium | Medium | Monitor 429 responses after deployment |
| Cloudflare API issues | Low | High | Rate limiting is Cloudflare-managed, resilient |
| Free tier limits | Low | Medium | Only 3 rules free tier - use judiciously |

---

## 5. Deployment Verification Checklist

### 5.1 Pre-Deployment Checks

| Check | Command | Expected Result |
|-------|---------|-----------------|
| DNS configured | `dig domain +short` | Cloudflare IPs |
| Proxy enabled | `curl -sI https://domain | grep cf-ray` | CF-Ray header |
| API token valid | Check Cloudflare API access | DNS:Edit permission |
| Environment configured | `cat .env | grep CLOUDFLARE` | API token present |

### 5.2 Post-Deployment Checks

| Check | Command | Expected Result |
|-------|---------|-----------------|
| Caddy running | `docker ps | grep caddy` | Container running |
| TLS certificate | `curl -sI https://domain | grep -i "strict-transport"` | HSTS header |
| Security headers | `curl -sI https://domain | grep -E "X-Content|X-Frame|Content-Security"` | Headers present |
| Server hidden | `curl -sI https://domain | grep -i server` | No Server header |
| Proxy working | `curl https://domain/health` | API health response |
| Logs accessible | `docker logs media-analysis-caddy 2>&1 | tail -20` | No errors |

### 5.3 Security Verification

```bash
# 1. Complete header audit
curl -sD - https://media-analysis.af.automatic.picturelle.com -o /dev/null | grep -iE "(strict-transport|x-content-type|x-frame|referrer|permissions|content-security|cache-control|pragma|expires|server)"

# 2. Expected headers:
#   Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
#   X-Content-Type-Options: nosniff
#   X-Frame-Options: SAMEORIGIN
#   Referrer-Policy: strict-origin-when-cross-origin
#   Permissions-Policy: accelerometer=(), ... (disabled features)
#   Content-Security-Policy: default-src 'self'; ...
#   Cache-Control: no-store, no-cache, must-revalidate, proxy-revalidate
#   Pragma: no-cache
#   Expires: 0
#   (No Server header)

# 3. Test HTTP redirect
curl -sI http://media-analysis.af.automatic.picturelle.com | grep -i "location"
# Expected: Location: https://media-analysis.af.automatic.picturelle.com/

# 4. Test rate limiting (optional, careful with API)
# Send burst of requests and verify challenge
```

---

## 6. Rollback Instructions

### 6.1 Quick Rollback

```bash
# 1. Stop Caddy container
docker stop media-analysis-caddy && docker rm media-analysis-caddy

# 2. (Optional) Restore previous Caddyfile
git checkout HEAD -- /opt/services/media-analysis/Caddyfile

# 3. (Optional) Redeploy previous version
docker-compose -f /opt/services/media-analysis/docker-compose.yml up -d

# 4. Verify old version running
curl -sI https://media-analysis.af.automatic.picturelle.com | head -1
```

### 6.2 Full Rollback

```bash
# 1. Revert git changes
git checkout HEAD -- .
git clean -fd

# 2. Stop all services
docker-compose -f /opt/services/media-analysis/docker-compose.yml down

# 3. Remove volumes (DESTRUCTIVE - certificates lost)
docker volume rm media-analysis_caddy_data media-analysis_caddy_logs

# 4. Redeploy previous version
docker-compose -f /opt/services/media-analysis/docker-compose.yml up -d

# 5. Verify
curl -sI https://media-analysis.af.automatic.picturelle.com | head -1
```

### 6.3 Emergency Shutdown

```bash
# Immediate shutdown - traffic will return 502
docker stop $(docker ps -q --filter ancestor=media-analysis-caddy)
```

---

## 7. Maintenance

### 7.1 Certificate Renewal

Caddy automatically handles certificate renewal. No manual action required.

**Check certificate status**:
```bash
# View certificate expiration
docker exec media-analysis-caddy cat /data/caddy/acme/acme-v02.api.letsencrypt.org-directory/*/cert.pem | openssl x509 -enddate -noout
```

### 7.2 Caddyfile Reload (Zero Downtime)

```bash
# Reload configuration without restarting
docker exec media-analysis-caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile

# Or via docker-compose
docker-compose -f /opt/services/media-analysis/docker-compose.yml exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### 7.3 Log Rotation

Docker handles container log rotation via `max-size` and `max-file`.

**Manual log rotation**:
```bash
# Rotate Caddy access logs
docker exec media-analysis-caddy sh -c "mv /var/log/caddy/access.log /var/log/caddy/access.log.$(date +%Y%m%d-%H%M%S) && kill -HUP \$(cat /var/run/caddy/caddy.pid)"
```

---

## 8. Dependencies and Requirements

### 8.1 Prerequisites

| Dependency | Version | Required For |
|------------|---------|--------------|
| Docker | 20.10+ | Container runtime |
| Docker Compose | 2.0+ | Orchestration |
| Cloudflare account | Any | DNS + TLS |
| Cloudflare API token | - | DNS challenge |
| Domain registration | - | DNS records |

### 8.2 Cloudflare Setup Required

1. **Create API Token**:
   - Go to: My Profile → API Tokens → Create Custom Token
   - Permissions: `Zone:DNS:Edit`, `Zone:Zone:Read`
   - Zone Resources: Include `automatic.picturelle.com`
   - Save token securely

2. **Create DNS Record**:
   - Type: `A` or `CNAME`
   - Name: `media-analysis`
   - Target: Cloudflare IP or origin server
   - Proxy: **Enabled** (orange cloud)

3. **Configure Rate Limiting** (optional):
   - Security → WAF → Rate Limiting Rules
   - Create rule as specified in Phase 5

---

## 9. Document Metadata

| Attribute | Value |
|-----------|-------|
| **Author** | Claude Sonnet 4.5 |
| **Created** | 2026-01-20 |
| **Version** | 1.0 |
| **Status** | Draft → Ready for Implementation |
| **Related Documents** | media-analysis-ma-27.md (system design) |
| **Estimated Implementation Time** | 45-60 minutes |
| **Estimated Files to Create** | 5 files |

---

## 10. Appendix

### 10.1 File Manifest

| File | Path | Lines (approx) |
|------|------|----------------|
| Caddyfile | `/opt/services/media-analysis/Caddyfile` | 120 |
| Dockerfile.caddy | `/opt/services/media-analysis/Dockerfile.caddy` | 45 |
| docker-compose.yml | `/opt/services/media-analysis/docker-compose.yml` | 65 |
| .env (template) | `/opt/services/media-analysis/.env` | 10 |
| .gitignore | `/opt/services/media-analysis/.gitignore` | 5 |

### 10.2 Security Headers Reference

| Header | OWASP Category | Severity |
|--------|----------------|----------|
| HSTS | Transport Layer Protection | High |
| X-Content-Type-Options | Content Security Policy | Medium |
| X-Frame-Options | Clickjacking Protection | Medium |
| Referrer-Policy | Information Leakage | Low |
| Permissions-Policy | Feature Policy | Low |
| Content-Security-Policy | Cross-Site Scripting | High |

### 10.3 Caddyfile Syntax Reference

```
# Site definition
domain.com {
    # TLS configuration
    tls {
        dns provider api_key
    }
    
    # Security headers
    header {
        Name "value"
        -Name  # Remove header
    }
    
    # Reverse proxy
    reverse_proxy localhost:port {
        header_up Name value
    }
}
```

### 10.4 Troubleshooting Commands

```bash
# Check Caddy logs
docker logs media-analysis-caddy --tail 100 -f

# Validate Caddyfile
docker run --rm -v Caddyfile:/Caddyfile caddy:2.8 caddy validate --config /Caddyfile

# Check certificate status
docker exec media-analysis-caddy caddy list-certificates

# Manual TLS obtain
docker exec media-analysis-caddy caddy validate --config /etc/caddy/Caddyfile

# Test DNS resolution from container
docker exec media-analysis-caddy dig +short media-analysis.af.automatic.picturelle.com
```

---

**END OF DOCUMENT**
