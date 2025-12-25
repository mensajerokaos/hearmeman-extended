# Project Agent Instructions - Task Logging & Agent Delegation

Use this file to track agent work and delegate tasks to specialized agents for efficiency.

---

## Task Logging System

Use this system to track work across sessions:

### Task States
- `[ ]` - Pending (not started)
- `[x]` - Completed (finished successfully)
- `[!]` - Errored (encountered blocker)
- `[>]` - In Progress (currently working on)

### Task Log Format

```markdown
## YYYY-MM-DD Session N

**Start**: YYYY-MM-DD HH:MM:SS CST (CDMX)

**Tasks**:
- [x] Task 1 - Brief description
- [ ] Task 2 - Brief description
  - Sub-task 2a (if applicable)
  - Sub-task 2b (if applicable)
- [!] Task 3 - Brief description
  - Error: Specific blocker or issue
  - Next step: What to do to unblock
- [>] Task 4 - Brief description
  - Currently on: Specific subtask being worked

**Status**: In Progress / Completed

**End**: YYYY-MM-DD HH:MM:SS CST (CDMX)
**Duration**: X hours Y minutes

---
```

### Task Logging Rules

1. **Mark status IMMEDIATELY** as you start/complete each task
2. **One task in Progress at a time** - focus principle
3. **Reference file paths** - add full paths for traceability
4. **Note errors clearly** - document blockers with next steps
5. **Calculate duration** - end timestamp - start timestamp

---

## Orchestrator Mode & Agent Delegation

**Role**: You are an orchestrator. Delegate tasks to agents whenever possible.

### Profile Selection

**ALWAYS check `~/.codex/config.toml` for current profiles before delegating.**

```bash
cat ~/.codex/config.toml | grep -A 5 "profiles"
```

### Available Codex Profiles

**Most Powerful (Codex-Max)**:
- `codex-max-xhigh` - Critical architecture/complex algorithms
- `codex-max-high` - Complex code generation
- `codex-max-medium` - Standard tasks
- `codex-max-low` - Simple/fast tasks

**Standard Codex**:
- `gpt5-codex-high`, `gpt5-codex-medium`, `gpt5-codex-low`
- `gpt5-codex-mini-high` - Lightweight tasks

**Multimodal (Non-Code)**:
- `gpt5-high`, `gpt5-medium`, `gpt5-low`, `gpt5-full`

### Delegation Workflow

```bash
# Single task delegation
# IMPORTANT: Always instruct agent to write output to a file to avoid token bloat
codex exec --skip-git-repo-check --full-auto -p codex-max-high \
  "Task description here. Write your output to artifacts/task-result.md"

# Parallel delegation (independent tasks)
codex exec --skip-git-repo-check --full-auto -p codex-max-high \
  "Task 1. Write output to artifacts/task1-result.md" &
codex exec --skip-git-repo-check --full-auto -p codex-max-medium \
  "Task 2. Write output to artifacts/task2-result.md" &
wait

# Then read results from files (keeps orchestrator context clean)
cat artifacts/task1-result.md
```

**Why write to files?** Codex stdout goes directly into the orchestrator's context window. Large outputs can bloat tokens and degrade performance. Writing to `.md` files keeps the orchestrator lean.

### Delegation Checklist

1. ✓ Check `~/.codex/config.toml` for available profiles
2. ✓ Identify independent tasks that can run in parallel
3. ✓ Select appropriate profile (prefer `codex-max-*` for complex work)
4. ✓ Execute with `--skip-git-repo-check --full-auto`
5. ✓ Verify results - ALWAYS run a self-test
6. ✓ Iterate if issues found

### When to Use Each Agent Type

| Task | Profile | When |
|------|---------|------|
| Architecture/Complex logic | `codex-max-xhigh` | Critical decisions, complex algorithms |
| Code generation | `codex-max-high` | Implementing features, refactoring |
| Straightforward coding | `codex-max-medium` | Standard development tasks |
| Simple tasks | `codex-max-low` | Formatting, simple edits, linting |
| Non-code work | `gpt5-*` | Screenshots, multimodal, reasoning |

---

## Session Time Limits

- **4.0 hours**: First reminder to wrap up
- **4.25 hours**: Final 15-minute warning
- **4.5 hours**: Hard stop - close session, log results

---

## Documentation Sync

**IMPORTANT**: Keep task logging consistent across all project documents.

- **PROJECT_TEMPLATE_CLAUDE.md**: Quick reference (paired with this file)
- **PROJECT_TEMPLATE_AGENTS.md**: This file - full workflows
- **PROJECT_TEMPLATE_CHANGELOG.md**: Active session logs

For active projects, update:
- **CLAUDE.md**: First-load context for new Claude Code sessions
- **AGENTS.md**: Canonical reference for orchestrator and agent workflows
- **CHANGELOG.md**: Session tracking and development history
