#!/usr/bin/env pwsh
# @SID: SCRIPT_SSOT_ACRONYM_AUDIT_V1

<#
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ssot_acronym_audit.ps1
# ║ Module: SSOT acronym auditor
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: SSOT
# ║ Purpose: Audit SSOT acronym consistency and line locations
# ║ Exports: (none)
# ║ Flags/Modes: -Root, -ShowAll, -FindLines
# ║ Cross-References: scripts/ssot_outline_extractor.ps1
# ╚════════════════════════════════════════════════════════════════════════════
#>

<#
.SYNOPSIS
    SSOT Acronym Consistency Auditor

.DESCRIPTION
    ⚠️ AUTO-UPDATE: Run after SSOT edits to catch acronym drift.
    Scans copilot-instructions.md for acronym patterns and reports:
    - Frequency counts
    - Variant detection (e.g., TRM-VRT vs T-TRM-FRM)
    - Line locations for fixes

.PARAMETER Root
    Base acronym to audit (e.g., 'TRM' finds TRM-VRT, TRM-GEO, T-TRM-FRM)

.PARAMETER ShowAll
    Show all acronyms in SSOT

.PARAMETER FindLines
    Show line numbers for specific acronym

.EXAMPLE
    .\ssot_acronym_audit.ps1 -Root 'TRM'
    .\ssot_acronym_audit.ps1 -ShowAll
    .\ssot_acronym_audit.ps1 -FindLines 'T-TRM-FRM'
#>

param(
    [string]$Root,
    [switch]$ShowAll,
    [string]$FindLines
)

. (Join-Path $PSScriptRoot "lib\ssot-paths.ps1")
$ssotPath = Resolve-SsotPath -Root (Resolve-Path "$PSScriptRoot\..") -Which pointer
$lines = Get-Content $ssotPath

# Build acronym index with line numbers
$acronymIndex = @{}
$lineNum = 0
foreach ($line in $lines) {
    $lineNum++
    # Match backtick-wrapped acronyms
    $matches = [regex]::Matches($line, '`([A-Z][A-Z0-9_-]+)`')
    foreach ($m in $matches) {
        $acronym = $m.Groups[1].Value
        if (-not $acronymIndex.ContainsKey($acronym)) {
            $acronymIndex[$acronym] = @{
                Count = 0
                Lines = @()
            }
        }
        $acronymIndex[$acronym].Count++
        $acronymIndex[$acronym].Lines += $lineNum
    }
}

if ($ShowAll) {
    Write-Host "`n=== ALL SSOT ACRONYMS (by frequency) ===" -ForegroundColor Cyan
    $acronymIndex.GetEnumerator() |
        Sort-Object { $_.Value.Count } -Descending |
        Select-Object -First 50 |
        ForEach-Object {
            $color = if ($_.Value.Count -gt 10) { 'Green' }
                     elseif ($_.Value.Count -gt 3) { 'Yellow' }
                     else { 'Gray' }
            Write-Host ("{0,-40} {1,3}x" -f $_.Key, $_.Value.Count) -ForegroundColor $color
        }
    Write-Host "`nTotal unique acronyms: $($acronymIndex.Count)" -ForegroundColor Magenta
}
elseif ($FindLines) {
    if ($acronymIndex.ContainsKey($FindLines)) {
        $info = $acronymIndex[$FindLines]
        Write-Host "`n=== $FindLines ===" -ForegroundColor Cyan
        Write-Host "Occurrences: $($info.Count)" -ForegroundColor Yellow
        Write-Host "Lines: $($info.Lines -join ', ')" -ForegroundColor Green
        Write-Host "`nContext:" -ForegroundColor Magenta
        foreach ($ln in $info.Lines | Select-Object -First 5) {
            Write-Host "  L$ln`: $($lines[$ln-1].Trim().Substring(0, [Math]::Min(80, $lines[$ln-1].Trim().Length)))..." -ForegroundColor Gray
        }
    } else {
        Write-Host "Acronym '$FindLines' not found in SSOT" -ForegroundColor Red
    }
}
elseif ($Root) {
    Write-Host "`n=== VARIANTS OF '$Root' ===" -ForegroundColor Cyan
    $variants = $acronymIndex.GetEnumerator() |
        Where-Object { $_.Key -match $Root } |
        Sort-Object { $_.Value.Count } -Descending

    # Find canonical (most used)
    $canonical = $variants | Select-Object -First 1
    Write-Host "CANONICAL: $($canonical.Key) ($($canonical.Value.Count)x)" -ForegroundColor Green

    Write-Host "`nVariants:" -ForegroundColor Yellow
    foreach ($v in $variants | Select-Object -Skip 1) {
        Write-Host ("  {0,-40} {1,3}x  Lines: {2}" -f $v.Key, $v.Value.Count, ($v.Value.Lines -join ',')) -ForegroundColor $(if($v.Value.Count -eq 1){'Red'}else{'Yellow'})
    }

    # Suggest fixes
    $singles = $variants | Where-Object { $_.Value.Count -eq 1 }
    if ($singles) {
        Write-Host "`n⚠️  POTENTIAL DEVIATIONS (single-use):" -ForegroundColor Red
        foreach ($s in $singles) {
            Write-Host "  Line $($s.Value.Lines[0]): $($s.Key)" -ForegroundColor Red
        }
    }
}
else {
    Write-Host "Usage:" -ForegroundColor Cyan
    Write-Host "  .\ssot_acronym_audit.ps1 -Root 'TRM'      # Find variants of TRM" -ForegroundColor Gray
    Write-Host "  .\ssot_acronym_audit.ps1 -ShowAll         # List all acronyms" -ForegroundColor Gray
    Write-Host "  .\ssot_acronym_audit.ps1 -FindLines 'DCRP' # Find line locations" -ForegroundColor Gray
}

