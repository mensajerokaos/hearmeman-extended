# Media Analysis API - Surgical Cloning Context

## Overview

Clone AF's cotizador-api infrastructure from devmaster to `/opt/services/media-analysis/` for media analysis operations (video, audio, document processing).

## Source System

| Property | Value |
|----------|-------|
| Source Path (devmaster) | `/opt/clients/af/dev/services/cotizador-api/` |
| Source Endpoint | `http://cotizador-api:8000/api/analyze` |
| Source Container | `cotizador-api` on af-network |
| Reference Scripts | `/opt/clients/af/dev/scripts/vision-testing/` |

## Services to Clone

| File | Purpose |
|------|---------|
| `cotizador_api.py` | Main FastAPI service (~344KB, 50+ endpoints) |
| `docker-compose.yml` | Service orchestration |
| `Dockerfile` | Container build |
| `.env` | Environment configuration |
| `Caddyfile` | Web server routing |
| `cotizador.py` | Core analysis logic |
| `hitl_push.py` | Human-in-the-loop push |
| `archive_endpoint.py` | Archival operations |
| `benchmark_models.py` | Model benchmarking |

## Target System

| Property | Value |
|----------|-------|
| Target Path | `/opt/services/media-analysis/` |
| Target Endpoint | `http://media-analysis-api:8000/api/media` |
| Target Network | `media-services-network` (new) |
| Target Container | `media-analysis-api` |

## Architecture - Three Branches

### Audio Branch
- **Endpoint**: `POST /api/media/audio`
- **Primary**: Deepgram transcription
- **Fallback**: Groq → OpenAI → Gemini
- **Languages**: Spanish (es-MX), Spanglish
- **Dependencies**: Deepgram API Key, Groq API Key, FFmpeg (libopus/ogg)

### Video Branch
- **Endpoint**: `POST /api/media/video`
- **Pipeline**: Video → 3fps Frame Extraction → 2x3 Grid → Contact Sheet → LLM
- **Output Paths**:
  - `/IMG/` - Individual frames
  - `/ImageContactSheets-Img/` - 2x3 grid contact sheets
- **Analysis**: MiniMax Vision / GPT-4V
- **Dependencies**: FFmpeg

### Document Branch
- **Endpoint**: `POST /api/media/document`
- **Capabilities**: Image/document OCR and analysis
- **Dependencies**: OCR libraries

## Key Features to Preserve

1. **Aggregator Endpoint** - Natural language prompt support
   - `POST /api/media/analyze` - Accepts video URL + prompt, orchestrates full pipeline

2. **Contact Sheet Generation**
   - 2x3 grid layout (6 frames per sheet)
   - Optimized for LLM parsing
   - Reference: `generate_contact_sheets.sh`

3. **Multi-Provider Fallback**
   - Transcription: Deepgram → Groq → OpenAI → Gemini
   - Vision: MiniMax → GPT-4V → Claude Vision

## Naming Conventions (To Change)

| Original | New |
|----------|-----|
| `cotizador-api` | `media-analysis-api` |
| `/api/analyze/*` | `/api/media/*` |
| `af-network` | `media-services-network` |
| `cotizador_api.py` | `media_analysis_api.py` |
| Container: `cotizador-api` | Container: `media-analysis-api` |

## Dependencies

- FastAPI (Python web framework)
- FFmpeg (video/audio processing)
- Deepgram SDK
- Groq SDK
- OpenAI SDK (fallback)
- Google Generative AI SDK (fallback)
- PIL/Pillow (image processing)

## Next Steps (Bead Chain)

1. `ma-01`: Read cotizador-api structure from devmaster (READ-ONLY)
2. `ma-02`: Read contact sheet scripts from devmaster (READ-ONLY)
3. `ma-03`: Create PRD for surgical cloning
4. `ma-04`: Clone service to /opt/services/media-analysis/
5. `ma-05`: Rename endpoints/routes
6. `ma-06`: Add aggregator with prompt support
7. `ma-07`: Add video branch implementation
8. `ma-08`: Add audio branch implementation
9. `ma-09`: Add document branch implementation
10. `ma-10`: Integrate MiniMax API
11. `ma-11`: Create Caddyfile configuration
12. `ma-12`: Deploy and test
13. `ma-13`: Research MiniMax via OpenRouter
14. `ma-14`: Add beat reminder for OpenRouter integration

## References

- BRV Context: `.brv/context-tree/structure/media_analysis/`
- Dev Scripts: `/opt/clients/af/dev/scripts/vision-testing/`
- AF-VPS Skill: `/home/oz/.claude/skills/af-vps.md`
