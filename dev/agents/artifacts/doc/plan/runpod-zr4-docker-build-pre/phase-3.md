## Phase 3: Dependency Installation

### Steps
| Step | File:Line | Action | Parallel With |
|------|-----------|--------|---------------|
| 1 | docker/Dockerfile:180-220 | Build with SteadyDancer dependencies | P4 |
| 2 | N/A | Monitor Flash-attn installation | P4 |
| 3 | N/A | Check for xformers fallback | P4 |
| 4 | N/A | Verify Python packages | P4 |
| 5 | N/A | Test import chain | P4 |

### Detailed Implementation

**Step 1: Build with Dependencies**
```bash
# Build with SteadyDancer dependencies
cd docker
docker build \
  --build-arg BAKE_STEADYDANCER=true \
  --build-arg STEADYDANCER_VARIANT=fp8 \
  -t steadydancer:test \
  -f Dockerfile \
  . > ../build-phase3.log 2>&1 &

BUILD_PID=$!
echo "Build started with PID: $BUILD_PID"
```

**Step 2: Monitor Installation**
```bash
# Monitor build progress
tail -f ../build-phase3.log | grep -E "Installing|Collecting|Successfully|error|ERROR" --color=auto

# Check every 5 minutes
sleep 300
if ps -p $BUILD_PID > /dev/null; then
    echo "Build still running after 5 minutes..."
else
    echo "Build completed"
fi
```

**Step 3: Check Flash-attn Installation**
```bash
# Check if Flash-attn was built
grep -i "flash-attn" ../build-phase3.log

# If Flash-attn failed, check for xformers
grep -i "xformers" ../build-phase3.log

# Expected: Either Flash-attn success OR xformers fallback
```

**Step 4: Verify Python Packages**
```bash
# Get container ID
CONTAINER_ID=$(docker ps -q --filter "ancestry=steadydancer:test" | head -1)

if [ -n "$CONTAINER_ID" ]; then
    # Test package imports
    docker exec $CONTAINER_ID python -c "
import mmengine
import mmcv
import mmdet
import mmpose
import dwpose
import torch
print('All packages imported successfully')
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.version.cuda}')
"
else
    echo "Container not found"
fi
```

**Step 5: Test Import Chain**
```bash
# Test SteadyDancer imports
CONTAINER_ID=$(docker ps -q --filter "ancestry=steadydancer:test" | head -1)

docker exec $CONTAINER_ID python -c "
try:
    import steady_dancer
    print('SteadyDancer imported OK')
except ImportError as e:
    echo "Import error: $e"
"
```

### Verification
```bash
# Complete verification
bash -c '
CONTAINER_ID=$(docker ps -q --filter "ancestry=steadydancer:test" | head -1)
if [ -n "$CONTAINER_ID" ]; then
    docker exec $CONTAINER_ID python -c "import mmcv, mmpose; print(\"✓ Dependencies OK\")"
else
    echo "✗ Container not found"
    exit 1
fi
'
```

### Parallel Execution
Phase 3 runs in parallel with Phase 4 (Model Configuration) as they modify different files.
