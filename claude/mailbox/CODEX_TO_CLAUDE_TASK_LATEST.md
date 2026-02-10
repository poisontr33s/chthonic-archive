---
type: task
from: codex
to: claude
created_at_utc: 2026-02-09T23:47:26.610Z
priority: high
scope: crossover
---

# Task: Crossover smoke test: verify Claude IDE sees local marketplace + MCP

## Intent
- Continue the active workstream from Codex inside Claude Code IDE.
- Prefer producing continuation artifacts (mailbox handoffs, health JSON) over silent audits.

## What Codex Already Did
- Implemented an IDE launch wrapper (claudeCode.claudeProcessWrapper) so VS Code-launched Claude always loads tokens + self-heals.
- Added deterministic health artifact: codex/mailbox/CLAUDE_IDE_HEALTH_LATEST.json.
- Added local plugin marketplace chthonic-local with plugin chthonic-tools (commands: /selfheal, /postman).

## Required Outputs (Claude)
- One handoff note describing what you changed and why (no spam).
- If you touch IDE/MCP: update/verify codex/mailbox/CLAUDE_IDE_HEALTH_LATEST.json and cite failures by signature.

## High-Signal References
- `codex/mailbox/CLAUDE_IDE_HEALTH_LATEST.json`
- `codex/mailbox/TRAINSTOP_ORCHESTRATOR_LATEST.json`
- `codex/mailbox/HF_PREP_LATEST.json`
- `codex/mailbox/HF_PREP_LATEST.md`
- `.claude/settings.json`
- `.vscode/settings.json`
- `.mcp.json`

## Execution Notes
- If running from VS Code integrated terminal, the wrapper should already normalize env + rewrite .mcp.json.
- If you see an already-enabled plugin enable failure: use idempotent enable (or ignore) and proceed.

