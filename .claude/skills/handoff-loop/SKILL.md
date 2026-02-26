---
name: handoff-loop
description: Unified handoff-loop orchestrator — validates, gates, routes, and tracks agent handoffs with receipt confirmation and obligation monitoring. Use when checking handoff status, validating before sending, routing with quality gates, or sweeping for stale/overdue items.
allowed-tools: "Read, Write, Glob, Grep, Bash"
user-invocable: true
---

# Handoff Loop (Claude Code)

Orchestration layer that closes manual gaps in the agent-to-agent mailbox pipeline.
Connects: `handoff_audit.py`, `mailbox_check.py`, `mailbox_manifest.py` into a self-healing loop.

## What It Adds Over mailbox-handoff

| Gap | mailbox-handoff | handoff-loop |
|-----|----------------|--------------|
| Pre-write validation | ❌ None | ✅ `validate` catches bad structure before routing |
| Quality gate | ❌ Advisory scoring only | ✅ `gate` blocks handoffs below threshold (default 6.0) |
| Receipt tracking | ❌ No delivery confirmation | ✅ `ack` records who read what, when |
| Obligation monitor | ❌ No stale detection | ✅ `obligations` / `sweep` flags overdue handoffs |

## Commands

```bash
# Check pipeline health
uv run scripts/handoff_loop.py status

# Validate a handoff before sending
uv run scripts/handoff_loop.py validate <file>

# Gate: validate + score; blocks if below threshold
uv run scripts/handoff_loop.py gate <file> --threshold 6.0

# Record receipt (reader acknowledges a handoff)
uv run scripts/handoff_loop.py ack <file> --reader claude

# List all unACK'd handoffs sorted by age
uv run scripts/handoff_loop.py obligations

# Full pipeline: validate → gate → route → log receipt
uv run scripts/handoff_loop.py route <file> --to codex

# Full sweep: obligations + stale alerts
uv run scripts/handoff_loop.py sweep
```

## Workflow Integration

### Before Sending a Handoff
1. Write `SESSION_HANDOFF_*.md` with required frontmatter + sections
2. `uv run scripts/handoff_loop.py validate <file>` — fix any errors
3. `uv run scripts/handoff_loop.py route <file> --to <target>` — gates + routes + logs

### After Reading a Handoff
1. `uv run scripts/handoff_loop.py ack <file> --reader claude` — record receipt

### Session Start / Periodic Check
1. `uv run scripts/handoff_loop.py sweep` — shows all stale + pending obligations

## Data Files

| File | Location | Purpose |
|------|----------|---------|
| Receipt log | `claude-codex-gemini/HANDOFF_RECEIPT_LOG.json` | Who read what, when |
| Mailbox manifest | `claude-codex-gemini/MAILBOX_MANIFEST.json` | Full inventory of all mailbox files |

Both are git-tracked lightweight JSON files. The actual mailbox files remain untracked.

## Quality Gate Thresholds

- Default: 6.0 (handoff_audit composite score)
- Override: `--threshold <float>` on `gate` and `route` commands

## Required Frontmatter Fields
`type`, `from`, `to`, `created`, `priority`, `scope`

## Required Sections
`Actions Taken`, `Files Changed`, `How to Verify`, `Next Actions`
