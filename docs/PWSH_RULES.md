# PowerShell Rules (pwsh-first)

<!--
@SID:           DOC_PWSH_RULES
@Type:          Policy Document
@Context:       Governance / Shell Environment
@SessionOrigin: SESSION_DOC_2026_01_05_SSOTIFICATION
@References:    CONTRACT_EXECUTION_INVARIANTS, CONTRACT_PROBE_ABI
@ReferencedBy:  DOC_CLAUDE_MD_ROOT
-->

**Version:** 1.2
**Status:** VERIFIED
**Validation Date:** 2026-02-01
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

## Execution Discipline (Non-Negotiable)

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

## Profile Configuration

**Pattern:** OneDrive stub sources local profile for fast startup (~65ms vs 60+ seconds).

**OneDrive profile** (`$PROFILE`):
```powershell
# Stub: Source actual profile from local disk (faster than OneDrive)
$localProfile = "C:\Users\erdno\.config\powershell\profile.ps1"
if (Test-Path $localProfile) { . $localProfile }
```

**Local profile** (`C:\Users\erdno\.config\powershell\profile.ps1`):
- UTF-8 encoding (must be first line)
- Reload guards using env vars and globals
- Chthonic CLI initialization

**UTF-8 encoding (required first line):**
```powershell
[Console]::InputEncoding = [Console]::OutputEncoding = $OutputEncoding = [System.Text.Encoding]::UTF8
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
- String concatenation: `$path = $root + "\\" + $file`
- Forward slashes on Windows: `$path = "$root/output.txt"`
- Relative paths: `.\scripts\bin\tool.exe` (use `$PSScriptRoot` + `Join-Path`)

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

## Translation Guide: Bash to PowerShell

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

## Common Error Patterns

### Error 1: Shell Nesting (Bash to PowerShell pipe)

**Anti-pattern:**
```bash
gh api ... | pwsh -Command "$input | Select-Object ..."
```

**Error:** `ParserError: An empty pipe element is not allowed.`

**Root Cause:** Piping from Bash into `pwsh -Command` with `$input` creates race conditions.

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

**Root Cause:** Bash interprets `{0}` and `{1}` as brace expansion.

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

### Quick Reference

| Situation | Correct | Avoid |
|-----------|---------|-------|
| GitHub API | `gh api ... \| ConvertFrom-Json` | `gh ... \| pwsh -Command` |
| String formatting | Write to `.ps1` file | Inline with Bash escapes |
| File operations | `Get-ChildItem` | `find`, `ls` |
| JSON processing | `ConvertFrom-Json` | `jq` piped to pwsh |
| Multi-step logic | Discrete pwsh commands | Long Bash to pwsh chains |

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

## Shell Capability Probe

**Location:** `.\scripts\shell_capabilities.ps1`
**Purpose:** Minimal, ABI-stable environment probe for AI agents
**Contract:** See [docs/PROBE_CONTRACT.md](PROBE_CONTRACT.md) for full ABI specification

**Quick Validation:**
```powershell
.\scripts\shell_capabilities.ps1 | ConvertFrom-Json | Format-List
```

**Agent Usage:** AI agents MUST run the probe before planning and use its JSON output as ground truth for environment detection.

---

## Governance References

**Authority Hierarchy (top-down):**
1. **Runtime Reality:** OS + shell behavior (Win11 + pwsh)
2. **Repository Doctrine:** `.github/copilot-instructions.md` (SSOT)
3. **Session Bootstrap:** [docs/SESSION_BOOTSTRAP_SPEC.md](SESSION_BOOTSTRAP_SPEC.md)
4. **Editing Policy:** [docs/CLI_EDITING_POLICY.md](CLI_EDITING_POLICY.md)
5. **This Document:** `docs/PWSH_RULES.md`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.2 | 2026-02-01 | Added profile configuration (OneDrive stub pattern, UTF-8); removed extraneous sections |
| 1.1 | 2026-01-29 | Added "Common Error Patterns" section from session learnings |
| 1.0 | 2026-01-05 | Initial pwsh-first contract |

---

**Maintained by:** Repository governance framework
**SSOT Reference:** `.github/copilot-instructions.md`
