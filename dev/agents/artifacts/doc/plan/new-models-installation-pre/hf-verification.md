# HuggingFace Model Verification

## 1. Qwen-Image-Edit-2511 (Comfy-Org repackaged)

- **Repository URL:** https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI
- **Available Files:**
    - `split_files/diffusion_models/qwen_image_edit_2509_bf16.safetensors`
    - `split_files/diffusion_models/qwen_image_edit_2509_fp8_e4m3fn.safetensors`
    - `split_files/diffusion_models/qwen_image_edit_2509_fp8mixed.safetensors`
    - `split_files/diffusion_models/qwen_image_edit_2511_bf16.safetensors`
    - `split_files/diffusion_models/qwen_image_edit_2511_fp8mixed.safetensors`
    - `split_files/diffusion_models/qwen_image_edit_bf16.safetensors`
    - `split_files/diffusion_models/qwen_image_edit_fp8_e4m3fn.safetensors`
    - `.gitattributes`
    - `README.md`
- **Recommended Download:**
    - `diffusion_models`: Recommend `qwen_image_edit_2511_bf16.safetensors` or `qwen_image_edit_2511_fp8mixed.safetensors` based on precision requirements.
    - `text_encoders`: Not explicitly found as separate files. Likely embedded within the main `.safetensors` files or named differently.
    - `vae`: Not explicitly found as separate files. Likely embedded within the main `.safetensors` files or named differently.
- **Notes:** A programmatic comprehensive file listing beyond directory content was not feasible with the available tools. `text_encoders` and `vae` were not found as distinct files/directories; they are presumed to be integrated into the primary model safetensors.

## 2. Genfocus Models

- **Repository URL:** https://huggingface.co/nycu-cplab/Genfocus-Model
- **Available Files:**
    - `checkpoints/depth_pro.pt`
    - `.gitattributes`
    - `README.md`
    - `bokehNet.safetensors`
    - `deblurNet.safetensors`
- **Recommended Download:**
    - `bokehNet`: `bokehNet.safetensors`
    - `deblurNet`: `deblurNet.safetensors`
    - `depth model`: `checkpoints/depth_pro.pt`
- **Notes:** The depth model is named `depth_pro.pt` and is located in the `checkpoints` subdirectory.

## 3. MVInverse Models

- **Repository URL:** https://huggingface.co/Maddog241/mvinverse
- **Available Files:**
    - `.gitattributes`
    - `README.md`
    - `config.json`
    - `model.safetensors`
- **Recommended Download:** `model.safetensors`
- **Notes:** The GitHub repository `https://github.com/zxhuang1698/MVInverse` was not found (404 error). The primary model file `model.safetensors` is hosted directly on HuggingFace.

## 4. Lightning LoRA for Qwen-Image-Edit-2511

- **Repository URL:** https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning
- **Available Files:**
    - `.gitattributes`
    - `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors`
    - `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-fp32.safetensors`
    - `README.md`
    - `qwen_image_edit_2511_fp8_e4m3fn_scaled_lightning.safetensors`
    - `qwen_image_edit_2511_fp8_e4m3fn_scaled_lightning_comfyui.safetensors`
- **Recommended Download:** `qwen_image_edit_2511_fp8_e4m3fn_scaled_lightning_comfyui.safetensors`
- **Notes:** Multiple LoRA files are available in `bf16`, `fp32`, and `fp8` variants. The `_comfyui` version is recommended for integration with ComfyUI.
