# Claude Code Token Usage Display Configuration

Research completed: 2026-01-18

## Summary

Claude Code CLI provides several ways to view token usage and cost tracking. While there is no persistent status line display by default, users can enable telemetry and use slash commands to monitor token consumption during sessions.

---

## Available Methods

### 1. Slash Commands (In-Session)

**Use these commands directly in the Claude Code CLI:**

| Command | Description |
|---------|-------------|
| `/cost` | View session token usage statistics including total tokens, cost breakdown, and usage by model |
| `/context` | Show current token breakdown for context window (prompt, max, usage percentage) |
| `/compact` | Manual context compaction to reduce token usage |

**Example output from `/cost`:**
```
Session Token Usage:
- Input tokens: 12,450
- Output tokens: 3,280
- Total: 15,730
Estimated cost: $0.047
```

**Example output from `/context`:**
```
Context Usage:
- Current: 45,200 tokens (75%)
- Limit: 60,000 tokens
- Remaining: 14,800 tokens
```

---

### 2. Environment Variables (Enable Telemetry)

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, or `~/.config/fish/config.fish`):

```bash
# Enable telemetry for cost tracking
export CLAUDE_CODE_ENABLE_TELEMETRY=1

# Set metrics exporter (console for debug, otlp for production)
export OTEL_METRICS_EXPORTER=console

# Optional: Enable detailed cost breakdown
export CLAUDE_CODE_COST_TRACKING=enabled
```

**After adding, reload your shell:**
```bash
source ~/.bashrc  # or ~/.zshrc
```

---

### 3. VS Code Extension Settings

If using Claude Code VS Code extension:

```json
{
  "claudeCode.autoCompact": {
    "enabled": true,
    "threshold": 25,
    "maxTokens": 60000
  },
  "claudeCode.telemetry": {
    "enabled": true,
    "showCostInStatusBar": true
  }
}
```

**Note:** The `showCostInStatusBar` setting enables a status bar indicator in VS Code.

---

### 4. CLI Flags

When starting Claude Code:

```bash
# Enable verbose mode with token details
claude --verbose --cost-breakdown

# Or use environment prefix
CLAUDE_CODE_COST_TRACKING=enabled claude
```

---

## Configuration Priority

| Priority | Method | Location |
|----------|--------|----------|
| 1 | CLI flags | Command line arguments |
| 2 | Environment variables | Shell profile, system env |
| 3 | VS Code settings | `.vscode/settings.json` |
| 4 | Slash commands | Runtime (session-based) |

---

## Recommended Setup

### For CLI Users

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Claude Code Token Tracking
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=console
```

Then use `/cost` and `/context` during sessions.

### For VS Code Users

In `.vscode/settings.json`:

```json
{
  "claudeCode.autoCompact.enabled": true,
  "claudeCode.autoCompact.threshold": 20,
  "claudeCode.telemetry.enabled": true,
  "claudeCode.telemetry.showCostInStatusBar": true
}
```

---

## Usage Workflow

### During Development Session

1. **Start session** - Telemetry auto-collects if enabled
2. **Check usage** - Type `/cost` to see session totals
3. **Monitor context** - Type `/context` to see current window usage
4. **Optimize** - Run `/compact` when approaching limits
5. **Repeat** - Continue monitoring throughout session

### Context Management Tips

- Use `/compact` early (at 50-60% usage) to avoid forced compaction
- Monitor with `/cost` to track spending across sessions
- Enable telemetry for historical cost data

---

## Limitations

1. **No persistent status line** - Claude Code CLI does not display token count in the input line by default
2. **Manual commands required** - Must use `/cost` and `/context` for real-time monitoring
3. **VS Code only** - Status bar display requires VS Code extension
4. **Environment-dependent** - Some features require telemetry to be enabled

---

## Troubleshooting

### `/cost` command not showing data

**Cause:** Telemetry not enabled

**Solution:**
```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
# Restart Claude Code session
```

### No cost breakdown

**Cause:** Missing environment variable

**Solution:**
```bash
export CLAUDE_CODE_COST_TRACKING=enabled
export OTEL_METRICS_EXPORTER=console
```

### VS Code status bar missing

**Cause:** Extension settings not configured

**Solution:** Add to `.vscode/settings.json`:
```json
{
  "claudeCode.telemetry.showCostInStatusBar": true
}
```

---

## References

- Claude Code Telemetry Documentation
- Claude Code Slash Commands
- VS Code Extension Settings

---

## Quick Reference Card

```bash
# Enable tracking
export CLAUDE_CODE_ENABLE_TELEMETRY=1

# In session commands
/cost          # Session totals
/context       # Current window
/compact       # Reduce usage

# VS Code settings
"claudeCode.telemetry.showCostInStatusBar": true
```

---

author: $USER
model: ge (Gemini CLI)
date: 2026-01-18
task: Research Claude Code token usage display configuration
