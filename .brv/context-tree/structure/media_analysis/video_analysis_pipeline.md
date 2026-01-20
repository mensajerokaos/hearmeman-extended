## Relations
@structure/media_analysis/media_analysis_pipeline_overview.md

## Raw Concept
**Task:**
Media Analysis API - Cotizador Clone

**Changes:**
- Documented specific video processing pipeline for media analysis

**Files:**
- generate_contact_sheets.sh

**Flow:**
Video -> Extract Frames (3fps) -> Grid Layout (2x3) -> Contact Sheet -> LLM Analysis

**Timestamp:** 2026-01-18

## Narrative
### Structure
- /opt/services/media-analysis/IMG/: Extraction output
- /opt/services/media-analysis/ImageContactSheets-Img/: Final sheets

### Dependencies
- FFmpeg
- generate_contact_sheets.sh (Reference script)

### Features
- 3fps extraction rate
- 2x3 grid layout for contact sheets
- Optimized for LLM visual analysis (MiniMax/GPT-4V)
- Sequential frame processing
