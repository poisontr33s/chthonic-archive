#!/usr/bin/env pwsh
# @SID: SCRIPT_SCAN_BROKEN_REFS_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: scan-broken-refs.ps1
# ║ Module: Markdown Reference Scanner
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: tooling/scanner
# ║ Architectural Role: Find broken [text](path) references in .md files
# ║ Purpose: Post-restructure validation - identify orphaned links
# ║ Usage: .\scripts\scan-broken-refs.ps1 [-Fix]
# ╚════════════════════════════════════════════════════════════════════════════

param(
    [switch]$Fix,           # Future: attempt auto-fix
    [string]$Root = "."     # Scan root
)

$ErrorActionPreference = "Continue"
$root = Resolve-Path $Root

Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  BROKEN REFERENCE SCANNER                                    ║" -ForegroundColor Cyan
Write-Host "║  Scanning: $root" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Regex to match markdown links: [text](path)
# Excludes absolute URLs (http/https/file/mailto/etc.)
$linkPattern = @'
\[([^\]]+)\]\((?![a-zA-Z][a-zA-Z0-9+\-.]*://)([^)]+)\)
'@

$brokenRefs = @()
$totalLinks = 0
$checkedFiles = 0

# Get all .md files, excluding node_modules, .git, etc.
$mdFiles = Get-ChildItem -Path $root -Recurse -Filter "*.md" -File |
    Where-Object {
        $_.FullName -notmatch @'
[\\/](node_modules|\.git|build|dist|\.venv)[\\/]
'@
    }

foreach ($file in $mdFiles) {
    $checkedFiles++
    $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
    if (-not $content) { continue }

    $fileDir = $file.DirectoryName
    $matches = [regex]::Matches($content, $linkPattern)

    foreach ($match in $matches) {
        $totalLinks++
        $linkText = $match.Groups[1].Value
        $linkPath = $match.Groups[2].Value

        # Skip anchors-only links like (#section)
        if ($linkPath.StartsWith("#")) { continue }

        # Skip mailto links
        if ($linkPath.StartsWith("mailto:", [System.StringComparison]::OrdinalIgnoreCase)) { continue }

        # Remove anchor from path for file check
        $pathOnly = $linkPath -replace '#.*$', ''

        # Resolve relative path
        $targetPath = Join-Path $fileDir $pathOnly
        $targetPath = [System.IO.Path]::GetFullPath($targetPath)

        # Check if target exists (LiteralPath avoids wildcard interpretation)
        $exists = (Test-Path -LiteralPath $targetPath -PathType Leaf) -or (Test-Path -LiteralPath $targetPath -PathType Container)

        if (-not $exists) {
            $rootStr = $root.Path
            $relativeSrc = $file.FullName -replace [regex]::Escape($rootStr), ""
            $relativeSrc = $relativeSrc.TrimStart("\", "/")
            $brokenRefs += [PSCustomObject]@{
                SourceFile = $relativeSrc
                LinkText   = $linkText
                BrokenPath = $linkPath
                Line       = ($content.Substring(0, $match.Index) -split "`n").Count
            }
        }
    }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "  SCAN RESULTS" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Files scanned:  $checkedFiles" -ForegroundColor White
Write-Host "  Links checked:  $totalLinks" -ForegroundColor White
Write-Host "  Broken refs:    $($brokenRefs.Count)" -ForegroundColor $(if ($brokenRefs.Count -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($brokenRefs.Count -gt 0) {
    Write-Host "  BROKEN REFERENCES:" -ForegroundColor Red
    Write-Host "  ──────────────────" -ForegroundColor Red

    # Group by source file for readability
    $grouped = $brokenRefs | Group-Object SourceFile

    foreach ($group in $grouped) {
        Write-Host ""
        Write-Host "  📄 $($group.Name)" -ForegroundColor Cyan
        foreach ($ref in $group.Group) {
            Write-Host "     L$($ref.Line): [$($ref.LinkText)]($($ref.BrokenPath))" -ForegroundColor Yellow
        }
    }

    # Output as JSON for programmatic use
    $outputPath = Join-Path $root "broken-refs.json"
    $brokenRefs | ConvertTo-Json -Depth 3 | Set-Content $outputPath -Encoding UTF8
    Write-Host ""
    Write-Host "  Output saved to: broken-refs.json" -ForegroundColor Gray
}
else {
    Write-Host "  ✓ All references valid!" -ForegroundColor Green
}

Write-Host ""

