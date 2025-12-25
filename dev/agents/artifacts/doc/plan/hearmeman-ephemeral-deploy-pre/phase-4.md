---
author: oz
model: claude-opus-4-5
date: 2025-12-24 01:40
task: Phase 4 Verification - Detailed expansion for Hearmeman ephemeral deployment
---

# Phase 4: Verification

**Objective**: Confirm all components are operational before production use.

**Duration**: 10-15 minutes (including test generations)

**Prerequisites**:
- Phase 1-3 completed successfully
- SSH tunnel established: `ssh -L 8188:localhost:8188 runpod`

---

## 1. ComfyUI Health Check

### 1.1 Basic HTTP Health Check

```bash
# Test ComfyUI is responding
ssh runpod "curl -s localhost:8188 | head -c 100"
# Expected: HTML response with "ComfyUI" in content

# System stats endpoint (JSON)
ssh runpod "curl -s localhost:8188/system_stats"
# Expected: JSON with system info
```

### 1.2 System Stats Verification

```bash
# Parse system stats for key metrics
ssh runpod "curl -s localhost:8188/system_stats | python3 -c '
import sys, json
data = json.load(sys.stdin)
print(f\"VRAM Total: {data.get(\"devices\", [{}])[0].get(\"vram_total\", 0) / 1e9:.1f} GB\")
print(f\"VRAM Free: {data.get(\"devices\", [{}])[0].get(\"vram_free\", 0) / 1e9:.1f} GB\")
print(f\"Torch Version: {data.get(\"system\", {}).get(\"python_version\", \"unknown\")}\")
'"
```

**Expected Output**:
```
VRAM Total: 48.0 GB
VRAM Free: 45.0 GB (varies based on loaded models)
Torch Version: 3.10.x
```

### 1.3 API Endpoints Verification

| Endpoint | Method | Expected | Command |
|----------|--------|----------|---------|
| `/` | GET | HTML page | `curl -s localhost:8188 \| head -1` |
| `/system_stats` | GET | JSON object | `curl -s localhost:8188/system_stats` |
| `/prompt` | POST | prompt_id | `curl -X POST localhost:8188/prompt -d '{}'` |
| `/history` | GET | Empty object | `curl -s localhost:8188/history` |
| `/object_info` | GET | Node definitions | `curl -s localhost:8188/object_info \| head -c 500` |
| `/models` | GET | Model list | `curl -s localhost:8188/models/diffusion_models` |

---

## 2. Model Availability Verification

### 2.1 ComfyUI Manager Check

```bash
# Verify ComfyUI Manager is installed
ssh runpod "ls -la /workspace/ComfyUI/custom_nodes/ComfyUI-Manager"

# Check for installed custom nodes
ssh runpod "ls /workspace/ComfyUI/custom_nodes/"
```

**Expected Custom Nodes**:
```
ComfyUI-Manager/
VibeVoice-ComfyUI/        # or ComfyUI-VibeVoice/
ComfyUI-SCAIL-Pose/       # if SCAIL installed
ComfyUI-VideoHelperSuite/ # usually pre-installed
```

### 2.2 Model Files Verification

```bash
# WAN 2.2 models (Hearmeman template)
ssh runpod "ls -lh /workspace/ComfyUI/models/diffusion_models/ | grep -i wan"
# Expected: Multiple wan*.safetensors files (60-80GB total)

# Text encoders
ssh runpod "ls -lh /workspace/ComfyUI/models/clip/ 2>/dev/null || \
            ls -lh /workspace/ComfyUI/models/text_encoders/"
# Expected: umt5_xxl or similar (~15GB)

# VAE
ssh runpod "ls -lh /workspace/ComfyUI/models/vae/"
# Expected: wan_*.safetensors (~500MB)

# SteadyDancer (P1 model)
ssh runpod "ls -lh /workspace/ComfyUI/models/diffusion_models/Wan21_SteadyDancer*"
# Expected: Wan21_SteadyDancer_fp16.safetensors (~28GB)

# SCAIL (P2 optional)
ssh runpod "ls -lh /workspace/ComfyUI/models/diffusion_models/SCAIL-Preview/ 2>/dev/null"
# Expected: Multiple files (~28GB total)
```

### 2.3 Model Size Summary Script

```bash
ssh runpod "cat << 'EOF' | python3
import os
from pathlib import Path

models_dir = Path('/workspace/ComfyUI/models')
total = 0

for subdir in ['diffusion_models', 'clip', 'text_encoders', 'vae']:
    path = models_dir / subdir
    if path.exists():
        size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        size_gb = size / 1e9
        print(f'{subdir}: {size_gb:.1f} GB')
        total += size

print(f'\\nTotal: {total/1e9:.1f} GB')
EOF
"
```

**Expected Output**:
```
diffusion_models: 120.0 GB
clip: 0.0 GB
text_encoders: 15.0 GB
vae: 0.5 GB

Total: 135.5 GB
```

---

## 3. CUDA and GPU Verification

### 3.1 nvidia-smi Check

```bash
# Full GPU status
ssh runpod "nvidia-smi"

# Compact single-line status
ssh runpod "nvidia-smi --query-gpu=name,memory.total,memory.used,temperature.gpu,power.draw --format=csv,noheader"
# Expected: NVIDIA L40S, 48627MiB, <5000MiB, 45C, 75W
```

### 3.2 PyTorch CUDA Verification

```bash
ssh runpod "python3 -c '
import torch
print(f\"PyTorch Version: {torch.__version__}\")
print(f\"CUDA Available: {torch.cuda.is_available()}\")
print(f\"CUDA Version: {torch.version.cuda}\")
print(f\"cuDNN Version: {torch.backends.cudnn.version()}\")
print(f\"Device Count: {torch.cuda.device_count()}\")
if torch.cuda.is_available():
    print(f\"Current Device: {torch.cuda.current_device()}\")
    print(f\"Device Name: {torch.cuda.get_device_name(0)}\")
    print(f\"Device Capability: {torch.cuda.get_device_capability(0)}\")
    # Memory test
    t = torch.zeros(1000, 1000).cuda()
    print(f\"Memory Allocation Test: PASSED\")
'"
```

**Expected Output**:
```
PyTorch Version: 2.8.0+cu128
CUDA Available: True
CUDA Version: 12.8
cuDNN Version: 90100
Device Count: 1
Current Device: 0
Device Name: NVIDIA L40S
Device Capability: (8, 9)
Memory Allocation Test: PASSED
```

### 3.3 CUDA Environment Variables

```bash
ssh runpod "echo 'CUDA_VISIBLE_DEVICES:' \$CUDA_VISIBLE_DEVICES
echo 'NVIDIA_VISIBLE_DEVICES:' \$NVIDIA_VISIBLE_DEVICES
echo 'LD_LIBRARY_PATH:' \$LD_LIBRARY_PATH | tr ':' '\n' | grep -i cuda"
```

### 3.4 CUDA Error Recovery

If CUDA fails, run the initialization script:

```bash
# Method 1: Use cuda_init.sh if present
ssh runpod "/workspace/scripts/cuda_init.sh 2>/dev/null || echo 'Script not found'"

# Method 2: Manual CUDA warmup
ssh runpod "python3 -c '
import torch
import time

for i in range(5):
    try:
        torch.cuda.init()
        torch.zeros(1).cuda()
        print(f\"CUDA initialized successfully on attempt {i+1}\")
        break
    except Exception as e:
        print(f\"Attempt {i+1} failed: {e}\")
        time.sleep(2)
else:
    print(\"CUDA initialization failed after 5 attempts\")
'"
```

---

## 4. VibeVoice Test

### 4.1 Node Installation Verification

```bash
# Check node files
ssh runpod "ls -la /workspace/ComfyUI/custom_nodes/VibeVoice-ComfyUI/ 2>/dev/null || \
            ls -la /workspace/ComfyUI/custom_nodes/ComfyUI-VibeVoice/"

# Check TTS package
ssh runpod "pip show TTS | head -5"
```

### 4.2 Voice Reference Verification

```bash
# Check voice reference file
ssh runpod "ls -la /workspace/ComfyUI/input/es-JoseObscura_woman.mp3 2>/dev/null || \
            ls -la /workspace/ComfyUI/input/voices/es-JoseObscura_woman.mp3 2>/dev/null"
# Expected: File exists, ~500KB-5MB

# Verify audio format
ssh runpod "file /workspace/ComfyUI/input/es-JoseObscura_woman.mp3"
# Expected: Audio file (MPEG ADTS, layer III, ...)
```

### 4.3 Simple TTS Generation Test

**Via ComfyUI API** (from local machine with SSH tunnel active):

```bash
# Create test workflow JSON
cat > /tmp/vibevoice_test.json << 'EOF'
{
  "prompt": {
    "1": {
      "class_type": "LoadAudio",
      "inputs": {
        "audio": "es-JoseObscura_woman.mp3"
      }
    },
    "2": {
      "class_type": "VibeVoiceSingleSpeakerNode",
      "inputs": {
        "ref_audio": ["1", 0],
        "text": "Esta es una prueba de generacion de voz.",
        "model": "VibeVoice-Large",
        "diffusion_steps": 10,
        "cfg_scale": 1.3,
        "seed": 42
      }
    },
    "3": {
      "class_type": "PreviewAudio",
      "inputs": {
        "audio": ["2", 0]
      }
    }
  }
}
EOF

# Submit to ComfyUI
curl -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d @/tmp/vibevoice_test.json

# Check history for completion
sleep 30
curl -s http://localhost:8188/history | python3 -c "
import sys, json
data = json.load(sys.stdin)
for pid, info in data.items():
    status = info.get('status', {})
    if status.get('completed', False):
        print(f'Prompt {pid}: COMPLETED')
    elif status.get('status_str'):
        print(f'Prompt {pid}: {status[\"status_str\"]}')
"
```

### 4.4 TTS Output Verification

```bash
# Check for generated audio
ssh runpod "ls -la /workspace/ComfyUI/output/*.wav 2>/dev/null | tail -5"

# Verify audio properties
ssh runpod "ffprobe -v quiet -print_format json -show_format -show_streams \
            /workspace/ComfyUI/output/tts_*.wav 2>/dev/null | head -30"
```

**Expected TTS Output Properties**:
- Format: WAV (PCM)
- Sample Rate: 24000 Hz
- Channels: 1 (mono)
- Duration: ~2-5 seconds for test phrase

---

## 5. WAN 2.2 720p Test Workflow

### 5.1 Model Loading Test

```bash
# Via API - test if WAN model loads
cat > /tmp/wan_test.json << 'EOF'
{
  "prompt": {
    "1": {
      "class_type": "WanVideoModelLoader",
      "inputs": {
        "model": "wan2.2_t2v_14B_fp8_scaled.safetensors",
        "precision": "fp8_e4m3fn"
      }
    }
  }
}
EOF

curl -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d @/tmp/wan_test.json
```

### 5.2 Simple T2V Generation Test

```bash
# Full T2V workflow test (via browser recommended)
# Navigate to: http://localhost:8188

# Or via API with minimal parameters
cat > /tmp/wan_t2v_test.json << 'EOF'
{
  "prompt": {
    "1": {
      "class_type": "WanVideoModelLoader",
      "inputs": {
        "model": "wan2.2_t2v_14B_fp8_scaled.safetensors",
        "precision": "fp8_e4m3fn"
      }
    },
    "2": {
      "class_type": "WanTextEncode",
      "inputs": {
        "text": "A woman walking through a colorful textile market",
        "model": ["1", 0]
      }
    },
    "3": {
      "class_type": "WanVideoSampler",
      "inputs": {
        "model": ["1", 0],
        "positive": ["2", 0],
        "width": 480,
        "height": 272,
        "frames": 17,
        "steps": 20,
        "cfg": 7.0,
        "seed": 42
      }
    },
    "4": {
      "class_type": "WanVideoDecode",
      "inputs": {
        "samples": ["3", 0],
        "model": ["1", 0]
      }
    },
    "5": {
      "class_type": "SaveVideo",
      "inputs": {
        "video": ["4", 0],
        "filename_prefix": "wan_test"
      }
    }
  }
}
EOF
```

### 5.3 WAN Generation Benchmarks

| Resolution | Frames | Expected Time | VRAM Usage |
|------------|--------|---------------|------------|
| 480x272 | 17 | 30-45s | ~18GB |
| 720x480 | 17 | 60-90s | ~28GB |
| 720x480 | 33 | 90-150s | ~32GB |
| 720x480 | 65 | 180-300s | ~40GB |

---

## 6. SteadyDancer Test (if installed)

### 6.1 Model Verification

```bash
# Verify SteadyDancer model
ssh runpod "ls -lh /workspace/ComfyUI/models/diffusion_models/Wan21_SteadyDancer_fp16.safetensors"
# Expected: ~28GB file
```

### 6.2 SteadyDancer Workflow Test

Load existing workflow if available:

```bash
# Check for SteadyDancer workflow
ssh runpod "ls /workspace/ComfyUI/user/default/workflows/*SteadyDancer* 2>/dev/null || \
            ls /workspace/ComfyUI/user/default/workflows/*steadydancer* 2>/dev/null"
```

**Browser Test**:
1. Open http://localhost:8188
2. Load `wanvideo_SteadyDancer_example_03oz.json`
3. Add reference dance video to input
4. Queue generation
5. Expected: ~3-5 minutes for 17 frames

### 6.3 SteadyDancer Benchmarks

| Input | Frames | Expected Time | VRAM Usage |
|-------|--------|---------------|------------|
| 5s dance video | 17 | 120-180s | ~35GB |
| 10s dance video | 33 | 240-360s | ~42GB |

---

## 7. Browser-Based UI Testing Checklist

### 7.1 Initial Load

```markdown
[ ] Navigate to http://localhost:8188
[ ] ComfyUI interface loads (< 5 seconds)
[ ] Node graph canvas visible
[ ] Sidebar with node categories visible
[ ] Queue panel visible (top-right)
```

### 7.2 Manager Verification

```markdown
[ ] Click "Manager" button (or Ctrl+Shift+M)
[ ] Manager popup appears
[ ] "Install Custom Nodes" tab accessible
[ ] Search for "VibeVoice" - should show installed
[ ] "Install Models" tab accessible
[ ] Close Manager
```

### 7.3 Node Availability

Test adding these nodes (double-click canvas → search):

```markdown
[ ] LoadAudio - found
[ ] VibeVoiceSingleSpeakerNode - found
[ ] WanVideoModelLoader - found
[ ] WanVideoSampler - found
[ ] SaveVideo - found
[ ] PreviewAudio - found
```

### 7.4 Workflow Load Test

```markdown
[ ] Click "Load" button
[ ] Navigate to workflows folder
[ ] Load tts-oz-vibevoice-api.json
[ ] All nodes render correctly (no red/error nodes)
[ ] Connections intact
```

### 7.5 Input Files Access

```markdown
[ ] Add LoadAudio node
[ ] Click "audio" dropdown
[ ] es-JoseObscura_woman.mp3 appears in list
[ ] Select file successfully
```

### 7.6 Generation Test

```markdown
[ ] Load TTS workflow
[ ] Enter test text: "Esta es una prueba."
[ ] Click "Queue Prompt" (or Ctrl+Enter)
[ ] Progress bar shows in queue
[ ] Generation completes without errors
[ ] Audio preview plays
[ ] Output file saved
```

---

## 8. Performance Benchmarks to Record

### 8.1 Benchmark Template

Record these metrics for future reference:

```
Date: YYYY-MM-DD
Pod Type: [L40S / A6000 / A40]
Template Version: Hearmeman 758dsjwiqz

=== System ===
GPU: [nvidia-smi output]
VRAM Total: XX GB
PyTorch: X.X.X
CUDA: 12.8

=== Model Load Times ===
WAN 2.2 T2V: XX seconds
VibeVoice-Large: XX seconds
SteadyDancer: XX seconds

=== Generation Benchmarks ===
TTS (10 words): XX seconds
TTS (50 words): XX seconds
WAN 480x272 17f: XX seconds
WAN 720x480 17f: XX seconds
SteadyDancer 17f: XX seconds

=== VRAM Usage ===
Idle: XX GB
TTS Generation: XX GB
WAN 720p: XX GB
SteadyDancer: XX GB
```

### 8.2 Quick Benchmark Script

```bash
ssh runpod "cat << 'EOF' | python3
import time
import torch

print('=== GPU Benchmark ===')

# Memory bandwidth test
start = time.time()
for _ in range(100):
    x = torch.randn(1000, 1000, device='cuda')
    y = x @ x
    torch.cuda.synchronize()
mem_time = time.time() - start
print(f'MatMul 100x (1000x1000): {mem_time:.2f}s')

# Large allocation
start = time.time()
x = torch.randn(10000, 10000, device='cuda')
torch.cuda.synchronize()
alloc_time = time.time() - start
print(f'Allocate 400MB tensor: {alloc_time:.3f}s')

# Memory stats
allocated = torch.cuda.memory_allocated() / 1e9
reserved = torch.cuda.memory_reserved() / 1e9
print(f'Memory Allocated: {allocated:.2f} GB')
print(f'Memory Reserved: {reserved:.2f} GB')
EOF
"
```

---

## 9. Success Criteria and Sign-Off Checklist

### 9.1 Critical (Must Pass)

```markdown
[ ] GPU detected with 48GB VRAM
[ ] CUDA initialized successfully
[ ] ComfyUI accessible at localhost:8188
[ ] WAN 2.2 models present (>60GB in diffusion_models)
[ ] VibeVoice node available in ComfyUI
[ ] Voice reference file uploaded and accessible
[ ] TTS test generation completes successfully
```

### 9.2 Important (Should Pass)

```markdown
[ ] SteadyDancer model downloaded (~28GB)
[ ] All custom nodes show in Manager
[ ] Workflow loads without errors
[ ] Audio output plays in browser preview
[ ] Video output saves correctly
```

### 9.3 Optional (Nice to Have)

```markdown
[ ] SCAIL model installed
[ ] Custom workflows synced
[ ] API generation tested
[ ] Benchmarks recorded
```

### 9.4 Sign-Off Template

```
=== Hearmeman Ephemeral Deployment Sign-Off ===

Date: YYYY-MM-DD
Operator: [name]
Pod ID: [runpod_pod_id]
GPU: [L40S / A6000]

Phase 1 - Template Deploy: [ ] PASS / [ ] FAIL
Phase 2 - SSH Setup: [ ] PASS / [ ] FAIL
Phase 3 - Model Install: [ ] PASS / [ ] FAIL
Phase 4 - Verification: [ ] PASS / [ ] FAIL

Critical Checks (9/9 required):
[ ] GPU 48GB VRAM
[ ] CUDA OK
[ ] ComfyUI HTTP OK
[ ] WAN models OK
[ ] VibeVoice node OK
[ ] Voice reference OK
[ ] TTS test OK
[ ] Text encoder OK
[ ] VAE OK

Notes:
_________________________________________________
_________________________________________________

Ready for Production: [ ] YES / [ ] NO

Signed: _________________ Date: _________
```

---

## 10. Common Issues and Resolution

### 10.1 ComfyUI Not Responding

**Symptom**: `curl localhost:8188` hangs or connection refused

**Resolution**:
```bash
# Check if ComfyUI process is running
ssh runpod "ps aux | grep python | grep main.py"

# Check logs
ssh runpod "tail -100 /workspace/comfyui.log"

# Restart ComfyUI
ssh runpod "pkill -f 'python.*main.py' 2>/dev/null; \
            nohup python /workspace/ComfyUI/main.py --listen 0.0.0.0 > /workspace/comfyui.log 2>&1 &"

# Wait and test
sleep 10
ssh runpod "curl -s localhost:8188/system_stats | head -c 50"
```

### 10.2 CUDA Not Available

**Symptom**: `torch.cuda.is_available()` returns False

**Resolution**:
```bash
# Check NVIDIA driver
ssh runpod "nvidia-smi"

# If nvidia-smi works but CUDA fails, reinitialize
ssh runpod "python3 -c '
import torch
torch.cuda.init()
print(torch.cuda.is_available())
'"

# If still failing, restart pod from console
```

### 10.3 Model Not Found in ComfyUI

**Symptom**: Model dropdown empty or model missing

**Resolution**:
```bash
# Check model paths
ssh runpod "ls -la /workspace/ComfyUI/models/diffusion_models/"

# Refresh ComfyUI models (via Manager or restart)
ssh runpod "curl -X POST localhost:8188/api/refresh"

# Verify model file integrity
ssh runpod "head -c 1000 /workspace/ComfyUI/models/diffusion_models/wan*.safetensors | file -"
```

### 10.4 VibeVoice Node Not Found

**Symptom**: Cannot find VibeVoiceSingleSpeakerNode

**Resolution**:
```bash
# Check custom node installation
ssh runpod "ls /workspace/ComfyUI/custom_nodes/ | grep -i vibe"

# Install/reinstall
ssh runpod "cd /workspace/ComfyUI/custom_nodes && \
            rm -rf VibeVoice-ComfyUI ComfyUI-VibeVoice && \
            git clone https://github.com/AIFSH/VibeVoice-ComfyUI && \
            cd VibeVoice-ComfyUI && \
            pip install -r requirements.txt"

# Restart ComfyUI
ssh runpod "pkill -f 'python.*main.py'; \
            nohup python /workspace/ComfyUI/main.py --listen 0.0.0.0 > /workspace/comfyui.log 2>&1 &"
```

### 10.5 Voice Reference Not Playing

**Symptom**: TTS fails with audio file error

**Resolution**:
```bash
# Verify file exists and is valid
ssh runpod "file /workspace/ComfyUI/input/es-JoseObscura_woman.mp3"

# Check file permissions
ssh runpod "chmod 644 /workspace/ComfyUI/input/*.mp3"

# Convert to standard format if needed
ssh runpod "ffmpeg -i /workspace/ComfyUI/input/es-JoseObscura_woman.mp3 \
            -ar 24000 -ac 1 \
            /workspace/ComfyUI/input/es-JoseObscura_woman_converted.mp3"
```

### 10.6 Out of VRAM

**Symptom**: CUDA out of memory error

**Resolution**:
```bash
# Check VRAM usage
ssh runpod "nvidia-smi"

# Clear VRAM cache
ssh runpod "python3 -c 'import torch; torch.cuda.empty_cache()'"

# Kill any orphan processes
ssh runpod "pkill -f 'python.*main.py'"
ssh runpod "nvidia-smi --gpu-reset"  # WARNING: Kills all GPU processes

# Use FP8 precision for WAN (if available)
# In workflow, change precision to "fp8_e4m3fn"
```

### 10.7 SSH Tunnel Not Working

**Symptom**: localhost:8188 not accessible in browser

**Resolution**:
```bash
# Check if tunnel is established
lsof -i :8188

# Kill existing tunnel and recreate
pkill -f 'ssh.*8188:localhost:8188'
ssh -fNL 8188:localhost:8188 runpod

# Verify tunnel
curl -s localhost:8188 | head -c 50
```

### 10.8 Model Download Incomplete

**Symptom**: Model files corrupt or too small

**Resolution**:
```bash
# Check file sizes
ssh runpod "ls -lh /workspace/ComfyUI/models/diffusion_models/*.safetensors"

# Re-download with resume
ssh runpod "cd /workspace/ComfyUI/models/diffusion_models && \
            wget -c https://huggingface.co/[model_path]/resolve/main/[model_file]"

# For git LFS files
ssh runpod "cd /workspace/ComfyUI/models/diffusion_models/SCAIL-Preview && \
            git lfs pull"
```

---

## Quick Health Check Script

Save this as `/workspace/health_check.sh`:

```bash
#!/bin/bash
# Comprehensive health check for Hearmeman ephemeral deployment

echo "=========================================="
echo "  Hearmeman Pod Health Check"
echo "  $(date)"
echo "=========================================="
echo

# 1. GPU
echo "=== GPU Status ==="
nvidia-smi --query-gpu=name,memory.total,memory.free,temperature.gpu --format=csv,noheader

# 2. CUDA
echo -e "\n=== CUDA Status ==="
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"

# 3. Disk
echo -e "\n=== Disk Status ==="
df -h /workspace | tail -1

# 4. ComfyUI
echo -e "\n=== ComfyUI Status ==="
if curl -s localhost:8188/system_stats > /dev/null 2>&1; then
    echo "ComfyUI: RUNNING"
    curl -s localhost:8188/system_stats | python3 -c "
import sys, json
data = json.load(sys.stdin)
devs = data.get('devices', [{}])
if devs:
    vram = devs[0].get('vram_free', 0) / 1e9
    print(f'VRAM Free: {vram:.1f} GB')
"
else
    echo "ComfyUI: NOT RUNNING"
fi

# 5. Models
echo -e "\n=== Installed Models ==="
echo "Diffusion models:"
ls /workspace/ComfyUI/models/diffusion_models/*.safetensors 2>/dev/null | wc -l
echo "files"

echo "Custom nodes:"
ls /workspace/ComfyUI/custom_nodes/ 2>/dev/null | grep -v __pycache__ | wc -l
echo "nodes"

# 6. Voice reference
echo -e "\n=== Voice Reference ==="
if ls /workspace/ComfyUI/input/es-JoseObscura*.mp3 2>/dev/null; then
    echo "Voice file: FOUND"
else
    echo "Voice file: NOT FOUND"
fi

echo -e "\n=========================================="
echo "  Health check complete"
echo "=========================================="
```

---

*Document generated: 2025-12-24*
*Project: José Obscura - La Maquila Erótica Documentary*
