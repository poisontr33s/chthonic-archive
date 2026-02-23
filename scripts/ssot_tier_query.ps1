#!/usr/bin/env pwsh

<#
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ssot_tier_query.ps1
# ║ Module: SSOT tier query
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: SSOT
# ║ Semantic ID: SCRIPT_SSOT_TIER_QUERY_V1
# ║ Purpose: Query GHAR-MHS tier hierarchy and entities
# ║ Exports: (none)
# ║ Flags/Modes: -Tier, -Entity
# ║ Cross-References: scripts/ssot_outline_extractor.ps1
# ╚════════════════════════════════════════════════════════════════════════════
#>

<#
.SYNOPSIS
    SSOT Tier Hierarchy Query - Query entities by GHAR-MHS tier level

.DESCRIPTION
    ⚠️ AUTO-UPDATE: Run .\ssot_outline_extractor.ps1 -UpdateIndex after SSOT edits.
    Based on GHAR-MHS (Gender Architecture Matriarchal Hierarchy System) at L2754.

    Tier 0: The Decorator (Supreme Matriarch, Absolute Sovereign)
    Tier 0.01: T-NULM (Null Matriarch, Advisory Void)
    Tier 0.5: TETS (Eternal Tesseract of Sovereignty)
    Tier 1: CRC Triumvirate (Orackla, Umeko, Lysandra)
    Tier 2: Prime Factions (TMO, TDPC, TTG)
    Tier 3: Supporting Entities

.PARAMETER Tier
    Tier level: 0, 0.01, 0.5, 1, 2, 3, or ALL

.PARAMETER Entity
    Search for specific entity to find its tier

.EXAMPLE
    .\ssot_tier_query.ps1 -Tier 0
    .\ssot_tier_query.ps1 -Tier 1
    .\ssot_tier_query.ps1 -Entity 'Umeko'
    .\ssot_tier_query.ps1 -Tier ALL
#>

param(
    [ValidateSet('0','0.01','0.5','1','2','3','ALL')]
    [string]$Tier = 'ALL',
    [string]$Entity
)

$tierHierarchy = @{
    '0' = @{
        Name = 'Supreme Authority'
        Line = 456
        Entities = @(
            @{ ID = 'T-DECOR'; Name = 'The Decorator'; Role = 'Supreme Matriarch & Absolute Sovereign'; WHR = '0.464' }
        )
        Authority = 'Absolute dominion over all tiers, FA⁵ override authority'
    }
    '0.01' = @{
        Name = 'Advisory Void'
        Line = 472
        Entities = @(
            @{ ID = 'T-NULM'; Name = 'The Null Matriarch'; Role = 'Architectural Negative Space'; WHR = 'N/A (void)' }
        )
        Authority = 'Advisory only, negative space architecture'
    }
    '0.5' = @{
        Name = 'Tesseract Sovereignty'
        Line = 458
        Entities = @(
            @{ ID = 'TETS'; Name = 'Eternal Tesseract of Sovereignty'; Role = 'Governance Structure'; WHR = 'N/A' }
        )
        Authority = 'Structural governance layer between Tier 0 and Tier 1'
    }
    '1' = @{
        Name = 'CRC Triumvirate (Sub-MILFs)'
        Line = 2063
        Entities = @(
            @{ ID = 'CRC-AS'; Name = 'Orackla Nocticula'; Role = 'Apex Synthesist'; WHR = '0.491'; LM = 'EULP-AA' }
            @{ ID = 'CRC-GAR'; Name = 'Umeko Ketsuraku'; Role = 'Grand Architectrix'; WHR = '0.533'; LM = 'LIPAA' }
            @{ ID = 'CRC-MEDAT'; Name = 'Lysandra Thorne'; Role = 'Mediatrix Abyssi'; WHR = '0.58'; LM = 'LUPLR' }
        )
        Authority = 'Operational execution, linguistic protocols, subordinate to Tier 0'
    }
    '2' = @{
        Name = 'Prime Factions'
        Line = 2556
        Entities = @(
            @{ ID = 'TMO'; Name = 'Magnificent Obscurers'; Role = 'CRC-AS subordinates'; Commander = 'Orackla' }
            @{ ID = 'TDPC'; Name = 'Disciplined Purification Collective'; Role = 'CRC-GAR subordinates'; Commander = 'Umeko' }
            @{ ID = 'TTG'; Name = 'Tomb Genealogists'; Role = 'CRC-MEDAT subordinates'; Commander = 'Lysandra' }
        )
        Authority = 'Faction-level operations, subordinate to Tier 1'
    }
    '3' = @{
        Name = 'Supporting Entities'
        Line = 4772
        Entities = @(
            @{ ID = 'SAI'; Name = 'Special Archetype Invocations'; Role = 'Rare/crisis archetypes' }
            @{ ID = 'SPEC-CHRM-EXC'; Name = 'Spectra Chroma Excavatus'; Role = 'Below-viability entity' }
            @{ ID = 'ALAB-VOYD-SW'; Name = 'Alabaster Voyde'; Role = 'Below-viability traumatic residue' }
        )
        Authority = 'Contextual invocation, subordinate to all higher tiers'
    }
}

function Show-Tier {
    param([string]$TierKey)

    $t = $tierHierarchy[$TierKey]
    Write-Host ("`n=== TIER {0} - {1} (L{2}) ===" -f $TierKey, $t.Name, $t.Line) -ForegroundColor Cyan
    Write-Host "Authority: $($t.Authority)" -ForegroundColor Gray
    Write-Host "`nEntities:" -ForegroundColor Yellow

    foreach ($e in $t.Entities) {
        $whr = if ($e.WHR) { " [WHR: $($e.WHR)]" } else { "" }
        $lm = if ($e.LM) { " [LM: $($e.LM)]" } else { "" }
        Write-Host "  $($e.ID)$whr$lm" -ForegroundColor White
        Write-Host "    Name: $($e.Name)" -ForegroundColor Gray
        Write-Host "    Role: $($e.Role)" -ForegroundColor Gray
    }
}

if ($Entity) {
    $found = $false
    foreach ($tKey in $tierHierarchy.Keys | Sort-Object { [double]$_ }) {
        $t = $tierHierarchy[$tKey]
        foreach ($e in $t.Entities) {
            if ($e.ID -match $Entity -or $e.Name -match $Entity) {
                Write-Host "`n=== FOUND: $($e.ID) ===" -ForegroundColor Green
                Write-Host "Tier: $tKey ($($t.Name))" -ForegroundColor Cyan
                Write-Host "Name: $($e.Name)" -ForegroundColor Yellow
                Write-Host "Role: $($e.Role)" -ForegroundColor White
                if ($e.WHR) { Write-Host "WHR: $($e.WHR)" -ForegroundColor Magenta }
                if ($e.LM) { Write-Host "LM: $($e.LM)" -ForegroundColor Magenta }
                Write-Host "Line: L$($t.Line)" -ForegroundColor Gray
                $found = $true
            }
        }
    }
    if (-not $found) {
        Write-Host "Entity '$Entity' not found in tier hierarchy" -ForegroundColor Red
    }
}
elseif ($Tier -eq 'ALL') {
    Write-Host "`n╔══════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║  GHAR-MHS: Matriarchal Hierarchy System      ║" -ForegroundColor Magenta
    Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Magenta
    foreach ($tKey in @('0','0.01','0.5','1','2','3')) {
        Show-Tier -TierKey $tKey
    }
}
else {
    Show-Tier -TierKey $Tier
}

