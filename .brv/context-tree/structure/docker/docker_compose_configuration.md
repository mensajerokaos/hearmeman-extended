## Relations
@structure/docker/docker_compose_configuration.md

## Raw Concept
**Task:**
Document Docker Compose updates for SteadyDancer

**Changes:**
- Updated docker-compose with 14 new environment variables for SteadyDancer control

**Files:**
- docker/docker-compose.yml
- CLAUDE.md

**Flow:**
docker-compose up -> start.sh -> ENV detection -> conditional model download -> workflow execution

**Timestamp:** 2026-01-18

## Narrative
### Structure
- docker/docker-compose.yml
- Environment Variables table in CLAUDE.md

### Dependencies
- Added 14 new environment variables for SteadyDancer/Turbo configuration
- Persistent volume mounts for models and output

### Features
- Service Toggling: ENABLE_STEADYDANCER, ENABLE_WAN22_DISTILL
- Model selection: STEADYDANCER_VARIANT (fp16/fp8/gguf)
- Optimization: VibeVoice/XTTS/Chatterbox disabled to free ~24GB VRAM
