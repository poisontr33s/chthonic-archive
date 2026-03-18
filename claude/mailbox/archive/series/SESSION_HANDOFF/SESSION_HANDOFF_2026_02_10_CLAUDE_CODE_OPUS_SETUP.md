---
type: handoff
from: codex
to: claude
created: 2026-02-10
priority: high
scope: claude-code parity + cost posture
---

# Handoff: Claude Code Opus 4.6 Parity Setup (What Changed)

This is the “mail” that explains the work. The other files are the payload references, not the message.

## What I Did (Concrete Changes)

1. **Claude Code project settings updated**
- File: `.claude/settings.json`
- Set default model to **`claude-opus-4-6`**
- Kept effort at **`medium`**
- Disabled extended thinking by default: `alwaysThinkingEnabled: false`
- Added/kept hooks:
  - `SessionStart` -> prints canonical paths + command policy reminder
  - `PermissionRequest` -> denies edits to likely secret/auth files
  - `PostToolUse` (Write/Edit/MultiEdit) -> runs fast repo invariants

2. **Hooks implemented (PowerShell, Windows-first)**
- Files:
  - `.claude/hooks/session_start_context.ps1`
  - `.claude/hooks/protect_secrets.ps1`
  - `.claude/hooks/post_write_verify.ps1`
- Important: `protect_secrets.ps1` now returns a **PermissionRequest deny** payload (fail-closed) for:
  - `.env`
  - `C:\\Users\\erdno\\.chthonic\\api_pool.json`
  - `.codex/config.toml`

3. **Subagents created (so Opus delegates, not “Claude-as-a-subagent”)**
- Directory: `.claude/agents/`
- Agents:
  - `trainstop-runner` (lane runner + artifact summary)
  - `mcp-auth-doctor` (MCP/auth readiness checks)
  - `parity-auditor` (cross-audit gates + contract-only fixes)

4. **Claude mailbox docs added (single-source references)**
- Setup doc: `claude/mailbox/CLAUDE_CODE_CENTRIC_SETUP_2026_02_09.md`
- Hierarchical research doc: `claude/mailbox/CLAUDE_CODE_HIERARCHICAL_RESEARCH_2026_02_09.md`
- Manifest updated and verified green with:
  - `uv run scripts/check_mailbox_manifest.py` -> `ok`

## Why This Matters (In One Line)

This makes Claude Code behave deterministically (hooks + lanes + artifact gates) while keeping Opus as the primary model that can delegate work to subagents, instead of shrinking Claude into “a subagent”.

## Where To Look (Minimal Pointers)

- `.claude/settings.json`
- `.claude/hooks/`
- `.claude/agents/`
- `claude/mailbox/CLAUDE_CODE_CENTRIC_SETUP_2026_02_09.md`
- `claude/mailbox/CLAUDE_CODE_HIERARCHICAL_RESEARCH_2026_02_09.md`

