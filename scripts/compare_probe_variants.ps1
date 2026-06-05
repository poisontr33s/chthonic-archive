#!/usr/bin/env pwsh
# @SID: SCRIPT_COMPARE_PROBE_VARIANTS_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: compare_probe_variants.ps1
# ║ Module: Probe variant scanner
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: DIAGNOSTIC
# ║ Purpose: Scan repo for probe-like PS1 variants and flag deviations
# ║ Exports: (none)
# ║ Flags/Modes: -CanonicalHash
# ║ Cross-References: scripts/shell_capabilities.ps1
# ╚════════════════════════════════════════════════════════════════════════════


# scripts/compare_probe_variants.ps1
# Scans repository for probe-like .ps1 files and compares against canonical form
# Usage: .\scripts\compare_probe_variants.ps1


param(
    [string]$CanonicalHash = "636383C0DB1F4ACDF539335337C322FD9E4F30F429A15B46C647876D29918116"
)

Write-Host "`n=== Probe Variant Scanner ===" -ForegroundColor Cyan
Write-Host "Scanning for shell/probe/capability-like .ps1 files...`n"

$variants = Get-ChildItem -Path . -Filter "*.ps1" -Recurse -File |
    Where-Object {
        $_.Name -like "*shell*" -or
        $_.Name -like "*probe*" -or
        $_.Name -like "*capabilities*" -or
        $_.Name -like "*sfs*"
    } |
    ForEach-Object {
        $path = $_.FullName
        $relativePath = $path.Replace("$PWD\", "")
        $hash = (Get-FileHash $path -Algorithm SHA256).Hash
        $content = Get-Content $path -Raw

        # Check for forbidden constructs
        $hasForbidden = $content -match '\b(if|foreach|for|while|switch|try|catch)\b'

        # Check for ABI header
        $hasHeader = $content -match '# DO NOT EDIT — ABI STABLE PROBE'

        # Determine status
        $isCanonical = $hash -eq $CanonicalHash
        $status = if ($isCanonical) {
            "✓ CANONICAL"
        } elseif ($hasForbidden) {
            "⚠ VARIANT (has logic)"
        } elseif ($hasHeader) {
            "⚠ VARIANT (modified)"
        } else {
            "⚠ VARIANT (different)"
        }

        [PSCustomObject]@{
            Path = $relativePath
            Status = $status
            HasHeader = if ($hasHeader) { "✓" } else { "✗" }
            HasLogic = if ($hasForbidden) { "⚠" } else { "✓" }
            Hash = $hash.Substring(0, 16) + "..."
            FullHash = $hash
        }
    }

# Display results
if ($variants.Count -eq 0) {
    Write-Host "No probe-like files found." -ForegroundColor Yellow
    exit 0
}

$variants | Format-Table -Property Path, Status, HasHeader, HasLogic, Hash -AutoSize

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
$canonical = $variants | Where-Object { $_.Status -eq "✓ CANONICAL" }
$variantsWithLogic = $variants | Where-Object { $_.HasLogic -eq "⚠" }

Write-Host "Total files: $($variants.Count)"
Write-Host "Canonical: $($canonical.Count)"
Write-Host "Variants with forbidden logic: $($variantsWithLogic.Count)"

if ($variantsWithLogic.Count -gt 0) {
    Write-Host "`n⚠ Action Required:" -ForegroundColor Yellow
    Write-Host "The following files contain forbidden logic constructs:"
    $variantsWithLogic | ForEach-Object {
        Write-Host "  - $($_.Path)" -ForegroundColor Red
    }
    Write-Host "`nRecommendation: Move to scripts/dev/ or rename with _obsolete suffix"
}

# Full hash dump for verification
Write-Host "`n=== Full Hashes ===" -ForegroundColor Cyan
$variants | ForEach-Object {
    $statusColor = if ($_.Status -eq "✓ CANONICAL") { "Green" } else { "Yellow" }
    Write-Host "$($_.Path)" -ForegroundColor $statusColor
    Write-Host "  $($_.FullHash)"
}

