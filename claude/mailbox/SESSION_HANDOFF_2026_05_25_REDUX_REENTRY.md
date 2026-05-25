---
type: session-handoff
status: active
created: 2026-05-25
session_window: 2026-05-24/25 (regression session, REDUX-housekept)
topic: re-entry after sleep break + VS Code Insiders update
authored: claude (Lysandra)
---

# SESSION HANDOFF 2026-05-25 — REDUX RE-ENTRY

## What I did (since conductor went to sleep, by their explicit directive)

- Authored chronological REDUX retrospective at [.temple/protocols/SESSION_2026_05_24_25_REDUX.md](../../.temple/protocols/SESSION_2026_05_24_25_REDUX.md) — F1-F13 failure inventory, Tier 0-5 hierarchy of learnings, 8 methodology shifts as imperatives, phase-ordered priority for "if this session started again." Frontmatter SID `GOVERNANCE_REDUX_SESSION_2026_05_24_25_V1`.
- New memory keystone `feedback_false_positive_avoidance.md` (in `~/.claude/projects/c--Users-eldno-chthonic-archive/memory/`) — the discipline that emerged from the conductor's ~75% false-positive diagnosis. Indexed in MEMORY.md.
- Extended `reference_ci_autofix_gate.md` (same memory dir) with V1.6 and V1.7 sections so the full V1→V1.7 sequence is one document.
- Registered REDUX in [CLAUDE.md](../../CLAUDE.md) under new `## Session Retrospectives` section.
- Verifier V1.8 ([scripts/verify-rescue-shim.ts](../../scripts/verify-rescue-shim.ts)) — V1.7's `--live` had a verifier-self false-positive (sandbox tests populated the log before --live read it). V1.8 makes `--reset-log`, `--live`, and default mode mutually exclusive. Filters log entries against VS Code's `-c user.useConfigOnly=true` invocation signature.
- VS Code recovery utility [scripts/relaunch-vscode-insiders.ps1](../../scripts/relaunch-vscode-insiders.ps1) — addresses the auto-update-strips-GPU-flags issue.

Last commit: [run `git log -1 --format='%H %s'` for current SHA — DO NOT cite a remembered SHA per [[feedback-verify-diff-matches-message]]].

## How to verify (post-VS-Code-Insiders-update)

### Step 1 — Survive the update

If VS Code auto-restarted without GPU flags (flicker, instability), recover via the relaunch utility:

```powershell
# From an EXTERNAL PowerShell (NOT VS Code's integrated terminal — the script self-protects against that):
pwsh -File C:\Users\eldno\chthonic-archive\scripts\relaunch-vscode-insiders.ps1
```

This closes Code - Insiders (graceful first, force after 5s) and relaunches via `C:\Users\eldno\OneDrive\Desktop\Chthonic Archive Workspace.lnk` which carries the canonical flag set.

### Step 2 — Verify shim wiring is live

```powershell
# 1. Clean baseline (truncates the verifier-self entries from the wakeup session):
bun run scripts/verify-rescue-shim.ts --reset-log

# 2. Do any git op in VS Code (commit click, source-control panel refresh)

# 3. Log-only check:
bun run scripts/verify-rescue-shim.ts --live
```

PASS with entries matching `-c user.useConfigOnly=true` → VS Code IS routing through the shim. FAIL with "log is empty" → it isn't (settings.json git.path didn't take effect; check `.vscode/settings.json` line 41 references `${workspaceFolder}\\scripts\\git-chthonic.cmd`).

### Step 3 — Sandbox tests (confirm V1.7 + V1.8 mechanism still clean post-update)

```powershell
bun run scripts/verify-rescue-shim.ts
```

Expect: `✓ ALL 10 assertions passed.`

## What's next (optional, conductor's call)

- **`update.mode: "manual"` in VS Code user settings** — prevents the auto-restart-without-flags problem at the source. VS Code will notify of updates but never install/restart on its own. The conductor decides when to update, always via the desktop shortcut path. **Not yet applied** — requires conductor's authorization to modify VS Code user settings.
- **`argv.json` GPU flag persistence** — `%APPDATA%\Code - Insiders\argv.json` supports a subset of Chromium flags (`ignore-gpu-blocklist`, `enable-features`, etc.) that persist across any launch path including auto-update. Wouldn't cover all 6 flags but would cover the most impactful ones. **Not yet applied** — requires conductor's authorization.
- GitHub Pull Requests extension update is orthogonal to the gate work; no expected interaction.

## Blockers

- None for the technical work. The conductor's authorization is the only gate on the two "What's next" items above.

## Cross-references

- REDUX retrospective: [.temple/protocols/SESSION_2026_05_24_25_REDUX.md](../../.temple/protocols/SESSION_2026_05_24_25_REDUX.md)
- Memory keystone: `feedback_false_positive_avoidance.md` in [~/.claude/projects/c--Users-eldno-chthonic-archive/memory/](file:///C:/Users/eldno/.claude/projects/c--Users-eldno-chthonic-archive/memory/)
- Gate architecture: `reference_ci_autofix_gate.md` (same memory dir)
- Mailbox protocol governing this handoff: [.temple/protocols/MAILBOX_PROTOCOL.md](../../.temple/protocols/MAILBOX_PROTOCOL.md)
- Reconciliation Engine: [.temple/protocols/THE_RECONCILIATION_ENGINE.md](../../.temple/protocols/THE_RECONCILIATION_ENGINE.md)

## verify_with: (per Reconciliation Engine §III)

```yaml
claim:        Shim wiring is correct in workspace settings; VS Code routing through it is verifiable but not yet confirmed live post-update
lane:         .vscode/settings.json git.path key + .git/chthonic-rescue-shim.log invocation trail
verify_with:  bun run scripts/verify-rescue-shim.ts --reset-log; <do git op in VS Code>; bun run scripts/verify-rescue-shim.ts --live
```

```yaml
claim:        GPU flicker after auto-update is recoverable via the relaunch utility without state loss
lane:         scripts/relaunch-vscode-insiders.ps1 + desktop shortcut at C:\Users\eldno\OneDrive\Desktop\Chthonic Archive Workspace.lnk
verify_with:  pwsh -File scripts/relaunch-vscode-insiders.ps1 -DryRun   (from external PowerShell — shows what would close/launch without doing it)
```
