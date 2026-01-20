# Caddy Cloudflare DNS Provider Research

## Cloudflare DNS Provider for Caddy

### Required Module
- **Module**: `github.com/caddy-dns/cloudflare`
- **Installation**: Build Caddy with the module or use official image with module included

### Dockerfile-based Build Approach
```dockerfile
FROM caddy:builder AS builder
RUN xcaddy build --with github.com/caddy-dns/cloudflare

FROM caddy:2.8
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
```

### Alternative: Caddy with CloudFlare Module Pre-built
The official Caddy Docker image may not include cloudflare module by default. Custom build required.

## TLS Configuration with Cloudflare DNS

### Automatic TLS (Cloudflare DNS Challenge)
```
media-analysis.af.automatic.picturelle.com {
    tls {
        dns cloudflare <API_TOKEN>
    }
    reverse_proxy localhost:8050
}
```

### Required Environment Variables
- `CLOUDFLARE_API_TOKEN`: DNS API token with Edit zone permissions
- `CLOUDFLARE_ZONE_API_TOKEN`: Alternative using Zone API key

### API Token Permissions Required
- Zone: DNS:Edit
- Account: Cloudflare Workers:Edit (if using Workers)

## Sources
- https://github.com/caddy-dns/cloudflare
- https://caddyserver.com/docs/caddyfile/directives/tls
