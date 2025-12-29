# RunPod & R2 Deployment Research Report

This report provides a comprehensive guide to configuring RunPod templates, integrating Cloudflare R2 with boto3, optimizing Docker registries, and handling ComfyUI outputs efficiently.

---

## 1. RunPod Template Configuration

RunPod templates are the blueprint for deploying GPU-accelerated containers. Custom templates allow for reproducible environments tailored to specific ML workflows.

### Key Configuration Components

*   **Environment Variables:**
    *   **Runtime vs. Build-time:** Define sensitive API keys or dynamic configs at runtime in the RunPod console. Use build-time variables (Dockerfile `ENV`) for static defaults.
    *   **Built-in Variables:** RunPod injects `RUNPOD_POD_ID`, `RUNPOD_API_KEY`, and `RUNPOD_POD_HOSTNAME` automatically.
    *   **Secrets:** For high-security credentials, use RunPod's Secret manager rather than plain environment variables.
*   **Volume Mounts:**
    *   **Container Disk:** Ephemeral storage for OS and packages. Wiped on pod restart.
    *   **Volume Disk (Local):** Persistent storage attached to the pod (e.g., `/workspace`). Persists across restarts but is tied to the specific pod.
    *   **Network Volume:** Shared storage that can be mounted across multiple pods or serverless endpoints (mounted at `/runpod-volume`). Ideal for sharing model weights.
*   **Network Ports:**
    *   **HTTP Ports:** Proxied via RunPod (HTTPS). Limit of 10 ports.
    *   **TCP Ports:** Direct raw TCP access. Use ports above `70000` to request symmetrical mapping (matching internal and external port numbers).

### Best Practices
- Always mount heavy assets (models, large datasets) to the **Volume Disk** to avoid long download times on pod startup.
- Use the `/workspace` directory as the primary mount point for persistent data.

---

## 2. R2/S3 Integration with boto3

Cloudflare R2 is S3-compatible, allowing the use of the `boto3` library for efficient file management.

### Boto3 Client Configuration
To connect to R2, you must override the `endpoint_url` and use Cloudflare-specific credentials.

```python
import boto3
from botocore.config import Config

def get_r2_client(account_id, access_key, secret_key):
    return boto3.client(
        service_name="s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=Config(signature_version="s3v4")
    )
```

### Uploading with Progress Tracking
For large files, using a callback with `upload_file` provides real-time feedback.

```python
import os
import sys
import threading

class ProgressPercentage:
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(f"\r{self._filename}  {self._seen_so_far} / {self._size}  ({percentage:.2f}%)")
            sys.stdout.flush()

# Multipart configuration
from boto3.s3.transfer import TransferConfig
config = TransferConfig(multipart_threshold=1024 * 25, max_concurrency=10)

s3.upload_file('large_file.zip', 'my-bucket', 'remote_key', 
               Config=config, Callback=ProgressPercentage('large_file.zip'))
```

---

## 3. Docker Registry Options & Optimization

Choosing the right registry and optimizing image size are critical for fast deployment on RunPod.

### Registry Comparison
| Feature | GHCR (GitHub) | Private VPS (Harbor) |
| :--- | :--- | :--- |
| **Ease of Setup** | Low (Integrated with GitHub Actions) | High (Requires VPS management) |
| **Cost** | Usage-based (Free for public) | Fixed VPS cost |
| **Security** | RBAC, Repository-linked | Vulnerability scanning (Trivy), Signing |
| **Performance** | Global CDN | Localized to your VPS region |

### Image Size Optimization: Multi-Stage Builds
Multi-stage builds allow you to keep the final production image small by discarding build-time dependencies.

```dockerfile
# Stage 1: Build
FROM python:3.10-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Final Runtime
FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "main.py"]
```

---

## 4. ComfyUI Output Handling

ComfyUI stores results locally, but automated workflows require reliable post-processing and synchronization.

### Directory Structure & Organization
- **Custom Output Path:** Use `--output-directory /workspace/outputs` at startup.
- **Dynamic Subfolders:** Use patterns in the `Save Image` node (e.g., `%date:yyyy-MM-dd%/%basename%_%counter%`) to keep files organized.

### Background Sync with `inotifywait`
To automatically sync outputs to R2, use a background script monitoring the output folder.

```bash
#!/bin/bash
WATCH_DIR="/workspace/outputs"

inotifywait -m -r -e close_write --format '%w%f' "$WATCH_DIR" | while read FILE
do
    if [[ "$FILE" =~ \.(png|jpg|webp)$ ]]; then
        echo "New file detected: $FILE"
        # Trigger python script to upload to R2
        python3 upload_to_r2.py "$FILE" &
    fi
done
```

---

## Best Practices & Potential Pitfalls

1.  **RunPod Timeouts:** Long-running uploads can be interrupted if the pod is pre-empted. Implement robust retry logic in `boto3`.
2.  **R2 Class B Operations:** Frequent `ListObjects` or small writes can incur higher costs. Batch your metadata operations where possible.
3.  **Docker Layers:** Order your Dockerfile commands from least-frequently changed to most-frequently changed to maximize layer caching.
4.  **Inotify Limits:** Large directory structures can hit the system `fs.inotify.max_user_watches` limit. Monitor subdirectories selectively.

---

*End of Report*
