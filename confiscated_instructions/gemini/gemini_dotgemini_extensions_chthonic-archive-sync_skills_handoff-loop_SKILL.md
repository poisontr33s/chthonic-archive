---
name: handoff-loop
description: Unified handoff-loop orchestrator — validates, gates, routes, and tracks agent handoffs with receipt confirmation and obligation monitoring. Use when checking handoff status, validating before sending, routing with quality gates, or sweeping for stale/overdue items.
---

# Handoff Loop

Orchestration layer for the agent-to-agent mailbox pipeline. Adds validation, quality gating, receipt tracking, and stale-obligation detection on top of `mailbox-handoff`.

## Commands

```powershell
uv run scripts/handoff_loop.py status                          # pipeline health
uv run scripts/handoff_loop.py validate <file>                 # pre-send validation
uv run scripts/handoff_loop.py gate <file> --threshold 6.0     # score gate
uv run scripts/handoff_loop.py route <file> --to codex         # full pipeline
uv run scripts/handoff_loop.py ack <file> --reader gemini      # record receipt
uv run scripts/handoff_loop.py obligations                      # unACK'd handoffs
uv run scripts/handoff_loop.py sweep                           # stale alerts
uv run scripts/handoff_loop.py link-audit <file> --dry-run     # link check
```

## Workflow

1. Write handoff → `validate` → `link-audit --dry-run` → `route --to <target>`
2. After reading a handoff → `ack <file> --reader gemini`
3. Session start → `sweep`

## References

- Full spec: `.codex/skills/handoff-loop/SKILL.md`
- Script: `scripts/handoff_loop.py`
- `AGENT_COMMON.md`
- `.temple/protocols/MAILBOX_PROTOCOL.md`
