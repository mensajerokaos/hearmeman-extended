# SteadyDancer/ComfyUI Testing Plan - Frieren Choreography

**Date**: 2026-01-22
**Test Subject**: Frieren Cosplay Choreography Video Analysis
**Objective**: Validate SteadyDancer dance video generation with physics-based parameters
**Status**: Ready for Testing

---

## Executive Summary

This testing plan integrates the **Frieren dance video analysis** (90% confidence, movement physics + character data) with SteadyDancer's dance video generation capabilities.

**Goal**: Generate new dance choreography frames using the extracted movement physics and character parameters, validating:
1. Motion blur preservation (critical)
2. Character consistency (Frieren aesthetic)
3. Physics realism (garment/hair movement)
4. Performance quality (vanilla vs TurboDiffusion)

---

## Test Environment

### Infrastructure
- **ComfyUI**: Fully configured with SteadyDancer support
- **Models Available**:
  - SteadyDancer vanilla (28GB fp16 or 14GB fp8)
  - TurboDiffusion accelerated (4-step variant)
  - DWPose for skeletal motion extraction
- **Workflows**: Two production workflows ready (steadydancer-dance.json, steadydancer-turbo.json)

### Input Sources
**From Analysis**:
- Video: `cosplayer-frieren-vibe-check-dc-Cody.mp4` (6.0s, 180 frames)
- Character Image: Reference Frieren pose
- Motion Data: Extracted from original video

**Analysis Parameters**:
```
Garment Physics: gravity=9.81, damping=0.15, stiffness=0.8
Hair Dynamics: ~3000 strands, shoulder-to-waist, arc motion
Motion Blur: Limbs (radial), Hair (arc), Fabric (tangential) - 2-4 frames
Foot Contact: Alternating shift, right pivot
Limb Motion: Arms 120°, legs 45°, synchronized
Character: Frieren, graceful, precise, professional
```

---

## Test Phases

### Phase 1: Setup & Validation

#### 1.1 Verify ComfyUI Startup
```bash
# Start ComfyUI with SteadyDancer enabled
cd /workspace/ComfyUI
python main.py --enable-steadydancer

# Expected: Server starts on localhost:8188
# Logs: "Loading SteadyDancer model" visible
```

**Validation Points**:
- [ ] ComfyUI starts successfully
- [ ] SteadyDancer model loads without VRAM errors
- [ ] DWPose weights loaded for pose extraction
- [ ] Web UI accessible at http://localhost:8188

#### 1.2 Load Test Workflows
```bash
# Check workflows are accessible
ls -la docker/workflows/steadydancer-*.json

# Expected output:
# steadydancer-dance.json (4.1 KB) - Vanilla workflow
# steadydancer-turbo.json (4.5 KB) - TurboDiffusion workflow
```

**Validation Points**:
- [ ] Both workflow files exist and are readable
- [ ] JSON syntax is valid (can parse)
- [ ] All referenced nodes are installed

#### 1.3 Prepare Input Assets
```bash
# Verify input video exists
ls -lh /mnt/m/solar/aria-cruz-ai/01-reto-freelancer/video/video_analysis/cosplayer-frieren-vibe-check-dc-Cody.mp4

# Read analysis file
cat /mnt/m/solar/aria-cruz-ai/01-reto-freelancer/video/video_analysis/frieren-cosplay-dance-analysis.md
```

**Validation Points**:
- [ ] Video file exists and is readable
- [ ] Analysis markdown is complete
- [ ] All physics parameters documented

---

### Phase 2: Test Vanilla SteadyDancer

#### 2.1 Create Vanilla Test Workflow

**Nodes Configuration**:
```
LoadImage:
  - Input: Reference Frieren character pose (generated from frames)
  - conditioning_strength: 0.8 (preserve identity)

LoadVideo:
  - Input: Original choreography video (25 fps, 16 frames)
  - frame_count: 16
  - start_frame: 0

DWPreprocessor:
  - detect_hand: true
  - detect_body: true
  - detect_face: true
  - Input video: Original choreography

Wan_LoadDiffusionModel:
  - model: SteadyDancer-14B
  - weight_dtype: fp8 (or fp16 if 24GB+ VRAM)

Wan_ReferenceAttention:
  - reference_image: Frieren character
  - conditioning_strength: 0.8 (from analysis - maintain character)

Wan_CrossFrameAttention:
  - driving_video: Extracted motion from DWPreprocessor
  - frame_count: 16
  - motion_strength: 1.0

Wan_KSampler:
  - steps: 50 (full quality)
  - cfg_scale: 5.0 (from analysis)
  - sampler_name: euler
  - scheduler: karras

SaveVideo:
  - fps: 25
  - format: mp4h264
  - pix_fmt: yuv420p
  - crf: 23 (high quality)
  - Output: generated_frieren_vanilla.mp4
```

#### 2.2 Run Vanilla Test
```bash
# Queue workflow in ComfyUI UI or via API
curl -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d @steadydancer-dance.json
```

**Expected Results**:
- Generation time: 8-12 minutes on 24GB GPU
- Output: `generated_frieren_vanilla.mp4`
- Quality: High (50 diffusion steps)

#### 2.3 Validate Vanilla Output

**Visual Inspection**:
```
✓ Character Identity Preserved
  - Frieren features maintained
  - White hair visible and realistic
  - Costume visible and correctly textured

✓ Motion Blur Preserved
  - Limbs show radial blur during high-speed motion
  - Hair shows arc-based blur during swings
  - Fabric edges show tangential blur

✓ Movement Physics Realistic
  - Garment moves with gravity (dampening visible)
  - Hair settles naturally between swings
  - Foot contact timing appears natural

✓ Frame Consistency
  - No flickering or artifacts
  - Smooth transitions between frames
  - Character stays in frame throughout

✓ Performance Quality
  - Graceful, controlled movements
  - Synchronization maintained
  - Professional appearance
```

---

### Phase 3: Test TurboDiffusion Accelerated

#### 3.1 Create TurboDiffusion Test Workflow

**Key Difference from Vanilla**:
```
Wan_LoadTurbo:
  - model: SteadyDancer-14B-TurboDiffusion
  - steps: 4 (vs 50 vanilla)
  - guide_scale: 5.0
  - end_cond_cfg: 0.4

Wan_KSampler:
  - steps: 4 (instead of 50)
  - cfg_scale: 5.0
  - sampler_name: euler
  - scheduler: karras

# All other nodes identical to vanilla
```

#### 3.2 Run TurboDiffusion Test
```bash
# Queue TurboDiffusion workflow
curl -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d @steadydancer-turbo.json
```

**Expected Results**:
- Generation time: 20-45 seconds on 24GB GPU
- Output: `generated_frieren_turbo.mp4`
- **Speedup**: 100-200x vs vanilla (confirmed in project docs: 4767s → 24s)

#### 3.3 Validate TurboDiffusion Output

**Same Quality Checks as Vanilla**:
```
✓ Character Identity Preserved
✓ Motion Blur Preserved
✓ Movement Physics Realistic
✓ Frame Consistency
✓ Performance Quality

+ Speedup Achievement
  - Generation time < 1 minute
  - Quality comparable to vanilla (4-step approximation)
```

---

### Phase 4: Comparative Analysis

#### 4.1 Quality Comparison

| Aspect | Vanilla | TurboDiffusion | Acceptable? |
|--------|---------|---|---|
| **Motion Blur** | Full quality | Approximate | ✓ if recognizable |
| **Character Identity** | Excellent | Good/Excellent | ✓ if consistent |
| **Movement Realism** | Smooth | May have artifacts | ✓ if natural |
| **Frame Artifacts** | Minimal | Acceptable | ✓ if < 5% visible |
| **Overall Aesthetic** | Professional | Professional | ✓ both acceptable |

#### 4.2 Performance Comparison

| Metric | Vanilla | TurboDiffusion | Ratio |
|--------|---------|---|---|
| **Generation Time** | 600s | 30s | 20x |
| **Steps** | 50 | 4 | 12.5x |
| **Expected Speedup** | 1x | 100-200x | Per docs |
| **VRAM Usage** | Same | Same | Equal |
| **Quality Loss** | Baseline | ~5-10% | Acceptable |

#### 4.3 Analysis Parameter Validation

**Test each parameter from analysis**:

```
GARMENT PHYSICS ✓
  - Damping 0.15: Is fabric settling visible?
  - Stiffness 0.8: Does fabric maintain shape?
  - Collision radius 0.15m: Is hip/thigh interaction realistic?

HAIR DYNAMICS ✓
  - ~3000 strands: Is hair volume realistic?
  - Shoulder-to-waist length: Is length accurate?
  - Key frames 12/24/35: Are motion patterns visible?

MOTION BLUR ✓
  - Limbs radial: Are arm/leg blurs present?
  - Hair arc: Is hair blur curved/arced?
  - Fabric tangential: Is edge blur tangential?
  - 2-4 frame extent: Does blur span expected frames?

FOOT CONTACT ✓
  - Alternating shift: Do feet alternate contact?
  - Right pivot: Is right foot pivot visible?
  - Frames 0/8/16: Are key contact frames correct?

LIMB MOTION ✓
  - Arms 120° arc: Do arms swing at correct angle?
  - Legs 45° extension: Is knee extension correct?
  - Synchronization: Do arms/legs move together?

CHARACTER IDENTITY ✓
  - Frieren aesthetic: Is character recognizable?
  - Graceful, precise: Are movements elegant?
  - Professional quality: Does output look polished?
```

---

### Phase 5: Extended Generation Test

#### 5.1 Generate Extended Choreography

**Use SteadyDancer to extend the original sequence**:

```
Test 1: Frame Extension
  Input: Original 16 frames
  Output: Extended to 32 frames (double length)
  Validation: Smooth continuation, motion physics consistent

Test 2: Character Variation
  Input: Original video with different character pose
  Output: New choreography on different character
  Validation: Motion transfer successful, new character identity preserved

Test 3: Motion Intensity Variation
  Input: Original video with reduced motion_strength
  Output: Subdued movement version
  Validation: Motion scaling works without breaking physics
```

#### 5.2 Motion Blur Preservation Test

**Critical validation - motion blur must be preserved**:

```
Analysis Requirement: MOTION BLUR PRESERVATION CRITICAL

Test Points:
  □ Identify frames with motion blur in original (12, 24, 35)
  □ Check generated frames at same positions
  □ Verify blur direction matches analysis (radial/arc/tangential)
  □ Measure blur temporal extent (expected 2-4 frames)
  □ Confirm blur present in limbs, hair, fabric edges

Pass Criteria:
  ✓ Motion blur clearly visible in generated frames
  ✓ Blur patterns match analysis predictions
  ✓ Blur contributes to visual authenticity
  ✓ No artificial blur removal or reduction
```

---

## Test Execution Checklist

### Pre-Test
- [ ] Read and understand Frieren analysis (`frieren-cosplay-dance-analysis.md`)
- [ ] Verify ComfyUI environment is ready
- [ ] Confirm workflow files are available
- [ ] Check VRAM availability (min 16GB for fp8)
- [ ] Prepare output directory for generated videos

### Vanilla Test
- [ ] Load vanilla workflow in ComfyUI
- [ ] Configure nodes with analysis parameters
- [ ] Run generation
- [ ] Record generation time
- [ ] Validate output file created
- [ ] Perform quality checks (character, blur, physics, consistency)
- [ ] Save output: `generated_frieren_vanilla.mp4`
- [ ] Document observations

### TurboDiffusion Test
- [ ] Load TurboDiffusion workflow
- [ ] Configure nodes with analysis parameters
- [ ] Run generation
- [ ] Record generation time
- [ ] Calculate speedup ratio
- [ ] Validate output file created
- [ ] Perform quality checks
- [ ] Save output: `generated_frieren_turbo.mp4`
- [ ] Document observations

### Comparison & Analysis
- [ ] Compare vanilla vs TurboDiffusion outputs
- [ ] Complete quality comparison table
- [ ] Complete performance comparison table
- [ ] Validate each analysis parameter
- [ ] Document findings in test report

### Extended Tests
- [ ] Test frame extension (16 → 32 frames)
- [ ] Test motion blur preservation specifically
- [ ] Document any artifacts or issues
- [ ] Provide recommendations for production use

---

## Expected Outcomes

### Success Criteria

**Phase 1 (Setup)**: ✓ PASS if:
- ComfyUI starts without errors
- SteadyDancer model loads
- DWPose weights available
- Both workflow files valid

**Phase 2 (Vanilla)**: ✓ PASS if:
- Generation completes (8-12 min)
- Output video playable
- Character identity maintained
- Motion blur visible and correct
- Movement appears natural and graceful

**Phase 3 (TurboDiffusion)**: ✓ PASS if:
- Generation completes (20-45 sec)
- Output video playable
- Quality comparable to vanilla (acceptable 4-step approximation)
- Speedup achieved (>10x)

**Phase 4 (Comparison)**: ✓ PASS if:
- Both outputs meet quality standards
- TurboDiffusion speedup validated
- All analysis parameters correctly applied
- Character consistency maintained

**Phase 5 (Extended)**: ✓ PASS if:
- Extended frames generated smoothly
- Motion blur preservation verified
- Physics remain consistent
- Output suitable for production

---

## Troubleshooting Guide

### Issue: "SteadyDancer model not found"
**Solution**:
```bash
cd docker
python scripts/download_models.sh --steadydancer
```

### Issue: "Out of VRAM"
**Solution**:
- Use fp8 variant instead of fp16
- Reduce frame batch size
- Close other GPU applications
- Use TurboDiffusion instead (same VRAM, faster)

### Issue: "Motion blur not visible in output"
**Solution**:
- Check if blur is inherent to motion (fast movements)
- Verify original video has motion blur
- Increase diffusion steps (vanilla workflow)
- Review DWPreprocessor pose extraction quality

### Issue: "Character identity not preserved"
**Solution**:
- Increase `conditioning_strength` (0.8 → 1.0)
- Use higher quality reference image
- Ensure reference image shows full character design
- Verify `Wan_ReferenceAttention` node configured correctly

### Issue: "Generated video has artifacts/flicker"
**Solution**:
- Increase steps (vanilla: 50 → 75-100)
- Improve `Wan_CrossFrameAttention` motion_strength calibration
- Check if original video is clean (no compression artifacts)
- Consider TurboDiffusion for faster iteration

---

## Documentation & Reporting

### Test Report Structure
```
SteadyDancer Testing Report - Frieren Choreography
Date: [Date]
Tester: [Name]
Environment: [VRAM, GPU, OS]

1. Setup Validation
   - ComfyUI status: [✓ Pass / ✗ Fail]
   - Model loading: [✓ Pass / ✗ Fail]
   - Workflows: [✓ Pass / ✗ Fail]

2. Vanilla Generation
   - Generation time: [X seconds]
   - Output quality: [✓ Pass / ✗ Fail]
   - Character identity: [Assessment]
   - Motion blur: [Assessment]
   - Physics realism: [Assessment]

3. TurboDiffusion Generation
   - Generation time: [X seconds]
   - Speedup achieved: [X.Xx]
   - Quality comparison: [Assessment]

4. Analysis Parameter Validation
   - [Parameter]: [Result]
   - ...

5. Recommendations
   - Production readiness: [Yes/No]
   - Suggested optimizations: [List]
   - Known limitations: [List]
```

### Output Files
Save generated files with timestamps:
- `generated_frieren_vanilla_[timestamp].mp4`
- `generated_frieren_turbo_[timestamp].mp4`
- `steadydancer_test_report_[timestamp].md`

---

## Production Readiness Checklist

After successful testing, confirm production readiness:

- [ ] Vanilla workflow produces high-quality output
- [ ] TurboDiffusion achieves acceptable quality with speedup
- [ ] Motion blur preservation validated
- [ ] Character consistency confirmed
- [ ] Physics parameters correctly applied
- [ ] Performance meets requirements (<1 min for TurboDiffusion)
- [ ] Error handling documented
- [ ] Scaling strategy defined (batch processing)
- [ ] Monitoring setup (logs, metrics, alerts)
- [ ] Rollback procedure documented

---

## Next Steps After Testing

1. **If Successful**:
   - Document results in implementation report
   - Create production workflow templates
   - Set up batch processing pipeline
   - Deploy to RunPod with monitoring

2. **If Issues Found**:
   - Troubleshoot per guide above
   - Document workarounds
   - Iterate on parameter tuning
   - Repeat testing until Pass

3. **Production Deployment**:
   - Create runpod template with SteadyDancer enabled
   - Set up automated job queuing
   - Implement result post-processing
   - Monitor generation metrics

---

**Test Plan Status**: Ready for Execution ✅
**Analysis Used**: Frieren Cosplay Choreography (90% confidence)
**Expected Timeline**: 1-2 hours for full testing cycle
