#!/usr/bin/env pwsh
#
# @SID: SCRIPT_THEME_SYNC_V1
# @Type: UTILITY
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Rebuild and sync chthonic-archive extension to VS Code Insiders.
#
<#
.SYNOPSIS
    Rebuild and sync chthonic-archive extension to VS Code Insiders.
.DESCRIPTION
    Automates: bun build → font generation → copy to installed extension → report.
    Syncs themes, fonts (product icon WOFF + codepoint map), and extension assets.
.EXAMPLE
    .\scripts\theme-sync.ps1
    .\scripts\theme-sync.ps1 -SkipBuild       # sync only, no recompile
    .\scripts\theme-sync.ps1 -SkipFontBuild   # skip product icon font regeneration
    .\scripts\theme-sync.ps1 -VerifyOnly       # hash-verify installed copy, no build/copy
#>
param(
    [switch]$SkipBuild,
    [switch]$SkipFontBuild,
    [switch]$VerifyOnly
)

$ErrorActionPreference = 'Stop'
$src = Join-Path $PSScriptRoot '..\extensions\chthonic-archive'
$pkgContent = Get-Content (Join-Path $src 'package.json') -Raw | ConvertFrom-Json
$version = $pkgContent.version
$extensionId = "$($pkgContent.publisher).$($pkgContent.name)-$version"

# Primary: glob-based discovery (version-independent)
$extDir = Join-Path $env:USERPROFILE ".vscode-insiders\extensions\"
$folders = Get-ChildItem -Path $extDir -Directory -Filter "$($pkgContent.publisher).$($pkgContent.name)-*" -ErrorAction SilentlyContinue
if ($folders.Count -eq 1) {
    $dst = $folders[0].FullName
    Write-Host "Extension: $dst" -ForegroundColor DarkGray
} elseif ($folders.Count -gt 1) {
    # Multiple versions installed — prefer exact version match
    $exact = $folders | Where-Object { $_.Name -eq $extensionId }
    if ($exact) { $dst = $exact.FullName }
    else { $dst = ($folders | Sort-Object Name -Descending | Select-Object -First 1).FullName }
    Write-Host "Multiple installs found — using: $dst" -ForegroundColor Yellow
} else {
    Write-Host "❌ Installed extension not found for $($pkgContent.publisher).$($pkgContent.name)" -ForegroundColor Red
    exit 1
}

# Step 1: Rebuild extension
if (!$SkipBuild -and !$VerifyOnly) {
    Write-Host "🔨 Building extension..." -ForegroundColor Cyan
    Push-Location $src
    bun run compile 2>&1 | Write-Host
    Pop-Location
}

# Step 1b: Regenerate product icon font
if (!$SkipFontBuild -and !$VerifyOnly) {
    Write-Host "🔤 Generating product icon font..." -ForegroundColor Cyan
    bun run scripts/generate-product-icon-font.mjs 2>&1 | Write-Host
}

# Step 2: Sync all relevant files
if ($VerifyOnly) {
    Write-Host "🔍 Verifying installed copy (no write)..." -ForegroundColor Cyan
} else {
    Write-Host "📦 Syncing to installed copy..." -ForegroundColor Cyan
}
$files = @(
    'package.json',
    'dist\extension.js'
)
# Add all theme files dynamically
Get-ChildItem (Join-Path $src 'themes') -Filter '*.json' | ForEach-Object {
    $files += "themes\$($_.Name)"
}
# Add font files (product icon WOFF + codepoint map)
$fontsDir = Join-Path $src 'themes\fonts'
if (Test-Path $fontsDir) {
    Get-ChildItem $fontsDir -Include '*.woff','*.json' -Recurse | ForEach-Object {
        $rel = $_.FullName.Substring($src.Length + 1)
        $files += $rel
    }
}

$script:hashFailures = 0

foreach ($f in $files) {
    $s = Join-Path $src $f
    $d = Join-Path $dst $f
    $dDir = Split-Path $d -Parent
    if (!(Test-Path $s)) {
        Write-Host "  ⚠️ SKIP (src missing) $f" -ForegroundColor Yellow
        continue
    }
    if (!$VerifyOnly) {
        if (!(Test-Path $dDir)) { New-Item $dDir -ItemType Directory -Force | Out-Null }
        Copy-Item $s $d -Force
    }
    if (Test-Path $d) {
        $match = (Get-FileHash $s).Hash -eq (Get-FileHash $d).Hash
        $icon = if ($match) { '✅' } else { '❌' }
        Write-Host "  $icon $f"
        if (-not $match) { $script:hashFailures++ }
    } else {
        Write-Host "  ⚠️ NOT INSTALLED $f" -ForegroundColor Yellow
    }
}

# Step 3: Report
$pkg = Get-Content (Join-Path $dst 'package.json') -Raw | ConvertFrom-Json
Write-Host "`n📋 Registered themes:" -ForegroundColor Yellow
foreach ($t in $pkg.contributes.themes) {
    Write-Host "  🎨 $($t.label) → $($t.path)"
}
if ($pkg.contributes.iconThemes) {
    Write-Host "`n📋 File icon themes:" -ForegroundColor Yellow
    foreach ($t in $pkg.contributes.iconThemes) {
        Write-Host "  📁 $($t.label) → $($t.path)"
    }
}
if ($pkg.contributes.productIconThemes) {
    Write-Host "`n📋 Product icon themes:" -ForegroundColor Yellow
    foreach ($t in $pkg.contributes.productIconThemes) {
        Write-Host "  🔣 $($t.label) → $($t.path)"
    }
}

Write-Host "`n⚡ Done. Run 'Developer: Reload Window' in VS Code Insiders." -ForegroundColor Green
if ($script:hashFailures -gt 0) {
    Write-Host "❌ $($script:hashFailures) file(s) failed hash verification." -ForegroundColor Red
    exit 1
}
