#!/usr/bin/env pwsh

# @SID: SCRIPT_CHECK_TOOLCHAIN_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: check-toolchain.ps1
# ║ Module: Oxidized CLI toolchain precondition gate
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: AMBER
# ║ Architectural Role: GATE / PREFLIGHT
# ║ Semantic ID: SCRIPT_CHECK_TOOLCHAIN_V1
# ║ Purpose: Verify Rust CLI toolchain (Tier 1-2) is installed before G6/G7+
# ║ Exports: (none)
# ║ Flags/Modes: -Tier, -Strict, -Json, -Install
# ║ Cross-References: chthonic.ps1, CORPUS_ACHIEVEMENT_GATES.md
# ╚════════════════════════════════════════════════════════════════════════════

param(
    # Which tiers to check: 1, 2, or "all"
    [ValidateSet("1","2","all")]
    [string]$Tier = "1",

    # Exit 1 if any Tier-1 tool is missing (CI gate mode)
    [switch]$Strict,

    # Emit structured JSON instead of human-readable output
    [switch]$Json,

    # After reporting, run cargo install for any missing tools
    [switch]$Install
)

$ErrorActionPreference = 'Stop'

# ─────────────────────────────────────────────────────────────────────────────
# TOOL CATALOG
# ─────────────────────────────────────────────────────────────────────────────

$TIER1 = @(
    @{ name = "rg";      crate = "ripgrep";          purpose = "fast grep — corpus search, G7 verification" },
    @{ name = "fd";      crate = "fd-find";           purpose = "fast find — session file discovery" },
    @{ name = "bat";     crate = "bat";               purpose = "syntax-highlighted cat — log inspection" },
    @{ name = "delta";   crate = "git-delta";         purpose = "semantic git diffs" },
    @{ name = "jaq";     crate = "jaq";               purpose = "jq-compatible JSON filter — Ollama/mistralrs response shaping" },
    @{ name = "xh";      crate = "xh";                purpose = "HTTP client — G7 Ollama :8765 + mistralrs :8080 probes" }
)

$TIER2 = @(
    # NOTE: ast-grep must be installed separately: cargo install --locked ast-grep --bin sg
    # (--bin sg leaks to all crates if combined with other packages in one invocation)
    @{ name = "sg";      crate = "ast-grep --bin sg"; purpose = "AST-aware grep — structural code search" },
    @{ name = "tokei";   crate = "tokei";             purpose = "language stats — corpus size profiling" },
    @{ name = "difft";   crate = "difftastic";        purpose = "tree-diffing — corpus migration validation" },
    @{ name = "hyperfine"; crate = "hyperfine";       purpose = "benchmarking — G6/G7 view vs materialized latency" }
)

# ─────────────────────────────────────────────────────────────────────────────
# RESOLVE WHICH TIERS TO CHECK
# ─────────────────────────────────────────────────────────────────────────────

$toCheck = @()
if ($Tier -eq "1" -or $Tier -eq "all") { $toCheck += $TIER1 | ForEach-Object { $_ + @{ tier = 1 } } }
if ($Tier -eq "2" -or $Tier -eq "all") { $toCheck += $TIER2 | ForEach-Object { $_ + @{ tier = 2 } } }

# ─────────────────────────────────────────────────────────────────────────────
# PROBE
# ─────────────────────────────────────────────────────────────────────────────

$results = @()
$missing1 = @()

foreach ($tool in $toCheck) {
    $cmd = Get-Command $tool.name -ErrorAction SilentlyContinue
    $version = $null
    if ($cmd) {
        try {
            $v = & $tool.name --version 2>&1 | Select-Object -First 1
            $version = "$v".Trim()
        } catch { $version = "(version check failed)" }
    }
    $entry = [ordered]@{
        tier    = $tool.tier
        name    = $tool.name
        crate   = $tool.crate
        ok      = ($null -ne $cmd)
        version = $version
        path    = if ($cmd) { $cmd.Source } else { $null }
        purpose = $tool.purpose
    }
    $results += $entry
    if ($tool.tier -eq 1 -and -not $cmd) { $missing1 += $tool.name }
}

# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT
# ─────────────────────────────────────────────────────────────────────────────

if ($Json) {
    $payload = [ordered]@{
        timestamp  = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
        tier       = $Tier
        ok_count   = ($results | Where-Object { $_.ok }).Count
        missing_t1 = $missing1
        tools      = $results
    }
    $payload | ConvertTo-Json -Depth 4
} else {
    Write-Host ""
    Write-Host "  ── Oxidized CLI Toolchain Gate ──────────────────────────────" -ForegroundColor Cyan

    foreach ($r in $results) {
        $tierLabel = "T$($r.tier)"
        if ($r.ok) {
            Write-Host ("  [{0}] {1,-12} OK   {2}" -f $tierLabel, $r.name, $r.version) -ForegroundColor Green
        } else {
            Write-Host ("  [{0}] {1,-12} MISSING  (cargo install --locked {2})" -f $tierLabel, $r.name, $r.crate) -ForegroundColor Red
        }
    }

    $okCount = ($results | Where-Object { $_.ok }).Count
    $total   = $results.Count
    Write-Host ""
    Write-Host ("  {0}/{1} tools installed" -f $okCount, $total) -ForegroundColor $(if ($okCount -eq $total) { "Green" } else { "Yellow" })

    if ($missing1.Count -gt 0) {
        Write-Host ""
        Write-Host "  Install Tier 1 missing tools:" -ForegroundColor Yellow
        $missingCrates = ($TIER1 | Where-Object { $missing1 -contains $_.name } | ForEach-Object { $_.crate }) -join " "
        Write-Host "    cargo install --locked $missingCrates" -ForegroundColor Gray
    }
    Write-Host ""
}

# ─────────────────────────────────────────────────────────────────────────────
# INSTALL (opt-in)
# ─────────────────────────────────────────────────────────────────────────────

if ($Install -and $missing1.Count -gt 0) {
    Write-Host "  Installing missing Tier 1 tools..." -ForegroundColor Cyan
    $missingCrates = ($TIER1 | Where-Object { $missing1 -contains $_.name } | ForEach-Object { $_.crate }) -join " "
    $cmd = "cargo install --locked $missingCrates"
    Write-Host "  > $cmd" -ForegroundColor Gray
    Invoke-Expression $cmd
}

# ─────────────────────────────────────────────────────────────────────────────
# EXIT CODE
# ─────────────────────────────────────────────────────────────────────────────

if ($Strict -and $missing1.Count -gt 0) {
    if (-not $Json) {
        Write-Host "  GATE FAIL: $($missing1.Count) Tier-1 tool(s) missing." -ForegroundColor Red
    }
    exit 1
}

exit 0
