#!/usr/bin/env pwsh
# @SID: GOLDEN_PACKAGE_V1
# @ankh: heritage-continuity — Package Chthonic Golden into distributable format
# SID: chthonic-golden-package
# Usage: .\package.ps1 -UpstreamPath .\upstream-vscode [-Output .\dist] [-Quality stable|insider]

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$UpstreamPath,

    [string]$Output = (Join-Path $PSScriptRoot '..' '..' 'dist' 'chthonic-golden'),

    [ValidateSet('stable', 'insider')]
    [string]$Quality = 'stable'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$GoldenRoot = $PSScriptRoot | Split-Path
$AllowlistPath = Join-Path $GoldenRoot 'extensions' 'allowlist.json'

Write-Host "`n[CHTHONIC-GOLDEN] Packaging ($Quality)" -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# 1. VERIFY BUILD EXISTS
# ---------------------------------------------------------------------------

$buildOutput = Join-Path $UpstreamPath '.build'
if (-not (Test-Path $buildOutput)) {
    # Check alternative build output locations
    $altPaths = @(
        (Join-Path $UpstreamPath 'out'),
        (Join-Path $UpstreamPath 'out-vscode')
    )
    $found = $altPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($found) {
        $buildOutput = $found
    } else {
        Write-Error "No build output found. Run build.ps1 first."
        exit 1
    }
}

Write-Host "[1/4] Build output found: $buildOutput" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 2. COPY BUILT-IN EXTENSIONS
# ---------------------------------------------------------------------------

Write-Host "[2/4] Bundling built-in extensions..." -ForegroundColor Yellow

if (Test-Path $AllowlistPath) {
    $allowlist = Get-Content $AllowlistPath -Raw | ConvertFrom-Json
    $required = @($allowlist.allowlist | Where-Object required -eq $true)
    Write-Host "  $($required.Count) required extensions configured" -ForegroundColor DarkGray
    foreach ($ext in $required) {
        Write-Host "    + $($ext.id) — $($ext.reason)" -ForegroundColor DarkGray
    }
} else {
    Write-Host "  No allowlist found — shipping with upstream default extensions" -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
# 3. CREATE OUTPUT DIRECTORY
# ---------------------------------------------------------------------------

Write-Host "[3/4] Creating output directory..." -ForegroundColor Yellow

$timestamp = Get-Date -Format 'yyyy-MM-ddTHH-mm-ss'
$outputDir = Join-Path $Output "chthonic-golden-$Quality-$timestamp"

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

Write-Host "  Output: $outputDir" -ForegroundColor DarkGray

# ---------------------------------------------------------------------------
# 4. PACKAGE (Portable ZIP for now — installer pipeline TBD after Deep Research)
# ---------------------------------------------------------------------------

Write-Host "[4/4] Packaging..." -ForegroundColor Yellow

# For the prototype phase, we create a manifest describing what would be packaged
$manifest = [PSCustomObject]@{
    Distribution = "Chthonic Golden"
    Quality = $Quality
    Timestamp = $timestamp
    UpstreamPath = $UpstreamPath
    BuildOutput = $buildOutput
    GpuHardened = $true
    V8HeapMB = 8192
    ExtensionAllowlist = if (Test-Path $AllowlistPath) { $AllowlistPath } else { 'none' }
    Status = 'PROTOTYPE — full packaging requires Electron Forge or VS Code native packaging (pending Deep Research)'
}

$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $outputDir 'MANIFEST.json') -Encoding UTF8

Write-Host "`n[CHTHONIC-GOLDEN] Package manifest written to:" -ForegroundColor Cyan
Write-Host "  $outputDir\MANIFEST.json" -ForegroundColor White
Write-Host ""
Write-Host "  NOTE: Full installer packaging requires:" -ForegroundColor Yellow
Write-Host "    - Electron Forge or VS Code's native gulp tasks" -ForegroundColor DarkGray
Write-Host "    - Code signing certificate (Windows)" -ForegroundColor DarkGray
Write-Host "    - These will be configured after Gemini Deep Research delivers build blueprint" -ForegroundColor DarkGray
