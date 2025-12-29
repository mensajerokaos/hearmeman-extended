# RunPod Template Configuration Guide: hearmeman-extended-r2

This document provides the standard configuration for deploying the **HearMeMan Extended** container on RunPod with Cloudflare R2 integration.

## 1. Core Template Settings

| Field | Value |
|-------|-------|
| **Template Name** | `hearmeman-extended-r2` |
| **Container Image** | `ghcr.io/oz/hearmeman-extended:latest` |
| **Container Disk** | 20 GB |
| **Volume Disk** | 100 GB (Minimum) |
| **Volume Mount Path** | `/workspace` |

## 2. Port Mapping

Ensure the following ports are mapped in the template to enable external access:
- **HTTP (8188)**: ComfyUI Web Interface
- **HTTP (8888)**: Jupyter Lab / Terminal access
- **TCP (22)**: SSH access (optional but recommended)

## 3. Environment Variables

### Static Configuration
Add these as standard environment variables in the template:

| Key | Value |
|-----|-------|
| `R2_BUCKET` | `runpod` |
| `R2_ENDPOINT` | `https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com` |
| `R2_REGION` | `auto` |

### Sensitive Credentials (Use RunPod Secrets)
Map these variables to your RunPod account secrets:

| Key | Reference |
|-----|-----------|
| `R2_ACCESS_KEY` | `$R2_ACCESS_KEY` |
| `R2_SECRET_KEY` | `$R2_SECRET_KEY` |
| `CIVITAI_API_KEY` | `$CIVITAI_API_KEY` |

## 4. Hardware Selection Guide

### Recommended GPUs
1. **The Professional Choice (A6000 48GB)**
   - **Reason**: 48GB VRAM comfortably fits WAN 2.2 5B models without heavy quantization.
   - **Set `GPU_TIER=PROSUMER`**

2. **The Speed King (RTX 4090 24GB)**
   - **Reason**: Best price-to-performance for TurboDiffusion and quantized WAN models.
   - **Set `GPU_TIER=CONSUMER`**

3. **The Powerhouse (A100 80GB)**
   - **Reason**: Necessary for large batches or fine-tuning workflows.
   - **Set `GPU_TIER=DATACENTER`**

## 5. Storage Notes
- The `/workspace` directory is persisted to the network volume.
- Large models should be stored in `/workspace/models` to avoid filling the container disk.
- Syncing to R2 is handled by the internal `r2-sync` scripts or manually via the CLI tools included in the image.
