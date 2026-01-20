# Agent 2B: Build-time Download

## Status
Already integrated into Agent 1A (Dockerfile changes)

## Implementation
- BAKE_STEADYDANCER=false (default)
- BAKE_TURBO=false (default)
- Conditional downloads in Dockerfile lines 276-300

## Usage
```bash
docker compose build   --build-arg BAKE_STEADYDANCER=true   --build-arg STEADYDANCER_VARIANT=fp8   --build-arg BAKE_TURBO=true
```

## Verification
```bash
docker images | grep hearmeman-extended
```
