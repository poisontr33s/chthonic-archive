#!/usr/bin/env pwsh
# @ankh: heritage-continuity — Build pipeline for Chthonic Golden VS Code distribution
# SID: chthonic-golden-build
# Usage: .\build.ps1 -UpstreamPath .\upstream-vscode [-Quality stable|insider] [-SkipPatches]

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$UpstreamPath,

    [ValidateSet('stable', 'insider')]
    [string]$Quality = 'stable',

    [switch]$SkipPatches
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$GoldenRoot = $PSScriptRoot | Split-Path
$ProductJson = Join-Path $GoldenRoot 'product.json'
$QualityJson = Join-Path $GoldenRoot 'quality.json'
$PatchDir = Join-Path $GoldenRoot 'patches'
$BootstrapJs = Join-Path $GoldenRoot 'electron-main' 'bootstrap.js'
$GpuPolicy = Join-Path $GoldenRoot 'electron-main' 'gpu-policy.json'

Write-Host "`n[CHTHONIC-GOLDEN] Build Pipeline" -ForegroundColor Cyan
Write-Host "  Upstream: $UpstreamPath" -ForegroundColor DarkGray
Write-Host "  Quality:  $Quality" -ForegroundColor DarkGray
Write-Host "  Patches:  $(if ($SkipPatches) { 'SKIP' } else { 'APPLY' })" -ForegroundColor DarkGray
Write-Host ""

# ---------------------------------------------------------------------------
# 1. VALIDATE UPSTREAM CHECKOUT
# ---------------------------------------------------------------------------

if (-not (Test-Path (Join-Path $UpstreamPath 'product.json'))) {
    Write-Error "Upstream path does not contain a VS Code checkout (no product.json found): $UpstreamPath"
    exit 1
}

$upstreamProduct = Get-Content (Join-Path $UpstreamPath 'product.json') -Raw | ConvertFrom-Json
Write-Host "[1/6] Upstream validated: $($upstreamProduct.nameShort) ($($upstreamProduct.commit))" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 2. APPLY PRODUCT.JSON OVERRIDE
# ---------------------------------------------------------------------------

Write-Host "[2/6] Replacing product.json with Chthonic Golden identity..." -ForegroundColor Yellow

$goldenProduct = Get-Content $ProductJson -Raw | ConvertFrom-Json

# Merge quality-specific overrides
$qualityDefs = Get-Content $QualityJson -Raw | ConvertFrom-Json
$qualityOverrides = $qualityDefs.$Quality
if ($qualityOverrides) {
    foreach ($prop in $qualityOverrides.PSObject.Properties) {
        $goldenProduct | Add-Member -NotePropertyName $prop.Name -NotePropertyValue $prop.Value -Force
    }
}

# Preserve upstream commit hash for traceability
$goldenProduct.commit = "$($upstreamProduct.commit)-golden-$Quality"

$goldenProduct | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $UpstreamPath 'product.json') -Encoding UTF8
Write-Host "  product.json replaced ($Quality quality)" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 3. APPLY PATCHES
# ---------------------------------------------------------------------------

if (-not $SkipPatches) {
    Write-Host "[3/6] Applying patches..." -ForegroundColor Yellow

    $patches = Get-ChildItem $PatchDir -Filter '*.patch' | Sort-Object Name
    if ($patches.Count -eq 0) {
        Write-Host "  No patch files found (this is normal for initial setup)" -ForegroundColor DarkGray
    } else {
        foreach ($patch in $patches) {
            Write-Host "  Applying $($patch.Name)..." -ForegroundColor DarkGray
            Push-Location $UpstreamPath
            try {
                git apply $patch.FullName
                Write-Host "    OK" -ForegroundColor Green
            } catch {
                Write-Warning "  Patch $($patch.Name) failed — manual resolution needed"
            } finally {
                Pop-Location
            }
        }
    }
} else {
    Write-Host "[3/6] Patches skipped (--SkipPatches)" -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
# 4. INJECT ELECTRON BOOTSTRAP
# ---------------------------------------------------------------------------

Write-Host "[4/6] Injecting hardened Electron bootstrap..." -ForegroundColor Yellow

$electronMainDir = Join-Path $UpstreamPath 'src' 'main'
if (-not (Test-Path $electronMainDir)) {
    # VS Code uses src/vs/code/electron-main as its entry
    $electronMainDir = Join-Path $UpstreamPath 'src' 'vs' 'code' 'electron-main'
}

# Copy bootstrap files alongside upstream entry point
$targetBootstrap = Join-Path $electronMainDir 'chthonic-bootstrap.js'
$targetGpuPolicy = Join-Path $electronMainDir 'gpu-policy.json'

Copy-Item $BootstrapJs $targetBootstrap -Force
Copy-Item $GpuPolicy $targetGpuPolicy -Force
Write-Host "  Injected: chthonic-bootstrap.js + gpu-policy.json" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 5. BUILD
# ---------------------------------------------------------------------------

Write-Host "[5/6] Building VS Code ($Quality)..." -ForegroundColor Yellow

Push-Location $UpstreamPath
try {
    # Install dependencies
    Write-Host "  Installing dependencies (yarn)..." -ForegroundColor DarkGray
    & yarn install --frozen-lockfile 2>&1 | Select-Object -Last 5

    # Compile
    Write-Host "  Compiling..." -ForegroundColor DarkGray
    & yarn compile 2>&1 | Select-Object -Last 5

    Write-Host "  Build complete" -ForegroundColor Green
} finally {
    Pop-Location
}

# ---------------------------------------------------------------------------
# 6. SUMMARY
# ---------------------------------------------------------------------------

Write-Host "`n[6/6] Build Summary" -ForegroundColor Cyan
Write-Host "  Distribution: Chthonic Golden ($Quality)" -ForegroundColor White
Write-Host "  Upstream:     $($upstreamProduct.commit)" -ForegroundColor DarkGray
Write-Host "  Commit:       $($goldenProduct.commit)" -ForegroundColor DarkGray
Write-Host "  GPU Policy:   Hardware acceleration baked in" -ForegroundColor DarkGray
Write-Host "  V8 Heap:      $((Get-Content $GpuPolicy -Raw | ConvertFrom-Json).v8.maxOldSpaceSize)MB" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Next: run .\package.ps1 to create distributable" -ForegroundColor Yellow
