#!/usr/bin/env pwsh
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: fix-md-links.ps1
# ║ Module: Markdown link repair
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: UTILITY
# ║ Semantic ID: SCRIPT_FIX_MD_LINKS_V1
# ║ Purpose: Find and repair broken relative Markdown links
# ║ Exports: (none)
# ║ Flags/Modes: --root, --fix, --dry-run
# ║ Cross-References: (none)
# ╚════════════════════════════════════════════════════════════════════════════

[CmdletBinding()]
param(
    [string]$Root = '.',
    [switch]$Fix,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

# Default to dry-run unless --Fix is explicitly set.
if (-not $Fix) { $DryRun = $true }

$ignoreDirs = @(
    '.git',
    'node_modules',
    'target',
    'build',
    'dist',
    '.venv',
    '.cache'
)

$linkPattern = [regex]'\[([^\]]+)\]\((?!https?:|mailto:|#|/)([^\)]+)\)'

function Normalize-RelPath([string]$path) {
    return ($path -replace '\\', '/').Trim()
}

function Get-RelativePath([string]$fromDir, [string]$toPath) {
    $rel = [System.IO.Path]::GetRelativePath($fromDir, $toPath)
    return Normalize-RelPath $rel
}

function Build-FileIndex([string]$rootDir) {
    $index = @{}
    Get-ChildItem -Path $rootDir -Recurse -File -Filter '*.md' -Force |
        Where-Object {
            $parts = $_.FullName.Split([System.IO.Path]::DirectorySeparatorChar)
            -not ($parts | Where-Object { $ignoreDirs -contains $_ })
        } | ForEach-Object {
            $name = $_.Name
            if (-not $index.ContainsKey($name)) {
                $index[$name] = @()
            }
            $index[$name] += $_.FullName
        }
    return $index
}

function Resolve-Link(
    [string]$link,
    [System.IO.FileInfo]$sourceFile,
    [hashtable]$index,
    [string]$rootDir
) {
    $clean = $link.Split('#')[0].Split('?')[0]
    if ([string]::IsNullOrWhiteSpace($clean)) { return $null }

    $sourceDir = $sourceFile.Directory.FullName

    $relativeTarget = [System.IO.Path]::GetFullPath((Join-Path $sourceDir $clean))
    if (Test-Path -LiteralPath $relativeTarget) { return $null }

    $rootTarget = [System.IO.Path]::GetFullPath((Join-Path $rootDir $clean))
    if (Test-Path -LiteralPath $rootTarget) {
        return Get-RelativePath $sourceDir $rootTarget
    }

    $targetName = [System.IO.Path]::GetFileName($clean)
    if (-not $index.ContainsKey($targetName)) { return $false }

    $candidates = $index[$targetName]
    if ($candidates.Count -eq 1) {
        $suffix = ''
        if ($link -like '*#*') { $suffix = '#' + $link.Split('#')[1] }
        elseif ($link -like '*?*') { $suffix = '?' + $link.Split('?')[1] }

        $relFix = Get-RelativePath $sourceDir $candidates[0]
        return $relFix + $suffix
    }

    return $false
}

function Process-File([System.IO.FileInfo]$file, [hashtable]$index, [string]$rootDir, [switch]$ApplyFixes) {
    $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
    $changes = 0

    $result = $linkPattern.Replace($content, {
        param($m)
        $label = $m.Groups[1].Value
        $link = $m.Groups[2].Value

        $fix = Resolve-Link -link $link -sourceFile $file -index $index -rootDir $rootDir

        if ($fix -eq $null) { return $m.Value }
        if ($fix -eq $false) {
            Write-Host "❌ Broken: '$link' in $($file.FullName)" -ForegroundColor DarkYellow
            return $m.Value
        }

        Write-Host "✅ Fix: '$link' -> '$fix' in $($file.FullName)" -ForegroundColor Green
        $script:changes++
        return "[$label]($fix)"
    })

    if ($ApplyFixes -and $result -ne $content) {
        Set-Content -Path $file.FullName -Value $result -Encoding UTF8
    }

    return $changes
}

$rootDir = (Resolve-Path -Path $Root).Path
Write-Host "🔍 Indexing markdown files in $rootDir..." -ForegroundColor Cyan
$index = Build-FileIndex -rootDir $rootDir
Write-Host "📂 Indexed $($index.Keys.Count) unique filenames." -ForegroundColor Gray

Write-Host "🚀 Scanning for broken links..." -ForegroundColor Cyan
$totalFixes = 0

Get-ChildItem -Path $rootDir -Recurse -File -Filter '*.md' -Force |
    Where-Object {
        $parts = $_.FullName.Split([System.IO.Path]::DirectorySeparatorChar)
        -not ($parts | Where-Object { $ignoreDirs -contains $_ })
    } | ForEach-Object {
        $totalFixes += (Process-File -file $_ -index $index -rootDir $rootDir -ApplyFixes:$Fix)
    }

if ($Fix) {
    Write-Host "`n✨ Completed. Fixed $totalFixes links." -ForegroundColor Green
} else {
    Write-Host "`nℹ️  Dry run complete. Found $totalFixes fixable links. Use --fix to apply." -ForegroundColor Yellow
}
