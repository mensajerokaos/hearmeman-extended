---
phase: 3
title: Validation & Monitoring
duration: 20 minutes
author: oz
model: claude-opus-4-5-20251101
---

# Phase 3: Validation & Monitoring

## Prerequisites

- [ ] Phase 1 scripts installed
- [ ] Phase 2 template configuration applied
- [ ] SSH access working with updated port

## Objective

1. Validate CUDA fix works on cold start
2. Create monitoring commands
3. Document troubleshooting guide
4. Update project documentation

---

## Cold Start Test Procedure

### Step 1: Full Stop
```bash
# Get API key
RUNPOD_API_KEY=$(grep RUNPOD_API_KEY ~/.zshrc | cut -d= -f2 | tr -d '"')

# Stop pod completely
curl -s --request POST \
  --header 'content-type: application/json' \
  --url "https://api.runpod.io/graphql?api_key=$RUNPOD_API_KEY" \
  --data '{"query": "mutation { podStop(input: { podId: \"k02604uwhjq6dm\" }) { id desiredStatus } }"}'

echo "Pod stopping... waiting 60 seconds"
sleep 60
```

### Step 2: Cold Start
```bash
# Resume pod
curl -s --request POST \
  --header 'content-type: application/json' \
  --url "https://api.runpod.io/graphql?api_key=$RUNPOD_API_KEY" \
  --data '{"query": "mutation { podResume(input: { podId: \"k02604uwhjq6dm\" }) { id desiredStatus } }"}'

echo "Pod starting... waiting 90 seconds for cold boot"
sleep 90
```

### Step 3: Get New SSH Port
```bash
# Query pod status
curl -s --request POST \
  --header 'content-type: application/json' \
  --url "https://api.runpod.io/graphql?api_key=$RUNPOD_API_KEY" \
  --data '{"query": "query Pods { myself { pods { id name desiredStatus runtime { ports { ip isIpPublic privatePort publicPort } } } } }"}' \
  | jq '.data.myself.pods[] | select(.id=="k02604uwhjq6dm") | .runtime.ports[] | select(.privatePort==22)'
```

### Step 4: Update SSH Config
Edit `~/.ssh/config` and update the `Port` for `runpod` host.

### Step 5: Verify CUDA
```bash
ssh runpod

# Check environment
echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
echo "CUDA_DEVICE_ORDER=$CUDA_DEVICE_ORDER"

# Check GPU
nvidia-smi

# Check PyTorch CUDA
source /workspace/venv/bin/activate
python /workspace/check_cuda.py
```

### Step 6: Verify ComfyUI
```bash
# Check if running
curl -s http://localhost:8188/system_stats | jq .

# Check logs
tail -100 /workspace/comfyui.log
```

---

## Test Checklist

### Automated Checks
| Check | Command | Expected |
|-------|---------|----------|
| Environment var set | `echo $CUDA_VISIBLE_DEVICES` | `0` |
| Device order set | `echo $CUDA_DEVICE_ORDER` | `PCI_BUS_ID` |
| nvidia-smi works | `nvidia-smi` | GPU info displayed |
| torch.cuda.is_available() | `python -c "import torch; print(torch.cuda.is_available())"` | `True` |
| ComfyUI running | `curl localhost:8188/system_stats` | JSON response |

### Manual Checks
| Check | Steps | Expected |
|-------|-------|----------|
| TTS Generation | Run VibeVoice workflow | Audio file generated |
| Voice cloning | Use Jose Obscura voice | Cloned voice output |
| API response time | Queue a prompt | < 60s for short text |

---

## Monitoring Commands

### Quick Status Check
```bash
# One-liner status
ssh runpod "nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader && curl -s localhost:8188/system_stats | jq -r '.devices[0].name'"
```

### Log Monitoring
```bash
# Watch ComfyUI logs
ssh runpod "tail -f /workspace/comfyui.log"

# Watch startup logs (if auto-start enabled)
ssh runpod "tail -f /workspace/startup.log"
```

### GPU Usage
```bash
# Real-time GPU monitoring
ssh runpod "watch -n 1 nvidia-smi"
```

---

## Troubleshooting Guide

### Issue: CUDA_VISIBLE_DEVICES Not Set

**Symptoms**:
- `echo $CUDA_VISIBLE_DEVICES` returns empty
- `torch.cuda.is_available()` returns `False`

**Fixes**:
1. Check pod environment variables in RunPod console
2. Manually set: `export CUDA_VISIBLE_DEVICES=0`
3. Add to `/workspace/cuda_init.sh`

### Issue: torch.cuda.is_available() Returns False

**Symptoms**:
- nvidia-smi works
- PyTorch can't see GPU

**Diagnostic**:
```bash
python /workspace/check_cuda.py
```

**Fixes**:
1. Set `CUDA_VISIBLE_DEVICES=0`
2. Set `CUDA_DEVICE_ORDER=PCI_BUS_ID`
3. Upgrade PyTorch: `pip install torch --index-url https://download.pytorch.org/whl/cu121`
4. Reload nvidia_uvm: `sudo modprobe -r nvidia_uvm && sudo modprobe nvidia_uvm`

### Issue: cuInit Error Code 3

**Symptoms**:
- `CUDA_ERROR_NOT_INITIALIZED` in logs
- First CUDA operation fails

**Fixes**:
1. Wait longer before CUDA init (increase `RETRY_DELAY` in `cuda_init.sh`)
2. Add more retry attempts
3. Warmup with simple tensor operation

### Issue: ComfyUI Won't Start

**Symptoms**:
- No response on port 8188
- Process not running

**Diagnostic**:
```bash
cat /workspace/comfyui.log
ps aux | grep python
```

**Fixes**:
1. Check venv exists: `ls /workspace/venv`
2. Check ComfyUI exists: `ls /workspace/ComfyUI`
3. Manual start: `nohup /workspace/start_comfyui.sh &`

### Issue: SSH Port Changed

**Symptoms**:
- `ssh runpod` times out
- Connection refused

**Fix**:
1. Check RunPod console for new port
2. Query via API (see Step 3 above)
3. Update `~/.ssh/config`

---

## Documentation Updates

### Add to CLAUDE.md

Add the following section:

```markdown
## RunPod CUDA Initialization

### Cold Start Fix Applied
The pod has a startup script that fixes CUDA initialization issues:

1. **Environment Variables** (set in pod template):
   - `CUDA_VISIBLE_DEVICES=0` - Remaps GPU to device 0
   - `CUDA_DEVICE_ORDER=PCI_BUS_ID` - Consistent device ordering

2. **Startup Scripts** (on network volume):
   - `/workspace/cuda_init.sh` - CUDA environment setup + GPU wait
   - `/workspace/start_comfyui.sh` - ComfyUI launcher with CUDA init
   - `/workspace/check_cuda.py` - Diagnostic script

### After Pod Restart
1. Wait ~90 seconds for cold boot
2. Get new SSH port from RunPod console
3. Update `~/.ssh/config` with new port
4. Verify CUDA: `ssh runpod "source /workspace/venv/bin/activate && python -c 'import torch; print(torch.cuda.is_available())'"`

### Troubleshooting
Run diagnostics: `ssh runpod "source /workspace/venv/bin/activate && python /workspace/check_cuda.py"`

View logs: `ssh runpod "tail -50 /workspace/comfyui.log"`
```

---

## Success Criteria

| Criteria | Target | Actual |
|----------|--------|--------|
| Cold start CUDA detection | 100% | |
| Time to CUDA ready | < 30s | |
| ComfyUI auto-start | Yes | |
| TTS generation works | Yes | |
| No manual intervention | Yes | |

---

## Final Checklist

- [ ] Cold start test passed
- [ ] CUDA environment variables verified
- [ ] ComfyUI starts automatically (if configured)
- [ ] TTS generation tested
- [ ] Logs reviewed for errors
- [ ] CLAUDE.md updated
- [ ] SSH config documented

---

## Maintenance Notes

### Monthly Check
1. Verify PyTorch version is current
2. Check RunPod for template updates
3. Review logs for recurring issues

### After RunPod Updates
1. Re-verify CUDA works after RunPod infrastructure updates
2. Check if environment variables persisted
3. Update scripts if base image changed

---

## References

- Phase 1: `/dev/agents/artifacts/doc/plan/runpod-cuda-fix-pre/phase-1.md`
- Phase 2: `/dev/agents/artifacts/doc/plan/runpod-cuda-fix-pre/phase-2.md`
- Research: `/dev/agents/artifacts/doc/plan/runpod-cuda-fix-pre/research-*.md`
- RunPod API: `/dev/agents/artifacts/doc/runpod-api/api-reference.md`
