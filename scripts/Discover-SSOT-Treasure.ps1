#!/usr/bin/env pwsh
#
# @SID: SCRIPT_DISCOVER_SSOT_TREASURE_V1
# @Type: ANALYSIS
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Requires -Version 7.0
#

#Requires -Version 7.0

<#
.SYNOPSIS
    SSOT Treasure Chamber Discovery - Find all .md files with semantic lineage markers
    
.DESCRIPTION
    Scans chthonic-archive for markdown files containing ANKH/ASC/SSOT markers.
    Classifies by rarity (unique patterns), invariance (core governance), and density.
    
.PARAMETER ScanPath
    Root path to scan (defaults to repository root)
    
.PARAMETER OutputFormat
    json | table | markdown (default: table)
    
.PARAMETER MinDensity
    Minimum ANKH marker density to include (default: 0.0 = all files)
    
.EXAMPLE
    .\Discover-SSOT-Treasure.ps1
    
.EXAMPLE
    .\Discover-SSOT-Treasure.ps1 -OutputFormat json -MinDensity 0.5
#>

[CmdletBinding()]
param(
    [Parameter()]
    [string]$ScanPath = (Split-Path -Parent $PSScriptRoot),
    
    [Parameter()]
    [ValidateSet('json', 'table', 'markdown')]
    [string]$OutputFormat = 'table',
    
    [Parameter()]
    [ValidateRange(0.0, 1.0)]
    [double]$MinDensity = 0.0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ============================================================================
# MARKER DEFINITIONS (ANKH/ASC/SSOT Semantic Indicators)
# ============================================================================

$MARKERS = @{
    # Core governance
    'SSOT'           = @{ Pattern = '\bSSOT\b'; Weight = 1.0; Category = 'Governance' }
    'ANKH'           = @{ Pattern = '\bANKH\b'; Weight = 1.0; Category = 'Governance' }
    'ASC'            = @{ Pattern = '\bASC\b'; Weight = 0.8; Category = 'Framework' }
    
    # Foundational axioms
    'FA¹'            = @{ Pattern = 'FA¹|FA1'; Weight = 0.9; Category = 'Axiom' }
    'FA²'            = @{ Pattern = 'FA²|FA2'; Weight = 0.9; Category = 'Axiom' }
    'FA³'            = @{ Pattern = 'FA³|FA3'; Weight = 0.9; Category = 'Axiom' }
    'FA⁴'            = @{ Pattern = 'FA⁴|FA4'; Weight = 0.9; Category = 'Axiom' }
    'FA⁵'            = @{ Pattern = 'FA⁵|FA5'; Weight = 0.9; Category = 'Axiom' }
    
    # Triumvirate entities
    'Orackla'        = @{ Pattern = '\bOrackla\b'; Weight = 0.7; Category = 'Entity-T1' }
    'Umeko'          = @{ Pattern = '\bUmeko\b'; Weight = 0.7; Category = 'Entity-T1' }
    'Lysandra'       = @{ Pattern = '\bLysandra\b'; Weight = 0.7; Category = 'Entity-T1' }
    'The Decorator'  = @{ Pattern = 'The Decorator|T-DECOR'; Weight = 0.8; Category = 'Entity-T0.5' }
    'Null Matriarch' = @{ Pattern = 'Null Matriarch|T-NULM'; Weight = 0.6; Category = 'Entity-T0' }
    
    # Protocols
    'DAFP'           = @{ Pattern = '\bDAFP\b'; Weight = 0.7; Category = 'Protocol' }
    'PRISM'          = @{ Pattern = '\bPRISM\b'; Weight = 0.6; Category = 'Protocol' }
    'MMPS'           = @{ Pattern = '\bMMPS\b'; Weight = 0.6; Category = 'Protocol' }
    'TPEF'           = @{ Pattern = '\bTPEF\b'; Weight = 0.6; Category = 'Protocol' }
    
    # Rare/special markers
    '$matriarch$'    = @{ Pattern = '\$matriarch\$'; Weight = 0.5; Category = 'Invocation' }
    '$body$'         = @{ Pattern = '\$body\$'; Weight = 0.5; Category = 'Invocation' }
    '$grimoire$'     = @{ Pattern = '\$grimoire\$'; Weight = 0.5; Category = 'Invocation' }
    'ET-S'           = @{ Pattern = '\bET-S\b'; Weight = 0.6; Category = 'Concept' }
    'MURI'           = @{ Pattern = '\bMURI\b'; Weight = 0.7; Category = 'Concept' }
}

# ============================================================================
# SCANNING FUNCTIONS
# ============================================================================

function Get-MarkdownFiles {
    param([string]$Path)
    
    Get-ChildItem -Path $Path -Filter '*.md' -Recurse -File |
        Where-Object { 
            # Exclude .git, node_modules, .venv, build artifacts
            $_.FullName -notmatch '\.git|node_modules|\.venv|build|dist|\.next'
        }
}

function Measure-SemanticDensity {
    param(
        [string]$FilePath,
        [hashtable]$Markers
    )
    
    $content = Get-Content -Path $FilePath -Raw -ErrorAction SilentlyContinue
    if (-not $content) {
        # Return zero-density object for empty/unreadable files (preserve measurement)
        return [PSCustomObject]@{
            Path       = $FilePath
            RelPath    = [System.IO.Path]::GetRelativePath($ScanPath, $FilePath)
            Lines      = 0
            Words      = 0
            Density    = 0.0
            MarkerHits = @{}
            Categories = @()
        }
    }
    
    $lineCount = ($content -split "`n").Count
    $wordCount = ($content -split '\s+').Count
    
    $hits = @{}
    $totalWeight = 0.0
    
    foreach ($markerName in $Markers.Keys) {
        $marker = $Markers[$markerName]
        $matches = [regex]::Matches($content, $marker.Pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
        
        if ($matches.Count -gt 0) {
            $hits[$markerName] = @{
                Count    = $matches.Count
                Weight   = $marker.Weight
                Category = $marker.Category
            }
            $totalWeight += ($matches.Count * $marker.Weight)
        }
    }
    
    # Density = weighted marker count / 100 words
    $density = if ($wordCount -gt 0) { ($totalWeight / $wordCount) * 100 } else { 0 }
    
    [PSCustomObject]@{
        Path       = $FilePath
        RelPath    = [System.IO.Path]::GetRelativePath($ScanPath, $FilePath)
        Lines      = $lineCount
        Words      = $wordCount
        Density    = [math]::Round($density, 4)
        MarkerHits = $hits
        Categories = ($hits.Values.Category | Select-Object -Unique | Sort-Object)
    }
}

function Get-Rarity {
    param([PSCustomObject]$FileData, [array]$AllFiles)
    
    $markerNames = $FileData.MarkerHits.Keys
    $uniqueCount = 0
    
    foreach ($marker in $markerNames) {
        $filesWithMarker = @($AllFiles | Where-Object { $_.MarkerHits.ContainsKey($marker) })
        if ($filesWithMarker.Count -le 3) { $uniqueCount++ }
    }
    
    if ($uniqueCount -ge 3) { return 'RARE' }
    if ($uniqueCount -ge 1) { return 'UNCOMMON' }
    return 'COMMON'
}

function Get-Invariance {
    param([PSCustomObject]$FileData)
    
    $hasSSot = $FileData.MarkerHits.ContainsKey('SSOT')
    $hasANKH = $FileData.MarkerHits.ContainsKey('ANKH')
    $hasAxioms = @($FileData.MarkerHits.Keys | Where-Object { $_ -match '^FA' }).Count
    
    if ($hasSSot -or $hasANKH) { return 'INVARIANT' }
    if ($hasAxioms -ge 3) { return 'STABLE' }
    return 'MUTABLE'
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

Write-Host "`n🔥💀⚓ SSOT Treasure Chamber Discovery 🔥💀⚓`n" -ForegroundColor Cyan
Write-Host "Scanning: $ScanPath" -ForegroundColor Gray
Write-Host "Min Density: $MinDensity`n" -ForegroundColor Gray

$mdFiles = Get-MarkdownFiles -Path $ScanPath
Write-Host "Found $($mdFiles.Count) markdown files (excluding build artifacts)`n" -ForegroundColor Yellow

$results = @()
$processed = 0

foreach ($file in $mdFiles) {
    $processed++
    Write-Progress -Activity "Scanning files" -Status $file.Name -PercentComplete (($processed / $mdFiles.Count) * 100)
    
    $data = Measure-SemanticDensity -FilePath $file.FullName -Markers $MARKERS
    if ($data -and $data.Density -ge $MinDensity) {
        $results += $data
    }
}

Write-Progress -Activity "Scanning files" -Completed

# Enrich with rarity/invariance
$enriched = $results | ForEach-Object {
    $_ | Add-Member -NotePropertyName 'Rarity' -NotePropertyValue (Get-Rarity -FileData $_ -AllFiles $results) -PassThru |
         Add-Member -NotePropertyName 'Invariance' -NotePropertyValue (Get-Invariance -FileData $_) -PassThru
}

# Sort by density (highest first)
$enriched = $enriched | Sort-Object -Property Density -Descending

# ============================================================================
# OUTPUT
# ============================================================================

switch ($OutputFormat) {
    'json' {
        $enriched | ConvertTo-Json -Depth 5 | Out-File -FilePath "ssot-treasure-$(Get-Date -Format 'yyyyMMdd-HHmmss').json" -Encoding utf8NoBOM
        Write-Host "`nJSON output saved to ssot-treasure-$(Get-Date -Format 'yyyyMMdd-HHmmss').json" -ForegroundColor Green
    }
    
    'markdown' {
        $md = @"
# SSOT Treasure Chamber Map
**Generated:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  
**Files Scanned:** $($mdFiles.Count)  
**Files with Markers:** $($enriched.Count)

## Top Treasures (by Density)

| Density | Invariance | Rarity | Lines | File |
|---------|------------|--------|-------|------|
"@
        foreach ($file in $enriched | Select-Object -First 25) {
            $md += "`n| $($file.Density) | $($file.Invariance) | $($file.Rarity) | $($file.Lines) | $($file.RelPath) |"
        }
        
        $md | Out-File -FilePath "ssot-treasure-map-$(Get-Date -Format 'yyyyMMdd-HHmmss').md" -Encoding utf8NoBOM
        Write-Host "`nMarkdown map saved to ssot-treasure-map-$(Get-Date -Format 'yyyyMMdd-HHmmss').md" -ForegroundColor Green
    }
    
    'table' {
        Write-Host "`n=== TOP 25 TREASURES (by Semantic Density) ===`n" -ForegroundColor Cyan
        
        $enriched | Select-Object -First 25 | Format-Table -Property @(
            @{ Label = 'Density'; Expression = { $_.Density }; Width = 8 }
            @{ Label = 'Invariance'; Expression = { $_.Invariance }; Width = 10 }
            @{ Label = 'Rarity'; Expression = { $_.Rarity }; Width = 10 }
            @{ Label = 'Lines'; Expression = { $_.Lines }; Width = 7 }
            @{ Label = 'File'; Expression = { $_.RelPath } }
        ) -AutoSize
        
        Write-Host "`n=== INVARIANTS (SSOT/ANKH Core) ===" -ForegroundColor Yellow
        $invariants = $enriched | Where-Object { $_.Invariance -eq 'INVARIANT' }
        Write-Host "Found $($invariants.Count) invariant files:`n"
        $invariants | ForEach-Object { Write-Host "  - $($_.RelPath) (Density: $($_.Density))" }
        
        Write-Host "`n=== RARES (Unique Markers) ===" -ForegroundColor Magenta
        $rares = $enriched | Where-Object { $_.Rarity -eq 'RARE' }
        Write-Host "Found $($rares.Count) rare files:`n"
        $rares | ForEach-Object { Write-Host "  - $($_.RelPath) (Density: $($_.Density))" }
    }
}

Write-Host "`n✅ Discovery complete. Total treasures: $($enriched.Count)`n" -ForegroundColor Green

