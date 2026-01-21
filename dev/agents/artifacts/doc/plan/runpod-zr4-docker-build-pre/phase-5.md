## Phase 5: Local Docker Build

### Steps
| Step | File:Line | Action | Parallel With |
|------|-----------|--------|---------------|
| 1 | docker/docker-compose.yml:69-89 | Execute docker compose build | - |
| 2 | N/A | Monitor build progress and errors | - |
| 3 | N/A | Monitor disk space usage | - |
| 4 | N/A | Verify image creation | - |
| 5 | N/A | Check image size | - |

### Detailed Implementation

**Step 1: Execute Docker Compose Build**
```bash
# Build with no cache for clean build
cd docker
docker compose build --no-cache > ../build-phase5.log 2>&1 &
BUILD_PID=$!
echo "Build started with PID: $BUILD_PID"
```

**Step 2: Monitor Build Progress**
```bash
# Tail build log for errors
tail -f ../build-phase5.log | grep -E "error|ERROR|failed|FAILED|Successfully built" --color=auto

# Check progress every 10 minutes
for i in {1..10}; do
    sleep 600  # 10 minutes
    if ps -p $BUILD_PID > /dev/null; then
        echo "Build still running ($((i * 10)) minutes)..."
        # Check last 20 lines for context
        tail -20 ../build-phase5.log
    else
        echo "Build completed"
        break
    fi
done
```

**Step 3: Monitor Disk Space**
```bash
# Check disk usage every 5 minutes
for i in {1..20}; do
    sleep 300  # 5 minutes
    DISK_USAGE=$(df /var/lib/docker | tail -1 | awk '{print $5}' | tr -d '%')
    echo "Disk usage: ${DISK_USAGE}%"
    
    if [ "$DISK_USAGE" -gt 80 ]; then
        echo "WARNING: Disk usage > 80%"
        echo "Consider cleaning Docker cache"
        docker system df
    fi
done
```

**Step 4: Verify Image Creation**
```bash
# Check if image was built
docker images | grep steadydancer

# Check for specific tags
docker images | grep -E "steadydancer|comfyui" | awk '{print $1, $2, $3, $NF}'
```

**Step 5: Check Image Size**
```bash
# Get image size
IMAGE_SIZE=$(docker images | grep steadydancer | awk '{print $NF, $2}' | grep -v "<none>" | head -1)

echo "=== Image Size ==="
docker images | grep steadydancer | grep -v "<none>" | awk '{print $1, ":", $2, "("$5" "$6")"}'

# Expected: < 50GB for SteadyDancer fp8 variant
if echo "$IMAGE_SIZE" | awk '{print $2}' | grep -q "GB"; then
    SIZE_NUM=$(echo "$IMAGE_SIZE" | awk '{print $2}' | tr -d 'GB')
    if [ "$SIZE_NUM" -lt 50 ]; then
        echo "✓ Image size acceptable (< 50GB)"
    else
        echo "⚠ Image size large (${SIZE_NUM}GB)"
    fi
fi
```

### Verification
```bash
# Complete verification
bash -c '
echo "=== Phase 5 Verification ==="
docker images | grep steadydancer | grep -v "<none>" | head -1
docker images | grep steadydancer | grep -v "<none>" | awk "{print \"Size: \"\$5\" \"\$6}"
echo ""
echo "=== Ready for Phase 6 ==="
'
```

### Rollback Instructions
If build fails:
```bash
# Revert to previous image
docker tag previous-steadydancer:stable steadydancer:latest 2>/dev/null || true

# Or use backup Dockerfile
cp docker/Dockerfile.backup docker/Dockerfile
docker build -t steadydancer:fallback -f docker/Dockerfile .
```
