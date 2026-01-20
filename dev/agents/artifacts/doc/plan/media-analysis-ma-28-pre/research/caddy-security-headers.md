# Caddy Security Headers Configuration

## Required Security Headers

### 1. Strict-Transport-Security (HSTS)
```
header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
```

### 2. X-Content-Type-Options
```
header X-Content-Type-Options "nosniff"
```

### 3. X-Frame-Options
```
header X-Frame-Options "SAMEORIGIN"
```

### 4. X-XSS-Protection (Legacy, Optional)
```
header X-XSS-Protection "1; mode=block"
```

### 5. Referrer-Policy
```
header Referrer-Policy "strict-origin-when-cross-origin"
```

### 6. Permissions-Policy
```
header Permissions-Policy "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
```

### 7. Content-Security-Policy
```
header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https://api.cloudflare.com;"
```

### 8. Cache-Control (For API)
```
header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate"
header Pragma "no-cache"
header Expires "0"
```

## Complete Security Headers Block

```
media-analysis.af.automatic.picturelle.com {
    header {
        # HSTS - Enable for production
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        
        # Prevent MIME type sniffing
        X-Content-Type-Options "nosniff"
        
        # Prevent clickjacking
        X-Frame-Options "SAMEORIGIN"
        
        # Referrer policy
        Referrer-Policy "strict-origin-when-cross-origin"
        
        # Permissions policy (disable unused features)
        Permissions-Policy "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
        
        # Content Security Policy
        # Adjust based on actual API requirements
        Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'"
        
        # Cache control for API responses
        Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate"
        Pragma "no-cache"
        Expires "0"
        
        # Remove server version header
        -Server
    }
    
    reverse_proxy localhost:8050
}
```

## Header Testing Commands

```bash
# Check headers with curl
curl -I https://media-analysis.af.automatic.picturelle.com

# Detailed header analysis
curl -sD - https://media-analysis.af.automatic.picturelle.com -o /dev/null

# Security header scanning
curl -s https://securityheaders.com/?q=https://media-analysis.af.automatic.picturelle.com
```
