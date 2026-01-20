# Media Analysis API Cloning & Architecture Research

## 1. Executive Summary
This research focuses on cloning the legacy `cotizador-api` (monolithic) into a modern, modular `media-analysis` service. The target architecture uses a multi-branch API structure (audio/video/document) running in isolated Docker containers, routed via Caddy.

**Key Findings:**
- The source `cotizador-api` is a ~8,000-line monolith; cloning requires a **Decomposition Strategy** rather than a direct copy-paste.
- **Identifier Collision Avoidance** is best handled by combining **Service Prefixes** (e.g., `ma_`) with **ULIDs** for lexicographical sortability.
- **Multi-Branch Architecture** should be implemented using FastAPI's `APIRouter` to isolate domain logic.
- **Networking isolation** via a dedicated Docker bridge network (`media-services-network`) ensures secure inter-service communication without port exposure.

---

## 2. API Cloning Best Practices (FastAPI)

### Refactoring from Monolith to Modular
The source `cotizador_api.py` contains 30+ endpoints in a single file. For the new service:
1. **Domain Isolation**: Split `cotizador.py` and `cotizador_api.py` logic into domain-specific modules.
2. **Layered Architecture**: Use a three-layer pattern to prevent logic leakage:
   - **Routers**: Handle HTTP, validation, and status codes.
   - **Services**: Orchestrate business logic (e.g., calling FFmpeg + LLM).
   - **Repositories**: Handle DB/Storage persistence.

### Dependency Management
- **Shared Utilities**: Create a `core` package for shared logic (auth, logging, config) to keep the clone clean.
- **Environment Parity**: Use Pydantic `BaseSettings` for all configurations to avoid hardcoded strings found in the source.

---

## 3. Multi-Branch Architecture Patterns

To support audio, video, and document processing under one API, use the **Router Branching** pattern:

```python
# app/main.py
from fastapi import FastAPI
from app.routers import audio, video, document

app = FastAPI(title="Media Analysis API")

app.include_router(audio.router, prefix="/api/v1/audio", tags=["Audio"])
app.include_router(video.router, prefix="/api/v1/video", tags=["Video"])
app.include_router(document.router, prefix="/api/v1/document", tags=["Document"])
```

### Domain-Specific workers
If processing is heavy (e.g., video transcoding), consider using **BackgroundTasks** or a dedicated task queue (Celery/Redis) with workers specialized for each branch.

---

## 4. Endpoint Naming & Identifier Collision Avoidance

### Naming Strategy
Avoid generic names like `/analyze`. Use hierarchical, resource-based naming:
- `POST /api/v1/audio/transcribe`
- `POST /api/v1/video/extract-frames`
- `POST /api/v1/document/ocr`

### Collision Avoidance (ID Strategy)
When two services (Cotizador and Media Analysis) share a database or exchange data, ID collisions are a risk.
- **Primary Mechanism**: **ULID** (Universally Unique Lexicographically Sortable Identifier).
- **Secondary Mechanism**: **Service Prefixes**.

**Recommended ID Format:** `ma_{ULID}` (e.g., `ma_01ARZ3NDEKTSV4RRFFQ69G5FAV`)

| Mechanism | Benefit |
|-----------|---------|
| **ULID** | 128-bit uniqueness, sortable by time (unlike UUID v4), compact representation. |
| **Prefix (`ma_`)** | Instant visual identification of origin in logs and cross-service databases. |

---

## 5. Container Networking & Isolation

### Dedicated Network: `media-services-network`
Isolate the media stack from the public-facing API network.

```yaml
# docker-compose.yml
services:
  media-analysis-api:
    image: media-analysis-api:latest
    networks:
      - media-services-network
    expose:
      - "8000" # Internal only

  # Workers share the same network for service discovery
  video-worker:
    networks:
      - media-services-network

networks:
  media-services-network:
    driver: bridge
    internal: true # Optional: restrict outbound traffic
```

### Service Discovery
Communication between services should use container names:
`http://media-analysis-api:8000/api/v1/...`

---

## 6. Caddyfile Routing for Multiple APIs

Use Caddy as a reverse proxy to route traffic based on subdomains or paths.

### Option A: Subdomain Routing (Recommended)
```caddyfile
# Caddyfile
api.example.com {
    reverse_proxy cotizador-api:8000
}

media.api.example.com {
    reverse_proxy media-analysis-api:8000
}
```

### Option B: Path Routing (Unified Domain)
```caddyfile
api.example.com {
    # Media Analysis Branch
    handle_path /media/* {
        reverse_proxy media-analysis-api:8000
    }

    # Default to Cotizador
    reverse_proxy cotizador-api:8000
}
```

---

## 7. Actionable Recommendations

1.  **Stop "File-based" Imports**: The source uses `os.path` and `.env.local` files for config. Transition to Pydantic `BaseSettings`.
2.  **Implement ULIDs Immediately**: Replace auto-incrementing integers or random UUIDs with `ma_` prefixed ULIDs for all new media records.
3.  **Use `UploadFile` Streaming**: For video/audio, ensure the clone uses `UploadFile` (spooled to disk) or direct stream processing to avoid OOM (Out of Memory) errors on large files.
4.  **Isolate Database Tables**: Even if sharing a PostgreSQL instance, use a `ma_` prefix for all tables (e.g., `ma_jobs`, `ma_results`) to prevent namespace collisions with `cotizador-api`.
5.  **Health Check Parity**: Maintain the `/health` endpoint pattern but include domain-specific health (e.g., check if `ffmpeg` and `tesseract` are available).

---

## 8. Potential Pitfalls to Avoid

- **Pitfall**: Shared state via global variables (found in source `cotizador.py`).
  - **Fix**: Use Dependency Injection for DB sessions and external clients.
- **Pitfall**: Hardcoded Port 8000.
  - **Fix**: Map internal 8000 to external 8001/8002 in Compose, but keep code port-agnostic via env vars.
- **Pitfall**: Inefficient Frame Extraction.
  - **Fix**: Implement the "Keyword-Triggered" extraction found in the source as an optional module, not a core requirement, to keep the service lean.