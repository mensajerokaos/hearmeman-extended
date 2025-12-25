---
author: oz
model: claude-opus-4-5
date: 2025-12-24 12:30
task: Research cheapest Docker image hosting for RunPod custom templates
---

# Docker Image Hosting Options for RunPod Templates

Research on the cheapest/free ways to host Docker images for RunPod custom templates, with focus on large AI model images (20GB+).

## Quick Comparison Table

| Registry | Free Storage | Free Pulls | Image Size Limit | Privacy | Setup Complexity | Best For |
|----------|-------------|------------|------------------|---------|-----------------|----------|
| **Docker Hub** | Unlimited public | 100/6hr (anon), 200/6hr (free acct) | No hard limit | Public free, Private limited | Very Easy | Small public images |
| **GHCR** | Unlimited public, 1GB private | Unlimited public | No hard limit | Public free | Easy | GitHub-integrated projects |
| **Google Artifact Registry** | 0.5GB | Free to GCP services | No hard limit | Private | Medium | GCP users |
| **Amazon ECR Public** | 50GB/month | 500GB/mo (anon), 5TB/mo (AWS acct) | No hard limit | Public | Medium | AWS ecosystem |
| **Self-Hosted (VPS)** | Disk-limited | Unlimited | Disk-limited | Private | Hard | Large images, full control |
| **Google Drive** | 15GB free | N/A | N/A | N/A | N/A | **Not viable** |

---

## 1. Docker Hub

### Pricing (2025)

- **Docker Personal (Free)**:
  - Unlimited public repositories
  - 1 private repository
  - 100 pulls/6 hours (unauthenticated)
  - 200 pulls/6 hours (authenticated)
  - Storage charges: **Delayed indefinitely** (no storage fees currently)
  - Pull consumption charges: **Cancelled entirely**

- **Docker Pro ($9/month)**: Unlimited pulls, 5 private repos
- **Docker Team ($15/user/month)**: Unlimited everything

### Pros
- Simplest setup (default Docker registry)
- No storage fees (for now)
- RunPod can pull without configuration
- Images cached on RunPod nodes if popular

### Cons
- Rate limits can hit during cold starts
- Images unused for 6 months may be deleted (free tier)
- Private repos limited on free tier

### RunPod Compatibility
- **Perfect**: RunPod pulls directly from Docker Hub by default
- Example: `username/my-image:latest`

### Sources
- [Docker Hub Usage and Limits](https://docs.docker.com/docker-hub/usage/)
- [Docker November 2024 Plans Update](https://www.docker.com/blog/november-2024-updated-plans-announcement/)
- [Docker Hub Pull Limits](https://docs.docker.com/docker-hub/usage/pulls/)

---

## 2. GitHub Container Registry (ghcr.io)

### Pricing (2025)

- **Public Packages**: **FREE** (storage and bandwidth)
- **Private Packages**:
  - 1GB free storage
  - 1GB free data transfer/month
  - $0.25/GB storage beyond free tier
  - $0.50/GB data transfer beyond free tier

### Pros
- Unlimited public image storage
- No pull rate limits (unlike Docker Hub)
- Integrates with GitHub Actions CI/CD
- Anonymous access for public images
- Container storage is **currently free** (GitHub may change with 1 month notice)

### Cons
- Private images get expensive at scale
- Less familiar than Docker Hub
- Requires GitHub account

### RunPod Compatibility
- **Works well**: Use full image path
- Example: `ghcr.io/username/my-image:latest`
- Public images: No authentication needed
- Private images: RunPod supports registry credentials

### Sources
- [GitHub Packages Billing](https://docs.github.com/en/billing/concepts/product-billing/github-packages)
- [GHCR Traffic Management](https://blog.cloud-eng.nl/2023/01/23/ghcr-acr-traffic/)
- [GitHub Container Registry Pricing Guide](https://expertbeacon.com/github-container-registry-pricing-the-complete-guide-for-2024/)

---

## 3. Google Artifact Registry

### Pricing (2025)

- **Free Tier**:
  - 0.5GB storage (across all projects on billing account)
  - Data transfer IN: Free
  - Transfer to GCP services: Free
  - $300 new customer credits

- **Paid**:
  - $0.10/GB/month storage
  - Egress to internet: Standard GCP network pricing (~$0.12/GB)

### Pros
- Integrates with GCP services
- Regional repositories reduce transfer costs
- Vulnerability scanning available

### Cons
- Only 0.5GB free (too small for AI images)
- Egress fees to non-GCP (RunPod = external)
- Requires GCP account setup

### RunPod Compatibility
- **Works but costly**: RunPod is external, so egress fees apply
- Need to configure authentication for private repos
- Example: `us-docker.pkg.dev/project-id/repo/image:tag`

### Sources
- [Artifact Registry Pricing](https://cloud.google.com/artifact-registry/pricing)
- [GCP Artifact Registry Docs](https://docs.cloud.google.com/artifact-registry/docs)

---

## 4. Amazon ECR

### Pricing (2025)

- **ECR Public (Free)**:
  - 50GB/month storage
  - 500GB/month data transfer (anonymous)
  - 5TB/month data transfer (with AWS account)

- **ECR Private**:
  - 500MB free for 12 months (new AWS customers)
  - $0.10/GB/month storage after

### Pros
- 50GB free public storage is generous
- Good for large AI images
- 500GB+ free egress monthly

### Cons
- Private repos require AWS Free Tier (12 months)
- AWS account setup required
- Less familiar CLI than Docker Hub

### RunPod Compatibility
- **Works well for public**: `public.ecr.aws/registry-alias/image:tag`
- Private: Requires ECR authentication setup

### Sources
- [Amazon ECR Pricing](https://aws.amazon.com/ecr/pricing/)
- [ECR Pricing Guide](https://handbook.vantage.sh/aws/services/ecr-pricing/)

---

## 5. Self-Hosted Docker Registry (VPS)

### Your VPS: devmaster (46.62.238.134)

Using your existing VPS as a Docker registry server.

### Setup

```bash
# On VPS (devmaster)
docker run -d \
  -p 5000:5000 \
  --restart=always \
  --name registry \
  -v /opt/registry:/var/lib/registry \
  registry:2
```

### With HTTPS (required for production)

```bash
# Using nginx as reverse proxy with SSL
# 1. Point domain to VPS (e.g., registry.yourdomain.com)
# 2. Get SSL cert (Let's Encrypt)
# 3. Configure nginx proxy to port 5000
```

### Storage Costs
- Limited only by VPS disk space
- Your VPS disk: Check available space
- Additional storage: ~$5-10/month per 100GB (varies by provider)

### Pros
- **Unlimited pulls** (no rate limits)
- **Full control** over storage and access
- **Private by default**
- No per-GB storage fees (beyond VPS cost)
- Closest to EU-based RunPod datacenters (EU-NL-1, EU-SE-1)

### Cons
- Setup complexity (SSL, nginx, maintenance)
- Bandwidth limited by VPS plan
- Single point of failure (no CDN)
- Must manage security/updates

### RunPod Compatibility
- **Works**: Use full URL with port
- Example: `registry.yourdomain.com:5000/my-image:latest`
- Or with nginx proxy: `registry.yourdomain.com/my-image:latest`

### Large Image Optimization

For 22GB+ images, configure nginx properly:

```nginx
client_max_body_size 0;  # Disable size limit
proxy_read_timeout 900;
proxy_connect_timeout 900;
proxy_send_timeout 900;
```

### Sources
- [Self-Host Container Registry Guide](https://www.freecodecamp.org/news/how-to-self-host-a-container-registry/)
- [Docker's Own Registry Guide](https://www.docker.com/blog/how-to-use-your-own-registry-2/)
- [Self-Hosted Registry with HTTPS](https://windix.medium.com/self-hosted-docker-registry-and-web-ui-f121d81f6ec8)

---

## 6. Google Drive - NOT VIABLE

### Why It Doesn't Work

Google Drive cannot serve as a Docker registry because:

1. **Not an OCI-compliant registry**: Docker requires registries to implement the OCI Distribution Specification
2. **No blob/manifest API**: Docker needs specific API endpoints for layers and manifests
3. **No authentication flow**: Docker uses token-based auth, not OAuth2 like Drive

### Alternatives Considered

- **rclone mount**: Could mount Drive as volume, but can't serve as registry
- **OCI artifacts on Drive**: Not supported; OCI requires proper registry implementation

### Sources
- [OCI Registry Specification](https://github.com/opencontainers/image-spec/blob/main/image-layout.md)
- [rclone Docker Volume Discussion](https://forum.rclone.org/t/how-to-use-google-drive-as-docker-volume/27026)

---

## How RunPod Pulls Custom Docker Images

### Pull Behavior

1. **Pod Creation**: RunPod pulls the specified container image to the host node
2. **Caching**:
   - **Secure Cloud**: Images are cached on nodes; subsequent startups on same node are faster
   - **Community Cloud**: Image downloaded each time (no caching guarantee)
3. **Serverless**: Worker images are pre-cached on worker nodes

### Optimization Tips

1. **Use popular base images**: CUDA/PyTorch images are often pre-cached
2. **Multi-stage builds**: Reduce final image size
3. **Layer ordering**: Put rarely-changing layers first (better cache hits)
4. **Network volumes**: Download models at runtime instead of baking in

### Architecture Requirement

RunPod only supports **linux/amd64**:
```bash
docker build --platform linux/amd64 -t myimage .
```

### Sources
- [RunPod Templates Overview](https://docs.runpod.io/pods/templates/overview)
- [RunPod Docker Setup Guide](https://www.runpod.io/articles/guides/docker-setup-pytorch-cuda-12-8-python-3-11)
- [RunPod Image Caching Discussion](https://www.answeroverflow.com/m/1213081606819024917)

---

## Best Practices for Large Images (20-50GB)

### 1. Don't Bake Models In

Instead of embedding 20GB+ models in the image:

```dockerfile
# BAD: 22GB image
COPY ./models /app/models

# GOOD: Small image, download at runtime
RUN mkdir /app/models
# Download models on first run to network volume
```

### 2. Use Network Volumes

RunPod network volumes persist models between pod restarts:
- Store models on `/workspace` (network volume mount)
- First pod run: Download models
- Subsequent runs: Models already present

### 3. Multi-Stage Builds

```dockerfile
# Build stage
FROM nvidia/cuda:12.1-devel-ubuntu22.04 AS builder
RUN apt-get update && apt-get install -y build-essential
# Compile stuff here

# Runtime stage (smaller)
FROM nvidia/cuda:12.1-runtime-ubuntu22.04
COPY --from=builder /app/compiled /app/compiled
# Runtime-only dependencies
```

### 4. Layer Optimization

```dockerfile
# Combine RUN commands
RUN apt-get update && \
    apt-get install -y --no-install-recommends pkg1 pkg2 && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt
```

### 5. Consider ONNX Quantization

For inference-only models:
- int8 quantization can 4x reduce model size
- Docker image reduced up to 10x
- Slight accuracy tradeoff

### Sources
- [Handling Large Model Files in Docker](https://medium.com/@leosiraj96/handling-large-model-files-in-dockerized-llm-applications-43fd821cd00e)
- [Reducing Docker Image Size for LLMs](https://towardsdatascience.com/reducing-the-size-of-docker-images-serving-llm-models-b70ee66e5a76/)
- [Docker Best Practices](https://docs.docker.com/build/building/best-practices/)

---

## Recommendations

### For Small Images (<5GB)

**Winner: GitHub Container Registry (ghcr.io)**

- Free unlimited storage for public images
- No rate limits
- Easy CI/CD with GitHub Actions
- No authentication needed for pulls

```bash
# Push to GHCR
docker tag myimage ghcr.io/username/myimage:latest
docker push ghcr.io/username/myimage:latest

# Use in RunPod template
Container Image: ghcr.io/username/myimage:latest
```

### For Large Images with Models (20-50GB)

**Winner: Hybrid Approach**

1. **Small base image** on GHCR or Docker Hub (~5GB)
2. **Models downloaded at runtime** to RunPod Network Volume

This approach:
- Faster cold starts (smaller image pull)
- Models persist on network volume
- Easy model updates without rebuilding image

If you MUST bake models in:

**Amazon ECR Public** - 50GB free storage, 500GB+ free egress

```bash
# Push to ECR Public
aws ecr-public get-login-password | docker login --username AWS --password-stdin public.ecr.aws
docker tag myimage:latest public.ecr.aws/x1y2z3/myimage:latest
docker push public.ecr.aws/x1y2z3/myimage:latest
```

### For Self-Hosted Option (Your VPS)

**Best for**: Development, testing, private images, full control

**Setup on devmaster (46.62.238.134)**:

```bash
# 1. Create registry directory
ssh vps "mkdir -p /opt/docker-registry"

# 2. Create docker-compose.yml
ssh vps "cat > /opt/docker-registry/docker-compose.yml << 'EOF'
version: '3'
services:
  registry:
    image: registry:2
    restart: always
    ports:
      - '5000:5000'
    volumes:
      - ./data:/var/lib/registry
    environment:
      REGISTRY_HTTP_HEADERS_Access-Control-Allow-Origin: '["*"]'
EOF"

# 3. Start registry
ssh vps "cd /opt/docker-registry && docker compose up -d"

# 4. Add nginx config for HTTPS (requires domain + SSL)
```

**Without HTTPS** (testing only):

Add to Docker daemon.json on your local machine:
```json
{
  "insecure-registries": ["46.62.238.134:5000"]
}
```

**Cost**: $0 additional (uses existing VPS)
**Capacity**: Limited by VPS disk space
**Speed**: Good to EU RunPod datacenters (EU-NL-1, EU-SE-1)

---

## RunPod Datacenter Locations

For optimal pull speed, choose registry location near your RunPod datacenter:

| RunPod Region | Location | Best Registry Choice |
|---------------|----------|---------------------|
| EU-NL-1 | Netherlands | Self-hosted (devmaster), GHCR |
| EU-SE-1 | Sweden | Self-hosted (devmaster), GHCR |
| EU-RO-1 | Romania | Self-hosted, GHCR |
| US-* | United States | Docker Hub, GHCR, ECR |

Your VPS (devmaster) is likely in Europe, making it ideal for EU RunPod datacenters.

---

## Summary Decision Matrix

| Scenario | Recommendation | Cost |
|----------|---------------|------|
| Public image, <5GB | GHCR | Free |
| Public image, 5-50GB | ECR Public | Free (50GB limit) |
| Private image, <1GB | GHCR | Free |
| Private image, 1-10GB | Self-hosted VPS | Free (existing VPS) |
| Large AI image, models baked in | ECR Public + optimize layers | Free |
| Large AI image, best practice | Small image + Network Volume | Free |
| Full control, no limits | Self-hosted registry | VPS cost only |

---

## Final Recommendation for Your Use Case

**For VibeVoice (22GB image with AI models)**:

1. **Best approach**:
   - Create small base image (~5GB) with code/dependencies on GHCR
   - Download VibeVoice models to network volume on first run
   - Models persist across pod restarts

2. **If models must be in image**:
   - Use Amazon ECR Public (50GB free)
   - Or self-hosted on devmaster for full control

3. **Quick win**:
   - Push current image to GHCR (free, unlimited public storage)
   - No rate limits means reliable pod starts
