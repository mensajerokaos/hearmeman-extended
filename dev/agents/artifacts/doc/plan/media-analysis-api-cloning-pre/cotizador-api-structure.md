# AF Cotizador-API Source Code Structure Analysis

## Overview
AF Cotizador-API is a FastAPI-based vehicle damage assessment and quote calculation service for AF High Definition Car Care. The application analyzes images, videos, and audio to generate repair quotes with Human-In-The-Loop (HITL) review workflows and CRM integration.

**Location**: `/home/oz/projects/2025/af/11/perito-hitl-media-gallery/dev/services/cotizador-api/`
**Main File**: `cotizador_api.py` (8,162 lines)
**Version**: 2.19.0

---

## Directory Structure

```
cotizador-api/
├── Dockerfile                              # Docker image definition
├── docker-compose.yml                      # Local development compose
├── docker-compose.service.yml              # Production service config
├── .env.example                            # Environment template
├── requirements.txt                        # Python dependencies
├── cotizador_api.py                        # Main FastAPI application (8,162 lines)
├── cotizador.py                            # Core quote calculation logic
├── kommo_client.py                         # Kommo CRM integration
├── metrics.py                              # HITL accuracy metrics
├── archive_endpoint.py                     # Archive quote endpoint (stand-alone)
├── kie_download.py                         # KIE model download utility
├── benchmark_models.py                     # Model benchmarking
├── test_*.py                               # Test files
├── optimize_elionn_prompt.py               # Prompt optimization
├── run_elionn_test.py                      # Elionn test runner
├── templates/
│   ├── quote.html                          # PDF quote template
│   └── assets/
│       └── AF-logo-negro.webp              # Company logo
└── __pycache__/                            # Python cache
```

---

## 1. FastAPI Application Structure

### Application Setup (Line 787-799)
```python
app = FastAPI(
    title="Cotizador API",
    description="AF High Definition Car Care - Automated Quote Calculator with Video/Audio Support",
    version=VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Middleware & Extensions
- **CORS**: Enabled for all origins (for development)
- **Logging**: Configured for A/B test tracking
- **Version**: 2.19.0 (Phase 2: Unified stored_files integration)

---

## 2. API Endpoints

### Core Analysis Endpoints

| Endpoint | Method | Purpose | Response Model |
|----------|--------|---------|-----------------|
| `/api/analyze` | POST | Full analysis with video/audio | `AnalyzeResponse` |
| `/api/extract-frames` | POST | Extract frames to HDD CDN | `ExtractFramesResponse` |
| `/api/transcribe` | POST | Transcribe audio | `TranscribeResponse` |
| `/api/process-document` | POST | PDF/Document analysis | `ProcessDocumentResponse` |
| `/api/compress-pdf` | POST | PDF compression | `CompressPDFResponse` |

### Quote Management Endpoints

| Endpoint | Method | Purpose | Response Model |
|----------|--------|---------|-----------------|
| `/api/quote/{session_id}` | GET | Get quote by session | JSON |
| `/api/quote/{quote_id}/approve` | POST | Approve quote | JSON |
| `/api/quote/{quote_id}/reject` | POST | Reject quote | JSON |
| `/api/quote/{quote_id}/schedule` | POST | Schedule repair | JSON |
| `/quote/active/{contact_id}` | GET | Get active quotes for contact | JSON |
| `/quote/merge` | POST | Merge duplicate quotes | JSON |

### HITL (Human-In-The-Loop) Endpoints

| Endpoint | Method | Purpose | Response Model |
|----------|--------|---------|-----------------|
| `/api/hitl/queue` | GET | Review queue listing | `QueueResponse` |
| `/api/hitl/stream` | GET | Streaming updates | Server-Sent Events |
| `/api/hitl-review` | POST | Submit review | `HITLReviewResponse` |
| `/api/quotes/{session_id}/claim` | POST | Claim for review | `ClaimResponse` |
| `/api/quotes/{session_id}/release` | POST | Release claimed quote | JSON |
| `/api/hitl/archive` | GET | Archived quotes | `ArchiveResponse` |

### CRM Integration Endpoints

| Endpoint | Method | Purpose | Response Model |
|----------|--------|---------|-----------------|
| `/api/customer-context` | POST | Fetch customer context from Kommo | `CustomerContextResponse` |
| `/api/generate-form-link` | POST | Generate customer form link | `GenerateFormLinkResponse` |
| `/api/create-quote` | POST | Create quote from form | `CreateQuoteResponse` |
| `/api/update-lead-stage` | POST | Update lead stage in Kommo | `UpdateLeadStageResponse` |
| `/api/v1/send-followup` | POST | Send follow-up message | `SendFollowUpResponse` |

### Feedback & Metrics Endpoints

| Endpoint | Method | Purpose | Response Model |
|----------|--------|---------|-----------------|
| `/api/quote-feedback` | POST | A/B test feedback tracking | `QuoteFeedbackResponse` |
| `/api/scores/calculate` | POST | Calculate accuracy scores | `ScoreCalculationResponse` |
| `/api/scores/lead/{lead_id}` | GET | Get scores for lead | JSON |

### System Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/` | GET | API information |
| `/api/store-media` | POST | Store media files |
| `/api/messages/ingest/v2` | POST | Message ingestion v2 |
| `/api/lead/{lead_id}/close` | POST | Close lead |
| `/api/generate-quote-pdf` | POST | Generate PDF quote |
| `/api/batch-timer/status` | GET | Batch timer status |
| `/api/jobs/status` | GET | Jobs status |
| `/api/scheduler/status` | GET | Scheduler status |

### Total Endpoints: 30+ API routes

---

## 3. Request/Response Models (Pydantic)

### Core Request Models

```python
class AnalyzeRequest(BaseModel):
    images: List[str] = []
    video_urls: Optional[List[str]] = None
    audio_url: Optional[str] = None
    customer_context: Optional[str] = None
    session_id: Optional[str] = None
    contact_sheet_max_width: int = 1920
    enable_diarization: bool = False
    reference_images_enabled: bool = True
    reference_image_ids: Optional[List[str]] = None
    contact_id: Optional[int] = None
    lead_id: Optional[int] = None
    document_urls: Optional[List[str]] = None

class ExtractFramesRequest(BaseModel):
    video_urls: List[str]
    audio_url: Optional[str] = None
    session_id: Optional[str] = None
    max_frames: int = 8
    contact_sheet_max_width: int = 1920
    extraction_method: str = "auto"  # "auto", "keyword", "uniform"

class HITLReviewRequest(BaseModel):
    session_id: str
    reviewer_action: str  # "approve" | "edit" | "reject"
    reviewer_id: str
    reviewer_name: str
    corrected_damages: Optional[List[Dict]] = None
    corrected_total: Optional[float] = None
    edit_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    lead_id: Optional[int] = None
```

### Core Response Models

```python
class AnalyzeResponse(BaseModel):
    success: bool
    analysis: Dict[str, Any]
    quote: Dict[str, Any]
    formatted_message: str
    cost_usd: float
    image_count: int
    model: str
    timestamp: str
    session_id: Optional[str] = None
    frame_urls: Optional[List[str]] = None
    contact_sheet_url: Optional[str] = None
    transcription: Optional[str] = None
    diarized_transcription: Optional[str] = None
    optimized_video_url: Optional[str] = None
    document_summary: Optional[str] = None

class HITLReviewResponse(BaseModel):
    success: bool
    message: str
    metrics: Optional[Dict[str, Any]] = None
    session_id: str
    pdf_url: Optional[str] = None
    pdf_generated: bool = False
    notification_sent: bool = False
    retake_requested: Optional[bool] = None
    retry_count: Optional[int] = None

class QueueResponse(BaseModel):
    success: bool
    quotes: List[QuoteQueueItem]
    total_count: int
    unclaimed_count: int

class ProcessDocumentResponse(BaseModel):
    success: bool
    is_meaningful: bool
    document_type: str  # competitor_quote, insurance_claim, etc.
    document_subtype: Optional[str] = None
    document_quality: Optional[str] = None
    confidence: float
    summary_for_staff: str
    summary_for_elionn: str
    extracted_data: Dict[str, Any]
    cdn_url: Optional[str] = None
    model: str = "gemini-3-flash"
    cost_usd: float = 0.0
```

**Total Pydantic Models**: 25+ request/response models

---

## 4. Database Integration

### Database Configuration (PostgreSQL)
```python
DB_HOST = os.getenv("DB_HOST", "af-postgres-1")  # Docker container name
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "af-memory")
DB_USER = os.getenv("DB_USER", "n8n")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
```

### Connection Pattern
```python
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# Usage:
with conn.cursor(cursor_factory=RealDictCursor) as cur:
    cur.execute(query, params)
    result = cur.fetchall()
```

### Database Operations Found
- Quote CRUD operations
- Lead/contact management
- Review queue management
- Media file tracking
- Form token management
- HITL metrics storage
- A/B test logging

### Key Database Tables (Inferred)
- `quotes` - Main quote records
- `leads` - Kommo lead references
- `contacts` - Customer contacts
- `media_files` - Attached media
- `form_tokens` - Secure form tokens
- `hitl_reviews` - Review history

---

## 5. External Service Integrations

### A. Transcription Providers (Fallback Chain)
```python
TRANSCRIPTION_PROVIDERS = ["groq", "openai", "gemini"]  # Priority order

# Groq Whisper (Recommended)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_WHISPER_MODEL = "whisper-large-v3-turbo"

# OpenAI Whisper (Fallback)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_WHISPER_URL = "https://api.openai.com/v1/audio/transcriptions"

# Gemini via OpenRouter (Final Fallback)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
```

### B. Kommo CRM Integration
```python
# kommo_client.py (38,499 bytes)
KOMMO_DOMAIN = os.getenv("KOMMO_DOMAIN", "")
KOMMO_ACCESS_TOKEN = os.getenv("KOMMO_ACCESS_TOKEN", "")
KOMMO_PIPELINE_ID = os.getenv("KOMMO_PIPELINE_ID", "12378399")
KOMMO_CF_VEHICULOS = os.getenv("KOMMO_CF_VEHICULOS", "3729952")

class KommoClient:
    """Client for Kommo CRM API v4."""
    
    def get_customer_context(self, lead_id: int = None, contact_id: int = None) -> Dict
    def format_context_for_llm(self, context: Dict) -> str
    def get_contact_details(self, contact_id: int) -> Dict
    def get_lead_details(self, lead_id: int) -> Dict
    def get_lead_history(self, lead_id: int) -> List[Dict]
```

### C. Vision/LLM Models
```python
# Primary and fallback vision models
VISION_MODEL_PRIMARY = "google/gemini-3-flash-preview"
VISION_MODEL_FALLBACK = "google/gemini-2.5-flash"

# Native video analysis
USE_NATIVE_VIDEO_API = os.getenv("USE_NATIVE_VIDEO_API", "false").lower() == "true"
NATIVE_VIDEO_MODEL = os.getenv("NATIVE_VIDEO_MODEL", "google/gemini-2.5-flash")
NATIVE_VIDEO_MODEL_FALLBACK = os.getenv("NATIVE_VIDEO_MODEL_FALLBACK", "qwen/qwen3-vl-32b-instruct")

# Document analysis
DOCUMENT_ANALYSIS_MODEL = os.getenv("DOCUMENT_ANALYSIS_MODEL", "google/gemini-2.5-flash")
```

### D. Storage & CDN
```python
# HDD CDN Configuration
HDD_BASE_URL = os.getenv("HDD_BASE_URL", "https://hdd.automatic.picturelle.com/af")
HDD_ACCESS_TOKEN = os.getenv("HDD_ACCESS_TOKEN", "")
UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", "/app/uploads"))

# PDF Generation
GOTENBERG_URL = "http://af-gotenberg-1:3000"
QUOTE_TEMPLATE_DIR = Path("/app/templates")
PDF_OUTPUT_DIR = Path("/app/uploads/quotes/pdf")
```

---

## 6. Core Business Logic

### Quote Calculation (cotizador.py)
```python
def analyze_images(image_paths: List[str], context: str = None) -> Dict[str, Any]
def calculate_quote(analysis: Dict[str, Any]) -> Dict[str, Any]
def format_quote_message(quote: Dict[str, Any]) -> str
def merge_damages(damages1: List, damages2: List) -> List
def build_damage_prompt(customer_context: str = None, include_reference_note: bool = False) -> str
```

### Video/Audio Processing
```python
def extract_frames_ffmpeg(video_path: str, output_dir: str, max_frames: int = 8) -> List[str]
def extract_audio_from_video(video_path: str, output_path: str) -> bool
def chunk_audio_file(audio_path: str, output_dir: str) -> List[str]
def transcribe_audio(audio_url: str, language: str = "es") -> str
def extract_frames_keyword_triggered(...) -> Dict
def analyze_video_native(...) -> Dict[str, Any]
def analyze_video_qwen(...) -> Dict[str, Any]
```

### Image Processing
```python
def optimize_image_ffmpeg(image_path: str, output_path: str, max_width: int = 1920) -> bool
def optimize_images_batch(image_paths: List[str], max_width: int = 1920) -> List[str]
def optimize_video_webm(video_path: str, output_path: str, max_width: int = 720) -> bool
def generate_contact_sheet(image_paths: List[str], output_path: str, layout: Dict) -> bool
def detect_repetition(text: str, min_pattern_len: int = 10, max_repetitions: int = 3) -> str
```

### Document Processing
```python
def is_compression_candidate(pdf_path: str, min_size_kb: int = 500) -> dict
def compress_pdf(input_path: str, output_path: str, quality: str = "ebook") -> bool
def summarize_document_with_llm(document_url: str) -> Optional[str]
```

### Metrics & HITL (metrics.py)
```python
def calculate_hitl_metrics(ai_prediction: dict, human_review: dict) -> dict
    """
    Calculate accuracy metrics comparing AI prediction to human review.
    Returns:
        - ai_total, human_total, price_delta, price_delta_pct
        - within_10_pct, within_20_pct (bool)
        - ai_damage_count, human_damage_count, damages_matched
        - damages_added, damages_removed
        - edit_severity (str: minor/moderate/significant)
        - accuracy_score (float: 0-100)
    """
```

---

## 7. Media Processing Pipeline

### A/B Test Framework
```python
AB_TEST_LOG_PATH = Path(os.getenv("AB_TEST_LOG_PATH", "/app/uploads/ab_test_log.jsonl"))

def log_ab_test_event(
    session_id: str,
    event_type: str,  # "frame_extraction" | "quote_generated" | "quote_accepted" | "quote_rejected"
    extraction_method: str,  # "keyword_triggered" | "hybrid" | "uniform_fallback" | "uniform"
    data: dict
):
    """Log A/B test events to JSONL file for later analysis."""
```

### Frame Extraction Methods
1. **Uniform**: Extract frames at regular intervals
2. **Keyword-Triggered**: Use Spanish keyword detection in audio to trigger frame extraction
3. **Hybrid**: Use keyword-triggered if audio available, else uniform
4. **Native Video**: Use native video API (Gemini 2.5 Flash)

### Damage Keywords (Spanish)
```python
DAMAGE_KEYWORDS = [
    # Pointing/demonstrating: "mira", "aquí", "acá", "ves", "este", "aquí", "fíjate"
    # Damage descriptors: "golpe", "daño", "raya", "rayón", "abolladura", "hundido", "raspón"
    # Car parts: "puerta", "cofre", "cajuela", "salpicadera", "facia", "defensa", "toldo"
    # Action words: "pegó", "rozó", "tocó"
]
```

### Audio Processing Config
```python
AUDIO_CONFIG = {
    "codec": "libopus",
    "format": "ogg",
    "bitrate_kbps": 16,
    "sample_rate": 16000,
    "mono": True,
    "highpass_hz": 180,
    "compressor": {
        "threshold": "-20.3dB",
        "ratio": 20,
        "attack": 20,
        "release": 500,
        "makeup": 12,
    },
    "max_file_size_mb": 24,
    "chunk_duration_sec": 300,
}
```

---

## 8. Environment Variables

### Required Variables
```bash
# Database
DB_PASSWORD=your_db_password

# AI/LLM APIs
OPENROUTER_API_KEY=your_openrouter_key
GROQ_API_KEY=your_groq_key  # Recommended for transcription
OPENAI_API_KEY=your_openai_key  # Optional

# Kommo CRM
KOMMO_DOMAIN=afhdcarcare.kommo.com
KOMMO_ACCESS_TOKEN=your_kommo_token
KOMMO_PIPELINE_ID=12378399

# Storage
HDD_BASE_URL=https://hdd.automatic.picturelle.com/af
HDD_ACCESS_TOKEN=your_hdd_token
UPLOADS_DIR=/app/uploads

# Gotenberg (PDF)
GOTENBERG_URL=http://af-gotenberg-1:3000
```

### Optional Variables
```bash
# Model Configuration
USE_NATIVE_VIDEO_API=false
NATIVE_VIDEO_MODEL=google/gemini-2.5-flash
DOCUMENT_ANALYSIS_MODEL=google/gemini-2.5-flash

# Transcription
GROQ_WHISPER_MODEL=whisper-large-v3-turbo
OPENAI_WHISPER_MODEL=whisper-1
GEMINI_WHISPER_MODEL=google/gemini-3-flash
WHISPER_FALLBACK_ENABLED=true

# Video Processing
VIDEO_MODEL_FALLBACK_ENABLED=true
NATIVE_VIDEO_MODEL_FALLBACK=qwen/qwen3-vl-32b-instruct

# HITL Configuration
MAX_RETAKE_RETRIES=3
CLAIM_TTL_SECONDS=600  # 10 minutes
RETAKEABLE_REASONS=["fotos_malas", "info_incompleta", "retomar"]
FINAL_REJECTION_REASONS=["spam", "fuera_alcance"]

# Logging
AB_TEST_LOG_PATH=/app/uploads/ab_test_log.jsonl

# Testing
ENV_PATH=/home/oz/projects/2025/af/11/perito/credentials/.env.local
GLOSSARY_PATH=/opt/clients/af/agents/uploads/referencias-cotizador/glossary_research.json
```

---

## 9. Docker Configuration

### Dockerfile (Python 3.11-slim)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-spa \
    ghostscript \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY cotizador.py cotizador_api.py metrics.py kommo_client.py ./

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "cotizador_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (Local Development)
```yaml
services:
  cotizador-api:
    build: .
    container_name: cotizador-api
    restart: unless-stopped
    env_file:
      - /opt/clients/af/.env
    ports:
      - "8001:8000"
    volumes:
      - /opt/clients/af/local_files/uploads:/app/uploads
      - /opt/clients/af/local_files/templates:/app/templates
    networks:
      - af_default

networks:
  af_default:
    external: true
```

### Python Dependencies (requirements.txt)
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
requests==2.31.0
pydantic==2.6.0
python-multipart==0.0.9
pymupdf>=1.24.0
python-docx>=1.1.0
httpx>=0.25.0
psycopg2-binary==2.9.9
jinja2>=3.0.0
apscheduler>=3.10.0
asyncpg>=0.29.0
```

---

## 10. Multi-Tenant & Modular Patterns

### Service Isolation Patterns

1. **Database-Level Isolation**
   - Single shared database (`af-memory`) with table prefixes implied
   - Uses PostgreSQL with table-level isolation
   - `form_tokens` table for tenant/contact isolation

2. **CRM Integration (Kommo)**
   - Pipeline-based isolation (Pipeline ID: 12378399)
   - Lead/contact IDs for customer isolation
   - Stage mapping for workflow states

3. **File Storage Isolation**
   - Session-based organization (`session_hash` derived from UUID)
   - Category-based subdirectories (frames, quotes, uploads)
   - CDN URL generation with hash-based paths

4. **API Versioning**
   - Route prefix versioning: `/api/v1/`, `/api/`
   - Version field in responses for compatibility
   - Backward compatibility maintained in responses

### Workflow Patterns

1. **Quote Processing Flow**
   ```
   Analyze Request → Frame Extraction → AI Analysis → Quote Calculation
   → HITL Review Queue → Review → PDF Generation → Customer Notification
   ```

2. **Document Processing Flow**
   ```
   Document Upload → OCR/Text Extraction → Classification → Summary
   → Data Extraction → Form Update (if applicable)
   ```

3. **HITL Workflow**
   ```
   Queue Entry → Claim (TTL 10 min) → Review (approve/edit/reject)
   → Metrics Calculation → A/B Test Logging → Archive
   ```

4. **Retake Flow**
   ```
   Rejection with reason → Customer notification → New form link
   → Re-upload → Re-processing (up to MAX_RETAKE_RETRIES times)
   ```

---

## 11. Key Files & Their Purposes

| File | Lines | Purpose |
|------|-------|---------|
| `cotizador_api.py` | 8,162 | Main FastAPI application with all endpoints |
| `cotizador.py` | 24,903 | Core quote calculation and analysis logic |
| `kommo_client.py` | 38,499 | Kommo CRM API integration |
| `metrics.py` | 22,737 | HITL accuracy metrics and scoring |
| `archive_endpoint.py` | 4,453 | Archive endpoint for completed quotes |
| `benchmark_models.py` | 8,077 | Model benchmarking utilities |
| `optimize_elionn_prompt.py` | 21,181 | Prompt optimization for Elionn |
| `run_elionn_test.py` | 26,792 | Elionn test runner |
| `test_cotizador_batch.py` | 14,275 | Batch testing utilities |
| `test_elionn_prompt.py` | 17,500 | Prompt testing |
| `test_native_video.py` | 11,343 | Native video API testing |
| `kie_download.py` | 1,750 | KIE model download utility |

---

## 12. Error Handling & Retry Patterns

### Transcription Fallback Chain
```python
def transcribe_audio(audio_url: str, language: str = "es") -> str:
    """
    Smart transcription: Try providers in order:
    1. Groq Whisper (fastest, recommended)
    2. OpenAI Whisper (reliable fallback)
    3. Gemini via OpenRouter (final fallback)
    """
    for provider in TRANSCRIPTION_PROVIDERS:
        try:
            # Attempt transcription
            return provider_result
        except Exception as e:
            print(f"{provider} failed: {e}")
            continue
    raise ValueError("No transcription provider available")
```

### Video Analysis Fallback
```python
if USE_NATIVE_VIDEO_API and OPENROUTER_API_KEY:
    try:
        native_result = analyze_video_native(...)
        if "error" not in native_result:
            extraction_method = "native_video"
            # Use native result
        else:
            print(f"Native video failed, falling back to legacy")
            native_result = None
    except Exception as e:
        print(f"Native video exception, falling back to legacy: {e}")
        native_result = None

# Legacy path if native failed
if not native_result:
    # Use extract_frames_ffmpeg or keyword-triggered extraction
```

---

## 13. Configuration Management

### Environment Variable Loading Pattern
```python
# Pattern 1: Direct environment variable
DB_HOST = os.getenv("DB_HOST", "af-postgres-1")

# Pattern 2: File-based environment (cotizador.py)
ENV_PATH = os.getenv("ENV_PATH", "/home/oz/projects/2025/af/11/perito/credentials/.env.local")
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# Pattern 3: Boolean conversion
USE_NATIVE_VIDEO_API = os.getenv("USE_NATIVE_VIDEO_API", "false").lower() == "true"
```

### Constants & Configuration Classes
```python
# Audio configuration (AUDIO_CONFIG dict)
# Stage mapping (KOMMO_STAGE_MAPPING dict)
# Damage keywords list (DAMAGE_KEYWORDS)
# Transcription providers list (TRANSCRIPTION_PROVIDERS)
```

---

## 14. Logging & Monitoring

### A/B Test Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
ab_test_logger = logging.getLogger("ab_test")

# Log format:
{
    "timestamp": "2026-01-18T10:30:00",
    "session_id": "abc123",
    "event_type": "quote_generated",
    "extraction_method": "keyword_triggered",
    "quote_total": 15000,
    "confidence": 0.85
}
```

### Health Check Response
```python
{
    "status": "ok",
    "version": "2.19.0",
    "model": "google/gemini-3-flash-preview",
    "features": ["images", "video_frames", "audio_transcription", 
                 "pdf_compression", "document_processing", "hdd_upload"],
    "timestamp": "2026-01-18T10:30:00"
}
```

---

## 15. Security & Validation

### Input Validation
- All endpoints use Pydantic models for request validation
- File upload validation (size limits, type checking)
- URL validation for external resources
- Session ID validation (UUID format)

### Sensitive Data Handling
- Database credentials via environment variables
- API keys via environment variables or file-based config
- No hardcoded secrets in source code
- External .env files for local development

### Rate Limiting
- Kommo client enforces 150ms delay between requests (~6.7 req/sec)
- Allows 7 requests per second (Kommo limit: 7 req/sec)

---

## 16. Performance Optimizations

### Audio Processing
- Compression for speech recognition (16kHz, mono, Opus codec)
- Chunking for files > 24MB (Groq/OpenAI limit)
- Noise reduction filters (highpass 180Hz)

### Image Processing
- Contact sheet generation for visual summary
- Aspect ratio detection and grid layout optimization
- FFmpeg-based optimization for large images

### Database Operations
- Connection pooling via context managers
- RealDictCursor for named column access
- Pagination for archive/queue endpoints

---

## 17. Extensibility Points

### Adding New Transcription Providers
1. Add provider to `TRANSCRIPTION_PROVIDERS` list
2. Implement provider function (e.g., `transcribe_audio_x`)
3. Add provider check in `get_transcription_provider()`

### Adding New Document Types
1. Add type to `ProcessDocumentResponse.document_type` enum
2. Update classification logic in document processing
3. Add extraction patterns for new fields

### Adding New Quote Statuses
1. Add status to `KOMMO_STAGE_MAPPING` dict
2. Update HITL review logic if needed
3. Add to workflow validation

---

## 18. Testing & Quality Assurance

### Test Files Available
- `test_cotizador_batch.py` - Batch testing
- `test_elionn_prompt.py` - Prompt testing
- `test_native_video.py` - Video API testing
- `benchmark_models.py` - Model benchmarking
- `run_elionn_test.py` - Elionn test runner

### Test Case Support
```python
VPS_TEST_CASES_BASE = "/opt/clients/af/agents/test-cases-elionn"

def run_test_case(case_num: int, verbose: bool = True) -> Dict[str, Any]:
    """Run predefined test case from test-cases-elionn directory."""
```

---

## 19. Deployment Architecture

### Service Dependencies
```
cotizador-api
├── PostgreSQL (af-postgres-1)
├── Gotenberg (af-gotenberg-1:3000) - PDF generation
├── HDD CDN (hdd.automatic.picturelle.com) - File storage
├── External APIs:
│   ├── OpenRouter (LLM/vision)
│   ├── Groq (Whisper transcription)
│   ├── OpenAI (Whisper fallback)
│   └── Kommo (CRM)
└── Docker Network: af_default
```

### Container Configuration
- **Port**: 8000 (internal), 8001 (external mapping)
- **Restart Policy**: unless-stopped
- **Health Check**: Python-based HTTP check
- **Volumes**: uploads, templates
- **Network**: af_default (external)

---

## Summary

The AF Cotizador-API is a well-structured, production-ready FastAPI application with:

- **30+ API endpoints** organized by functional area
- **Multi-provider integrations** for transcription and AI with fallback chains
- **PostgreSQL database** with table-level isolation
- **Kommo CRM integration** for workflow automation
- **Comprehensive media processing** for images, video, and audio
- **HITL workflow support** with review queues and metrics
- **A/B testing framework** for extraction method comparison
- **Docker-ready deployment** with proper health checks
- **Clear separation of concerns** (API layer, business logic, integrations)
- **Production-grade error handling** and validation

The codebase follows Python best practices with Pydantic models, environment-based configuration, and modular design that enables easy extension and maintenance.

---

**Author**: Claude Code Analysis
**Date**: 2026-01-18
**Analysis Scope**: Full codebase exploration and documentation
