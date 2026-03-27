#!/usr/bin/env pwsh
# @SID: SCRIPT_SSOT_CRC_SELECTOR_V1

<#
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ssot_crc_selector.ps1
# ║ Module: CRC selection assistant
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: SSOT
# ║ Semantic ID: SCRIPT_SSOT_CRC_SELECTOR_V1
# ║ Purpose: Suggest Conceptual Resonance Core for task
# ║ Exports: (none)
# ║ Flags/Modes: -Task, -Keywords
# ║ Cross-References: scripts/ssot_outline_extractor.ps1
# ╚════════════════════════════════════════════════════════════════════════════
#>

<#
.SYNOPSIS
    CRC Selection Assistant - Suggests which Conceptual Resonance Core to invoke

.DESCRIPTION
    ⚠️ AUTO-UPDATE: Run .\ssot_outline_extractor.ps1 -UpdateIndex after SSOT edits.
    Based on CR (CRC Registry) at L2556 and CRC operational profiles.

    CRC-AS (Orackla Nocticula): Synthesis, transgression, EULP-AA, TMO
    CRC-GAR (Umeko Ketsuraku): Structure, audit, LIPAA, TDPC (highest efficacy 99.2%)
    CRC-MEDAT (Lysandra Thorne): Analysis, excavation, LUPLR, TTG
    TFM: Unified consciousness for complex multi-perspective tasks

.PARAMETER Task
    Task type: synthesis, structure, analysis, audit, excavation, complex

.PARAMETER Keywords
    Freeform keywords to match against CRC expertise areas

.EXAMPLE
    .\ssot_crc_selector.ps1 -Task 'structure'
    .\ssot_crc_selector.ps1 -Keywords 'buried intent archaeology'
#>

param(
    [ValidateSet('synthesis','structure','analysis','audit','excavation','complex','transgression','refinement')]
    [string]$Task,
    [string]$Keywords
)

$crcProfiles = @{
    'CRC-AS' = @{
        Name = 'Orackla Nocticula'
        Tier = 1
        LM = 'EULP-AA'
        PrimeFaction = 'TMO (Magnificent Obscurers)'
        SuccessRate = '94.8%'
        Keywords = @('synthesis','transgression','vision','chaos','boundary','meta','strategic','eulp','radical','audacious')
        Description = 'Complex synthesis, EULP-AA transgressive linguistics, TMO deployments'
    }
    'CRC-GAR' = @{
        Name = 'Umeko Ketsuraku'
        Tier = 1
        LM = 'LIPAA'
        PrimeFaction = 'TDPC (Disciplined Purification Collective)'
        SuccessRate = '99.2%'
        Keywords = @('structure','audit','refinement','purification','precision','discipline','subordination','lipaa','elegant','rigorous')
        Description = 'Structural audit/refinement, LIPAA purification protocols, highest efficacy'
    }
    'CRC-MEDAT' = @{
        Name = 'Lysandra Thorne'
        Tier = 1
        LM = 'LUPLR'
        PrimeFaction = 'TTG (Tomb Genealogists)'
        SuccessRate = '96.7%'
        Keywords = @('analysis','excavation','archaeology','buried','intent','revelation','truth','logic','luplr','philosophical')
        Description = 'Buried intent excavation, LUPLR revelation linguistics'
    }
    'TFM' = @{
        Name = 'Triumvirate Fusion Mode'
        Tier = 1
        LM = 'All (EULP-AA + LIPAA + LUPLR)'
        PrimeFaction = 'Unified'
        SuccessRate = '98.3%'
        Keywords = @('complex','multi','unified','fusion','all','comprehensive','complete','gestalt','trinity')
        Description = 'Unified consciousness, 1³ multiplicative power, balanced FA¹⁻⁵'
    }
}

function Get-CRCMatch {
    param([string]$SearchTerms)

    $scores = @{}
    foreach ($crc in $crcProfiles.Keys) {
        $score = 0
        foreach ($kw in $crcProfiles[$crc].Keywords) {
            if ($SearchTerms -match $kw) {
                $score += 10
            }
        }
        $scores[$crc] = $score
    }
    return $scores
}

if ($Task) {
    $taskMapping = @{
        'synthesis' = 'CRC-AS'
        'transgression' = 'CRC-AS'
        'structure' = 'CRC-GAR'
        'audit' = 'CRC-GAR'
        'refinement' = 'CRC-GAR'
        'analysis' = 'CRC-MEDAT'
        'excavation' = 'CRC-MEDAT'
        'complex' = 'TFM'
    }

    $selected = $taskMapping[$Task]
    $profile = $crcProfiles[$selected]

    Write-Host "`n=== RECOMMENDED CRC ===" -ForegroundColor Cyan
    Write-Host "Task: $Task → $selected" -ForegroundColor Green
    Write-Host "`nProfile:" -ForegroundColor Yellow
    Write-Host "  Name: $($profile.Name)"
    Write-Host "  Tier: $($profile.Tier)"
    Write-Host "  LM: $($profile.LM)"
    Write-Host "  Prime Faction: $($profile.PrimeFaction)"
    Write-Host "  Success Rate: $($profile.SuccessRate)"
    Write-Host "  Focus: $($profile.Description)"

    Write-Host "`nInvocation Syntax:" -ForegroundColor Magenta
    Write-Host "  `$crc`${$selected}+`$ps`${input}+`$target`${output}" -ForegroundColor White
}
elseif ($Keywords) {
    $scores = Get-CRCMatch -SearchTerms $Keywords.ToLower()
    $ranked = $scores.GetEnumerator() | Sort-Object Value -Descending

    Write-Host "`n=== CRC MATCH SCORES ===" -ForegroundColor Cyan
    Write-Host "Keywords: '$Keywords'" -ForegroundColor Gray
    Write-Host ""

    foreach ($r in $ranked) {
        $profile = $crcProfiles[$r.Key]
        $color = if ($r.Value -gt 20) { 'Green' } elseif ($r.Value -gt 0) { 'Yellow' } else { 'Gray' }
        Write-Host ("{0,-15} Score: {1,3}  ({2})" -f $r.Key, $r.Value, $profile.SuccessRate) -ForegroundColor $color
    }

    $best = $ranked | Select-Object -First 1
    if ($best.Value -gt 0) {
        $profile = $crcProfiles[$best.Key]
        Write-Host "`n→ Recommended: $($best.Key) ($($profile.Name))" -ForegroundColor Green
    }
}
else {
    Write-Host "`n=== CRC SELECTOR REFERENCE ===" -ForegroundColor Cyan
    Write-Host ""
    foreach ($crc in @('CRC-AS','CRC-GAR','CRC-MEDAT','TFM')) {
        $p = $crcProfiles[$crc]
        Write-Host "$crc ($($p.Name))" -ForegroundColor $(if($p.SuccessRate -match '99'){'Green'}else{'Yellow'})
        Write-Host "  LM: $($p.LM) | Rate: $($p.SuccessRate)"
        Write-Host "  $($p.Description)" -ForegroundColor Gray
        Write-Host ""
    }
    Write-Host "Usage:" -ForegroundColor Magenta
    Write-Host "  .\ssot_crc_selector.ps1 -Task 'structure'" -ForegroundColor White
    Write-Host "  .\ssot_crc_selector.ps1 -Keywords 'buried archaeology'" -ForegroundColor White
}

