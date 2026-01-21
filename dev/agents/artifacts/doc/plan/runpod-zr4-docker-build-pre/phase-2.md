## Phase 2: Dockerfile Validation

### Steps
| Step | File:Line | Action | Parallel With |
|------|-----------|--------|---------------|
| 1 | docker/Dockerfile:1-50 | Validate Dockerfile syntax | - |
| 2 | docker/Dockerfile:VAR | Verify build-arg definitions | - |
| 3 | docker/Dockerfile:VAR | Check dependency specifications | - |
| 4 | docker/Dockerfile:VAR | Confirm environment variables | - |

### Detailed Implementation

**Step 1: Validate Dockerfile Syntax**
```bash
# Dry run to check syntax (no actual build)
docker build --help  # Verify buildx available
docker build -t syntax-check --no-run -f docker/Dockerfile .

# Check exit code
if [ $? -eq 0 ]; then
    echo "✓ Dockerfile syntax valid"
else
    echo "✗ Dockerfile has syntax errors"
    exit 1
fi
```

**Step 2: Verify Build-Arg Definitions**
```bash
# Check for SteadyDancer-related ARGs
echo "=== Build ARGs ==="
grep -n "ARG.*=" docker/Dockerfile | grep -i "steadydancer\|bake\|enable" || echo "No SteadyDancer ARGs found"

# Expected ARGs:
# ARG BAKE_STEADYDANCER=false
# ARG STEADYDANCER_VARIANT=fp8
# ARG ENABLE_FLASH_ATTN=true
```

**Step 3: Check Dependency Specifications**
```bash
# Check for OpenMMLab dependencies
echo "=== Dependencies ==="
grep -n "mmcv\|mmpose\|mmdet\|mmengine\|dwpose" docker/Dockerfile | head -10

# Expected:
# mmcv==2.1.0
# mmdet>=3.1.0
# mmpose>=1.0.0
# dwpose>=0.1.0
```

**Step 4: Confirm Environment Variables**
```bash
# Check for SteadyDancer environment variables
echo "=== Environment Variables ==="
grep -n "ENABLE_STEADYDANCER\|STEADYDANCER_VARIANT\|STEADYDANCER_" docker/Dockerfile

# Expected:
# ENV ENABLE_STEADYDANCER=false
# ENV STEADYDANCER_VARIANT=fp8
```

### Verification
```bash
# Complete validation script
bash -c '
echo "=== Phase 2 Verification ==="
docker build -t syntax-check --no-run -f docker/Dockerfile . && echo "✓ Syntax valid"
grep -q "ARG BAKE_STEADYDANCER" docker/Dockerfile && echo "✓ BAKE_STEADYDANCER arg present"
grep -q "mmcv==2.1.0" docker/Dockerfile && echo "✓ mmcv 2.1.0 specified"
grep -q "ENABLE_STEADYDANCER" docker/Dockerfile && echo "✓ ENABLE_STEADYDANCER env present"
echo ""
echo "=== Ready for Phase 3 ==="
'
```
