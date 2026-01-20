## Relations
@structure/generation/specialized_generation_models.md
@structure/deployment/runpod_deployment.md

## Raw Concept
**Task:**
SteadyDancer Integration Testing

**Changes:**
- Finalized testing results: ComfyUI 0.6.0 compatibility, prompt framework, and GGUF VRAM requirement (7GB)

**Files:**
- docker/workflows/steadydancer-turbo.json
- docker/download_models.sh

**Flow:**
Accept License -> Set HF_TOKEN -> Extract Pose -> ReferenceAttention -> TurboDiffusion (4 steps) -> Output

**Timestamp:** 2026-01-18

## Narrative
### Structure
- Wan_ReferenceAttention (Identity preservation)
- Wan_CrossFrameAttention (Temporal coherence)
- Wan_KSampler (Core generation)
- Workflow: steadydancer-turbo.json (4 steps)

### Dependencies
- ComfyUI 0.6.0
- Gated Model: MCG-NJU/SteadyDancer-14B (requires license acceptance and HF_TOKEN)
- TurboDiffusion (Dec 2025) for 4-step generation
- DWPose for motion extraction

### Features
- Testing Complete: Verified on RTX 4080 SUPER
- GGUF variant supported for low VRAM (7GB footprint)
- 100-200x speedup via TurboDiffusion (4 steps vs 50+)
- Prompt framework: hair movement, clothing physics, foot grounding
- Key inference settings: guide_scale=5.0, condition_scale=1.0, end_cfg=0.4
