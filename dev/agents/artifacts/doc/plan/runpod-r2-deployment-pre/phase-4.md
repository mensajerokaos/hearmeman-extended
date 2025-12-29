# Phase 4 Implementation Specification: RunPod Template Configuration

## Phase 4 Objective
Create a robust RunPod template configured with R2 cloud storage credentials, optimized for the HearMeMan Extended environment (ComfyUI + WAN 2.2 + TurboDiffusion).

## Step 4.1: RunPod Template Settings
The following settings should be applied in the RunPod "Templates" section.

| Setting | Value |
|---------|-------|
| **Template Name** | `hearmeman-extended-r2` |
| **Container Image** | `ghcr.io/oz/hearmeman-extended:latest` |
| **Container Disk** | 20 GB |
| **Volume Disk** | 100 GB (Provisioned for model storage) |
| **Volume Mount Path** | `/workspace` |
| **Expose HTTP Ports** | `8188` (ComfyUI), `8888` (Jupyter) |
| **Expose TCP Ports** | `22` (SSH) |

## Step 4.2: Environment Variables Configuration
Configure these variables in the template to ensure the application starts with correct storage and performance settings.

### Visible Variables (Public)
| Variable | Value | Description |
|----------|-------|-------------|
| `R2_BUCKET` | `runpod` | The target R2 bucket name. |
| `R2_ENDPOINT` | `https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com` | R2 S3-compatible API endpoint. |
| `R2_REGION` | `auto` | Cloudflare R2 default region. |
| `COMFYUI_PORT` | `8188` | Internal port for ComfyUI. |
| `JUPYTER_PORT` | `8888` | Internal port for Jupyter Lab. |

### GPU Performance Tiers (GPU_TIER)
The `GPU_TIER` variable should be set at pod deployment time or within the template based on expected hardware:
- **RTX 4090 / 3090**: `CONSUMER`
- **A6000 / A5000**: `PROSUMER`
- **A100 / H100**: `DATACENTER`

## Step 4.3: RunPod Secrets Setup
To maintain security, do **NOT** hardcode credentials. Use RunPod Secrets.

### Required Secrets
1. `R2_ACCESS_KEY`: The AWS-style access key for Cloudflare R2.
2. `R2_SECRET_KEY`: The secret key for Cloudflare R2.
3. `CIVITAI_API_KEY`: (Optional) Required for downloading certain models via API.

### Configuration Process
1. Navigate to **User Settings** -> **Secrets**.
2. Add each secret above with its corresponding value.
3. In the Template Environment Variables, reference them using:
   - `R2_ACCESS_KEY` = `$R2_ACCESS_KEY`
   - `R2_SECRET_KEY` = `$R2_SECRET_KEY`

## Step 4.4: GPU Recommendations and VRAM Estimates

| GPU Type | VRAM | Tier | Best Use Case |
|----------|------|------|---------------|
| **RTX 4090** | 24 GB | Consumer | Fast image generation (TurboDiffusion), quantized video models. |
| **A6000** | 48 GB | Prosumer | **Recommended** for WAN 2.2 5B models and high-res video. |
| **A100** | 80 GB | Datacenter | High-batch processing and native BF16 video generation. |

### VRAM Usage Estimates
- **TurboDiffusion (SDXL-based)**: ~8-12 GB VRAM.
- **WAN 2.2 5B (Native BF16)**: ~32-36 GB VRAM.
- **WAN 2.2 5B (GGUF/Quantized)**: ~18-24 GB VRAM (can run on 4090).

## Step 4.5: Deployment Documentation
A user-facing configuration guide will be maintained at `/docs/runpod-template-config.md` for team-wide consistency.
