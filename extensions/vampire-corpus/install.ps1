#!/usr/bin/env pwsh
# @SID: VAMPIRE_CORPUS_INSTALL_V1
# Install vampire-corpus VS Code extension from source.
# Usage: .\install.ps1 [-Build] [-Force]
param(
    [switch]$Build,    # force rebuild even if dist/ exists
    [switch]$Force     # pass --force to code --install-extension
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = $PSScriptRoot
Set-Location $scriptDir

function Write-Step([string]$msg) {
    Write-Host "  => $msg" -ForegroundColor Cyan
}

Write-Host "`nVampire Corpus — Extension Installer" -ForegroundColor Magenta
Write-Host ('=' * 40) -ForegroundColor DarkGray

# 1. Install dependencies
Write-Step "Installing devDependencies with bun..."
bun install --silent

# 2. Build TypeScript
$distExists = Test-Path (Join-Path $scriptDir 'dist' 'extension.js')
if ($Build -or -not $distExists) {
    Write-Step "Compiling TypeScript..."
    bun run build
} else {
    Write-Step "dist/ already present — skipping build (use -Build to force)"
}

# 3. Package
$vsixGlob = Join-Path $scriptDir '*.vsix'
$existing = Get-Item $vsixGlob -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($Build -or -not $existing) {
    Write-Step "Packaging extension..."
    bunx @vscode/vsce package --no-dependencies --allow-missing-repository 2>&1 | Write-Host
    $existing = Get-Item $vsixGlob | Sort-Object LastWriteTime -Descending | Select-Object -First 1
} else {
    Write-Step "VSIX already present: $($existing.Name) — skipping package (use -Build to force)"
}

if (-not $existing) {
    Write-Host "`n  ERROR: VSIX not found after package step." -ForegroundColor Red
    exit 1
}

# 4. Install extension
$forceFlag = if ($Force) { '--force' } else { '' }
Write-Step "Installing: $($existing.Name)"
if ($forceFlag) {
    code-insiders --install-extension $existing.FullName --force
} else {
    code-insiders --install-extension $existing.FullName
}

Write-Host "`n  Done. Reload VS Code window to activate Vampire Corpus panel." -ForegroundColor Green
Write-Host "  Shortcut: Ctrl+Shift+P → 'Developer: Reload Window'" -ForegroundColor DarkGray
