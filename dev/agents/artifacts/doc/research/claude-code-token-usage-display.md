# Claude Code Token Usage Display Configuration

**Research Date**: 2026-01-18
**Status**: Complete

---

## Summary

Claude Code does not have a built-in token usage display in the status line by default. However, token visibility can be enabled through OpenTelemetry configuration, CLI commands, and VS Code settings. Below are all documented methods for enabling token/cost display.

---

## 1. Environment Variables (Enable Token Tracking)

Add these to your shell profile (`~/.bashrc`, `~/.zshrc`, or `.env`):

```bash
# Core telemetry enable (REQUIRED for token tracking)
export CLAUDE_CODE_ENABLE_TELEMETRY=1

# Metrics export options
export OTEL_METRICS_EXPORTER=console    # Debug: output to terminal
export OTEL_METRICS_EXPORTER=otlp       # Production: send to OTLP endpoint

# Logs export
export OTEL_LOGS_EXPORTER=console       # or otlp

# Traces export
export OTEL_TRACES_EXPORTER=console     # or otlp

# Optional: OTLP endpoint configuration
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc

# Optional: Authentication for OTLP
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer your-token"
```

**Key Variable**: `CLAUDE_CODE_ENABLE_TELEMETRY=1` is critical for enabling any token/cost tracking.

---

## 2. CLI Commands and Slash Commands

These commands are available within Claude Code sessions:

| Command | Description |
|---------|-------------|
| `/cost` | Display current session token usage statistics and cost breakdown |
| `/context` | Show current token usage, available tokens, and category breakdown |
| `/compact` | Manually trigger context compaction to reduce token usage |

**External CLI Tools**:

```bash
ccusage  # Analyze historical usage data from local files
```

---

## 3. VS Code Extension Settings

For VS Code users, configure these settings:

```json
{
  "claudeCode.autoCompact.enabled": true,
  "claudeCode.autoCompact.threshold": 25
}
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `claudeCode.autoCompact.enabled` | boolean | `true` | Enable automatic context compaction |
| `claudeCode.autoCompact.threshold` | number | `25` | Percentage threshold for triggering compaction |

---

## 4. Claude Code Configuration Files

### CLAUDE.md
Project-level `CLAUDE.md` files can inject system reminders about token usage, but this is for instructions rather than display configuration.

### Local Configuration
- **Session files**: Claude Code stores session data in JSONL format at `~/.claude/sessions/`
- **Token tracking data**: Stored in `~/.claude/cache/ccr-token-state.json` (for CCR users)

---

## 5. Status Line Display

**Status**: Claude Code does not currently support a built-in token counter in the interactive status line.

**Workaround**: Use the `/cost` slash command to view token usage on-demand during sessions.

---

## 6. Official Documentation References

- **Claude Code Telemetry**: https://claude.com/docs/claude-code/configuration#telemetry-and-observability
- **CCR Token Counter Issue**: https://github.com/musistudio/claude-code-router/issues/1118

---

## 7. Quick Setup Checklist

1. Add environment variables to shell profile:
   ```bash
   export CLAUDE_CODE_ENABLE_TELEMETRY=1
   export OTEL_METRICS_EXPORTER=console  # or otlp
   ```

2. Reload shell: `source ~/.bashrc` (or restart terminal)

3. Use `/cost` command in Claude Code session to verify tracking

4. (Optional) Configure VS Code settings for auto-compaction

---

## 8. Troubleshooting

**Token counter shows zero despite usage**:
- Check if `CLAUDE_CODE_ENABLE_TELEMETRY=1` is set
- Ensure shell was reloaded after adding variables
- Try `OTEL_METRICS_EXPORTER=console` for debug output
- Monitor GitHub issue #1118 for SDK-specific fixes

---

## 9. Summary Table of Methods

| Method | Type | What It Does |
|--------|------|--------------|
| `CLAUDE_CODE_ENABLE_TELEMETRY=1` | Environment Variable | Enables telemetry export |
| `OTEL_METRICS_EXPORTER=console` | Environment Variable | Outputs metrics to terminal (debug) |
| `/cost` | Slash Command | View session token usage |
| `/context` | Slash Command | View token breakdown |
| VS Code settings | Configuration | Enable auto-compaction |

---

**Author**: Research compilation from Claude Code Router documentation and user configuration files
**Model**: gemini-2.5-flash-lite (local files analysis)
**Date**: 2026-01-18
