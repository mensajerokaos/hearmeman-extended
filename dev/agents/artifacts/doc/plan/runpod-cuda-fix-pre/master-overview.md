---
task: RunPod CUDA Cold Start Fix
created: 2025-12-23T22:50:00Z
phases: 3
author: oz
model: claude-opus-4-5-20251101
---

# Master Plan: RunPod CUDA Initialization Fix

## Executive Summary

Fix persistent CUDA initialization failures on RunPod pod cold starts affecting the VibeVoice TTS pod (`k02604uwhjq6dm`). The pod uses an RTX A6000 GPU (48GB VRAM) for voice cloning with ComfyUI and VibeVoice.

**Target**: Automatic, reliable CUDA initialization on every cold start without manual intervention.

---

## Root Cause Analysis

Based on research findings, the CUDA initialization failures have **three root causes**:

### 1. GPU Device Index Mismatch (Primary)
- **Symptom**: `/dev/nvidia8` exists, `/dev/nvidia0` doesn't
- **Cause**: RunPod multi-GPU hosts assign the original device index, not 0
- **Impact**: PyTorch expects device 0, can't find it
- **Fix**: Set `CUDA_VISIBLE_DEVICES=0` to remap visible GPU to index 0

### 2. Cold Start Race Condition (Secondary)
- **Symptom**: First task fails, subsequent tasks succeed
- **Cause**: GPU driver not fully initialized when first CUDA call made
- **Impact**: `cuInit()` returns error code 3 (NOT_INITIALIZED)
- **Fix**: Add retry loop with delay before CUDA initialization

### 3. Device Ordering Inconsistency (Contributing)
- **Symptom**: nvidia-smi and CUDA show different device orders
- **Cause**: nvidia-smi uses "fastest first", CUDA uses PCI Bus ID
- **Impact**: Inconsistent GPU selection
- **Fix**: Set `CUDA_DEVICE_ORDER=PCI_BUS_ID`

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Pod Cold Start Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   Pod Start                                                       │
│       ↓                                                          │
│   Container boots (RunPod base image)                            │
│       ↓                                                          │
│   /workspace mounts (Network Volume - persistent)                │
│       ↓                                                          │
│   ┌────────────────────────────────────────────────────┐         │
│   │ NEW: /workspace/cuda_init.sh (auto-run)            │         │
│   │                                                     │         │
│   │ 1. Set CUDA_VISIBLE_DEVICES=0                      │         │
│   │ 2. Set CUDA_DEVICE_ORDER=PCI_BUS_ID                │         │
│   │ 3. Wait for nvidia-smi (retry loop)                │         │
│   │ 4. Warmup CUDA (torch.zeros(1).cuda())             │         │
│   │ 5. Start ComfyUI                                   │         │
│   └────────────────────────────────────────────────────┘         │
│       ↓                                                          │
│   ComfyUI ready with CUDA working                                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase Summary

| Phase | Name | Duration | Goal |
|-------|------|----------|------|
| **1** | Startup Script Fix | 15 min | Create CUDA initialization script |
| **2** | Pod Template Config | 10 min | Auto-run script on cold start |
| **3** | Validation & Monitoring | 20 min | Test and document |

**Total estimated time**: 45 minutes

---

## Phase 1: Startup Script Fix

### Goal
Create a robust startup script that handles CUDA initialization before ComfyUI starts.

### Deliverables
1. `/workspace/cuda_init.sh` - CUDA environment setup + GPU wait
2. `/workspace/start_comfyui.sh` - Updated to use cuda_init.sh
3. `/workspace/check_cuda.py` - Python script to verify CUDA

### Key Features
- Environment variable configuration
- Retry loop for GPU availability (10 attempts, 3s delay)
- CUDA warmup (tensor creation on GPU)
- Fallback error handling
- Logging for debugging

---

## Phase 2: Pod Template Configuration

### Goal
Configure RunPod pod template to auto-run startup script on cold boot.

### Deliverables
1. Updated pod environment variables
2. Container start command configuration
3. PyTorch version upgrade (optional)

### Options
- **Option A**: Set environment variables in pod template
- **Option B**: Custom entrypoint in container start command
- **Option C**: Both (recommended)

---

## Phase 3: Validation & Monitoring

### Goal
Verify fix works on cold start and document for future reference.

### Deliverables
1. Cold start test checklist
2. Monitoring commands
3. Troubleshooting guide
4. Updated CLAUDE.md documentation

### Test Cases
1. Stop pod → Start pod → Verify CUDA works
2. SSH in → Check logs → Verify no errors
3. Run TTS generation → Verify output quality

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Script doesn't auto-run | Medium | High | Test container start command format |
| Environment vars not applied | Low | High | Verify in SSH session after restart |
| PyTorch upgrade breaks deps | Low | Medium | Test in venv before upgrade |
| GPU still not detected | Low | High | Add UUID-based device selection fallback |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Cold start CUDA success rate | 100% |
| Time to first TTS generation | < 5 min after pod start |
| Manual intervention required | None |
| GPU detection on first attempt | Yes |

---

## Quick Reference Commands

### Test CUDA Manually
```bash
ssh runpod
source /workspace/venv/bin/activate
python3 -c "import torch; print(torch.cuda.is_available())"
```

### Check GPU Device
```bash
ls -la /dev/nvidia*
nvidia-smi -L
```

### View Startup Logs
```bash
cat /workspace/comfyui.log
```

### Restart ComfyUI
```bash
pkill -f "python.*main.py"
nohup /workspace/start_comfyui.sh > /workspace/comfyui.log 2>&1 &
```

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `/workspace/cuda_init.sh` | CREATE | CUDA environment setup |
| `/workspace/start_comfyui.sh` | MODIFY | Call cuda_init.sh |
| `/workspace/check_cuda.py` | CREATE | CUDA verification script |
| Pod template | MODIFY | Environment variables |
| `CLAUDE.md` | UPDATE | Document new startup process |

---

## Dependencies

- RunPod API access (for pod template modification)
- SSH access to pod
- Python 3.x with PyTorch in venv
- Network volume persistence

---

## Next Steps

1. Create Phase 1 detailed specification
2. Write and test startup script
3. Update pod template
4. Run cold start tests
5. Document results

---

*Master plan created: 2025-12-23*
*Pod ID: k02604uwhjq6dm*
