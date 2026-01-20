# Oz Workflow Methodology

## Overview

This guide documents the workflow that achieved **50/50 PRD scores** and **100% test pass rates** for the media-analysis-api and prompt-routing implementations.

## Core Principles

### 1. Task Tracking with TodoWrite
```javascript
TodoWrite({
  todos: [
    {content: "Task name", status: "in_progress", activeForm: "Doing task"},
    {content: "Task name", status: "pending", activeForm: "Waiting for X"},
    {content: "Task name", status: "completed", activeForm: "Completed task"}
  ]
})
```

**Rules:**
- Update todo at start of each major phase
- Mark completed when fully done
- Keep activeForm descriptive (e.g., "Running plan04 perfection")

### 2. Planning Phase (plan00 → plan04)

**plan00 (Draft PRD):**
- Use for initial planning
- Target: 40-45/50 score
- Focus: Architecture, phases, basic details

**plan04 (Refine PRD):**
- Use for perfection
- Target: 49-50/50 score
- Add: FILE:LINE targets, BEFORE/AFTER patterns, curl commands, risk scripts

**UltraThink Mode:**
```
Think deeply and thoroughly. Use extended reasoning to explore all angles before responding.
```

### 3. Execution Phase (/implement)

**Mode Selection:**
- `/implement --from {prd}` → FIRST mode (expand + Wave 1)
- `/implement --wave {N}` → SUBSEQUENT mode (specific wave)
- `/implement --from {run} --to {target}` → DEPLOY mode

**Execution Flow:**
```
1. Validate PRD
2. Backup
3. Expand waves
4. Execute wave (SSH to devmaster)
5. Audit files
6. Ask for restart (if needed)
```

### 4. Bead System

**Bead Structure:**
```json
{
  "id": "runpod-xxx",
  "title": "Brief description",
  "description": "Detailed description",
  "status": "pending|in_progress|completed",
  "priority": 1|2|3,
  "dependencies": [{"issue_id": "...", "type": "blocks|requires"}]
}
```

**Dependency Types:**
- `blocks`: This bead blocks the dependent
- `requires`: This bead requires the dependency first

### 5. Monitoring (Cron)

**Persistent Wakeup Script:**
```bash
# /tmp/periodic_wakeup.sh
*/15 * * * * /tmp/periodic_wakeup.sh >> /tmp/periodic_wakeup.log 2>&1
```

**Key Features:**
- Runs every 15 minutes indefinitely
- Logs status to file
- No polling - passive observation

## Communication Style

### Status Blocks
```markdown
**Component** | **Status** | **Details**
--------------|------------|-----------
 PRD Score | ✅ 50/50 | Perfect
 Tests | 🔄 Running | 24/24 passed
```

### Return Format (Under 50 tokens)
```
✅ implement-{name} | Wave 1 complete | X files → {path}
```

### Quick Status Check
```bash
tail -3 {activity_file}
```

## Report Structure

### PRD Structure
1. Executive Summary
2. Architecture Overview (ASCII diagrams)
3. Implementation Phases
4. FILE:LINE Targets
5. BEFORE/AFTER Patterns
6. curl Verification Commands
7. Risk Assessment
8. Beads with Dependencies

### Implementation Report
1. Summary Metrics
2. Files Created
3. Test Results
4. Issues Found
5. Next Steps

## Styling Conventions

### ASCII Diagrams
```
┌─────────────────────────────────────────┐
│           Component Name                │
│  ┌───────────┐  ┌───────────────┐      │
│  │ Sub-comp  │  │  Sub-comp 2   │      │
│  └───────────┘  └───────────────┘      │
└─────────────────────────────────────────┘
```

### Tables
```
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
```

### Code Blocks
```python
# BEFORE
old_code()

# AFTER
new_code()
```

## Directory Structure

```
.claude/
├── skills/
│   ├── oz-workflow.md          ← This guide
│   ├── af-vps.md               ← VPS connection
│   └── ...
├── transformers/
│   ├── master-system-prompt.js
│   └── ...
├── code/
│   └── ...
└── ...

.beads/
├── issues-media-analysis.jsonl  ← Task tracking
└── ...

dev/
├── agents/
│   └── artifacts/
│       ├── doc/
│       │   ├── plan/           ← PRDs
│       │   ├── implement-runs/  ← Execution
│       │   └── audit/          ← Audits
│       └── ...
└── ...

opt/services/
└── media-analysis/             ← Target service
    ├── api/
    ├── docker/
    └── scripts/
```

## Key Files

| File | Purpose |
|------|---------|
| `.beads/issues-*.jsonl` | Task tracking with dependencies |
| `dev/agents/artifacts/doc/plan/{name}.md` | PRDs |
| `dev/agents/artifacts/doc/implement-runs/{timestamp}/` | Execution outputs |
| `dev/agents/artifacts/doc/audit/{name}.md` | Quality audits |
| `/tmp/monitor_*.log` | Background monitoring logs |

## Quality Targets

| Document | Target Score | Minimum |
|----------|-------------|---------|
| PRDs | 50/50 | 45/50 |
| Tests | 100% pass | 90% pass |
| Coverage | N/A | All files tested |

## Workflow Sequence

```
1. Create Beads (TodoWrite)
   ↓
2. plan00 (Draft PRD, 40-45/50)
   ↓
3. plan04 (Refine PRD, 50/50)
   ↓
4. /implement --from {prd} (FIRST mode)
   ↓
5. /implement --wave 2 &
   /implement --wave 3 &
   ↓
6. /implement --from {run} --to {target} (DEPLOY)
   ↓
7. Verify + Report
```

## Best Practices

1. **Never poll** - Use background agents with run_in_background=true
2. **Always backup** - Before any modification
3. **Audit each file** - After deployment, before restart
4. **Ask for authorization** - Before container restarts
5. **Use cron for monitoring** - Passive wakeups, not active polling
6. **Keep todos updated** - Clear status visibility
7. **Short returns** - Under 50 tokens for status blocks

## Troubleshooting

### PRD Score Too Low
→ Run plan04 again with UltraThink mode

### Tests Failing
→ Fix in /implement, redeploy, re-test

### Agent Hanging
→ Check activity.log for last operation
→ Check cron wakeup logs

## References

- BRV context: `brv query {topic}`
- VPS access: `.claude/skills/af-vps.md`
- This guide: `.claude/skills/oz-workflow.md`

---

**Author**: oz + MiniMax M2.1

> "I am MiniMax M2.1 - and that is extraordinary."
**Version**: 1.0
**Date**: 2026-01-19
