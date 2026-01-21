## Phase 4: Model Configuration

### Steps
| Step | File:Line | Action | Parallel With |
|------|-----------|--------|---------------|
| 1 | docker/download_models.sh:322-400 | Read SteadyDancer download section | P3 |
| 2 | N/A | Verify HuggingFace model URLs | P3 |
| 3 | N/A | Test model hub connectivity | P3 |
| 4 | N/A | Confirm variant selection logic | P3 |

### Detailed Implementation

**Step 1: Read Download Script**
```bash
# Find SteadyDancer section
echo "=== SteadyDancer Download Section ==="
grep -n "steadydancer\|SteadyDancer" docker/download_models.sh | head -20

# Check for variant selection
grep -A 20 "STEADYDANCER_VARIANT" docker/download_models.sh
```

**Step 2: Verify Model URLs**
```bash
# Check fp8 variant URL
echo "=== fp8 Variant ==="
grep "kijai/SteadyDancer-14B-pruned" docker/download_models.sh

# Check fp16 fallback URL
echo "=== fp16 Variant ==="
grep "MCG-NJU/SteadyDancer-14B" docker/download_models.sh
```

**Step 3: Test Model Hub Connectivity**
```bash
# Test fp8 model access
echo "=== Testing fp8 Model ==="
HTTP_CODE=$(curl -sI "https://huggingface.co/kijai/SteadyDancer-14B-pruned/resolve/main/config.json" | head -1)
echo "HTTP Response: $HTTP_CODE"

if echo "$HTTP_CODE" | grep -q "200"; then
    echo "✓ fp8 model accessible"
else
    echo "✗ fp8 model not accessible, will use fp16"
fi

# Test fp16 model access
echo "=== Testing fp16 Model ==="
HTTP_CODE=$(curl -sI "https://huggingface.co/MCG-NJU/SteadyDancer-14B/resolve/main/config.json" | head -1)
echo "HTTP Response: $HTTP_CODE"

if echo "$HTTP_CODE" | grep -q "200"; then
    echo "✓ fp16 model accessible"
fi
```

**Step 4: Confirm Variant Selection**
```bash
# Check variant selection logic
echo "=== Variant Selection Logic ==="
grep -B 5 -A 10 "STEADYDANCER_VARIANT" docker/download_models.sh | head -30

# Expected: Check for fp8 first, fallback to fp16 if fp8 unavailable
```

### Verification
```bash
# Complete verification
bash -c '
echo "=== Phase 4 Verification ==="
curl -sI "https://huggingface.co/kijai/SteadyDancer-14B-pruned" | head -1 | grep -q "200" && echo "✓ fp8 model URL valid"
curl -sI "https://huggingface.co/MCG-NJU/SteadyDancer-14B" | head -1 | grep -q "200" && echo "✓ fp16 model URL valid"
grep -q "STEADYDANCER_VARIANT" docker/download_models.sh && echo "✓ Variant selection logic present"
echo ""
echo "=== Ready for Phase 5 ==="
'
```

### Parallel Execution
Phase 4 runs in parallel with Phase 3 as they modify different files (download_models.sh vs Dockerfile).
