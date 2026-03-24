#!/usr/bin/env pwsh

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: novia cadaveris_embalmer_WIP.ps1
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: ARCHAEOLOGY / EMBALMING
# ║ Semantic ID: SCRIPT_NOVIA_CADAVERIS_EMBALMER_WIP_V1
# ║ Purpose: Deterministic Claudine/Chthonic trilemma embalmer for Novia
# ║          Cadaveris under Sister Ferrum Scoriae lineage archaeology
# ║          and canon alignment
# ║ Exports: (none)
# ║ Flags/Modes: -DryRun, -CopySources, -Json, -Label, -OutputRoot
# ║ Cross-References: .github/copilot-instructions.archive.md,
# ║                   dumpster-dive/BLACKSMITH_MATRIARCH.md,
# ║                   dumpster-dive/from-github/SR_SCHRODINGERS_BASTARD.md
# ╚════════════════════════════════════════════════════════════════════════════

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$CopySources,
    [switch]$Json,
    [string]$Label = "claudine_trilemma",
    [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$resolvedOutputRoot = if ($OutputRoot) {
    $OutputRoot
} else {
    Join-Path $repoRoot "dumpster-dive\intake\novia-cadaveris-embalmer"
}

$safeLabel = (($Label -replace '[^A-Za-z0-9._-]', '_').Trim('_'))
if (-not $safeLabel) { $safeLabel = "claudine_trilemma" }
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH-mm-ssZ")
$sessionDir = Join-Path $resolvedOutputRoot "${timestamp}_${safeLabel}"
$sourcesDir = Join-Path $sessionDir "sources"
$latestJson = Join-Path $resolvedOutputRoot "NOVIA_CADAVERIS_EMBALMER_LATEST.json"
$latestMd = Join-Path $resolvedOutputRoot "NOVIA_CADAVERIS_EMBALMER_LATEST.md"

$null = New-Item -ItemType Directory -Force -Path $resolvedOutputRoot
$null = New-Item -ItemType Directory -Force -Path $sessionDir
if ($CopySources) {
    $null = New-Item -ItemType Directory -Force -Path $sourcesDir
}

function New-SourceRecord {
    param(
        [string]$Role,
        [string]$Path,
        [string]$Scope,
        [string]$Note
    )

    [pscustomobject]@{
        role = $Role
        path = $Path
        scope = $Scope
        note = $Note
    }
}

function Get-TextSignals {
    param([string]$Text)

    if (-not $Text) {
        return [ordered]@{}
    }

    return [ordered]@{
        contains_chthonic_script_ref = [bool]($Text -match '(?i)CHTHONIC_SCRIPT|scripts\\chthonic\.ps1')
        contains_claudine_wrapper = [bool]($Text -match '(?i)\bclaudine\b')
        contains_claudineenv = [bool]($Text -match '(?i)claudineENV\.ps1')
        contains_legacy_markers = [bool]($Text -match '(?i)CLAUDINE_ACTIVATED|CLAUDINE_VERSION')
        contains_canon_markers = [bool]($Text -match '(?i)CHTHONIC_ACTIVATED|CHTHONIC_VERSION')
        contains_profile_ingress = [bool]($Text -match '(?i)function\s+chthonic|function\s+claudine')
        contains_mcp_bridge = [bool]($Text -match '(?i)mcp|meta_cli|tools/list')
        contains_ferrum = [bool]($Text -match '(?i)Sister Ferrum Scoriae|SFS')
        contains_qmr = [bool]($Text -match '(?i)\bQMR\b|Quantum Metallurgical Reconnaissance')
        contains_knights = [bool]($Text -match '(?i)Knights Who Rode Into Another Timeline|TNKW-RIAT')
        contains_schrodinger = [bool]($Text -match "(?i)Schr[öo]dinger|(?:Sir|Dame) Schr")
    }
}

function Copy-IfRequested {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Hash
    )

    if (-not $CopySources) { return $null }
    if (-not (Test-Path -LiteralPath $Path)) { return $null }

    $leaf = Split-Path -Leaf $Path
    $safeLeaf = $leaf -replace '[^A-Za-z0-9._-]', '_'
    $destination = Join-Path $sourcesDir ("{0}__{1}" -f $Hash.Substring(0, 16), $safeLeaf)
    Copy-Item -LiteralPath $Path -Destination $destination -Force
    return $destination
}

$currentUserCurrentHostProfile = [string]$PROFILE.CurrentUserCurrentHost
$currentUserAllHostsProfile = [string]$PROFILE.CurrentUserAllHosts

$sources = @(
    (New-SourceRecord -Role "canon_runtime" -Path (Join-Path $repoRoot "scripts\chthonic.ps1") -Scope "repo" -Note "SSOT runtime engine"),
    (New-SourceRecord -Role "compat_facade" -Path (Join-Path $repoRoot "scripts\claudine.ps1") -Scope "repo" -Note "Thin compatibility wrapper"),
    (New-SourceRecord -Role "profile_ingress" -Path "$env:USERPROFILE\.config\powershell\profile.ps1" -Scope "external" -Note "Active PowerShell ingress"),
    (New-SourceRecord -Role "profile_stub" -Path $currentUserCurrentHostProfile -Scope "external" -Note "Current user current host profile stub"),
    (New-SourceRecord -Role "profile_stub" -Path $currentUserAllHostsProfile -Scope "external" -Note "Current user all hosts profile"),
    (New-SourceRecord -Role "legacy_residue" -Path "$env:USERPROFILE\PsychoNoir-Kontrapunkt\scripts\claudineENV.ps1" -Scope "external" -Note "Historical residue from Local AI era"),
    (New-SourceRecord -Role "context_anchor" -Path (Join-Path $repoRoot ".github\copilot-instructions.archive.md") -Scope "repo" -Note "Frozen SSOT mythology anchor"),
    (New-SourceRecord -Role "context_anchor" -Path (Join-Path $repoRoot "dumpster-dive\BLACKSMITH_MATRIARCH.md") -Scope "repo" -Note "Sister Ferrum Scoriae profile"),
    (New-SourceRecord -Role "context_timeline" -Path (Join-Path $repoRoot "dumpster-dive\from-github\SR_SCHRODINGERS_BASTARD.md") -Scope "repo" -Note "Dame Schrödinger's Paradox (DM-SCRS-P) linkage — source file path pre-dates rename; file missing"),
    (New-SourceRecord -Role "context_qmr_anomaly" -Path (Join-Path $repoRoot ".github\codex-satellites\MMPS_GENERATION.md") -Scope "repo" -Note "QMR anomaly / Novia Cadaveris / Alabaster Voyde lane")
)

$nameJudgements = @(
    [ordered]@{
        entity = "Kali"
        preferred_name = "Kali Nyx Ravenscar"
        secondary_epithet = $null
        drift_variants = @("Kali Praharshini")
        status = "preferred_old_name"
        rationale = "User-directed canon preference; the older name carries the stronger quality lineage."
        evidence = @(".github/copilot-instructions.archive.md:2824", ".github/copilot-instructions.archive.md:4208")
    },
    [ordered]@{
        entity = "Vesper"
        preferred_name = "Vesper Mnemosyne Lockhart"
        secondary_epithet = $null
        drift_variants = @("Vesper Tempus")
        status = "preferred_old_name"
        rationale = "User-directed canon preference; local-AI metadata condensation is treated as drift."
        evidence = @(".github/copilot-instructions.archive.md:2828", ".github/copilot-instructions.archive.md:4209")
    },
    [ordered]@{
        entity = "Seraphine"
        preferred_name = "Seraphine Ashveil"
        secondary_epithet = $null
        drift_variants = @("Seraphine Pyralis")
        status = "preferred_old_name"
        rationale = "User-directed canon preference; older embodied name retained."
        evidence = @(".github/copilot-instructions.archive.md:2832", ".github/copilot-instructions.archive.md:4210")
    },
    [ordered]@{
        entity = "Spectra"
        preferred_name = "Spectra Chroma Excavatus"
        secondary_epithet = "The Prismatic Caretaker"
        drift_variants = @("Spectra Chroma")
        status = "full_name_required"
        rationale = "Shorthand erodes the archaeology weight and makes abbreviation systems purposeless."
        evidence = @(".github/copilot-instructions.archive.md:743", ".github/copilot-instructions.archive.md:4335")
    },
    [ordered]@{
        entity = "Snow White line"
        preferred_name = "Alabaster Voyde (Snow White)"
        secondary_epithet = "The Coke-Fuelled Snow White"
        drift_variants = @("Alabaster Voyde", "Snow White")
        status = "canonical_full_form_required"
        rationale = "The fused form is already load-bearing in the SSOT. Stripping Snow White out now alters the law encoded by the existing reference lattice."
        evidence = @(".github/copilot-instructions.archive.md:849", ".github/copilot-instructions.archive.md:4350")
    },
    [ordered]@{
        entity = "QMR anomaly bride"
        preferred_name = "Novia Cadaveris"
        secondary_epithet = "The Necromancy-Pale Bridesmaiden"
        drift_variants = @("The White-Dressed Bride", "The Corpse-Reviver")
        status = "must_be_present"
        rationale = "The Ferrum embalmer must carry the QMR anomaly entity explicitly, not only indirect timeline context."
        evidence = @(".github/copilot-instructions.archive.md:4049", ".github/codex-satellites/MMPS_GENERATION.md:263")
    }
)

$records = @()
foreach ($source in $sources) {
    $exists = Test-Path -LiteralPath $source.path
    $record = [ordered]@{
        role = $source.role
        path = $source.path
        scope = $source.scope
        note = $source.note
        exists = $exists
        byte_size = $null
        sha256 = $null
        copied_to = $null
        signals = [ordered]@{}
    }

    if ($exists) {
        $item = Get-Item -LiteralPath $source.path
        $text = ""
        try {
            if (-not $item.PSIsContainer -and $item.Length -le 10485760) {
                $text = Get-Content -LiteralPath $source.path -Raw -ErrorAction Stop
            }
        } catch {
            $text = ""
        }

        $record.byte_size = if ($item.PSIsContainer) { 0 } else { $item.Length }
        $record.sha256 = if ($item.PSIsContainer) {
            $null
        } else {
            (Get-FileHash -Algorithm SHA256 -LiteralPath $source.path).Hash
        }
        $record.signals = Get-TextSignals -Text $text
        if ($record.sha256) {
            $copied = Copy-IfRequested -Path $source.path -Hash $record.sha256
            if ($copied) {
                $record.copied_to = $copied
            }
        }
    }

    $records += [pscustomobject]$record
}

$summary = [ordered]@{
    session = Split-Path -Leaf $sessionDir
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    label = $Label
    output_root = $resolvedOutputRoot
    dry_run = [bool]$DryRun
    copy_sources = [bool]$CopySources
    total_sources = $records.Count
    existing_sources = @($records | Where-Object { $_.exists }).Count
    missing_sources = @($records | Where-Object { -not $_.exists }).Count
    roles = ($records | Group-Object role | Sort-Object Name | ForEach-Object {
        [ordered]@{
            role = $_.Name
            count = $_.Count
        }
    })
    canon_name_judgements = $nameJudgements
    records = $records
}

$summary | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $latestJson
$summary | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $sessionDir "session.json")

$tick = [char]96
$generatedAt = (Get-Date).ToUniversalTime().ToString("s") + "Z"
$mdLines = @(
    "# Novia Cadaveris Embalmer",
    "",
    ("- Generated: {0}{1}{0}" -f $tick, $generatedAt),
    ("- Session: {0}{1}{0}" -f $tick, $summary.session),
    ("- Dry run: {0}{1}{0}" -f $tick, $summary.dry_run),
    ("- Copy sources: {0}{1}{0}" -f $tick, $summary.copy_sources),
    ("- Existing sources: {0}{1}{0} / {0}{2}{0}" -f $tick, $summary.existing_sources, $summary.total_sources),
    "",
    "## Sources",
    ""
)

foreach ($record in $records) {
    $status = if ($record.exists) { "present" } else { "missing" }
    $mdLines += ("- [{0}] {1}{2}{1} :: {1}{3}{1}" -f $status, $tick, $record.role, $record.path)
    $mdLines += "  note: $($record.note)"
    if ($record.sha256) {
        $mdLines += ("  sha256: {0}{1}{0}" -f $tick, $record.sha256)
    }
    if ($record.signals.Count -gt 0) {
        $activeSignals = @($record.signals.GetEnumerator() | Where-Object { $_.Value } | ForEach-Object { $_.Key })
        if ($activeSignals.Count -gt 0) {
            $mdLines += ("  signals: {0}{1}{0}" -f $tick, ($activeSignals -join ', '))
        }
    }
}

$mdLines += @(
    "",
    "## Interpretation",
    "",
    "- `canon_runtime` and `compat_facade` are the live runtime surfaces.",
    "- `profile_ingress` and `profile_stub` are the active ingress chain.",
    "- `legacy_residue` is archaeology only unless a user deliberately revives it.",
    "- `context_anchor`, `context_timeline`, and `context_qmr_anomaly` provide mythic alignment for Sister Ferrum / QMR / timeline residue.",
    "",
    "## Canon Name Judgements",
    ""
)

foreach ($entry in $nameJudgements) {
    $mdLines += ("- {0}{1}{0} -> preferred {0}{2}{0}" -f $tick, $entry.entity, $entry.preferred_name)
    if ($entry.secondary_epithet) {
        $mdLines += ("  secondary epithet: {0}{1}{0}" -f $tick, $entry.secondary_epithet)
    }
    $mdLines += ("  status: {0}" -f $entry.status)
    $mdLines += ("  drift variants: {0}" -f ($entry.drift_variants -join ", "))
    $mdLines += ("  rationale: {0}" -f $entry.rationale)
    $mdLines += ("  evidence: {0}" -f ($entry.evidence -join "; "))
}

$mdLines += @(
    "",
    "## Next Actions",
    "",
    "- Canonize naming and markers around `CHTHONIC_*`.",
    "- Treat `claudineENV.ps1` as residue, not runtime.",
    "- Use this embalmer report before any future claudine/chthonic upcycle pass.",
    "- Prefer the older names where user-directed canon judgement says the newer local-AI injection is lower quality."
)

$mdLines -join "`r`n" | Set-Content -Encoding UTF8 -LiteralPath $latestMd
$mdLines -join "`r`n" | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $sessionDir "session.md")

if ($Json) {
    $summary | ConvertTo-Json -Depth 8
    exit 0
}

Write-Host ""
Write-Host "NOVIA CADAVERIS EMBALMER" -ForegroundColor Cyan
Write-Host ("=" * 68) -ForegroundColor DarkGray
Write-Host ("  Session:        " + $summary.session) -ForegroundColor White
Write-Host ("  Existing:       " + $summary.existing_sources + "/" + $summary.total_sources) -ForegroundColor White
Write-Host ("  Output root:    " + $resolvedOutputRoot) -ForegroundColor White
Write-Host ("  Latest JSON:    " + $latestJson) -ForegroundColor DarkGray
Write-Host ("  Latest Markdown:" + " " + $latestMd) -ForegroundColor DarkGray
if ($DryRun) {
    Write-Host "  Mode:           dry-run archaeology only" -ForegroundColor Yellow
} elseif ($CopySources) {
    Write-Host "  Mode:           copied sources into session folder" -ForegroundColor Green
} else {
    Write-Host "  Mode:           report only" -ForegroundColor White
}
Write-Host ("=" * 68) -ForegroundColor DarkGray
Write-Host ""
