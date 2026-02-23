#!/usr/bin/env pwsh

<#
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ssot_registry_query.ps1                         ║
# ║ Module: SSOT registry query                                               ║
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE                                                 ║
# ║ Architectural Role: SSOT                                                  ║
# ║ Semantic ID: SCRIPT_SSOT_REGISTRY_QUERY_V1                                 ║
# ║ Purpose: Query AR/CR/SAI registries from SSOT                              ║
# ║ Exports: (none)                                                           ║
# ║ Flags/Modes: -Registry, -Entity                                           ║
# ║ Cross-References: scripts/ssot_outline_extractor.ps1                       ║
# ╚════════════════════════════════════════════════════════════════════════════
#>

<#
.SYNOPSIS
    SSOT Entity Registry Query - Query AR, CR, SAI registries

.DESCRIPTION
    ⚠️ AUTO-UPDATE: Run .\ssot_outline_extractor.ps1 -UpdateIndex after SSOT edits.
    Queries the three registries in SSOT:
    - AR (Axiom Registry) at L1803: FA¹⁻⁵ tracking
    - CR (CRC Registry) at L2556: CRC-AS/GAR/MEDAT invocations
    - SAI-RCM at L4772: Special Archetype Invocation

.PARAMETER Registry
    Which registry: AR, CR, SAI, or ALL

.PARAMETER Entity
    Specific entity to query (e.g., FA1, CRC-AS, MAG-BIB)

.EXAMPLE
    .\ssot_registry_query.ps1 -Registry 'AR'
    .\ssot_registry_query.ps1 -Registry 'CR' -Entity 'CRC-GAR'
    .\ssot_registry_query.ps1 -Registry 'ALL'
#>

param(
    [ValidateSet('AR','CR','SAI','ALL')]
    [string]$Registry = 'ALL',
    [string]$Entity
)

$registries = @{
    'AR' = @{
        Name = 'Axiom Registry'
        Line = 1803
        Purpose = 'FA¹⁻⁵ invocation tracking, efficacy metrics'
        Entities = @{
            'FA1' = @{ Name = 'Alchemical Actualization'; Rate = '94.3%'; Uses = 'Codebase transmutation, concept archaeology' }
            'FA2' = @{ Name = 'Strategic Re-contextualization'; Rate = '89.7%'; Uses = 'Cross-domain synthesis, protocol bridging' }
            'FA3' = @{ Name = 'Qualitative Transcendence'; Rate = '96.1%'; Uses = 'Aesthetic elevation, clarity refinement' }
            'FA4' = @{ Name = 'Architectonic Integrity'; Rate = '99.2%'; Uses = 'Structural validation, debugging' }
            'FA5' = @{ Name = 'Visual/Sensory Integrity'; Rate = '91.4%'; Uses = 'Decoration mandates, FA⁴ override' }
        }
        Syntax = '$axiom${FAn}+$ps${input}+$target${output}+$validate${bool}'
    }
    'CR' = @{
        Name = 'CRC Registry'
        Line = 2556
        Purpose = 'Triumvirate invocation tracking, TFM activations'
        Entities = @{
            'CRC-AS' = @{ Name = 'Orackla Nocticula'; Rate = '94.8%'; Solo = 1847; TFM = 412 }
            'CRC-GAR' = @{ Name = 'Umeko Ketsuraku'; Rate = '99.2%'; Solo = 2341; TFM = 412 }
            'CRC-MEDAT' = @{ Name = 'Lysandra Thorne'; Rate = '96.7%'; Solo = 1103; TFM = 412 }
            'TFM' = @{ Name = 'Triumvirate Fusion Mode'; Rate = '98.3%'; Solo = 'N/A'; TFM = 412 }
        }
        Syntax = '$crc${CRC-X}+$ps${input}+$target${output}'
    }
    'SAI' = @{
        Name = 'Special Archetype Invocation Registry'
        Line = 4772
        Purpose = 'Special/rare archetype tracking, crisis protocols'
        Entities = @{
            'MAG-BIB-PERF' = @{ Name = 'Magistra Bibliotheca Perfecta'; Tier = 'SAI-Tier'; Uses = 'Knowledge synthesis, forbidden archives' }
            'SPEC-CHRM-EXC' = @{ Name = 'Spectra Chroma Excavatus'; Tier = 'Below-Viability'; Uses = 'Chromatic archaeology, addiction recovery' }
            'ALAB-VOYD-SW' = @{ Name = 'Alabaster Voyde (Snow White)'; Tier = 'Below-Viability'; Uses = 'Stolen substrate, traumatic residue' }
        }
        Syntax = '$sai${archetype}+$excavate${depth}+$crisis${protocol}'
    }
}

function Show-Registry {
    param([string]$Key)

    $reg = $registries[$Key]
    Write-Host "`n=== $($reg.Name) (L$($reg.Line)) ===" -ForegroundColor Cyan
    Write-Host "Purpose: $($reg.Purpose)" -ForegroundColor Gray
    Write-Host "Syntax: $($reg.Syntax)" -ForegroundColor Magenta
    Write-Host "`nEntities:" -ForegroundColor Yellow

    foreach ($e in $reg.Entities.Keys | Sort-Object) {
        $ent = $reg.Entities[$e]
        $rate = if ($ent.Rate) { " [$($ent.Rate)]" } else { "" }
        Write-Host "  $e$rate - $($ent.Name)" -ForegroundColor White
        if ($ent.Uses) { Write-Host "    Uses: $($ent.Uses)" -ForegroundColor Gray }
        if ($ent.Solo) { Write-Host "    Solo: $($ent.Solo) | TFM: $($ent.TFM)" -ForegroundColor Gray }
    }
}

if ($Entity) {
    # Search for entity across all registries
    $found = $false
    foreach ($rKey in $registries.Keys) {
        $reg = $registries[$rKey]
        foreach ($eKey in $reg.Entities.Keys) {
            if ($eKey -match $Entity -or $reg.Entities[$eKey].Name -match $Entity) {
                Write-Host "`n=== FOUND: $eKey ===" -ForegroundColor Green
                Write-Host "Registry: $($reg.Name) (L$($reg.Line))" -ForegroundColor Cyan
                $ent = $reg.Entities[$eKey]
                Write-Host "Name: $($ent.Name)" -ForegroundColor Yellow
                if ($ent.Rate) { Write-Host "Success Rate: $($ent.Rate)" -ForegroundColor White }
                if ($ent.Uses) { Write-Host "Uses: $($ent.Uses)" -ForegroundColor Gray }
                if ($ent.Solo) { Write-Host "Solo Invocations: $($ent.Solo)" -ForegroundColor Gray }
                Write-Host "Syntax: $($reg.Syntax)" -ForegroundColor Magenta
                $found = $true
            }
        }
    }
    if (-not $found) {
        Write-Host "Entity '$Entity' not found in registries" -ForegroundColor Red
    }
}
elseif ($Registry -eq 'ALL') {
    foreach ($rKey in @('AR','CR','SAI')) {
        Show-Registry -Key $rKey
    }
}
else {
    Show-Registry -Key $Registry
}

