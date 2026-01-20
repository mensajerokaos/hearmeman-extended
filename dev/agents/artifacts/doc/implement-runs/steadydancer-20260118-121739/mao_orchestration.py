#!/usr/bin/env python3
"""
MAO Orchestration for SteadyDancer Integration PRD Implementation
Executes WAVE 1 agents in parallel, then WAVE 2 agents
"""

import subprocess
import json
import os
from datetime import datetime
from pathlib import Path

# Configuration
OUTPUT_DIR = Path("/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/implement-runs/steadydancer-20260118-121739")
PRD_PATH = Path("/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/steadydancer-integration.md")
WORKING_DIR = Path("/home/oz/projects/2025/oz/12/runpod")

def read_prd_section(start_line, end_line):
    """Read specific line range from PRD"""
    with open(PRD_PATH, 'r') as f:
        lines = f.readlines()
        return ''.join(lines[start_line-1:end_line])

def execute_ma_task(task_name, task_prompt, output_file):
    """Execute a MiniMax Agent task"""
    print(f"\n{'='*60}")
    print(f"EXECUTING: {task_name}")
    print(f"{'='*60}")

    # Create task input
    task_input = {
        "task": task_name,
        "prompt": task_prompt,
        "output_file": str(output_file),
        "working_dir": str(WORKING_DIR)
    }

    # Execute via ma command
    cmd = [
        "ma", "execute",
        "--input", json.dumps(task_input),
        "--output", str(output_file),
        "--model", "haiku"  # Use Haiku for fast execution
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        print(f"Status: {'SUCCESS' if result.returncode == 0 else 'FAILED'}")
        if result.stdout:
            print(f"Output: {result.stdout[:200]}...")
        if result.stderr:
            print(f"Stderr: {result.stderr[:200]}...")
        return result.returncode == 0
    except Exception as e:
        print(f"Error executing task: {e}")
        return False

# WAVE 1: Parallel execution
print("\n" + "="*80)
print("MAO ORCHESTRATION: WAVE 1 (Parallel Execution)")
print("="*80)

wave1_tasks = {
    "1A-dockerfile": {
        "prompt": f"""
Execute AGENT 1A: Dockerfile Updates for SteadyDancer Integration

PRD REFERENCE: Lines 321-370, 1389-1417, 1405-1416
TARGET FILE: /home/oz/projects/2025/oz/12/runpod/docker/Dockerfile
TARGET LINES: 148-177, 181, 201, 204-250

CHANGES REQUIRED:
1. Add PyTorch 2.5.1 pinning (lines 339-342):
   - torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 (cu124)

2. Add pose estimation dependencies (lines 344-350):
   - mmengine, mmcv==2.1.0, mmdet>=3.1.0, mmpose, dwpose>=0.1.0

3. Enable flash_attn (line 353-354):
   - flash_attn==2.7.4.post1 with fallback

4. Update model directories (line 368):
   - Add 'steadydancer' directory

5. Add build ARGs (lines 595-598):
   - ARG BAKE_STEADYDANCER=false
   - ARG STEADYDANCER_VARIANT=fp8
   - ARG BAKE_TURBO=false

6. Add build-time download (lines 604-629):
   - Conditional download based on BAKE_STEADYDANCER/BAKE_TURBO

OUTPUT FILE: {OUTPUT_DIR}/agent-1A-dockerfile.md

FORMAT YOUR OUTPUT AS:
```markdown
# Agent 1A: Dockerfile Updates
## Changes Summary
- List of all changes made

## Detailed Changes

### Change 1: [Description]
**Location**: Line X
**Before**:
```dockerfile
[original code]
```
**After**:
```dockerfile
[new code]
```

## Verification
```bash
# Command to verify syntax
docker build --check -t test .
```
```
""",
        "output": OUTPUT_DIR / "agent-1A-dockerfile.md"
    },

    "1B-download": {
        "prompt": f"""
Execute AGENT 1B: Download Script v2 for SteadyDancer Integration

PRD REFERENCE: Lines 371-479, 1454-1488
TARGET FILE: /home/oz/projects/2025/oz/12/runpod/docker/download_models.sh
TARGET LINES: 323-328, 389-461

CHANGES REQUIRED:
1. Replace existing SteadyDancer section (lines 389-461) with enhanced version:
   - Support fp8, fp16, GGUF variants via STEADYDANCER_VARIANT
   - fp8: kijai/SteadyDancer-14B-pruned (14GB)
   - fp16: MCG-NJU/SteadyDancer-14B (28GB)
   - GGUF: MCG-NJU/SteadyDancer-GGUF (7GB)

2. Add DWPose download section (NEW, ~2GB):
   - yzd-v/DWPose weights
   - ControlNet openpose model

3. Add TurboDiffusion section (lines 464-478):
   - kijai/wan-2.1-turbodiffusion (~14GB)

4. Add shared dependencies check:
   - UMT5-XXL text encoder (9.5GB)
   - CLIP Vision (1.4GB)
   - WAN VAE (335MB)

OUTPUT FILE: {OUTPUT_DIR}/agent-1B-download.md

FORMAT YOUR OUTPUT AS:
```markdown
# Agent 1B: Download Script Updates
## Changes Summary
- List of all changes

## Section 1: SteadyDancer Enhanced Download
**Lines**: 389-461
**Code**:
```bash
[complete bash code with fp8/fp16/GGUF support]
```

## Section 2: DWPose Download
**Lines**: NEW (after SteadyDancer)
**Code**:
```bash
[complete DWPose download section]
```

## Section 3: TurboDiffusion Download
**Lines**: 464-478
**Code**:
```bash
[complete TurboDiffusion download section]
```

## Verification
```bash
bash -n download_models.sh  # Syntax check
```
```
""",
        "output": OUTPUT_DIR / "agent-1B-download.md"
    },

    "1C-compose": {
        "prompt": f"""
Execute AGENT 1C: Docker Compose v2 for SteadyDancer Integration

PRD REFERENCE: Lines 481-499, 1419-1450
TARGET FILE: /home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml
TARGET LINES: 37-67

CHANGES REQUIRED:
Add the following environment variables after ENABLE_STORYMEM:

```yaml
# Tier 3: Datacenter GPU (48-80GB A100/H100)
- ENABLE_INFCAM=false

# SteadyDancer (Dance Video Generation)
- ENABLE_STEADYDANCER=false
- STEADYDANCER_VARIANT=fp8
- STEADYDANCER_GUIDE_SCALE=5.0
- STEADYDANCER_CONDITION_GUIDE=1.0
- STEADYDANCER_END_CFG=0.4
- STEADYDANCER_SEED=106060

# DWPose (Pose Extraction)
- ENABLE_DWPOSE=false
- DWPOSE_DETECT_HAND=true
- DWPOSE_DETECT_BODY=true
- DWPOSE_DETECT_FACE=true
- DWPOSE_RESOLUTION=512

# TurboDiffusion (100-200x acceleration)
- ENABLE_WAN22_DISTILL=false
- TURBO_STEPS=4
- TURBO_GUIDE_SCALE=5.0
- TURBO_CONDITION_GUIDE=1.0
- TURBO_END_CFG=0.4
```

OUTPUT FILE: {OUTPUT_DIR}/agent-1C-compose.md

FORMAT YOUR OUTPUT AS:
```markdown
# Agent 1C: Docker Compose Updates
## Changes Summary
- List of all env vars added

## Environment Variables Added
**Location**: After ENABLE_STORYMEM (~line 55)
**Code**:
```yaml
[complete YAML block]
```

## Verification
```bash
docker compose config  # Validate YAML syntax
```
```
""",
        "output": OUTPUT_DIR / "agent-1C-compose.md"
    }
}

# Execute WAVE 1 in parallel
wave1_results = {}
print(f"\nExecuting {len(wave1_tasks)} tasks in parallel...")

for task_name, task_config in wave1_tasks.items():
    result = execute_ma_task(
        task_name,
        task_config["prompt"],
        task_config["output"]
    )
    wave1_results[task_name] = result
    print(f"  {task_name}: {'SUCCESS' if result else 'FAILED'}")

# Check WAVE 1 completion
wave1_success = all(wave1_results.values())
print(f"\nWAVE 1 COMPLETE: {'All agents succeeded' if wave1_success else 'Some agents failed'}")

if not wave1_success:
    print("\nFailed tasks:")
    for task, success in wave1_results.items():
        if not success:
            print(f"  - {task}")
    exit(1)

print("\n" + "="*80)
print("MAO ORCHESTRATION: WAVE 2 (After WAVE 1 Complete)")
print("="*80)
print("WAVE 2 tasks pending execution...")
print("They depend on WAVE 1 file changes being applied")

# Create MAO report for WAVE 1
report = f"""# SteadyDancer Integration - MAO Implementation Report

## Execution Summary

**Date**: {datetime.now().isoformat()}
**Output Directory**: {OUTPUT_DIR}
**PRD**: {PRD_PATH}

## WAVE 1: Completed

| Agent | Task | Status |
|-------|------|--------|
| 1A | Dockerfile Updates | {'✅ SUCCESS' if wave1_results.get('1A-dockerfile') else '❌ FAILED'} |
| 1B | Download Script v2 | {'✅ SUCCESS' if wave1_results.get('1B-download') else '❌ FAILED'} |
| 1C | Docker Compose v2 | {'✅ SUCCESS' if wave1_results.get('1C-compose') else '❌ FAILED'} |

## WAVE 2: Pending

WAVE 2 agents depend on WAVE 1 file changes:

- **Agent 2A**: Workflow Creation (depends on Dockerfile, Download Script)
- **Agent 2B**: Build-time Download (depends on Dockerfile)
- **Agent 2C**: Documentation Update (depends on all WAVE 1 outputs)

## Next Steps

1. Apply WAVE 1 file changes to actual source files
2. Execute WAVE 2 agents sequentially
3. Verify all changes
4. Generate final implementation report
"""

with open(OUTPUT_DIR / "wave1-complete.md", "w") as f:
    f.write(report)

print(f"\nWAVE 1 report saved to: {OUTPUT_DIR}/wave1-complete.md")
print("\n" + "="*80)
EOF
