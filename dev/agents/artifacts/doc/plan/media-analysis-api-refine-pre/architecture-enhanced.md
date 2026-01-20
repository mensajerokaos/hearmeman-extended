---
author: $USER
model: claude-sonnet-4-5-20250929
date: 2026-01-18 22:15
task: Comprehensive Architecture Enhancement Document - Media Analysis API Cloning
---

# Media Analysis API Cloning - Enhanced Architecture Documentation

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-18 | $USER | Initial architecture documentation |
| 1.1 | 2026-01-18 | $USER | Enhanced with FILE:LINE targets and code patterns |

---

## Table of Contents

1. [Detailed BEFORE Architecture](#1-detailed-before-architecture-current-state)
2. [Detailed AFTER Architecture](#2-detailed-after-architecture-target-state)
3. [Network Isolation Diagram](#3-network-isolation-diagram)
4. [Data Flow Through Aggregator](#4-data-flow-through-aggregator)
5. [MiniMax Integration Points](#5-minimax-integration-points)
6. [FILE:LINE Reference Targets](#6-fileline-reference-targets)
7. [BEFORE/AFTER Code Patterns](#7-beforeafter-code-patterns)
8. [Enhanced Verification Commands](#8-enhanced-verification-commands)

---

## 1. Detailed BEFORE Architecture (Current State)

```
═══════════════════════════════════════════════════════════════════════════════════════════
                         AF DEVELOPMENT ENVIRONMENT (devmaster)
═══════════════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           af-network (172.20.0.0/16)                                    │
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                  │  │
│  │              ┌─────────────────────────────────────────┐                          │  │
│  │              │      cotizador-api:8000 (container)      │                          │  │
│  │              │  ┌───────────────────────────────────┐  │                          │  │
│  │              │  │      FastAPI Application          │  │                          │  │
│  │              │  │  ┌─────────────────────────────┐  │  │                          │  │
│  │              │  │  │    Main App (line 30-60)    │  │  │                          │  │
│  │              │  │  │    - CORS middleware        │  │  │                          │  │
│  │              │  │  │    - Startup handlers       │  │  │                          │  │
│  │              │  │  │    - Shutdown handlers      │  │  │                          │  │
│  │              │  │  └─────────────────────────────┘  │  │                          │  │
│  │              │  │                                    │  │                          │  │
│  │              │  │  ┌─────────────────────────────┐  │  │                          │  │
│  │              │  │  │   ENDPOINTS (line 4040+)    │  │  │                          │  │
│  │              │  │  │                             │  │  │                          │  │
│  │              │  │  │  GET  /health               │  │  │                          │  │
│  │              │  │  │  GET  /                     │  │  │                          │  │
│  │              │  │  │  POST /api/extract-frames   │  │  │                          │  │
│  │              │  │  │  POST /api/video_express    │  │  │                          │  │
│  │              │  │  │  POST /api/transcribe       │  │  │                          │  │
│  │              │  │  │  POST /api/customer-context │  │  │                          │  │
│  │              │  │  │  POST /api/generate-form-link│ │  │                          │  │
│  │              │  │  │  POST /api/create-quote     │  │  │                          │  │
│  │              │  │  │  POST /api/analyze          │  │  │                          │  │
│  │              │  │  │  POST /api/hitl-review      │  │  │                          │  │
│  │              │  │  │  POST /api/store-media      │  │  │                          │  │
│  │              │  │  │  POST /api/process-document │  │  │                          │  │
│  │              │  │  │  ... (30+ endpoints total)  │  │  │                          │  │
│  │              │  │  └─────────────────────────────┘  │  │                          │  │
│  │              │  │                                    │  │                          │  │
│  │              │  │  ┌─────────────────────────────┐  │  │                          │  │
│  │              │  │  │   DATA MODELS (line 417+)   │  │  │                          │  │
│  │              │  │  │                             │  │  │                          │  │
│  │              │  │  │  AnalyzeRequest             │  │  │                          │  │
│  │              │  │  │  TranscribeRequest          │  │  │                          │  │
│  │              │  │  │  ProcessDocumentRequest     │  │  │                          │  │
│  │              │  │  │  HITLReviewRequest          │  │  │                          │  │
│  │              │  │  │  ... (20+ models)           │  │  │                          │  │
│  │              │  │  └─────────────────────────────┘  │  │                          │  │
│  │              │  │                                    │  │                          │  │
│  │              │  │  ┌─────────────────────────────┐  │  │                          │  │
│  │              │  │  │   CORE FUNCTIONS (line 275+)│  │  │                          │  │
│  │              │  │  │                             │  │  │                          │  │
│  │              │  │  │  get_transcription_provider │  │  │                          │  │
│  │              │  │  │  extract_audio_from_video   │  │  │                          │  │
│  │              │  │  │  extract_frames_ffmpeg      │  │  │                          │  │
│  │              │  │  │  optimize_images_batch      │  │  │                          │  │
│  │              │  │  │  parse_native_video_response│  │  │                          │  │
│  │              │  │  │  ... (40+ functions)        │  │  │                          │  │
│  │              │  │  └─────────────────────────────┘  │  │                          │  │
│  │              │  └───────────────────────────────────┘  │                          │  │
│  │              │                                         │                          │  │
│  │              │  ┌───────────────────────────────────┐  │                          │  │
│  │              │  │   DEPENDENT MODULES              │  │                          │  │
│  │              │  │                                   │  │                          │  │
│  │              │  │  cotizador.py (line 57 import)    │  │                          │  │
│  │              │  │  - analyze_images()               │  │                          │  │
│  │              │  │  - calculate_quote()              │  │                          │  │
│  │              │  │  - format_quote_message()         │  │                          │  │
│  │              │  │  - MODEL                          │  │                          │  │
│  │              │  │                                   │  │                          │  │
│  │              │  │  metrics.py                       │  │                          │  │
│  │              │  │  - calculate_hitl_metrics()       │  │                          │  │
│  │              │  │                                   │  │                          │  │
│  │              │  │  kommo_client.py                  │  │                          │  │
│  │              │  │  scoring/                         │  │                          │  │
│  │              │  │  jobs/                            │  │                          │  │
│  │              │  │  services/                        │  │                          │  │
│  │              │  └───────────────────────────────────┘  │                          │  │
│  │              └─────────────────────────────────────────┘                          │  │
│  │                                                                                  │  │
│  │  Service Health:  http://cotizador-api:8000/health                               │  │
│  │  API Docs:        http://cotizador-api:8000/docs                                 │  │
│  │  OpenAPI Spec:    http://cotizador-api:8000/openapi.json                         │  │
│  │                                                                                  │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                                   │
│              ┌───────────────────────┼───────────────────────┐                           │
│              ▼                       ▼                       ▼                           │
│      ┌───────────────┐       ┌───────────────┐       ┌───────────────────────┐           │
│      │   Deepgram    │       │    FFmpeg     │       │         n8n           │           │
│      │   :5005       │       │   (local)     │       │      :5679            │           │
│      │               │       │               │       │                       │           │
│      │ /v1/listen    │       │ -i input.mp4  │       │  /api/workflows       │           │
│      │  (TTS/ASR)    │       │ -vf fps=3     │       │  /webhook/            │           │
│      │               │       │ -ss 00:00:05  │       │  (HITL workflows)     │           │
│      │ Input: audio  │       │ frame_%04d.jpg│       │                       │           │
│      │ Output: text  │       └───────────────┘       │ Input: JSON webhook   │           │
│      └───────────────┘                               │ Output: CRM update    │           │
│                                                      └───────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Caddy Reverse Proxy
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL NETWORK (internet)                                   │
│                                                                                          │
│  https://af-dev.automatic.picturelle.com/api/analyze/*                                   │
│  https://af-dev.automatic.picturelle.com/api/transcribe                                  │
│  https://af-dev.automatic.picturelle.com/api/customer-context                            │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### BEFORE File Structure

```
/opt/clients/af/dev/services/cotizador-api/
├── cotizador_api.py                    (Main FastAPI app - 9,462 lines)
│   ├── Imports (line 20-46)
│   ├── Data Models (line 417-900+)
│   ├── Helper Functions (line 275-1250)
│   ├── Main App Setup (line 4040-4100)
│   └── Endpoints (line 4040-8873)
│
├── cotizador.py                        (Core business logic - imported)
├── hitl_push.py                        (HITL integration module)
├── archive_endpoint.py                 (Archive functionality)
├── benchmark_models.py                 (Model benchmarking)
├── kommo_client.py                     (Kommo CRM integration)
├── scoring/                            (Scoring engine modules)
│   ├── __init__.py
│   ├── classifier.py
│   ├── constants.py
│   ├── engine.py
│   ├── quality.py
│   └── temperature.py
├── jobs/                               (Background job processing)
│   ├── __init__.py
│   ├── queue_processor.py
│   └── scheduler.py
├── services/                           (Service layer)
│   ├── __init__.py
│   └── kommo_update_service.py
├── docker-compose.yml                  (Network: af_default/af-network)
├── Dockerfile                          (Python 3.11, uvicorn)
├── .env                                (COTIZADOR_* environment vars)
├── .env.example                        (Template)
├── Caddyfile                           (af-dev subdomain routing)
├── requirements.txt                    (fastapi>=0.104, uvicorn, etc.)
└── config_loader.py                    (Configuration management)

FILE SIZE SUMMARY:
├── cotizador_api.py     9,462 lines (PRIMARY TRANSFORMATION TARGET)
├── cotizador.py         ~800 lines
├── Other modules        ~3,000 lines total
└── Total codebase       ~13,000+ lines
```

### BEFORE Key Identifiers

| Identifier Type | Original Value | File:Line Target | Count |
|-----------------|----------------|------------------|-------|
| Main Class | `CotizadorAPI` | cotizador_api.py:~50 | 1 |
| Business Class | `Cotizador` | cotizador.py:~line TBD | 1 |
| Logger Name | `"cotizador"` | cotizador_api.py:53 | 1 |
| Module Name | `cotizador` | cotizador_api.py:57 | 1 |
| Service Name | `cotizador-api` | docker-compose.yml:3 | 1 |
| Network Name | `af_default` / `af-network` | docker-compose.yml:19 | 1 |
| Env Prefix | `COTIZADOR_` | .env (all vars) | 12+ |
| Endpoint Prefix | `/api/analyze/` | cotizador_api.py:4848 | 1 |
| Endpoints (count) | 30+ | cotizador_api.py:4040-8873 | 33 |

---

## 2. Detailed AFTER Architecture (Target State)

```
═══════════════════════════════════════════════════════════════════════════════════════════
                         MEDIA SERVICES ENVIRONMENT (NEW)
═══════════════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                      media-services-network (172.28.0.0/16)                             │
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                  │  │
│  │              ┌─────────────────────────────────────────┐                          │  │
│  │              │    media-analysis-api:8000 (container)  │                          │  │
│  │              │  ┌───────────────────────────────────┐  │                          │  │
│  │              │  │      FastAPI Application          │  │                          │  │
│  │              │  │  ┌─────────────────────────────┐  │  │                          │  │
│  │              │  │  │    Main App (NEW line 30)   │  │  │                          │  │
│  │              │  │  │    - CORS middleware        │  │  │                          │  │
│  │              │  │  │    - Startup handlers       │  │  │                          │  │
│  │              │  │  │    - Shutdown handlers      │  │  │                          │  │
│  │              │  │  └─────────────────────────────┘  │  │                          │  │
│  │              │  │                                    │  │                          │  │
│  │              │  │  ┌─────────────────────────────┐  │  │                          │  │
│  │              │  │  │   ENDPOINTS (NEW line TBD)  │  │  │                          │  │
│  │              │  │  │                             │  │  │                          │  │
│  │              │  │  │  GET  /health               │  │  │                          │  │
│  │              │  │  │  GET  /                     │  │  │                          │  │
│  │              │  │  │  POST /api/media/extract-frames  │  │                          │  │
│  │              │  │  │  POST /api/media/video_express   │  │                          │  │
│  │              │  │  │  POST /api/media/transcribe  │  │  │                          │  │
│  │              │  │  │  POST /api/media/customer-context │  │                      │  │
│  │              │  │  │  POST /api/media/generate-form-link  │  │                  │  │
│  │              │  │  │  POST /api/media/create-quote │  │  │                          │  │
│  │              │  │  │  POST /api/media/analyze     │  │  │  ◄── NEW AGGREGATOR    │  │
│  │              │  │  │  POST /api/media/hitl-review │  │  │                          │  │
│  │              │  │  │  POST /api/media/store-media │  │  │                          │  │
│  │              │  │  │  POST /api/media/process-document  │  │                      │  │
│  │              │  │  │  ... (30+ endpoints migrated)│  │  │                          │  │
│  │              │  │  └─────────────────────────────┘  │  │                          │  │
│  │              │  │                                    │  │                          │  │
│  │              │  │  ┌─────────────────────────────┐  │  │                          │  │
│  │              │  │  │   AGGREGATOR MODULE        │  │  │  ◄── NEW COMPONENT       │  │
│  │              │  │  │   (NEW - line TBD)         │  │  │                          │  │
│  │              │  │  │                             │  │  │                          │  │
│  │              │  │  │  analyze_media()            │  │  │                          │  │
│  │              │  │  │  _detect_media_type()       │  │  │                          │  │
│  │              │  │  │  _process_video_analysis()  │  │  │                          │  │
│  │              │  │  │  _process_audio_analysis()  │  │  │                          │  │
│  │              │  │  │  _process_document_analysis()│ │  │                          │  │
│  │              │  │  │  _calculate_confidence()    │  │  │                          │  │
│  │              │  │  └─────────────────────────────┘  │  │                          │  │
│  │              │  │                                    │  │                          │  │
│  │              │  │  ┌─────────────────────────────┐  │  │                          │  │
│  │              │  │  │   MINIMAX INTEGRATION       │  │  │  ◄── NEW COMPONENT       │  │
│  │              │  │  │   (NEW - line TBD)          │  │  │                          │  │
│  │              │  │  │                             │  │  │                          │  │
│  │              │  │  │  MiniMaxClient              │  │  │                          │  │
│  │              │  │  │  MiniMaxConfig              │  │  │                          │  │
│  │              │  │  │  MiniMaxIntegration         │  │  │                          │  │
│  │              │  │  │  - vision_analysis()        │  │  │                          │  │
│  │              │  │  │  - transcribe_with_context()│  │  │                          │  │
│  │              │  │  │  - summarize_analysis()     │  │  │                          │  │
│  │              │  │  └─────────────────────────────┘  │  │                          │  │
│  │              │  │                                    │  │                          │  │
│  │              │  │  ┌─────────────────────────────┐  │  │                          │  │
│  │              │  │  │   DATA MODELS (MIGRATED)    │  │  │                          │  │
│  │              │  │  │                             │  │  │                          │  │
│  │              │  │  │  AnalyzeRequest             │  │  │                          │  │
│  │              │  │  │  TranscribeRequest          │  │  │                          │  │
│  │              │  │  │  ProcessDocumentRequest     │  │  │                          │  │
│  │              │  │  │  NEW: MediaAnalysisRequest  │  │  │                          │  │
│  │              │  │  │  NEW: AggregatorResponse    │  │  │                          │  │
│  │              │  │  └─────────────────────────────┘  │  │                          │  │
│  │              │  │                                    │  │                          │  │
│  │              │  │  ┌─────────────────────────────┐  │  │                          │  │
│  │              │  │  │   CORE FUNCTIONS (MIGRATED) │  │  │                          │  │
│  │              │  │  │                             │  │  │                          │  │
│  │              │  │  │  get_transcription_provider │  │  │                          │  │
│  │              │  │  │  extract_audio_from_video   │  │  │                          │  │
│  │              │  │  │  extract_frames_ffmpeg      │  │  │                          │  │
│  │              │  │  │  ... (40+ functions)        │  │  │                          │  │
│  │              │  │  └─────────────────────────────┘  │  │                          │  │
│  │              │  └───────────────────────────────────┘  │                          │  │
│  │              │                                         │                          │  │
│  │              │  ┌───────────────────────────────────┐  │                          │  │
│  │              │  │   DEPENDENT MODULES (RENAMED)     │  │                          │  │
│  │              │  │                                   │  │                          │  │
│  │              │  │  media_analysis.py (was cotizador.py)  │                      │  │
│  │              │  │  - analyze_images()               │  │                          │  │
│  │              │  │  - calculate_quote()              │  │                          │  │
│  │              │  │  - format_quote_message()         │  │                          │  │
│  │              │  │  - MODEL                          │  │                          │  │
│  │              │  │                                   │  │                          │  │
│  │              │  │  metrics.py (unchanged)           │  │                          │  │
│  │              │  │  minimax_client.py (NEW)          │  │                          │  │
│  │              │  │  minimax_integration.py (NEW)     │  │                          │  │
│  │              │  │                                   │  │                          │  │
│  │              │  │  (kommo_client.py - REMOVED)      │  │  ◄── NOT NEEDED         │  │
│  │              │  │  (scoring/ - REMOVED)             │  │  ◄── NOT NEEDED         │  │
│  │              │  │  (jobs/ - REMOVED)                │  │  ◄── NOT NEEDED         │  │
│  │              │  │  (services/ - REMOVED)            │  │  ◄── NOT NEEDED         │  │
│  │              │  └───────────────────────────────────┘  │                          │  │
│  │              └─────────────────────────────────────────┘                          │  │
│  │                                                                                  │  │
│  │  Service Health:  http://media-analysis-api:8000/health                          │  │
│  │  API Docs:        http://media-analysis-api:8000/docs                            │  │
│  │  OpenAPI Spec:    http://media-analysis-api:8000/openapi.json                    │  │
│  │                                                                                  │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                                   │
│              ┌───────────────────────┼───────────────────────┐                           │
│              ▼                       ▼                       ▼                           │
│      ┌───────────────┐       ┌───────────────┐       ┌───────────────────────┐           │
│      │   Deepgram    │       │    FFmpeg     │       │      MiniMax API      │           │
│      │   :5005       │       │   (local)     │       │    (EXTERNAL HTTPS)   │           │
│      │               │       │               │       │                       │           │
│      │ /v1/listen    │       │ -i input.mp4  │       │  https://api.minimax.│           │
│      │  (TTS/ASR)    │       │ -vf fps=3     │       │  chat/v1/chat/...     │           │
│      │               │       │ -ss 00:00:05  │       │                       │           │
│      │ Input: audio  │       │ frame_%04d.jpg│       │  /v1/chat/completions │           │
│      │ Output: text  │       └───────────────┘       │  (Vision + Text)       │           │
│      └───────────────┘                               │  Input: images + text  │           │
│                                                      │  Output: analysis      │           │
│                                                      └───────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Caddy Reverse Proxy (NEW CONTAINER)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL NETWORK (internet)                                   │
│                                                                                          │
│  https://media-analysis-api.automatic.picturelle.com/api/media/*                         │
│  https://media-analysis-api.automatic.picturelle.com/api/media/analyze                   │
│  https://media-analysis-api.automatic.picturelle.com/api/media/transcribe                │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### AFTER File Structure

```
/opt/services/media-analysis/
├── api/
│   ├── __init__.py
│   ├── media_analysis_api.py          (Renamed from cotizador_api.py - 9,462 lines)
│   │   ├── Imports (line 20-46) - UPDATED
│   │   ├── Data Models (line 417+) - UNCHANGED
│   │   ├── Helper Functions (line 275+) - UNCHANGED
│   │   ├── Main App Setup (line ~30) - UPDATED: MediaAnalysisAPI
│   │   └── Endpoints (line 4040+) - UPDATED: /api/media/*
│   │
│   ├── media_analysis.py              (Renamed from cotizador.py)
│   ├── hitl_push.py                   (Updated imports)
│   ├── archive_endpoint.py            (Updated imports)
│   ├── benchmark_models.py            (Updated imports)
│   ├── minimax_client.py              (NEW - MiniMax API client)
│   │   ├── MiniMaxConfig
│   │   ├── MiniMaxClient
│   │   ├── MiniMaxRequest
│   │   └── MiniMaxResponse
│   │
│   └── minimax_integration.py         (NEW - Integration layer)
│       ├── MiniMaxIntegration
│       ├── analyze_video_contact_sheet()
│       ├── transcribe_with_context()
│       └── summarize_analysis()
│
├── scripts/
│   ├── generate_contact_sheets.sh     (From dev/scripts)
│   └── video_processor.sh             (NEW utility)
│
├── config/
│   ├── .env                           (MEDIA_ANALYSIS_* vars)
│   └── requirements.txt               (fastapi>=0.104, openai>=1.0.0, etc.)
│
├── docker/
│   ├── Dockerfile                     (Updated CMD: media_analysis_api:app)
│   └── docker-compose.yml             (Network: media-services-network)
│
├── Caddyfile                          (NEW - media-analysis-api subdomain)
└── README.md                          (NEW - Service documentation)

FILE SIZE SUMMARY:
├── media_analysis_api.py    9,462 lines (95% same, 5% updated)
├── media_analysis.py        ~800 lines (95% same, 5% updated)
├── minimax_client.py        ~100 lines (NEW)
├── minimax_integration.py   ~80 lines (NEW)
└── Total codebase           ~10,500 lines
```

### AFTER Key Identifiers

| Identifier Type | New Value | File:Line Target | Status |
|-----------------|-----------|------------------|--------|
| Main Class | `MediaAnalysisAPI` | media_analysis_api.py:~50 | RENAME |
| Business Class | `MediaAnalysis` | media_analysis.py:~line TBD | RENAME |
| Logger Name | `"media_analysis"` | media_analysis_api.py:53 | RENAME |
| Module Name | `media_analysis` | media_analysis_api.py:57 | RENAME |
| Service Name | `media-analysis-api` | docker-compose.yml:3 | RENAME |
| Network Name | `media-services-network` | docker-compose.yml:19 | NEW |
| Env Prefix | `MEDIA_ANALYSIS_` | .env (all vars) | RENAME |
| Endpoint Prefix | `/api/media/` | media_analysis_api.py | RENAME |
| Aggregator | `POST /api/media/analyze` | media_analysis_api.py:NEW | NEW |

---

## 3. Network Isolation Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           AF ENVIRONMENT (devmaster)                                     │
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                         af-network (172.20.0.0/16)                                │  │
│  │                                                                                  │  │
│  │  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────────────┐ │  │
│  │  │    cotizador-api   │  │      n8n           │  │       PostgreSQL           │ │  │
│  │  │       :8000        │  │      :5679         │  │       :5432                │ │  │
│  │  │                    │  │                    │  │                            │ │  │
│  │  │ Dependencies:      │  │ Dependencies:      │  │ Dependencies:              │ │  │
│  │  │ - Deepgram (:5005) │  │ - cotizador-api    │  │ - cotizador-api            │ │  │
│  │  │ - n8n (webhook)    │  │ - PostgreSQL       │  │ - n8n                      │ │  │
│  │  │ - PostgreSQL       │  │ - External APIs    │  │                            │ │  │
│  │  └────────────────────┘  └────────────────────┘  └────────────────────────────┘ │  │
│  │                                                                                  │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                          │
│  ════════════════════════════════════════════════════════════════════════════════════  │
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                   media-services-network (172.28.0.0/16)                          │  │
│  │                                                                                  │  │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐   │  │
│  │  │                    media-analysis-api:8000                                │   │  │
│  │  │                                                                         │   │  │
│  │  │  Dependencies:                                                           │   │  │
│  │  │  - Deepgram (:5005) - SAME service, DIFFERENT network path              │   │  │
│  │  │  - MiniMax API (external - https://api.minimax.chat)                    │   │  │
│  │  │  - FFmpeg (local container)                                             │   │  │
│  │  │                                                                         │   │  │
│  │  │  NO ACCESS TO:                                                          │   │  │
│  │  │  - cotizador-api (different network)                                    │   │  │
│  │  │  - n8n (different network)                                              │   │  │
│  │  │  - PostgreSQL (different network - use external endpoint if needed)     │   │  │
│  │  │                                                                         │   │  │
│  │  └──────────────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                                  │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════════════
                              NETWORK ISOLATION RULES
═══════════════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  DENY ALL CROSS-NETWORK TRAFFIC                                                         │
│  ═════════════════════════════════                                                     │
│                                                                                          │
│  ┌────────────────────┐    ┌────────────────────┐    ┌────────────────────────────┐   │
│  │ media-analysis-api │ ✗  │   cotizador-api    │    │  media-analysis-api        │   │
│  │ CANNOT reach       │    │   CANNOT reach     │    │  CAN reach                 │   │
│  │                    │    │                    │    │                            │   │
│  │ - cotizador-api    │    │ - media-analysis   │    │  - Deepgram :5005          │   │
│  │ - n8n :5679        │    │ - MiniMax API      │    │  - MiniMax API (HTTPS)     │   │
│  │ - af-network IPs   │    │ - media-services   │    │  - FFmpeg (local)          │   │
│  │                    │      network IPs       │    │                            │   │
│  └────────────────────┘    └────────────────────┘    └────────────────────────────┘   │
│                                                                                          │
│  REASON: Complete service isolation for security and independent scaling                │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Network Configuration Details

#### BEFORE (cotizador-api)

```yaml
# /opt/clients/af/dev/services/cotizador-api/docker-compose.yml
services:
  cotizador-api:
    container_name: cotizador-api
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

#### AFTER (media-analysis-api)

```yaml
# /opt/services/media-analysis/docker/docker-compose.yml
services:
  media-analysis-api:
    container_name: media-analysis-api
    env_file:
      - ./config/.env
    ports:
      - "8001:8000"  # Different port to avoid conflict
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    networks:
      - media-services-network

  caddy:
    image: caddy:2.7
    container_name: media-analysis-caddy
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    ports:
      - "80:80"
      - "443:443"
    networks:
      - media-services-network
    depends_on:
      - media-analysis-api

networks:
  media-services-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
          gateway: 172.28.0.1

volumes:
  caddy_data:
```

---

## 4. Data Flow Through Aggregator

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          AGGREGATOR DATA FLOW DIAGRAM                                   │
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                           EXTERNAL CLIENT                                         │  │
│  │                                                                                  │  │
│  │    POST /api/media/analyze                                                       │  │
│  │    Content-Type: application/json                                                │  │
│  │    {                                                                             │  │
│  │      "media_type": "video",  // "video" | "audio" | "document" | "auto"         │  │
│  │      "media_url": "https://example.com/video.mp4",                               │  │
│  │      "prompt": "Describe what happens in this video",                             │  │
│  │      "options": {                                                                │  │
│  │        "extract_frames": true,                                                    │  │
│  │        "contact_sheets": true,                                                    │  │
│  │        "transcription": true,                                                     │  │
│  │        "minimax_analysis": true                                                   │  │
│  │      }                                                                          │  │
│  │    }                                                                             │  │
│  │                                                                                  │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                                 │
│                                        ▼                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                    media-analysis-api:8000                                        │  │
│  │                    POST /api/media/analyze                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐    │  │
│  │  │                      AGGREGATOR HANDLER                                  │    │  │
│  │  │                   (media_analysis_api.py:NEW)                            │    │  │
│  │  │                                                                         │    │  │
│  │  │  1. Validate request body                                                │    │  │
│  │  │  2. Generate request_id (UUID)                                           │    │  │
│  │  │  3. Start processing timer                                               │    │  │
│  │  │                                                                         │    │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘    │  │
│  │                                      │                                              │  │
│  │                    ┌─────────────────┼─────────────────┐                          │  │
│  │                    ▼                 ▼                 ▼                          │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────────┐    │  │
│  │  │   VIDEO BRANCH   │  │  AUDIO BRANCH    │  │      DOCUMENT BRANCH         │    │  │
│  │  │                  │  │                  │  │                              │    │  │
│  │  │ _process_video_  │  │ _process_audio_  │  │  _process_document_          │    │  │
│  │  │    analysis()    │  │    analysis()    │  │      analysis()              │    │  │
│  │  │                  │  │                  │  │                              │    │  │
│  │  │ ┌──────────────┐ │  │ ┌──────────────┐ │  │  ┌────────────────────────┐  │    │  │
│  │  │ │ Extract      │ │  │ │ Extract      │ │  │  │ Process document        │  │    │  │
│  │  │ │ frames @3fps │ │  │ │ audio from   │ │  │  │ (PDF, images, etc.)     │  │    │  │
│  │  │ │              │ │  │ │ video if URL │ │  │  │                          │  │    │  │
│  │  │ └──────┬───────┘ │  │ └──────┬───────┘ │  │  └───────────┬────────────┘  │    │  │
│  │  │        │         │  │        │         │  │              │               │    │  │
│  │  │        ▼         │  │        ▼         │  │              ▼               │    │  │
│  │  │ ┌──────────────┐ │  │ ┌──────────────┐ │  │  ┌────────────────────────┐  │    │  │
│  │  │ │ Create       │ │  │ │ Transcribe   │ │  │  │ Extract text content   │  │    │  │
│  │  │ │ contact      │ │  │ │ with         │ │  │  │                          │  │    │  │
│  │  │ │ sheets (2x3) │ │  │ │ Deepgram     │ │  │  └───────────┬────────────┘  │    │  │
│  │  │ └──────┬───────┘ │  │ └──────┬───────┘ │  │              │               │    │  │
│  │  │        │         │  │        │         │  │              ▼               │    │  │
│  │  │        │         │  │        │         │  │  ┌────────────────────────┐  │    │  │
│  │  │        │         │  │        │         │  │  │ OCR if needed          │  │    │  │
│  │  │        │         │  │        │         │  │  │ (images, scans)        │  │    │  │
│  │  │        │         │  │        │         │  │  └───────────┬────────────┘  │    │  │
│  │  │        │         │  │        │         │  │              │               │    │  │
│  │  │        ▼         │  │        ▼         │  │              ▼               │    │  │
│  │  │ ┌──────────────┐ │  │ ┌──────────────┐ │  │  ┌────────────────────────┐  │    │  │
│  │  │ │ MiniMax      │ │  │ │ MiniMax      │ │  │  │ MiniMax                │  │    │  │
│  │  │ │ Vision       │ │  │ │ Text Enhance │ │  │  │ Document Analysis      │  │    │  │
│  │  │ │ Analysis     │ │  │ │              │ │  │  │                        │  │    │  │
│  │  │ │ (contact     │ │  │ │ (transcript  │ │  │  │ (content + OCR text)   │  │    │  │
│  │  │ │  sheets)     │ │  │ │  context)    │ │  │  │                        │  │    │  │
│  │  │ └──────┬───────┘ │  │ └──────┬───────┘ │  │  └───────────┬────────────┘  │    │  │
│  │  │        │         │  │        │         │  │              │               │    │  │
│  │  └────────┼─────────┘  └────────┼─────────┘  └──────────────┼───────────────┘    │  │
│  │           │                    │                           │                      │  │
│  │           └────────────────────┼───────────────────────────┘                      │  │
│  │                                │                                                  │  │
│  │                                ▼                                                  │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐    │  │
│  │  │                      AGGREGATOR RESPONSE                                 │    │  │
│  │  │                                                                         │    │  │
│  │  │  {                                                                       │    │  │
│  │  │    "request_id": "uuid-v4-string",                                      │    │  │
│  │  │    "media_type": "video",                                               │    │  │
│  │  │    "prompt": "Describe what happens in this video",                     │    │  │
│  │  │    "results": {                                                         │    │  │
│  │  │      "video_analysis": "...",        // MiniMax vision output           │    │  │
│  │  │      "frames_extracted": 45,         // Number of frames                │    │  │
│  │  │      "contact_sheets_created": 8,    // Number of sheets                │    │  │
│  │  │      "transcription": "...",         // Deepgram output                 │    │  │
│  │  │      "minimax_analysis": "..."       // Combined analysis               │    │  │
│  │  │    },                                                                  │    │  │
│  │  │    "processing_time": 12.34,         // Seconds                         │    │  │
│  │  │    "confidence": 0.95                 // 0.0 - 1.0                      │    │  │
│  │  │  }                                                                       │    │  │
│  │  │                                                                         │    │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                                  │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                                 │
│                                        ▼                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                           EXTERNAL CLIENT                                         │  │
│  │                           HTTP 200 OK + JSON Response                            │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Aggregator Implementation Details

**File**: `api/media_analysis_api.py` (NEW section)

**Line Target**: After line 4848 (original `/api/analyze` endpoint)

```python
# NEW: Aggregator endpoint
router = APIRouter(prefix="/api/media", tags=["aggregator"])

class AnalyzeRequest(BaseModel):
    """Natural language media analysis request."""
    media_type: str  # "video", "audio", "document", "auto"
    media_url: Optional[str] = None
    media_path: Optional[str] = None
    prompt: str  # Natural language instruction
    options: Optional[Dict[str, Any]] = None

class AnalyzeResponse(BaseModel):
    """Aggregator response with full pipeline results."""
    request_id: str
    media_type: str
    prompt: str
    results: Dict[str, Any]
    processing_time: float
    confidence: float

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_media(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Natural language media analysis aggregator.

    Accepts a media URL/path and natural language prompt,
    routes to appropriate processing branch, and aggregates results.
    """
    import uuid
    from datetime import datetime

    request_id = str(uuid.uuid4())
    start_time = datetime.utcnow().timestamp()

    logger.info(f"Analysis request received: {request_id}")

    # Auto-detect media type if not specified
    if request.media_type == "auto":
        request.media_type = await _detect_media_type(request)

    # Route to appropriate branch
    if request.media_type == "video":
        results = await _process_video_analysis(request)
    elif request.media_type == "audio":
        results = await _process_audio_analysis(request)
    elif request.media_type == "document":
        results = await _process_document_analysis(request)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported media type: {request.media_type}"
        )

    # Aggregate results
    end_time = datetime.utcnow().timestamp()
    processing_time = end_time - start_time

    return AnalyzeResponse(
        request_id=request_id,
        media_type=request.media_type,
        prompt=request.prompt,
        results=results,
        processing_time=processing_time,
        confidence=_calculate_confidence(results)
    )
```

---

## 5. MiniMax Integration Points

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           MINIMAX INTEGRATION ARCHITECTURE                               │
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                    media-analysis-api (container)                                 │  │
│  │                                                                                  │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐    │  │
│  │  │                      MINIMAX CLIENT LAYER                                │    │  │
│  │  │                   (api/minimax_client.py)                                │    │  │
│  │  │                                                                         │    │  │
│  │  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │    │  │
│  │  │  │  MiniMaxConfig  │  │ MiniMaxRequest  │  │    MiniMaxResponse      │  │    │  │
│  │  │  │                 │  │                 │  │                         │  │    │  │
│  │  │  │ - api_key       │  │ - model         │  │  - id                   │  │    │  │
│  │  │  │ - base_url      │  │ - messages      │  │  - object               │  │    │  │
│  │  │  │ - model         │  │ - temperature   │  │  - created              │  │    │  │
│  │  │  │ - timeout       │  │ - max_tokens    │  │  - model                │  │    │  │
│  │  │  └─────────────────┘  │ - stream        │  │  - choices              │  │    │  │
│  │  │                        └─────────────────┘  │  - usage                │  │    │  │
│  │  │                                                └─────────────────────────┘  │    │  │
│  │  │                                                                         │    │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘    │  │
│  │                                    │                                              │  │
│  │                                    ▼                                              │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐    │  │
│  │  │                   MINIMAX INTEGRATION LAYER                             │    │  │
│  │  │                (api/minimax_integration.py)                             │    │  │
│  │  │                                                                         │    │  │
│  │  │  ┌─────────────────────────────────────────────────────────────────┐    │    │  │
│  │  │  │                   MiniMaxIntegration                             │    │    │  │
│  │  │  │                                                                │    │    │  │
│  │  │  │  ┌─────────────────────┐  ┌─────────────────────────────┐      │    │    │  │
│  │  │  │  │ vision_analysis()   │  │  analyze_video_contact_    │      │    │    │  │
│  │  │  │  │                     │  │  sheet()                    │      │    │    │  │
│  │  │  │  │ Input:              │  │                             │      │    │    │  │
│  │  │  │  │ - image_url         │  │  Input:                     │      │    │    │  │
│  │  │  │  │ - prompt            │  │  - contact_sheet_paths      │      │    │    │  │
│  │  │  │  │                     │  │  - prompt                   │      │    │    │  │
│  │  │  │  │ Output:             │  │                             │      │    │    │  │
│  │  │  │  │ - analysis_text     │  │  Output:                    │      │    │    │  │
│  │  │  │  │                     │  │  - video_description        │      │    │    │  │
│  │  │  │  └─────────────────────┘  └─────────────────────────────┘      │    │    │  │
│  │  │  │                                                                │    │    │  │
│  │  │  │  ┌─────────────────────┐  ┌─────────────────────────────┐      │    │    │  │
│  │  │  │  │ transcribe_with_    │  │  summarize_analysis()       │      │    │    │  │
│  │  │  │  │ context()           │  │                             │      │    │    │  │
│  │  │  │  │                     │  │  Input:                     │      │    │    │  │
│  │  │  │  │ Input:              │  │  - analysis_results dict    │      │    │    │  │
│  │  │  │  │ - transcription     │  │  - output_prompt            │      │    │    │  │
│  │  │  │  │ - context_prompt    │  │                             │      │    │    │  │
│  │  │  │  │                     │  │  Output:                    │      │    │    │  │
│  │  │  │  │ Output:             │  │  - summary_text             │      │    │    │  │
│  │  │  │  │ - enhanced_text     │  │                             │      │    │    │  │
│  │  │  │  └─────────────────────┘  └─────────────────────────────┘      │    │    │  │
│  │  │  │                                                                │    │    │  │
│  │  │  └─────────────────────────────────────────────────────────────────┘    │    │  │
│  │  │                                                                         │    │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                                  │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                                 │
│                                        ▼ HTTPS (port 443)                               │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                  │  │
│  │                              MINIMAX API                                         │  │
│  │                         https://api.minimax.chat                                 │  │
│  │                                                                                  │  │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐   │  │
│  │  │  POST /v1/chat/completions                                                │   │  │
│  │  │                                                                          │   │  │
│  │  │  Request Body:                                                           │   │  │
│  │  │  {                                                                       │   │  │
│  │  │    "model": "abab6.5s-chat",                                             │   │  │
│  │  │    "messages": [                                                         │   │  │
│  │  │      {                                                                   │   │  │
│  │  │        "role": "user",                                                   │   │  │
│  │  │        "content": [                                                      │   │  │
│  │  │          {"type": "text", "text": "Describe this image..."},             │   │  │
│  │  │          {"type": "image_url", "image_url": {"url": "https://..."}}      │   │  │
│  │  │        ]                                                                 │   │  │
│  │  │      }                                                                   │   │  │
│  │  │    ],                                                                    │   │  │
│  │  │    "temperature": 0.7,                                                   │   │  │
│  │  │    "max_tokens": 2048                                                    │   │  │
│  │  │  }                                                                       │   │  │
│  │  │                                                                          │   │  │
│  │  │  Response:                                                               │   │  │
│  │  │  {                                                                       │   │  │
│  │  │    "id": "gen_xxx",                                                      │   │  │
│  │  │    "object": "chat.completion",                                          │   │  │
│  │  │    "choices": [{                                                         │   │  │
│  │  │      "message": {                                                        │   │  │
│  │  │        "role": "assistant",                                              │   │  │
│  │  │        "content": "The image shows..."                                   │   │  │
│  │  │      }                                                                   │   │  │
│  │  │    }],                                                                   │   │  │
│  │  │    "usage": {"prompt_tokens": 150, "completion_tokens": 200}             │   │  │
│  │  │  }                                                                       │   │  │
│  │  │                                                                          │   │  │
│  │  └──────────────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                                  │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### MiniMax Integration Code Files

#### api/minimax_client.py (NEW FILE - ~100 lines)

**Purpose**: Low-level HTTP client for MiniMax API

```python
"""MiniMax API client for vision and text processing."""

import httpx
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import logging

logger = logging.getLogger("media_analysis")

class MiniMaxConfig(BaseModel):
    """MiniMax API configuration."""
    api_key: str
    base_url: str = "https://api.minimax.chat/v1"
    model: str = "abab6.5s-chat"

class MiniMaxMessage(BaseModel):
    """Message format for MiniMax API."""
    role: str  # "system", "user", "assistant"
    content: str

class MiniMaxRequest(BaseModel):
    """Request format for MiniMax API."""
    model: str
    messages: List[MiniMaxMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048

class MiniMaxResponse(BaseModel):
    """Response format from MiniMax API."""
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

class MiniMaxClient:
    """Client for interacting with MiniMax API."""

    def __init__(self, config: MiniMaxConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=120.0)

    async def chat(self, messages: List[MiniMaxMessage]) -> MiniMaxResponse:
        """Send chat request to MiniMax."""
        request_data = MiniMaxRequest(
            model=self.config.model,
            messages=messages
        )

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        response = await self.client.post(
            f"{self.config.base_url}/chat/completions",
            json=request_data.model_dump(),
            headers=headers
        )

        response.raise_for_status()
        return MiniMaxResponse(**response.json())

    async def vision_analysis(
        self,
        image_url: str,
        prompt: str
    ) -> str:
        """Analyze image with vision capabilities."""
        messages = [
            MiniMaxMessage(
                role="user",
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            )
        ]

        response = await self.chat(messages)
        return response.choices[0]["message"]["content"]

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
```

#### api/minimax_integration.py (NEW FILE - ~80 lines)

**Purpose**: High-level integration layer for media processing

```python
"""MiniMax integration for video, audio, and document analysis."""

from .minimax_client import MiniMaxClient, MiniMaxConfig, MiniMaxMessage
from typing import List, Optional
import logging

logger = logging.getLogger("media_analysis")

class MiniMaxIntegration:
    """Integration layer for MiniMax API."""

    def __init__(self, api_key: str):
        config = MiniMaxConfig(api_key=api_key)
        self.client = MiniMaxClient(config)

    async def analyze_video_contact_sheet(
        self,
        contact_sheet_paths: List[str],
        prompt: str
    ) -> str:
        """Analyze video contact sheets with MiniMax vision."""
        messages = [
            MiniMaxMessage(
                role="user",
                content=f"Analyze these video frames:\n\n{prompt}\n\nFrames:"
            )
        ]

        # Add each contact sheet
        for path in contact_sheet_paths:
            messages[0].content.append({
                "type": "image_url",
                "image_url": {"url": f"file://{path}"}
            })

        response = await self.client.chat(messages)
        return response.choices[0]["message"]["content"]

    async def transcribe_with_context(
        self,
        transcription: str,
        context_prompt: str
    ) -> str:
        """Enhance transcription with MiniMax text processing."""
        messages = [
            MiniMaxMessage(
                role="system",
                content="You are a transcription enhancement assistant. Improve the accuracy and formatting of transcriptions."
            ),
            MiniMaxMessage(
                role="user",
                content=f"{context_prompt}\n\nTranscription:\n{transcription}"
            )
        ]

        response = await self.client.chat(messages)
        return response.choices[0]["message"]["content"]

    async def summarize_analysis(
        self,
        analysis_results: dict,
        output_prompt: str
    ) -> str:
        """Summarize multi-branch analysis results."""
        messages = [
            MiniMaxMessage(
                role="user",
                content=f"{output_prompt}\n\nAnalysis Results:\n{analysis_results}"
            )
        ]

        response = await self.client.chat(messages)
        return response.choices[0]["message"]["content"]

    async def close(self):
        """Close the MiniMax client."""
        await self.client.close()
```

---

## 6. FILE:LINE Reference Targets

### cotizador_api.py Main File Structure

| Section | Line Range | Content | Action |
|---------|------------|---------|--------|
| Imports | 20-46 | `import` statements | UPDATE (line 57) |
| Logger | 53 | `ab_test_logger = logging.getLogger("cotizador")` | UPDATE |
| Main App | ~30-60 | `app = FastAPI(...)` | UPDATE class name |
| Data Models | 417-900+ | Pydantic models | KEEP (review for identifier refs) |
| Helper Functions | 275-1250 | Core functions | KEEP (review for identifier refs) |
| Endpoints | 4040-8873 | @app.post/get decorators | UPDATE ALL |

### Endpoint Definitions (Grep Pattern)

**Original Pattern**:
```bash
grep -n "@app\." /opt/clients/af/dev/services/cotizador-api/cotizador_api.py
```

**Target Lines**:
| Line | Original Endpoint | New Endpoint | Action |
|------|-------------------|--------------|--------|
| 4040 | `GET /health` | `GET /health` | KEEP |
| 4056 | `GET /` | `GET /` | KEEP |
| 4075 | `POST /api/extract-frames` | `POST /api/media/extract-frames` | RENAME |
| 4204 | `POST /api/video_express` | `POST /api/media/video_express` | RENAME |
| 4377 | `POST /api/transcribe` | `POST /api/media/transcribe` | RENAME |
| 4393 | `POST /api/customer-context` | `POST /api/media/customer-context` | RENAME |
| 4569 | `POST /api/generate-form-link` | `POST /api/media/generate-form-link` | RENAME |
| 4630 | `POST /api/create-quote` | `POST /api/media/create-quote` | RENAME |
| 4746 | `POST /api/update-lead-stage` | `POST /api/media/update-lead-stage` | RENAME |
| 4816 | `POST /api/quote-feedback` | `POST /api/media/quote-feedback` | RENAME |
| 4848 | `POST /api/analyze` | `POST /api/media/analyze` | RENAME + ENHANCE |
| 5213 | `GET /api/quote/{session_id}` | `GET /api/media/quote/{session_id}` | RENAME |
| 5340 | `GET /api/hitl/queue` | `GET /api/media/hitl/queue` | RENAME |
| 5451 | `GET /api/hitl/stream` | `GET /api/media/hitl/stream` | RENAME |
| 5608 | `POST /api/hitl-review` | `POST /api/media/hitl-review` | RENAME |
| 6041 | `POST /api/quotes/{session_id}/claim` | `POST /api/media/quotes/{session_id}/claim` | RENAME |
| 6104 | `POST /api/quotes/{session_id}/release` | `POST /api/media/quotes/{session_id}/release` | RENAME |
| 6143 | `POST /api/v1/send-followup` | `POST /api/media/v1/send-followup` | RENAME |
| 6508 | `POST /api/generate-quote-pdf` | `POST /api/media/generate-quote-pdf` | RENAME |
| 6561 | `GET /quote/active/{contact_id}` | `GET /api/media/quote/active/{contact_id}` | RENAME |
| 6579 | `POST /quote/merge` | `POST /api/media/quote/merge` | RENAME |
| 6629 | `POST /api/store-media` | `POST /api/media/store-media` | RENAME |
| 6728 | `POST /api/compress-pdf` | `POST /api/media/compress-pdf` | RENAME |
| 6819 | `POST /api/process-document` | `POST /api/media/process-document` | RENAME |
| 7258 | `POST /api/chat/parse-stream` | `POST /api/media/chat/parse-stream` | RENAME |
| 7617 | `POST /api/messages/ingest/v2` | `POST /api/media/messages/ingest/v2` | RENAME |
| 8438 | `POST /api/quote/{quote_id}/approve` | `POST /api/media/quote/{quote_id}/approve` | RENAME |
| 8488 | `POST /api/quote/{quote_id}/reject` | `POST /api/media/quote/{quote_id}/reject` | RENAME |
| 8538 | `POST /api/quote/{quote_id}/schedule` | `POST /api/media/quote/{quote_id}/schedule` | RENAME |
| 8587 | `POST /api/lead/{lead_id}/close` | `POST /api/media/lead/{lead_id}/close` | RENAME |
| 8688 | `POST /api/scores/calculate` | `POST /api/media/scores/calculate` | RENAME |
| 8710 | `GET /api/scores/lead/{lead_id}` | `GET /api/media/scores/lead/{lead_id}` | RENAME |

### Router Declarations (Grep Pattern)

**Original Pattern**:
```bash
grep -n "router = APIRouter\|@router\." /opt/clients/af/dev/services/cotizador-api/*.py
```

**If routers exist** (not visible in grep output, may use direct @app decorators):

| File | Line | Pattern | Action |
|------|------|---------|--------|
| cotizador_api.py | Any | `router = APIRouter(...)` | UPDATE prefix |
| Any | Any | `@router.post("/analyze/...` | UPDATE to `/media/...` |

### Caddyfile Routes (Grep Pattern)

**Original Pattern**:
```bash
grep -rn "cotizador\|/api/analyze" /opt/clients/af/dev/services/cotizador-api/Caddyfile
```

**Target File**: `/opt/services/media-analysis/Caddyfile` (NEW)

```
media-analysis-api.automatic.picturelle.com {
    route /api/media/* {
        reverse_proxy media-analysis-api:8000 {
            header_up Host {host}
            header_up X-Real-IP {remote}
            header_up X-Forwarded-For {remote}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    route /health {
        respond "OK" 200 {
            type text/plain
        }
    }

    route /docs {
        reverse_proxy media-analysis-api:8000
    }

    route /redoc {
        reverse_proxy media-analysis-api:8000
    }
}

localhost:8001 {
    reverse_proxy media-analysis-api:8000
}
```

### Docker Compose Configuration (Grep Pattern)

**Original Pattern**:
```bash
grep -n "cotizador\|af-network\|af_default" /opt/clients/af/dev/services/cotizador-api/docker-compose.yml
```

**Target Lines** (BEFORE):
| Line | Content | Change |
|------|---------|--------|
| 3 | `cotizador-api:` | RENAME to `media-analysis-api:` |
| 5 | `container_name: cotizador-api` | RENAME to `container_name: media-analysis-api` |
| 17 | `networks: - af_default` | RENAME to `networks: - media-services-network` |
| 19 | `af_default:` | RENAME to `media-services-network:` |

---

## 7. BEFORE/AFTER Code Patterns

### Pattern 1: Endpoint Renaming

**BEFORE** (cotizador_api.py:4040-4100):
```python
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_media(request: AnalyzeRequest):
    """Analyze media endpoint."""
    # ... implementation
```

**AFTER** (media_analysis_api.py:4040-4100):
```python
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/api/media/analyze", response_model=AnalyzeResponse)
async def analyze_media(request: AnalyzeRequest):
    """Analyze media endpoint - MEDIA SERVICES VERSION."""
    # ... implementation
```

**Sed Command**:
```bash
# Rename all /api/analyze/* to /api/media/*
sed -i 's|@app\.post("/api/analyze/|@app.post("/api/media/|g' media_analysis_api.py
sed -i 's|@app\.get("/api/analyze/|@app.get("/api/media/|g' media_analysis_api.py
sed -i 's|@app\.put("/api/analyze/|@app.put("/api/media/|g' media_analysis_api.py
sed -i 's|@app\.delete("/api/analyze/|@app.delete("/api/media/|g' media_analysis_api.py
```

### Pattern 2: Service Name Renaming

**BEFORE** (docker-compose.yml:1-20):
```yaml
version: '3.8'

services:
  cotizador-api:
    build:
      context: .
      dockerfile: Dockerfile
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

**AFTER** (docker-compose.yml:1-30):
```yaml
version: '3.8'

services:
  media-analysis-api:
    build:
      context: ./api
      dockerfile: Dockerfile
    container_name: media-analysis-api
    restart: unless-stopped
    env_file:
      - ./config/.env
    ports:
      - "8001:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    networks:
      - media-services-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  caddy:
    image: caddy:2.7
    container_name: media-analysis-caddy
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    ports:
      - "80:80"
      - "443:443"
    networks:
      - media-services-network
    depends_on:
      - media-analysis-api

networks:
  media-services-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
          gateway: 172.28.0.1

volumes:
  caddy_data:
```

### Pattern 3: Network Name Renaming

**BEFORE** (docker-compose.yml:19-21):
```yaml
networks:
  af_default:
    external: true
```

**AFTER** (docker-compose.yml:25-29):
```yaml
networks:
  media-services-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
          gateway: 172.28.0.1
```

### Pattern 4: Class Name Renaming

**BEFORE** (cotizador_api.py:50-60):
```python
from cotizador import analyze_images, calculate_quote, format_quote_message, MODEL

app = FastAPI(
    title="Cotizador API",
    description="Multi-purpose media analysis and quote generation service",
    version="1.0.0"
)

logger = logging.getLogger("cotizador")
```

**AFTER** (media_analysis_api.py:50-65):
```python
from media_analysis import analyze_images, calculate_quote, format_quote_message, MODEL

app = FastAPI(
    title="Media Analysis API",
    description="Media processing service with natural language aggregator and MiniMax integration",
    version="1.0.0"
)

logger = logging.getLogger("media_analysis")
```

### Pattern 5: Environment Variable Renaming

**BEFORE** (.env):
```
# Cotizador API Configuration
COTIZADOR_ENV=production
COTIZADOR_API_KEY=your-api-key
DEEPGRAM_API_KEY=your-deepgram-key
GROQ_API_KEY=your-groq-key
UPLOAD_DIR=/app/uploads
LOG_LEVEL=INFO
```

**AFTER** (config/.env):
```
# Media Analysis API Configuration
MEDIA_ANALYSIS_ENV=production
MEDIA_ANALYSIS_API_KEY=your-api-key
DEEPGRAM_API_KEY=your-deepgram-key
GROQ_API_KEY=your-groq-key
MINIMAX_API_KEY=your-minimax-key
UPLOAD_DIR=/app/uploads
OUTPUT_DIR=/app/outputs
LOG_LEVEL=INFO
```

---

## 8. Enhanced Verification Commands

### Phase 3 Verification: Code Renaming

```bash
# =============================================================================
# VERIFICATION: Phase 3 - Surgical Code Renaming
# =============================================================================

echo "=== 3.1 Verify Class Names ==="
ssh devmaster 'grep "^class Media" /opt/services/media-analysis/api/*.py'

echo ""
echo "=== 3.2 Verify Endpoint Renaming ==="
ssh devmaster 'grep "@app\.post.*/api/media" /opt/services/media-analysis/api/media_analysis_api.py | head -10'

echo ""
echo "=== 3.3 Verify Imports ==="
ssh devmaster 'grep "^from media_analysis\|^import media_analysis" /opt/services/media-analysis/api/media_analysis_api.py | head -10'

echo ""
echo "=== 3.4 Verify Environment Variables ==="
ssh devmaster 'grep "MEDIA_ANALYSIS_" /opt/services/media-analysis/config/.env | head -10'

echo ""
echo "=== 3.5 Verify No cotizador References (MUST BE EMPTY) ==="
ssh devmaster 'grep -r "cotizador" /opt/services/media-analysis/api/ --include="*.py" | grep -v "^Binary" || echo "OK: No cotizador references found"'

echo ""
echo "=== 3.6 Verify No /api/analyze Endpoints (MUST BE EMPTY) ==="
ssh devmaster 'grep -r "/api/analyze" /opt/services/media-analysis/api/ --include="*.py" || echo "OK: No /api/analyze endpoints found"'
```

### Phase 4 Verification: Docker Configuration

```bash
# =============================================================================
# VERIFICATION: Phase 4 - Network & Configuration
# =============================================================================

echo "=== 4.1 Verify Docker Compose Syntax ==="
ssh devmaster 'cd /opt/services/media-analysis && docker compose config'

echo ""
echo "=== 4.2 Verify Dockerfile Syntax ==="
ssh devmaster 'docker build --file /opt/services/media-analysis/docker/Dockerfile --tag media-analysis-api:test .'

echo ""
echo "=== 4.3 Verify Network Creation ==="
ssh devmaster 'docker network inspect media-services-network 2>/dev/null | jq ".[0].Name" || echo "Network not found"'
```

### Phase 8 Verification: Complete Testing

```bash
# =============================================================================
# VERIFICATION: Phase 8 - Testing & Verification
# =============================================================================

echo "=== 8.1 Check Container Status ==="
ssh devmaster 'docker ps --filter "name=media-analysis" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'

echo ""
echo "=== 8.2 Health Check ==="
curl -s http://localhost:8001/health

echo ""
echo "=== 8.3 Test All Endpoints ==="
echo "Testing GET /health..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health
echo ""

echo "Testing POST /api/media/transcribe..."
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/api/media/transcribe \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "test.wav"}'
echo ""

echo "Testing POST /api/media/process-document..."
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/api/media/process-document \
  -H "Content-Type: application/json" \
  -d '{"document_url": "test.pdf"}'
echo ""

echo "Testing POST /api/media/analyze (NEW)..."
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/api/media/analyze \
  -H "Content-Type: application/json" \
  -d '{"media_type": "video", "media_url": "test.mp4", "prompt": "Describe this video"}'
echo ""

echo "=== 8.4 Verify Network Isolation ==="
ssh devmaster 'docker network inspect media-services-network | jq ".[0].Containers"'

echo ""
echo "=== 8.5 Check Logs for Errors ==="
ssh devmaster 'docker logs media-analysis-api --since 5m 2>&1 | grep -i error | tail -10 || echo "No errors found"'
```

### Complete Endpoint Test Suite

```bash
#!/bin/bash
# test_media_analysis_api.sh - Complete endpoint test suite

BASE_URL="http://localhost:8001"
PASS=0
FAIL=0

echo "=== Media Analysis API Test Suite ==="
echo ""

# Test 1: Health Check
echo -n "[1/8] Health check... "
response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
if [ "$response" = "200" ]; then
    echo "PASS (HTTP $response)"
    ((PASS++))
else
    echo "FAIL (HTTP $response)"
    ((FAIL++))
fi

# Test 2: Root endpoint
echo -n "[2/8] Root endpoint... "
response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/")
if [ "$response" = "200" ]; then
    echo "PASS (HTTP $response)"
    ((PASS++))
else
    echo "FAIL (HTTP $response)"
    ((FAIL++))
fi

# Test 3: Transcribe endpoint
echo -n "[3/8] Transcribe endpoint... "
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/media/transcribe" \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "https://example.com/audio.wav"}')
if [ "$response" = "200" ] || [ "$response" = "400" ] || [ "$response" = "422" ]; then
    echo "PASS (HTTP $response - endpoint exists)"
    ((PASS++))
else
    echo "FAIL (HTTP $response)"
    ((FAIL++))
fi

# Test 4: Process document endpoint
echo -n "[4/8] Process document endpoint... "
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/media/process-document" \
  -H "Content-Type: application/json" \
  -d '{"document_url": "https://example.com/document.pdf"}')
if [ "$response" = "200" ] || [ "$response" = "400" ] || [ "$response" = "422" ]; then
    echo "PASS (HTTP $response - endpoint exists)"
    ((PASS++))
else
    echo "FAIL (HTTP $response)"
    ((FAIL++))
fi

# Test 5: Aggregator endpoint (NEW)
echo -n "[5/8] Aggregator endpoint (NEW)... "
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/media/analyze" \
  -H "Content-Type: application/json" \
  -d '{"media_type": "video", "media_url": "https://example.com/video.mp4", "prompt": "Describe this video"}')
if [ "$response" = "200" ] || [ "$response" = "400" ] || [ "$response" = "422" ]; then
    echo "PASS (HTTP $response - endpoint exists)"
    ((PASS++))
else
    echo "FAIL (HTTP $response)"
    ((FAIL++))
fi

# Test 6: Store media endpoint
echo -n "[6/8] Store media endpoint... "
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/media/store-media" \
  -H "Content-Type: application/json" \
  -d '{"media_type": "video", "media_url": "https://example.com/video.mp4"}')
if [ "$response" = "200" ] || [ "$response" = "400" ] || [ "$response" = "422" ]; then
    echo "PASS (HTTP $response - endpoint exists)"
    ((PASS++))
else
    echo "FAIL (HTTP $response)"
    ((FAIL++))
fi

# Test 7: Video express endpoint
echo -n "[7/8] Video express endpoint... "
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/media/video_express" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://example.com/video.mp4"}')
if [ "$response" = "200" ] || [ "$response" = "400" ] || [ "$response" = "422" ]; then
    echo "PASS (HTTP $response - endpoint exists)"
    ((PASS++))
else
    echo "FAIL (HTTP $response)"
    ((FAIL++))
fi

# Test 8: Extract frames endpoint
echo -n "[8/8] Extract frames endpoint... "
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/media/extract-frames" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://example.com/video.mp4"}')
if [ "$response" = "200" ] || [ "$response" = "400" ] || [ "$response" = "422" ]; then
    echo "PASS (HTTP $response - endpoint exists)"
    ((PASS++))
else
    echo "FAIL (HTTP $response)"
    ((FAIL++))
fi

echo ""
echo "=== Test Suite Complete ==="
echo "Passed: $PASS/8"
echo "Failed: $FAIL/8"

if [ "$FAIL" -eq 0 ]; then
    echo "SUCCESS: All tests passed!"
    exit 0
else
    echo "WARNING: Some tests failed"
    exit 1
fi
```

### Quick Verification One-Liner

```bash
# Quick verification of critical changes
ssh devmaster 'echo "=== Quick Verification ===" && \
echo "1. Class names:" && grep "^class Media" /opt/services/media-analysis/api/*.py && \
echo "2. Endpoint prefix:" && grep "@app\.post.*/api/media" /opt/services/media-analysis/api/media_analysis_api.py | head -1 && \
echo "3. Logger name:" && grep "logger = logging.getLogger" /opt/services/media-analysis/api/media_analysis_api.py && \
echo "4. Service name:" && grep "container_name:" /opt/services/media-analysis/docker-compose.yml && \
echo "5. Network name:" && grep "media-services-network" /opt/services/media-analysis/docker-compose.yml && \
echo "6. Env prefix:" && grep "MEDIA_ANALYSIS_" /opt/services/media-analysis/config/.env | head -1 && \
echo "7. No cotizador refs:" && (grep -r "cotizador" /opt/services/media-analysis/api/*.py && echo "FAIL: Found cotizador references" || echo "OK: No cotizador references")'
```

---

## Appendix A: Complete Grep Reference

### All Grep Patterns for Verification

| Pattern | Purpose | Expected Result |
|---------|---------|-----------------|
| `grep -n "^class Media" *.py` | Verify class renames | MediaAnalysisAPI, MediaAnalysis |
| `grep -n "@app\.post.*/api/media" *.py` | Verify endpoint migration | All /api/media/* endpoints |
| `grep -n "logger = logging.getLogger" *.py` | Verify logger rename | `"media_analysis"` |
| `grep -n "^from media_analysis" *.py` | Verify import updates | media_analysis imports |
| `grep -r "cotizador" api/` | Check for leftover references | No results |
| `grep -r "/api/analyze" api/` | Check for old endpoints | No results |
| `grep "container_name:" docker-compose.yml` | Verify service name | `media-analysis-api` |
| `grep "media-services-network" docker-compose.yml` | Verify network name | Present |
| `grep "MEDIA_ANALYSIS_" .env` | Verify env prefix | All vars updated |

---

## Document End

**Document Version:** 1.1
**Created:** 2026-01-18 22:15
**Author:** $USER
**Model:** claude-sonnet-4-5-20250929

This document provides complete BEFORE/AFTER architecture diagrams, explicit FILE:LINE targets, code patterns, and verification commands for the media-analysis-api cloning project.
