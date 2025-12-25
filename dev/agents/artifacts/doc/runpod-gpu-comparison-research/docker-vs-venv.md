---
task: Docker vs venv explanation for RunPod
agent: hc (headless claude)
model: claude-opus-4-5-20251101
timestamp: 2025-12-23T13:35:00Z
status: completed
---

# Docker vs venv on RunPod: A Practical Guide

## TL;DR

RunPod pods **are already Docker containers**. You don't "choose" Docker vs venv—you use venv *inside* the container to manage Python dependencies persistently.

## 1. RunPod IS Docker-Based

When you create a RunPod pod:
- You select a **Docker image** (e.g., `runpod/pytorch:2.1.0-py3.10-cuda11.8.0`)
- The pod runs as a **container** from that image
- Container storage is **ephemeral** by default (lost on stop/restart)

This is why understanding persistence matters.

## 2. Why Use venv Inside a Container?

| Reason | Explanation |
|--------|-------------|
| **Dependency isolation** | Avoid conflicts with base image packages |
| **Reproducibility** | Lock exact versions for your project |
| **Persistence** | Store venv on Network Volume, survives restarts |
| **Portability** | Same setup works across different base images |

Without venv, every pod restart means reinstalling your pip packages.

## 3. Best Practice: Network Volume + venv

```
┌─────────────────────────────────────────────────┐
│  RunPod Pod (Docker Container)                  │
│  ┌─────────────────────────────────────────┐   │
│  │  /workspace (Network Volume)            │   │
│  │  ├── venv/        ← Persistent venv     │   │
│  │  ├── models/      ← Cached models       │   │
│  │  └── projects/    ← Your code           │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  Container storage (ephemeral - lost on stop)  │
└─────────────────────────────────────────────────┘
```

**Network Volume** = persistent storage attached at `/workspace`

## 4. Setting Up Persistent venv

### First-time setup (create venv on network volume):

```bash
# Create venv on persistent storage
python -m venv /workspace/venv

# Activate it
source /workspace/venv/bin/activate

# Install your packages
pip install torch transformers diffusers accelerate

# Save requirements for reproducibility
pip freeze > /workspace/requirements.txt
```

### On pod restart (reuse existing venv):

```bash
# Just activate - packages are already there
source /workspace/venv/bin/activate

# Verify
which python  # Should show /workspace/venv/bin/python
```

## 5. Quick Setup Script

Save this as `/workspace/setup.sh`:

```bash
#!/bin/bash
VENV_PATH="/workspace/venv"

if [ -d "$VENV_PATH" ]; then
    echo "Activating existing venv..."
    source "$VENV_PATH/bin/activate"
else
    echo "Creating new venv..."
    python -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    pip install --upgrade pip

    # Install your base packages
    if [ -f "/workspace/requirements.txt" ]; then
        pip install -r /workspace/requirements.txt
    fi
fi

echo "Python: $(which python)"
echo "Pip packages: $(pip list | wc -l)"
```

Run on every pod start:
```bash
source /workspace/setup.sh
```

## Summary

| What | Where | Persists? |
|------|-------|-----------|
| Docker image | RunPod template | N/A (base) |
| Container storage | `/` (root) | ❌ No |
| Network Volume | `/workspace` | ✅ Yes |
| venv | `/workspace/venv` | ✅ Yes |
| Models | `/workspace/models` | ✅ Yes |

**Bottom line**: Always put anything you want to keep in `/workspace`.
