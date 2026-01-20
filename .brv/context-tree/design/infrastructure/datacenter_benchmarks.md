## Relations
@structure/deployment/runpod_deployment.md

## Raw Concept
**Task:**
SteadyDancer Integration Research

**Changes:**
- Added RunPod A100 pricing, spot savings, and multi-GPU throughput strategy

**Files:**
- structure/deployment/runpod_deployment.md

**Flow:**
Select Cloud -> Select GPU -> Select Instance Type (On-demand/Spot) -> Multi-instance for throughput

**Timestamp:** 2026-01-18

## Narrative
### Structure
- RunPod A100 80GB pricing and cloud comparison table

### Dependencies
- PCIe 4.0 x16 minimum for A100 80GB performance

### Features
- Secure Cloud (T3/T4): $0.39 - $1.74/hr
- Community Cloud (P2P): $0.19/hr
- Spot Instances: 30-70% cost savings
- Multi-GPU: ComfyUI does not parallelize single workflows; use multiple instances for throughput scaling
