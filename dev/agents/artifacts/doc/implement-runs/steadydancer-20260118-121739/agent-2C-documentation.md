# Agent 2C: Documentation Updates

## CLAUDE.md Updates

### Storage Requirements Table (Lines 176-177)
- Updated SteadyDancer: ~14-28GB (fp8/fp16 variants)
- Added TurboDiffusion: ~14GB

### Environment Variables Table (Lines 231-233)
- Added ENABLE_STEADYDANCER
- Added STEADYDANCER_VARIANT
- Added ENABLE_DWPOSE

## Files Modified
- `/home/oz/projects/2025/oz/12/runpod/CLAUDE.md` (storage table, env vars table)

## Verification
```bash
grep -n "SteadyDancer\|TurboDiffusion\|ENABLE_DWPOSE" /home/oz/projects/2025/oz/12/runpod/CLAUDE.md
```
