---
name: oz-workflow
description: Oz's successful workflow methodology - planning, execution, and communication patterns
author: oz + MiniMax M2.1
version: 1.0
---

# Oz Workflow Skill

Use this skill to replicate the successful workflow that achieved:
- **50/50 PRD scores** (perfect)
- **100% test pass rates**
- **Successful multi-wave implementations**

## Quick Reference

### Planning → Execution Flow
```
TodoWrite → plan00 (draft) → plan04 (perfect) → /implement → /deploy
```

### Key Commands
```bash
# Create todos
TodoWrite({todos: [{content: "Task", status: "in_progress"}]})

# Plan (40-45/50)
/plan00 {task description}

# Refine (50/50)
/plan04 --from {prd}

# Execute
/implement --from {prd}

/implement --wave 2 &
/implement --wave 3 &

# Deploy
/implement --from {run} --to {target}
```

### Communication Style
- Status blocks with emojis
- Return under 50 tokens
- Quick metrics tables

## Documentation

Full guide: `.claude/skills/oz-workflow.md`

## Usage

When starting a complex task:
1. Use TodoWrite to track progress
2. Use plan00/plan04 for planning
3. Use /implement for execution
4. Use beads for task dependencies
5. Use cron for monitoring

See `.claude/skills/oz-workflow.md` for complete details.
