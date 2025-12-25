# Research for Hearmeman Extended Template

**Author**: oz
**Model**: gemini-2.5-flash
**Date**: Wednesday, December 24, 2025
**Task**: External Research for Hearmeman Extended Template

## 1. RunPod Documentation

### Template Creation API

RunPod offers both REST API and GraphQL endpoints for template creation.

**REST API Endpoint:** `POST https://rest.runpod.io/v1/templates`

**GraphQL Endpoint:** `POST https://api.runpod.io/graphql` (using `saveTemplate` mutation)

Key parameters for template creation:
- `name` (string): The display name for your template.
- `imageName` (string): The path to the Docker image (e.g., "runpod/base:0.1.0").
- `dockerArgs` (string): Arguments to pass to the Docker container. For GraphQL, this is a string. For REST, `dockerEntrypoint` (array of strings) and `dockerStartCmd` (array of strings) can also be used.
- `containerDiskInGb` (integer): Disk size for the container in GB.
- `volumeInGb` (integer): Size of the persistent volume in GB. (Must be 0 for serverless templates)
- `volumeMountPath` (string): Path where the volume will be mounted inside the container (default: "/workspace").
- `ports` (string or array of strings): Port mappings for the container (e.g., "8888/http,22/tcp" for REST API, or ["8888/http", "22/tcp"] for GraphQL).
- `env` (array of objects for GraphQL/Python SDK, or object for REST): Environment variables to set. Each object has "key" and "value" fields.
- `isPublic` (boolean): Whether the template is public.
- `isServerless` (boolean): Whether the template is for serverless deployment.

### Environment Variable Handling

Environment variables can be set during template creation using the `env` parameter.

- **REST API:** `env` parameter is an object with key-value pairs (e.g., `"env": { "ENV_VAR": "value" }`).
- **GraphQL/Python SDK:** `env` is an array of objects, each with a `key` and `value` property (e.g., `"env": [ { "key": "key1", "value": "value1" } ]`).

These environment variables are then available within the container at runtime.

### /workspace Mount Detection

The `volumeMountPath` parameter, when creating a template, defaults to `/workspace`. This indicates that RunPod expects `/workspace` to be the primary location for persistent storage that can be shared across instances or re-attached.

Best practice is to configure applications within the Docker image to expect or check for `/workspace` for data persistence.

### Start Command Best Practices

The `dockerArgs`, `dockerEntrypoint`, and `dockerStartCmd` parameters control how the container starts.

- `dockerArgs` (string): General arguments passed to Docker.
- `dockerEntrypoint` (array of strings): Defines the executable that will run when the container starts. If specified, `dockerStartCmd` will be passed as arguments to this entrypoint.
- `dockerStartCmd` (array of strings): The command that will be executed when the container starts. If `dockerEntrypoint` is not specified, this will be the main command executed.

It's recommended to have a `start.sh` script within your Docker image, which can then be invoked by `dockerStartCmd` or `dockerEntrypoint`. This script can handle environment setup, dependency checks, and then launch your main application. For example:
`"dockerArgs": "bash -c \"cd /workspace && python train.py\""` or using a `start.sh` script: `"dockerStartCmd": ["bash", "/app/start.sh"]`.

### RunPod Template Configuration JSON
A typical JSON structure for creating a RunPod template via the REST API:
```json
{
  "name": "My Custom ComfyUI Template",
  "imageName": "your-ghcr-username/comfyui-hearmeman:latest",
  "category": "NVIDIA",
  "containerDiskInGb": 50,
  "volumeInGb": 100,
  "volumeMountPath": "/workspace",
  "ports": [
    "8188/http"
  ],
  "env": {
    "COMFYUI_PORT": "8188",
    "PYTHONUNBUFFERED": "1"
  },
  "isPublic": false,
  "readme": "## My Custom ComfyUI Template\n\nThis template provides a pre-configured environment for ComfyUI with various custom nodes and models."
}
```


```bash
#!/bin/bash

# Detect /workspace mount
if [ -d "/workspace" ]; then
    echo "/workspace detected. Using it for persistent storage."
    DATA_DIR="/workspace"
else
    echo "/workspace not detected. Using /app/data for temporary storage."
    DATA_DIR="/app/data"
    mkdir -p $DATA_DIR
fi

# Example: Navigate to ComfyUI directory
cd /app/ComfyUI

# Example: Activate virtual environment if necessary
# source venv/bin/activate

# Example: Start ComfyUI
# python main.py --listen 0.0.0.0 --port 3000 --highvram --gpu-id 0

# Keep container running
tail -f /dev/null
```

## 2. ComfyUI Custom Nodes (web search)

### ComfyUI-ControlNet Repo and Models

- The foundational ControlNet GitHub repository is by `lllyasviel` (https://github.com/lllyasviel/ControlNet).
- Hugging Face is a primary source for official ControlNet models, including those for SDXL. Stability AI provides official ControlNet LoRA files on Hugging Face.
- Downloaded ControlNet model files (typically `.pth` or `.safetensors` extensions) should be placed in the `ComfyUI/models/controlnet/` directory.

### Latest ControlNet Model URLs (HuggingFace)
*(To be filled with specific URLs and sizes)*

### ControlNet Preprocessor Repos

- The `Fannovel16/comfyui_controlnet_aux` GitHub repository (https://github.com/Fannovel16/comfyui_controlnet_aux) provides auxiliary preprocessors for creating hint images (e.g., stickman, Canny edge) that are used with ControlNet models.


## 3. Model Download URLs (HuggingFace)

### VibeVoice-Large
- **URL**: https://huggingface.co/microsoft/VibeVoice-Large
- **Size**: 18.7 GB (There are also 8-bit quantized at 11.6 GB and 4-bit NF4 quantized at ~6.6 GB versions available.)

### SteadyDancer Weights
- **Hugging Face Repository**: `MCG-NJU/SteadyDancer-14B`
- **Download Command (using `huggingface-cli`)**:
  ```bash
  huggingface-cli download MCG-NJU/SteadyDancer-14B --local-dir ./SteadyDancer-14B
  ```
- **URL**: https://huggingface.co/MCG-NJU/SteadyDancer-14B
- **Size**: Approximately 28 GB (Estimated based on prompt, as exact file size requires direct Hugging Face page inspection).

### SCAIL Weights
- **URL**: https://huggingface.co/zai-org/SCAIL-Preview
- **Size**: 32.8 GB

### Z-Image Turbo Components

Z-Image Turbo utilizes a Scalable Single-Stream Diffusion Transformer (S3-DiT) architecture where Text Encoder, Diffusion Model, and VAE components are integrated into "All-in-One" packages. Individual components with the specified sizes (~8GB Text encoder, ~13GB Diffusion model, ~335MB VAE) were not explicitly found as separate downloads.

The available "All-in-One" repackages of Z-Image Turbo on Hugging Face include the integrated VAE and Text Encoder:

- **Z-Image Turbo FP8-AIO:** Approximately 10 GB
- **Z-Image Turbo BF16-AIO:** Approximately 20 GB

**Relevant Hugging Face Model Page:**
- **URL**: https://huggingface.co/Z-Image-model-card

### ControlNet Models (Canny, Depth, Pose, Normal, Lineart)

#### Canny
- **Model**: `qualcomm/ControlNet-Canny`
- **URL**: https://huggingface.co/qualcomm/ControlNet-Canny
- **Size**: 1.4 GB
- **Note**: Other versions exist for SDXL with varying sizes (e.g., `diffusers_xl_canny_full.safetensors` at 2.5 GB).

#### Depth
- **Model**: `control_v11p_sd15_depth.pth`
- **URL**: https://huggingface.co/lllyasviel/ControlNet/blob/main/models/control_v11p_sd15_depth.pth
- **Size**: 1.45 GB

#### Pose
- **Model**: `control_v11p_sd15_openpose.pth`
- **URL**: https://huggingface.co/lllyasviel/ControlNet/blob/main/models/control_v11p_sd15_openpose.pth
- **Size**: 1.45 GB

#### Normal
- **Model**: `control_v11p_sd15_normalbae.pth`
- **URL**: https://huggingface.co/lllyasviel/ControlNet/blob/main/models/control_v11p_sd15_normalbae.pth
- **Size**: 1.45 GB

#### Lineart
- **Model**: `control_v11p_sd15_lineart.pth`
- **URL**: https://huggingface.co/lllyasviel/ControlNet/blob/main/models/control_v11p_sd15_lineart.pth
- **Size**: 1.45 GB


## 4. Docker Best Practices

### Multi-stage Builds for PyTorch

Multi-stage builds are crucial for creating optimized Docker images for PyTorch applications, separating the build environment (with heavy dependencies) from the lightweight runtime environment.

**1. Choose Appropriate Base Images:**
- **Builder Stage**: Use a base image with all necessary build tools and development dependencies. For PyTorch with CUDA, `nvidia/cuda:X.Y-cudnnZ-devel-ubuntuA.B` is suitable.
- **Runtime Stage**: Select a minimal base image for the final image. Examples include `python:X.Y-slim-buster` or a PyTorch-specific runtime image like `pytorch/pytorch:X.Y.Z-cudaA.B-cudnnC-runtime`. If no GPU is needed, a CPU-only PyTorch installation drastically reduces size.

**2. Implement Multi-Stage Builds Effectively:**
- Use multiple `FROM` instructions, naming each stage (e.g., `FROM ... AS builder`).
- Only copy essential artifacts (application code, trained models, installed packages) from the build stage to the final runtime stage using `COPY --from=<stage_name>`. This avoids including unnecessary build-time dependencies.

**3. Optimize Dependency Installation:**
- Install all Python packages and other dependencies in the build stage.
- Use `pip install --no-cache-dir` to prevent `pip` from caching downloaded packages, reducing image size.
- Clean up package manager caches (e.g., `rm -rf /var/lib/apt/lists/*` after `apt` installs).
- For custom CUDA kernels, install `cuda-minimal-build` in the build stage instead of the larger `devel` image.

**4. Enhance Build Efficiency:**
- Optimize build order: Place layers that change infrequently earlier in the `Dockerfile` to leverage Docker's build cache.
- Use `.dockerignore`: Exclude irrelevant files (e.g., `.git`, `__pycache__`) from the build context.
- Leverage BuildKit: Enable BuildKit for improved performance and caching.

**5. Deployment Considerations:**
- Store large model weights separately from the application code to allow for easier updates and smaller image sizes.



### GHCR Authentication and Push Workflow

GitHub Container Registry (GHCR) can be used to host Docker images. Authentication and pushing can be done manually via the Docker CLI or automated using GitHub Actions.

**1. Manual Authentication and Push (using Docker CLI)**

- **Generate a Personal Access Token (PAT)**:
    - Go to GitHub settings > Developer settings > Personal access tokens > Tokens (classic).
    - Generate a new token with a descriptive name and set an expiration.
    - **Crucially, select the `write:packages` scope.** (`read:packages` for pulling, `delete:packages` for deleting are optional).
    - Copy the token immediately. Store it securely and never commit it to version control.

- **Log in to GHCR**:
    ```bash
    echo YOUR_PERSONAL_ACCESS_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
    ```
    Replace `YOUR_PERSONAL_ACCESS_TOKEN` and `YOUR_GITHUB_USERNAME`.

- **Build and Tag Your Docker Image**:
    ```bash
    docker build -t ghcr.io/YOUR_GITHUB_USERNAME/YOUR_IMAGE_NAME:latest .
    ```
    Replace `YOUR_GITHUB_USERNAME` and `YOUR_IMAGE_NAME`.

- **Push Your Docker Image**:
    ```bash
    docker push ghcr.io/YOUR_GITHUB_USERNAME/YOUR_IMAGE_NAME:latest
    ```

**2. Automated Push Workflow (using GitHub Actions)**

Create a YAML file (e.g., `.github/workflows/build-and-push.yml`) in your repository:

```yaml
name: Build and Push Docker Image to GHCR

on:
  push:
    branches:
      - main # Trigger on pushes to the main branch

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write # Grant write permission for pushing to GHCR

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }} # GitHub username
          password: ${{ secrets.GITHUB_TOKEN }} # Automatically generated GITHUB_TOKEN

      - name: Build and push Docker image
        run: |
          IMAGE_NAME=ghcr.io/${{ github.repository }}:latest
          docker build . --tag $IMAGE_NAME
          docker push $IMAGE_NAME
```
- **`permissions: packages: write`**: Explicitly grant `write` permission to the `GITHUB_TOKEN` for pushing images.
- **`secrets.GITHUB_TOKEN`**: This token is automatically provided to GitHub Actions workflows.

### Layer Caching for Pip Installs

Optimizing Docker layer caching for `pip install` is crucial for faster builds and smaller image sizes.

**1. Order Dockerfile Commands Strategically:**
- Place `COPY requirements.txt .` *before* `RUN pip install -r requirements.txt`. This ensures that the `pip install` layer is only rebuilt if `requirements.txt` changes, not if only application code changes.
- `COPY . .` (application code) should come after dependency installation.

**2. Use BuildKit Cache Mounts for `pip`:**
- Leverage Docker BuildKit's `--mount=type=cache,target=/root/.cache/pip` feature. This caches `pip`'s downloaded package wheels externally across builds, preventing re-downloading even if `requirements.txt` changes.
- **Example:**
  ```dockerfile
  # syntax = docker/dockerfile:1.2
  FROM python:3.9-slim-buster
  WORKDIR /app
  COPY requirements.txt .
  RUN --mount=type=cache,target=/root/.cache/pip \
      pip install -r requirements.txt
  COPY . .
  CMD ["python", "your_app.py"]
  ```

**3. Use `--no-cache-dir` with `pip install`:**
- Even when using BuildKit cache mounts, it's best practice to include `--no-cache-dir` with `pip install`. This prevents `pip` from storing its cache *inside the image layer*, which would unnecessarily increase the final image size. The BuildKit cache mount handles persistent external caching.
- **Example:** `pip install --no-cache-dir -r requirements.txt`

**4. Pin Dependency Versions:**
- Always specify exact versions for all dependencies in `requirements.txt` (e.g., `flask==1.1.2`). This ensures reproducible builds and improves caching effectiveness by making the `requirements.txt` file more stable.

**5. Utilize Multi-stage Builds for Runtime Image:**
- Combine with multi-stage builds to create a lean final image. Install dependencies in a `builder` stage, then copy only the installed packages to the final runtime image.
- **Example:**
  ```dockerfile
  # Stage 1: Build dependencies
  FROM python:3.9-slim-buster AS builder
  WORKDIR /app
  COPY requirements.txt .
  RUN --mount=type=cache,target=/root/.cache/pip \
      pip install --no-cache-dir -r requirements.txt

  # Stage 2: Create final runtime image
  FROM python:3.9-slim-buster
  WORKDIR /app
  COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
  COPY . .
  CMD ["python", "your_app.py"]
  ```

**6. Clean Up (if not using `--no-cache-dir` or BuildKit mounts):**
- If external caching or `--no-cache-dir` is not used, manually clean up `pip`'s cache and temporary files after installation: `rm -rf /root/.cache/pip`.

### Dockerfile Patterns for Each Component

A multi-stage Dockerfile is recommended for building a production-ready image for ComfyUI, ensuring a lean final image.

```dockerfile
# syntax=docker/dockerfile:1.4
# Stage 1: Build ComfyUI dependencies and custom nodes
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.10 python3.10-venv python3.10-dev \
        git curl wget unzip zip libgl1 libglib2.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Setup Python virtual environment
RUN python3.10 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install/update pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Clone ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /app/ComfyUI
WORKDIR /app/ComfyUI

# Install ComfyUI core dependencies
# Use a requirements.txt generated from a working ComfyUI setup
# COPY requirements_comfyui.txt .
# RUN pip install --no-cache-dir -r requirements_comfyui.txt

# Placeholder for custom nodes installation (e.g., ComfyUI-ControlNet-Aux)
# RUN git clone https://github.com/Fannovel16/comfyui_controlnet_aux.git custom_nodes/comfyui_controlnet_aux
# WORKDIR custom_nodes/comfyui_controlnet_aux
# COPY requirements_controlnet_aux.txt .
# RUN pip install --no-cache-dir -r requirements_controlnet_aux.txt
# WORKDIR /app/ComfyUI

# Stage 2: Prepare runtime image
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04 AS runner

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install minimal system dependencies required for runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.10 libgl1 libglib2.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy ComfyUI and custom nodes from builder stage
COPY --from=builder /app/ComfyUI /app/ComfyUI

# Create directories for models (if not using /workspace for all)
RUN mkdir -p /app/ComfyUI/models/checkpoints \
             /app/ComfyUI/models/vae \
             /app/ComfyUI/models/controlnet \
             /app/ComfyUI/models/clip_vision \
             /app/ComfyUI/custom_nodes \
             /app/models/VibeVoice \
             /app/models/SteadyDancer \
             /app/models/SCAIL \
             /app/models/ZImageTurbo

# Copy a startup script (e.g., start.sh)
COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

# Placeholder for model downloads (typically handled by start.sh or on-demand)
# The actual large model files (VibeVoice, SteadyDancer, SCAIL, Z-Image Turbo, ControlNet)
# are usually downloaded to /workspace or managed by an external storage system.
# For images, you might pre-download smaller models or placeholder configs.

# Expose ComfyUI port
EXPOSE 8188

ENTRYPOINT ["/usr/local/bin/start.sh"]
CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
```
**Explanation of Sections:**

1.  **`Stage 1: builder`**:
    *   Uses a `*-devel` CUDA image for build tools.
    *   Installs Python and system libraries.
    *   Sets up a Python virtual environment to isolate dependencies.
    *   Clones ComfyUI and installs its core requirements.
    *   Includes placeholders for cloning and installing custom nodes (e.g., `comfyui_controlnet_aux`).

2.  **`Stage 2: runner`**:
    *   Uses a `*-runtime` CUDA image, which is much smaller than `devel` and contains only necessary libraries for execution.
    *   Copies the virtual environment, ComfyUI, and custom nodes from the `builder` stage. This leverages Docker's layer caching and ensures only required files are in the final image.
    *   Creates necessary directories for models, anticipating they might be mounted externally (`/workspace`) or downloaded on first run.
    *   Includes a `start.sh` script to handle dynamic logic like `/workspace` detection and model downloads.
    *   Exposes ComfyUI's default port (8188).
    *   Sets `ENTRYPOINT` to `start.sh` for custom startup logic and `CMD` to run ComfyUI.
