#!/usr/bin/env pwsh

# Cross-Reference Validation Script
# Validates all cross-references in dumpster-dive/ folder
# Usage: .\validate_references.ps1

param(
    [string]$Path = ".",
    [switch]$Verbose,
    [switch]$FixBroken
)

Write-Host "🔍 Cross-Reference Validation Tool" -ForegroundColor Cyan
Write-Host "Checking: $((Resolve-Path $Path).Path)" -ForegroundColor Gray
Write-Host ""

$script:issues = @{
    BrokenLinks = @()
    OrphanedFiles = @()
    MissingCrossRefs = @()
    DeprecatedRefs = @()
}

$script:stats = @{
    TotalFiles = 0
    TotalLinks = 0
    ValidLinks = 0
    BrokenLinks = 0
    FilesWithCrossRefs = 0
    OrphanedFiles = 0
}

# Get all markdown files
$mdFiles = Get-ChildItem -Path $Path -Recurse -Filter *.md | Where-Object { 
    $_.FullName -notlike "*\build\*" -and 
    $_.FullName -notlike "*\target\*" -and
    $_.FullName -notlike "*\node_modules\*"
}

# Get all JSON files
$jsonFiles = Get-ChildItem -Path $Path -Recurse -Filter *.json | Where-Object { 
    $_.FullName -notlike "*\build\*" -and 
    $_.FullName -notlike "*\target\*" -and
    $_.FullName -notlike "*\node_modules\*"
}

$allFiles = $mdFiles + $jsonFiles
$script:stats.TotalFiles = $allFiles.Count

Write-Host "📄 Found $($mdFiles.Count) markdown files" -ForegroundColor Green
Write-Host "📄 Found $($jsonFiles.Count) JSON files" -ForegroundColor Green
Write-Host ""

# Function to extract markdown links
function Get-MarkdownLinks {
    param([string]$FilePath)
    
    $content = Get-Content $FilePath -Raw
    $links = @()
    
    # Match [text](path) format
    $pattern = '\[([^\]]+)\]\(([^\)]+)\)'
    $matches = [regex]::Matches($content, $pattern)
    
    foreach ($match in $matches) {
        $linkText = $match.Groups[1].Value
        $linkPath = $match.Groups[2].Value
        if ($null -eq $linkPath) { continue }

        $linkPath = $linkPath.Trim()
        if ([string]::IsNullOrWhiteSpace($linkPath)) { continue }

        # Skip malformed captures (e.g., regex spanning newlines or large blocks)
        if ($linkPath -match "[\r\n]") { continue }
        
        # Skip external URLs
        if ($linkPath -match '^https?://') { continue }
        if ($linkPath -match '^mailto:') { continue }

        # Skip non-file URI schemes (e.g., custom emoji links like ild:...)
        # Keep Windows drive-letter paths (C:\...) as-is so they can be flagged.
        if ($linkPath -match '^[A-Za-z][A-Za-z0-9+.-]*:' -and $linkPath -notmatch '^[A-Za-z]:[\\/]') { continue }

        # Skip obvious placeholder/example targets used in documentation samples
        if ($linkPath -match '(^|/)path/to/' ) { continue }
        
        # Remove anchors for file existence check
        $filePath = $linkPath -replace '#.*$', ''
        
        $links += @{
            Text = $linkText
            Path = $linkPath
            FilePath = $filePath
            Line = $content.Substring(0, $match.Index).Split("`n").Count
        }
    }
    
    return $links
}

# Function to check if file exists relative to current file
function Test-RelativeLink {
    param(
        [string]$SourceFile,
        [string]$LinkPath
    )
    
    $sourceDir = Split-Path $SourceFile -Parent
    $targetPath = Join-Path $sourceDir $LinkPath
    
    # Resolve relative path
    try {
        $resolved = Resolve-Path $targetPath -ErrorAction SilentlyContinue
        return $null -ne $resolved
    }
    catch {
        return $false
    }
}

# Function to check for Cross-References section
function Test-HasCrossReferences {
    param([string]$FilePath)
    
    $content = Get-Content $FilePath -Raw
    return $content -match '##\s+Cross-References'
}

# Function to find references TO a file
function Get-ReferencesToFile {
    param([string]$TargetFile)
    
    $targetName = Split-Path $TargetFile -Leaf
    $references = @()
    
    foreach ($file in $allFiles) {
        if ($file.FullName -eq $TargetFile) { continue }
        
        $content = Get-Content $file.FullName -Raw
        if ($content -match [regex]::Escape($targetName)) {
            $references += $file.FullName
        }
    }
    
    return $references
}

Write-Host "🔗 Validating markdown links..." -ForegroundColor Yellow

# Check all markdown files for broken links
foreach ($file in $mdFiles) {
    $links = Get-MarkdownLinks -FilePath $file.FullName
    $script:stats.TotalLinks += $links.Count
    
    foreach ($link in $links) {
        $isValid = Test-RelativeLink -SourceFile $file.FullName -LinkPath $link.FilePath
        
        if ($isValid) {
            $script:stats.ValidLinks++
        }
        else {
            $script:stats.BrokenLinks++
            $script:issues.BrokenLinks += @{
                File = $file.FullName
                Line = $link.Line
                Text = $link.Text
                Path = $link.Path
            }
            
            if ($Verbose) {
                Write-Host "  ❌ $($file.Name):$($link.Line) → [$($link.Text)]($($link.Path))" -ForegroundColor Red
            }
        }
    }
}

Write-Host "✅ Valid links: $($script:stats.ValidLinks)" -ForegroundColor Green
Write-Host "❌ Broken links: $($script:stats.BrokenLinks)" -ForegroundColor Red
Write-Host ""

Write-Host "📋 Checking for Cross-References sections..." -ForegroundColor Yellow

# Check which files have cross-references
foreach ($file in $mdFiles) {
    if (Test-HasCrossReferences -FilePath $file.FullName) {
        $script:stats.FilesWithCrossRefs++
    }
    else {
        $script:issues.MissingCrossRefs += $file.FullName
        
        if ($Verbose) {
            Write-Host "  ⚠️  Missing: $($file.Name)" -ForegroundColor Yellow
        }
    }
}

Write-Host "✅ Files with Cross-References: $($script:stats.FilesWithCrossRefs)" -ForegroundColor Green
Write-Host "⚠️  Files missing Cross-References: $($script:issues.MissingCrossRefs.Count)" -ForegroundColor Yellow
Write-Host ""

Write-Host "🔍 Finding orphaned files..." -ForegroundColor Yellow

# Check for orphaned files (no incoming references)
foreach ($file in $mdFiles) {
    # Skip README files (entry points don't need incoming refs)
    if ($file.Name -eq 'README.md') { continue }
    
    $references = Get-ReferencesToFile -TargetFile $file.FullName
    
    if ($references.Count -eq 0) {
        $script:stats.OrphanedFiles++
        $script:issues.OrphanedFiles += $file.FullName
        
        if ($Verbose) {
            Write-Host "  🏝️  Orphaned: $($file.Name)" -ForegroundColor Magenta
        }
    }
}

Write-Host "⚠️  Orphaned files (no incoming references): $($script:stats.OrphanedFiles)" -ForegroundColor Yellow
Write-Host ""

# Summary Report
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "VALIDATION SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "Total Files:              $($script:stats.TotalFiles)" -ForegroundColor White
Write-Host "Total Links:              $($script:stats.TotalLinks)" -ForegroundColor White
Write-Host "Valid Links:              $($script:stats.ValidLinks)" -ForegroundColor Green
Write-Host "Broken Links:             $($script:stats.BrokenLinks)" -ForegroundColor $(if ($script:stats.BrokenLinks -eq 0) { 'Green' } else { 'Red' })
Write-Host "Files with Cross-Refs:    $($script:stats.FilesWithCrossRefs)" -ForegroundColor Green
Write-Host "Missing Cross-Refs:       $($script:issues.MissingCrossRefs.Count)" -ForegroundColor $(if ($script:issues.MissingCrossRefs.Count -eq 0) { 'Green' } else { 'Yellow' })
Write-Host "Orphaned Files:           $($script:stats.OrphanedFiles)" -ForegroundColor $(if ($script:stats.OrphanedFiles -eq 0) { 'Green' } else { 'Yellow' })
Write-Host ""

# Detailed issue reporting
if ($script:stats.BrokenLinks -gt 0) {
    Write-Host "=" * 60 -ForegroundColor Red
    Write-Host "BROKEN LINKS DETAILS" -ForegroundColor Red
    Write-Host "=" * 60 -ForegroundColor Red
    Write-Host ""
    
    foreach ($issue in $script:issues.BrokenLinks) {
        $relativePath = Resolve-Path $issue.File -Relative
        Write-Host "📄 $relativePath" -ForegroundColor Yellow
        Write-Host "   Line $($issue.Line): [$($issue.Text)]($($issue.Path))" -ForegroundColor Red
        Write-Host ""
    }
}

if ($script:issues.MissingCrossRefs.Count -gt 0 -and $Verbose) {
    Write-Host "=" * 60 -ForegroundColor Yellow
    Write-Host "FILES MISSING CROSS-REFERENCES" -ForegroundColor Yellow
    Write-Host "=" * 60 -ForegroundColor Yellow
    Write-Host ""
    
    foreach ($file in $script:issues.MissingCrossRefs) {
        $relativePath = Resolve-Path $file -Relative
        Write-Host "  📄 $relativePath" -ForegroundColor Yellow
    }
    Write-Host ""
}

if ($script:stats.OrphanedFiles -gt 0 -and $Verbose) {
    Write-Host "=" * 60 -ForegroundColor Magenta
    Write-Host "ORPHANED FILES (No Incoming References)" -ForegroundColor Magenta
    Write-Host "=" * 60 -ForegroundColor Magenta
    Write-Host ""
    
    foreach ($file in $script:issues.OrphanedFiles) {
        $relativePath = Resolve-Path $file -Relative
        Write-Host "  🏝️  $relativePath" -ForegroundColor Magenta
    }
    Write-Host ""
    Write-Host "Note: Orphaned files may still be valid entry points or awaiting integration." -ForegroundColor Gray
}

# Health score
$healthScore = 0
if ($script:stats.TotalLinks -gt 0) {
    $healthScore = [math]::Round(($script:stats.ValidLinks / $script:stats.TotalLinks) * 100, 1)
}

$crossRefScore = 0
if ($mdFiles.Count -gt 0) {
    $crossRefScore = [math]::Round(($script:stats.FilesWithCrossRefs / $mdFiles.Count) * 100, 1)
}

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "HEALTH SCORES" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Link Integrity:           $healthScore%" -ForegroundColor $(if ($healthScore -ge 95) { 'Green' } elseif ($healthScore -ge 80) { 'Yellow' } else { 'Red' })
Write-Host "Cross-Reference Coverage: $crossRefScore%" -ForegroundColor $(if ($crossRefScore -ge 80) { 'Green' } elseif ($crossRefScore -ge 50) { 'Yellow' } else { 'Red' })
Write-Host ""

# Exit code based on results
if ($script:stats.BrokenLinks -eq 0) {
    Write-Host "✅ No broken links found. All references are valid!" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "⚠️  Found $($script:stats.BrokenLinks) broken link(s). Please fix." -ForegroundColor Yellow
    exit 1
}
