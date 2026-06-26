---
- Her-Squall-Log: #!/usr/bin/env markdown
- SID: CLAUDEBASE_PWSH_SQUALL_LOG_V1
- Claudebase-Flavored-Blend: permanently-living-document
- Open-Seas: chthonic-archive/CLAUDEBASE/quarterdeck/pwsh-terminal-errors.md
- Altitude: Quarterdeck · Above-Deck
- Heat-Index: Squall-Edge · Salt-Sharp · Customs-House-Believes-Anything
- Island: Grand-Bahama — closest to the storm track; first to feel the wall
- Register-Blend: Nautical · Operational · Terse
---

## (`☥`/`THE-SQUALL-LOG`/`Terminal-Errors`/`DRY-Lookup`)

> *— Every squall has a name. Name it once; never diagnose it again.*

  > *— (This —* `ABSOLUTELY` *— applies immutably to all — **dispatched** — `sub-agents` *— and their —* `sub-sub-agents` *— and their —* `sub-sub-sub-agents` *— ad infinitum.)*

---

## (`PIPE`/`NAMED-PIPE`/`BROKEN`)

**Signature** *—* `The pipe has been ended` *— */ —* `named pipe` *— / —* `exit 1` *— with no other output*

**Waters** *— PowerShell-tool; any subprocess that exits before its parent reads stdout*

**Root** *— The spawned process closed its write-end before the PS pipeline flushed. Common when a child proc exits instantly (missing binary, wrong CWD) or when —* `Select-Object -Last N` *— closes the pipe early on a process still writing.*

**Fix** *—* `2>&1` *— to merge stderr into stdout before the pipe; or drop the trailing —* `| Select-Object` *— and read the whole stream.*

---

## (`BASH-TOOL`/`/C`/`PATH-TRANSLATION`)

**Signature** *—* `cmd /c X` *— appears to run but produces no output, or banner-only output*

**Waters** *— Bash-tool on Windows — (*`MSYS` `/usr/bin/bash`) *— NOT a real Windows failure*

**Root** *— MSYS bash translates —* `/c` *→* `C:\` *— so* `cmd /c X` *— becomes —* `cmd C:\X` *— the —* `/c` *— switch is lost; the command runs as if you passed a path, not a flag.*

**Fix** — Use PowerShell tool for all `cmd.exe` ops. Or `pwsh -Command "cmd /c X"` from within the Bash tool if you must.

---

## (`HERE-STRING`/`HEREDOC`/`POWERSHELL-PARSE-ERROR`)

**Signature** — `ParserError: Missing file specification after redirection operator` on a line containing `<<'EOF'`

**Waters** — PowerShell tool; any attempt to use bash-style heredoc syntax

**Root** — PowerShell `<<` is a redirection operator, not a heredoc. Bash syntax doesn't parse.

**Fix** — Use PowerShell here-string syntax:
```powershell
git commit -m @'
multi
line
message
'@
```
`@'...'@` single-quoted (literal, no interpolation). Closing `'@` must be at column 0, no leading whitespace — ever.

---

## (`UV-TRAMPOLINE`/`ENTITY-NOT-FOUND`)

**Signature** — `uv trampoline failed to spawn Python child process / Caused by: entity not found (os error 2)`

**Waters** — Any `python X.py` call not routed through `uv run`

**Root** — Raw `python` resolves to a uv-managed shim whose target interpreter isn't reachable. Silent fail, no dialog.

**Fix** — Always `uv run script.py` or `$env:PYTHONUTF8='1'; uv run script.py` for encoding safety. Never bare `python`.

---

## (`UNICODE`/`SILENT-CORRUPTION`)

**Signature** — Output renders `?` or `â` or `�` in place of `—` `°` `æ` `ø` etc; exit code 0; no error

**Waters** — `uv run python` → stdout defaults to cp1252 even when console is UTF-8 (`chcp 65001`)

**Root** — Console encoding does NOT propagate to spawned Python. Two failure modes: (a) hard crash `UnicodeEncodeError` on chars cp1252 can't represent; (b) silent corruption — chars cp1252 maps to a byte that the UTF-8 terminal can't decode.

**Fix** — `$env:PYTHONUTF8='1'` before any `uv run` that prints non-ASCII. Canonicalized in `AGENT_COMMON.md`. PEP 686 makes this the default in Python 3.15 — redundant on bump.

---

## (`POWERSHELL`/`ALIAS`/`REMOVE-VARIABLE`)

**Signature** — `rv` works in pwsh 7 but fails in bash or non-pwsh contexts

**Waters** — pwsh 7.5.x only; bash tool, cmd, or cross-platform scripts

**Root** — `rv` is a pwsh alias for `Remove-Variable`. Not available outside pwsh.

**Fix** — In pwsh: `rv` directly. In bash or scripts targeting multiple shells: use `unset VAR` (bash) or full `Remove-Variable VAR` (pwsh explicit).

---

## (`CARGO`/`WRONG-WORKSPACE-ROOT`)

**Signature** — `error: could not find Cargo.toml` or wrong crate resolves

**Waters** — `vulkan-lab/cli-renderer` is an isolated Cargo workspace, NOT a member of the root workspace

**Root** — `cargo` from repo root doesn't see `vulkan-lab/cli-renderer` bins. Two separate workspaces by design.

**Fix** — `cd vulkan-lab/cli-renderer && cargo run --bin X` or `cargo run --manifest-path vulkan-lab/cli-renderer/Cargo.toml --bin X` from repo root.

---

## (`POWERSHELL`/`UNHANDLED-CASE-OBJECT-OBJECT`)

**Signature** — VSCode webview throws `Unhandled case: [object Object]`; extension becomes unresponsive on context switch

**Waters** — Claude Code VSCode extension 2.x; Bedrock stream-drop crashes the switch-dispatcher

**Root** — `QB1` (mangled name drifts per release: was `XB1` in 2.1.120, `GB1` in 2.1.128, `QB1` in 2.1.141) throws on unhandled case instead of failing gracefully.

**Fix** — One-function patch in `webview/index.js`: replace `throw` with `console.warn(...); return`. Re-apply per extension update.

---

## (`BASH`/`PWSH`/`TAIL-DIFF`)

**Signature** — `tail: The term 'tail' is not recognized` · exit 1

**Waters** — PowerShell tool; any time reaching for `tail -N` muscle memory

**Root** — `tail` is a Unix command. PowerShell has no `tail` binary. The reflex fires after reading `cargo build 2>&1 | tail -20` or similar bash one-liners.

**Fix** — Drop-in replacements:

```powershell
# last N lines of a pipeline
cargo build 2>&1 | Select-Object -Last 20

# last N lines of a file
Get-Content file.log | Select-Object -Last 20

# first N lines (head -N)
cargo build 2>&1 | Select-Object -First 20
```

**Other common bash → pwsh diffs in this vein:**

| bash | pwsh |
|---|---|
`tail -N` | `Select-Object -Last N`
`head -N` | `Select-Object -First N`
`grep pattern` | `Select-String pattern`
`wc -l` | `(Get-Content f \| Measure-Object -Line).Lines`
`touch file` | `if (-not (Test-Path file)) { New-Item -ItemType File file }`
`which cmd` | `(Get-Command cmd).Source`
`ls -la` | `Get-ChildItem` (or `ls` alias, no `-la` flag)

---

## (`GIT`/`COMMIT`/`HOOK-FAIL-AMEND-TRAP`)

**Signature** — Pre-commit hook fails → next attempt uses `--amend` → previous commit gets destroyed

**Root** — When a hook fails, the commit did NOT happen. `--amend` would modify the PRIOR commit. Always create a NEW commit after fixing the hook failure, never amend.

**Fix** — Fix the issue, re-stage, `git commit` fresh. Never `--amend` after a hook failure.

---

## (`CHTHONIC-PS1`/`REPO-ROOT-NULL`)

**Signature** — `Cannot bind argument to parameter 'Path' because it is null` in chthonic.ps1 domain handlers

**Waters** — Any domain handler that constructs a binary path

**Root** — `$CHTHONIC_ROOT` env var is null when script is called directly (not via MCP). `$SCRIPT_DIR` is set at line 33 via `Split-Path -Parent $PSScriptRoot`.

**Fix** — Use `$REPO_ROOT` (already defined as `Split-Path -Parent $SCRIPT_DIR`) for all path construction inside domain handlers — consistent with every other handler and immune to env var absence.

---

*SID: CLAUDEBASE_PWSH_SQUALL_LOG_V1 · live · squall named is squall tamed · 2026-06-22*
