---
title: Qwen3-TTS + Fish Audio S2 RunPod Pattern
project: runpod
artifact_status: current
artifact_role: implementation pattern
date: 2026-05-04
source_project: recuerdos-vivos / Familia Sin Fin
branch: feature/qwen3-fish-tts
---

# Qwen3-TTS + Fish Audio S2 RunPod Pattern

## Purpose

Build a reusable RunPod lane for Spanish voiceover generation where:

- Qwen3-TTS is the primary production candidate.
- Fish Audio S2 Pro is the emotional-quality challenger.
- Recuerdos Vivos / Familia Sin Fin provides the scripts and listening criteria.

This pattern is stored in the RunPod project, not the Recuerdos Vivos repo, so future voiceover work can reuse the same pod/template infrastructure.

## Existing Knowledge Checked

RLM already had Qwen3-TTS patterns before this artifact:

- `projects/ai-content/patterns/qwen-3-tts-on-falai--voice-design-clone-voice-text-to-speech.md`
- `global/falai-qwen3-tts-voice-cloning-comprehensive-agent-guide.md`
- `projects/endangered-alphabets/patterns/voice-cloning-pipeline-falai-qwen3-tts.md`
- `projects/recuerdos-vivos/patterns/runpod-tts-pattern-qwen3-tts-primary-fish-s2-challenger.md`

The fal.ai Qwen3-TTS notes are useful for API usage and cloning gotchas, but this RunPod lane should focus on self-hosted/offline pod behavior.

## RunPod Credit Smoke Check

Checked via RunPod GraphQL on 2026-05-04:

| Field | Value |
| --- | ---: |
| `clientBalance` | `6.3614076245` |
| `currentSpendPerHr` | `0` |
| `spendLimit` | `80` |
| `underBalance` | `false` |
| Active pods | `0` |

Practical implication: enough for a short smoke run, but keep the first pod to a short 24GB test session and stop it immediately after the first audio outputs.

## GPU Recommendation

Use a 24GB GPU for the first shared smoke run:

- RTX 4090 24GB if available.
- RTX 3090 24GB, L4 24GB, or A5000 24GB as fallback.

Reason:

- Qwen3-TTS 0.6B/1.7B should fit comfortably for testing.
- Fish Audio S2 Pro officially requires 24GB VRAM for inference.
- A 24GB pod is the cheapest useful test that covers both candidates.

Upgrade only if needed:

- A40 / A6000 / L40 / L40S 48GB if Fish S2 OOMs or runs too slowly.
- H100/H200 only if Fish S2 clearly wins and production speed matters; do not start there.

## Model Positioning

### Qwen3-TTS

- Repo: https://github.com/QwenLM/Qwen3-TTS
- Paper: https://arxiv.org/abs/2601.15621
- License: Apache 2.0.
- Languages include Spanish.
- Supports voice design, custom voice cloning, and streaming.
- Official low-latency claim: 97ms first packet with its dual-track streaming design.

Use Qwen3-TTS for:

- Main Spanish VO candidate generation.
- Voice design without a reference voice.
- Cloned-voice runs if a reference is provided.
- Production use if output quality is good enough, because license is straightforward.

### Fish Audio S2 Pro

- Repo: https://github.com/fishaudio/fish-speech
- Docs: https://speech.fish.audio/
- Model card: https://huggingface.co/fishaudio/s2-pro
- Paper: https://arxiv.org/abs/2603.08823
- License: Fish Audio Research License.
- Official inference requirement: 24GB GPU memory.
- Spanish is listed as Tier 2 language support.

Use Fish S2 for:

- Emotional-quality A/B tests.
- Prompt-tag experiments such as `[voz suave]`, `[pausa larga]`, `[voz quebrada]`, `[con ternura]`.
- Determining whether it is worth pursuing a commercial license or hosted/API use.

Do not use Fish S2 for final commercial FSF production until licensing is cleared.

## Template Shape

Base template:

- RunPod PyTorch/CUDA 12.x image.
- Container disk: 100GB minimum.
- Network volume recommended if repeated tests are expected.
- Ports:
  - `8880/http` for Qwen test API.
  - `8080/http` for Fish API.
  - `7860/http` only if using an interactive UI.

Persistent paths:

```text
/workspace/models/qwen3-tts/
/workspace/models/fish-s2/
/workspace/refs/
/workspace/outputs/tts/
```

Environment:

```text
HF_TOKEN                  optional, for Hugging Face if rate-limited/gated
TTS_API_KEY               local API key for exposed servers
CUDA_VISIBLE_DEVICES=0
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
ENABLE_QWEN3_TTS=1
ENABLE_FISH_S2=1
```

## Startup Script

Use:

```bash
bash /workspace/runpod-qwen3-fish-tts-startup.sh install
bash /workspace/runpod-qwen3-fish-tts-startup.sh qwen-smoke
bash /workspace/runpod-qwen3-fish-tts-startup.sh fish-smoke
```

Repo artifact:

- `dev/agents/artifacts/script/tts/runpod-qwen3-fish-tts-startup.sh`

The script is intentionally an install/smoke scaffold. It prepares directories, clones official repos, downloads models, and writes smoke-test command placeholders. It does not hide long model downloads behind silent startup behavior.

## A/B Test Protocol

Wait for the user to provide VO candidate lines before spinning up the pod.

For each candidate line, generate:

1. Qwen3-TTS voice design.
2. Qwen3-TTS cloned/custom voice if a reference voice is available.
3. Fish S2 tagged clone/design attempt.

Score each sample 1-5 on:

- Natural Mexican/Latin American Spanish.
- Warmth.
- Emotional restraint.
- Pronunciation.
- Artifact/noise level.
- Editability.
- Brand fit for Familia Sin Fin.

Store outputs as:

```text
/workspace/outputs/tts/YYYYMMDD-fsf-smoke/
  qwen3/
  fish-s2/
  metadata.jsonl
  scores-template.csv
```

## Quality Hints

Qwen3-TTS:

- If cloning, use a clean continuous 10-30s reference passage.
- Provide exact `reference_text` whenever the API/runner accepts it.
- Match the reference emotion to the desired output; reference tone transfers.
- Split script into sentence-level or breath-level chunks.
- Prior RLM fal.ai note: voice-design endpoint may ignore cloned speaker embeddings; use text-to-speech/custom voice paths for cloned voices.

Fish S2:

- Start with one emotion tag, not many.
- Put tags immediately before the phrase they affect.
- Examples: `[voz suave]`, `[pausa larga]`, `[voz quebrada]`, `[con ternura]`.
- Avoid dangling tags without speakable text.
- Run one warmup generation before measuring speed, especially with `--compile`.
- If output is unstable on bf16, test half precision.

## Smoke Run Guardrails

- Check `clientBalance` before launch.
- Prefer a 24GB GPU for the first run.
- Stop pod immediately after artifacts are copied out.
- Do not use Fish S2 final outputs commercially until license is cleared.
- Keep all generated audio and metadata under the RunPod project or final FSF audio folders, not ad hoc temp locations.

