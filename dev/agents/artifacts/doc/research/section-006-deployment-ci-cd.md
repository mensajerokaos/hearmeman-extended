---
task: Section 006 - Deployment, CI/CD
agent: hc (headless claude)
model: claude-sonnet-4-5-20250929
timestamp: 2026-01-17T18:00:00Z
status: completed
---

# Deployment, CI/CD Documentation

## 1. GitHub Actions Workflow

### Complete Workflow Configuration

**File**: `.github/workflows/docker-build.yml`

The workflow automates Docker image building and publishing to GitHub Container Registry (GHCR) on every push to main/master branches when changes are made to the `docker/` directory.

#### Workflow Triggers

```yaml
on:
  push:
    branches: [main, master]
    paths:
      - 'docker/**'
  workflow_dispatch:
    inputs:
      bake_wan_720p:
        description: 'Bake WAN 2.1 720p models (~25GB)'
        required: false
        type: boolean
        default: false
      bake_wan_480p:
        description: 'Bake WAN 2.1 480p models (~12GB)'
        required: false
        type: boolean
        default: false
      bake_illustrious:
        description: 'Bake Illustrious XL models (~7GB)'
        required: false
        type: boolean
        default: false
      image_tag:
        description: 'Custom image tag (default: latest)'
        required: false
        type: string
        default: 'latest'
```

#### Complete Step-by-Step Breakdown

| Step | Action | Purpose |
|------|--------|---------|
| 1 | Free Disk Space | Remove ~20GB of unused packages to ensure Docker build succeeds |
| 2 | Checkout Repository | Clone source code for build context |
| 3 | Setup Docker Buildx | Enable advanced build features and multi-platform builds |
| 4 | Login to GHCR | Authenticate using GITHUB_TOKEN for image push |
| 5 | Determine Image Tag | Logic to select tag based on inputs |
| 6 | Extract Metadata | Generate OCI labels and tags for image |
| 7 | Build and Push | Execute Docker build with cache and push to GHCR |

#### Step 1: Disk Space Optimization

```bash
sudo rm -rf /usr/share/dotnet
sudo rm -rf /opt/ghc
sudo rm -rf /usr/local/share/boost
sudo rm -rf "$AGENT_TOOLSDIRECTORY"
sudo rm -rf /usr/local/lib/android
sudo rm -rf /usr/share/swift
docker system prune -af --volumes || true
df -h
```

**Rationale**: GitHub Actions runners have limited disk space (~14GB free after base system). Docker images are ~11GB before models. Must clean to avoid build failures.

#### Step 2: Checkout

```yaml
- name: Checkout repository
  uses: actions/checkout@v4
```

#### Step 3: Docker Buildx Setup

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
```

Enables:
- BuildKit for faster builds
- Layer caching via GitHub Actions cache
- Multi-architecture support (amd64)

#### Step 4: GHCR Authentication

```yaml
- name: Log in to Container Registry
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

Uses GitHub's automatic token for authentication. Requires `packages: write` permission.

#### Step 5: Image Tag Logic

```bash
if [ "${{ inputs.image_tag }}" != "" ] && [ "${{ inputs.image_tag }}" != "latest" ]; then
  echo "tag=${{ inputs.image_tag }}" >> $GITHUB_OUTPUT
elif [ "${{ inputs.bake_wan_720p }}" = "true" ]; then
  echo "tag=wan720p" >> $GITHUB_OUTPUT
elif [ "${{ inputs.bake_wan_480p }}" = "true" ]; then
  echo "tag=wan480p" >> $GITHUB_OUTPUT
elif [ "${{ inputs.bake_illustrious }}" = "true" ]; then
  echo "tag=illustrious" >> $GITHUB_OUTPUT
else
  echo "tag=latest" >> $GITHUB_OUTPUT
fi
```

**Tag Selection Matrix**:

| Input | Resulting Tag | Use Case |
|-------|---------------|----------|
| No inputs | `latest` | Standard builds |
| `bake_wan_720p: true` | `wan720p` | Pre-baked WAN 2.1 720p models |
| `bake_wan_480p: true` | `wan480p` | Pre-baked WAN 2.1 480p models |
| `bake_illustrious: true` | `illustrious` | Pre-baked Illustrious model |
| `image_tag: custom` | `custom` | Manual tagging |

#### Step 6: OCI Metadata

```yaml
- name: Extract metadata
  id: meta
  uses: docker/metadata-action@v5
  with:
    images: ghcr.io/${{ github.repository_owner }}/hearmeman-extended
    tags: |
      type=raw,value=${{ steps.tag.outputs.tag }}
      type=sha,prefix=
```

Generates full image reference: `ghcr.io/oz/hearmeman-extended:latest` or `ghcr.io/oz/hearmeman-extended:sha-abc123`

#### Step 7: Build with Cache

```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: ./docker
    push: true
    tags: ${{ steps.meta.outputs.tags }}
    labels: ${{ steps.meta.outputs.labels }}
    platforms: linux/amd64
    cache-from: type=gha
    cache-to: type=gha,mode=max
    build-args: |
      BAKE_WAN_720P=${{ inputs.bake_wan_720p || 'false' }}
      BAKE_WAN_480P=${{ inputs.bake_wan_480p || 'false' }}
      BAKE_ILLUSTRIOUS=${{ inputs.bake_illustrious || 'false' }}
```

**Cache Strategy**:
- `cache-from: type=gha` - Restore layers from previous builds
- `cache-to: type=gha,mode=max` - Export all layers for max cache hit
- Build arguments passed for conditional model baking

---

## 2. RunPod Pod Creation Commands

### Standard Deployment Command

```bash
~/.local/bin/runpodctl create pod \
  --name "hearmeman-$(date +%H%M)" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA GeForce RTX 4090" \
  --gpuCount 1 \
  --containerDiskSize 20 \
  --volumeSize 15 \
  --secureCloud \
  --ports "8188/http" \
  --ports "19123/http" \
  --env "ENABLE_VIBEVOICE=true" \
  --env "WAN_720P=true" \
  --env "ENABLE_R2_SYNC=true" \
  --env "R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com" \
  --env "R2_BUCKET=runpod" \
  --env "R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}" \
  --env "R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}"
```

### Full Configuration Command (All Models)

```bash
~/.local/bin/runpodctl create pod \
  --name "hearmeman-full-$(date +%H%M)" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA GeForce RTX 4090" \
  --gpuCount 1 \
  --containerDiskSize 20 \
  --volumeSize 100 \
  --secureCloud \
  --ports "8188/http" \
  --ports "8888/http" \
  --ports "22/tcp" \
  --env "ENABLE_VIBEVOICE=true" \
  --env "ENABLE_CONTROLNET=true" \
  --env "WAN_720P=true" \
  --env "ENABLE_WAN22_DISTILL=true" \
  --env "ENABLE_I2V=true" \
  --env "ENABLE_ILLUSTRIOUS=true" \
  --env "ENABLE_ZIMAGE=false" \
  --env "ENABLE_R2_SYNC=true" \
  --env "R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com" \
  --env "R2_BUCKET=runpod" \
  --env "GPU_TIER=consumer" \
  --env "GPU_MEMORY_MODE=auto" \
  --env "CIVITAI_API_KEY={{RUNPOD_SECRET_civitai_key}}" \
  --env "R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}" \
  --env "R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}"
```

### Minimal Command (Basic Usage)

```bash
~/.local/bin/runpodctl create pod \
  --name "hearmeman-minimal" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA GeForce RTX 4090" \
  --gpuCount 1 \
  --containerDiskSize 20 \
  --volumeSize 15 \
  --ports "8188/http" \
  --env "ENABLE_VIBEVOICE=true" \
  --env "WAN_720P=true"
```

### WAN 2.2 TurboDiffusion Command

```bash
~/.local/bin/runpodctl create pod \
  --name "hearmeman-turbodiffusion-$(date +%H%M)" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA RTX A6000" \
  --gpuCount 1 \
  --containerDiskSize 20 \
  --volumeSize 50 \
  --secureCloud \
  --ports "8188/http" \
  --env "WAN_720P=true" \
  --env "ENABLE_WAN22_DISTILL=true" \
  --env "ENABLE_I2V=true" \
  --env "ENABLE_R2_SYNC=true" \
  --env "R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com" \
  --env "R2_BUCKET=runpod" \
  --env "GPU_TIER=prosumer" \
  --env "GPU_MEMORY_MODE=model_cpu_offload" \
  --env "R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}" \
  --env "R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}"
```

### GPU-Specific Commands

#### RTX 4090 (24GB Consumer)

```bash
~/.local/bin/runpodctl create pod \
  --name "hearmeman-rtx4090" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA GeForce RTX 4090" \
  --gpuCount 1 \
  --containerDiskSize 20 \
  --volumeSize 50 \
  --ports "8188/http" \
  --env "ENABLE_VIBEVOICE=true" \
  --env "WAN_720P=true" \
  --env "GPU_TIER=consumer" \
  --env "GPU_MEMORY_MODE=auto"
```

#### RTX A6000 (48GB Prosumer)

```bash
~/.local/bin/runpodctl create pod \
  --name "hearmeman-a6000" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA RTX A6000" \
  --gpuCount 1 \
  --containerDiskSize 20 \
  --volumeSize 100 \
  --secureCloud \
  --ports "8188/http" \
  --env "ENABLE_VIBEVOICE=true" \
  --env "WAN_720P=true" \
  --env "ENABLE_WAN22_DISTILL=true" \
  --env "ENABLE_I2V=true" \
  --env "GPU_TIER=prosumer" \
  --env "GPU_MEMORY_MODE=auto"
```

#### A100 80GB (Datacenter)

```bash
~/.local/bin/runpodctl create pod \
  --name "hearmeman-a100" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA A100 80GB" \
  --gpuCount 1 \
  --containerDiskSize 20 \
  --volumeSize 150 \
  --secureCloud \
  --ports "8188/http" \
  --env "ENABLE_VIBEVOICE=true" \
  --env "WAN_720P=true" \
  --env "ENABLE_WAN22_DISTILL=true" \
  --env "ENABLE_I2V=true" \
  --env "ENABLE_FLASHPORTRAIT=true" \
  --env "ENABLE_STORYMEM=true" \
  --env "ENABLE_INFCAM=true" \
  --env "GPU_TIER=datacenter" \
  --env "GPU_MEMORY_MODE=full"
```

---

## 3. Secret Management

### RunPod Secrets Configuration

**IMPORTANT**: Never expose credentials in plain text. Use [RunPod Secrets](https://docs.runpod.io/pods/templates/secrets) for secure credential storage.

#### Creating Secrets in RunPod Console

1. Go to **Settings > Secrets**
2. Create the following secrets:

| Secret Name | Value | Purpose |
|-------------|-------|---------|
| `r2_access_key` | R2 Access Key ID | R2 bucket authentication |
| `r2_secret_key` | R2 Secret Access Key | R2 bucket authentication |
| `civitai_key` | CivitAI API Token | Rate-limited model downloads |

#### Referencing Secrets in Pod Template

Use `{{RUNPOD_SECRET_<name>}}` syntax in environment variables:

```bash
--env "R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}"
--env "R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}"
--env "CIVITAI_API_KEY={{RUNPOD_SECRET_civitai_key}}"
```

**Security Notes**:
- Secrets are injected at container runtime
- Not visible in pod logs
- Encrypted at rest
- Not exposed in template export

### Alternative: Environment Variable File

For local Docker testing, create `.env` file:

```bash
# .env (add to .gitignore!)
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com
R2_BUCKET=runpod
CIVITAI_API_KEY=your_civitai_key
```

```bash
# Load env file
export $(cat .env | xargs)
docker compose up -d
```

### CI/CD Secret Configuration

For GitHub Actions, configure in repository settings:

| Secret | Purpose |
|--------|---------|
| `GITHUB_TOKEN` | Auto-provided for GHCR pushes |

---

## 4. Container Startup on RunPod

### Startup Sequence

```
+------------------+
| 1. Image Pull    | ghcr.io image pulled (~11GB)
+------------------+
         |
         v
+------------------+
| 2. GPU Detection | nvidia-smi queries VRAM
+------------------+
         |
         v
+------------------+
| 3. Storage Mode  | Detects ephemeral vs persistent
+------------------+
         |
         v
+------------------+
| 4. SSH Config    | If PUBLIC_KEY set, enables SSH
+------------------+
         |
         v
+------------------+
| 5. JupyterLab    | If JUPYTER_PASSWORD set, starts
+------------------+
         |
         v
+------------------+
| 6. Model Download| Calls download_models.sh
+------------------+
         |
         v
+------------------+
| 7. R2 Sync       | Starts r2_sync.sh daemon
+------------------+
         |
         v
+------------------+
| 8. ComfyUI       | Starts on port 8188
+------------------+
```

### Startup Script: `start.sh`

**File**: `docker/start.sh`

#### Storage Mode Detection

```bash
detect_storage_mode() {
    if [ "$STORAGE_MODE" = "ephemeral" ]; then
        echo "ephemeral"
    elif [ "$STORAGE_MODE" = "persistent" ]; then
        echo "persistent"
    elif [ "$STORAGE_MODE" = "auto" ] || [ -z "$STORAGE_MODE" ]; then
        if [ -d "/workspace" ] && mountpoint -q "/workspace" 2>/dev/null; then
            echo "persistent"
        else
            echo "ephemeral"
        fi
    else
        echo "ephemeral"
    fi
}
```

**Behavior**:
- **Ephemeral**: Models downloaded on every start (slow startup)
- **Persistent**: Models cached on volume (fast startup)
- **Auto**: Detects if `/workspace` is a mount point

#### GPU VRAM Detection

```bash
detect_gpu_config() {
    GPU_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -n 1)

    if [ -z "$GPU_VRAM" ]; then
        echo "  [Warning] Could not detect GPU VRAM, using defaults"
        GPU_VRAM=0
    fi

    # Auto-detect GPU tier
    if [ -z "$GPU_TIER" ] || [ "$GPU_TIER" = "auto" ]; then
        if (( GPU_VRAM >= 48000 )); then
            export GPU_TIER="datacenter"     # A100/H100
        elif (( GPU_VRAM >= 20000 )); then
            export GPU_TIER="prosumer"       # RTX A6000
        else
            export GPU_TIER="consumer"       # RTX 4090
        fi
    fi

    # Auto-detect memory mode
    if [ "$GPU_MEMORY_MODE" = "auto" ]; then
        if (( GPU_VRAM >= 48000 )); then
            export GPU_MEMORY_MODE="full"
        elif (( GPU_VRAM >= 24000 )); then
            export GPU_MEMORY_MODE="model_cpu_offload"
        else
            export GPU_MEMORY_MODE="sequential_cpu_offload"
        fi
    fi

    # Auto-detect ComfyUI args
    if [ -z "$COMFYUI_ARGS" ]; then
        if (( GPU_VRAM < 8000 )); then
            export COMFYUI_ARGS="--lowvram --cpu-vae --force-fp16"
        elif (( GPU_VRAM < 12000 )); then
            export COMFYUI_ARGS="--lowvram --force-fp16"
        elif (( GPU_VRAM < 16000 )); then
            export COMFYUI_ARGS="--medvram --cpu-text-encoder --force-fp16"
        elif (( GPU_VRAM < 24000 )); then
            export COMFYUI_ARGS="--normalvram --force-fp16"
        else
            export COMFYUI_ARGS=""
        fi
    fi
}
```

**VRAM Thresholds**:

| VRAM | GPU Tier | Memory Mode | ComfyUI Args |
|------|----------|-------------|--------------|
| < 8GB | consumer | sequential_cpu_offload | --lowvram --cpu-vae --force-fp16 |
| 8-12GB | consumer | sequential_cpu_offload | --lowvram --force-fp16 |
| 12-16GB | consumer | sequential_cpu_offload | --medvram --cpu-text-encoder --force-fp16 |
| 16-24GB | consumer | model_cpu_offload | --normalvram --force-fp16 |
| 24-48GB | prosumer | model_cpu_offload | (default args) |
| 48GB+ | datacenter | full | (empty - native BF16) |

#### SSH Setup

```bash
if [[ -n "$PUBLIC_KEY" ]]; then
    echo "[SSH] Configuring SSH access..."
    mkdir -p ~/.ssh && chmod 700 ~/.ssh
    echo "$PUBLIC_KEY" >> ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    service ssh start
    echo "[SSH] Ready on port 22"
fi
```

**Enables**:
- SSH access on port 22
- Key-based authentication only
- SFTP for file transfers

#### JupyterLab Setup

```bash
if [[ -n "$JUPYTER_PASSWORD" ]]; then
    echo "[Jupyter] Starting JupyterLab on port 8888..."
    nohup jupyter lab \
        --allow-root \
        --no-browser \
        --port=8888 \
        --ip=0.0.0.0 \
        --ServerApp.token="$JUPYTER_PASSWORD" \
        --ServerApp.allow_origin='*' \
        > /var/log/jupyter.log 2>&1 &
fi
```

**Features**:
- Token-protected access
- Root user support
- CORS enabled for API access

#### Model Download

```bash
echo "[Models] Starting model downloads..."
/download_models.sh
```

Calls `download_models.sh` which handles:
- WAN 2.1/2.2 models
- VibeVoice TTS
- ControlNet models
- Optional models based on env vars

#### R2 Sync Daemon

```bash
if [ "${ENABLE_R2_SYNC:-false}" = "true" ]; then
    echo "[R2 Sync] Starting background sync daemon..."
    mkdir -p /workspace/ComfyUI/output
    nohup /r2_sync.sh > /var/log/r2_sync_init.log 2>&1 &
    echo "[R2 Sync] Daemon active, monitoring /workspace/ComfyUI/output"
fi
```

Starts `r2_sync.sh` daemon that:
- Watches `/workspace/ComfyUI/output` with inotifywait
- Detects new files (png, jpg, mp4, webm, wav)
- Uploads to R2 via `upload_to_r2.py`

#### ComfyUI Startup

```bash
echo "[ComfyUI] Starting on port ${COMFYUI_PORT:-8188}..."
cd /workspace/ComfyUI
exec python main.py \
    --listen 0.0.0.0 \
    --port ${COMFYUI_PORT:-8188} \
    --enable-cors-header \
    --preview-method auto \
    $COMFYUI_ARGS
```

**Flags**:
- `--listen 0.0.0.0` - Bind all interfaces
- `--enable-cors-header` - Allow cross-origin requests
- `--preview-method auto` - Generate image previews

---

## 5. Port Configuration

### Port Summary Table

| Port | Protocol | Service | Purpose | Access |
|------|----------|---------|---------|--------|
| 22 | TCP | SSH | Remote terminal access | SSH client |
| 8188 | HTTP | ComfyUI | Main web interface | Browser, API |
| 8888 | HTTP | JupyterLab | Python notebook server | Browser |
| 8000 | TCP | XTTS API | TTS REST API (separate container) | API calls |
| 4123 | TCP | XTTS internal | Internal container port | Docker networking |
| 19123 | TCP | Custom | Optional custom services | Application-specific |

### Port Configuration in Docker Compose

```yaml
services:
  hearmeman-extended:
    ports:
      - "8188:8188"   # ComfyUI
      - "8888:8888"   # JupyterLab (optional)
      - "2222:22"     # SSH (optional)
```

### RunPod Port Format

```bash
--ports "8188/http"    # Expose as HTTP endpoint
--ports "22/tcp"       # Expose as TCP endpoint
```

**Format**: `PORT/PROTOCOL` or `PORT/http` for web endpoints

### Port Security Considerations

| Port | Security | Recommendation |
|------|----------|----------------|
| 22 | SSH | Use key-based auth only, firewall if possible |
| 8188 | HTTP | Use behind authentication proxy in production |
| 8888 | HTTP | Use strong token, disable if not needed |
| 8000 | API | Internal only, never expose publicly |

---

## 6. Datacenter Considerations

### Datacenter Speed Comparison

| Region | Startup Time | Network Speed | Recommendation |
|--------|--------------|---------------|----------------|
| **US (Secure Cloud)** | ~37 sec | 51 MB/s | **Recommended** |
| US (Community) | ~1 sec | Variable | Good for testing |
| EU (CZ) | 4+ min | Unknown | Avoid for speed-critical |
| UAE | 2+ min | Slow | Avoid |

### Key Findings

**US Secure Cloud**:
- Startup time: ~37 seconds (includes GPU initialization)
- Network speed: 51 MB/s sustained
- Best for: Production workloads requiring reliability
- Cost: Premium (secure cloud pricing)

**US Community Cloud**:
- Startup time: ~1 second (pod already warm)
- Network speed: Variable (shared resources)
- Best for: Development, testing, quick iterations
- Cost: Standard community pricing

**EU Datacenters**:
- Startup time: 4+ minutes (cold boot)
- Network speed: Inconsistent
- Best for: EU-based users needing data residency
- Limitation: Slower model downloads

### Recommended Datacenter Selection

| Use Case | Recommended Datacenter | Rationale |
|----------|------------------------|-----------|
| Production video generation | US Secure Cloud | Reliable, fast, 51 MB/s |
| Development/testing | US Community | Fastest startup, cost-effective |
| EU data residency | EU (last resort) | Accept slower startup |
| Quick experiments | US Community | Instant pod availability |

### Secure Cloud vs Community Cloud

| Feature | Secure Cloud | Community Cloud |
|---------|--------------|-----------------|
| GPU Availability | Guaranteed | Best-effort |
| Network Speed | 51 MB/s | Variable |
| Startup Time | ~37 sec | ~1 sec |
| Cost | Premium | Standard |
| Isolation | Dedicated | Shared |
| Recommendation | Production | Development |

### Performance Benchmarks

#### Pod Startup Time Breakdown

| Phase | Time (US Secure) | Time (US Community) |
|-------|------------------|---------------------|
| Image pull | ~10 sec | ~1 sec |
| Container init | ~5 sec | Instant |
| GPU detection | ~2 sec | Instant |
| Model downloads | ~15-20 min | ~15-20 min |
| ComfyUI start | ~5 sec | ~5 sec |
| **Total (no cache)** | **~20 min** | **~18 min** |
| **Total (cached volume)** | **~1 min** | **~30 sec** |

#### Model Download Speeds

| Model | Size | Time (Secure Cloud) | Time (Community) |
|-------|------|---------------------|------------------|
| WAN 2.1 720p | 25 GB | ~8 min @ 51 MB/s | Variable |
| WAN 2.2 Distilled | 28 GB | ~9 min @ 51 MB/s | Variable |
| VibeVoice-Large | 18 GB | ~6 min @ 51 MB/s | Variable |
| Illustrious | 6.5 GB | ~2 min @ 51 MB/s | Variable |

#### R2 Upload Performance

| File Type | Size | Upload Time | Notes |
|-----------|------|-------------|-------|
| Image (768px) | 1-2 MB | < 1 sec | Instant upload |
| WAN 720p video | 20-50 MB | ~1-2 sec | Depends on R2 region |
| TTS audio | 0.5-2 MB | < 1 sec | Instant upload |

---

## 7. Environment Variable Reference

### Build-time Variables (Dockerfile)

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_R2_SYNC` | false | Enable R2 output sync daemon |
| `R2_BUCKET` | runpod | R2 bucket name |
| `R2_ENDPOINT` | R2 URL | Cloudflare R2 endpoint |
| `ENABLE_WAN22_DISTILL` | false | Enable WAN 2.2 TurboDiffusion |
| `BAKE_WAN_720P` | false | Pre-bake WAN models into image |
| `BAKE_WAN_480P` | false | Pre-bake WAN 480p models |
| `BAKE_ILLUSTRIOUS` | false | Pre-bake Illustrious model |

### Runtime Variables (RunPod Template)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_VIBEVOICE` | visible | false | Enable VibeVoice TTS |
| `VIBEVOICE_MODEL` | visible | Large | VibeVoice model size (1.5B/Large) |
| `ENABLE_CONTROLNET` | visible | true | Enable ControlNet models |
| `WAN_720P` | visible | false | Enable WAN 2.1 T2V 720p |
| `ENABLE_I2V` | visible | false | Enable Image-to-Video |
| `ENABLE_WAN22_DISTILL` | visible | false | Enable TurboDiffusion I2V |
| `ENABLE_ILLUSTRIOUS` | visible | false | Enable Realism Illustrious |
| `ENABLE_ZIMAGE` | visible | false | Enable Z-Image Turbo |
| `ENABLE_R2_SYNC` | visible | false | Enable R2 output sync |
| `R2_ENDPOINT` | visible | - | R2 endpoint URL |
| `R2_BUCKET` | visible | runpod | R2 bucket name |
| `R2_ACCESS_KEY_ID` | secret | - | R2 access key |
| `R2_SECRET_ACCESS_KEY` | secret | - | R2 secret key |
| `GPU_TIER` | visible | consumer | GPU tier (consumer/prosumer/datacenter) |
| `GPU_MEMORY_MODE` | visible | auto | Memory management mode |
| `PUBLIC_KEY` | secret | - | SSH public key for access |
| `JUPYTER_PASSWORD` | secret | - | JupyterLab password/token |
| `CIVITAI_API_KEY` | secret | - | CivitAI API key |
| `COMFYUI_ARGS` | visible | - | Additional CLI args |

### Tier Configuration

#### Consumer GPU (8-24GB VRAM)

```bash
--env "GPU_TIER=consumer"
--env "GPU_MEMORY_MODE=auto"
--env "ENABLE_GENFOCUS=true"
--env "ENABLE_QWEN_EDIT=true"
--env "QWEN_EDIT_MODEL=Q4_K_M"
--env "ENABLE_MVINVERSE=true"
```

#### Prosumer GPU (24-48GB VRAM)

```bash
--env "GPU_TIER=prosumer"
--env "GPU_MEMORY_MODE=auto"
--env "ENABLE_FLASHPORTRAIT=true"
--env "ENABLE_STORYMEM=true"
```

#### Datacenter GPU (48-80GB VRAM)

```bash
--env "GPU_TIER=datacenter"
--env "GPU_MEMORY_MODE=full"
--env "ENABLE_INFCAM=true"
--env "ENABLE_FLASHPORTRAIT=true"
--env "ENABLE_STORYMEM=true"
--env "QWEN_EDIT_MODEL=full"
```

---

## 8. Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| CUDA out of memory | VRAM exceeded | Increase --medvram or use smaller models |
| GPU not detected | nvidia-smi failed | Contact RunPod support, try different image |
| Model download timeout | Network slow | Use US datacenter, enable R2 cache |
| R2 upload fails | Invalid credentials | Verify secrets are set correctly |
| SSH not working | PUBLIC_KEY not set | Add public key to template |
| JupyterLab 404 | Password not set | Set JUPYTER_PASSWORD env var |

### Verification Commands

```bash
# Check GPU
nvidia-smi

# Check GPU VRAM detection
nvidia-smi --query-gpu=memory.total --format=csv

# Verify ComfyUI running
curl -s http://localhost:8188/api/system_stats | jq

# Check R2 sync daemon
ps aux | grep r2_sync

# Test R2 connection
python3 /upload_to_r2.py --test

# Verify models downloaded
ls -la /workspace/ComfyUI/models/diffusion_models/
```

---

## 9. Quick Reference Commands

### Deploy to RunPod (Standard)

```bash
~/.local/bin/runpodctl create pod \
  --name "hearmeman-$(date +%H%M)" \
  --imageName "ghcr.io/mensajerokaos/hearmeman-extended:latest" \
  --gpuType "NVIDIA GeForce RTX 4090" \
  --gpuCount 1 \
  --containerDiskSize 20 \
  --volumeSize 50 \
  --secureCloud \
  --ports "8188/http" \
  --env "ENABLE_VIBEVOICE=true" \
  --env "WAN_720P=true" \
  --env "ENABLE_R2_SYNC=true" \
  --env "R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com" \
  --env "R2_BUCKET=runpod" \
  --env "R2_ACCESS_KEY_ID={{RUNPOD_SECRET_r2_access_key}}" \
  --env "R2_SECRET_ACCESS_KEY={{RUNPOD_SECRET_r2_secret_key}}"
```

### Test R2 Upload Locally

```bash
export R2_ENDPOINT=https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com
export R2_ACCESS_KEY_ID=your_key
export R2_SECRET_ACCESS_KEY=your_secret
export R2_BUCKET=runpod

python docker/upload_to_r2.py test_file.png
```

### Manual Docker Build and Push

```bash
cd /home/oz/projects/2025/oz/12/runpod/docker
docker tag hearmeman-extended:local ghcr.io/oz/hearmeman-extended:latest
echo $GITHUB_TOKEN | docker login ghcr.io -u oz --password-stdin
docker push ghcr.io/oz/hearmeman-extended:latest
```

### Local Docker Development

```bash
cd /home/oz/projects/2025/oz/12/runpod/docker
docker compose build
docker compose up -d
```

---
