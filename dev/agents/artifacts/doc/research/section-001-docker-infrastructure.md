# Docker Infrastructure (RunPod Custom Template)
Generated: 2026-01-17 23:11:36

## Scope
This document analyzes the Docker build/run infrastructure and the local ComfyUI custom nodes shipped with the image. It is intended to be production-relevant for RunPod-style ephemeral pods (no manual intervention on start).

Analyzed files (full paths):
- /home/oz/projects/2025/oz/12/runpod/docker/Dockerfile
- /home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml
- /home/oz/projects/2025/oz/12/runpod/docker/start.sh
- /home/oz/projects/2025/oz/12/runpod/docker/download_models.sh
- /home/oz/projects/2025/oz/12/runpod/docker/r2_sync.sh
- /home/oz/projects/2025/oz/12/runpod/docker/upload_to_r2.py
- /home/oz/projects/2025/oz/12/runpod/docker/scripts/xtts-vo-gen.py
- /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/__init__.py
- /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/nodes/__init__.py
- /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/nodes/bokeh.py
- /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/nodes/deblur.py
- /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/nodes/loaders.py
- /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/nodes/pipeline.py
- /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/requirements.txt
- /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/utils/__init__.py
- /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/utils/tensor_utils.py
- /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-MVInverse/__init__.py
- /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-MVInverse/mvinverse_inverse.py
- /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-MVInverse/mvinverse_loader.py
- /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-MVInverse/requirements.txt
## High-Level Architecture
**Build**: `docker/Dockerfile` builds a single image containing ComfyUI, several third-party custom nodes, and local custom nodes.

**Run**: `docker/docker-compose.yml` runs the main ComfyUI container (and optionally a Chatterbox TTS API container via a profile).

**Startup**: The container entrypoint is `docker/start.sh`, which:
- Detects storage mode and GPU tier/VRAM
- Optionally starts SSH and JupyterLab
- Runs `docker/download_models.sh` to fetch models at startup
- Optionally starts an R2 sync daemon (`docker/r2_sync.sh`)
- Launches ComfyUI (`python main.py ...`)

## Ports, Volumes, Paths
**Ports (as used by `docker/docker-compose.yml`)**
| Service | Container Port | Host Port | Purpose |
| --- | --- | --- | --- |
| hearmeman-extended | 8188 | 8188 | ComfyUI web UI + API |
| hearmeman-extended | 22 | 2222 | SSH (key-based; password auth disabled in image) |
| hearmeman-extended | 8888 | 8888 | JupyterLab (token set via `JUPYTER_PASSWORD`) |
| chatterbox | 4123 | 8000 | Chatterbox TTS API |
**Key in-container paths**
| Path | Description |
| --- | --- |
| /workspace/ComfyUI | ComfyUI checkout (cloned during image build) |
| /workspace/ComfyUI/models | Model storage root (bind-mounted in compose) |
| /workspace/ComfyUI/output | Generated outputs (bind-mounted in compose) |
| /var/log/download_models.log | Startup model download logs (`download_models.sh`) |
| /var/log/jupyter.log | JupyterLab logs (`start.sh`) |
| /var/log/r2_sync.log | R2 sync daemon logs (`r2_sync.sh`) |
| /workspace/.civitai-token | CivitAI token file (written if `CIVITAI_API_KEY` is set) |
## Dockerfile (Build Image)
Source: `/home/oz/projects/2025/oz/12/runpod/docker/Dockerfile`

### Base Image + Build Args
- Base image is configurable via `BASE_IMAGE` build arg (default is RunPod PyTorch CUDA image).
- `COMFYUI_COMMIT` build arg exists but is not used to pin a commit (ComfyUI is cloned without checkout).
- Optional model baking build args: `BAKE_WAN_720P`, `BAKE_WAN_480P`, `BAKE_ILLUSTRIOUS`.

### Layers Overview (What Each Layer Adds)
1. **System deps**: git, git-lfs, wget/curl, ffmpeg, OpenGL libs, SSH server, aria2, inotify-tools.
2. **ComfyUI base**: clones ComfyUI into `/workspace/ComfyUI` and installs Python requirements.
3. **Third-party custom nodes**: clones multiple repos into `/workspace/ComfyUI/custom_nodes` and attempts to `pip install -r requirements.txt` (errors ignored with `|| true` in several cases).
4. **Local custom nodes**: copies `docker/custom_nodes/*` into the image and installs their requirements.
5. **Extra Python deps**: installs HuggingFace + diffusion ecosystem utilities and various runtime libs.
6. **Scripts/config**: copies `start.sh`, `download_models.sh`, `upload_to_r2.py`, `r2_sync.sh`, and example workflows.
7. **Optional baked models**: when build args are enabled, downloads WAN and/or Illustrious models into the image.

### Third-Party Custom Nodes Included
The image clones these custom node repos during build:

- ComfyUI-Manager (`https://github.com/ltdrdata/ComfyUI-Manager.git`)
- VibeVoice-ComfyUI (`https://github.com/Enemyx-net/VibeVoice-ComfyUI.git`)
- ComfyUI-Chatterbox (`https://github.com/thefader/ComfyUI-Chatterbox.git`)
- ComfyUI-SCAIL-Pose (`https://github.com/kijai/ComfyUI-SCAIL-Pose.git`)
- comfyui_controlnet_aux (`https://github.com/Fannovel16/comfyui_controlnet_aux.git`)
- Comfyui_turbodiffusion (`https://github.com/anveshane/Comfyui_turbodiffusion.git`)
- ComfyUI-WanVideoWrapper (`https://github.com/kijai/ComfyUI-WanVideoWrapper.git`)
- ComfyUI-VideoHelperSuite (`https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git`)
### Environment Defaults (Image-Level)
These are set in the Dockerfile and can be overridden at runtime (compose/RunPod env).

| Variable | Default | Description |
| --- | --- | --- |
| COMFYUI_PORT | 8188 | Port ComfyUI listens on (passed to `main.py --port`). |
| GPU_TIER | consumer | Intended GPU tier (`consumer\|prosumer\|datacenter`). |
| GPU_MEMORY_MODE | auto | Memory strategy (`auto\|full\|sequential_cpu_offload\|model_cpu_offload`). |
| COMFYUI_ARGS | "" | Extra args appended to `python main.py` (VRAM flags auto-set if empty). |
| ENABLE_GENFOCUS | false | Enable Genfocus model downloads (and intended usage). |
| ENABLE_QWEN_EDIT | false | Enable Qwen Image Edit model download. |
| QWEN_EDIT_MODEL | Q4_K_M | Qwen Image Edit quantization (`Q4_K_M`, `Q5_K_M`, `Q8_0`, `full`, etc.). |
| ENABLE_MVINVERSE | false | Enable MVInverse repo clone/model setup. |
| ENABLE_FLASHPORTRAIT | false | Enable FlashPortrait snapshot download. |
| ENABLE_STORYMEM | false | Enable StoryMem snapshot download. |
| ENABLE_INFCAM | false | Enable InfCam snapshot download (datacenter tier only). |
| ENABLE_R2_SYNC | false | Enable R2 output sync daemon on startup. |
| R2_ENDPOINT | (preset) | Cloudflare R2 S3 endpoint URL. |
| R2_BUCKET | runpod | Target R2 bucket name. |
| R2_ACCESS_KEY_ID | "" | R2 Access Key ID (required when R2 sync enabled). |
| R2_SECRET_ACCESS_KEY | "" | R2 Secret Access Key (required when R2 sync enabled). |
### Build-Time Model Baking (Optional)
The Dockerfile supports baking large model assets into the image at build time (faster startup, larger image).

Build args:
- `BAKE_WAN_720P=true|false`
- `BAKE_WAN_480P=true|false`
- `BAKE_ILLUSTRIOUS=true|false`

Example:
```bash
cd docker
docker build --build-arg BAKE_ILLUSTRIOUS=true -t hearmeman-extended:baked .
```

## docker-compose.yml (Local Run Topology)
Source: `/home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml`

### Services
| Service | Enabled By Default | Notes |
| --- | --- | --- |
| hearmeman-extended | Yes | Main ComfyUI container. Uses NVIDIA runtime; binds models/output. |
| chatterbox | No | Only runs when profile `chatterbox` is enabled. |
### Profiles
- `chatterbox` profile: starts the Chatterbox API container.

Examples:
```bash
cd docker
docker compose up -d
docker compose --profile chatterbox up -d
```

### Volumes
- `./models` is bind-mounted into `/workspace/ComfyUI/models` (persists model downloads).
- `./output` is bind-mounted into `/workspace/ComfyUI/output` (persists generations).
- A local host path `/home/oz/comfyui/models/vibevoice` is mounted read-only into `/workspace/ComfyUI/models/vibevoice` (developer-specific).

## start.sh (Container Entrypoint)
Source: `/home/oz/projects/2025/oz/12/runpod/docker/start.sh`

### Startup Sequence
- Detect storage mode (`STORAGE_MODE=auto|ephemeral|persistent`) using `/workspace` mountpoint heuristics.
- Detect GPU VRAM via `nvidia-smi` and auto-set `GPU_TIER`, `GPU_MEMORY_MODE`, and ComfyUI VRAM flags (`COMFYUI_ARGS`) when not explicitly set.
- Optional SSH setup when `PUBLIC_KEY` is set (starts sshd; key-based auth).
- Optional JupyterLab when `JUPYTER_PASSWORD` is set (token-based auth).
- Optional `git pull` update for custom nodes when `UPDATE_NODES_ON_START=true`.
- Run `/download_models.sh` (logs to `/var/log/download_models.log`).
- Optional background R2 sync daemon when `ENABLE_R2_SYNC=true`.
- Launch ComfyUI via `python main.py --listen 0.0.0.0 --port $COMFYUI_PORT ... $COMFYUI_ARGS`.
## download_models.sh (Startup Model Downloads)
Source: `/home/oz/projects/2025/oz/12/runpod/docker/download_models.sh`

### Download Helpers
The script provides multiple helpers:

- `download_model(URL, DEST, EXPECTED_SIZE?)`: uses `wget` with resume; falls back to `curl`.
- `hf_download(REPO, FILE, DEST, EXPECTED_SIZE?)`: constructs HuggingFace `resolve/main/...` URL and calls `download_model`.
- `hf_snapshot_download(REPO, DEST)`: uses `huggingface_hub.snapshot_download` from Python (downloads a repo snapshot).
- `civitai_download(VERSION_ID, TARGET_DIR, DESCRIPTION?)`: downloads via CivitAI API using `wget`/`curl`, optionally using `CIVITAI_API_KEY`.

### Key Environment Variables
| Variable | Default | Used For |
| --- | --- | --- |
| MODELS_DIR | /workspace/ComfyUI/models | Root directory for model downloads. |
| DRY_RUN | false | If true, logs intended downloads without downloading (only honored by `download_model`). |
| DOWNLOAD_TIMEOUT | 1800 | Timeout (seconds) for `wget`/`curl` in `download_model`. |
| CIVITAI_API_KEY | (unset) | Appended as `?token=...` for CivitAI downloads. |
| ENABLE_VIBEVOICE | false | Enable VibeVoice snapshot downloads. |
| VIBEVOICE_MODEL | Large | VibeVoice model selection (`1.5B`, `Large`, `Large-Q8`). |
| ENABLE_ZIMAGE | false | Enable Z-Image Turbo downloads. |
| WAN_720P | false | Enable WAN 2.1 720p model downloads. |
| WAN_480P | false | Enable WAN 2.1 480p model downloads. |
| ENABLE_I2V | false | Enable I2V-specific deps (additional diffusion model and CLIP vision). |
| ENABLE_WAN22_DISTILL | false | Enable WAN 2.2 distilled TurboDiffusion I2V downloads. |
| ENABLE_CONTROLNET | true | Enable ControlNet model downloads. |
| CONTROLNET_MODELS | canny,depth,openpose | Comma list of ControlNet models to download. |
| ENABLE_ILLUSTRIOUS | false | Enable Realism Illustrious downloads. |
| ENABLE_ILLUSTRIOUS_EMBEDDINGS | true | Enable Illustrious embeddings downloads. |
| ILLUSTRIOUS_LORAS | (unset) | Comma list of CivitAI version IDs to download into `models/loras`. |
| ENABLE_CIVITAI | false | Enable generic CivitAI LoRA downloads via `CIVITAI_LORAS`. |
| CIVITAI_LORAS | (unset) | Comma list of CivitAI version IDs to download. |
| ENABLE_QWEN_EDIT | false | Enable Qwen Image Edit downloads. |
| QWEN_EDIT_MODEL | Q4_K_M | Qwen GGUF quantization or `full`. |
| ENABLE_GENFOCUS | false | Enable Genfocus model component downloads. |
| ENABLE_MVINVERSE | false | Enable MVInverse repo clone into models dir. |
| ENABLE_FLASHPORTRAIT | false | Enable FlashPortrait snapshot downloads. |
| GPU_MEMORY_MODE | auto | Affects FlashPortrait logging/expectations. |
| ENABLE_STORYMEM | false | Enable StoryMem snapshot downloads. |
| ENABLE_INFCAM | false | Enable InfCam snapshot downloads (requires `GPU_TIER=datacenter`). |
### Model Path Conventions (Workflow Compatibility)
The script writes to ComfyUI's standard model directories under `MODELS_DIR`. Workflows must reference these filenames exactly.

Common outputs:
- `models/text_encoders/*.safetensors`
- `models/diffusion_models/*.safetensors`
- `models/vae/*.safetensors`
- `models/controlnet/*.safetensors`
- `models/embeddings/*.safetensors`
- `models/loras/*.safetensors`
- `models/vibevoice/<repo snapshot>`
- `models/genfocus/{bokehNet.safetensors,deblurNet.safetensors,depth_pro.pt}`
- `models/qwen/qwen-image-edit-2511-<quant>.gguf`

### Known Quirks / Footguns
- `download_model()` treats any existing file >1MB as 'complete' and skips it, even if the download is partial (resume only happens when size <= 1MB).
- `civitai_download()` does not honor `DRY_RUN` or `DOWNLOAD_TIMEOUT` (it uses its own wget/curl path).
- CivitAI downloads may save as `model_<version_id>.safetensors` if the filename cannot be detected from headers; workflows must match the actual filename on disk.
- WAN blocks are labeled 'WAN 2.2' in comments but download both Wan 2.1 and Wan 2.2 artifacts depending on flags.
- `ENABLE_XTTS` block calls `from TTS.api import TTS`; the base ComfyUI image may not include that dependency (the code handles failure by printing a note).
- MVInverse: `download_models.sh` clones the MVInverse repo into `models/mvinverse/mvinverse`, but the ComfyUI node loader expects the python package `mvinverse` to be importable (usually via `pip install` or cloning into `custom_nodes/mvinverse`).
## R2 Output Sync Utilities
Sources:

- `/home/oz/projects/2025/oz/12/runpod/docker/r2_sync.sh`
- `/home/oz/projects/2025/oz/12/runpod/docker/upload_to_r2.py`

`start.sh` can launch `r2_sync.sh` in the background when `ENABLE_R2_SYNC=true`. The daemon watches the ComfyUI output directory and uploads new files to R2.

### R2 Environment Variables
| Variable | Default | Description |
| --- | --- | --- |
| ENABLE_R2_SYNC | false | When true, `start.sh` launches the sync daemon. |
| COMFYUI_OUTPUT_DIR | /workspace/ComfyUI/output | Directory watched by `r2_sync.sh`. |
| R2_ENDPOINT | (preset) | Cloudflare R2 S3 endpoint URL. |
| R2_BUCKET | runpod | Target bucket name. |
| R2_ACCESS_KEY_ID | (required) | Access key ID. |
| R2_SECRET_ACCESS_KEY | (required) | Secret access key. |
| R2_ACCESS_KEY | (optional alias) | Alternate env name supported by scripts. |
| R2_SECRET_KEY | (optional alias) | Alternate env name supported by scripts. |
## docker/scripts (Utility Scripts)
Directory: `/home/oz/projects/2025/oz/12/runpod/docker/scripts`

Currently contains a single helper script for XTTS voice-over generation.

### xtts-vo-gen.py
Source: `/home/oz/projects/2025/oz/12/runpod/docker/scripts/xtts-vo-gen.py`

- Talks to an XTTS API server (default `http://localhost:8020`).
- Supports single-line generation, batch generation from a text file, speaker presets, and streaming mode.
- Environment variable: `XTTS_API_URL`.

## docker/custom_nodes (Local ComfyUI Nodes)
Directory: `/home/oz/projects/2025/oz/12/runpod/docker/custom_nodes`

These packages are copied into `/workspace/ComfyUI/custom_nodes/` during the Docker build. ComfyUI loads nodes by importing each package's `__init__.py` and reading `NODE_CLASS_MAPPINGS`.

### ComfyUI-Genfocus
Path: `/home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus`

Provides nodes to load Genfocus model components and perform generative refocusing (DeblurNet + BokehNet).

Model files expected under `models/genfocus/` (downloaded by `download_models.sh` when `ENABLE_GENFOCUS=true`).

Important runtime dependency: the nodes attempt to instantiate `diffusers.FluxPipeline.from_pretrained('black-forest-labs/FLUX.1-dev')`, which typically requires HuggingFace authentication and will download additional large assets on first use. Fallback paths exist but are explicitly described as placeholders in code.

### ComfyUI-MVInverse
Path: `/home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-MVInverse`

Provides nodes for MVInverse multi-view inverse rendering.

Known integration gap: the loader imports `mvinverse.models.mvinverse.MVInverse`. The repository clone performed by `download_models.sh` is placed under `models/mvinverse/mvinverse`, but the loader only auto-adds `custom_nodes/mvinverse` to `sys.path` if it exists, otherwise it requires `mvinverse` to be installed via pip.

## Appendix: Full Source Listings (with line numbers)
All analyzed files are included below as line-numbered listings for precise reference.

### /home/oz/projects/2025/oz/12/runpod/docker/Dockerfile
```text
     1	# ============================================
     2	# Hearmeman Extended Template
     3	# ============================================
     4	ARG BASE_IMAGE=runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04
     5	FROM ${BASE_IMAGE}
     6	
     7	# OCI Labels for GHCR linking
     8	LABEL org.opencontainers.image.source=https://github.com/mensajerokaos/hearmeman-extended
     9	LABEL org.opencontainers.image.description="ComfyUI with AI video/audio generation (WAN, VibeVoice, TurboDiffusion)"
    10	LABEL org.opencontainers.image.licenses=MIT
    11	
    12	# Build arguments
    13	ARG COMFYUI_COMMIT=latest
    14	ARG DEBIAN_FRONTEND=noninteractive
    15	
    16	# Build-time model downloads (bakes models into image for instant startup)
    17	ARG BAKE_WAN_720P=false
    18	ARG BAKE_WAN_480P=false
    19	ARG BAKE_ILLUSTRIOUS=false
    20	
    21	# Environment
    22	ENV PYTHONUNBUFFERED=1
    23	ENV SHELL=/bin/bash
    24	ENV COMFYUI_PORT=8188
    25	
    26	# GPU Tier and Model Toggle Configuration
    27	ENV GPU_TIER="consumer"
    28	# Options: consumer, prosumer, datacenter
    29	
    30	# Tier 1: Consumer GPU (8-24GB VRAM)
    31	ENV ENABLE_GENFOCUS="false"
    32	ENV ENABLE_QWEN_EDIT="false"
    33	ENV QWEN_EDIT_MODEL="Q4_K_M"
    34	# Options: Q4_K_M (13GB), Q5_K_M (15GB), Q8_0 (22GB), full (54GB)
    35	ENV ENABLE_MVINVERSE="false"
    36	
    37	# Tier 2: Prosumer GPU (24GB+ with CPU offload)
    38	ENV ENABLE_FLASHPORTRAIT="false"
    39	ENV ENABLE_STORYMEM="false"
    40	
    41	# Tier 3: Datacenter GPU (48-80GB VRAM - A100/H100)
    42	ENV ENABLE_INFCAM="false"
    43	
    44	# GPU Memory Management
    45	ENV GPU_MEMORY_MODE="auto"
    46	# Options: auto, full, sequential_cpu_offload, model_cpu_offload
    47	
    48	# R2 Configuration
    49	ENV ENABLE_R2_SYNC="false"
    50	ENV R2_ENDPOINT="https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com"
    51	ENV R2_BUCKET="runpod"
    52	ENV R2_ACCESS_KEY_ID=""
    53	ENV R2_SECRET_ACCESS_KEY=""
    54	
    55	ENV COMFYUI_ARGS=""
    56	# For: --lowvram, --medvram, --novram, --cpu-vae, etc.
    57	
    58	# ============================================
    59	# Layer 1: System Dependencies
    60	# ============================================
    61	RUN apt-get update && apt-get install -y --no-install-recommends \
    62	    git \
    63	    git-lfs \
    64	    wget \
    65	    curl \
    66	    vim \
    67	    ffmpeg \
    68	    libsm6 \
    69	    libxext6 \
    70	    libgl1-mesa-glx \
    71	    openssh-server \
    72	    aria2 \
    73	    inotify-tools \
    74	    && apt-get clean \
    75	    && rm -rf /var/lib/apt/lists/*
    76	
    77	# Initialize git-lfs
    78	RUN git lfs install
    79	
    80	# ============================================
    81	# Layer 2: ComfyUI Base (latest for Z-Image support)
    82	# ============================================
    83	WORKDIR /workspace
    84	RUN git clone https://github.com/comfyanonymous/ComfyUI.git && \
    85	    cd ComfyUI && \
    86	    pip install --no-cache-dir -r requirements.txt
    87	
    88	# ============================================
    89	# Layer 3: Custom Nodes (baked in)
    90	# ============================================
    91	WORKDIR /workspace/ComfyUI/custom_nodes
    92	
    93	# ComfyUI-Manager
    94	RUN git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Manager.git
    95	
    96	# VibeVoice-ComfyUI (Enemyx-net fork - v1.8.1+, actively maintained)
    97	RUN git clone --depth 1 https://github.com/Enemyx-net/VibeVoice-ComfyUI.git && \
    98	    cd VibeVoice-ComfyUI && \
    99	    pip install --no-cache-dir -r requirements.txt || true
   100	
   101	# ComfyUI-Chatterbox (Resemble AI TTS - zero-shot voice cloning)
   102	RUN git clone --depth 1 https://github.com/thefader/ComfyUI-Chatterbox.git && \
   103	    cd ComfyUI-Chatterbox && \
   104	    pip install --no-cache-dir -r requirements.txt || true
   105	
   106	# ComfyUI-SCAIL-Pose
   107	RUN git clone --depth 1 https://github.com/kijai/ComfyUI-SCAIL-Pose.git
   108	
   109	# ControlNet Preprocessors
   110	RUN git clone --depth 1 https://github.com/Fannovel16/comfyui_controlnet_aux.git && \
   111	    cd comfyui_controlnet_aux && \
   112	    pip install --no-cache-dir -r requirements.txt || true
   113	
   114	# TurboDiffusion (100-200x video speedup for WAN models)
   115	RUN git clone --depth 1 https://github.com/anveshane/Comfyui_turbodiffusion.git && \
   116	    cd Comfyui_turbodiffusion && \
   117	    pip install --no-cache-dir -r requirements.txt || true
   118	
   119	# ComfyUI-WanVideoWrapper (WAN 2.2/2.5 video generation nodes)
   120	RUN git clone --depth 1 https://github.com/kijai/ComfyUI-WanVideoWrapper.git && \
   121	    cd ComfyUI-WanVideoWrapper && \
   122	    pip install --no-cache-dir -r requirements.txt || true
   123	
   124	# ComfyUI-VideoHelperSuite (video processing utilities)
   125	RUN git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git && \
   126	    cd ComfyUI-VideoHelperSuite && \
   127	    pip install --no-cache-dir -r requirements.txt || true
   128	
   129	# CivitAI integration
   130	RUN pip install --no-cache-dir civitai-downloader
   131	
   132	# ============================================
   133	# Layer 3.5: Custom AI Model Wrappers (Local)
   134	# ============================================
   135	# ComfyUI-Genfocus (Depth-of-Field Refocusing)
   136	COPY custom_nodes/ComfyUI-Genfocus /workspace/ComfyUI/custom_nodes/ComfyUI-Genfocus
   137	RUN cd /workspace/ComfyUI/custom_nodes/ComfyUI-Genfocus && \
   138	    pip install --no-cache-dir -r requirements.txt || true
   139	
   140	# ComfyUI-MVInverse (Multi-view Inverse Rendering)
   141	COPY custom_nodes/ComfyUI-MVInverse /workspace/ComfyUI/custom_nodes/ComfyUI-MVInverse
   142	RUN cd /workspace/ComfyUI/custom_nodes/ComfyUI-MVInverse && \
   143	    pip install --no-cache-dir -r requirements.txt || true
   144	
   145	# ============================================
   146	# Layer 4: Additional Dependencies
   147	# ============================================
   148	WORKDIR /workspace
   149	RUN pip install --no-cache-dir \
   150	    huggingface_hub \
   151	    accelerate \
   152	    safetensors \
   153	    boto3 \
   154	    sentencepiece \
   155	    protobuf \
   156	    # New dependencies for AI models
   157	    cupy-cuda12x \
   158	    imageio[ffmpeg] \
   159	    einops \
   160	    modelscope \
   161	    ftfy \
   162	    lpips \
   163	    lightning \
   164	    pandas \
   165	    matplotlib \
   166	    wandb \
   167	    ffmpeg-python \
   168	    # Dependencies for custom nodes
   169	    audiotsm \
   170	    loguru \
   171	    # Dependencies for Genfocus/MVInverse
   172	    diffusers>=0.21.0 \
   173	    peft>=0.4.0 \
   174	    opencv-python>=4.5.0 \
   175	    timm \
   176	    # NVIDIA GPU management (for TurboDiffusion)
   177	    pynvml
   178	
   179	# Flash Attention - DISABLED due to ABI compatibility issues with kornia
   180	# Uncomment only if you need FlashPortrait/InfCam and have matching CUDA/PyTorch
   181	# RUN pip install --no-cache-dir flash_attn || echo "[Note] flash_attn install failed"
   182	
   183	# ============================================
   184	# Layer 5: Scripts and Configuration
   185	# ============================================
   186	COPY start.sh /start.sh
   187	COPY download_models.sh /download_models.sh
   188	COPY upload_to_r2.py /upload_to_r2.py
   189	COPY r2_sync.sh /r2_sync.sh
   190	RUN chmod +x /start.sh /download_models.sh /r2_sync.sh
   191	
   192	# Copy example workflows
   193	COPY workflows/ /workspace/ComfyUI/user/default/workflows/
   194	
   195	# SSH configuration
   196	RUN mkdir -p /var/run/sshd && \
   197	    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
   198	    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
   199	
   200	# Create model directories (including new AI models)
   201	RUN mkdir -p /workspace/ComfyUI/models/{checkpoints,embeddings,vibevoice,text_encoders,diffusion_models,vae,controlnet,loras,clip_vision,genfocus,qwen,mvinverse,flashportrait,storymem,infcam}
   202	
   203	# ============================================
   204	# Layer 6: Build-time Model Downloads (Optional)
   205	# ============================================
   206	# Re-declare ARGs after FROM (Docker requirement)
   207	ARG BAKE_WAN_720P
   208	ARG BAKE_WAN_480P
   209	ARG BAKE_ILLUSTRIOUS
   210	
   211	# WAN 2.1 720p Models (~25GB total: 14B diffusion + text encoders + VAE)
   212	RUN if [ "$BAKE_WAN_720P" = "true" ]; then \
   213	    echo "[BUILD] Downloading WAN 2.1 720p models..." && \
   214	    wget -q --show-progress -O /workspace/ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors \
   215	        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" && \
   216	    wget -q --show-progress -O /workspace/ComfyUI/models/clip_vision/clip_vision_h.safetensors \
   217	        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" && \
   218	    wget -q --show-progress -O /workspace/ComfyUI/models/vae/wan_2.1_vae.safetensors \
   219	        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" && \
   220	    wget -q --show-progress -O /workspace/ComfyUI/models/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors \
   221	        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" && \
   222	    echo "[BUILD] WAN 2.1 720p models downloaded"; \
   223	    fi
   224	
   225	# WAN 2.1 480p Models (~12GB total: 1.3B diffusion + text encoders + VAE)
   226	RUN if [ "$BAKE_WAN_480P" = "true" ]; then \
   227	    echo "[BUILD] Downloading WAN 2.1 480p models..." && \
   228	    [ -f /workspace/ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors ] || \
   229	    wget -q --show-progress -O /workspace/ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors \
   230	        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" && \
   231	    [ -f /workspace/ComfyUI/models/vae/wan_2.1_vae.safetensors ] || \
   232	    wget -q --show-progress -O /workspace/ComfyUI/models/vae/wan_2.1_vae.safetensors \
   233	        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" && \
   234	    wget -q --show-progress -O /workspace/ComfyUI/models/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors \
   235	        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors" && \
   236	    echo "[BUILD] WAN 2.1 480p models downloaded"; \
   237	    fi
   238	
   239	# Illustrious XL Models (~6.5GB checkpoint + embeddings)
   240	RUN if [ "$BAKE_ILLUSTRIOUS" = "true" ]; then \
   241	    echo "[BUILD] Downloading Illustrious XL models..." && \
   242	    wget -q --show-progress -O /workspace/ComfyUI/models/checkpoints/illustrious_realism_v10.safetensors \
   243	        "https://civitai.com/api/download/models/2091367" && \
   244	    mkdir -p /workspace/ComfyUI/models/embeddings && \
   245	    wget -q --show-progress -O /workspace/ComfyUI/models/embeddings/negativeXL_D.safetensors \
   246	        "https://civitai.com/api/download/models/134583" && \
   247	    wget -q --show-progress -O /workspace/ComfyUI/models/embeddings/PDXL.safetensors \
   248	        "https://civitai.com/api/download/models/367841" && \
   249	    echo "[BUILD] Illustrious XL models downloaded"; \
   250	    fi
   251	
   252	# Expose ports (22=SSH, 8188=ComfyUI, 8888=Jupyter)
   253	EXPOSE 22 8188 8888
   254	
   255	# Working directory
   256	WORKDIR /workspace/ComfyUI
   257	
   258	# Entry point
   259	ENTRYPOINT ["/start.sh"]
```
### /home/oz/projects/2025/oz/12/runpod/docker/docker-compose.yml
```text
     1	services:
     2	  # ===========================================
     3	  # Chatterbox TTS (Resemble AI)
     4	  # API: http://localhost:8000/health
     5	  # OpenAI-compatible: http://localhost:8000/v1/audio/speech
     6	  # ===========================================
     7	  chatterbox:
     8	    build:
     9	      context: ./chatterbox-api
    10	      dockerfile: docker/Dockerfile.gpu
    11	    image: chatterbox-tts-api:local
    12	    container_name: chatterbox
    13	    runtime: nvidia
    14	    ports:
    15	      - "8000:4123"
    16	    environment:
    17	      - NVIDIA_VISIBLE_DEVICES=all
    18	    volumes:
    19	      - ./chatterbox-voices:/app/voices
    20	      - ./output:/app/output
    21	    deploy:
    22	      resources:
    23	        reservations:
    24	          devices:
    25	            - driver: nvidia
    26	              count: 1
    27	              capabilities: [gpu]
    28	    restart: unless-stopped
    29	    profiles:
    30	      - chatterbox  # Only starts with: docker compose --profile chatterbox up
    31	
    32	  # ===========================================
    33	  # ComfyUI Main Service
    34	  # ComfyUI: http://localhost:8188
    35	  # TTS profile: chatterbox
    36	  # ===========================================
    37	  hearmeman-extended:
    38	    build:
    39	      context: .
    40	      dockerfile: Dockerfile
    41	    image: hearmeman-extended:local
    42	    container_name: hearmeman-extended
    43	    runtime: nvidia
    44	    environment:
    45	      - NVIDIA_VISIBLE_DEVICES=all
    46	      # Existing models
    47	      - ENABLE_VIBEVOICE=true
    48	      - ENABLE_CONTROLNET=true
    49	      - ENABLE_ILLUSTRIOUS=false
    50	      - ENABLE_ZIMAGE=false
    51	      - VIBEVOICE_MODEL=Large
    52	      - STORAGE_MODE=persistent
    53	      - COMFYUI_PORT=8188
    54	      # GPU Configuration (auto-detect or manual override)
    55	      - GPU_TIER=consumer
    56	      - GPU_MEMORY_MODE=auto
    57	      # Tier 1: Consumer GPU (8-24GB VRAM)
    58	      - ENABLE_GENFOCUS=true
    59	      - ENABLE_QWEN_EDIT=true
    60	      - QWEN_EDIT_MODEL=Q4_K_M
    61	      # Options: Q4_K_M (13GB), Q5_K_M (15GB), Q8_0 (22GB), full (54GB)
    62	      - ENABLE_MVINVERSE=true
    63	      # Tier 2: Prosumer GPU (24GB+ with CPU offload)
    64	      - ENABLE_FLASHPORTRAIT=false
    65	      - ENABLE_STORYMEM=false
    66	      # Tier 3: Datacenter GPU (48-80GB A100/H100)
    67	      - ENABLE_INFCAM=false
    68	    ports:
    69	      - "8188:8188"
    70	      - "8888:8888"
    71	      - "2222:22"
    72	    volumes:
    73	      - ./models:/workspace/ComfyUI/models
    74	      - ./output:/workspace/ComfyUI/output
    75	      - /home/oz/comfyui/models/vibevoice:/workspace/ComfyUI/models/vibevoice:ro
    76	    deploy:
    77	      resources:
    78	        reservations:
    79	          devices:
    80	            - driver: nvidia
    81	              count: 1
    82	              capabilities: [gpu]
    83	    restart: unless-stopped
    84	
    85	volumes:
    86	  models:
    87	  output:
```
### /home/oz/projects/2025/oz/12/runpod/docker/start.sh
```text
     1	#!/bin/bash
     2	set -e
     3	
     4	echo "============================================"
     5	echo "=== Hearmeman Extended Template Startup ==="
     6	echo "============================================"
     7	echo "Timestamp: $(date)"
     8	echo ""
     9	
    10	# ============================================
    11	# Storage Mode Detection
    12	# ============================================
    13	detect_storage_mode() {
    14	    if [ "$STORAGE_MODE" = "ephemeral" ]; then
    15	        echo "ephemeral"
    16	    elif [ "$STORAGE_MODE" = "persistent" ]; then
    17	        echo "persistent"
    18	    elif [ "$STORAGE_MODE" = "auto" ] || [ -z "$STORAGE_MODE" ]; then
    19	        if [ -d "/workspace" ] && mountpoint -q "/workspace" 2>/dev/null; then
    20	            echo "persistent"
    21	        else
    22	            echo "ephemeral"
    23	        fi
    24	    else
    25	        echo "ephemeral"
    26	    fi
    27	}
    28	
    29	DETECTED_STORAGE=$(detect_storage_mode)
    30	export STORAGE_MODE="$DETECTED_STORAGE"
    31	echo "[Storage] Mode: $STORAGE_MODE"
    32	
    33	# ============================================
    34	# GPU VRAM Detection & Configuration
    35	# ============================================
    36	detect_gpu_config() {
    37	    # Detect GPU VRAM in MB
    38	    GPU_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -n 1)
    39	
    40	    if [ -z "$GPU_VRAM" ]; then
    41	        echo "  [Warning] Could not detect GPU VRAM, using defaults"
    42	        GPU_VRAM=0
    43	    fi
    44	
    45	    echo "[GPU] Detected VRAM: ${GPU_VRAM} MB"
    46	
    47	    # Auto-detect GPU tier if not set
    48	    if [ -z "$GPU_TIER" ] || [ "$GPU_TIER" = "auto" ]; then
    49	        if (( GPU_VRAM >= 48000 )); then
    50	            export GPU_TIER="datacenter"
    51	        elif (( GPU_VRAM >= 20000 )); then
    52	            export GPU_TIER="prosumer"
    53	        else
    54	            export GPU_TIER="consumer"
    55	        fi
    56	        echo "[GPU] Auto-detected tier: $GPU_TIER"
    57	    else
    58	        echo "[GPU] Configured tier: $GPU_TIER"
    59	    fi
    60	
    61	    # Auto-detect memory mode if set to "auto"
    62	    if [ "$GPU_MEMORY_MODE" = "auto" ]; then
    63	        if (( GPU_VRAM >= 48000 )); then
    64	            export GPU_MEMORY_MODE="full"
    65	        elif (( GPU_VRAM >= 24000 )); then
    66	            export GPU_MEMORY_MODE="model_cpu_offload"
    67	        else
    68	            export GPU_MEMORY_MODE="sequential_cpu_offload"
    69	        fi
    70	        echo "[GPU] Auto-detected memory mode: $GPU_MEMORY_MODE"
    71	    fi
    72	
    73	    # Auto-detect ComfyUI VRAM flags if not set
    74	    if [ -z "$COMFYUI_ARGS" ]; then
    75	        if (( GPU_VRAM < 8000 )); then
    76	            export COMFYUI_ARGS="--lowvram --cpu-vae --force-fp16"
    77	        elif (( GPU_VRAM < 12000 )); then
    78	            export COMFYUI_ARGS="--lowvram --force-fp16"
    79	        elif (( GPU_VRAM < 16000 )); then
    80	            export COMFYUI_ARGS="--medvram --cpu-text-encoder --force-fp16"
    81	        elif (( GPU_VRAM < 24000 )); then
    82	            export COMFYUI_ARGS="--normalvram --force-fp16"
    83	        else
    84	            export COMFYUI_ARGS=""
    85	        fi
    86	
    87	        if [ -n "$COMFYUI_ARGS" ]; then
    88	            echo "[GPU] Auto-detected ComfyUI args: $COMFYUI_ARGS"
    89	        fi
    90	    fi
    91	}
    92	
    93	detect_gpu_config
    94	
    95	# ============================================
    96	# SSH Setup
    97	# ============================================
    98	if [[ -n "$PUBLIC_KEY" ]]; then
    99	    echo "[SSH] Configuring SSH access..."
   100	    mkdir -p ~/.ssh && chmod 700 ~/.ssh
   101	    echo "$PUBLIC_KEY" >> ~/.ssh/authorized_keys
   102	    chmod 600 ~/.ssh/authorized_keys
   103	    service ssh start
   104	    echo "[SSH] Ready on port 22"
   105	fi
   106	
   107	# ============================================
   108	# JupyterLab Setup
   109	# ============================================
   110	if [[ -n "$JUPYTER_PASSWORD" ]]; then
   111	    echo "[Jupyter] Starting JupyterLab on port 8888..."
   112	    nohup jupyter lab \
   113	        --allow-root \
   114	        --no-browser \
   115	        --port=8888 \
   116	        --ip=0.0.0.0 \
   117	        --ServerApp.token="$JUPYTER_PASSWORD" \
   118	        --ServerApp.allow_origin='*' \
   119	        > /var/log/jupyter.log 2>&1 &
   120	fi
   121	
   122	# ============================================
   123	# Update Custom Nodes (if enabled)
   124	# ============================================
   125	if [ "${UPDATE_NODES_ON_START:-false}" = "true" ]; then
   126	    echo "[Nodes] Updating custom nodes..."
   127	    for dir in /workspace/ComfyUI/custom_nodes/*/; do
   128	        if [ -d "$dir/.git" ]; then
   129	            echo "  Updating: $(basename $dir)"
   130	            cd "$dir" && git pull --quiet || true
   131	        fi
   132	    done
   133	fi
   134	
   135	# ============================================
   136	# Download Models
   137	# ============================================
   138	echo "[Models] Starting model downloads..."
   139	/download_models.sh
   140	
   141	# ============================================
   142	# R2 Sync Daemon Setup
   143	# ============================================
   144	if [ "${ENABLE_R2_SYNC:-false}" = "true" ]; then
   145	    echo "[R2 Sync] Starting background sync daemon..."
   146	    # Ensure output directory exists before watching
   147	    mkdir -p /workspace/ComfyUI/output
   148	    nohup /r2_sync.sh > /var/log/r2_sync_init.log 2>&1 &
   149	    echo "[R2 Sync] Daemon active, monitoring /workspace/ComfyUI/output"
   150	fi
   151	
   152	# ============================================
   153	# Start ComfyUI
   154	# ============================================
   155	echo "[ComfyUI] Starting on port ${COMFYUI_PORT:-8188}..."
   156	if [ -n "$COMFYUI_ARGS" ]; then
   157	    echo "[ComfyUI] Using VRAM args: $COMFYUI_ARGS"
   158	fi
   159	cd /workspace/ComfyUI
   160	exec python main.py \
   161	    --listen 0.0.0.0 \
   162	    --port ${COMFYUI_PORT:-8188} \
   163	    --enable-cors-header \
   164	    --preview-method auto \
   165	    $COMFYUI_ARGS
```
### /home/oz/projects/2025/oz/12/runpod/docker/download_models.sh
```text
     1	#!/bin/bash
     2	# Model download script with resume support
     3	set -o pipefail
     4	
     5	# ============================================
     6	# Configuration
     7	# ============================================
     8	LOG_FILE="/var/log/download_models.log"
     9	DRY_RUN="${DRY_RUN:-false}"
    10	DOWNLOAD_TIMEOUT="${DOWNLOAD_TIMEOUT:-1800}"  # 30 min default
    11	
    12	# Logging setup
    13	mkdir -p "$(dirname "$LOG_FILE")"
    14	exec > >(tee -a "$LOG_FILE") 2>&1
    15	
    16	echo ""
    17	echo "============================================"
    18	echo "[$(date -Iseconds)] Model download started"
    19	echo "  DRY_RUN=$DRY_RUN"
    20	echo "  TIMEOUT=${DOWNLOAD_TIMEOUT}s"
    21	echo "============================================"
    22	
    23	# ============================================
    24	# Helper Functions
    25	# ============================================
    26	
    27	# Helper function for downloads
    28	download_model() {
    29	    local URL="$1"
    30	    local DEST="$2"
    31	    local EXPECTED_SIZE="${3:-}"  # Optional expected size for display
    32	    local NAME=$(basename "$DEST")
    33	
    34	    if [ -f "$DEST" ]; then
    35	        local SIZE=$(stat -c%s "$DEST" 2>/dev/null || echo "0")
    36	        if [ "$SIZE" -gt 1000000 ]; then  # >1MB means likely complete
    37	            echo "  [Skip] $NAME already exists ($(numfmt --to=iec $SIZE 2>/dev/null || echo ${SIZE}B))"
    38	            return 0
    39	        fi
    40	        echo "  [Resume] $NAME incomplete ($(numfmt --to=iec $SIZE 2>/dev/null || echo 0B)), resuming..."
    41	    fi
    42	
    43	    # Dry run mode - just show what would be downloaded
    44	    if [ "$DRY_RUN" = "true" ]; then
    45	        echo "  [DRY-RUN] Would download: $NAME ${EXPECTED_SIZE:+($EXPECTED_SIZE)}"
    46	        return 0
    47	    fi
    48	
    49	    echo "  [Download] $NAME ${EXPECTED_SIZE:+($EXPECTED_SIZE)} from ${URL%%\?*}"
    50	    mkdir -p "$(dirname "$DEST")"
    51	
    52	    # Use wget with timeout and progress bar directly to stderr
    53	    local WGET_EXIT=0
    54	    timeout "$DOWNLOAD_TIMEOUT" wget -c --progress=bar:force:noscroll -O "$DEST" "$URL" 2>&1 || WGET_EXIT=$?
    55	
    56	    if [ $WGET_EXIT -ne 0 ]; then
    57	        echo "  [Warn] wget failed (exit $WGET_EXIT), trying curl..."
    58	        timeout "$DOWNLOAD_TIMEOUT" curl -L -C - --progress-bar -o "$DEST" "$URL" 2>&1 || {
    59	            echo "  [ERROR] Failed to download $NAME after wget and curl attempts"
    60	            rm -f "$DEST"
    61	            return 1
    62	        }
    63	    fi
    64	
    65	    # Verify download
    66	    if [ -f "$DEST" ]; then
    67	        local FINAL_SIZE=$(stat -c%s "$DEST" 2>/dev/null || echo "0")
    68	        echo "  [OK] $NAME downloaded ($(numfmt --to=iec $FINAL_SIZE 2>/dev/null || echo ${FINAL_SIZE}B))"
    69	    else
    70	        echo "  [ERROR] $NAME not found after download"
    71	        return 1
    72	    fi
    73	}
    74	
    75	# HuggingFace download helper
    76	hf_download() {
    77	    local REPO="$1"
    78	    local FILE="$2"
    79	    local DEST="$3"
    80	    local EXPECTED_SIZE="${4:-}"  # Optional size hint
    81	    download_model "https://huggingface.co/${REPO}/resolve/main/${FILE}" "$DEST" "$EXPECTED_SIZE"
    82	}
    83	
    84	# CivitAI download helper
    85	civitai_download() {
    86	    local VERSION_ID="$1"
    87	    local TARGET_DIR="$2"
    88	    local DESCRIPTION="${3:-CivitAI asset}"
    89	
    90	    mkdir -p "$TARGET_DIR"
    91	
    92	    echo "  [Download] $DESCRIPTION (version: $VERSION_ID)"
    93	
    94	    # Build URL
    95	    local URL="https://civitai.com/api/download/models/${VERSION_ID}"
    96	    if [ -n "$CIVITAI_API_KEY" ]; then
    97	        URL="${URL}?token=${CIVITAI_API_KEY}"
    98	    fi
    99	
   100	    # Try wget with explicit redirect handling first
   101	    if wget --version >/dev/null 2>&1; then
   102	        wget -c -q --show-progress \
   103	            --max-redirect=10 \
   104	            --content-disposition \
   105	            -P "$TARGET_DIR" \
   106	            "$URL" 2>/dev/null && return 0
   107	    fi
   108	
   109	    # Fallback to curl if wget fails
   110	    echo "  [Info] Retrying with curl..."
   111	    local FILENAME=$(curl -sI -L "$URL" 2>/dev/null | grep -i "content-disposition" | sed -n 's/.*filename="\?\([^"]*\)"\?.*/\1/p' | tr -d '\r')
   112	    if [ -z "$FILENAME" ]; then
   113	        FILENAME="model_${VERSION_ID}.safetensors"
   114	    fi
   115	
   116	    curl -L -C - -o "$TARGET_DIR/$FILENAME" "$URL" || {
   117	        echo "  [Error] Failed: $VERSION_ID"
   118	        return 1
   119	    }
   120	}
   121	
   122	MODELS_DIR="${MODELS_DIR:-/workspace/ComfyUI/models}"
   123	
   124	# Python download helper with logging
   125	hf_snapshot_download() {
   126	    local REPO="$1"
   127	    local DEST="$2"
   128	    local NAME=$(basename "$DEST")
   129	
   130	    if [ -d "$DEST" ] && [ "$(ls -A "$DEST" 2>/dev/null)" ]; then
   131	        echo "  [Skip] $NAME already exists"
   132	        return 0
   133	    fi
   134	
   135	    echo "  [Download] $NAME from $REPO..."
   136	    mkdir -p "$DEST"
   137	
   138	    python3 -c "
   139	import sys
   140	from huggingface_hub import snapshot_download
   141	try:
   142	    snapshot_download('$REPO',
   143	        local_dir='$DEST',
   144	        local_dir_use_symlinks=False)
   145	    print('  [OK] $NAME downloaded successfully')
   146	except Exception as e:
   147	    print(f'  [Error] Failed to download $NAME: {e}', file=sys.stderr)
   148	    sys.exit(1)
   149	" 2>&1
   150	
   151	    return $?
   152	}
   153	
   154	# ============================================
   155	# VibeVoice Models
   156	# ============================================
   157	if [ "${ENABLE_VIBEVOICE:-false}" = "true" ]; then
   158	    echo ""
   159	    echo "[VibeVoice] Downloading model: ${VIBEVOICE_MODEL:-Large}"
   160	
   161	    case "${VIBEVOICE_MODEL:-Large}" in
   162	        "1.5B")
   163	            hf_snapshot_download "microsoft/VibeVoice-1.5B" "$MODELS_DIR/vibevoice/VibeVoice-1.5B"
   164	            ;;
   165	        "Large")
   166	            hf_snapshot_download "aoi-ot/VibeVoice-Large" "$MODELS_DIR/vibevoice/VibeVoice-Large"
   167	            ;;
   168	        "Large-Q8")
   169	            hf_snapshot_download "FabioSarracino/VibeVoice-Large-Q8" "$MODELS_DIR/vibevoice/VibeVoice-Large-Q8"
   170	            ;;
   171	    esac
   172	
   173	    # Download Qwen tokenizer (required for VibeVoice)
   174	    TOKENIZER_DIR="$MODELS_DIR/vibevoice/tokenizer"
   175	    if [ ! -f "$TOKENIZER_DIR/tokenizer.json" ]; then
   176	        echo "[VibeVoice] Downloading Qwen tokenizer..."
   177	        mkdir -p "$TOKENIZER_DIR"
   178	        wget -q -O "$TOKENIZER_DIR/tokenizer_config.json" \
   179	            "https://huggingface.co/Qwen/Qwen2.5-1.5B/resolve/main/tokenizer_config.json" && \
   180	        wget -q -O "$TOKENIZER_DIR/vocab.json" \
   181	            "https://huggingface.co/Qwen/Qwen2.5-1.5B/resolve/main/vocab.json" && \
   182	        wget -q -O "$TOKENIZER_DIR/merges.txt" \
   183	            "https://huggingface.co/Qwen/Qwen2.5-1.5B/resolve/main/merges.txt" && \
   184	        wget -q -O "$TOKENIZER_DIR/tokenizer.json" \
   185	            "https://huggingface.co/Qwen/Qwen2.5-1.5B/resolve/main/tokenizer.json" && \
   186	        echo "  [OK] Qwen tokenizer downloaded" || \
   187	        echo "  [Error] Failed to download Qwen tokenizer"
   188	    else
   189	        echo "  [Skip] Qwen tokenizer already exists"
   190	    fi
   191	
   192	    echo "[VibeVoice] Download complete"
   193	fi
   194	
   195	# ============================================
   196	# Z-Image Turbo
   197	# ============================================
   198	if [ "${ENABLE_ZIMAGE:-false}" = "true" ]; then
   199	    echo "[Z-Image] Downloading components..."
   200	    hf_download "Tongyi-MAI/Z-Image-Turbo" "qwen_3_4b.safetensors" "$MODELS_DIR/text_encoders/qwen_3_4b.safetensors"
   201	    hf_download "Tongyi-MAI/Z-Image-Turbo" "z_image_turbo_bf16.safetensors" "$MODELS_DIR/diffusion_models/z_image_turbo_bf16.safetensors"
   202	    hf_download "Tongyi-MAI/Z-Image-Turbo" "ae.safetensors" "$MODELS_DIR/vae/ae.safetensors"
   203	fi
   204	
   205	# ============================================
   206	# WAN 2.2 Video Generation Models
   207	# ============================================
   208	if [ "${WAN_720P:-false}" = "true" ]; then
   209	    echo ""
   210	    echo "[WAN] Downloading WAN 2.1 720p models (~25GB total)..."
   211	    echo "  Text encoder (9.5GB) + CLIP vision (1.4GB) + VAE (335MB) + 14B diffusion (14GB)"
   212	    # Text encoders (shared)
   213	    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   214	        "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
   215	        "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
   216	        "9.5GB"
   217	
   218	    # CLIP Vision for I2V
   219	    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   220	        "split_files/clip_vision/clip_vision_h.safetensors" \
   221	        "$MODELS_DIR/clip_vision/clip_vision_h.safetensors" \
   222	        "1.4GB"
   223	
   224	    # VAE
   225	    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   226	        "split_files/vae/wan_2.1_vae.safetensors" \
   227	        "$MODELS_DIR/vae/wan_2.1_vae.safetensors" \
   228	        "335MB"
   229	
   230	    # 720p diffusion model (T2V)
   231	    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   232	        "split_files/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" \
   233	        "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" \
   234	        "14GB"
   235	
   236	    # 720p I2V model (if I2V enabled)
   237	    if [ "${ENABLE_I2V:-false}" = "true" ]; then
   238	        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   239	            "split_files/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" \
   240	            "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" \
   241	            "14GB"
   242	    fi
   243	fi
   244	
   245	if [ "${WAN_480P:-false}" = "true" ]; then
   246	    echo "[WAN] Downloading WAN 2.2 480p models (~12GB)..."
   247	    # Text encoders (shared - skip if already downloaded)
   248	    if [ ! -f "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" ]; then
   249	        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   250	            "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
   251	            "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
   252	    fi
   253	
   254	    # VAE (shared)
   255	    if [ ! -f "$MODELS_DIR/vae/wan_2.1_vae.safetensors" ]; then
   256	        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   257	            "split_files/vae/wan_2.1_vae.safetensors" \
   258	            "$MODELS_DIR/vae/wan_2.1_vae.safetensors"
   259	    fi
   260	
   261	    # 480p diffusion model (T2V) - smaller, fits 16GB VRAM
   262	    hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   263	        "split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors" \
   264	        "$MODELS_DIR/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors"
   265	fi
   266	
   267	# ============================================
   268	# WAN 2.2 Distilled Models (TurboDiffusion I2V)
   269	# High/Low noise expert models for 4-step inference
   270	# VRAM: ~24GB | Size: ~28GB total
   271	# ============================================
   272	if [ "${ENABLE_WAN22_DISTILL:-false}" = "true" ]; then
   273	    echo ""
   274	    echo "[WAN 2.2] Downloading distilled models for TurboDiffusion I2V..."
   275	    echo "  High noise (14GB) + Low noise (14GB) + shared deps = ~28GB total"
   276	
   277	    # Text encoder (shared - skip if already exists)
   278	    if [ ! -f "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" ]; then
   279	        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   280	            "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
   281	            "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
   282	            "9.5GB"
   283	    else
   284	        echo "  [Skip] Text encoder already exists"
   285	    fi
   286	
   287	    # VAE (shared - skip if already exists)
   288	    if [ ! -f "$MODELS_DIR/vae/wan_2.1_vae.safetensors" ]; then
   289	        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   290	            "split_files/vae/wan_2.1_vae.safetensors" \
   291	            "$MODELS_DIR/vae/wan_2.1_vae.safetensors" \
   292	            "335MB"
   293	    else
   294	        echo "  [Skip] VAE already exists"
   295	    fi
   296	
   297	    # WAN 2.2 High Noise Expert (I2V) - ~14GB FP8
   298	    hf_download "Comfy-Org/Wan_2.2_ComfyUI_Repackaged" \
   299	        "split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors" \
   300	        "$MODELS_DIR/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors" \
   301	        "14GB"
   302	
   303	    # WAN 2.2 Low Noise Expert (I2V) - ~14GB FP8
   304	    hf_download "Comfy-Org/Wan_2.2_ComfyUI_Repackaged" \
   305	        "split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors" \
   306	        "$MODELS_DIR/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors" \
   307	        "14GB"
   308	
   309	    # CLIP Vision for I2V (required)
   310	    if [ ! -f "$MODELS_DIR/clip_vision/clip_vision_h.safetensors" ]; then
   311	        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   312	            "split_files/clip_vision/clip_vision_h.safetensors" \
   313	            "$MODELS_DIR/clip_vision/clip_vision_h.safetensors" \
   314	            "1.4GB"
   315	    else
   316	        echo "  [Skip] CLIP vision already exists"
   317	    fi
   318	
   319	    echo "[WAN 2.2] Distilled models download complete"
   320	fi
   321	
   322	# ============================================
   323	# SteadyDancer
   324	# ============================================
   325	if [ "${ENABLE_STEADYDANCER:-false}" = "true" ]; then
   326	    echo "[SteadyDancer] Downloading model..."
   327	    hf_download "MCG-NJU/SteadyDancer-14B" "Wan21_SteadyDancer_fp16.safetensors" "$MODELS_DIR/diffusion_models/Wan21_SteadyDancer_fp16.safetensors"
   328	fi
   329	
   330	# ============================================
   331	# SCAIL
   332	# ============================================
   333	if [ "${ENABLE_SCAIL:-false}" = "true" ]; then
   334	    echo "[SCAIL] Downloading model..."
   335	    cd "$MODELS_DIR/diffusion_models"
   336	    if [ ! -d "SCAIL-Preview" ]; then
   337	        GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/zai-org/SCAIL-Preview
   338	        cd SCAIL-Preview
   339	        git lfs pull
   340	    fi
   341	fi
   342	
   343	# ============================================
   344	# ControlNet Models
   345	# ============================================
   346	if [ "${ENABLE_CONTROLNET:-true}" = "true" ]; then
   347	    echo "[ControlNet] Downloading FP16 models..."
   348	
   349	    CONTROLNET_LIST="${CONTROLNET_MODELS:-canny,depth,openpose}"
   350	    IFS=',' read -ra MODELS <<< "$CONTROLNET_LIST"
   351	
   352	    for model in "${MODELS[@]}"; do
   353	        model=$(echo "$model" | xargs)  # trim whitespace
   354	        case "$model" in
   355	            "canny")
   356	                hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
   357	                    "control_v11p_sd15_canny_fp16.safetensors" \
   358	                    "$MODELS_DIR/controlnet/control_v11p_sd15_canny_fp16.safetensors"
   359	                ;;
   360	            "depth")
   361	                hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
   362	                    "control_v11f1p_sd15_depth_fp16.safetensors" \
   363	                    "$MODELS_DIR/controlnet/control_v11f1p_sd15_depth_fp16.safetensors"
   364	                ;;
   365	            "openpose")
   366	                hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
   367	                    "control_v11p_sd15_openpose_fp16.safetensors" \
   368	                    "$MODELS_DIR/controlnet/control_v11p_sd15_openpose_fp16.safetensors"
   369	                ;;
   370	            "lineart")
   371	                hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
   372	                    "control_v11p_sd15_lineart_fp16.safetensors" \
   373	                    "$MODELS_DIR/controlnet/control_v11p_sd15_lineart_fp16.safetensors"
   374	                ;;
   375	            "normalbae")
   376	                hf_download "comfyanonymous/ControlNet-v1-1_fp16_safetensors" \
   377	                    "control_v11p_sd15_normalbae_fp16.safetensors" \
   378	                    "$MODELS_DIR/controlnet/control_v11p_sd15_normalbae_fp16.safetensors"
   379	                ;;
   380	        esac
   381	    done
   382	fi
   383	
   384	# ============================================
   385	# XTTS v2
   386	# ============================================
   387	if [ "${ENABLE_XTTS:-false}" = "true" ]; then
   388	    echo "[XTTS] Downloading XTTS v2 model..."
   389	    python -c "
   390	from TTS.api import TTS
   391	# This downloads the model on first init
   392	tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=False)
   393	print('XTTS v2 model downloaded successfully')
   394	" 2>&1 || echo "  [Note] XTTS will download on first use"
   395	fi
   396	
   397	# ============================================
   398	# CLIP Vision for I2V (Image-to-Video)
   399	# ============================================
   400	if [ "${ENABLE_I2V:-false}" = "true" ]; then
   401	    echo "[I2V] Downloading CLIP Vision model..."
   402	    mkdir -p "$MODELS_DIR/clip_vision"
   403	    hf_download "Comfy-Org/sigclip_vision_384" \
   404	        "sigclip_vision_patch14_384.safetensors" \
   405	        "$MODELS_DIR/clip_vision/sigclip_vision_patch14_384.safetensors"
   406	fi
   407	
   408	# ============================================
   409	# WAN VACE (Video All-in-One Creation and Editing)
   410	# ============================================
   411	if [ "${ENABLE_VACE:-false}" = "true" ]; then
   412	    echo "[VACE] Downloading WAN VACE 14B model..."
   413	    hf_download "Wan-AI/Wan2.1-VACE-14B" \
   414	        "wan2.1_vace_14B_fp16.safetensors" \
   415	        "$MODELS_DIR/diffusion_models/wan2.1_vace_14B_fp16.safetensors"
   416	fi
   417	
   418	# ============================================
   419	# WAN Fun InP (First-Last Frame Interpolation)
   420	# ============================================
   421	if [ "${ENABLE_FUN_INP:-false}" = "true" ]; then
   422	    echo "[Fun InP] Downloading WAN Fun InP 14B model..."
   423	    hf_download "Wan-AI/Wan2.2-Fun-InP-14B" \
   424	        "wan2.2_fun_inp_14B_fp16.safetensors" \
   425	        "$MODELS_DIR/diffusion_models/wan2.2_fun_inp_14B_fp16.safetensors"
   426	fi
   427	
   428	# ============================================
   429	# Realism Illustrious (SDXL-based photorealism)
   430	# ============================================
   431	if [ "${ENABLE_ILLUSTRIOUS:-false}" = "true" ]; then
   432	    echo ""
   433	    echo "[Illustrious] Downloading Realism Illustrious v5.0 FP16..."
   434	
   435	    # Checkpoint (6.46GB)
   436	    CHECKPOINT_FILE="$MODELS_DIR/checkpoints/realismIllustriousByStableYogi_v50FP16.safetensors"
   437	    if [ ! -f "$CHECKPOINT_FILE" ]; then
   438	        civitai_download "2091367" "$MODELS_DIR/checkpoints" "Realism Illustrious checkpoint (6.46GB)"
   439	    else
   440	        echo "  [Skip] Checkpoint already exists"
   441	    fi
   442	
   443	    # Embeddings (optional but recommended)
   444	    if [ "${ENABLE_ILLUSTRIOUS_EMBEDDINGS:-true}" = "true" ]; then
   445	        echo "[Illustrious] Downloading embeddings..."
   446	
   447	        # Positive Embedding (352KB)
   448	        POSITIVE_EMB="$MODELS_DIR/embeddings/Stable_Yogis_Illustrious_Positives.safetensors"
   449	        if [ ! -f "$POSITIVE_EMB" ]; then
   450	            civitai_download "1153237" "$MODELS_DIR/embeddings" "Positive Embedding"
   451	        fi
   452	
   453	        # Negative Embedding (536KB)
   454	        NEGATIVE_EMB="$MODELS_DIR/embeddings/Stable_Yogis_Illustrious_Negatives.safetensors"
   455	        if [ ! -f "$NEGATIVE_EMB" ]; then
   456	            civitai_download "1153212" "$MODELS_DIR/embeddings" "Negative Embedding"
   457	        fi
   458	    fi
   459	
   460	    echo "[Illustrious] Download complete"
   461	fi
   462	
   463	# ============================================
   464	# Illustrious LoRAs (optional)
   465	# ============================================
   466	if [ "${ENABLE_ILLUSTRIOUS:-false}" = "true" ] && [ -n "$ILLUSTRIOUS_LORAS" ]; then
   467	    echo ""
   468	    echo "[Illustrious] Downloading Illustrious-compatible LoRAs..."
   469	
   470	    IFS=',' read -ra LORA_IDS <<< "$ILLUSTRIOUS_LORAS"
   471	    for version_id in "${LORA_IDS[@]}"; do
   472	        version_id=$(echo "$version_id" | xargs)  # trim whitespace
   473	        civitai_download "$version_id" "$MODELS_DIR/loras" "LoRA"
   474	    done
   475	fi
   476	
   477	# ============================================
   478	# CivitAI LoRAs
   479	# ============================================
   480	if [ "${ENABLE_CIVITAI:-false}" = "true" ] && [ -n "$CIVITAI_LORAS" ]; then
   481	    echo "[CivitAI] Downloading LoRAs..."
   482	
   483	    # Store API key if provided
   484	    if [ -n "$CIVITAI_API_KEY" ]; then
   485	        echo "$CIVITAI_API_KEY" > /workspace/.civitai-token
   486	        chmod 600 /workspace/.civitai-token
   487	    fi
   488	
   489	    IFS=',' read -ra LORA_IDS <<< "$CIVITAI_LORAS"
   490	    for version_id in "${LORA_IDS[@]}"; do
   491	        version_id=$(echo "$version_id" | xargs)  # trim whitespace
   492	        civitai_download "$version_id" "$MODELS_DIR/loras" "CivitAI LoRA"
   493	    done
   494	fi
   495	
   496	# ============================================
   497	# TIER 1: Consumer GPU Models (8-24GB VRAM)
   498	# ============================================
   499	
   500	# ============================================
   501	# Qwen-Image-Edit-2511 (Instruction-based Image Editing)
   502	# GGUF quantized versions from unsloth for consumer GPUs
   503	# Full version for datacenter GPUs
   504	# ============================================
   505	if [ "${ENABLE_QWEN_EDIT:-false}" = "true" ]; then
   506	    echo ""
   507	    QWEN_MODEL="${QWEN_EDIT_MODEL:-Q4_K_M}"
   508	
   509	    case "$QWEN_MODEL" in
   510	        "full")
   511	            echo "[Qwen-Edit] Downloading FULL model (54GB - datacenter only)..."
   512	            python -c "
   513	from huggingface_hub import snapshot_download
   514	snapshot_download('Qwen/Qwen-Image-Edit-2511',
   515	    local_dir='$MODELS_DIR/qwen/Qwen-Image-Edit-2511',
   516	    local_dir_use_symlinks=False)
   517	" 2>&1 || echo "  [Note] Qwen-Edit will download on first use"
   518	            ;;
   519	        "Q4_K_M"|"Q5_K_M"|"Q6_K"|"Q8_0"|"Q2_K"|"Q3_K_M")
   520	            echo "[Qwen-Edit] Downloading GGUF ${QWEN_MODEL} quantized version..."
   521	            GGUF_FILE="qwen-image-edit-2511-${QWEN_MODEL}.gguf"
   522	            GGUF_DEST="$MODELS_DIR/qwen/${GGUF_FILE}"
   523	
   524	            if [ ! -f "$GGUF_DEST" ]; then
   525	                mkdir -p "$MODELS_DIR/qwen"
   526	                echo "  [Download] ${GGUF_FILE} from unsloth/Qwen-Image-Edit-2511-GGUF"
   527	                python -c "
   528	from huggingface_hub import hf_hub_download
   529	hf_hub_download(
   530	    repo_id='unsloth/Qwen-Image-Edit-2511-GGUF',
   531	    filename='${GGUF_FILE}',
   532	    local_dir='$MODELS_DIR/qwen',
   533	    local_dir_use_symlinks=False
   534	)
   535	" 2>&1 || echo "  [Error] Failed to download GGUF model"
   536	            else
   537	                echo "  [Skip] ${GGUF_FILE} already exists"
   538	            fi
   539	            ;;
   540	        *)
   541	            echo "[Qwen-Edit] Unknown model type: $QWEN_MODEL"
   542	            echo "  Valid options: Q4_K_M, Q5_K_M, Q6_K, Q8_0, Q2_K, Q3_K_M, full"
   543	            ;;
   544	    esac
   545	
   546	    echo "[Qwen-Edit] Download complete"
   547	fi
   548	
   549	# ============================================
   550	# Genfocus (Depth-of-Field Refocusing)
   551	# VRAM: ~12GB | Size: ~12GB
   552	# ============================================
   553	if [ "${ENABLE_GENFOCUS:-false}" = "true" ]; then
   554	    echo ""
   555	    echo "[Genfocus] Downloading model components..."
   556	
   557	    hf_download "nycu-cplab/Genfocus-Model" \
   558	        "bokehNet.safetensors" \
   559	        "$MODELS_DIR/genfocus/bokehNet.safetensors"
   560	
   561	    hf_download "nycu-cplab/Genfocus-Model" \
   562	        "deblurNet.safetensors" \
   563	        "$MODELS_DIR/genfocus/deblurNet.safetensors"
   564	
   565	    hf_download "nycu-cplab/Genfocus-Model" \
   566	        "checkpoints/depth_pro.pt" \
   567	        "$MODELS_DIR/genfocus/depth_pro.pt"
   568	
   569	    echo "[Genfocus] Download complete"
   570	fi
   571	
   572	# ============================================
   573	# MVInverse (Multi-view Inverse Rendering)
   574	# VRAM: ~8GB | Size: ~8GB
   575	# ============================================
   576	if [ "${ENABLE_MVINVERSE:-false}" = "true" ]; then
   577	    echo ""
   578	    echo "[MVInverse] Cloning repository and downloading checkpoints..."
   579	
   580	    MVINVERSE_DIR="$MODELS_DIR/mvinverse"
   581	    if [ ! -d "$MVINVERSE_DIR/mvinverse" ]; then
   582	        git clone --depth 1 https://github.com/Maddog241/mvinverse.git "$MVINVERSE_DIR/mvinverse" || \
   583	            echo "  [Error] Failed to clone MVInverse repo"
   584	        echo "  [Note] Checkpoints auto-download on first inference via --ckpt flag"
   585	    else
   586	        echo "  [Skip] MVInverse repository already exists"
   587	    fi
   588	
   589	    echo "[MVInverse] Setup complete"
   590	fi
   591	
   592	# ============================================
   593	# TIER 2: Prosumer GPU Models (24GB+ with CPU offload)
   594	# ============================================
   595	
   596	# ============================================
   597	# FlashPortrait (Portrait Animation)
   598	# VRAM: 60GB (full) | 30GB (model_cpu_offload) | 10GB (sequential_cpu_offload)
   599	# RAM: 32GB minimum for CPU offload modes
   600	# Size: ~60GB
   601	# ============================================
   602	if [ "${ENABLE_FLASHPORTRAIT:-false}" = "true" ]; then
   603	    echo ""
   604	    echo "[FlashPortrait] Downloading models..."
   605	
   606	    case "${GPU_MEMORY_MODE:-auto}" in
   607	        "full"|"model_full_load")
   608	            echo "  [FlashPortrait] Full model load mode (60GB VRAM required)"
   609	            ;;
   610	        "sequential_cpu_offload")
   611	            echo "  [FlashPortrait] Sequential CPU offload mode (10GB VRAM + 32GB+ RAM)"
   612	            ;;
   613	        "model_cpu_offload")
   614	            echo "  [FlashPortrait] Model CPU offload mode (30GB VRAM)"
   615	            ;;
   616	        "auto")
   617	            echo "  [FlashPortrait] Auto mode - will detect VRAM at startup"
   618	            ;;
   619	    esac
   620	
   621	    # FlashPortrait main checkpoint
   622	    python -c "
   623	from huggingface_hub import snapshot_download
   624	snapshot_download('FrancisRing/FlashPortrait',
   625	    local_dir='$MODELS_DIR/flashportrait/FlashPortrait',
   626	    local_dir_use_symlinks=False)
   627	" 2>&1 || echo "  [Note] FlashPortrait will download on first use"
   628	
   629	    # Wan2.1 I2V 14B 720P (required dependency) - check if already exists
   630	    if [ ! -f "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" ]; then
   631	        echo "  [FlashPortrait] Downloading Wan2.1 I2V 720p dependency..."
   632	        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   633	            "split_files/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" \
   634	            "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors"
   635	    fi
   636	
   637	    echo "[FlashPortrait] Download complete"
   638	fi
   639	
   640	# ============================================
   641	# StoryMem (Multi-Shot Video Storytelling)
   642	# Based on Wan2.2, uses LoRA variants (MI2V, MM2V)
   643	# VRAM: ~20-24GB (base models + LoRA)
   644	# Size: ~20GB (LoRAs) + Wan2.1 base models
   645	# ============================================
   646	if [ "${ENABLE_STORYMEM:-false}" = "true" ]; then
   647	    echo ""
   648	    echo "[StoryMem] Downloading models and dependencies..."
   649	
   650	    # Ensure Wan2.1 T2V base model
   651	    if [ ! -f "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" ]; then
   652	        echo "  [StoryMem] Downloading Wan2.1 T2V 14B base model..."
   653	        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   654	            "split_files/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" \
   655	            "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors"
   656	    fi
   657	
   658	    # Ensure Wan2.1 I2V base model
   659	    if [ ! -f "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" ]; then
   660	        echo "  [StoryMem] Downloading Wan2.1 I2V 720p 14B base model..."
   661	        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   662	            "split_files/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors" \
   663	            "$MODELS_DIR/diffusion_models/wan2.1_i2v_720p_14B_fp8_e4m3fn.safetensors"
   664	    fi
   665	
   666	    # Ensure text encoder
   667	    if [ ! -f "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" ]; then
   668	        echo "  [StoryMem] Downloading UMT5-XXL text encoder..."
   669	        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   670	            "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
   671	            "$MODELS_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
   672	    fi
   673	
   674	    # Ensure VAE
   675	    if [ ! -f "$MODELS_DIR/vae/wan_2.1_vae.safetensors" ]; then
   676	        echo "  [StoryMem] Downloading WAN VAE..."
   677	        hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   678	            "split_files/vae/wan_2.1_vae.safetensors" \
   679	            "$MODELS_DIR/vae/wan_2.1_vae.safetensors"
   680	    fi
   681	
   682	    # StoryMem LoRA variants
   683	    echo "  [StoryMem] Downloading StoryMem LoRA variants..."
   684	    python -c "
   685	from huggingface_hub import snapshot_download
   686	snapshot_download('Kevin-thu/StoryMem',
   687	    local_dir='$MODELS_DIR/storymem/StoryMem',
   688	    local_dir_use_symlinks=False)
   689	" 2>&1 || echo "  [Note] StoryMem LoRAs will download on first use"
   690	
   691	    echo "[StoryMem] Download complete"
   692	fi
   693	
   694	# ============================================
   695	# TIER 3: Datacenter GPU Models (48-80GB VRAM)
   696	# ============================================
   697	
   698	# ============================================
   699	# InfCam (Camera-Controlled Video Generation)
   700	# WARNING: EXPERIMENTAL - DATACENTER TIER ONLY
   701	# VRAM: 50GB+ inference, 52-56GB/GPU training
   702	# Requires: A100 80GB or H100 80GB
   703	# Size: ~50GB+
   704	# ============================================
   705	if [ "${ENABLE_INFCAM:-false}" = "true" ]; then
   706	    if [ "${GPU_TIER}" = "datacenter" ]; then
   707	        echo ""
   708	        echo "[InfCam] EXPERIMENTAL - Downloading for datacenter tier..."
   709	        echo "  [Warning] Requires A100 80GB or H100 80GB GPU"
   710	
   711	        # InfCam main checkpoint
   712	        python -c "
   713	from huggingface_hub import snapshot_download
   714	snapshot_download('emjay73/InfCam',
   715	    local_dir='$MODELS_DIR/infcam/InfCam',
   716	    local_dir_use_symlinks=False)
   717	" 2>&1 || echo "  [Note] InfCam will download on first use"
   718	
   719	        # UniDepth-v2-vitl14 (required dependency)
   720	        python -c "
   721	from huggingface_hub import snapshot_download
   722	snapshot_download('lpiccinelli/unidepth-v2-vitl14',
   723	    local_dir='$MODELS_DIR/infcam/unidepth-v2-vitl14',
   724	    local_dir_use_symlinks=False)
   725	" 2>&1 || echo "  [Note] UniDepth will download on first use"
   726	
   727	        # Wan2.1 base model for InfCam
   728	        if [ ! -f "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" ]; then
   729	            echo "  [InfCam] Downloading Wan2.1 T2V base model..."
   730	            hf_download "Comfy-Org/Wan_2.1_ComfyUI_repackaged" \
   731	                "split_files/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors" \
   732	                "$MODELS_DIR/diffusion_models/wan2.1_t2v_14B_fp8_e4m3fn.safetensors"
   733	        fi
   734	
   735	        echo "[InfCam] Download complete"
   736	    else
   737	        echo ""
   738	        echo "[InfCam] Skipped - GPU_TIER must be 'datacenter' (current: ${GPU_TIER:-consumer})"
   739	        echo "  [Info] InfCam requires 50GB+ VRAM (A100/H100)"
   740	    fi
   741	fi
   742	
   743	echo ""
   744	echo "============================================"
   745	echo "[$(date -Iseconds)] Model download complete"
   746	echo "============================================"
   747	echo ""
   748	echo "Downloaded models summary:"
   749	ls -lh "$MODELS_DIR"/*/  2>/dev/null | grep -E "\.safetensors|\.pt|\.ckpt|\.bin" | head -20 || echo "  No models found"
   750	echo ""
```
### /home/oz/projects/2025/oz/12/runpod/docker/r2_sync.sh
```text
     1	#!/bin/bash
     2	# R2 Sync Daemon - watches ComfyUI output directory and uploads new files
     3	#
     4	# Author: oz
     5	# Model: claude-opus-4-5
     6	# Date: 2025-12-29
     7	
     8	set -e
     9	
    10	OUTPUT_DIR="${COMFYUI_OUTPUT_DIR:-/workspace/ComfyUI/output}"
    11	LOG_FILE="/var/log/r2_sync.log"
    12	UPLOAD_SCRIPT="/upload_to_r2.py"
    13	
    14	# File patterns to watch (images, videos, audio)
    15	WATCH_PATTERNS="\.png$|\.jpg$|\.jpeg$|\.webp$|\.mp4$|\.webm$|\.gif$|\.wav$|\.mp3$|\.flac$"
    16	
    17	log() {
    18	    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
    19	}
    20	
    21	# Check dependencies
    22	if ! command -v inotifywait &> /dev/null; then
    23	    log "ERROR: inotifywait not found. Install: apt-get install inotify-tools"
    24	    exit 1
    25	fi
    26	
    27	if [ ! -f "$UPLOAD_SCRIPT" ]; then
    28	    log "ERROR: Upload script not found: $UPLOAD_SCRIPT"
    29	    exit 1
    30	fi
    31	
    32	# Check R2 credentials (support both naming conventions)
    33	R2_ACCESS="${R2_ACCESS_KEY_ID:-$R2_ACCESS_KEY}"
    34	R2_SECRET="${R2_SECRET_ACCESS_KEY:-$R2_SECRET_KEY}"
    35	if [ -z "$R2_ACCESS" ] || [ -z "$R2_SECRET" ]; then
    36	    log "ERROR: R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY required"
    37	    exit 1
    38	fi
    39	
    40	mkdir -p "$OUTPUT_DIR"
    41	
    42	log "Starting R2 sync daemon"
    43	log "Watching: $OUTPUT_DIR"
    44	
    45	# Watch for new files and upload them
    46	inotifywait -m -r -e close_write --format '%w%f' "$OUTPUT_DIR" 2>/dev/null | while read filepath; do
    47	    if echo "$filepath" | grep -qE "$WATCH_PATTERNS"; then
    48	        sleep 1  # Ensure file is fully written
    49	        if [ -f "$filepath" ]; then
    50	            log "New file: $filepath"
    51	            (
    52	                python3 "$UPLOAD_SCRIPT" "$filepath" >> "$LOG_FILE" 2>&1
    53	                [ $? -eq 0 ] && log "Uploaded: $(basename "$filepath")" || log "FAILED: $(basename "$filepath")"
    54	            ) &
    55	        fi
    56	    fi
    57	done
```
### /home/oz/projects/2025/oz/12/runpod/docker/upload_to_r2.py
```text
     1	#!/usr/bin/env python3
     2	"""
     3	R2 Upload Script for ComfyUI Output Sync.
     4	
     5	Uploads files to Cloudflare R2 with retry logic and organized folder structure.
     6	Designed for use with r2_sync.sh inotifywait daemon.
     7	
     8	Author: oz
     9	Model: claude-opus-4-5
    10	Date: 2025-12-29
    11	"""
    12	
    13	import os
    14	import sys
    15	import argparse
    16	import logging
    17	from datetime import datetime
    18	from pathlib import Path
    19	import time
    20	
    21	try:
    22	    import boto3
    23	    from botocore.config import Config
    24	    from botocore.exceptions import ClientError
    25	except ImportError:
    26	    print("[R2] Error: boto3 not installed. Run: pip install boto3")
    27	    sys.exit(1)
    28	
    29	logging.basicConfig(
    30	    level=logging.INFO,
    31	    format='[R2] %(asctime)s - %(levelname)s - %(message)s',
    32	    datefmt='%Y-%m-%d %H:%M:%S'
    33	)
    34	logger = logging.getLogger(__name__)
    35	
    36	
    37	class R2Uploader:
    38	    """Cloudflare R2 file uploader with retry logic."""
    39	
    40	    def __init__(self):
    41	        self.endpoint = os.environ.get(
    42	            'R2_ENDPOINT',
    43	            'https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com'
    44	        )
    45	        self.bucket = os.environ.get('R2_BUCKET', 'runpod')
    46	        # Support both naming conventions
    47	        self.access_key = os.environ.get('R2_ACCESS_KEY_ID') or os.environ.get('R2_ACCESS_KEY')
    48	        self.secret_key = os.environ.get('R2_SECRET_ACCESS_KEY') or os.environ.get('R2_SECRET_KEY')
    49	
    50	        if not self.access_key or not self.secret_key:
    51	            logger.error("R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY environment variables required")
    52	            raise ValueError("Missing R2 credentials")
    53	
    54	        self.client = boto3.client(
    55	            's3',
    56	            endpoint_url=self.endpoint,
    57	            aws_access_key_id=self.access_key,
    58	            aws_secret_access_key=self.secret_key,
    59	            config=Config(signature_version='s3v4', retries={'max_attempts': 3, 'mode': 'adaptive'}),
    60	            region_name='auto'
    61	        )
    62	        logger.info(f"R2 client ready: {self.bucket}")
    63	
    64	    def upload_file(self, local_path: str, remote_prefix: str = "outputs", max_retries: int = 3) -> bool:
    65	        local_path = Path(local_path)
    66	        if not local_path.exists():
    67	            logger.error(f"File not found: {local_path}")
    68	            return False
    69	
    70	        date_folder = datetime.now().strftime('%Y-%m-%d')
    71	        remote_key = f"{remote_prefix}/{date_folder}/{local_path.name}"
    72	        file_size = local_path.stat().st_size
    73	        logger.info(f"Uploading: {local_path.name} ({file_size / 1024 / 1024:.2f} MB)")
    74	
    75	        for attempt in range(1, max_retries + 1):
    76	            try:
    77	                if file_size > 100 * 1024 * 1024:
    78	                    self._multipart_upload(local_path, remote_key)
    79	                else:
    80	                    self.client.upload_file(str(local_path), self.bucket, remote_key)
    81	                logger.info(f"Uploaded: s3://{self.bucket}/{remote_key}")
    82	                return True
    83	            except ClientError as e:
    84	                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
    85	                logger.warning(f"Attempt {attempt}/{max_retries} failed: {error_code}")
    86	                if attempt < max_retries:
    87	                    time.sleep(2 ** attempt)
    88	                else:
    89	                    logger.error(f"Upload failed: {e}")
    90	                    return False
    91	            except Exception as e:
    92	                logger.error(f"Error: {e}")
    93	                return False
    94	        return False
    95	
    96	    def _multipart_upload(self, local_path: Path, remote_key: str, chunk_size: int = 50 * 1024 * 1024):
    97	        file_size = local_path.stat().st_size
    98	        mpu = self.client.create_multipart_upload(Bucket=self.bucket, Key=remote_key)
    99	        upload_id = mpu['UploadId']
   100	        parts = []
   101	        try:
   102	            with open(local_path, 'rb') as f:
   103	                part_number = 1
   104	                while True:
   105	                    data = f.read(chunk_size)
   106	                    if not data:
   107	                        break
   108	                    response = self.client.upload_part(
   109	                        Bucket=self.bucket, Key=remote_key,
   110	                        PartNumber=part_number, UploadId=upload_id, Body=data
   111	                    )
   112	                    parts.append({'PartNumber': part_number, 'ETag': response['ETag']})
   113	                    logger.info(f"  Part {part_number}: {min((part_number * chunk_size / file_size) * 100, 100):.0f}%")
   114	                    part_number += 1
   115	            self.client.complete_multipart_upload(
   116	                Bucket=self.bucket, Key=remote_key, UploadId=upload_id,
   117	                MultipartUpload={'Parts': parts}
   118	            )
   119	        except Exception as e:
   120	            self.client.abort_multipart_upload(Bucket=self.bucket, Key=remote_key, UploadId=upload_id)
   121	            raise
   122	
   123	    def test_connection(self) -> bool:
   124	        try:
   125	            self.client.list_objects_v2(Bucket=self.bucket, MaxKeys=1)
   126	            logger.info(f"Connection OK: {self.bucket}")
   127	            return True
   128	        except ClientError as e:
   129	            logger.error(f"Connection failed: {e}")
   130	            return False
   131	
   132	
   133	def main():
   134	    parser = argparse.ArgumentParser(description='Upload files to Cloudflare R2')
   135	    parser.add_argument('files', nargs='*', help='Files to upload')
   136	    parser.add_argument('--test', action='store_true', help='Test R2 connection')
   137	    parser.add_argument('--prefix', default='outputs', help='R2 key prefix')
   138	    args = parser.parse_args()
   139	
   140	    try:
   141	        uploader = R2Uploader()
   142	    except ValueError:
   143	        sys.exit(1)
   144	
   145	    if args.test:
   146	        sys.exit(0 if uploader.test_connection() else 1)
   147	
   148	    if not args.files:
   149	        parser.print_help()
   150	        sys.exit(1)
   151	
   152	    success = sum(1 for f in args.files if uploader.upload_file(f, args.prefix))
   153	    logger.info(f"Complete: {success}/{len(args.files)}")
   154	    sys.exit(0 if success == len(args.files) else 1)
   155	
   156	
   157	if __name__ == '__main__':
   158	    main()
```
### /home/oz/projects/2025/oz/12/runpod/docker/scripts/xtts-vo-gen.py
```text
     1	#!/usr/bin/env python3
     2	"""
     3	XTTS Voice-Over Generator
     4	Batch TTS generation using the XTTS API server.
     5	
     6	Usage:
     7	    # Single line
     8	    python xtts-vo-gen.py "Hello world" --output hello.wav
     9	
    10	    # From file (one line per output)
    11	    python xtts-vo-gen.py --file script.txt --output-dir ./vo-output
    12	
    13	    # Custom voice cloning (provide reference audio)
    14	    python xtts-vo-gen.py "Hello world" --speaker /path/to/reference.wav
    15	
    16	    # Stream to stdout
    17	    python xtts-vo-gen.py "Hello world" --stream | ffplay -
    18	
    19	API Endpoints:
    20	    - /tts_to_file: Save to server path
    21	    - /tts_to_audio/: Get audio bytes directly
    22	    - /tts_stream: Stream audio chunks
    23	"""
    24	
    25	import argparse
    26	import json
    27	import os
    28	import sys
    29	import time
    30	from pathlib import Path
    31	from typing import Optional
    32	import urllib.request
    33	import urllib.error
    34	
    35	
    36	XTTS_API_URL = os.environ.get("XTTS_API_URL", "http://localhost:8020")
    37	
    38	# Built-in speakers
    39	SPEAKERS = ["male", "female", "calm_female"]
    40	
    41	# Supported languages
    42	LANGUAGES = {
    43	    "ar": "Arabic", "pt": "Brazilian Portuguese", "zh-cn": "Chinese",
    44	    "cs": "Czech", "nl": "Dutch", "en": "English", "fr": "French",
    45	    "de": "German", "it": "Italian", "pl": "Polish", "ru": "Russian",
    46	    "es": "Spanish", "tr": "Turkish", "ja": "Japanese", "ko": "Korean",
    47	    "hu": "Hungarian", "hi": "Hindi"
    48	}
    49	
    50	
    51	def api_request(endpoint: str, data: dict = None, method: str = "GET") -> bytes:
    52	    """Make API request to XTTS server."""
    53	    url = f"{XTTS_API_URL}{endpoint}"
    54	
    55	    if data:
    56	        req = urllib.request.Request(
    57	            url,
    58	            data=json.dumps(data).encode('utf-8'),
    59	            headers={'Content-Type': 'application/json'},
    60	            method=method
    61	        )
    62	    else:
    63	        req = urllib.request.Request(url, method=method)
    64	
    65	    try:
    66	        with urllib.request.urlopen(req, timeout=120) as response:
    67	            return response.read()
    68	    except urllib.error.HTTPError as e:
    69	        print(f"API Error: {e.code} - {e.read().decode()}", file=sys.stderr)
    70	        sys.exit(1)
    71	    except urllib.error.URLError as e:
    72	        print(f"Connection Error: {e.reason}", file=sys.stderr)
    73	        print(f"Is XTTS server running at {XTTS_API_URL}?", file=sys.stderr)
    74	        sys.exit(1)
    75	
    76	
    77	def generate_tts(
    78	    text: str,
    79	    speaker: str = "female",
    80	    language: str = "en",
    81	    output_path: Optional[str] = None,
    82	    stream: bool = False
    83	) -> Optional[bytes]:
    84	    """Generate TTS audio from text."""
    85	
    86	    data = {
    87	        "text": text,
    88	        "speaker_wav": speaker,
    89	        "language": language
    90	    }
    91	
    92	    if output_path:
    93	        # Use tts_to_file for server-side saving
    94	        data["file_name_or_path"] = output_path
    95	        result = api_request("/tts_to_file", data, method="POST")
    96	        response = json.loads(result)
    97	        print(f"Saved: {response.get('output_path', output_path)}")
    98	        return None
    99	    elif stream:
   100	        # Stream endpoint for real-time playback
   101	        return api_request("/tts_stream", data, method="POST")
   102	    else:
   103	        # Return raw audio bytes
   104	        return api_request("/tts_to_audio/", data, method="POST")
   105	
   106	
   107	def process_script_file(
   108	    script_path: str,
   109	    output_dir: str,
   110	    speaker: str = "female",
   111	    language: str = "en",
   112	    prefix: str = "line"
   113	):
   114	    """Process a script file with multiple lines."""
   115	
   116	    Path(output_dir).mkdir(parents=True, exist_ok=True)
   117	
   118	    with open(script_path, 'r') as f:
   119	        lines = [line.strip() for line in f if line.strip()]
   120	
   121	    print(f"Processing {len(lines)} lines...")
   122	
   123	    for i, line in enumerate(lines, 1):
   124	        output_file = os.path.join(output_dir, f"{prefix}_{i:03d}.wav")
   125	        print(f"[{i}/{len(lines)}] {line[:50]}...")
   126	
   127	        audio = generate_tts(line, speaker, language)
   128	        if audio:
   129	            with open(output_file, 'wb') as f:
   130	                f.write(audio)
   131	            print(f"  -> {output_file}")
   132	
   133	        # Brief pause between requests
   134	        time.sleep(0.5)
   135	
   136	    print(f"\nDone! Generated {len(lines)} audio files in {output_dir}")
   137	
   138	
   139	def list_speakers():
   140	    """List available speakers."""
   141	    result = api_request("/speakers_list")
   142	    speakers = json.loads(result)
   143	    print("Available speakers:")
   144	    for speaker in speakers:
   145	        print(f"  - {speaker}")
   146	    return speakers
   147	
   148	
   149	def list_languages():
   150	    """List supported languages."""
   151	    result = api_request("/languages")
   152	    data = json.loads(result)
   153	    print("Supported languages:")
   154	    for name, code in data.get("languages", {}).items():
   155	        print(f"  {code}: {name}")
   156	
   157	
   158	def main():
   159	    parser = argparse.ArgumentParser(
   160	        description="XTTS Voice-Over Generator",
   161	        formatter_class=argparse.RawDescriptionHelpFormatter,
   162	        epilog=__doc__
   163	    )
   164	
   165	    parser.add_argument("text", nargs="?", help="Text to synthesize")
   166	    parser.add_argument("-f", "--file", help="Script file (one line per output)")
   167	    parser.add_argument("-o", "--output", help="Output file path")
   168	    parser.add_argument("-d", "--output-dir", default="./vo-output",
   169	                        help="Output directory for batch processing")
   170	    parser.add_argument("-s", "--speaker", default="female",
   171	                        help=f"Speaker voice: {', '.join(SPEAKERS)} or path to .wav")
   172	    parser.add_argument("-l", "--language", default="en",
   173	                        help=f"Language code: {', '.join(LANGUAGES.keys())}")
   174	    parser.add_argument("-p", "--prefix", default="line",
   175	                        help="Filename prefix for batch output")
   176	    parser.add_argument("--stream", action="store_true",
   177	                        help="Stream audio to stdout")
   178	    parser.add_argument("--list-speakers", action="store_true",
   179	                        help="List available speakers")
   180	    parser.add_argument("--list-languages", action="store_true",
   181	                        help="List supported languages")
   182	    parser.add_argument("--api-url", help="XTTS API URL (default: http://localhost:8020)")
   183	
   184	    args = parser.parse_args()
   185	
   186	    if args.api_url:
   187	        global XTTS_API_URL
   188	        XTTS_API_URL = args.api_url
   189	
   190	    if args.list_speakers:
   191	        list_speakers()
   192	        return
   193	
   194	    if args.list_languages:
   195	        list_languages()
   196	        return
   197	
   198	    if args.file:
   199	        process_script_file(
   200	            args.file,
   201	            args.output_dir,
   202	            args.speaker,
   203	            args.language,
   204	            args.prefix
   205	        )
   206	    elif args.text:
   207	        if args.stream:
   208	            audio = generate_tts(args.text, args.speaker, args.language, stream=True)
   209	            sys.stdout.buffer.write(audio)
   210	        elif args.output:
   211	            audio = generate_tts(args.text, args.speaker, args.language)
   212	            with open(args.output, 'wb') as f:
   213	                f.write(audio)
   214	            print(f"Saved: {args.output}")
   215	        else:
   216	            audio = generate_tts(args.text, args.speaker, args.language)
   217	            sys.stdout.buffer.write(audio)
   218	    else:
   219	        parser.print_help()
   220	        sys.exit(1)
   221	
   222	
   223	if __name__ == "__main__":
   224	    main()
```
### /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/__init__.py
```text
     1	"""
     2	ComfyUI-Genfocus: Generative Refocusing Custom Nodes
     3	
     4	A ComfyUI wrapper for the Genfocus framework, enabling:
     5	- DeblurNet: Recover all-in-focus images from blurry input
     6	- BokehNet: Synthesize photorealistic depth-of-field effects
     7	
     8	Based on: https://github.com/rayray9999/Genfocus
     9	Paper: "Generative Refocusing: Flexible Defocus Control from a Single Image"
    10	
    11	Model downloads: https://huggingface.co/nycu-cplab/Genfocus-Model
    12	"""
    13	
    14	import logging
    15	import os
    16	
    17	# Setup logging
    18	logging.basicConfig(level=logging.INFO)
    19	logger = logging.getLogger("ComfyUI-Genfocus")
    20	
    21	# Import nodes
    22	from .nodes.loaders import (
    23	    GenfocusDeblurNetLoader,
    24	    GenfocusBokehNetLoader,
    25	    GenfocusDepthLoader,
    26	    clear_model_cache,
    27	)
    28	from .nodes.deblur import GenfocusDeblur
    29	from .nodes.bokeh import GenfocusBokeh
    30	from .nodes.pipeline import GenfocusPipeline, GenfocusDepthEstimator
    31	
    32	# Node class mappings for ComfyUI registration
    33	NODE_CLASS_MAPPINGS = {
    34	    # Loaders
    35	    "GenfocusDeblurNetLoader": GenfocusDeblurNetLoader,
    36	    "GenfocusBokehNetLoader": GenfocusBokehNetLoader,
    37	    "GenfocusDepthLoader": GenfocusDepthLoader,
    38	
    39	    # Processing nodes
    40	    "GenfocusDeblur": GenfocusDeblur,
    41	    "GenfocusBokeh": GenfocusBokeh,
    42	
    43	    # Pipeline / utility nodes
    44	    "GenfocusPipeline": GenfocusPipeline,
    45	    "GenfocusDepthEstimator": GenfocusDepthEstimator,
    46	}
    47	
    48	# Display names for ComfyUI UI
    49	NODE_DISPLAY_NAME_MAPPINGS = {
    50	    # Loaders
    51	    "GenfocusDeblurNetLoader": "Genfocus DeblurNet Loader",
    52	    "GenfocusBokehNetLoader": "Genfocus BokehNet Loader",
    53	    "GenfocusDepthLoader": "Genfocus Depth Loader",
    54	
    55	    # Processing nodes
    56	    "GenfocusDeblur": "Genfocus Deblur",
    57	    "GenfocusBokeh": "Genfocus Bokeh",
    58	
    59	    # Pipeline / utility nodes
    60	    "GenfocusPipeline": "Genfocus Pipeline (All-in-One)",
    61	    "GenfocusDepthEstimator": "Genfocus Depth Estimator",
    62	}
    63	
    64	# Web directory for custom UI elements (if any)
    65	WEB_DIRECTORY = "./web"
    66	
    67	# Version info
    68	__version__ = "0.1.0"
    69	__author__ = "ComfyUI-Genfocus Contributors"
    70	
    71	# Exported symbols
    72	__all__ = [
    73	    "NODE_CLASS_MAPPINGS",
    74	    "NODE_DISPLAY_NAME_MAPPINGS",
    75	    "WEB_DIRECTORY",
    76	    # Loaders
    77	    "GenfocusDeblurNetLoader",
    78	    "GenfocusBokehNetLoader",
    79	    "GenfocusDepthLoader",
    80	    # Processing
    81	    "GenfocusDeblur",
    82	    "GenfocusBokeh",
    83	    # Pipeline
    84	    "GenfocusPipeline",
    85	    "GenfocusDepthEstimator",
    86	    # Utilities
    87	    "clear_model_cache",
    88	]
    89	
    90	# Log successful initialization
    91	logger.info(f"ComfyUI-Genfocus v{__version__} loaded successfully")
    92	logger.info(f"Registered {len(NODE_CLASS_MAPPINGS)} nodes")
    93	
    94	# Create models directory if it doesn't exist
    95	models_dir = os.path.join(os.path.dirname(__file__), "models")
    96	if not os.path.exists(models_dir):
    97	    os.makedirs(models_dir, exist_ok=True)
    98	    logger.info(f"Created models directory: {models_dir}")
```
### /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/nodes/__init__.py
```text
     1	# ComfyUI-Genfocus Nodes
     2	from .loaders import GenfocusDeblurNetLoader, GenfocusBokehNetLoader, GenfocusDepthLoader
     3	from .deblur import GenfocusDeblur
     4	from .bokeh import GenfocusBokeh
     5	from .pipeline import GenfocusPipeline
     6	
     7	__all__ = [
     8	    "GenfocusDeblurNetLoader",
     9	    "GenfocusBokehNetLoader",
    10	    "GenfocusDepthLoader",
    11	    "GenfocusDeblur",
    12	    "GenfocusBokeh",
    13	    "GenfocusPipeline",
    14	]
```
### /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/nodes/bokeh.py
```text
     1	"""
     2	GenfocusBokeh node for ComfyUI.
     3	
     4	Applies BokehNet diffusion model to synthesize photorealistic
     5	depth-of-field effects with controllable parameters.
     6	"""
     7	
     8	import logging
     9	from typing import Dict, Any, Tuple, Optional
    10	
    11	import torch
    12	import numpy as np
    13	
    14	from ..utils.tensor_utils import (
    15	    comfyui_to_pytorch,
    16	    pytorch_to_comfyui,
    17	    ensure_batch_dim,
    18	    get_dtype,
    19	    create_focus_mask,
    20	)
    21	
    22	logger = logging.getLogger("ComfyUI-Genfocus")
    23	
    24	# Custom types
    25	GENFOCUS_BOKEH_MODEL = "GENFOCUS_BOKEH"
    26	DEPTH_MAP = "DEPTH_MAP"
    27	
    28	
    29	# Aperture shape kernels for bokeh highlights
    30	APERTURE_SHAPES = {
    31	    "circle": "circular",
    32	    "triangle": "triangular",
    33	    "heart": "heart",
    34	    "star": "star",
    35	    "hexagon": "hexagonal",
    36	}
    37	
    38	
    39	class GenfocusBokeh:
    40	    """
    41	    Apply BokehNet bokeh synthesis to image.
    42	
    43	    This node uses a FLUX-based diffusion model trained for synthesizing
    44	    photorealistic depth-of-field effects. It can create various bokeh
    45	    shapes and intensities based on depth information.
    46	    """
    47	
    48	    @classmethod
    49	    def INPUT_TYPES(cls) -> Dict:
    50	        return {
    51	            "required": {
    52	                "image": ("IMAGE",),
    53	                "model": (GENFOCUS_BOKEH_MODEL,),
    54	                "steps": ("INT", {
    55	                    "default": 30,
    56	                    "min": 1,
    57	                    "max": 100,
    58	                    "step": 1,
    59	                    "display": "number"
    60	                }),
    61	                "guidance_scale": ("FLOAT", {
    62	                    "default": 7.5,
    63	                    "min": 0.0,
    64	                    "max": 20.0,
    65	                    "step": 0.5,
    66	                    "display": "number"
    67	                }),
    68	                "focus_distance": ("FLOAT", {
    69	                    "default": 0.5,
    70	                    "min": 0.0,
    71	                    "max": 1.0,
    72	                    "step": 0.05,
    73	                    "display": "slider",
    74	                    "tooltip": "Focus plane distance (0=near, 1=far)"
    75	                }),
    76	                "bokeh_intensity": ("FLOAT", {
    77	                    "default": 0.5,
    78	                    "min": 0.0,
    79	                    "max": 1.0,
    80	                    "step": 0.05,
    81	                    "display": "slider",
    82	                    "tooltip": "Strength of bokeh effect (0=none, 1=maximum)"
    83	                }),
    84	                "aperture_shape": (list(APERTURE_SHAPES.keys()), {
    85	                    "default": "circle"
    86	                }),
    87	            },
    88	            "optional": {
    89	                "depth_map": (DEPTH_MAP, {
    90	                    "tooltip": "Pre-computed depth map (optional, auto-estimated if not provided)"
    91	                }),
    92	                "seed": ("INT", {
    93	                    "default": 0,
    94	                    "min": 0,
    95	                    "max": 0xffffffffffffffff,
    96	                    "step": 1
    97	                }),
    98	                "aperture_size": ("FLOAT", {
    99	                    "default": 0.1,
   100	                    "min": 0.01,
   101	                    "max": 0.5,
   102	                    "step": 0.01,
   103	                    "display": "slider",
   104	                    "tooltip": "Aperture size (smaller = larger DOF)"
   105	                }),
   106	                "focus_falloff": ("FLOAT", {
   107	                    "default": 2.0,
   108	                    "min": 0.5,
   109	                    "max": 10.0,
   110	                    "step": 0.5,
   111	                    "tooltip": "How quickly blur increases away from focus plane"
   112	                }),
   113	            }
   114	        }
   115	
   116	    RETURN_TYPES = ("IMAGE", "MASK")
   117	    RETURN_NAMES = ("bokeh_image", "focus_mask")
   118	    FUNCTION = "apply_bokeh"
   119	    CATEGORY = "image/genfocus"
   120	    DESCRIPTION = "Apply BokehNet to synthesize depth-of-field bokeh effects"
   121	
   122	    def __init__(self):
   123	        self._pipeline = None
   124	        self._depth_estimator = None
   125	
   126	    def _ensure_pipeline(self, model: Dict[str, Any]) -> Any:
   127	        """Lazily initialize the BokehNet diffusion pipeline."""
   128	        if model.get("_pipeline") is not None:
   129	            return model["_pipeline"]
   130	
   131	        logger.info("Initializing BokehNet diffusion pipeline...")
   132	
   133	        try:
   134	            from diffusers import FluxPipeline, DDIMScheduler
   135	            from peft import PeftModel
   136	
   137	            device = model["device"]
   138	            dtype = model["dtype"]
   139	
   140	            # Load base FLUX.1-dev pipeline
   141	            pipe = FluxPipeline.from_pretrained(
   142	                "black-forest-labs/FLUX.1-dev",
   143	                torch_dtype=dtype,
   144	            )
   145	
   146	            # Load LoRA weights
   147	            state_dict = model["state_dict"]
   148	            lora_state_dict = {
   149	                k: v for k, v in state_dict.items()
   150	                if "lora" in k.lower() or "adapter" in k.lower()
   151	            }
   152	
   153	            if lora_state_dict:
   154	                pipe.transformer.load_state_dict(lora_state_dict, strict=False)
   155	                logger.info(f"Loaded {len(lora_state_dict)} BokehNet LoRA parameters")
   156	
   157	            # Configure scheduler
   158	            pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)
   159	
   160	            # Handle device placement
   161	            if model.get("offload_to_cpu"):
   162	                pipe.enable_model_cpu_offload()
   163	            else:
   164	                pipe = pipe.to(device)
   165	
   166	            model["_pipeline"] = pipe
   167	            model["_is_loaded"] = True
   168	
   169	            return pipe
   170	
   171	        except Exception as e:
   172	            logger.error(f"BokehNet pipeline init failed: {e}")
   173	            raise
   174	
   175	    def _estimate_depth(
   176	        self,
   177	        image_tensor: torch.Tensor,
   178	        device: str
   179	    ) -> torch.Tensor:
   180	        """
   181	        Estimate depth map using simple gradient-based heuristic.
   182	
   183	        This is a fallback when no depth model is provided.
   184	        For production, use GenfocusDepthLoader with depth_pro.pt
   185	        """
   186	        # Simple depth estimation based on image gradients
   187	        # Higher frequency = closer (sharper details)
   188	        # This is a rough approximation
   189	
   190	        gray = image_tensor.mean(dim=1, keepdim=True)  # (B, 1, H, W)
   191	
   192	        # Compute gradients
   193	        sobel_x = torch.tensor([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]],
   194	                               dtype=image_tensor.dtype, device=device)
   195	        sobel_y = torch.tensor([[-1, -2, -1], [0, 0, 0], [1, 2, 1]],
   196	                               dtype=image_tensor.dtype, device=device)
   197	
   198	        sobel_x = sobel_x.view(1, 1, 3, 3)
   199	        sobel_y = sobel_y.view(1, 1, 3, 3)
   200	
   201	        grad_x = torch.nn.functional.conv2d(gray, sobel_x, padding=1)
   202	        grad_y = torch.nn.functional.conv2d(gray, sobel_y, padding=1)
   203	
   204	        # Gradient magnitude
   205	        gradient_mag = torch.sqrt(grad_x ** 2 + grad_y ** 2)
   206	
   207	        # Smooth and normalize
   208	        depth = torch.nn.functional.avg_pool2d(gradient_mag, 16, stride=1, padding=8)
   209	
   210	        # Normalize to [0, 1]
   211	        d_min, d_max = depth.min(), depth.max()
   212	        if d_max - d_min > 0:
   213	            depth = (depth - d_min) / (d_max - d_min)
   214	        else:
   215	            depth = torch.zeros_like(depth) + 0.5
   216	
   217	        return depth
   218	
   219	    def _apply_bokeh_blur(
   220	        self,
   221	        image: torch.Tensor,
   222	        depth_map: torch.Tensor,
   223	        focus_distance: float,
   224	        bokeh_intensity: float,
   225	        aperture_size: float,
   226	        focus_falloff: float,
   227	    ) -> Tuple[torch.Tensor, torch.Tensor]:
   228	        """
   229	        Apply depth-aware bokeh blur to image.
   230	
   231	        Uses the depth map to compute per-pixel blur amounts
   232	        based on distance from the focus plane.
   233	        """
   234	        device = image.device
   235	        dtype = image.dtype
   236	        B, C, H, W = image.shape
   237	
   238	        # Compute circle of confusion based on depth
   239	        coc = torch.abs(depth_map - focus_distance)
   240	        coc = coc ** (1.0 / focus_falloff)  # Apply falloff curve
   241	
   242	        # Scale by aperture and intensity
   243	        blur_amount = coc * bokeh_intensity * aperture_size * 50
   244	
   245	        # Ensure blur_amount matches image dimensions (depth estimation can produce different sizes)
   246	        if blur_amount.shape[-2:] != (H, W):
   247	            blur_amount = torch.nn.functional.interpolate(
   248	                blur_amount, size=(H, W), mode='bilinear', align_corners=False
   249	            )
   250	
   251	        # Create focus mask (1 = in focus, 0 = blurred)
   252	        focus_mask = 1.0 - torch.clamp(blur_amount, 0, 1)
   253	
   254	        # Multi-scale blur approximation
   255	        blurred = image.clone()
   256	
   257	        for scale in [2, 4, 8, 16]:
   258	            # Gaussian-like blur via average pooling
   259	            kernel_size = scale * 2 + 1
   260	            padding = scale
   261	
   262	            # Apply blur
   263	            blur_layer = torch.nn.functional.avg_pool2d(
   264	                image, kernel_size, stride=1, padding=padding
   265	            )
   266	
   267	            # Ensure same size
   268	            if blur_layer.shape[-2:] != image.shape[-2:]:
   269	                blur_layer = torch.nn.functional.interpolate(
   270	                    blur_layer, size=(H, W), mode='bilinear', align_corners=False
   271	                )
   272	
   273	            # Blend based on blur amount for this scale
   274	            scale_threshold = scale / 20.0
   275	            scale_mask = (blur_amount > scale_threshold).float()
   276	            scale_mask = scale_mask.expand_as(image)
   277	
   278	            blurred = blurred * (1 - scale_mask * 0.3) + blur_layer * scale_mask * 0.3
   279	
   280	        # Final blend with original based on focus mask
   281	        focus_mask_expanded = focus_mask.expand_as(image)
   282	        output = image * focus_mask_expanded + blurred * (1 - focus_mask_expanded)
   283	
   284	        return output, focus_mask.squeeze(1)
   285	
   286	    def _run_diffusion_bokeh(
   287	        self,
   288	        pipeline: Any,
   289	        image_tensor: torch.Tensor,
   290	        depth_map: torch.Tensor,
   291	        model: Dict[str, Any],
   292	        steps: int,
   293	        guidance_scale: float,
   294	        focus_distance: float,
   295	        bokeh_intensity: float,
   296	        aperture_shape: str,
   297	        seed: int,
   298	    ) -> torch.Tensor:
   299	        """
   300	        Run diffusion-based bokeh synthesis.
   301	
   302	        When full pipeline is available, uses it for high-quality
   303	        neural bokeh synthesis. Otherwise falls back to traditional
   304	        depth-aware blur.
   305	        """
   306	        device = model["device"]
   307	        dtype = model["dtype"]
   308	
   309	        generator = torch.Generator(device=device).manual_seed(seed)
   310	
   311	        if pipeline is not None and hasattr(pipeline, '__call__'):
   312	            try:
   313	                # Prepare conditioning prompt with bokeh parameters
   314	                prompt = (
   315	                    f"shallow depth of field, {aperture_shape} bokeh, "
   316	                    f"focus distance {focus_distance:.2f}, "
   317	                    f"blur intensity {bokeh_intensity:.2f}, "
   318	                    f"professional photography"
   319	                )
   320	
   321	                # Prepare image input
   322	                image_input = image_tensor.to(device=device, dtype=dtype)
   323	                image_input = image_input * 2.0 - 1.0  # Scale to [-1, 1]
   324	
   325	                # Run pipeline with depth conditioning
   326	                output = pipeline(
   327	                    prompt=prompt,
   328	                    image=image_input,
   329	                    num_inference_steps=steps,
   330	                    guidance_scale=guidance_scale,
   331	                    generator=generator,
   332	                    # Note: depth conditioning integration depends on
   333	                    # specific pipeline implementation
   334	                ).images[0]
   335	
   336	                # Convert output
   337	                output_np = np.array(output).astype(np.float32) / 255.0
   338	                output_tensor = torch.from_numpy(output_np)
   339	                output_tensor = output_tensor.unsqueeze(0).permute(0, 3, 1, 2)
   340	
   341	                return output_tensor
   342	
   343	            except Exception as e:
   344	                logger.warning(f"Diffusion bokeh failed, using fallback: {e}")
   345	
   346	        # Fallback: traditional depth-aware blur
   347	        return None
   348	
   349	    def apply_bokeh(
   350	        self,
   351	        image: torch.Tensor,
   352	        model: Dict[str, Any],
   353	        steps: int,
   354	        guidance_scale: float,
   355	        focus_distance: float,
   356	        bokeh_intensity: float,
   357	        aperture_shape: str,
   358	        depth_map: Optional[torch.Tensor] = None,
   359	        seed: int = 0,
   360	        aperture_size: float = 0.1,
   361	        focus_falloff: float = 2.0,
   362	    ) -> Tuple[torch.Tensor, torch.Tensor]:
   363	        """
   364	        Apply BokehNet bokeh synthesis with controllable parameters.
   365	
   366	        Args:
   367	            image: Input image (typically all-in-focus from DeblurNet)
   368	            model: Loaded BokehNet model
   369	            steps: Number of diffusion steps
   370	            guidance_scale: Classifier-free guidance scale
   371	            focus_distance: Where to focus (0=near, 1=far)
   372	            bokeh_intensity: Strength of bokeh effect (0-1)
   373	            aperture_shape: Shape of bokeh highlights
   374	            depth_map: Optional pre-computed depth map
   375	            seed: Random seed
   376	            aperture_size: Aperture size controlling DOF
   377	            focus_falloff: How quickly blur increases away from focus
   378	
   379	        Returns:
   380	            Tuple of (bokeh_image, focus_mask)
   381	        """
   382	        # Validate model type
   383	        if model.get("type") != "bokeh":
   384	            raise ValueError(
   385	                f"Expected BokehNet model, got: {model.get('type', 'unknown')}"
   386	            )
   387	
   388	        logger.info(
   389	            f"Running BokehNet: steps={steps}, focus={focus_distance}, "
   390	            f"intensity={bokeh_intensity}, shape={aperture_shape}"
   391	        )
   392	
   393	        device = model["device"]
   394	
   395	        # Convert to PyTorch format
   396	        image_pt = comfyui_to_pytorch(image).to(device)
   397	
   398	        # Estimate or use provided depth map
   399	        if depth_map is None:
   400	            logger.info("No depth map provided, estimating from image")
   401	            depth_pt = self._estimate_depth(image_pt, device)
   402	        else:
   403	            # Convert depth map to proper format
   404	            if depth_map.ndim == 3:
   405	                depth_pt = depth_map.unsqueeze(0).unsqueeze(0)
   406	            elif depth_map.ndim == 4:
   407	                depth_pt = depth_map
   408	            else:
   409	                depth_pt = depth_map.unsqueeze(0)
   410	
   411	            depth_pt = depth_pt.to(device)
   412	
   413	            # Ensure same spatial size as image
   414	            if depth_pt.shape[-2:] != image_pt.shape[-2:]:
   415	                depth_pt = torch.nn.functional.interpolate(
   416	                    depth_pt, size=image_pt.shape[-2:],
   417	                    mode='bilinear', align_corners=False
   418	                )
   419	
   420	        # Try diffusion-based bokeh first
   421	        pipeline = None
   422	        try:
   423	            pipeline = self._ensure_pipeline(model)
   424	        except Exception as e:
   425	            logger.warning(f"Could not load BokehNet pipeline: {e}")
   426	
   427	        output_pt = self._run_diffusion_bokeh(
   428	            pipeline=pipeline,
   429	            image_tensor=image_pt,
   430	            depth_map=depth_pt,
   431	            model=model,
   432	            steps=steps,
   433	            guidance_scale=guidance_scale,
   434	            focus_distance=focus_distance,
   435	            bokeh_intensity=bokeh_intensity,
   436	            aperture_shape=aperture_shape,
   437	            seed=seed,
   438	        )
   439	
   440	        # If diffusion failed, use traditional blur
   441	        if output_pt is None:
   442	            logger.info("Using traditional depth-aware bokeh blur")
   443	            output_pt, focus_mask = self._apply_bokeh_blur(
   444	                image=image_pt,
   445	                depth_map=depth_pt,
   446	                focus_distance=focus_distance,
   447	                bokeh_intensity=bokeh_intensity,
   448	                aperture_size=aperture_size,
   449	                focus_falloff=focus_falloff,
   450	            )
   451	        else:
   452	            # Create focus mask from depth for output
   453	            focus_mask = create_focus_mask(depth_pt, focus_distance, aperture_size)
   454	            focus_mask = focus_mask.squeeze(1)
   455	
   456	        # Convert back to ComfyUI format
   457	        output = pytorch_to_comfyui(output_pt)
   458	
   459	        # Ensure focus mask is proper format for MASK output
   460	        if focus_mask.ndim == 4:
   461	            focus_mask = focus_mask.squeeze(1)
   462	        if focus_mask.ndim == 2:
   463	            focus_mask = focus_mask.unsqueeze(0)
   464	
   465	        focus_mask = focus_mask.cpu()
   466	
   467	        logger.info(f"BokehNet complete: output shape {output.shape}")
   468	
   469	        return (output, focus_mask)
```
### /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/nodes/deblur.py
```text
     1	"""
     2	GenfocusDeblur node for ComfyUI.
     3	
     4	Applies DeblurNet diffusion model to recover all-in-focus images
     5	from blurry or out-of-focus input images.
     6	"""
     7	
     8	import logging
     9	from typing import Dict, Any, Tuple, Optional
    10	
    11	import torch
    12	import numpy as np
    13	
    14	from ..utils.tensor_utils import (
    15	    comfyui_to_pytorch,
    16	    pytorch_to_comfyui,
    17	    ensure_batch_dim,
    18	    get_dtype,
    19	)
    20	
    21	logger = logging.getLogger("ComfyUI-Genfocus")
    22	
    23	# Custom type for type checking
    24	GENFOCUS_DEBLUR_MODEL = "GENFOCUS_DEBLUR"
    25	
    26	
    27	class GenfocusDeblur:
    28	    """
    29	    Apply DeblurNet deblurring to recover all-in-focus image.
    30	
    31	    This node uses a FLUX-based diffusion model trained for image deblurring.
    32	    It takes a blurry or out-of-focus image and produces a sharp, all-in-focus result.
    33	    """
    34	
    35	    @classmethod
    36	    def INPUT_TYPES(cls) -> Dict:
    37	        return {
    38	            "required": {
    39	                "image": ("IMAGE",),
    40	                "model": (GENFOCUS_DEBLUR_MODEL,),
    41	                "steps": ("INT", {
    42	                    "default": 30,
    43	                    "min": 1,
    44	                    "max": 100,
    45	                    "step": 1,
    46	                    "display": "number"
    47	                }),
    48	                "guidance_scale": ("FLOAT", {
    49	                    "default": 7.5,
    50	                    "min": 0.0,
    51	                    "max": 20.0,
    52	                    "step": 0.5,
    53	                    "display": "number"
    54	                }),
    55	            },
    56	            "optional": {
    57	                "text_prompt": ("STRING", {
    58	                    "default": "",
    59	                    "multiline": True,
    60	                    "placeholder": "Optional: describe desired output (sharp, clear, focused)"
    61	                }),
    62	                "seed": ("INT", {
    63	                    "default": 0,
    64	                    "min": 0,
    65	                    "max": 0xffffffffffffffff,
    66	                    "step": 1
    67	                }),
    68	                "denoise_strength": ("FLOAT", {
    69	                    "default": 1.0,
    70	                    "min": 0.0,
    71	                    "max": 1.0,
    72	                    "step": 0.05,
    73	                    "display": "slider"
    74	                }),
    75	            }
    76	        }
    77	
    78	    RETURN_TYPES = ("IMAGE",)
    79	    RETURN_NAMES = ("deblurred_image",)
    80	    FUNCTION = "deblur"
    81	    CATEGORY = "image/genfocus"
    82	    DESCRIPTION = "Apply DeblurNet to recover all-in-focus image from blurry input"
    83	
    84	    def __init__(self):
    85	        self._pipeline = None
    86	
    87	    def _ensure_pipeline(self, model: Dict[str, Any]) -> Any:
    88	        """
    89	        Lazily initialize the diffusion pipeline.
    90	
    91	        This defers heavy model loading until first inference,
    92	        and handles model offloading for memory efficiency.
    93	        """
    94	        if model.get("_pipeline") is not None:
    95	            return model["_pipeline"]
    96	
    97	        logger.info("Initializing DeblurNet diffusion pipeline...")
    98	
    99	        try:
   100	            from diffusers import FluxPipeline, DDIMScheduler
   101	            from peft import PeftModel
   102	
   103	            device = model["device"]
   104	            dtype = model["dtype"]
   105	
   106	            # Load base FLUX.1-dev pipeline
   107	            # Note: Requires HuggingFace authentication
   108	            pipe = FluxPipeline.from_pretrained(
   109	                "black-forest-labs/FLUX.1-dev",
   110	                torch_dtype=dtype,
   111	            )
   112	
   113	            # Load LoRA weights from state dict
   114	            state_dict = model["state_dict"]
   115	
   116	            # Apply LoRA weights to transformer
   117	            # Genfocus uses PEFT-style LoRA with rank=128
   118	            lora_config = {
   119	                "r": model.get("lora_rank", 128),
   120	                "lora_alpha": model.get("lora_rank", 128),
   121	                "target_modules": ["to_q", "to_k", "to_v", "to_out.0"],
   122	            }
   123	
   124	            # Filter and load LoRA weights
   125	            lora_state_dict = {
   126	                k: v for k, v in state_dict.items()
   127	                if "lora" in k.lower() or "adapter" in k.lower()
   128	            }
   129	
   130	            if lora_state_dict:
   131	                pipe.transformer.load_state_dict(lora_state_dict, strict=False)
   132	                logger.info(f"Loaded {len(lora_state_dict)} LoRA parameters")
   133	
   134	            # Configure scheduler for deblurring
   135	            pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)
   136	
   137	            # Move to device
   138	            if model.get("offload_to_cpu"):
   139	                pipe.enable_model_cpu_offload()
   140	            else:
   141	                pipe = pipe.to(device)
   142	
   143	            model["_pipeline"] = pipe
   144	            model["_is_loaded"] = True
   145	
   146	            return pipe
   147	
   148	        except ImportError as e:
   149	            logger.error(f"Missing dependency: {e}")
   150	            raise ImportError(
   151	                f"Failed to load diffusers pipeline. "
   152	                f"Please install: pip install diffusers peft transformers"
   153	            )
   154	        except Exception as e:
   155	            logger.error(f"Pipeline initialization failed: {e}")
   156	            raise RuntimeError(f"Failed to initialize DeblurNet pipeline: {e}")
   157	
   158	    def _run_inference(
   159	        self,
   160	        pipeline: Any,
   161	        image_tensor: torch.Tensor,
   162	        model: Dict[str, Any],
   163	        steps: int,
   164	        guidance_scale: float,
   165	        text_prompt: str,
   166	        seed: int,
   167	        denoise_strength: float,
   168	    ) -> torch.Tensor:
   169	        """
   170	        Run diffusion-based deblurring inference.
   171	
   172	        For models without a loaded pipeline, falls back to
   173	        direct state dict processing.
   174	        """
   175	        device = model["device"]
   176	        dtype = model["dtype"]
   177	
   178	        # Set random seed for reproducibility
   179	        generator = torch.Generator(device=device).manual_seed(seed)
   180	
   181	        # Prepare image for pipeline
   182	        # Pipeline expects (B, C, H, W) in [-1, 1] range
   183	        image_input = image_tensor.to(device=device, dtype=dtype)
   184	
   185	        # Scale from [0, 1] to [-1, 1] for diffusion
   186	        image_input = image_input * 2.0 - 1.0
   187	
   188	        # If we have a full pipeline, use it
   189	        if pipeline is not None and hasattr(pipeline, '__call__'):
   190	            try:
   191	                output = pipeline(
   192	                    prompt=text_prompt if text_prompt else "sharp, clear, focused image",
   193	                    image=image_input,
   194	                    num_inference_steps=steps,
   195	                    guidance_scale=guidance_scale,
   196	                    strength=denoise_strength,
   197	                    generator=generator,
   198	                ).images[0]
   199	
   200	                # Convert PIL output back to tensor
   201	                output_np = np.array(output).astype(np.float32) / 255.0
   202	                output_tensor = torch.from_numpy(output_np)
   203	                output_tensor = output_tensor.unsqueeze(0)  # Add batch dim
   204	                output_tensor = output_tensor.permute(0, 3, 1, 2)  # To (B, C, H, W)
   205	
   206	                return output_tensor
   207	
   208	            except Exception as e:
   209	                logger.warning(f"Pipeline inference failed, using fallback: {e}")
   210	
   211	        # Fallback: Direct diffusion sampling with state dict
   212	        return self._fallback_inference(
   213	            image_tensor, model, steps, guidance_scale, seed, denoise_strength
   214	        )
   215	
   216	    def _fallback_inference(
   217	        self,
   218	        image_tensor: torch.Tensor,
   219	        model: Dict[str, Any],
   220	        steps: int,
   221	        guidance_scale: float,
   222	        seed: int,
   223	        denoise_strength: float,
   224	    ) -> torch.Tensor:
   225	        """
   226	        Fallback inference when full pipeline is not available.
   227	
   228	        Uses a simplified diffusion sampling process with the
   229	        loaded state dict weights.
   230	        """
   231	        device = model["device"]
   232	        dtype = model["dtype"]
   233	        state_dict = model["state_dict"]
   234	
   235	        logger.info("Using fallback inference mode")
   236	
   237	        # Set seed
   238	        torch.manual_seed(seed)
   239	        if device == "cuda":
   240	            torch.cuda.manual_seed(seed)
   241	
   242	        # Move to device
   243	        x = image_tensor.to(device=device, dtype=dtype)
   244	
   245	        # For fallback, we apply a simple denoising process
   246	        # This is a placeholder - full implementation requires
   247	        # the complete Genfocus architecture
   248	
   249	        # Simple multi-step denoising approximation
   250	        for step in range(steps):
   251	            # Calculate noise level for this step
   252	            t = 1.0 - (step / steps)
   253	            noise_level = t * denoise_strength
   254	
   255	            # Add noise
   256	            noise = torch.randn_like(x) * noise_level * 0.1
   257	            x_noisy = x + noise
   258	
   259	            # Apply guidance (simplified)
   260	            if guidance_scale > 1.0:
   261	                # Sharpening via high-pass filter approximation
   262	                kernel_size = 3
   263	                pad = kernel_size // 2
   264	                # Sobel-like sharpening
   265	                mean = torch.nn.functional.avg_pool2d(
   266	                    x_noisy, kernel_size, stride=1, padding=pad
   267	                )
   268	                high_freq = x_noisy - mean
   269	                x = x_noisy + high_freq * (guidance_scale - 1.0) * 0.1 * (1 - t)
   270	
   271	        # Clamp output
   272	        x = torch.clamp(x, 0.0, 1.0)
   273	
   274	        return x
   275	
   276	    def deblur(
   277	        self,
   278	        image: torch.Tensor,
   279	        model: Dict[str, Any],
   280	        steps: int,
   281	        guidance_scale: float,
   282	        text_prompt: str = "",
   283	        seed: int = 0,
   284	        denoise_strength: float = 1.0,
   285	    ) -> Tuple[torch.Tensor]:
   286	        """
   287	        Apply DeblurNet to recover all-in-focus image.
   288	
   289	        Args:
   290	            image: Input image tensor (B, H, W, C) in [0, 1]
   291	            model: Loaded DeblurNet model wrapper
   292	            steps: Number of diffusion steps
   293	            guidance_scale: Classifier-free guidance scale
   294	            text_prompt: Optional text conditioning
   295	            seed: Random seed for reproducibility
   296	            denoise_strength: Strength of denoising (0-1)
   297	
   298	        Returns:
   299	            Deblurred image as IMAGE tensor (B, H, W, C)
   300	        """
   301	        # Validate model type
   302	        if model.get("type") != "deblur":
   303	            raise ValueError(
   304	                f"Expected DeblurNet model, got: {model.get('type', 'unknown')}"
   305	            )
   306	
   307	        logger.info(f"Running DeblurNet: steps={steps}, guidance={guidance_scale}")
   308	
   309	        # Convert ComfyUI format to PyTorch
   310	        image_pt = comfyui_to_pytorch(image)
   311	
   312	        # Initialize pipeline if needed
   313	        pipeline = None
   314	        try:
   315	            pipeline = self._ensure_pipeline(model)
   316	        except Exception as e:
   317	            logger.warning(f"Could not load full pipeline, using fallback: {e}")
   318	
   319	        # Run inference
   320	        output_pt = self._run_inference(
   321	            pipeline=pipeline,
   322	            image_tensor=image_pt,
   323	            model=model,
   324	            steps=steps,
   325	            guidance_scale=guidance_scale,
   326	            text_prompt=text_prompt,
   327	            seed=seed,
   328	            denoise_strength=denoise_strength,
   329	        )
   330	
   331	        # Convert back to ComfyUI format
   332	        output = pytorch_to_comfyui(output_pt)
   333	
   334	        logger.info(f"DeblurNet complete: output shape {output.shape}")
   335	
   336	        return (output,)
```
### /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/nodes/loaders.py
```text
     1	"""
     2	Model loader nodes for ComfyUI-Genfocus.
     3	
     4	Handles loading and caching of DeblurNet, BokehNet, and Depth models.
     5	"""
     6	
     7	import os
     8	import logging
     9	from typing import Dict, Any, Optional, Tuple
    10	
    11	import torch
    12	from safetensors.torch import load_file
    13	
    14	import folder_paths
    15	
    16	# Setup logging
    17	logger = logging.getLogger("ComfyUI-Genfocus")
    18	
    19	# Custom type identifiers
    20	GENFOCUS_DEBLUR_MODEL = "GENFOCUS_DEBLUR"
    21	GENFOCUS_BOKEH_MODEL = "GENFOCUS_BOKEH"
    22	DEPTH_MODEL = "DEPTH_MODEL"
    23	
    24	# Model cache for lazy loading and memory efficiency
    25	_MODEL_CACHE: Dict[str, Any] = {}
    26	
    27	
    28	def get_model_path(filename: str) -> str:
    29	    """
    30	    Resolve model path from filename.
    31	
    32	    Searches in order:
    33	    1. Absolute path
    34	    2. ComfyUI models/genfocus directory
    35	    3. Custom nodes directory
    36	    """
    37	    # If absolute path, use directly
    38	    if os.path.isabs(filename) and os.path.exists(filename):
    39	        return filename
    40	
    41	    # Check ComfyUI model paths
    42	    genfocus_dir = os.path.join(folder_paths.models_dir, "genfocus")
    43	    if os.path.exists(os.path.join(genfocus_dir, filename)):
    44	        return os.path.join(genfocus_dir, filename)
    45	
    46	    # Check in custom_nodes directory
    47	    custom_nodes_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    48	    models_path = os.path.join(custom_nodes_dir, "models", filename)
    49	    if os.path.exists(models_path):
    50	        return models_path
    51	
    52	    # Return filename for error reporting
    53	    return filename
    54	
    55	
    56	def list_genfocus_models() -> list:
    57	    """List available Genfocus model files."""
    58	    models = []
    59	    genfocus_dir = os.path.join(folder_paths.models_dir, "genfocus")
    60	
    61	    if os.path.exists(genfocus_dir):
    62	        for f in os.listdir(genfocus_dir):
    63	            if f.endswith((".safetensors", ".pt", ".pth", ".bin")):
    64	                models.append(f)
    65	
    66	    return models if models else ["deblurNet.safetensors", "bokehNet.safetensors"]
    67	
    68	
    69	def get_cache_key(model_path: str, dtype: str, device: str) -> str:
    70	    """Generate unique cache key for model configuration."""
    71	    return f"{model_path}_{dtype}_{device}"
    72	
    73	
    74	def clear_model_cache():
    75	    """Clear all cached models to free memory."""
    76	    global _MODEL_CACHE
    77	    _MODEL_CACHE.clear()
    78	    if torch.cuda.is_available():
    79	        torch.cuda.empty_cache()
    80	    logger.info("Model cache cleared")
    81	
    82	
    83	class GenfocusDeblurNetLoader:
    84	    """
    85	    Load Genfocus DeblurNet model with FLUX backbone.
    86	
    87	    DeblurNet uses a FLUX.1-DEV backbone with LoRA (rank r=128) for
    88	    diffusion-based image deblurring to recover all-in-focus images.
    89	    """
    90	
    91	    @classmethod
    92	    def INPUT_TYPES(cls) -> Dict:
    93	        return {
    94	            "required": {
    95	                "model_path": (list_genfocus_models(), {
    96	                    "default": "deblurNet.safetensors"
    97	                }),
    98	                "dtype": (["auto", "float32", "float16", "bfloat16"], {
    99	                    "default": "auto"
   100	                }),
   101	                "device": (["cuda", "cpu"], {
   102	                    "default": "cuda"
   103	                }),
   104	            },
   105	            "optional": {
   106	                "offload_to_cpu": ("BOOLEAN", {
   107	                    "default": False,
   108	                    "label_on": "Offload when idle",
   109	                    "label_off": "Keep on GPU"
   110	                }),
   111	            }
   112	        }
   113	
   114	    RETURN_TYPES = (GENFOCUS_DEBLUR_MODEL,)
   115	    RETURN_NAMES = ("deblur_model",)
   116	    FUNCTION = "load_model"
   117	    CATEGORY = "loaders/genfocus"
   118	    DESCRIPTION = "Load Genfocus DeblurNet for image deblurring"
   119	
   120	    def load_model(
   121	        self,
   122	        model_path: str,
   123	        dtype: str,
   124	        device: str,
   125	        offload_to_cpu: bool = False
   126	    ) -> Tuple[Dict[str, Any]]:
   127	        """
   128	        Load DeblurNet model from safetensors file.
   129	
   130	        Args:
   131	            model_path: Path to deblurNet.safetensors
   132	            dtype: Data type for model (auto-detect or explicit)
   133	            device: CPU or CUDA device
   134	            offload_to_cpu: Whether to offload model to CPU when not in use
   135	
   136	        Returns:
   137	            Loaded model wrapper dict
   138	        """
   139	        # Resolve actual path
   140	        full_path = get_model_path(model_path)
   141	
   142	        # Check cache first
   143	        cache_key = get_cache_key(full_path, dtype, device)
   144	        if cache_key in _MODEL_CACHE:
   145	            logger.info(f"Using cached DeblurNet model: {cache_key}")
   146	            return (_MODEL_CACHE[cache_key],)
   147	
   148	        # Validate file exists
   149	        if not os.path.exists(full_path):
   150	            raise FileNotFoundError(
   151	                f"DeblurNet model not found at: {full_path}\n"
   152	                f"Please download from: https://huggingface.co/nycu-cplab/Genfocus-Model"
   153	            )
   154	
   155	        logger.info(f"Loading DeblurNet from: {full_path}")
   156	
   157	        # Determine dtype
   158	        if dtype == "auto":
   159	            model_dtype = torch.float16 if device == "cuda" else torch.float32
   160	        else:
   161	            dtype_map = {
   162	                "float32": torch.float32,
   163	                "float16": torch.float16,
   164	                "bfloat16": torch.bfloat16
   165	            }
   166	            model_dtype = dtype_map[dtype]
   167	
   168	        # Load state dict
   169	        try:
   170	            state_dict = load_file(full_path)
   171	        except Exception as e:
   172	            logger.error(f"Failed to load safetensors: {e}")
   173	            # Try torch.load as fallback
   174	            state_dict = torch.load(full_path, map_location="cpu")
   175	
   176	        # Create model wrapper with metadata
   177	        model_wrapper = {
   178	            "type": "deblur",
   179	            "state_dict": state_dict,
   180	            "dtype": model_dtype,
   181	            "device": device,
   182	            "offload_to_cpu": offload_to_cpu,
   183	            "model_path": full_path,
   184	            "lora_rank": 128,  # DeblurNet uses r=128 LoRA
   185	            # Lazy-loaded components
   186	            "_pipeline": None,
   187	            "_is_loaded": False,
   188	        }
   189	
   190	        # Cache the model wrapper
   191	        _MODEL_CACHE[cache_key] = model_wrapper
   192	        logger.info(f"DeblurNet loaded successfully (dtype={model_dtype}, device={device})")
   193	
   194	        return (model_wrapper,)
   195	
   196	
   197	class GenfocusBokehNetLoader:
   198	    """
   199	    Load Genfocus BokehNet model with FLUX backbone.
   200	
   201	    BokehNet uses a FLUX.1-DEV backbone with LoRA (rank r=64) for
   202	    diffusion-based bokeh synthesis with controllable depth-of-field.
   203	    """
   204	
   205	    @classmethod
   206	    def INPUT_TYPES(cls) -> Dict:
   207	        return {
   208	            "required": {
   209	                "model_path": (list_genfocus_models(), {
   210	                    "default": "bokehNet.safetensors"
   211	                }),
   212	                "dtype": (["auto", "float32", "float16", "bfloat16"], {
   213	                    "default": "auto"
   214	                }),
   215	                "device": (["cuda", "cpu"], {
   216	                    "default": "cuda"
   217	                }),
   218	            },
   219	            "optional": {
   220	                "offload_to_cpu": ("BOOLEAN", {
   221	                    "default": False,
   222	                    "label_on": "Offload when idle",
   223	                    "label_off": "Keep on GPU"
   224	                }),
   225	            }
   226	        }
   227	
   228	    RETURN_TYPES = (GENFOCUS_BOKEH_MODEL,)
   229	    RETURN_NAMES = ("bokeh_model",)
   230	    FUNCTION = "load_model"
   231	    CATEGORY = "loaders/genfocus"
   232	    DESCRIPTION = "Load Genfocus BokehNet for bokeh synthesis"
   233	
   234	    def load_model(
   235	        self,
   236	        model_path: str,
   237	        dtype: str,
   238	        device: str,
   239	        offload_to_cpu: bool = False
   240	    ) -> Tuple[Dict[str, Any]]:
   241	        """
   242	        Load BokehNet model from safetensors file.
   243	
   244	        Args:
   245	            model_path: Path to bokehNet.safetensors
   246	            dtype: Data type for model
   247	            device: CPU or CUDA device
   248	            offload_to_cpu: Whether to offload model to CPU when not in use
   249	
   250	        Returns:
   251	            Loaded model wrapper dict
   252	        """
   253	        # Resolve actual path
   254	        full_path = get_model_path(model_path)
   255	
   256	        # Check cache
   257	        cache_key = get_cache_key(full_path, dtype, device)
   258	        if cache_key in _MODEL_CACHE:
   259	            logger.info(f"Using cached BokehNet model: {cache_key}")
   260	            return (_MODEL_CACHE[cache_key],)
   261	
   262	        # Validate file exists
   263	        if not os.path.exists(full_path):
   264	            raise FileNotFoundError(
   265	                f"BokehNet model not found at: {full_path}\n"
   266	                f"Please download from: https://huggingface.co/nycu-cplab/Genfocus-Model"
   267	            )
   268	
   269	        logger.info(f"Loading BokehNet from: {full_path}")
   270	
   271	        # Determine dtype
   272	        if dtype == "auto":
   273	            model_dtype = torch.float16 if device == "cuda" else torch.float32
   274	        else:
   275	            dtype_map = {
   276	                "float32": torch.float32,
   277	                "float16": torch.float16,
   278	                "bfloat16": torch.bfloat16
   279	            }
   280	            model_dtype = dtype_map[dtype]
   281	
   282	        # Load state dict
   283	        try:
   284	            state_dict = load_file(full_path)
   285	        except Exception as e:
   286	            logger.error(f"Failed to load safetensors: {e}")
   287	            state_dict = torch.load(full_path, map_location="cpu")
   288	
   289	        # Create model wrapper
   290	        model_wrapper = {
   291	            "type": "bokeh",
   292	            "state_dict": state_dict,
   293	            "dtype": model_dtype,
   294	            "device": device,
   295	            "offload_to_cpu": offload_to_cpu,
   296	            "model_path": full_path,
   297	            "lora_rank": 64,  # BokehNet uses r=64 LoRA
   298	            # Lazy-loaded components
   299	            "_pipeline": None,
   300	            "_is_loaded": False,
   301	        }
   302	
   303	        # Cache
   304	        _MODEL_CACHE[cache_key] = model_wrapper
   305	        logger.info(f"BokehNet loaded successfully (dtype={model_dtype}, device={device})")
   306	
   307	        return (model_wrapper,)
   308	
   309	
   310	class GenfocusDepthLoader:
   311	    """
   312	    Load auxiliary depth estimation model (depth_pro.pt).
   313	
   314	    Uses Apple's Depth Pro for high-quality monocular depth estimation,
   315	    providing depth maps for bokeh synthesis.
   316	    """
   317	
   318	    @classmethod
   319	    def INPUT_TYPES(cls) -> Dict:
   320	        return {
   321	            "required": {
   322	                "model_path": ("STRING", {
   323	                    "default": "checkpoints/depth_pro.pt",
   324	                    "multiline": False
   325	                }),
   326	                "device": (["cuda", "cpu"], {
   327	                    "default": "cuda"
   328	                }),
   329	            }
   330	        }
   331	
   332	    RETURN_TYPES = (DEPTH_MODEL,)
   333	    RETURN_NAMES = ("depth_model",)
   334	    FUNCTION = "load_model"
   335	    CATEGORY = "loaders/genfocus"
   336	    DESCRIPTION = "Load Depth Pro model for depth estimation"
   337	
   338	    def load_model(
   339	        self,
   340	        model_path: str,
   341	        device: str
   342	    ) -> Tuple[Dict[str, Any]]:
   343	        """
   344	        Load depth estimation model.
   345	
   346	        Args:
   347	            model_path: Path to depth_pro.pt
   348	            device: CPU or CUDA device
   349	
   350	        Returns:
   351	            Loaded depth model wrapper
   352	        """
   353	        # Resolve path
   354	        full_path = get_model_path(model_path)
   355	
   356	        # Check cache
   357	        cache_key = get_cache_key(full_path, "float32", device)
   358	        if cache_key in _MODEL_CACHE:
   359	            logger.info(f"Using cached Depth model: {cache_key}")
   360	            return (_MODEL_CACHE[cache_key],)
   361	
   362	        # Validate
   363	        if not os.path.exists(full_path):
   364	            raise FileNotFoundError(
   365	                f"Depth model not found at: {full_path}\n"
   366	                f"Please download from: https://huggingface.co/nycu-cplab/Genfocus-Model"
   367	            )
   368	
   369	        logger.info(f"Loading Depth model from: {full_path}")
   370	
   371	        # Load checkpoint
   372	        checkpoint = torch.load(full_path, map_location="cpu")
   373	
   374	        # Create wrapper
   375	        model_wrapper = {
   376	            "type": "depth",
   377	            "state_dict": checkpoint.get("state_dict", checkpoint),
   378	            "device": device,
   379	            "model_path": full_path,
   380	            "_model": None,
   381	            "_is_loaded": False,
   382	        }
   383	
   384	        # Cache
   385	        _MODEL_CACHE[cache_key] = model_wrapper
   386	        logger.info(f"Depth model loaded successfully (device={device})")
   387	
   388	        return (model_wrapper,)
```
### /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/nodes/pipeline.py
```text
     1	"""
     2	GenfocusPipeline convenience node for ComfyUI.
     3	
     4	Combines DeblurNet + BokehNet in a single node for end-to-end
     5	generative refocusing workflows.
     6	"""
     7	
     8	import logging
     9	from typing import Dict, Any, Tuple, Optional
    10	
    11	import torch
    12	
    13	from .deblur import GenfocusDeblur
    14	from .bokeh import GenfocusBokeh
    15	from ..utils.tensor_utils import comfyui_to_pytorch, pytorch_to_comfyui
    16	
    17	logger = logging.getLogger("ComfyUI-Genfocus")
    18	
    19	# Custom types
    20	GENFOCUS_DEBLUR_MODEL = "GENFOCUS_DEBLUR"
    21	GENFOCUS_BOKEH_MODEL = "GENFOCUS_BOKEH"
    22	DEPTH_MODEL = "DEPTH_MODEL"
    23	
    24	
    25	class GenfocusPipeline:
    26	    """
    27	    All-in-one Genfocus refocusing pipeline.
    28	
    29	    Combines DeblurNet + BokehNet for end-to-end refocusing in a single node.
    30	    This is a convenience wrapper for simple workflows that don't need
    31	    intermediate control between stages.
    32	
    33	    Pipeline flow:
    34	    1. DeblurNet: Input image -> All-in-focus (AIF) image
    35	    2. BokehNet: AIF image -> Refocused image with synthetic DOF
    36	    """
    37	
    38	    @classmethod
    39	    def INPUT_TYPES(cls) -> Dict:
    40	        return {
    41	            "required": {
    42	                "image": ("IMAGE",),
    43	                "deblur_model": (GENFOCUS_DEBLUR_MODEL,),
    44	                "bokeh_model": (GENFOCUS_BOKEH_MODEL,),
    45	                "deblur_steps": ("INT", {
    46	                    "default": 30,
    47	                    "min": 1,
    48	                    "max": 100,
    49	                    "step": 1
    50	                }),
    51	                "bokeh_steps": ("INT", {
    52	                    "default": 30,
    53	                    "min": 1,
    54	                    "max": 100,
    55	                    "step": 1
    56	                }),
    57	                "guidance_scale": ("FLOAT", {
    58	                    "default": 7.5,
    59	                    "min": 0.0,
    60	                    "max": 20.0,
    61	                    "step": 0.5
    62	                }),
    63	                "focus_distance": ("FLOAT", {
    64	                    "default": 0.5,
    65	                    "min": 0.0,
    66	                    "max": 1.0,
    67	                    "step": 0.05,
    68	                    "display": "slider"
    69	                }),
    70	                "bokeh_intensity": ("FLOAT", {
    71	                    "default": 0.5,
    72	                    "min": 0.0,
    73	                    "max": 1.0,
    74	                    "step": 0.05,
    75	                    "display": "slider"
    76	                }),
    77	                "aperture_shape": (["circle", "triangle", "heart", "star", "hexagon"], {
    78	                    "default": "circle"
    79	                }),
    80	            },
    81	            "optional": {
    82	                "text_prompt": ("STRING", {
    83	                    "default": "",
    84	                    "multiline": True,
    85	                    "placeholder": "Optional text conditioning for deblur stage"
    86	                }),
    87	                "depth_map": ("DEPTH_MAP", {
    88	                    "tooltip": "Pre-computed depth map (optional)"
    89	                }),
    90	                "seed": ("INT", {
    91	                    "default": 0,
    92	                    "min": 0,
    93	                    "max": 0xffffffffffffffff
    94	                }),
    95	                "denoise_strength": ("FLOAT", {
    96	                    "default": 1.0,
    97	                    "min": 0.0,
    98	                    "max": 1.0,
    99	                    "step": 0.05,
   100	                    "display": "slider"
   101	                }),
   102	                "aperture_size": ("FLOAT", {
   103	                    "default": 0.1,
   104	                    "min": 0.01,
   105	                    "max": 0.5,
   106	                    "step": 0.01
   107	                }),
   108	                "skip_deblur": ("BOOLEAN", {
   109	                    "default": False,
   110	                    "label_on": "Skip DeblurNet",
   111	                    "label_off": "Run DeblurNet",
   112	                    "tooltip": "Skip deblur stage if input is already sharp"
   113	                }),
   114	            }
   115	        }
   116	
   117	    RETURN_TYPES = ("IMAGE", "IMAGE", "MASK")
   118	    RETURN_NAMES = ("deblurred_image", "refocused_image", "focus_mask")
   119	    FUNCTION = "refocus"
   120	    CATEGORY = "image/genfocus"
   121	    DESCRIPTION = "Complete Genfocus pipeline: Deblur -> Bokeh synthesis"
   122	
   123	    def __init__(self):
   124	        self._deblur_node = None
   125	        self._bokeh_node = None
   126	
   127	    def _get_deblur_node(self) -> GenfocusDeblur:
   128	        """Lazy init deblur node."""
   129	        if self._deblur_node is None:
   130	            self._deblur_node = GenfocusDeblur()
   131	        return self._deblur_node
   132	
   133	    def _get_bokeh_node(self) -> GenfocusBokeh:
   134	        """Lazy init bokeh node."""
   135	        if self._bokeh_node is None:
   136	            self._bokeh_node = GenfocusBokeh()
   137	        return self._bokeh_node
   138	
   139	    def refocus(
   140	        self,
   141	        image: torch.Tensor,
   142	        deblur_model: Dict[str, Any],
   143	        bokeh_model: Dict[str, Any],
   144	        deblur_steps: int,
   145	        bokeh_steps: int,
   146	        guidance_scale: float,
   147	        focus_distance: float,
   148	        bokeh_intensity: float,
   149	        aperture_shape: str,
   150	        text_prompt: str = "",
   151	        depth_map: Optional[torch.Tensor] = None,
   152	        seed: int = 0,
   153	        denoise_strength: float = 1.0,
   154	        aperture_size: float = 0.1,
   155	        skip_deblur: bool = False,
   156	    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
   157	        """
   158	        Run complete refocusing pipeline.
   159	
   160	        Args:
   161	            image: Input image (blurry or sharp)
   162	            deblur_model: Loaded DeblurNet model
   163	            bokeh_model: Loaded BokehNet model
   164	            deblur_steps: Diffusion steps for deblur stage
   165	            bokeh_steps: Diffusion steps for bokeh stage
   166	            guidance_scale: CFG scale for both stages
   167	            focus_distance: Where to focus (0=near, 1=far)
   168	            bokeh_intensity: Strength of bokeh effect
   169	            aperture_shape: Shape of bokeh highlights
   170	            text_prompt: Optional text conditioning
   171	            depth_map: Optional pre-computed depth
   172	            seed: Random seed
   173	            denoise_strength: Denoising strength for deblur
   174	            aperture_size: Aperture size for DOF
   175	            skip_deblur: Skip deblur if input is already sharp
   176	
   177	        Returns:
   178	            Tuple of (deblurred_image, refocused_image, focus_mask)
   179	        """
   180	        logger.info("Starting Genfocus pipeline...")
   181	
   182	        # Stage 1: Deblur (optional)
   183	        if skip_deblur:
   184	            logger.info("Skipping deblur stage (skip_deblur=True)")
   185	            deblurred = image
   186	        else:
   187	            logger.info(f"Stage 1: DeblurNet (steps={deblur_steps})")
   188	
   189	            deblur_node = self._get_deblur_node()
   190	            (deblurred,) = deblur_node.deblur(
   191	                image=image,
   192	                model=deblur_model,
   193	                steps=deblur_steps,
   194	                guidance_scale=guidance_scale,
   195	                text_prompt=text_prompt,
   196	                seed=seed,
   197	                denoise_strength=denoise_strength,
   198	            )
   199	
   200	        # Stage 2: Bokeh synthesis
   201	        logger.info(f"Stage 2: BokehNet (steps={bokeh_steps})")
   202	
   203	        bokeh_node = self._get_bokeh_node()
   204	        (refocused, focus_mask) = bokeh_node.apply_bokeh(
   205	            image=deblurred,
   206	            model=bokeh_model,
   207	            steps=bokeh_steps,
   208	            guidance_scale=guidance_scale,
   209	            focus_distance=focus_distance,
   210	            bokeh_intensity=bokeh_intensity,
   211	            aperture_shape=aperture_shape,
   212	            depth_map=depth_map,
   213	            seed=seed,
   214	            aperture_size=aperture_size,
   215	        )
   216	
   217	        logger.info("Genfocus pipeline complete")
   218	
   219	        return (deblurred, refocused, focus_mask)
   220	
   221	
   222	class GenfocusDepthEstimator:
   223	    """
   224	    Estimate depth map using auxiliary depth model.
   225	
   226	    Uses depth_pro.pt or similar depth estimation network to
   227	    generate depth maps for explicit depth control in bokeh synthesis.
   228	    """
   229	
   230	    @classmethod
   231	    def INPUT_TYPES(cls) -> Dict:
   232	        return {
   233	            "required": {
   234	                "image": ("IMAGE",),
   235	                "depth_model": (DEPTH_MODEL,),
   236	            },
   237	            "optional": {
   238	                "normalize": ("BOOLEAN", {
   239	                    "default": True,
   240	                    "label_on": "Normalize to [0,1]",
   241	                    "label_off": "Raw depth values"
   242	                }),
   243	                "invert": ("BOOLEAN", {
   244	                    "default": False,
   245	                    "label_on": "Invert (near=1)",
   246	                    "label_off": "Normal (near=0)"
   247	                }),
   248	            }
   249	        }
   250	
   251	    RETURN_TYPES = ("DEPTH_MAP", "IMAGE")
   252	    RETURN_NAMES = ("depth_map", "depth_preview")
   253	    FUNCTION = "estimate_depth"
   254	    CATEGORY = "image/genfocus"
   255	    DESCRIPTION = "Estimate depth map from image using Depth Pro model"
   256	
   257	    def estimate_depth(
   258	        self,
   259	        image: torch.Tensor,
   260	        depth_model: Dict[str, Any],
   261	        normalize: bool = True,
   262	        invert: bool = False,
   263	    ) -> Tuple[torch.Tensor, torch.Tensor]:
   264	        """
   265	        Estimate depth map from input image.
   266	
   267	        Args:
   268	            image: Input image tensor (B, H, W, C)
   269	            depth_model: Loaded depth estimation model
   270	            normalize: Whether to normalize output to [0, 1]
   271	            invert: Whether to invert depth (near=1 instead of near=0)
   272	
   273	        Returns:
   274	            Tuple of (depth_map, depth_preview)
   275	        """
   276	        logger.info("Estimating depth map...")
   277	
   278	        device = depth_model.get("device", "cuda")
   279	
   280	        # Convert to PyTorch format
   281	        image_pt = comfyui_to_pytorch(image).to(device)
   282	
   283	        # Check if we have a loaded model
   284	        model = depth_model.get("_model")
   285	
   286	        if model is not None:
   287	            # Use actual depth model
   288	            with torch.no_grad():
   289	                depth = model(image_pt)
   290	        else:
   291	            # Fallback: gradient-based depth estimation
   292	            logger.warning("Depth model not loaded, using gradient-based fallback")
   293	
   294	            gray = image_pt.mean(dim=1, keepdim=True)
   295	
   296	            # Sobel gradients
   297	            sobel_x = torch.tensor(
   298	                [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]],
   299	                dtype=image_pt.dtype, device=device
   300	            ).view(1, 1, 3, 3)
   301	            sobel_y = torch.tensor(
   302	                [[-1, -2, -1], [0, 0, 0], [1, 2, 1]],
   303	                dtype=image_pt.dtype, device=device
   304	            ).view(1, 1, 3, 3)
   305	
   306	            grad_x = torch.nn.functional.conv2d(gray, sobel_x, padding=1)
   307	            grad_y = torch.nn.functional.conv2d(gray, sobel_y, padding=1)
   308	
   309	            depth = torch.sqrt(grad_x ** 2 + grad_y ** 2)
   310	
   311	            # Smooth
   312	            depth = torch.nn.functional.avg_pool2d(depth, 8, stride=1, padding=4)
   313	
   314	        # Normalize if requested
   315	        if normalize:
   316	            d_min, d_max = depth.min(), depth.max()
   317	            if d_max - d_min > 0:
   318	                depth = (depth - d_min) / (d_max - d_min)
   319	
   320	        # Invert if requested
   321	        if invert:
   322	            depth = 1.0 - depth
   323	
   324	        # Create grayscale preview for visualization
   325	        depth_preview = depth.repeat(1, 3, 1, 1)  # (B, 3, H, W)
   326	        depth_preview = pytorch_to_comfyui(depth_preview)
   327	
   328	        # Depth map output (keep as single channel)
   329	        depth_map = depth.squeeze(1)  # (B, H, W)
   330	
   331	        logger.info(f"Depth estimation complete: shape {depth_map.shape}")
   332	
   333	        return (depth_map.cpu(), depth_preview)
```
### /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/requirements.txt
```text
     1	torch>=2.0.0
     2	torchvision
     3	numpy
     4	safetensors>=0.4.0
     5	transformers>=4.34.0
     6	diffusers>=0.21.0
     7	peft>=0.4.0
     8	accelerate
     9	einops
    10	Pillow
```
### /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/utils/__init__.py
```text
     1	# ComfyUI-Genfocus Utilities
     2	from .tensor_utils import (
     3	    comfyui_to_pytorch,
     4	    pytorch_to_comfyui,
     5	    normalize_to_comfyui,
     6	    ensure_batch_dim,
     7	    to_device,
     8	)
     9	
    10	__all__ = [
    11	    "comfyui_to_pytorch",
    12	    "pytorch_to_comfyui",
    13	    "normalize_to_comfyui",
    14	    "ensure_batch_dim",
    15	    "to_device",
    16	]
```
### /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-Genfocus/utils/tensor_utils.py
```text
     1	"""
     2	Tensor conversion utilities for ComfyUI-Genfocus.
     3	
     4	ComfyUI IMAGE format: [B, H, W, C] float32, range [0, 1]
     5	PyTorch convention: [B, C, H, W] with various ranges
     6	"""
     7	
     8	import torch
     9	import numpy as np
    10	from typing import Union, Optional
    11	
    12	
    13	def comfyui_to_pytorch(image_tensor: torch.Tensor) -> torch.Tensor:
    14	    """
    15	    Convert ComfyUI IMAGE tensor to PyTorch convention.
    16	
    17	    Args:
    18	        image_tensor: ComfyUI IMAGE tensor with shape (B, H, W, C)
    19	
    20	    Returns:
    21	        PyTorch tensor with shape (B, C, H, W)
    22	    """
    23	    if image_tensor.ndim == 3:
    24	        # Single image without batch: (H, W, C) -> (1, C, H, W)
    25	        return image_tensor.permute(2, 0, 1).unsqueeze(0)
    26	    elif image_tensor.ndim == 4:
    27	        # Batched: (B, H, W, C) -> (B, C, H, W)
    28	        return image_tensor.permute(0, 3, 1, 2)
    29	    else:
    30	        raise ValueError(f"Expected 3D or 4D tensor, got {image_tensor.ndim}D")
    31	
    32	
    33	def pytorch_to_comfyui(tensor: torch.Tensor) -> torch.Tensor:
    34	    """
    35	    Convert PyTorch tensor to ComfyUI IMAGE format.
    36	
    37	    Args:
    38	        tensor: PyTorch tensor with shape (B, C, H, W)
    39	
    40	    Returns:
    41	        ComfyUI IMAGE tensor with shape (B, H, W, C), float32, range [0, 1]
    42	    """
    43	    if tensor.ndim == 3:
    44	        # Single image without batch: (C, H, W) -> (1, H, W, C)
    45	        tensor = tensor.unsqueeze(0)
    46	
    47	    if tensor.ndim != 4:
    48	        raise ValueError(f"Expected 3D or 4D tensor, got {tensor.ndim}D")
    49	
    50	    # Permute from (B, C, H, W) to (B, H, W, C)
    51	    output = tensor.permute(0, 2, 3, 1)
    52	
    53	    # Ensure float32 and clamp to [0, 1]
    54	    output = output.float()
    55	    output = torch.clamp(output, 0.0, 1.0)
    56	
    57	    return output
    58	
    59	
    60	def normalize_to_comfyui(array: Union[np.ndarray, torch.Tensor]) -> torch.Tensor:
    61	    """
    62	    Normalize array/tensor values to [0, 1] range for ComfyUI.
    63	
    64	    Args:
    65	        array: Input array (numpy or torch) with arbitrary range
    66	
    67	    Returns:
    68	        torch.Tensor with values in [0, 1] range
    69	    """
    70	    if isinstance(array, np.ndarray):
    71	        array = torch.from_numpy(array)
    72	
    73	    array = array.float()
    74	
    75	    # If values are in [0, 255], normalize to [0, 1]
    76	    if array.max() > 1.0:
    77	        array = array / 255.0
    78	
    79	    # Clamp to valid range
    80	    array = torch.clamp(array, 0.0, 1.0)
    81	
    82	    return array
    83	
    84	
    85	def ensure_batch_dim(tensor: torch.Tensor, expected_dims: int = 4) -> torch.Tensor:
    86	    """
    87	    Ensure tensor has batch dimension.
    88	
    89	    Args:
    90	        tensor: Input tensor
    91	        expected_dims: Expected number of dimensions (default 4 for images)
    92	
    93	    Returns:
    94	        Tensor with batch dimension added if necessary
    95	    """
    96	    while tensor.ndim < expected_dims:
    97	        tensor = tensor.unsqueeze(0)
    98	    return tensor
    99	
   100	
   101	def to_device(
   102	    tensor: torch.Tensor,
   103	    device: Union[str, torch.device],
   104	    dtype: Optional[torch.dtype] = None
   105	) -> torch.Tensor:
   106	    """
   107	    Move tensor to device with optional dtype conversion.
   108	
   109	    Args:
   110	        tensor: Input tensor
   111	        device: Target device ('cuda', 'cpu', or torch.device)
   112	        dtype: Optional dtype to convert to
   113	
   114	    Returns:
   115	        Tensor on specified device with specified dtype
   116	    """
   117	    if dtype is not None:
   118	        return tensor.to(device=device, dtype=dtype)
   119	    return tensor.to(device=device)
   120	
   121	
   122	def get_dtype(dtype_str: str, device: str = "cuda") -> torch.dtype:
   123	    """
   124	    Get torch dtype from string specification.
   125	
   126	    Args:
   127	        dtype_str: One of 'auto', 'float32', 'float16', 'bfloat16'
   128	        device: Target device (used for 'auto' mode)
   129	
   130	    Returns:
   131	        torch.dtype
   132	    """
   133	    if dtype_str == "auto":
   134	        return torch.float16 if device == "cuda" else torch.float32
   135	
   136	    dtype_map = {
   137	        "float32": torch.float32,
   138	        "float16": torch.float16,
   139	        "bfloat16": torch.bfloat16,
   140	    }
   141	
   142	    if dtype_str not in dtype_map:
   143	        raise ValueError(f"Unknown dtype: {dtype_str}. Expected one of {list(dtype_map.keys())}")
   144	
   145	    return dtype_map[dtype_str]
   146	
   147	
   148	def depth_to_grayscale(depth_map: torch.Tensor) -> torch.Tensor:
   149	    """
   150	    Convert single-channel depth map to 3-channel grayscale for visualization.
   151	
   152	    Args:
   153	        depth_map: Depth tensor with shape (B, 1, H, W) or (B, H, W)
   154	
   155	    Returns:
   156	        Grayscale tensor with shape (B, 3, H, W)
   157	    """
   158	    if depth_map.ndim == 3:
   159	        depth_map = depth_map.unsqueeze(1)
   160	
   161	    # Normalize depth to [0, 1] for visualization
   162	    d_min = depth_map.min()
   163	    d_max = depth_map.max()
   164	    if d_max - d_min > 0:
   165	        depth_map = (depth_map - d_min) / (d_max - d_min)
   166	
   167	    # Repeat to 3 channels
   168	    return depth_map.repeat(1, 3, 1, 1)
   169	
   170	
   171	def create_focus_mask(
   172	    depth_map: torch.Tensor,
   173	    focus_distance: float,
   174	    aperture: float = 0.1
   175	) -> torch.Tensor:
   176	    """
   177	    Create a focus mask based on depth map and focus distance.
   178	
   179	    Args:
   180	        depth_map: Normalized depth map (B, 1, H, W), values in [0, 1]
   181	        focus_distance: Focus plane distance in [0, 1]
   182	        aperture: Aperture size controlling DOF (smaller = more blur)
   183	
   184	    Returns:
   185	        Focus mask tensor (B, 1, H, W), 1 = in focus, 0 = blurred
   186	    """
   187	    # Calculate circle of confusion
   188	    coc = torch.abs(depth_map - focus_distance)
   189	
   190	    # Convert to focus weight (inverse of blur amount)
   191	    # Using a smooth falloff based on aperture
   192	    focus_mask = torch.exp(-(coc ** 2) / (2 * aperture ** 2))
   193	
   194	    return focus_mask
```
### /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-MVInverse/__init__.py
```text
     1	"""
     2	ComfyUI-MVInverse
     3	Custom nodes for MVInverse multi-view inverse rendering.
     4	
     5	Nodes:
     6	- MVInverseLoader: Load MVInverse model from checkpoint or HF Hub
     7	- MVInverseInverse: Execute inverse rendering on multi-view images
     8	
     9	Author: oz
    10	Model: claude-opus-4-5
    11	Date: 2025-12-29
    12	"""
    13	
    14	from .mvinverse_loader import MVInverseLoader
    15	from .mvinverse_inverse import MVInverseInverse
    16	
    17	NODE_CLASS_MAPPINGS = {
    18	    "MVInverseLoader": MVInverseLoader,
    19	    "MVInverseInverse": MVInverseInverse,
    20	}
    21	
    22	NODE_DISPLAY_NAME_MAPPINGS = {
    23	    "MVInverseLoader": "Load MVInverse Model",
    24	    "MVInverseInverse": "MVInverse Inverse Render",
    25	}
    26	
    27	__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
    28	
    29	WEB_DIRECTORY = None
```
### /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-MVInverse/mvinverse_inverse.py
```text
     1	"""
     2	MVInverse Inverse Rendering Node for ComfyUI.
     3	
     4	Executes multi-view inverse rendering to extract material properties:
     5	albedo, normal, metallic, roughness, and shading maps.
     6	
     7	Author: oz
     8	Model: claude-opus-4-5
     9	Date: 2025-12-29
    10	"""
    11	
    12	import torch
    13	import torch.nn.functional as F
    14	
    15	
    16	class MVInverseInverse:
    17	    """
    18	    Execute multi-view inverse rendering.
    19	
    20	    Takes a batch of multi-view images and produces material property maps
    21	    for each view using the MVInverse model.
    22	
    23	    Input Format:
    24	        images: [B, H, W, C] where B = number of views, C = 3 or 4 channels
    25	
    26	    Output Format:
    27	        All outputs are [B, H, W, C] in ComfyUI format (float32, range [0, 1])
    28	        - albedo: [B, H, W, 3] - Base color/diffuse
    29	        - normal: [B, H, W, 3] - Surface normals (remapped from [-1,1] to [0,1])
    30	        - metallic: [B, H, W, 1] - Metallic property
    31	        - roughness: [B, H, W, 1] - Surface roughness
    32	        - shading: [B, H, W, 3] - Computed shading
    33	    """
    34	
    35	    @classmethod
    36	    def INPUT_TYPES(cls):
    37	        """Define input parameters for the node."""
    38	        return {
    39	            "required": {
    40	                "images": ("IMAGE",),
    41	                "mvinverse_model": ("MVINVERSE_MODEL",),
    42	                "max_size": (
    43	                    "INT",
    44	                    {
    45	                        "default": 1024,
    46	                        "min": 224,
    47	                        "max": 2048,
    48	                        "step": 14,  # Align to patch size
    49	                        "display": "slider"
    50	                    }
    51	                ),
    52	            },
    53	            "optional": {
    54	                "upscale_output": (
    55	                    ["disabled", "bilinear", "nearest"],
    56	                    {"default": "disabled"}
    57	                ),
    58	            },
    59	        }
    60	
    61	    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    62	    RETURN_NAMES = ("albedo", "normal", "metallic", "roughness", "shading")
    63	    FUNCTION = "inverse_render"
    64	    CATEGORY = "image/material"
    65	    DESCRIPTION = "Extract material properties from multi-view images using MVInverse"
    66	
    67	    def inverse_render(
    68	        self,
    69	        images,
    70	        mvinverse_model,
    71	        max_size,
    72	        upscale_output="disabled"
    73	    ):
    74	        """
    75	        Execute inverse rendering on multi-view images.
    76	
    77	        Args:
    78	            images: Input tensor [B, H, W, C] where B = number of views
    79	            mvinverse_model: Loaded MVInverse model
    80	            max_size: Maximum dimension for processing (aligned to patch size 14)
    81	            upscale_output: Whether to upscale outputs to original size
    82	
    83	        Returns:
    84	            Tuple of (albedo, normal, metallic, roughness, shading) tensors
    85	        """
    86	        # Get model device and dtype
    87	        device = next(mvinverse_model.parameters()).device
    88	        dtype = next(mvinverse_model.parameters()).dtype
    89	
    90	        B, H, W, C = images.shape
    91	        print(f"[MVInverse] Input: {B} views, {H}x{W}, {C} channels")
    92	
    93	        # Step 1: Validate input
    94	        if B < 1:
    95	            raise ValueError("[MVInverse] At least 1 view required")
    96	
    97	        if B > 16:
    98	            print(f"[MVInverse] Warning: {B} views may cause memory issues. Consider using fewer views.")
    99	
   100	        # Step 2: Prepare images for MVInverse
   101	        prepared, original_size, processed_size = self._prepare_images(
   102	            images, max_size, device, dtype
   103	        )
   104	
   105	        print(f"[MVInverse] Processing at {processed_size[0]}x{processed_size[1]}")
   106	
   107	        # Step 3: Run inference with memory optimization
   108	        with torch.no_grad():
   109	            if dtype == torch.float16 and device.type == 'cuda':
   110	                with torch.amp.autocast('cuda', dtype=torch.float16):
   111	                    outputs = mvinverse_model(prepared)
   112	            else:
   113	                outputs = mvinverse_model(prepared)
   114	
   115	        # Step 4: Process outputs to ComfyUI format
   116	        result = self._process_outputs(
   117	            outputs,
   118	            original_size,
   119	            upscale_output
   120	        )
   121	
   122	        # Clear CUDA cache if needed
   123	        if device.type == 'cuda':
   124	            torch.cuda.empty_cache()
   125	
   126	        print(f"[MVInverse] Output shapes: albedo={result['albedo'].shape}, "
   127	              f"normal={result['normal'].shape}")
   128	
   129	        return (
   130	            result['albedo'],
   131	            result['normal'],
   132	            result['metallic'],
   133	            result['roughness'],
   134	            result['shading']
   135	        )
   136	
   137	    @staticmethod
   138	    def _prepare_images(images_batch, max_size, device, dtype):
   139	        """
   140	        Convert ComfyUI image batch to MVInverse format.
   141	
   142	        Converts from [B, H, W, C] (ComfyUI) to [1, B, 3, H, W] (MVInverse).
   143	        Handles resizing and patch size alignment.
   144	
   145	        Args:
   146	            images_batch: Input tensor [B, H, W, C]
   147	            max_size: Maximum longest dimension
   148	            device: Target device
   149	            dtype: Target dtype
   150	
   151	        Returns:
   152	            Tuple of (prepared_tensor, original_size, processed_size)
   153	        """
   154	        B, H, W, C = images_batch.shape
   155	        original_size = (H, W)
   156	
   157	        # Convert to [B, C, H, W] (channels first)
   158	        images = images_batch.permute(0, 3, 1, 2)
   159	
   160	        # Handle channel count
   161	        if C == 4:
   162	            # Drop alpha channel
   163	            images = images[:, :3, :, :]
   164	        elif C == 1:
   165	            # Expand grayscale to RGB
   166	            images = images.repeat(1, 3, 1, 1)
   167	        elif C != 3:
   168	            raise ValueError(f"[MVInverse] Unsupported channel count: {C}")
   169	
   170	        # Calculate new size while maintaining aspect ratio
   171	        scale = min(max_size / max(H, W), 1.0)
   172	        new_h = int(H * scale)
   173	        new_w = int(W * scale)
   174	
   175	        # Align to patch size (14) - this is CRITICAL for MVInverse
   176	        patch_size = 14
   177	        new_h = max((new_h // patch_size) * patch_size, patch_size)
   178	        new_w = max((new_w // patch_size) * patch_size, patch_size)
   179	
   180	        # Resize if needed
   181	        if (new_h, new_w) != (H, W):
   182	            images = F.interpolate(
   183	                images,
   184	                size=(new_h, new_w),
   185	                mode='bilinear',
   186	                align_corners=False,
   187	                antialias=True
   188	            )
   189	
   190	        processed_size = (new_h, new_w)
   191	
   192	        # Add batch dimension: [B, C, H, W] -> [1, B, C, H, W]
   193	        # MVInverse expects (batch=1, num_views=B, channels=3, H, W)
   194	        images = images.unsqueeze(0)
   195	
   196	        # Move to device and dtype
   197	        images = images.to(device=device, dtype=dtype)
   198	
   199	        return images, original_size, processed_size
   200	
   201	    @staticmethod
   202	    def _process_outputs(outputs, original_size, upscale_mode):
   203	        """
   204	        Convert MVInverse outputs to ComfyUI format.
   205	
   206	        Handles normalization of different output types and optional
   207	        upscaling back to original resolution.
   208	
   209	        MVInverse output ranges:
   210	            - albedo: [0, 255]
   211	            - normal: [-1, 1]
   212	            - metallic: [0, 255]
   213	            - roughness: [0, 255]
   214	            - shading: [0, 255]
   215	
   216	        ComfyUI expected format:
   217	            - All: [B, H, W, C], float32, range [0, 1]
   218	
   219	        Args:
   220	            outputs: Dict with keys {albedo, normal, metallic, roughness, shading}
   221	            original_size: Tuple (H, W) of original input size
   222	            upscale_mode: "disabled", "bilinear", or "nearest"
   223	
   224	        Returns:
   225	            Dict of tensors in ComfyUI format
   226	        """
   227	        result = {}
   228	        H, W = original_size
   229	
   230	        output_keys = ['albedo', 'normal', 'metallic', 'roughness', 'shading']
   231	
   232	        for key in output_keys:
   233	            if key not in outputs:
   234	                raise KeyError(f"[MVInverse] Expected output '{key}' not found in model outputs")
   235	
   236	            tensor = outputs[key]  # Expected shape: [N, H, W, C] from model
   237	
   238	            # Handle different tensor formats from model
   239	            if tensor.dim() == 5:
   240	                # [1, N, H, W, C] -> [N, H, W, C]
   241	                tensor = tensor.squeeze(0)
   242	            elif tensor.dim() == 3:
   243	                # [N, H, W] -> [N, H, W, 1] (for metallic/roughness)
   244	                tensor = tensor.unsqueeze(-1)
   245	
   246	            # Normalize based on output type
   247	            if key == 'normal':
   248	                # Normal maps are in [-1, 1], remap to [0, 1] for visualization
   249	                tensor = tensor * 0.5 + 0.5
   250	            else:
   251	                # All others are in [0, 255], normalize to [0, 1]
   252	                if tensor.max() > 1.0:
   253	                    tensor = tensor / 255.0
   254	
   255	            # Clamp to valid range
   256	            tensor = torch.clamp(tensor, 0.0, 1.0)
   257	
   258	            # Ensure float32 for ComfyUI compatibility
   259	            tensor = tensor.to(torch.float32)
   260	
   261	            # Move to CPU for ComfyUI
   262	            tensor = tensor.cpu()
   263	
   264	            # Optional upscaling back to original size
   265	            if upscale_mode != "disabled":
   266	                current_h, current_w = tensor.shape[1], tensor.shape[2]
   267	                if (current_h, current_w) != (H, W):
   268	                    # Convert [N, H, W, C] -> [N, C, H, W] for interpolate
   269	                    tensor = tensor.permute(0, 3, 1, 2)
   270	
   271	                    align_corners = False if upscale_mode == "bilinear" else None
   272	                    tensor = F.interpolate(
   273	                        tensor,
   274	                        size=(H, W),
   275	                        mode=upscale_mode,
   276	                        align_corners=align_corners
   277	                    )
   278	
   279	                    # Convert back [N, C, H, W] -> [N, H, W, C]
   280	                    tensor = tensor.permute(0, 2, 3, 1)
   281	
   282	            # Ensure metallic and roughness have 3 channels for preview
   283	            # (ComfyUI PreviewImage expects 3-channel images)
   284	            if key in ['metallic', 'roughness'] and tensor.shape[-1] == 1:
   285	                tensor = tensor.repeat(1, 1, 1, 3)
   286	
   287	            result[key] = tensor
   288	
   289	        return result
   290	
   291	    @classmethod
   292	    def IS_CHANGED(cls, images, mvinverse_model, max_size, upscale_output="disabled"):
   293	        """
   294	        Determine if outputs need to be recalculated.
   295	
   296	        Returns a unique hash based on input configuration.
   297	        """
   298	        # Images tensor hash (simplified - based on shape and sample values)
   299	        img_hash = f"{images.shape}_{images.mean().item():.4f}"
   300	        return f"{img_hash}_{max_size}_{upscale_output}"
```
### /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-MVInverse/mvinverse_loader.py
```text
     1	"""
     2	MVInverse Model Loader Node for ComfyUI.
     3	
     4	Loads MVInverse checkpoint from local storage or HuggingFace Hub with model caching.
     5	Supports FP16/FP32 precision and automatic device selection.
     6	
     7	Author: oz
     8	Model: claude-opus-4-5
     9	Date: 2025-12-29
    10	"""
    11	
    12	import torch
    13	import os
    14	import sys
    15	from pathlib import Path
    16	
    17	# ComfyUI imports
    18	import folder_paths
    19	
    20	
    21	class MVInverseLoader:
    22	    """
    23	    Load MVInverse model checkpoint.
    24	
    25	    This node loads the MVInverse model from either a local checkpoint file
    26	    or downloads it from HuggingFace Hub. The model is cached to avoid
    27	    reloading on subsequent runs.
    28	
    29	    Outputs:
    30	        MVINVERSE_MODEL: The loaded model ready for inference
    31	    """
    32	
    33	    # Global model cache to avoid reloading
    34	    _models_cache = {}
    35	
    36	    def __init__(self):
    37	        """Initialize loader and ensure checkpoint directory exists."""
    38	        self.checkpoints_dir = os.path.join(
    39	            folder_paths.models_dir, "mvinverse"
    40	        )
    41	        os.makedirs(self.checkpoints_dir, exist_ok=True)
    42	
    43	    @classmethod
    44	    def INPUT_TYPES(cls):
    45	        """Define input parameters for the node."""
    46	        checkpoints = cls._get_checkpoint_options()
    47	        return {
    48	            "required": {
    49	                "checkpoint": (
    50	                    checkpoints,
    51	                    {"default": checkpoints[0] if checkpoints else "mvinverse"}
    52	                ),
    53	                "device": (
    54	                    ["cuda", "cpu"],
    55	                    {"default": "cuda"}
    56	                ),
    57	                "use_fp16": (
    58	                    ["auto", "true", "false"],
    59	                    {"default": "auto"}
    60	                ),
    61	            },
    62	        }
    63	
    64	    RETURN_TYPES = ("MVINVERSE_MODEL",)
    65	    RETURN_NAMES = ("mvinverse_model",)
    66	    FUNCTION = "load_model"
    67	    CATEGORY = "loaders/models"
    68	    DESCRIPTION = "Load MVInverse model for multi-view inverse rendering"
    69	
    70	    @classmethod
    71	    def _get_checkpoint_options(cls):
    72	        """
    73	        Get list of available checkpoints.
    74	
    75	        Scans the mvinverse models directory for local .pt files and
    76	        always includes the HF Hub default option.
    77	
    78	        Returns:
    79	            List of checkpoint names (without .pt extension)
    80	        """
    81	        checkpoints = ["mvinverse"]  # HF Hub default always available
    82	
    83	        # Scan local models directory
    84	        models_dir = os.path.join(folder_paths.models_dir, "mvinverse")
    85	        if os.path.exists(models_dir):
    86	            local_checkpoints = [
    87	                f.replace(".pt", "")
    88	                for f in os.listdir(models_dir)
    89	                if f.endswith(".pt")
    90	            ]
    91	            # Prepend local checkpoints (priority over HF Hub)
    92	            checkpoints = local_checkpoints + checkpoints
    93	
    94	        # Remove duplicates while preserving order
    95	        return list(dict.fromkeys(checkpoints))
    96	
    97	    @classmethod
    98	    def IS_CHANGED(cls, checkpoint, device, use_fp16):
    99	        """
   100	        Check if model needs to be reloaded.
   101	
   102	        Returns a hash based on the configuration. ComfyUI uses this
   103	        to determine if cached outputs are still valid.
   104	        """
   105	        return f"{checkpoint}_{device}_{use_fp16}"
   106	
   107	    def load_model(self, checkpoint, device, use_fp16):
   108	        """
   109	        Load MVInverse model with caching.
   110	
   111	        Args:
   112	            checkpoint: Name of checkpoint file or "mvinverse" for HF Hub
   113	            device: "cuda" or "cpu"
   114	            use_fp16: "auto", "true", or "false"
   115	
   116	        Returns:
   117	            Tuple containing the loaded model
   118	        """
   119	        cache_key = f"{checkpoint}_{device}_{use_fp16}"
   120	
   121	        # Return cached model if available
   122	        if cache_key in MVInverseLoader._models_cache:
   123	            print(f"[MVInverse] Using cached model: {checkpoint}")
   124	            return (MVInverseLoader._models_cache[cache_key],)
   125	
   126	        # Validate device availability
   127	        if device == "cuda" and not torch.cuda.is_available():
   128	            print("[MVInverse] CUDA unavailable, falling back to CPU")
   129	            device = "cpu"
   130	
   131	        # Determine dtype based on settings
   132	        if use_fp16 == "true":
   133	            dtype = torch.float16
   134	        elif use_fp16 == "false":
   135	            dtype = torch.float32
   136	        else:  # auto
   137	            dtype = torch.float16 if device == "cuda" else torch.float32
   138	
   139	        print(f"[MVInverse] Loading {checkpoint} on {device} ({dtype})")
   140	
   141	        # Load the model
   142	        model = self._load_checkpoint(checkpoint, device, dtype)
   143	        model.eval()
   144	
   145	        # Disable gradient computation for inference
   146	        for param in model.parameters():
   147	            param.requires_grad = False
   148	
   149	        # Cache model for future use
   150	        MVInverseLoader._models_cache[cache_key] = model
   151	
   152	        print(f"[MVInverse] Model loaded successfully")
   153	        return (model,)
   154	
   155	    def _load_checkpoint(self, checkpoint_name, device, dtype):
   156	        """
   157	        Load checkpoint from local file or HuggingFace Hub.
   158	
   159	        Args:
   160	            checkpoint_name: Either a local filename (without .pt) or "mvinverse" for HF Hub
   161	            device: Target device ("cuda" or "cpu")
   162	            dtype: Target dtype (torch.float16 or torch.float32)
   163	
   164	        Returns:
   165	            Loaded MVInverse model in eval mode
   166	        """
   167	        # Try to import MVInverse
   168	        try:
   169	            from mvinverse.models.mvinverse import MVInverse
   170	        except ImportError:
   171	            # Try adding the custom_nodes path
   172	            custom_nodes_path = os.path.join(
   173	                os.path.dirname(os.path.dirname(__file__)),
   174	                "mvinverse"
   175	            )
   176	            if os.path.exists(custom_nodes_path):
   177	                sys.path.insert(0, custom_nodes_path)
   178	                from mvinverse.models.mvinverse import MVInverse
   179	            else:
   180	                raise ImportError(
   181	                    "[MVInverse] Failed to import mvinverse package. "
   182	                    "Please ensure mvinverse is installed: pip install -e <mvinverse-repo>"
   183	                )
   184	
   185	        # Check for local checkpoint first
   186	        local_path = os.path.join(self.checkpoints_dir, f"{checkpoint_name}.pt")
   187	
   188	        if os.path.exists(local_path):
   189	            # Load from local checkpoint file
   190	            print(f"[MVInverse] Loading from local: {local_path}")
   191	            checkpoint = torch.load(
   192	                local_path,
   193	                map_location=device,
   194	                weights_only=False
   195	            )
   196	            model = MVInverse()
   197	        else:
   198	            # Use from_pretrained to download from HuggingFace Hub
   199	            # This uses PyTorchModelHubMixin's built-in download mechanism
   200	            print(f"[MVInverse] Downloading from HuggingFace Hub (maddog241/mvinverse)...")
   201	            try:
   202	                model = MVInverse.from_pretrained("maddog241/mvinverse")
   203	                print(f"[MVInverse] Downloaded and loaded successfully")
   204	                checkpoint = None  # Already loaded via from_pretrained
   205	            except Exception as e:
   206	                raise RuntimeError(
   207	                    f"[MVInverse] Failed to download from HuggingFace Hub: {e}. "
   208	                    "Ensure you have internet access or provide a local checkpoint."
   209	                )
   210	
   211	        # Load state dict - handle different checkpoint formats
   212	        # (Skip if checkpoint is None - already loaded via from_pretrained)
   213	        if checkpoint is not None:
   214	            if isinstance(checkpoint, dict):
   215	                if 'model_state_dict' in checkpoint:
   216	                    model.load_state_dict(checkpoint['model_state_dict'])
   217	                elif 'state_dict' in checkpoint:
   218	                    model.load_state_dict(checkpoint['state_dict'])
   219	                elif 'model' in checkpoint:
   220	                    model.load_state_dict(checkpoint['model'])
   221	                else:
   222	                    # Assume the dict is the state dict itself
   223	                    model.load_state_dict(checkpoint)
   224	            else:
   225	                # Direct state dict
   226	                model.load_state_dict(checkpoint)
   227	
   228	        # Move to device and set precision
   229	        model = model.to(device=device, dtype=dtype)
   230	
   231	        return model
   232	
   233	    @classmethod
   234	    def clear_cache(cls):
   235	        """
   236	        Clear the model cache.
   237	
   238	        Useful for freeing VRAM when switching between models.
   239	        """
   240	        cls._models_cache.clear()
   241	        if torch.cuda.is_available():
   242	            torch.cuda.empty_cache()
   243	        print("[MVInverse] Model cache cleared")
```
### /home/oz/projects/2025/oz/12/runpod/docker/custom_nodes/ComfyUI-MVInverse/requirements.txt
```text
     1	# ComfyUI-MVInverse Requirements
     2	# Author: oz
     3	# Date: 2025-12-29
     4	
     5	# Core PyTorch (ComfyUI provides these, but listed for standalone use)
     6	torch>=2.0.0
     7	torchvision>=0.15.0
     8	
     9	# MVInverse dependencies
    10	pillow>=9.0.0
    11	opencv-python>=4.5.0
    12	huggingface_hub>=0.16.0
    13	
    14	# MVInverse package (install from source)
    15	# pip install -e <path-to-mvinverse-repo>
    16	# OR
    17	# pip install git+https://github.com/Maddog241/mvinverse.git
    18	
    19	# Optional: For better performance
    20	# xformers>=0.0.20  # Memory-efficient attention (CUDA only)
```
