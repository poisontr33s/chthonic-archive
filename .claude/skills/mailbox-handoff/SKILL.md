---
name: mailbox-handoff
description: Manage Codex/Claude/Gemini mailboxes for handoffs, responses, verification, and routing. Use when checking inboxes, verifying handoff coverage across codex/.codex/claude/.claude/claude-codex-gemini, routing tasks, or running mailbox ops (postman/scribe/polisher).
metadata:
  short-description: "Triad mailbox operations with cross-root handoff verification."
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
- Gemini inbox: `gemini/mailbox/`
- Shadow mailboxes (sentinel-only): `.codex/mailbox/`, `.claude/mailbox/`
- Triad context root: `claude-codex-gemini/`

## Workflow (deterministic)
1. **Scan inbox (continuation-first)**
   - Read `mailbox_manifest.json` (if present).
   - Open the newest `SESSION_HANDOFF_*.md` (fallback: newest `*.md`).
   - For overnight/local-LLM handoffs, read `LOCAL_AI_READINESS_LATEST.md` first and treat it as the gate artifact.
2. **Extract intent**
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

- **One handoff note per change-set.** Update payload docs in place; don't emit duplicates.
- **Every claim must be verifiable** via a file path, command, or artifact.
- **No "checklist homework"** unless secrets/UI consent are required.
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

## Cross-Root Handoff Verification

Verify handoff presence across canonical + shadow + triad roots:

```powershell
uv run .codex/skills/mailbox-handoff/scripts/mailbox_check.py --mode verify
```

Machine-readable output + mailbox report:

```powershell
uv run .codex/skills/mailbox-handoff/scripts/mailbox_check.py --mode verify --json
uv run .codex/skills/mailbox-handoff/scripts/mailbox_check.py --mode verify --emit-report --report-target codex
```

## Mailbox Scribe

Regenerate a single, up-to-date session packet from current mailbox artifacts. Does not delete historical content.

```powershell
uv run scripts/mailbox_scribe.py --target codex --packet codex/mailbox/TETRAGRAMMATON_PACKET.md
uv run scripts/mailbox_scribe.py --target claude --packet claude/mailbox/TETRAGRAMMATON_PACKET.md
```

Optional send (route packet):

```powershell
.\scripts\mailbox_handoff.ps1 -Target claude -Source codex\mailbox\TETRAGRAMMATON_PACKET.md
```

## Integrated Ops (Postman + Scribe + Polisher)

`mailbox_check.py` orchestrates related mailbox tools directly so mailbox flow is one command surface.

Postman relay from inbox:

```powershell
uv run .codex/skills/mailbox-handoff/scripts/mailbox_check.py --mode verify --postman-target claude --postman-inbox codex/mailbox --send-latest
```

Postman relay from source file:

```powershell
uv run .codex/skills/mailbox-handoff/scripts/mailbox_check.py --postman-target claude --postman-source codex/mailbox/SESSION_HANDOFF_EXAMPLE.md
```

Run scribe and polisher from same command surface:

```powershell
uv run .codex/skills/mailbox-handoff/scripts/mailbox_check.py --scribe-target codex
uv run .codex/skills/mailbox-handoff/scripts/mailbox_check.py --polish-target codex
uv run .codex/skills/mailbox-handoff/scripts/mailbox_check.py --polish-target codex --polish-apply
```

## Link Canon Guard (via mailbox_check.py)

Duplicate filename disambiguation via the Codex-side `mailbox_check.py` engine:

```powershell
# Dry-run check (fails on findings)
uv run .codex/skills/mailbox-handoff/scripts/mailbox_check.py --mode link-canon --link-canon-file <file>

# Apply fixes in place
uv run .codex/skills/mailbox-handoff/scripts/mailbox_check.py --mode link-canon --link-canon-file <file> --link-canon-apply
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

## Link Audit (post-create guard)

After creating or editing a handoff, run link-audit to catch broken/ambiguous `[label](path)` references:

```bash
# Dry-run: show what's broken without writing
uv run scripts/handoff_loop.py link-audit <file> --dry-run

# Fix: rewrite fixable broken links in-place
uv run scripts/handoff_loop.py link-audit <file> --fix

# Standalone (same engine, more options)
uv run scripts/link_audit.py check <file> --dry-run
uv run scripts/link_audit.py check <file> --fix

# List all basename collisions in the repo
uv run scripts/link_audit.py collisions --filter .md
```

When creating handoff files, always run `link-audit --dry-run` before routing to catch path drift.

## Cross-Flavor Compatibility
- Codex flavor: requires `agents/openai.yaml` and `assets/` with SVG icons.
- Claude flavor: requires `SKILL.md` with valid frontmatter (`name`, `description`), optional `allowed-tools`.
- For shared audits use: `uv run scripts/skill_audit.py --flavor codex --root .codex/skills` and `uv run scripts/skill_audit.py --flavor claude --root .claude/skills`.
