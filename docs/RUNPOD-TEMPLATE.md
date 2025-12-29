# RunPod Template Configuration

## Template Settings

| Setting | Value |
|---------|-------|
| **Container Image** | `ghcr.io/oz-swe/hearmeman-extended:latest` |
| **Container Disk** | 20 GB |
| **Volume Disk** | 100 GB (for models) |
| **Volume Mount** | `/workspace` |
| **HTTP Ports** | 8188 (ComfyUI), 8888 (Jupyter) |
| **TCP Ports** | 22 (SSH) |

## Environment Variables

### Required for R2 Sync
| Variable | Value | Type |
|----------|-------|------|
| `ENABLE_R2_SYNC` | `true` | Visible |
| `R2_ENDPOINT` | `https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com` | Visible |
| `R2_BUCKET` | `runpod` | Visible |
| `R2_ACCESS_KEY_ID` | (your key) | **Secret** |
| `R2_SECRET_ACCESS_KEY` | (your secret) | **Secret** |

### Model Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `WAN_720P` | `true` | WAN 2.2 720p T2V model |
| `WAN_480P` | `false` | WAN 2.2 480p (smaller, 16GB VRAM) |
| `ENABLE_I2V` | `false` | Image-to-Video support |
| `ENABLE_STEADYDANCER` | `false` | Dance video generation |
| `ENABLE_VIBEVOICE` | `true` | TTS voice cloning |
| `ENABLE_ILLUSTRIOUS` | `false` | Photorealistic image gen |
| `ENABLE_GENFOCUS` | `false` | Depth-of-field refocus |
| `ENABLE_MVINVERSE` | `false` | Material extraction |

### Optional
| Variable | Default | Description |
|----------|---------|-------------|
| `PUBLIC_KEY` | (none) | SSH public key for access |
| `JUPYTER_PASSWORD` | (none) | Enable JupyterLab |
| `CIVITAI_API_KEY` | (none) | For CivitAI model downloads |

## GPU Recommendations

| GPU | VRAM | Best For |
|-----|------|----------|
| RTX 4090 | 24GB | WAN 480p, VibeVoice, Illustrious |
| A5000 | 24GB | Same as 4090 |
| A6000 | 48GB | WAN 720p + TurboDiffusion |
| A100 | 80GB | All models, multiple workflows |
| H100 | 80GB | Maximum throughput |

## VRAM Requirements

| Workflow | VRAM Needed |
|----------|-------------|
| WAN 2.2 480p T2V | ~12-16 GB |
| WAN 2.2 720p T2V | ~24-32 GB |
| WAN 720p + TurboDiffusion | ~24-40 GB |
| VibeVoice TTS | ~8-12 GB |
| Illustrious txt2img | ~8-12 GB |
| SteadyDancer | ~24-32 GB |

## Creating RunPod Secrets

1. Go to RunPod Console → Settings → Secrets
2. Create secrets:
   - Name: `R2_ACCESS_KEY_ID`, Value: your R2 access key
   - Name: `R2_SECRET_ACCESS_KEY`, Value: your R2 secret key
3. Reference in template env vars as `{{ RUNPOD_SECRET_R2_ACCESS_KEY_ID }}`

## Startup Flow

1. Container starts → `start.sh` runs
2. GPU detected → appropriate VRAM args set
3. SSH/Jupyter started (if configured)
4. Models downloaded (first run only, ~10-30 min)
5. R2 sync daemon started (if enabled)
6. ComfyUI starts on port 8188

## Verifying R2 Sync

```bash
# Check sync daemon running
ps aux | grep r2_sync

# Check sync log
tail -f /var/log/r2_sync.log

# Manual upload test
python3 /upload_to_r2.py --test
```

## Troubleshooting

### R2 Upload Fails
- Check credentials: `echo $R2_ACCESS_KEY_ID`
- Test connection: `python3 /upload_to_r2.py --test`
- Check logs: `cat /var/log/r2_sync.log`

### Models Not Downloading
- Check env vars: `env | grep ENABLE`
- Check logs: `cat /var/log/model_download.log`
- Retry: `/download_models.sh`

### ComfyUI OOM
- Reduce resolution (768 instead of 1024)
- Use `--lowvram` or `--medvram` flags
- Check COMFYUI_ARGS env var
