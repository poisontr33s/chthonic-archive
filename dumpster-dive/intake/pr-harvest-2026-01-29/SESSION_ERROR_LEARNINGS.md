# Session Error Learnings — 2026-01-29

## Error Catalog

### Error 1: Shell Nesting (Bash→PowerShell pipe)
**Command:**
```bash
gh api ... | pwsh -Command "$input | Select-Object -Skip 1 | ..."
```

**Error:**
```
ParserError: An empty pipe element is not allowed.
```

**Root Cause:** Piping from Bash into `pwsh -Command` with `$input` creates race conditions. The PowerShell parser sees an empty pipe before stdin arrives.

**PWSH_RULES.md Violation:** Line 35 — "NEVER nest shells: `Bash(pwsh …)` is forbidden."

**Correct Pattern:**
```powershell
# Option A: Pure PowerShell
$result = gh api ... | ConvertFrom-Json
$result | ForEach-Object { ... }

# Option B: Pure Bash (if simple)
gh api ... --jq '.field' > output.txt

# Option C: Write to file, then process
gh api ... > temp.json
pwsh -Command "Get-Content temp.json | ..."
```

---

### Error 2: String Formatting Escape Issues
**Command:**
```bash
pwsh -Command "... | ForEach-Object { '{0,-60} {1,8}' -f ... }"
```

**Error:**
```
ParserError: You must provide a value expression following the '-f' operator.
```

**Root Cause:** Bash interprets `{0}` and `{1}` as brace expansion. The `-f` format operator never receives its arguments.

**PWSH_RULES.md Guidance:** Line 38 — "Complex PowerShell content MUST be written to a `.ps1` file before execution."

**Correct Pattern:**
```powershell
# Write to .ps1 file first
@'
Get-ChildItem -Recurse | ForEach-Object {
    '{0,-60} {1,8}' -f $_.Name, $_.Length
}
'@ | Set-Content temp.ps1

pwsh -File temp.ps1
```

---

### Error 3: Using Bash `find` Instead of PowerShell
**Command:**
```bash
find dumpster-dive/intake/... -type f -exec ls -la {} \;
```

**Observation:** This worked but violated pwsh-first policy.

**PWSH_RULES.md:** Line 154 — `find . -name "*.txt"` → `Get-ChildItem -Recurse -Filter "*.txt"`

**Correct Pattern:**
```powershell
Get-ChildItem -Path 'dumpster-dive/intake/...' -Recurse -File |
    Select-Object FullName, Length |
    Format-Table -AutoSize
```

---

## Corrected Patterns for Common Operations

### GitHub API → Local File
```powershell
# CORRECT: Direct gh output to file, then process
gh api repos/owner/repo/pulls/N/files --jq '.' |
    Set-Content -Path 'output.json'

# Then process in pure PowerShell
$data = Get-Content 'output.json' | ConvertFrom-Json
```

### Directory Listing with Sizes
```powershell
# CORRECT: Pure PowerShell
Get-ChildItem -Path $path -Recurse -File |
    Select-Object @{N='RelativePath';E={$_.FullName.Replace($basePath, '')}}, Length |
    Format-Table -AutoSize
```

### Extract Patch Content from PR
```powershell
# CORRECT: Use gh with jq for extraction, then pure PowerShell for processing
$patches = gh api repos/owner/repo/pulls/N/files | ConvertFrom-Json

foreach ($file in $patches) {
    $filename = $file.filename -replace '[/\\]', '_'
    $file.patch | Set-Content -Path "raw/$filename.patch"
}
```

---

## Rule Summary (For Future Sessions)

| Situation | Do This | Not This |
|-----------|---------|----------|
| GitHub API calls | `gh api ... \| ConvertFrom-Json` in pwsh | `gh ... \| pwsh -Command` |
| Complex string formatting | Write to `.ps1` file first | Inline in Bash with escapes |
| File operations | `Get-ChildItem`, `Get-Content` | `find`, `ls`, `cat` |
| JSON processing | `ConvertFrom-Json` / `ConvertTo-Json` | `jq` piped to pwsh |
| Multi-step pipelines | Split into discrete pwsh commands | Long Bash→pwsh chains |

---

## Integration with Sub-Agent Delegation

When spawning sub-agents for file operations:
1. **Prefer pure PowerShell** for all Windows file/path operations
2. **Use `gh` CLI directly** (it handles its own output)
3. **Avoid shell nesting** — if complex, write a `.ps1` script
4. **File paths:** Always use `Join-Path` and `-LiteralPath`

---

**Session:** 2026-01-29
**Errors Analyzed:** 3
**[PWSH_RULES.md](../../../docs/PWSH_RULES.md) Lines Referenced:** 35, 38, 154
