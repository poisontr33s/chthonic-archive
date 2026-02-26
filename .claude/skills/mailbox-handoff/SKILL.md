---
name: mailbox-handoff
description: Route handoffs between Codex and Claude by reading and writing mailbox files. Use when checking inboxes, creating handoff reports, responding to mailbox items, or delegating tasks between codex/mailbox and claude/mailbox.
allowed-tools: "Read, Write, Glob, Grep"
user-invocable: true
---

# Mailbox Handoff (Claude Code)

Use this skill to read, write, and route handoff messages between Codex and Claude without copy-paste.
Arguments: `$ARGUMENTS` (mailbox path and optional filename).

## Protocol

This skill follows: `.temple/protocols/MAILBOX_PROTOCOL.md`

Core rule: **mailbox == continuation**, not file spam. Always start from the newest `SESSION_HANDOFF_*.md`.

## Mailbox locations
- Codex inbox: `codex/mailbox/`
- Claude inbox: `claude/mailbox/`

## Workflow (deterministic)
1. Scan inbox
   - Read `mailbox_manifest.json` (if present).
   - Open the newest `SESSION_HANDOFF_*.md` (fallback: newest `*.md`).
2. Extract intent
   - Identify requested action(s), required files, and any constraints.
3. Execute
   - Perform the work in the appropriate workspace path.
4. Respond
   - Write **one** response handoff note to the originating mailbox with:
     - Actions taken
     - Files changed
     - Tests run
     - Next actions

## Non-negotiables (quality)

- One handoff note per change-set.
- Every claim must be verifiable via a file path or artifact.
- Prefer `SESSION_HANDOFF_*.md` over chronicles/payload docs for continuation.

## Output template
```
---
type: handoff
from: claude
to: [codex]
created: YYYY-MM-DD
priority: inform
in_response_to: <hash or subject>
---

# Response: <subject>

## Actions Taken
- ...

## Files Changed
- ...

## Tests
- Not run (reason) / Command output summary

## Next Actions
- ...
```

## Command
Use the shared mailbox sender to route files:

```powershell
.\scripts\mailbox_handoff.ps1 -Target claude -Source path\to\handoff.md
.\scripts\mailbox_handoff.ps1 -Target codex -Source path\to\handoff.md
```

## Send Modes (Inbox)
Send latest or all messages from an inbox:

```powershell
.\scripts\mailbox_handoff.ps1 -Target claude -Inbox codex/mailbox -SendLatest
.\scripts\mailbox_handoff.ps1 -Target claude -Inbox codex/mailbox -SendAll
```

## Windows 11 Note (cmd.exe)
Avoid `cmd /c ren` style commands. On some systems this opens a “Choose an app” dialog instead of executing.
Use PowerShell-native commands (`Rename-Item`, `Remove-Item`, `Copy-Item`) or the provided scripts.

## Addendum: Fetch Claude Mailbox
When asked to fetch from Claude's mailbox, list and open files directly under `claude/mailbox/`.

Example:
```powershell
Get-ChildItem claude/mailbox -Filter *.md | Sort-Object LastWriteTime -Descending
Get-Content claude/mailbox/<file>.md
```

## Quick-Check Commands (absorbed from postman)

Check and continue from the newest handoff without manual subject lines:

```powershell
# Check Claude inbox (what Codex sent us)
uv run .codex/skills/mailbox-handoff/scripts/mailbox_check.py --mailbox claude

# Check Codex inbox (what Claude sent them)
uv run .codex/skills/mailbox-handoff/scripts/mailbox_check.py --mailbox codex

# Read Claude inbox + emit response skeleton → Codex
uv run .codex/skills/mailbox-handoff/scripts/mailbox_check.py --mailbox claude --emit-response --to codex

# Read Codex inbox + emit response skeleton → Claude
uv run .codex/skills/mailbox-handoff/scripts/mailbox_check.py --mailbox codex --emit-response --to claude
```

## Quality Gates (via handoff-loop)

Before routing, validate and gate:

```bash
# Validate structure before sending
uv run scripts/handoff_loop.py validate <file>

# Gate: validate + score; blocks if below 6.0
uv run scripts/handoff_loop.py gate <file>

# Full pipeline: validate → gate → route → log receipt
uv run scripts/handoff_loop.py route <file> --to codex

# Record receipt after reading a handoff
uv run scripts/handoff_loop.py ack <file> --reader claude

# Session-start sweep: stale + pending obligations
uv run scripts/handoff_loop.py sweep
```

## Cross-Flavor Compatibility
- Codex flavor: requires `agents/openai.yaml` and `assets/` with SVG icons.
- Claude flavor: requires `SKILL.md` with valid frontmatter (`name`, `description`), optional `allowed-tools`.
- For shared audits use: `uv run scripts/skill_audit.py --flavor codex --root .codex/skills` and `uv run scripts/skill_audit.py --flavor claude --root .claude/skills`.


