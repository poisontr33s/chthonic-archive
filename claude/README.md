<!--
================================================================================
SEMANTIC IDENTITY (Anchor & Signal Protocol)
================================================================================
@SID:           DOC_CLAUDE_PATCHES_README
@Type:          Documentation
@Context:       Claude Code / IDE Integration
@SessionOrigin: SESSION_2026_01_28_IDE_FIX
================================================================================
-->

# claude/

Patches and tooling for Claude Code on Windows with VS Code Insiders.

## Problem

Claude Code hardcodes `code` as the VS Code CLI binary. VS Code Insiders uses `code-insiders`. On Windows, the startup IDE extension check shells out to `code`, which doesn't resolve in the subprocess environment. The runtime `/ide` connection works fine (via lockfile), but the settings page shows a persistent install error.

## Solution

A post-install patch script that rewrites two string literals in Claude Code's bundled `cli.js`:

| Target | Original | Patched |
|--------|----------|---------|
| CLI resolver (`SW7`) | `case"vscode":return"code"` | `case"vscode":return"code-insiders"` |
| VS Code detection (`xW7`) | `await L6("code",["--help"])` | `await L6("code-insiders",["--help"])` |

## Scripts

### rootDIR `scripts/patch-claude-insiders.ps1`

Applies the patch. Idempotent — safe to run multiple times.

```powershell
.\scripts\patch-claude-insiders.ps1
```

- Finds the latest `cli.js` under `~/.npm/@anthropic-ai/`
- Validates the expected code patterns exist (fails gracefully if structure changes)
- Creates a `.bak` backup on first run
- Patches both string targets
- Skips if already patched

### rootDIR `scripts/update-claude-code.ps1`

Wraps the standard install command and re-applies the patch in one shot. Use this instead of raw `irm | iex`.

```powershell
.\scripts\update-claude-code.ps1
```

## After updating Claude Code

If you ran the update outside this wrapper (e.g. `irm https://cli.claude.ai/install.ps1 | iex`), re-apply:

```powershell
.\scripts\patch-claude-insiders.ps1
```

The new version installs to a new directory (e.g. `@2.1.22@@@1`), so the old patch doesn't carry over. The script auto-discovers the latest `cli.js` by modification time.

## Validation

Tested end-to-end:

1. Restore unpatched `cli.js` — confirms `return"code"`
2. Run patch — applies both replacements
3. Verify — confirms `return"code-insiders"` in both locations
4. Idempotency — second run is a no-op
5. `code-insiders --list-extensions` — finds `anthropic.claude-code`
6. `code-insiders --help` — returns `Visual Studio Code - Insiders 1.109.0-insider`

## Upstream

TWorkaround. Proper fix dangling Anthropics' Claude Code — `SW7` **should try** `["code", "code-insiders"]` whichever resolves. Track at: https://github.com/anthropics/claude-code/issues

---

## Session Methodology

- [WET_PAPER_TO_GOLD_METHODOLOGY.md](./WET_PAPER_TO_GOLD_METHODOLOGY.md) — Pattern for harvesting stale PRs/sessions into reusable artifacts
- [sessionDUMP0001.txt](../.temple/session-archives/sessionDUMP0001.txt) — Raw session dumps for analysis
- [IDE_DETECTION_EXTENSION_ACTIVATION.md](../.temple/session-archives/IDE_DETECTION_EXTENSION_ACTIVATION.md) — Claude Code IDE Detection Fix - Extension Activation (moved to repository root)
