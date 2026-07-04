# (`ALWAYS`/`Refer-To`/`chthonic-archive/CLAUDEBASE`/`Leave-The`/`SSOT-Frozen-Monolith`/`As-Is`/`Guidance`): 
- [New-Meeting-Point](/CLAUDEBASE/MANIFEST.md) **<- NAVIGATE BACK**

# PowerShell Rules (pwsh-first)

<!--
@SID:           DOC_PWSH_RULES
@Type:          Policy Document
@Context:       Governance / Shell Environment
@SessionOrigin: SESSION_DOC_2026_01_05_SSOTIFICATION
@References:    CONTRACT_EXECUTION_INVARIANTS, CONTRACT_PROBE_ABI
@ReferencedBy:  DOC_CLAUDE_MD_ROOT
-->

**Version:** 1.6
**Status:** VERIFIED
**Validation Date:** 2026-04-21
**Authority:** `.github/copilot-instructions.md` [SSOT-companion](.github/copilot-instructions.archive.md) (SSOT-canon) --monolith 'macro.prompt-world'

---

## Policy Statement

This repository adopts **PowerShell 7.5.x+ (Chthonic) --as the canonical Win11 environment for all scripting, automation, and CLI operations.

### Objectives
1. **Determinism** - No profile pollution via `-NoProfile`
2. **Cross-platform** - PowerShell 7.5.x+ runs on Windows, macOS, Linux
3. **Governance** - Shell rules tracked in `.claude/settings.local.json`
4. **Auditability** - Shell capability probes validate environment state

---

## Execution Discipline — Windows (Non-Negotiable)

1. Canonical shell is PowerShell 7.x.x (`pwsh`).
2. PowerShell commands MUST run directly in pwsh — never via Bash.
3. NEVER nest shells: `Bash(pwsh …)` is forbidden.
4. Bash is a foreign runtime; use only as: `pwsh> bash -lc "<pure bash>"`.
5. Bash commands MUST contain zero PowerShell syntax.
6. Complex PowerShell content MUST be written to a `.ps1` file before execution.
7. Heredocs for PowerShell via Bash are forbidden.
8. If a command fails due to shell mismatch, STOP — do not retry.
9. Git commits are NEVER executed by Claude; only prepared and handed off.
10. When in doubt, re-plan before invoking any tool.

---

## Canonical Shell

**Executable:** `pwsh.exe` or `pwsh` (PowerShell 7.x.x or later)
**Required:** All new scripts MUST use PowerShell 7.x.x+
**VS Code Terminal:** "Pwsh (Chthonic)" with `-NoProfile -NoExit`

**Verification:**
```powershell
$PSVersionTable.PSVersion   # Should return 7.x.x or higher
$PSVersionTable.PSEdition   # Should return "Core"
```

---

## Script Standards

### 1. Header Requirements

Every PowerShell script MUST include:

```powershell
[CmdletBinding()]
param(
  # Parameters with type annotations
  [string]$ExampleParam,
  [switch]$ExampleSwitch
)

$ErrorActionPreference = 'Stop'
```

**Rationale:**
- `[CmdletBinding()]` enables advanced parameter features
- Type annotations prevent runtime type errors
- Strict error mode (`Stop`) prevents silent failures

### 2. Path Handling

**REQUIRED patterns:**

```powershell
# Repo-root discovery (canonical pattern)
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path

# Path normalization
function Normalize-Dir([string]$p) {
  if ([string]::IsNullOrWhiteSpace($p)) { return $null }
  try {
    $rp = (Resolve-Path -LiteralPath $p -ErrorAction Stop).Path
    return $rp.TrimEnd('\\')
  } catch {
    return $null
  }
}

# Path construction
$outputPath = Join-Path $repoRoot 'dumpster-dive\intake\output.json'
```

**FORBIDDEN:**
- ❌ String concatenation: `$path = $root + "\\" + $file`
- ❌ Forward slashes on Windows: `$path = "$root/output.txt"`
- ❌ Relative paths: `.\scripts\bin\tool.exe` (use `$PSScriptRoot` + `Join-Path`)

### 3. Output Formats

**Structured data (JSON):**
```powershell
$report = [ordered]@{
  timestamp = (Get-Date).ToString('o')
  results = @{ ... }
}

$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $outputPath
```

**Human-readable (Tables):**
```powershell
$results | Format-Table -AutoSize -Property Name, Status, Count
```

**No interactive prompts** - Use parameters instead of `Read-Host`

### 4. Error Handling

```powershell
try {
  # Risky operation
  $result = Invoke-SomeCommand -ErrorAction Stop
} catch {
  Write-Error "Operation failed: $_"
  # Handle or rethrow
  throw
}
```

---

## Translation Guide: Bash → PowerShell

| Bash | PowerShell | Notes |
|------|-----------|-------|
| `ls -la` | `Get-ChildItem -Force` | Include hidden files |
| `cat file.txt` | `Get-Content -LiteralPath file.txt` | Use `-LiteralPath` for special chars |
| `grep pattern file` | `Select-String -Pattern pattern -Path file` | Supports regex |
| `ps aux` | `Get-Process` | Structured object output |
| `chmod +x script.sh` | `Set-ExecutionPolicy` | Windows uses execution policy |
| `export VAR=value` | `$env:VAR = "value"` | Session-scoped by default |
| `find . -name "*.txt"` | `Get-ChildItem -Recurse -Filter "*.txt"` | Structured filtering |

---

## Common Error Patterns & Corrections

**Source:** Session learnings (2026-01-29) — Claude Code + PWSH interactions

### Error 1: Shell Nesting (Bash→PowerShell pipe)

**Anti-pattern:**
```bash
gh api ... | pwsh -Command "$input | Select-Object ..."
```

**Error:** `ParserError: An empty pipe element is not allowed.`

**Root Cause:** Piping from Bash into `pwsh -Command` with `$input` creates race conditions. The PowerShell parser sees an empty pipe before stdin arrives.

**Violation:** Line 35 — "NEVER nest shells"

**Correct Patterns:**
```powershell
# Option A: Pure PowerShell (preferred)
$result = gh api repos/owner/repo/pulls/N/files | ConvertFrom-Json
$result | ForEach-Object { $_.filename }

# Option B: Write to file, then process
gh api ... > temp.json
$data = Get-Content temp.json | ConvertFrom-Json

# Option C: Pure gh with jq (if simple extraction)
gh api ... --jq '.[] | .filename'
```

### Error 2: String Formatting Escape Issues

**Anti-pattern:**
```bash
pwsh -Command "... | ForEach-Object { '{0,-60} {1,8}' -f ... }"
```

**Error:** `ParserError: You must provide a value expression following the '-f' operator.`

**Root Cause:** Bash interprets `{0}` and `{1}` as brace expansion. The format operator never receives arguments.

**Violation:** Line 38 — "Complex PowerShell content MUST be written to a `.ps1` file before execution."

**Correct Pattern:**
```powershell
# Write to .ps1 file first
$scriptContent = @'
Get-ChildItem -Recurse | ForEach-Object {
    '{0,-60} {1,8}' -f $_.Name, $_.Length
}
'@
$scriptContent | Set-Content temp.ps1
pwsh -NoProfile -File temp.ps1
```

### Error 3: Bash-First File Operations

**Anti-pattern:**
```bash
find /path -type f -exec ls -la {} \;
```

**Problem:** Works, but violates pwsh-first policy and loses structured output.

**Correct Pattern:**
```powershell
Get-ChildItem -Path $path -Recurse -File |
    Select-Object FullName, Length, LastWriteTime |
    Format-Table -AutoSize
```

### Quick Reference Table

| Situation | Correct | Avoid |
|-----------|---------|-------|
| GitHub API | `gh api ... \| ConvertFrom-Json` | `gh ... \| pwsh -Command` |
| String formatting | Write to `.ps1` file | Inline with Bash escapes |
| File operations | `Get-ChildItem` | `find`, `ls` |
| JSON processing | `ConvertFrom-Json` | `jq` piped to pwsh |
| Multi-step logic | Discrete pwsh commands | Long Bash→pwsh chains |

---

## Bash Compatibility (Deprecated)

**Status:** Existing Bash permissions RETAINED but deprecated for new work

**Allowed:** Legacy scripts and cross-agent compatibility (Copilot, Gemini CLI may use Bash)

**Forbidden:** New Bash scripts in `/scripts` directory

**Invocation pattern (if required):**
```powershell
# Invoke Bash from PowerShell (explicit wrapper)
bash -lc "command here"
```

---

## Repo-Local Patterns

### Example: `scripts/probe_toolchain_path.ps1`
- **Lines 1-14:** Parameter block with switches
- **Lines 16-21:** `New-Stamp` timestamp function
- **Lines 23-31:** `Normalize-Dir` path handling
- **Lines 57-67:** Repo-root discovery and output directory setup
- **Lines 173-220:** JSON serialization and file output

### Example: `scripts/launch_claude_code.ps1`
- **Lines 7-10:** Parameter block (Force, WaitSeconds)
- **Lines 12:** Helper function with `Log` pattern
- **Lines 18-24:** Process detection helper
- **Lines 26-29:** Conditional execution logic

---

## Governance References

**Authority Hierarchy (top-down):**
1. **Runtime Reality:** OS + shell behavior (Win11 + pwsh)
2. **Repository Doctrine:** [SSOT](.github/copilot-instructions.archive.md) (SSOT - FROZEN Monolith - 313KB)
3. **Session Bootstrap:** [SESSION_BOOTSTRAP_SPEC.md](docs/archive/sessions/SESSION_BOOTSTRAP_SPEC.md) v1.1
4. **Editing Policy:** [CLI_EDITING_POLICY.md](docs/ops/CLI_EDITING_POLICY.md) (mechanical edits only)
5. **This Document:** [PWSH_RULES.md (repo-root)](PWSH_RULES.md) v1.0

<!-- NOTE: ARBITRAGE-BRIDGE.md planned but not yet created. Multi-agent shell preference negotiation is documented in AGENT_COMMON.md -->

---

## Validation & Testing

### Shell Capability Probe Contract

**Location:** [shell_capabilities.ps1](scripts/shell_capabilities.ps1)
**Purpose:** Minimal, ABI-stable environment probe for Claude Code and other AI agents
**Canonical Hash:** `934B9E30F4C30F65E4229055E2CCE41B99E99E792450D8A6B63EFC5F880B5E82`
**Contract:** See [PROBE_CONTRACT.md](docs/ops/PROBE_CONTRACT.md) for full ABI specification

**Requirements:**
See [PROBE_CONTRACT.md](docs/ops/PROBE_CONTRACT.md) for complete ABI contract. Key invariants:
- ✅ MUST output pure JSON to stdout (no text/logging)
- ✅ MUST NOT contain logic, branching, validation, or side-effects
- ✅ Validated by `scripts/validate_shell_probe.ps1` (hard gate)

**Quick Validation (4-step checklist):**

1. **Run probe and inspect JSON:**
   ```powershell
   .\scripts\shell_capabilities.ps1 | ConvertFrom-Json | Format-List
   ```

2. **Ensure no forbidden constructs:**
   ```powershell
   Select-String -Path .\scripts\shell_capabilities.ps1 -Pattern 'if|foreach|while|switch|try|catch' -SimpleMatch
   # Expected: no output
   ```

3. **Verify canonical hash:**
   ```powershell
   Get-FileHash .\scripts\shell_capabilities.ps1 -Algorithm SHA256
   # Expected: 934B9E30F4C30F65E4229055E2CCE41B99E99E792450D8A6B63EFC5F880B5E82
   ```

4. **Run automated validator:**
   ```powershell
   .\scripts\validate_probe.ps1
   # Expected: exit code 0 (all checks pass)
   ```

**CI Integration:**

Probe validation runs automatically on push/PR via `.github/workflows/validate-probe.yml`. The workflow:
- Validates canonical hash match
- Checks for forbidden logic constructs
- Runs upcycle audit to detect violations
- Scans for probe variants in repository

**Comparing Probe Variants:**

If multiple `.ps1` files exist that might be probe variants, compare them:

```powershell
Get-ChildItem -Path . -Filter "*.ps1" -Recurse | ForEach-Object {
  $path = $_.FullName
  $hash = (Get-FileHash $path -Algorithm SHA256).Hash
  $hasForbidden = if (Select-String -Path $path -Pattern 'if|foreach|while|switch|try|catch' -SimpleMatch) { $true } else { $false }
  [PSCustomObject]@{
    Path = $path
    SHA256 = $hash
    HasForbiddenLogic = $hasForbidden
    IsCanonical = ($hash -eq "934B9E30F4C30F65E4229055E2CCE41B99E99E792450D8A6B63EFC5F880B5E82")
  }
} | Format-Table -AutoSize
```

**Action Required for Non-Canonical Variants:**
- Variants with `HasForbiddenLogic = True` violate ABI contract → quarantine to `scripts/dev/` or rename with `_obsolete` suffix
- Variants with different hash but no forbidden logic → document purpose or archive

**Output Format:**
```json
{
  "os": "Microsoft Windows 11 Pro",
  "pwsh_version": "7.5.4",
  "bash": "C:\\Program Files\\Git\\bin\\bash.exe",
  "bun": "C:\\Users\\...\\bun.exe",
  "cargo": "C:\\Users\\...\\.cargo\\bin\\cargo.exe",
  "uv": "C:\\Users\\...\\uv.exe",
  "git": "C:\\Program Files\\Git\\cmd\\git.exe",
  "claude": null,
  "path": ["...", "..."]
}
```

**Agent Usage Policy:**

AI agents (Claude Code, GitHub Copilot CLI) MUST:
1. Run `.\scripts\shell_capabilities.ps1` before planning
2. Use JSON output as ground truth for environment detection
3. NOT attempt to "improve" or modify the probe (ABI stable)
4. Reference canonical hash when reporting environment state

**Integration test:** All scripts pass `-NoProfile` execution without errors.

---

## Package Management (bun-first)

**Canonical package manager:** `bun`
**npm status:** DEAD — removed from `node_modules\`. If `npm` resolves, it is from a stale `node_modules\npm\` in a parent dir. Kill it: `Remove-Item -Recurse -Force node_modules`.

### Add dev dependency
```pwsh
bun add -d <package>
```

### Add dependency to a specific workspace/package
```pwsh
bun add -d <package> --cwd packages/<package-folder>
```

### Security Audit — Architecture

`bun audit` walks **UP from CWD to the nearest `package.json`** and audits that workspace. Overrides do NOT cascade between workspaces.

**Precedence chain for this machine:**
```
C:\Users\eldno\               → package.json (home-level workspace — global installs live here)
└── chthonic-archive\         → package.json (repo root workspace)
    └── apps\chthonic-next\   → package.json (nested sub-workspace, isolated)
    └── [all other subdirs]   → walk up → hit repo root
```

**`bunfig.toml [audit]` is NOT implemented in bun 1.3.12** — the section is silently ignored at runtime. Use `bun run audit` instead (script with `--ignore` flags baked in):
```pwsh
bun run audit        # filtered — ignores known false-positives
bun run audit:full   # unfiltered — shows everything including false-positives
bun audit            # bare — also works if overrides block covers all vulns
```

**Hono boundary comparison bug (bun 1.3.12):**
`hono@4.12.12` IS the patched version, but bun incorrectly evaluates `4.12.12 < 4.12.12 = true`.
Fix: add `"hono": "4.12.12"` to the `overrides` block in `package.json`. This tells the resolver the version is explicitly governed, bypassing the boundary check entirely. This is an architectural fix, not a suppression workaround.

**Home-dir workspace (`~\package.json`) is a real, separate scope:**
When bun installs global packages (gemini-cli, claude-code, etc.), it creates `C:\Users\eldno\package.json`. Running `bun audit` from `~` audits THIS file, not the repo. It needs its own `overrides` block maintained independently.

**Rule: every directory where `bun audit` might be run needs its own overrides.** This is universal — applies to any local project folder, not just this repo.

**`bunfig.toml` additivity:** user-global (`~\.config\bun\bunfig.toml`) + CWD-local `bunfig.toml` are both loaded simultaneously and merged. `BUNFIG_PATH` env var is intentionally NOT set in profile — setting it would shadow CWD-local bunfig.

**Notes:**
- Bun scopes installs by working directory, not `--filter`
- `pnpm`, `npm`, and `yarn` commands are not canonical in this repository

---

## Advanced Topics

### Performance Optimization
- Avoid dot-sourcing in loops
- Use `System.Collections.Generic.List[T]` instead of `@()` arrays for large datasets
- Pipeline filtering: `Where-Object { $_.Property }` vs `foreach` loops

### Windows-Specific Features
- COM interop: `New-Object -ComObject Shell.Application`
- Registry access: `Get-ItemProperty -Path "HKLM:\Software\..."`
- Execution policy management: `Set-ExecutionPolicy -Scope Process`

### Profile Optimization & UTF-8
**Mandatory Encoding Preamble (First Line):**
```powershell
[Console]::InputEncoding = [Console]::OutputEncoding = $OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"   # PEP 597 — stream encoding for pipes/ttys
$env:PYTHONUTF8      = "1"        # PEP 540 — global UTF-8 mode (file I/O + locale)
chcp 65001 | Out-Null             # Win32 console code page — covers legacy tools
```
All four are already set in `~/.config/powershell/profile.ps1`. The Microsoft.PowerShell_profile.ps1 stub sets them as fallback (guarded, idempotent). `fortify_terminal.ps1` applies them in automation contexts.

**OneDrive Performance Fix (Stub Pattern):**
If `$PROFILE` resides on OneDrive, replace it with a stub that sources a local file to bypass sync latency (60s -> 65ms):
```powershell
$localProfile = "C:\Users\eldno\.config\powershell\profile.ps1"
if (Test-Path $localProfile) { . $localProfile }
```

### Module Loading
```powershell
# Check availability
if (Get-Module -ListAvailable ModuleName) {
  Import-Module ModuleName
}
```

---

## Future Extensions

**Phase 2 (Strict Enforcement):**
- CI validation: Fail if non-pwsh scripts detected in `/scripts`
- Automated smoke tests: All scripts run with `-NoProfile` in CI
- Version pinning: Require PSv7.4.0+ in all scripts

**Phase 3 (Multi-Agent Integration):**
- Bash opt-in for specific agent workflows
- Shell preference negotiation protocol in ARBITRAGE-BRIDGE.md
- Cross-shell testing matrix

---

## PATH Integrity & Invocation Rules

> **Origin:** Session 2026-04-15. Root cause: extensionless phantom files in PATH dirs hijack ShellExecute and produce "Open With" dialogs. These rules prevent recurrence.

### Rule P-1: Always use `.exe` for system executables

```powershell
# CORRECT — explicit extension, bypasses PATHEXT/ShellExecute ambiguity
& powershell.exe -NoProfile -Command '...'
Start-Process pwsh.exe -ArgumentList '-NoProfile', '-Command', '...'

# FORBIDDEN — bare name triggers ShellExecute, will open "Open With" if any
#             extensionless file shadows the real exe in PATH
& powershell
& cmd
```

### Rule P-2: Never create extensionless files in PATH directories

AI agents and scripts MUST NOT create files without extensions in any directory that appears in `$env:PATH`. This includes `C:\WINDOWS\System32\`, `C:\WINDOWS\`, and any tool bin directory.

```powershell
# FORBIDDEN — creates phantom that shadows cmd.exe
New-Item 'C:\WINDOWS\System32\powershell'

# CORRECT — always include extension
New-Item 'C:\WINDOWS\System32\my-tool.exe'
```

### Rule P-3: MSYS2/Cygwin `usr\bin` must never appear before System32 in PATH

The `msys64\usr\bin` directory contains bash scripts named `cmd`, `start`, `shell` with no extension. These **will** hijack ShellExecute and trigger "Open With" dialogs for any bare-name invocation.

- `rv shell env powershell` (Ruby DevKit) re-injects `msys64\usr\bin` on every shell init — the profile **must** strip it immediately after `Invoke-Expression`
- `ucrt64\bin` is safe to keep (contains `.exe` files only)
- Detection: `$env:PATH -split ';' | Where-Object { $_ -match 'msys64\\usr\\bin' }`

### Rule P-4: PATH integrity audit on shell startup

The profile runs `Test-PathIntegrity` on startup. Any zero-byte extensionless file in the first 30 PATH entries triggers a `Write-Warning`. Elevated sessions can delete; non-elevated sessions must report.

```powershell
# Audit manually:
$env:PATH -split ';' | Select-Object -First 30 | ForEach-Object {
    if (Test-Path $_) {
        Get-ChildItem $_ -File | Where-Object { -not $_.Extension -and $_.Length -eq 0 } |
            ForEach-Object { Write-Warning "PHANTOM: $($_.FullName)" }
    }
}
```

### Rule P-5: `powershell.exe` vs `pwsh.exe`

| Use case | Correct invocation |
|----------|--------------------|
| Run PS 5.1 explicitly | `powershell.exe -NoProfile -Command '...'` |
| Run PS 7.x (canonical) | `pwsh.exe -NoProfile -Command '...'` |
| Elevated spawn | `Start-Process pwsh.exe -Verb RunAs` |
| Agent/AI tool calls | Always `.exe` suffix — never bare name |

---

## Ruby Toolchain (rv + ridk)

> **Origin:** Session 2026-04-22. Root cause: bare `ridk` resolves via PATH without rv version binding — targets the wrong version's `msys64`. `rv r ridk` is the only canonical form.

### Rule R-1: Never invoke bare `ridk`

```powershell
# CORRECT — rv proxy routes to active version's own msys64
rv r ridk version
rv r ridk install 1

# FORBIDDEN — PATH resolution bypasses rv binding, targets wrong msys64
ridk version
ridk install 1 2 3
```

### Rule R-2: DevKit install is sequential — never combined

```powershell
# CORRECT — one phase at a time
rv r ridk install 1   # MSYS2 base
rv r ridk install 2   # MSYS2 system update (pacman -Syu)
rv r ridk install 3   # MINGW toolchain (gcc, binutils, ucrt64, winpthreads, pkgconf)

# FORBIDDEN — combined hides per-phase failure
rv r ridk install 1 2 3
```

Phase 2 and 3 depend on phase 1. Sequential runs surface failure at the correct step and allow retry without repeating prior phases.

### Rule R-3: Pin Ruby version per repo

```powershell
# Pin active version — run once, commit .ruby-version
rv ruby pin <version>   # writes .ruby-version to repo root
```

`.ruby-version` is rv's per-project pin file. `rv` reads it on directory entry and activates the matching installed version automatically.

**Current repo pin:** `4.0.3` (`.ruby-version` committed 2026-04-22)

### Rule R-4: Upgrade path — no `upgrade` subcommand

`rv ruby upgrade` does not exist. The canonical upgrade sequence:

```powershell
rv ruby install <new-version>    # install new version
rv r ridk install 1              # MSYS2 base in new version's msys64
rv r ridk install 2              # MSYS2 system update
rv r ridk install 3              # MINGW DevKit
rv ruby uninstall <old-version>  # remove old (no stacking)
rv ruby pin <new-version>        # update .ruby-version, commit
```

---

## R Toolchain (rv-r)

> **Origin:** Session 2026-04-22. Disambiguation: `rv` = Ruby version manager. `rv-r` = R package manager. Same binary namespace prefix, different tools — no collision when the suffix is correct.

### Rule RR-1: `rv-r` is R packages — `rv` is Ruby versions

| Invocation | Manages | Config file |
|------------|---------|-------------|
| `rv` | Ruby versions (install/uninstall/pin) | `.ruby-version` |
| `rv r ridk` | Ruby DevKit / MSYS2 (via rv proxy) | — |
| `rv-r` | R packages (add/sync/upgrade) | `rproject.toml` |

```powershell
# R package operations — rv-r only
rv-r sync              # install locked packages
rv-r add <pkg>         # add package and sync
rv-r upgrade           # upgrade all packages
rv-r plan              # dry-run of sync
rv-r summary           # project status

# FORBIDDEN — rv manages Ruby versions, not R packages
rv install ggplot2
```

### Rule RR-2: R version is pinned in `rproject.toml`

Unlike Ruby (`.ruby-version`), R version is declared directly in `rproject.toml`:

```toml
[project]
r_version = "4.5"   # R version constraint — not a rv-r subcommand
```

`rproject.toml` is the `rv-r` project manifest (equivalent to `pyproject.toml` for `uv`). It holds both the R version constraint and package dependencies. Committed at repo root.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.6 | 2026-04-22 | Added R Toolchain section (RR-1/RR-2): rv-r vs rv disambiguation, rproject.toml as R manifest, R version pin location; rproject.toml whitelisted in .gitignore |
| 1.5 | 2026-04-22 | Added Ruby Toolchain section (R-1 through R-4): rv r ridk canonical form, sequential DevKit install, version pin (.ruby-version), upgrade path |
| 1.4 | 2026-04-21 | Hash refresh (shell_capabilities.ps1 → `934B9E30...`); `eldno` → `eldno` typo fix |
| 1.3 | 2026-04-15 | Added PATH Integrity & Invocation Rules (P-1 through P-5): bare-name phantom risk, MSYS2 usr\bin demotion, extensionless file prohibition, powershell.exe/pwsh.exe disambiguation |
| 1.2 | 2026-04-13 | Added bun audit architecture, precedence chain, hono boundary bug, home-dir workspace scope, npm death strategy |
| 1.1 | 2026-01-29 | Added "Common Error Patterns & Corrections" section from session learnings |
| 1.0 | 2026-01-05 | Initial pwsh-first contract |

---

**Maintained by:** Repository governance framework
**SSOT Reference:** `.github/copilot-instructions.md`
**Related:** `docs/docs/SESSION_BOOTSTRAP_SPEC.md` v1.1, `docs/docs/CLI_EDITING_POLICY.md`

