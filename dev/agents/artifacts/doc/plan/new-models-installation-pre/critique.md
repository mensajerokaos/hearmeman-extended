# Implementation Plan Critique
## New Models Installation - Hearmeman Extended RunPod Template

**Reviewer**: claude-opus-4-5 (self-critique)
**Date**: 2025-12-28
**Plan Version**: Draft 1

---

## Scoring Summary

| Criteria | Score | Notes |
|----------|-------|-------|
| **Clarity** | 6/10 | Good structure, but custom nodes have incomplete implementations |
| **Completeness** | 5/10 | Missing actual inference code, dependency conflicts unresolved |
| **Accuracy** | 3/10 | **CRITICAL**: Wrong HuggingFace repos/files, missing model paths |
| **Feasibility** | 4/10 | Placeholder code won't function; MVInverse location unknown |

**Overall Score**: 4.5/10 - **Not ready for implementation**

---

## Critical Issues (MUST FIX)

### 1. Wrong HuggingFace Repository Names (Accuracy: CRITICAL)

**Section 2.1 - Qwen Image Edit 2511 Download Block**

| Item | Plan States | Reality | Action |
|------|-------------|---------|--------|
| Repo name | `Comfy-Org/Qwen-Image-Edit-2511_ComfyUI_repackaged` | **DOES NOT EXIST** | Use `Comfy-Org/Qwen-Image-Edit_ComfyUI` |
| Diffusion file | `qwen_image_edit_2511_fp8_e4m3fn.safetensors` | **NOT AVAILABLE** | Use `split_files/diffusion_models/qwen_image_edit_2511_bf16.safetensors` or `qwen_image_edit_2511_fp8mixed.safetensors` |
| Text encoder | `qwen_2.5_vl_7b_fp8_scaled.safetensors` | Different repo | Use `Comfy-Org/HunyuanVideo_1.5_repackaged` for this file |
| VAE | `qwen_image_vae.safetensors` | Different repo | Use `Comfy-Org/Qwen-Image_ComfyUI` |
| Lightning LoRA | `Qwen-Image-Lightning-4steps-V1.0.safetensors` | Wrong repo | Use `lightx2v/Qwen-Image-Edit-2511-Lightning` repo with file `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors` |

**Correct Download Block**:
```bash
if [ "${ENABLE_QWEN_IMAGE_EDIT:-false}" = "true" ]; then
    echo "[Qwen Image Edit] Downloading Qwen-Image-Edit-2511 models..."

    # Diffusion Model (BF16 - no FP8 e4m3fn variant for 2511)
    hf_download "Comfy-Org/Qwen-Image-Edit_ComfyUI" \
        "split_files/diffusion_models/qwen_image_edit_2511_bf16.safetensors" \
        "$MODELS_DIR/diffusion_models/qwen_image_edit_2511_bf16.safetensors"

    # Text Encoder (from HunyuanVideo repackaged)
    hf_download "Comfy-Org/HunyuanVideo_1.5_repackaged" \
        "qwen_2.5_vl_7b_fp8_scaled.safetensors" \
        "$MODELS_DIR/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors"

    # VAE (from Qwen-Image)
    hf_download "Comfy-Org/Qwen-Image_ComfyUI" \
        "qwen_image_vae.safetensors" \
        "$MODELS_DIR/vae/qwen_image_vae.safetensors"

    # Lightning LoRA for faster inference (optional)
    hf_download "lightx2v/Qwen-Image-Edit-2511-Lightning" \
        "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors" \
        "$MODELS_DIR/loras/Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors"

    echo "[Qwen Image Edit] Download complete"
fi
```

---

### 2. MVInverse Model Location Unknown (Accuracy: CRITICAL)

**Section 2.3 - MVInverse Download Block**

| Issue | Details |
|-------|---------|
| HuggingFace repo | `Maddog241/mvinverse` - **Cannot be verified** (no API response) |
| Checkpoint files | **Not documented** in GitHub README |
| Download method | `snapshot_download` may fail if repo doesn't exist |

**Questions to Resolve**:
1. Does `Maddog241/mvinverse` exist on HuggingFace or is it private?
2. Are checkpoints hosted on Google Drive or another platform?
3. What are the exact checkpoint filenames?

**Research Required**: Check GitHub issues/discussions or contact authors at `https://github.com/Maddog241/mvinverse`

---

### 3. Custom Node Implementations Are Placeholders (Feasibility: CRITICAL)

**Section 3.1 - Genfocus Custom Node**

The current implementation has `# TODO: Implement actual...` comments everywhere:
- Lines 383-387: Depth estimation returns grayscale placeholder
- Lines 420-424: Deblur returns input unchanged
- Lines 481-486: Bokeh returns input unchanged

**Missing Implementation Details**:
- How to load safetensors into proper model architectures
- What are the actual model classes? (BokehNet, DeblurNet architectures)
- Input/output tensor shapes and normalization requirements
- The Genfocus `demo.py` has the inference code but it's not public yet per their roadmap

**Genfocus Dependencies Missing** (from actual requirements.txt):
```
transformers
diffusers
peft
opencv-python
protobuf
sentencepiece
gradio
jupyter
torchao
git+https://github.com/apple/ml-depth-pro.git
scikit-image
```

**Plan States**:
```
einops
timm
kornia
safetensors
```

This is **completely wrong**. Genfocus uses `ml-depth-pro` (Apple's depth model), not a custom depth model!

---

### 4. MVInverse Custom Node Has No Real Implementation (Feasibility: CRITICAL)

**Section 3.2 - MVInverse Custom Node**

- Line 617-620: Model loading returns `{"loaded": True}` dummy
- Lines 694-700: Inference returns placeholder tensors
- No actual DINOv2 encoder integration
- No ResNeXt feature extraction
- No DPT prediction heads

**MVInverse Dependencies Missing** (from actual requirements.txt):
```
pillow
opencv-python
huggingface_hub
```

But the project likely needs more (DINOv2, etc.) - documentation is incomplete.

---

## Moderate Issues (SHOULD FIX)

### 5. Dockerfile Layer 3 - Missing Requirements Install

**Line 55-57**: Plan has `pip install --no-cache-dir -r requirements.txt || true` for QwenEditUtils.

However, the QwenEditUtils GitHub page doesn't show a requirements.txt. Need to verify the file exists before relying on it.

**Verification**: Check `https://github.com/lrzjason/Comfyui-QwenEditUtils/blob/main/requirements.txt`

---

### 6. Layer 4 Dependencies May Conflict

**Potential Issues**:

1. **diffusers from git**: Latest diffusers may break existing code
   ```dockerfile
   RUN pip install --no-cache-dir git+https://github.com/huggingface/diffusers.git
   ```
   - Risk: API changes break other nodes
   - Mitigation: Pin to specific commit

2. **Genfocus requires ml-depth-pro**:
   ```
   git+https://github.com/apple/ml-depth-pro.git
   ```
   - Not mentioned in plan
   - May have its own heavy dependencies

3. **gradio**: Genfocus needs it but it's a web framework - unnecessary for ComfyUI node

---

### 7. Model Directory Path Inconsistency

**Section 1.4 - Layer 5 Model Directories**

Plan creates `/workspace/ComfyUI/models/genfocus` and `/workspace/ComfyUI/models/mvinverse`

But custom nodes hardcode:
```python
MODELS_DIR = "/workspace/ComfyUI/models/genfocus"  # Line 313
MODELS_DIR = "/workspace/ComfyUI/models/mvinverse" # Line 607
```

This is fine, but the plan should:
1. Specify these are **non-standard** ComfyUI model directories
2. Document how ComfyUI Manager would find them (if at all)
3. Consider using `folder_paths.get_folder_paths()` for consistency

---

### 8. VRAM Estimates May Be Wrong

**Executive Summary Table**:
| Model | Plan States | Likely Reality |
|-------|-------------|----------------|
| Qwen-Image-Edit-2511 | 12-16GB | ~24GB+ for BF16 (7B text encoder + diffusion model) |
| Genfocus | 12GB+ | Unknown (no benchmarks available) |
| MVInverse | 10-16GB | ~12-16GB (DINOv2 + ResNeXt + DPT heads) |

**Issue**: Using BF16 instead of FP8 for Qwen means higher VRAM. Plan should document FP8mixed as alternative.

---

### 9. QwenEditUtils Node Compatibility

**Section 1.2** states:
> ComfyUI Node Status: **Exists**: lrzjason/Comfyui-QwenEditUtils

**Reality**:
- The node provides text encoding utilities, not full inference
- Actual nodes: `TextEncodeQwenImageEditPlusAdvance`, `TextEncodeQwenImageEditPlusCustom`
- These work WITH ComfyUI's built-in Qwen loaders, not as standalone
- Plan should clarify what nodes are actually provided

---

## Minor Issues (NICE TO FIX)

### 10. Verification Commands May Fail

**Line 70-71**:
```bash
docker exec -it runpod ls -la /workspace/ComfyUI/custom_nodes/ | grep -E "(QwenEdit|Genfocus|MVInverse)"
```

- Container name is `hearmeman-extended`, not `runpod` (per docker-compose.yml)
- Fix: `docker exec -it hearmeman-extended ls ...`

---

### 11. Missing Python Type Hints

Custom nodes lack proper type hints which reduces maintainability:
```python
def estimate_depth(self, image):  # No type hints
```

Should be:
```python
def estimate_depth(self, image: torch.Tensor) -> tuple[torch.Tensor]:
```

---

### 12. NODE_DISPLAY_NAME_MAPPINGS Are Too Long

**Line 563-567**:
```python
"GenfocusDeblur": "Genfocus Deblur (All-in-Focus)",
```

Consider shorter names that fit ComfyUI's UI better:
```python
"GenfocusDeblur": "Genfocus Deblur",
```

---

## Questions That Need Answers Before Implementation

| # | Question | Required For |
|---|----------|--------------|
| 1 | Does `Comfy-Org/Qwen-Image-Edit_ComfyUI` have all files in `split_files/` path structure? | Download script |
| 2 | What is the actual HuggingFace repo for MVInverse? Or is it Google Drive? | Download script |
| 3 | What model architectures do Genfocus BokehNet/DeblurNet use? | Custom node implementation |
| 4 | Does `ml-depth-pro` work with CUDA 12.8 in the base image? | Dockerfile dependencies |
| 5 | Is Genfocus inference code public? (Roadmap shows unchecked) | Custom node implementation |
| 6 | What exact checkpoint files does MVInverse inference need? | Download script, custom node |
| 7 | Does QwenEditUtils require additional ComfyUI nodes (like Qwen loaders)? | Dockerfile layer 3 |

---

## Recommended Actions

### Priority 1: Fix Download Scripts (BLOCKING)

1. **Verify exact file paths** from HuggingFace API:
   ```bash
   curl -s "https://huggingface.co/api/models/Comfy-Org/Qwen-Image-Edit_ComfyUI" | jq '.siblings[]?.rfilename'
   ```

2. **Research MVInverse model hosting** - check GitHub issues or contact authors

3. **Update plan** with correct repos and file paths

### Priority 2: Implement Real Inference Code (BLOCKING)

1. **Genfocus**: Wait for official inference code or reverse-engineer from `demo.py`

2. **MVInverse**: Get actual model loading code from GitHub repo

3. **Consider deferring** these nodes until official ComfyUI integrations exist

### Priority 3: Fix Dependencies (HIGH)

1. Use actual `requirements.txt` from each project
2. Pin diffusers to known-working version
3. Add `ml-depth-pro` for Genfocus

### Priority 4: Update Documentation (MEDIUM)

1. Correct VRAM estimates
2. Fix container name in verification commands
3. Document custom model directory structure

---

## Conclusion

The plan has a solid structure but contains **critical accuracy errors** that would cause the implementation to fail:

1. **Wrong HuggingFace repositories** for Qwen models
2. **Unknown model location** for MVInverse
3. **Placeholder implementations** that don't actually function
4. **Wrong dependencies** for Genfocus

**Recommendation**: Do NOT implement until:
1. Correct HuggingFace URLs are verified
2. MVInverse model location is confirmed
3. Real inference code is obtained or written
4. Dependencies are validated

---

## Sources

- [Comfy-Org/Qwen-Image-Edit_ComfyUI](https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI)
- [lrzjason/Comfyui-QwenEditUtils](https://github.com/lrzjason/Comfyui-QwenEditUtils)
- [nycu-cplab/Genfocus-Model](https://huggingface.co/nycu-cplab/Genfocus-Model)
- [rayray9999/Genfocus](https://github.com/rayray9999/Genfocus)
- [Maddog241/mvinverse](https://github.com/Maddog241/mvinverse)
- [ComfyUI Qwen Image Edit Tutorial](https://docs.comfy.org/tutorials/image/qwen/qwen-image-edit-2511)
