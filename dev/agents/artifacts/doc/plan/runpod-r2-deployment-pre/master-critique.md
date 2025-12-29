# Master Plan Self-Critique

## Clarity Score: 6/10

### Issues Identified

#### 1. Missing Specific File Paths
- Phase 1: Says "CREATE: docker/upload_to_r2.py" but doesn't specify full path
- Need: `/home/oz/projects/2025/oz/12/runpod/docker/upload_to_r2.py`

#### 2. Vague Task Descriptions
- "Verify WAN 2.2 download paths are correct" - HOW to verify?
- "Test model download on fresh container" - WHAT command to run?
- "Configure GHCR authentication" - WHAT exact steps?

#### 3. Missing BEFORE/AFTER Code Blocks
- Phase 1 modifies Dockerfile but doesn't show exact changes
- Phase 1 modifies start.sh but doesn't show insertion point
- No concrete code provided for any task

#### 4. Banned Words Present
- "can run in parallel" - vague, need specific dependency list
- "ensure" - what specific check?
- "verify" without command

#### 5. Missing Acceptance Criteria
- Phase 1: What proves R2 sync works?
- Phase 3: What proves GHCR push succeeded?
- No testable criteria for any phase

#### 6. Missing Environment Variable Values
- R2_ENDPOINT value provided but not R2_ACCESS_KEY/R2_SECRET_KEY handling
- No mention of how secrets are passed to RunPod

#### 7. Missing Effort Estimates
- No hour estimates for any phase
- No total project estimate

#### 8. Incomplete Parallel Execution Map
- ASCII diagram is too simple
- Doesn't show which STEPS within phases can run in parallel
- No terminal assignment

#### 9. Missing Rollback Plans
- If R2 sync fails, what happens?
- If GHCR push fails, what happens?
- No recovery procedures

#### 10. Missing Prerequisites
- What tools need to be installed locally?
- What credentials need to be configured?
- What existing files need to exist?

---

## Required Improvements for Pass 3

1. **Full absolute paths** for all files
2. **Exact code snippets** with BEFORE/AFTER for every modification
3. **VERIFY commands** for every step (runnable bash)
4. **Testable acceptance criteria** with expected outputs
5. **Hour estimates** per phase
6. **Rollback commands** per phase
7. **Prerequisites checklist** at document start
8. **Terminal execution matrix** with specific commands

---

## Specific Fixes Needed

### Phase 1 Missing Details:
```
FILE: /home/oz/projects/2025/oz/12/runpod/docker/Dockerfile
LINE: 44 (add after existing apt-get packages)
BEFORE: libgl1-mesa-glx \
AFTER: libgl1-mesa-glx \
    inotify-tools \

VERIFY: docker build --target layer1 -t test . && docker run test inotifywait --version
```

### Phase 2 Missing Details:
- TurboDiffusion model URL not specified
- No environment variable for enabling TurboDiffusion

### Phase 3 Missing Details:
- GitHub repository name not specified
- GHCR image name pattern not defined
- No PAT token setup instructions

### Phase 4 Missing Details:
- RunPod template ID not generated
- Volume size recommendation missing
- GPU type recommendation missing

---

*Critique complete - Pass 3 must address ALL items above*
