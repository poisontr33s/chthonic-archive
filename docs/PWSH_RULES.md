# PowerShell Rules (pwsh-first)

<!--
@SID:           DOC_PWSH_RULES
@Type:          Policy Document
@Context:       Governance / Shell Environment
@SessionOrigin: SESSION_DOC_2026_01_05_SSOTIFICATION
@References:    CONTRACT_EXECUTION_INVARIANTS, CONTRACT_PROBE_ABI
@ReferencedBy:  DOC_CLAUDE_MD_ROOT
-->

**Version:** 1.1
**Status:** VERIFIED
**Validation Date:** 2026-01-29
**Authority:** `.github/copilot-instructions.md` (SSOT)

---

## Policy Statement

This repository adopts **PowerShell 7+ as the canonical shell environment** for all scripting, automation, and CLI operations.

### Objectives
1. **Determinism** - No profile pollution via `-NoProfile`
2. **Cross-platform** - PowerShell 7 runs on Windows, macOS, Linux
3. **Governance** - Shell rules tracked in `.claude/settings.local.json`
4. **Auditability** - Shell capability probes validate environment state

---

## Execution Discipline — Windows (Non-Negotiable)

1. Canonical shell is PowerShell 7+ (`pwsh`).
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

**Executable:** `pwsh.exe` or `pwsh` (PowerShell 7.4.0 or later)
**Required:** All new scripts MUST use PowerShell 7+
**VS Code Terminal:** "Pwsh (Chthonic)" with `-NoProfile -NoExit`

**Verification:**
```powershell
$PSVersionTable.PSVersion   # Should return 7.4.0 or higher
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
2. **Repository Doctrine:** `.github/copilot-instructions.md` (SSOT - 313KB)
3. **Session Bootstrap:** `docs/docs/SESSION_BOOTSTRAP_SPEC.md` v1.1
4. **Editing Policy:** `docs/docs/CLI_EDITING_POLICY.md` (mechanical edits only)
5. **This Document:** `docs/PWSH_RULES.md` v1.0

**Multi-Agent Coordination:** See `ARBITRAGE-BRIDGE.md` for shell preference negotiation between Claude Code, GPT-5/Copilot, and Gemini CLI.

---

## Validation & Testing

### Shell Capability Probe Contract

**Location:** `.\scripts\shell_capabilities.ps1`
**Purpose:** Minimal, ABI-stable environment probe for Claude Code and other AI agents
**Canonical Hash:** `6D6782ED8FFC4BF434D2A7108A0F3BACF13C3B40CC5C8F00F53CB789A96D9DF8`
**Contract:** See `docs/PROBE_CONTRACT.md` for full ABI specification

**Requirements:**
See `docs/PROBE_CONTRACT.md` for complete ABI contract. Key invariants:
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
   # Expected: 6D6782ED8FFC4BF434D2A7108A0F3BACF13C3B40CC5C8F00F53CB789A96D9DF8
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
    IsCanonical = ($hash -eq "6D6782ED8FFC4BF434D2A7108A0F3BACF13C3B40CC5C8F00F53CB789A96D9DF8")
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

### Add dev dependency
```pwsh
bun add -d <package>
```

### Add dependency to a specific workspace/package
```pwsh
bun add -d <package> --cwd packages/<package-folder>
```

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

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2026-01-29 | Added "Common Error Patterns & Corrections" section from session learnings |
| 1.0 | 2026-01-05 | Initial pwsh-first contract |

---

**Maintained by:** Repository governance framework
**SSOT Reference:** `.github/copilot-instructions.md` hash `49ef091b...`
**Related:** `docs/docs/SESSION_BOOTSTRAP_SPEC.md` v1.1, `docs/docs/CLI_EDITING_POLICY.md`
