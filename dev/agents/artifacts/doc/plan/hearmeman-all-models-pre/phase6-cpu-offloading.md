# Phase 6: CPU Offloading Configuration Documentation for RunPod

This document outlines various CPU offloading options available for ComfyUI and specific models within the RunPod environment. Proper configuration can significantly reduce VRAM requirements, allowing models to run on GPUs with less memory at the cost of increased system RAM usage and potentially slower inference times.

---

## 1. ComfyUI VRAM Management Flags

ComfyUI provides several command-line arguments to manage VRAM usage. These flags can be passed via the `COMFYUI_ARGS` environment variable.

| Flag                  | Description                                                                                                                              | VRAM Impact           | Notes                                                    |
| :-------------------- | :--------------------------------------------------------------------------------------------------------------------------------------- | :-------------------- | :------------------------------------------------------- |
| `--lowvram`           | Aggressively moves model parts to CPU when not in use. Splits UNet and performs frequent CPU-GPU transfers.                              | Minimal (e.g., ~4GB)  | Higher system RAM usage, slower performance.             |
| `--medvram`           | A balanced approach, offloading some model components but less aggressively than `--lowvram`.                                            | Medium (e.g., ~6-8GB) | Better performance than `--lowvram`, less system RAM.    |
| `--novram`            | An even more aggressive version of `--lowvram`, for scenarios where `--lowvram` is still insufficient.                                   | Near-zero             | Very high system RAM usage, significantly slower.        |
| `--cpu`               | Forces ComfyUI to run entirely on the CPU.                                                                                               | 0 (CPU-only)          | Extremely slow; use as a last resort or for debugging.   |
| `--async-offload`     | Enables asynchronous weight offloading, potentially improving performance by overlapping computation and data transfer.                  | Low                   | Can improve perceived responsiveness during offloading.  |
| `--reserve-vram N`    | Reserves `N` gigabytes of VRAM for other processes or the operating system. Useful for ensuring system stability on shared GPUs.           | Custom (N GB reserved)| Prevents ComfyUI from using all available VRAM.          |
| `--cpu-text-encoder`  | Forces the text encoder component of the diffusion model to run on the CPU.                                                              | Low                   | Reduces VRAM, increases system RAM/CPU load.             |
| `--cpu-vae`           | Forces the Variational AutoEncoder (VAE) component of the diffusion model to run on the CPU.                                             | Low                   | Reduces VRAM, increases system RAM/CPU load.             |
| `--force-fp16`        | Forces the model to run using half-precision floating-point numbers (FP16), reducing VRAM usage.                                         | Significant           | May introduce minor quality degradation for some models. |
| `--preview-method auto`| Automatically selects the best preview method, often optimizing for VRAM.                                                              | Variable              | Often combined with other VRAM flags.                    |

### COMFYUI_ARGS Environment Variable Usage

To use these flags, set the `COMFYUI_ARGS` environment variable before starting ComfyUI. This is typically done in your `start.sh` script or directly in the shell.

**Example:**
```bash
export COMFYUI_ARGS="--lowvram --cpu-vae --force-fp16"
python main.py $COMFYUI_ARGS
```

---

## 2. Model-Specific Configurations

Some models or custom nodes offer their own specific offloading mechanisms, independent of or in conjunction with ComfyUI's general VRAM flags.

### FlashPortrait (and similar Video Models like Wan2.x)

FlashPortrait, and video models built on frameworks like Wan2.x, often have internal memory management modes. These are typically configured within the model's code or via specific parameters when initializing the model, rather than directly through ComfyUI's command-line arguments.

| Configuration              | Description                                                                    | VRAM Usage | Notes                                     |
| :------------------------- | :----------------------------------------------------------------------------- | :--------- | :---------------------------------------- |
| `model_full_load`          | Loads the entire model onto the GPU.                                           | ~60GB      | Requires high VRAM GPUs (e.g., A100 80GB).|
| `sequential_cpu_offload`   | Offloads model components to CPU sequentially, processing parts on GPU as needed.| ~10GB      | Relies heavily on system RAM for swapping. |
| `model_cpu_offload`        | Offloads a significant portion of the model to CPU.                            | ~30GB      | A more balanced offload than sequential.   |

**Example (Conceptual - actual implementation depends on model API):**
```python
# In a Python script or custom node for FlashPortrait/Wan2.x
if GPU_MEMORY_MODE == "sequential_cpu_offload":
    model = FlashPortraitModel(memory_mode="sequential_cpu_offload")
elif GPU_MEMORY_MODE == "model_cpu_offload":
    model = FlashPortraitModel(memory_mode="model_cpu_offload")
else:
    model = FlashPortraitModel(memory_mode="model_full_load")
```

### FLUX.1 and SDXL Specific Flags

For FLUX.1 and SDXL-based workflows, a common set of flags is recommended for VRAM optimization, especially when `xformers` (a memory-efficient attention mechanism) is not available or causes issues.

**Recommended Flags for FLUX.1/SDXL (when `xformers` is problematic):**
```bash
--disable-xformers --use-split-cross-attention --cache-classic --lowvram
```
- `--disable-xformers`: Disables the xformers library.
- `--use-split-cross-attention`: Uses a memory-efficient split cross-attention mechanism.
- `--cache-classic`: Enables classic caching, which can help reduce redundant computations.
- `--lowvram`: (As described above) further reduces VRAM by aggressive offloading.

---

## 3. RAM Requirements Table for Offloading

CPU offloading modes heavily rely on available system RAM. Insufficient system RAM can lead to out-of-memory errors or extremely slow performance due to excessive disk swapping.

| System RAM Requirement | Use Case                                                               | Notes                                                                                                |
| :--------------------- | :--------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------- |
| **16GB**               | Minimum for basic `--lowvram` usage (e.g., SD 1.5, 512x512).          | May struggle with larger models, higher resolutions, or complex workflows.                           |
| **32GB**               | Comfortable for most `--lowvram`/`--medvram` workflows with SDXL.      | Allows for more complex workflows, larger batch sizes, or intermediate model states to be stored.    |
| **64GB+**              | Ideal for running multiple large models, extensive CPU offloading, or large video models with `sequential_cpu_offload`. | Provides ample headroom for demanding tasks, minimizing disk thrashing.                              |

**GPU VRAM vs. System RAM Tradeoffs:**
- **High VRAM GPUs (24GB+)**: Primarily rely on VRAM for speed and efficiency. System RAM is less critical for offloading.
- **Low VRAM GPUs (8-12GB)**: Heavily dependent on fast and ample system RAM to compensate for limited VRAM. Performance will be bottlenecked by CPU-GPU data transfer and RAM speed.
- **No VRAM (CPU-only)**: Requires maximum system RAM and a powerful CPU. Performance is significantly lower than even low-VRAM GPU setups.

---

## 4. `start.sh` Integration

To make CPU offloading dynamic and adaptable to different RunPod GPU tiers, you can integrate the `COMFYUI_ARGS` environment variable into your `start.sh` script. This allows you to set appropriate flags based on the available VRAM.

**Example `start.sh` snippet:**

```bash
#!/bin/bash

# Default ComfyUI arguments
COMFYUI_ARGS=""

# Check available GPU VRAM (assuming `nvidia-smi` is available)
GPU_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n 1)

echo "Detected GPU VRAM: ${GPU_VRAM} MB"

if (( GPU_VRAM < 12000 )); then # Less than 12GB (e.g., 8GB, 6GB)
    echo "Applying low VRAM settings for ComfyUI."
    COMFYUI_ARGS="--lowvram --cpu-vae --force-fp16 --preview-method auto"
elif (( GPU_VRAM < 24000 )); then # Between 12GB and 24GB (e.g., 12GB, 16GB)
    echo "Applying balanced VRAM settings for ComfyUI."
    COMFYUI_ARGS="--medvram --cpu-text-encoder --force-fp16"
else # 24GB or more (e.g., 24GB, 48GB)
    echo "Applying high VRAM settings for ComfyUI."
    COMFYUI_ARGS="--normalvram" # Or keep empty if no specific flags are needed
fi

# Export COMFYUI_ARGS so ComfyUI can pick them up
export COMFYUI_ARGS

echo "Starting ComfyUI with arguments: ${COMFYUI_ARGS}"

# Your command to start ComfyUI (e.g., python main.py or other entry point)
# Make sure your ComfyUI startup script actually uses the $COMFYUI_ARGS variable
python /workspace/ComfyUI/main.py $COMFYUI_ARGS
```

**Dynamic Flag Selection based on `GPU_TIER` (if available from RunPod environment):**

If RunPod provides a `GPU_TIER` environment variable (e.g., `CONSUMER_8GB`, `PROSUMER_24GB`, `DATACENTER_80GB`), you can use that for more robust logic.

```bash
#!/bin/bash

COMFYUI_ARGS=""
MODEL_SPECIFIC_ARGS="" # For models like FlashPortrait that use internal modes

case "$GPU_TIER" in
    "CONSUMER_8GB"|"CONSUMER_12GB")
        echo "Configuring for consumer GPU tier (${GPU_TIER})."
        COMFYUI_ARGS="--lowvram --cpu-vae --force-fp16 --preview-method auto"
        # For FlashPortrait:
        MODEL_SPECIFIC_ARGS="sequential_cpu_offload"
        ;;
    "PROSUMER_24GB"|"PROSUMER_48GB")
        echo "Configuring for prosumer GPU tier (${GPU_TIER})."
        COMFYUI_ARGS="--medvram --cpu-text-encoder --force-fp16"
        # For FlashPortrait:
        MODEL_SPECIFIC_ARGS="model_cpu_offload"
        ;;
    "DATACENTER_80GB")
        echo "Configuring for datacenter GPU tier (${GPU_TIER})."
        COMFYUI_ARGS="" # No specific VRAM flags needed, use full VRAM
        # For FlashPortrait:
        MODEL_SPECIFIC_ARGS="model_full_load"
        ;;
    *)
        echo "Unknown GPU tier or no tier specified. Using default settings."
        COMFYUI_ARGS=""
        MODEL_SPECIFIC_ARGS="model_full_load"
        ;;
esac

export COMFYUI_ARGS
export GPU_MEMORY_MODE="$MODEL_SPECIFIC_ARGS" # For models that check this env var

echo "Starting ComfyUI with arguments: ${COMFYUI_ARGS}"
echo "Model specific GPU memory mode: ${GPU_MEMORY_MODE}"

python /workspace/ComfyUI/main.py $COMFYUI_ARGS
```

---

## 5. Recommended Configurations by GPU

Here are recommended starting configurations for various GPU VRAM capacities. These are general guidelines; optimal settings may vary depending on the specific workflow and models used.

| GPU VRAM | Recommended ComfyUI Flags                                    | Primary Models/Workflows          | Notes                                                              |
| :------- | :----------------------------------------------------------- | :-------------------------------- | :----------------------------------------------------------------- |
| **8GB**  | `--lowvram --cpu-vae --force-fp16 --preview-method auto`     | SD 1.5, pruned SDXL (768x768)     | Requires 16GB+ system RAM. Expect slower inference.                |
| **12GB** | `--medvram --cpu-text-encoder --force-fp16`                 | SDXL (1024x1024)                  | Comfortable for many SDXL workflows. 32GB+ system RAM recommended. |
| **24GB** | `--normalvram` (default) or no flags                         | SDXL, Genfocus, MVInverse, FlashPortrait (`model_cpu_offload`) | Good balance of VRAM and performance. 32GB+ system RAM.            |
| **48GB+**| No specific VRAM flags (use defaults)                        | InfCam, FlashPortrait (`model_full_load`), large video models | Optimal performance. Less reliance on system RAM for offloading.   |

---

## 6. Troubleshooting Tips

-   **Out of System RAM (OOM)**: If you experience system instability, freezing, or errors indicating memory exhaustion, increase your RunPod's system RAM. Using `--lowvram` or `--novram` with insufficient system RAM will lead to severe performance degradation or crashes.
-   **Slow Inference**: CPU offloading will always be slower than running entirely on GPU. If performance is critical, consider upgrading to a GPU with more VRAM.
-   **Model-Specific Errors**: If a model consistently fails with offloading flags, check its documentation for specific VRAM requirements or incompatible configurations. Some models might not support aggressive offloading well.
-   **Verify `COMFYUI_ARGS`**: Ensure that your ComfyUI startup script correctly receives and processes the `COMFYUI_ARGS` environment variable. Add `echo $COMFYUI_ARGS` in your `start.sh` to debug.
-   **Experimentation**: VRAM management is often an iterative process. Start with moderate settings and progressively increase aggression (e.g., `--medvram` -> `--lowvram` -> `--novram`) until a stable configuration is found.
