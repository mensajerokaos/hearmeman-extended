---
author: oz
model: claude-opus-4-5
date: 2025-12-24 01:40
task: Phase 2 detailed expansion - SSH Setup for Hearmeman ephemeral deployment
---

# Phase 2: SSH Setup (Detailed Expansion)

**Objective**: Configure SSH connection for command-line access to the ephemeral RunPod pod.

**Duration**: 2-5 minutes

**Prerequisites**:
- Phase 1 complete (pod deployed and running)
- SSH public key already configured in RunPod account settings
- Local SSH key pair: `~/.ssh/id_ed25519` (or `~/.ssh/id_rsa`)

---

## Step 2.1: Finding IP and Port from RunPod Console

After deploying the pod, you need to retrieve the SSH connection details. These change on every pod restart.

### Visual Guide

1. **Navigate to Pods**:
   - Go to https://console.runpod.io/pods
   - Find your pod (e.g., "jose-wan-720p" or the default template name)
   - Ensure status shows "Running" (green indicator)

2. **Click "Connect" Button**:
   - Located on the right side of the pod row
   - Opens a dropdown/modal with connection options

3. **Locate SSH Connection String**:
   - Look for "SSH over exposed TCP" section
   - Format: `ssh root@<IP_ADDRESS> -p <PORT> -i ~/.ssh/<KEY_FILE>`
   - Example: `ssh root@194.68.245.83 -p 22095 -i ~/.ssh/id_ed25519`

4. **Extract Values**:
   - **IP Address**: The number after `root@` (e.g., `194.68.245.83`)
   - **Port**: The number after `-p` (e.g., `22095`)

### Alternative: Web Terminal for Quick Access

If you just need quick access without SSH setup:
- Click the "Connect" button → "Connect to Web Terminal"
- Opens browser-based terminal (useful for emergencies)

---

## Step 2.2: Complete ~/.ssh/config Entry

### Full Config Block

Add or update this block in `~/.ssh/config`:

```ssh-config
# RunPod - Hearmeman Ephemeral Pod
# Note: HostName and Port change on each pod restart
# Update values from RunPod Console → Pod → Connect button
Host runpod
    HostName <NEW_IP_ADDRESS>
    Port <NEW_PORT>
    User root
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 60
    ServerAliveCountMax 3

# Optional: Internal hostname (only works from other RunPod pods)
# Host runpod-internal
#     HostName <POD_ID>.runpod.internal
#     User root
#     IdentityFile ~/.ssh/id_ed25519
#     StrictHostKeyChecking no
```

### Option Explanations

| Option | Value | Purpose |
|--------|-------|---------|
| `HostName` | Dynamic IP | RunPod proxy server IP (changes per restart) |
| `Port` | Dynamic port | Mapped SSH port (changes per restart) |
| `User` | `root` | All RunPod containers use root |
| `IdentityFile` | Your private key | Path to SSH private key |
| `StrictHostKeyChecking` | `no` | Avoids "host key changed" errors (expected with ephemeral) |
| `UserKnownHostsFile` | `/dev/null` | Don't save host keys (they'll change anyway) |
| `ServerAliveInterval` | `60` | Send keepalive every 60s to prevent disconnects |
| `ServerAliveCountMax` | `3` | Disconnect after 3 missed keepalives (3 min timeout) |

### Example with Real Values

```ssh-config
Host runpod
    HostName 194.68.245.83
    Port 22095
    User root
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

---

## Step 2.3: Updating SSH Config (Methods)

### Method A: Manual Edit

```bash
# Open config in editor
nano ~/.ssh/config
# or
code ~/.ssh/config
```

### Method B: Sed Command (One-liner)

For existing `runpod` host entry:

```bash
NEW_IP="194.68.245.83"
NEW_PORT="22095"

# Update in place
sed -i "/Host runpod/,/Host [^r]/{s/HostName .*/HostName $NEW_IP/}" ~/.ssh/config
sed -i "/Host runpod/,/Host [^r]/{s/Port [0-9]*/Port $NEW_PORT/}" ~/.ssh/config
```

### Method C: Shell Function (Add to ~/.bashrc or ~/.zshrc)

```bash
# Quick update function
update_runpod_ssh() {
    local ip="$1"
    local port="$2"

    if [[ -z "$ip" || -z "$port" ]]; then
        echo "Usage: update_runpod_ssh <IP> <PORT>"
        echo "Example: update_runpod_ssh 194.68.245.83 22095"
        return 1
    fi

    sed -i "/Host runpod$/,/Host [^r]/{s/HostName .*/HostName $ip/}" ~/.ssh/config
    sed -i "/Host runpod$/,/Host [^r]/{s/Port [0-9]*/Port $port/}" ~/.ssh/config

    echo "Updated ~/.ssh/config:"
    grep -A5 "Host runpod$" ~/.ssh/config
}

# Usage after pod restart:
# update_runpod_ssh 194.68.245.83 22095
```

---

## Step 2.4: SSH Connection Commands

### Basic Connection

```bash
# Using config alias
ssh runpod

# Direct connection (no config needed)
ssh root@194.68.245.83 -p 22095 -i ~/.ssh/id_ed25519
```

### Connection with Specific Options

```bash
# Verbose mode (debugging connection issues)
ssh -v runpod

# Very verbose (more debug info)
ssh -vvv runpod

# Force new connection (bypass cached sockets)
ssh -o ControlPath=none runpod
```

### Run Command Directly

```bash
# Check GPU status
ssh runpod "nvidia-smi"

# Check model downloads
ssh runpod "ls -la /workspace/ComfyUI/models/diffusion_models/"

# Check disk space
ssh runpod "df -h /workspace"

# Check running processes
ssh runpod "ps aux | grep -E 'python|comfyui'"
```

---

## Step 2.5: ComfyUI Tunnel Setup (Port 8188)

ComfyUI runs on port 8188 inside the pod. You need an SSH tunnel to access it from your browser.

### Foreground Tunnel (Interactive)

```bash
# Creates tunnel AND gives you a shell
ssh -L 8188:localhost:8188 runpod

# Then in browser: http://localhost:8188
```

### Background Tunnel (Non-blocking)

```bash
# Start tunnel in background, no shell
ssh -fNL 8188:localhost:8188 runpod

# Verify tunnel is running
ps aux | grep "ssh.*8188"
# or
lsof -i :8188
```

### Kill Background Tunnel

```bash
# Find and kill the tunnel process
pkill -f "ssh.*8188.*runpod"

# or find PID and kill
lsof -ti :8188 | xargs kill -9
```

### Multi-Port Tunnel (ComfyUI + Jupyter)

If you need Jupyter Lab access too:

```bash
# Tunnel both ports
ssh -L 8188:localhost:8188 -L 8888:localhost:8888 runpod
```

### SSH Config Tunnel (Automatic)

Add to `~/.ssh/config` for automatic port forwarding:

```ssh-config
Host runpod
    HostName <IP>
    Port <PORT>
    User root
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LocalForward 8188 localhost:8188
    # Optional: Jupyter
    # LocalForward 8888 localhost:8888
```

Then just `ssh runpod` and tunnel is automatic.

---

## Step 2.6: Connection Verification Steps

Run these commands in order to verify full connectivity:

### 1. Basic SSH Test

```bash
ssh runpod "echo 'SSH OK'"
# Expected: SSH OK
```

### 2. GPU Verification

```bash
ssh runpod "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader"
# Expected: NVIDIA L40S, 46068 MiB (or similar 48GB GPU)
```

### 3. Check Python/PyTorch

```bash
ssh runpod "python3 -c 'import torch; print(f\"PyTorch {torch.__version__}, CUDA {torch.cuda.is_available()}\")'"
# Expected: PyTorch 2.8.0+..., CUDA True
```

### 4. Check Disk Space

```bash
ssh runpod "df -h /workspace"
# Expected: >200GB free (450GB ephemeral minus model downloads)
```

### 5. Check Model Downloads

```bash
ssh runpod "ls -lh /workspace/ComfyUI/models/diffusion_models/ | head -10"
# Expected: wan*.safetensors files
```

### 6. Check ComfyUI Status

```bash
# Check if ComfyUI process is running
ssh runpod "pgrep -f 'python.*main.py' && echo 'ComfyUI Running' || echo 'ComfyUI NOT Running'"

# Check ComfyUI API (if running)
ssh runpod "curl -s localhost:8188/system_stats | head -c 100"
# Expected: JSON with system info
```

### 7. Full Health Check (One-liner)

```bash
ssh runpod 'echo "=== GPU ==="; nvidia-smi -L; echo "=== Disk ==="; df -h /workspace; echo "=== ComfyUI ==="; curl -s localhost:8188/system_stats > /dev/null && echo "Running" || echo "Not Running"'
```

---

## Step 2.7: SSH Key Considerations

### Key Location

RunPod requires your public key to be uploaded to your account settings:

1. Go to https://console.runpod.io/settings
2. Find "SSH Keys" section
3. Paste your public key content

### Finding Your Public Key

```bash
# Ed25519 key (recommended)
cat ~/.ssh/id_ed25519.pub

# RSA key (if Ed25519 not available)
cat ~/.ssh/id_rsa.pub
```

### Generating a New Key (if needed)

```bash
# Generate Ed25519 key (recommended)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Or RSA (if Ed25519 not supported)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

### Multiple Keys

If you have multiple SSH keys, specify which to use:

```bash
# In SSH config
Host runpod
    IdentityFile ~/.ssh/runpod_key

# Or on command line
ssh -i ~/.ssh/runpod_key root@<IP> -p <PORT>
```

### Key Permissions (Must Be Correct)

```bash
# Fix permissions if needed
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
chmod 600 ~/.ssh/config
```

---

## Step 2.8: Alternative Connection Methods

### A. Web Terminal (Browser-based)

**Pros**: No SSH config needed, works immediately
**Cons**: Limited functionality, no file transfer, less stable

1. Go to https://console.runpod.io/pods
2. Find your pod
3. Click "Connect" → "Connect to Web Terminal"
4. Terminal opens in new browser tab

### B. RunPod CLI (API-based)

```bash
# Install RunPod CLI
pip install runpod

# Set API key
export RUNPOD_API_KEY="your_api_key_here"

# List pods
runpodctl get pods

# SSH via CLI (auto-discovers port)
runpodctl ssh --pod-id <POD_ID>
```

### C. VS Code Remote SSH

1. Install "Remote - SSH" extension in VS Code
2. Add RunPod host to SSH config (as shown above)
3. Ctrl+Shift+P → "Remote-SSH: Connect to Host" → "runpod"
4. VS Code opens in pod filesystem

### D. JupyterLab (if enabled)

If `JUPYTER_PASSWORD` env var was set during deploy:

```bash
# Tunnel Jupyter port
ssh -L 8888:localhost:8888 runpod

# Browser: http://localhost:8888
# Password: value of JUPYTER_PASSWORD
```

---

## Step 2.9: Troubleshooting Connection Issues

### Issue 1: "Connection refused"

**Symptoms**: `ssh: connect to host ... port ...: Connection refused`

**Causes & Fixes**:

| Cause | Fix |
|-------|-----|
| Pod not running | Check RunPod console, start pod |
| Wrong IP/port | Re-copy from Console → Connect |
| Pod still initializing | Wait 1-2 min, retry |
| Firewall blocking | Try web terminal instead |

```bash
# Verify pod is running via API
curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" \
    https://api.runpod.io/graphql \
    -d '{"query":"{ pod(input: {podId: \"<POD_ID>\"}) { id desiredStatus runtime { ports { ip port } } } }"}'
```

### Issue 2: "Permission denied (publickey)"

**Symptoms**: `Permission denied (publickey).`

**Causes & Fixes**:

| Cause | Fix |
|-------|-----|
| Public key not in RunPod | Upload to Settings → SSH Keys |
| Wrong key file path | Check `IdentityFile` in config |
| Key permissions wrong | Run `chmod 600 ~/.ssh/id_ed25519` |

```bash
# Test with verbose to see which key is being tried
ssh -vvv runpod 2>&1 | grep "Offering public key"
```

### Issue 3: "Host key verification failed"

**Symptoms**: `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!`

**Cause**: Normal for ephemeral pods (IP reused by different containers)

**Fix**: Add these to SSH config:
```ssh-config
StrictHostKeyChecking no
UserKnownHostsFile /dev/null
```

Or remove old host key:
```bash
ssh-keygen -R "[<IP>]:<PORT>"
```

### Issue 4: "Connection timed out"

**Symptoms**: `ssh: connect to host ... Connection timed out`

**Causes & Fixes**:

| Cause | Fix |
|-------|-----|
| Pod shut down | Restart pod |
| Network issue | Try different network/VPN |
| Wrong port | Re-check console |

### Issue 5: SSH Hangs / No Response

**Symptoms**: SSH command hangs, no output

**Causes & Fixes**:

| Cause | Fix |
|-------|-----|
| Pod busy (model loading) | Wait 5-10 min |
| SSH service not started | Use web terminal to debug |
| Network latency | Add `ServerAliveInterval 60` to config |

```bash
# Try with connection timeout
ssh -o ConnectTimeout=10 runpod "echo OK"
```

### Issue 6: Tunnel Port Already in Use

**Symptoms**: `bind: Address already in use` when creating tunnel

**Fix**:
```bash
# Find what's using port 8188
lsof -i :8188

# Kill existing tunnel
pkill -f "ssh.*8188.*runpod"

# Or use different local port
ssh -L 8189:localhost:8188 runpod
# Then access: http://localhost:8189
```

---

## Quick Reference Card

```bash
# === AFTER POD DEPLOY ===

# 1. Get connection details from console
# IP: xxx.xxx.xxx.xxx  Port: xxxxx

# 2. Update SSH config
sed -i "/Host runpod$/,/Host [^r]/{s/HostName .*/HostName <NEW_IP>/}" ~/.ssh/config
sed -i "/Host runpod$/,/Host [^r]/{s/Port [0-9]*/Port <NEW_PORT>/}" ~/.ssh/config

# 3. Verify connection
ssh runpod "nvidia-smi -L"

# 4. Start ComfyUI tunnel
ssh -L 8188:localhost:8188 runpod

# 5. Open browser: http://localhost:8188
```

---

## Success Criteria for Phase 2

| # | Check | Command | Expected Result |
|---|-------|---------|-----------------|
| ✓ | SSH config updated | `grep -A5 "Host runpod$" ~/.ssh/config` | New IP and port shown |
| ✓ | SSH connects | `ssh runpod "echo OK"` | Returns "OK" |
| ✓ | GPU accessible | `ssh runpod "nvidia-smi -L"` | Shows 48GB GPU |
| ✓ | Tunnel works | `ssh -L 8188:localhost:8188 runpod` | No errors |
| ✓ | ComfyUI accessible | Browser: `http://localhost:8188` | ComfyUI UI loads |

**Phase 2 Complete** → Proceed to Phase 3: Model Installation

---

*Document generated: 2025-12-24*
*Parent: master-overview.md*
*Next: phase-3.md (Model Installation)*
