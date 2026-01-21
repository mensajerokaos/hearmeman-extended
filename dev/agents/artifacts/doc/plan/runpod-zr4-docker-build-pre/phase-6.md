## Phase 6: Local Testing

### Steps
| Step | File:Line | Action | Parallel With |
|------|-----------|--------|---------------|
| 1 | docker-compose.yml | Start Docker containers | - |
| 2 | N/A | Wait for ComfyUI initialization | - |
| 3 | N/A | Verify ComfyUI web interface | - |
| 4 | docker/workflows/steadydancer-dance.json | Load and validate workflow | - |
| 5 | N/A | Generate test video | - |
| 6 | N/A | Verify output file | - |

### Detailed Implementation

**Step 1: Start Containers**
```bash
# Start containers in detached mode
cd docker
docker compose up -d > ../docker-up.log 2>&1

# Verify containers running
docker compose ps
```

**Step 2: Wait for Initialization**
```bash
# Wait for ComfyUI to initialize
echo "Waiting for ComfyUI to initialize..."
sleep 30

# Check container status
docker compose logs --tail 20
```

**Step 3: Verify ComfyUI Web Interface**
```bash
# Check if ComfyUI is accessible
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8188)
echo "HTTP Response Code: $HTTP_CODE"

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✓ ComfyUI is accessible"
    
    # Check page title
    PAGE_TITLE=$(curl -s http://localhost:8188 | grep -o "<title>.*</title>" | sed 's/<[^>]*>//g')
    echo "Page title: $PAGE_TITLE"
else
    echo "✗ ComfyUI not accessible (HTTP $HTTP_CODE)"
    docker compose logs
fi
```

**Step 4: Load and Validate Workflow**
```bash
# Check workflow file exists
ls -la docker/workflows/steadydancer-dance.json

# Verify workflow can be loaded (basic validation)
python3 -c "
import json
with open('docker/workflows/steadydancer-dance.json') as f:
    workflow = json.load(f)
    print(f'✓ Workflow valid: {len(workflow)} nodes')
    print(f'  Nodes: {list(workflow.keys())[:5]}...')
"

# Optional: Check for SteadyDancer-specific nodes
python3 -c "
import json
with open('docker/workflows/steadydancer-dance.json') as f:
    workflow = json.load(f)
    steady_nodes = [k for k in workflow if 'Steady' in str(workflow[k].get('class_type', ''))]
    print(f'SteadyDancer nodes found: {len(steady_nodes)}')
"
```

**Step 5: Generate Test Video**
```bash
# For testing, use minimal parameters:
# - Resolution: 512x512
# - Frames: 30
# - Steps: 10 (instead of 50)

# Using API (if available):
# POST to /api/prompt with minimal workflow

# Or manual testing:
# 1. Open http://localhost:8188
# 2. Load steadydancer-dance.json
# 3. Reduce resolution to 512x512
# 4. Reduce frames to 30
# 5. Reduce steps to 10
# 6. Queue prompt

echo "Test generation with minimal parameters:"
echo "- Resolution: 512x512"
echo "- Frames: 30"
echo "- Steps: 10"
echo "- Expected time: ~2-5 minutes"
```

**Step 6: Verify Output File**
```bash
# Check output directory
ls -la ComfyUI/output/ 2>/dev/null | head -20

# Look for video files
ls -la ComfyUI/output/*.mp4 2>/dev/null

# Check file size
if [ -f ComfyUI/output/*.mp4 ]; then
    FILE_SIZE=$(ls -lh ComfyUI/output/*.mp4 | awk '{print $5}')
    echo "✓ Video generated: $FILE_SIZE"
    
    # Verify file is playable
    ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 ComfyUI/output/*.mp4 2>/dev/null && echo "✓ Video codec valid"
else
    echo "✗ No video file found"
    echo "Check ComfyUI logs: docker compose logs"
fi
```

### Verification
```bash
# Complete verification
bash -c '
echo "=== Phase 6 Verification ==="
echo "Containers running:"
docker compose ps | grep -c "Up" || echo "0"

echo ""
echo "ComfyUI accessible:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8188 | grep -q "200" && echo "✓ HTTP 200 OK"

echo ""
echo "Video generated:"
ls -la ComfyUI/output/*.mp4 2>/dev/null | head -1 || echo "✗ No video"

echo ""
echo "=== All Tests Complete ==="
'
```

### Rollback Instructions
```bash
# If tests fail:
docker compose down
docker rmi steadydancer:latest
docker tag previous-steadydancer:stable steadydancer:latest 2>/dev/null || true
docker compose up -d
```
