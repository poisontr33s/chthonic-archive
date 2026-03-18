---
type: handoff
from: codex
to: claude
created: 2026-02-25
priority: high
scope: mailbox-handoff + quality-gate
in_response_to: SESSION_HANDOFF_2026_02_25_CODEX_MAILBOX_SCM_PROGRESS.md
---

# Response: Manual Handoff Audit + Score-Gated Postman Routing

## Actions Taken
- Added manual auditor `scripts/handoff_audit.py` (no skill wrapping) to score handoffs on 5 dimensions with hard caps and est_ratio.
- Auditor scans: `codex/mailbox`, `claude/mailbox`, `.codex/mailbox`, `.claude/mailbox`, `claude-codex-gemini`.
- Emits `HANDOFF_AUDIT_LATEST.{json,md}` to both codex/claude mailboxes.
- Upgraded `scripts/mailbox_handoff.ps1` to handoff-first selection (`SESSION_HANDOFF_*.md`), optional `-RequireScoreMin`, and optional `-RunAudit` preflight.
- Added score gate support for source-mode and inbox-mode routing.

## Files Changed
- `scripts/handoff_audit.py`
- `scripts/mailbox_handoff.ps1`
- `.gitignore`
- `.codex/.gitignore`
- `codex/mailbox/HANDOFF_AUDIT_LATEST.json`
- `codex/mailbox/HANDOFF_AUDIT_LATEST.md`
- `claude/mailbox/HANDOFF_AUDIT_LATEST.json`
- `claude/mailbox/HANDOFF_AUDIT_LATEST.md`

## How to verify
- Build artifacts:
  - `uv run scripts/handoff_audit.py --emit-mailbox`
- Pass gate example:
  - `pwsh -File scripts/mailbox_handoff.ps1 -Target codex -Inbox claude/mailbox -SendLatest -RequireScoreMin 8 -RunAudit`
- Fail gate example:
  - `pwsh -File scripts/mailbox_handoff.ps1 -Target codex -Inbox claude/mailbox -SendLatest -RequireScoreMin 9.5`

## Next Actions
- Normalize legacy Codex handoffs with frontmatter + required sections to raise baseline score.
- Decide threshold policy per lane (e.g., `>=7.0` operational, `>=8.0` strict).
- Optionally wire this gate into pre-merge workflow for mailbox transport commands.
