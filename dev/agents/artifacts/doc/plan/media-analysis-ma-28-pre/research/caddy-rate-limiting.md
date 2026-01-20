# Caddy Rate Limiting Configuration

## Approach 1: Caddy 2.7+ Built-in (Recommended)
Caddy 2.7+ includes `limit` in the HTTP server options.

### Configuration
```
media-analysis.af.automatic.picturelle.com {
    reverse_proxy localhost:8050 {
        transport http {
            read_buffer 8192
        }
    }
    
    # Global rate limiting not natively supported in Caddyfile
    # Use nginx-like approach or middleware
}
```

## Approach 2: Using `on-demand-tls` for Connection Limits
```
media-analysis.af.automatic.picturelle.com {
    tls {
        dns cloudflare <API_TOKEN>
    }
    
    # Connection rate limiting via on-demand TLS
    on_demand_tls {
        ask https://internal-api/check-limit
    }
    
    reverse_proxy localhost:8050
}
```

## Approach 3: Custom Middleware (Advanced)
Use Caddy's Go API to implement custom rate limiting, or use a forward proxy like nginx in front.

## Practical Rate Limiting Solution
Since Caddy doesn't have native rate limiting in Caddyfile, consider:

1. **Upstream nginx**: Place nginx with rate limiting before Caddy
2. **Application-level**: Implement in the media-analysis-api itself
3. **Cloudflare**: Use Cloudflare's built-in rate limiting (Rules section)

### Cloudflare Rate Limiting (Recommended for This Setup)
- Free tier: 3 rules
- Rules: Configure in Cloudflare dashboard
- Action: Challenge, JS Challenge, or Block

## Recommendation
Use Cloudflare Rate Limiting for simplicity:
- No additional infrastructure complexity
- Configurable via Cloudflare dashboard
- Works at edge before traffic reaches server
