## Relations
@structure/media_analysis/media_analysis_pipeline_overview.md

## Raw Concept
**Task:**
Media Analysis API - Cotizador Clone

**Changes:**
- Documented audio transcription branch and fallback logic

**Files:**
- cotizador_api.py

**Flow:**
Audio File -> Format Normalization -> Transcription Provider -> Text Result

**Timestamp:** 2026-01-18

## Narrative
### Structure
- /api/analyze/audio endpoint
- cotizador_api.py transcription logic

### Dependencies
- Deepgram API Key
- Groq/Grok API Key
- FFmpeg (libopus/ogg config)

### Features
- Multi-provider fallback: Groq -> Deepgram -> OpenAI -> Gemini
- Support for multiple audio formats
- Optimized for Spanish (es-MX) and Spanglish
- Asynchronous transcription processing
