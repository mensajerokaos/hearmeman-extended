---
phase: 2
title: Pod Template Configuration
duration: 10 minutes
author: oz
model: claude-opus-4-5-20251101
---

# Phase 2: Pod Template Configuration

## Prerequisites

- [ ] Phase 1 scripts installed and tested
- [ ] RunPod API key available (`$RUNPOD_API_KEY` in `~/.zshrc`)
- [ ] Pod ID: `k02604uwhjq6dm`

## Objective

Configure the RunPod pod template to:
1. Set CUDA environment variables automatically
2. Run startup script on cold boot
3. (Optional) Upgrade PyTorch to cu121/cu124

---

## Option A: Environment Variables Only (Recommended First)

### Step 1: Access RunPod Console
1. Go to https://runpod.io/console/pods
2. Find pod `k02604uwhjq6dm` (vibevoice)
3. Click "Edit Pod" or pod settings

### Step 2: Set Environment Variables
Add these environment variables in the pod configuration:

| Variable | Value |
|----------|-------|
| `CUDA_VISIBLE_DEVICES` | `0` |
| `CUDA_DEVICE_ORDER` | `PCI_BUS_ID` |
| `NVIDIA_VISIBLE_DEVICES` | `all` |
| `NVIDIA_DRIVER_CAPABILITIES` | `compute,utility` |

### Step 3: Save and Restart
1. Save pod configuration
2. Stop pod: `podStop` mutation
3. Start pod: `podResume` mutation
4. SSH in and verify: `echo $CUDA_VISIBLE_DEVICES`

### API Commands
```bash
# Get API key
RUNPOD_API_KEY=$(grep RUNPOD_API_KEY ~/.zshrc | cut -d= -f2 | tr -d '"')

# Stop pod
curl -s --request POST \
  --header 'content-type: application/json' \
  --url "https://api.runpod.io/graphql?api_key=$RUNPOD_API_KEY" \
  --data '{"query": "mutation { podStop(input: { podId: \"k02604uwhjq6dm\" }) { id desiredStatus } }"}'

# Wait 30 seconds
sleep 30

# Resume pod
curl -s --request POST \
  --header 'content-type: application/json' \
  --url "https://api.runpod.io/graphql?api_key=$RUNPOD_API_KEY" \
  --data '{"query": "mutation { podResume(input: { podId: \"k02604uwhjq6dm\" }) { id desiredStatus } }"}'
```

---

## Option B: Container Start Command (Advanced)

### Step 1: Create Auto-Start Script
On the pod, create `/workspace/auto_start.sh`:

```bash
#!/bin/bash
# auto_start.sh - Automatic startup for RunPod cold boot
# Runs when container starts via Container Start Command

LOG_FILE="/workspace/startup.log"

echo "========================================" >> "$LOG_FILE"
echo "[$(date -Iseconds)] Auto Start: Container starting..." >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Set CUDA environment
export CUDA_VISIBLE_DEVICES=0
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=compute,utility

echo "[$(date -Iseconds)] Auto Start: CUDA env vars set" >> "$LOG_FILE"

# Wait for network volume
MAX_WAIT=30
for i in $(seq 1 $MAX_WAIT); do
    if [ -d "/workspace/ComfyUI" ]; then
        echo "[$(date -Iseconds)] Auto Start: Network volume ready" >> "$LOG_FILE"
        break
    fi
    echo "[$(date -Iseconds)] Auto Start: Waiting for /workspace... ($i/$MAX_WAIT)" >> "$LOG_FILE"
    sleep 1
done

# Start ComfyUI if scripts exist
if [ -f "/workspace/start_comfyui.sh" ]; then
    echo "[$(date -Iseconds)] Auto Start: Launching ComfyUI..." >> "$LOG_FILE"
    nohup /workspace/start_comfyui.sh >> /workspace/comfyui.log 2>&1 &
    echo "[$(date -Iseconds)] Auto Start: ComfyUI launched (PID: $!)" >> "$LOG_FILE"
else
    echo "[$(date -Iseconds)] Auto Start: WARNING - start_comfyui.sh not found" >> "$LOG_FILE"
fi

# Keep container running (SSH access)
echo "[$(date -Iseconds)] Auto Start: Container ready" >> "$LOG_FILE"
sleep infinity
```

### Step 2: Install Script
```bash
ssh runpod
cat > /workspace/auto_start.sh << 'SCRIPT_END'
# ... (content above)
SCRIPT_END
chmod +x /workspace/auto_start.sh
```

### Step 3: Update Pod Template

In RunPod console, set Container Start Command to:
```
/bin/bash /workspace/auto_start.sh
```

Or use JSON format:
```json
{ "cmd": ["/workspace/auto_start.sh"], "entrypoint": ["/bin/bash"] }
```

**Note**: The Container Start Command runs AFTER the network volume mounts, so `/workspace` should be available.

---

## Option C: Custom Template (Most Robust)

### Step 1: Create Pod Template
1. Go to https://runpod.io/console/templates
2. Click "New Template"
3. Configure:

| Field | Value |
|-------|-------|
| Template Name | `vibevoice-cuda-fixed` |
| Container Image | (same as current pod) |
| Docker Command | `/bin/bash /workspace/auto_start.sh` |

### Step 2: Environment Variables
Add in template:
```
CUDA_VISIBLE_DEVICES=0
CUDA_DEVICE_ORDER=PCI_BUS_ID
NVIDIA_VISIBLE_DEVICES=all
NVIDIA_DRIVER_CAPABILITIES=compute,utility
```

### Step 3: Deploy Pod with Template
1. Stop current pod
2. Create new pod from template
3. Attach same network volume (`ul56y9ya5h`)

---

## (Optional) PyTorch Upgrade

### Check Current Version
```bash
ssh runpod
source /workspace/venv/bin/activate
python -c "import torch; print(torch.__version__)"
```

### Upgrade to cu121 (Recommended)
```bash
source /workspace/venv/bin/activate
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Verify Upgrade
```bash
python -c "import torch; print(f'Version: {torch.__version__}, CUDA: {torch.version.cuda}')"
```

Expected: `Version: 2.x.x+cu121, CUDA: 12.1`

---

## Verification Steps

### 1. Stop and Start Pod
```bash
# Stop
curl -s --request POST \
  --header 'content-type: application/json' \
  --url "https://api.runpod.io/graphql?api_key=$RUNPOD_API_KEY" \
  --data '{"query": "mutation { podStop(input: { podId: \"k02604uwhjq6dm\" }) { id desiredStatus } }"}'

# Wait 60 seconds for full stop
sleep 60

# Resume
curl -s --request POST \
  --header 'content-type: application/json' \
  --url "https://api.runpod.io/graphql?api_key=$RUNPOD_API_KEY" \
  --data '{"query": "mutation { podResume(input: { podId: \"k02604uwhjq6dm\" }) { id desiredStatus } }"}'
```

### 2. Update SSH Config
After pod restarts, get new SSH port from RunPod dashboard and update `~/.ssh/config`:
```bash
# Check pod status and ports
curl -s --request POST \
  --header 'content-type: application/json' \
  --url "https://api.runpod.io/graphql?api_key=$RUNPOD_API_KEY" \
  --data '{"query": "query Pods { myself { pods { id name desiredStatus runtime { ports { ip isIpPublic privatePort publicPort } } } } }"}'
```

### 3. SSH In and Verify
```bash
ssh runpod
echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
echo "CUDA_DEVICE_ORDER=$CUDA_DEVICE_ORDER"
source /workspace/venv/bin/activate
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

### 4. Check ComfyUI
```bash
# If auto-start configured
curl http://localhost:8188/system_stats

# Check logs
tail -50 /workspace/comfyui.log
```

---

## Troubleshooting

### Environment Variables Not Applied
1. Check pod configuration in RunPod console
2. Verify with: `env | grep CUDA`
3. Try Option B (Container Start Command)

### ComfyUI Not Auto-Starting
1. Check startup log: `cat /workspace/startup.log`
2. Verify script exists: `ls -la /workspace/auto_start.sh`
3. Start manually: `nohup /workspace/start_comfyui.sh &`

### SSH Port Changed
1. Get new port from RunPod console or API
2. Update `~/.ssh/config` with new port

---

## Rollback Plan

### Remove Auto-Start
1. Clear Container Start Command in pod config
2. Delete: `rm /workspace/auto_start.sh`
3. Restart pod

### Remove Environment Variables
1. Remove CUDA vars from pod configuration
2. Restart pod

---

## Next Phase

After Phase 2 is verified working:
- Proceed to Phase 3: Validation & Monitoring
- Test cold start cycle
- Document results
