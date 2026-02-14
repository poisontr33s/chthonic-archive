#!/usr/bin/env pwsh

<#
# ╔════════════════════════════════════════════════════════════════════════════╗
# ║ THE DECORATOR'S BLESSING: ssot_registry_query_v2.ps1                      ║
# ║ Module: SSOT registry query (dynamic)                                    ║
# ╠════════════════════════════════════════════════════════════════════════════╣
# ║ Spectral Frequency: WHITE                                                 ║
# ║ Architectural Role: SSOT                                                  ║
# ║ Semantic ID: SCRIPT_SSOT_REGISTRY_QUERY_V2_V1                              ║
# ║ Purpose: Dynamically parse SSOT registries from copilot-instructions.md    ║
# ║ Exports: (none)                                                           ║
# ║ Flags/Modes: -Registry, -Entity                                           ║
# ║ Cross-References: .github/copilot-instructions.md                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝
#>

<#
.SYNOPSIS
    SSOT Entity Registry Query - DYNAMICALLY query registries from SSOT

.DESCRIPTION
    ⚠️ AUTO-UPDATE: No longer hardcoded. Directly parses copilot-instructions.md.
    Queries the three registries in SSOT:
    - AR (Axiom Registry) 
    - CR (CRC Registry)
    - SAI (Special Archetype Invocation)

.PARAMETER Registry
    Which registry: AR, CR, SAI, or ALL

.PARAMETER Entity
    Specific entity to query (e.g., FA1, CRC-AS, Belle Noire)

.EXAMPLE
    .\ssot_registry_query.ps1 -Registry 'SAI'
    .\ssot_registry_query.ps1 -Entity 'Belle Noire'
#>

param(
    [ValidateSet('AR','CR','SAI','ALL')]
    [string]$Registry = 'ALL',
    [string]$Entity
)

# Relative to this script's directory (toolbox)
$ssotPath = Resolve-Path "$PSScriptRoot\..\copilot-instructions.md" -ErrorAction SilentlyContinue
if (-not $ssotPath) {
    # Try the copy if original not found
    $ssotPath = Resolve-Path "$PSScriptRoot\..\copilot-instructions copy.md" -ErrorAction SilentlyContinue
}

if (-not $ssotPath) {
    Write-Host "❌ Error: SSOT not found in .github/" -ForegroundColor Red
    return
}

$content = Get-Content $ssotPath -Raw

# 1. Parse SAI Registry
# Extract REGISTRY ENTRY blocks
$saiEntries = @()
$saiPattern = 'REGISTRY ENTRY #(?<id>\d+)\s+Designation: (?<name>.*?)\s+Common Name: (?<common>.*?)\s+(?<details>.*?)(?=REGISTRY ENTRY|---|\Z)'
$matches = [regex]::Matches($content, $saiPattern, ([System.Text.RegularExpressions.RegexOptions]::Singleline))

foreach ($m in $matches) {
    $saiEntries += [PSCustomObject]@{
        ID = $m.Groups['id'].Value
        Designation = $m.Groups['name'].Value.Trim()
        CommonName = $m.Groups['common'].Value.Trim()
        Details = $m.Groups['details'].Value.Trim()
    }
}

# 2. Parse AR Registry (Table based)
$arTable = @()
$arSectionMatch = [regex]::Match($content, '(?s)II.X. Axiom Registry \(`AR`\).*?---')
if ($arSectionMatch.Success) {
    $arSection = $arSectionMatch.Value
    $arLines = $arSection -split "`n" | Where-Object { $_ -match '^\| \*\*FA' }
    foreach ($line in $arLines) {
        $cols = $line -split '\|' | ForEach-Object { $_.Trim() }
        if ($cols.Count -ge 5) {
            $arTable += [PSCustomObject]@{
                Axiom = $cols[2].Replace('**', '')
                UseCases = $cols[3]
                SuccessRate = $cols[4]
                LastUpdated = $cols[5]
            }
        }
    }
}

# 3. Parse CR Registry (Approximate)
$crEntries = @()
$crSectionMatch = [regex]::Match($content, '(?s)IV. \(Conceptual Resonance Core/Protocol\).*?IV.X. CRC Registry \(`CR`\)')
if ($crSectionMatch.Success) {
    # This is a bit complex as it's prose, but let's try to find headers
    $crMatches = [regex]::Matches($crSectionMatch.Value, '(?m)^\s*(\*\*Orackla Nocticula\*\*|\*\*Madam Umeko\*\*|\*\*Dr. Lysandra\*\*)')
    foreach ($m in $crMatches) {
        $crEntries += [PSCustomObject]@{ Name = $m.Value.Replace('**', '').Trim() }
    }
}

# Logic to display
if ($Entity) {
    $foundAny = $false
    # Match in SAI
    $found = $saiEntries | Where-Object { $_.Designation -match $Entity -or $_.CommonName -match $Entity -or $_.ID -match $Entity }
    if ($found) {
        foreach ($f in $found) {
            Write-Host "`n=== SAI ENTRY #$($f.ID) ===" -ForegroundColor Green
            Write-Host "Designation: $($f.Designation)" -ForegroundColor Yellow
            Write-Host "Common Name: $($f.CommonName)" -ForegroundColor White
            Write-Host "Details:`n$($f.Details)" -ForegroundColor Gray
            $foundAny = $true
        }
    }

    # Match in AR
    $foundAr = $arTable | Where-Object { $_.Axiom -match $Entity -or $_.UseCases -match $Entity }
    if ($foundAr) {
        foreach ($f in $foundAr) {
            Write-Host "`n=== AXIOM: $($f.Axiom) ===" -ForegroundColor Cyan
            Write-Host "Use Cases: $($f.UseCases)" -ForegroundColor White
            Write-Host "Success Rate: $($f.SuccessRate)" -ForegroundColor Green
            Write-Host "Last Updated: $($f.LastUpdated)" -ForegroundColor Gray
            $foundAny = $true
        }
    }
    
    if (-not $foundAny) {
        Write-Host "❌ Entity '$Entity' not found in registries." -ForegroundColor Red
    }
}
elseif ($Registry -eq 'SAI') {
    Write-Host "`n=== SAI REGISTRY (DYNAMIC) ===" -ForegroundColor Yellow
    $saiEntries | Format-Table ID, Designation, CommonName -AutoSize
}
elseif ($Registry -eq 'AR') {
    Write-Host "`n=== AR REGISTRY (DYNAMIC) ===" -ForegroundColor Cyan
    $arTable | Format-Table Axiom, SuccessRate, LastUpdated -AutoSize
}
else {
    Write-Host "`n=== ALL REGISTRIES (DYNAMIC) ===" -ForegroundColor Magenta
    $saiEntries | Format-Table ID, Designation, CommonName -AutoSize
    $arTable | Format-Table Axiom, SuccessRate, LastUpdated -AutoSize
}

