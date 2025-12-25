# RunPod Expense Report - Z-Image & Voice Test
**Date**: 2025-12-24
**Author**: oz + claude-opus-4-5

## Session Info
| Property | Value |
|----------|-------|
| Pod ID | 43kqp2ypdw3uh6 |
| GPU | RTX A5000 (24GB VRAM) |
| Hourly Cost | $0.16/hr |
| Template | Hearmeman 758dsjwiqz |
| Storage | Ephemeral (450GB) |

## Timeline

| Time (CST) | Event | Elapsed | Notes |
|------------|-------|---------|-------|
| 02:32:45 | Pod deployed | 0:00 | GraphQL API deployment |
| 02:33:29 | SSH available | +0:01 | Pod booting |
| 02:37:37 | ComfyUI ready | +0:05 | Proxy accessible |
| 02:39:56 | Z-Image check | +0:07 | NOT installed (video template) |
| 02:40:47 | VibeVoice test | +0:08 | First TTS submission |
| 02:41:58 | Test complete | +0:09 | 30s generation time |
| 02:47:00 | Ch1 generation | +0:14 | Apertura |
| 02:48:00 | Ch2 generation | +0:15 | El Origen |
| 02:49:00 | Ch3 generation | +0:16 | Lo Colectivo |
| 02:50:00 | Ch4 generation | +0:17 | El Lenguaje |
| 02:51:00 | Ch5 generation | +0:18 | La Exposición |
| 02:52:00 | Ch6 generation | +0:19 | Lo Que Viene |
| 02:53:00 | All downloaded | +0:20 | 7 FLAC files saved |

## Test Results Summary

### VibeVoice TTS ✅ SUCCESS
- **Model**: VibeVoice-1.5B
- **Generation Time**: ~30 seconds per segment
- **Quality**: FLAC lossless, 24kHz stereo
- **Total Audio**: 7 files, ~105 seconds combined

### Z-Image ❌ NOT AVAILABLE
- Template is video-focused (WAN 2.1/2.2)
- No image generation checkpoints
- Requires manual installation via ComfyUI Manager UI

### XTTS v2 ❌ NOT INSTALLED
- Only VibeVoice TTS node available
- Would need manual installation for voice cloning

## Generated Audio Files

| File | Duration | Size | Content |
|------|----------|------|---------|
| voice_test_maquila_00001_.flac | 10.4s | 226KB | Intro test |
| vo_ch1_apertura_00001_.flac | 18.3s | 426KB | Ch1: Por Mi Vulva |
| vo_ch2_origen_00001_.flac | 16.1s | 345KB | Ch2: El Origen |
| vo_ch3_colectivo_00001_.flac | 14.9s | 365KB | Ch3: Lo Colectivo |
| vo_ch4_lenguaje_00001_.flac | 18.5s | 409KB | Ch4: El Lenguaje |
| vo_ch5_exposicion_00001_.flac | 13.5s | 298KB | Ch5: La Exposición |
| vo_ch6_futuro_00001_.flac | 13.3s | 281KB | Ch6: Lo Que Viene |
| **TOTAL** | **105.0s** | **2.35MB** | |

## Cost Calculation

| Metric | Value |
|--------|-------|
| Runtime | ~20 minutes |
| Hours | 0.33 hr |
| Rate | $0.16/hr |
| **Session Cost** | **$0.053** |

### If Pod Still Running
- Current time check recommended
- Stop pod to prevent additional charges

## Files Saved To

**Local Project**:
```
/home/oz/projects/2025/jose-obscura/12/documental-macq/audio/vo-test/
```

**NAS**:
```
R:\Jose Obscura\Documental MACQ\Audio\VO\
```

## Recommendations

1. **Stop the pod** if no further testing needed to save costs
2. **For Z-Image testing**: Deploy a different template with SDXL/Flux checkpoints, or manually install Z-Image via the ComfyUI Manager UI
3. **For voice cloning**: VibeVoice supports reference audio via `speaker_X_voice` inputs - upload reference audio to test
4. **Quality check**: Review generated audio for accent/pronunciation quality

## Commands Reference

```bash
# Stop pod (save costs)
curl -s --request POST \
  --header 'content-type: application/json' \
  --url "https://api.runpod.io/graphql?api_key=$API_KEY" \
  --data '{"query": "mutation { podStop(input: { podId: \"43kqp2ypdw3uh6\" }) { id } }"}'

# Check pod status
curl -s --request POST \
  --header 'content-type: application/json' \
  --url "https://api.runpod.io/graphql?api_key=$API_KEY" \
  --data '{"query": "query { pod(input: {podId: \"43kqp2ypdw3uh6\"}) { desiredStatus runtime { uptimeInSeconds } } }"}'
```
