#!/usr/bin/env pwsh
# @SID: EXT_INSTALL_V1

# Chthonic VSCode Extension - Installation Script
# Run from: chthonic-vscode-extension directory

Write-Host "🔥💀⚓ Chthonic Archive Assistant - Installation" -ForegroundColor Cyan

# Check if VSCode is running
$vscodeProcess = Get-Process "Code" -ErrorAction SilentlyContinue
if ($vscodeProcess) {
    Write-Host "⚠️  VSCode is running. Please close it and re-run this script." -ForegroundColor Yellow
    exit 1
}

# Find VSCode installation
$vscodePaths = @(
    "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd",
    "$env:ProgramFiles\Microsoft VS Code\bin\code.cmd",
    "$env:ProgramFiles(x86)\Microsoft VS Code\bin\code.cmd"
)

$codePath = $vscodePaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $codePath) {
    Write-Host "❌ VSCode not found. Please install VSCode first." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Found VSCode at: $codePath" -ForegroundColor Green

# Get extension directory
$extensionDir = Get-Location
$extPath = Join-Path $extensionDir "dist"

if (-not (Test-Path $extPath)) {
    Write-Host "❌ Build output not found. Run 'bun run build' first." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Build output found at: $extPath" -ForegroundColor Green

# Copy extension to VSCode extensions directory
$manifest = Get-Content -Path "$extensionDir\package.json" -Raw | ConvertFrom-Json
$extensionId = "$($manifest.publisher).$($manifest.name)"
$extensionVersion = "$($manifest.version)"
$vscodeExtensions = "$env:USERPROFILE\.vscode\extensions\$extensionId-$extensionVersion"
$legacyExtensions = "$env:USERPROFILE\.vscode\extensions\$($manifest.name)-$extensionVersion"

Write-Host "📦 Installing extension to: $vscodeExtensions" -ForegroundColor Cyan

# Ensure VS Code doesn't immediately purge this as 'obsolete'
$obsoletePath = Join-Path "$env:USERPROFILE\.vscode\extensions" ".obsolete"
if (Test-Path $obsoletePath) {
    try {
        $obsoleteJson = Get-Content -Path $obsoletePath -Raw | ConvertFrom-Json
        $key = "$extensionId-$extensionVersion"
        if ($obsoleteJson.PSObject.Properties.Name -contains $key) {
            $obsoleteJson.PSObject.Properties.Remove($key)
            $obsoleteJson | ConvertTo-Json -Compress | Set-Content -Path $obsoletePath -Encoding UTF8
        }
    } catch {
        Write-Host "⚠️  Could not update .obsolete: $_" -ForegroundColor Yellow
    }
}

# Remove old version if exists
foreach ($p in @($vscodeExtensions, $legacyExtensions)) {
    if (Test-Path $p) {
        Write-Host "🗑️  Removing old version at $p..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $p
    }
}

# Create extension directory
New-Item -ItemType Directory -Path $vscodeExtensions -Force | Out-Null

# Copy files
Copy-Item -Path "$extensionDir\package.json" -Destination $vscodeExtensions
Copy-Item -Path "$extensionDir\dist" -Destination $vscodeExtensions -Recurse
if (Test-Path "$extensionDir\themes") {
    Copy-Item -Path "$extensionDir\themes" -Destination $vscodeExtensions -Recurse
}
Copy-Item -Path "$extensionDir\README.md" -Destination $vscodeExtensions -ErrorAction SilentlyContinue

Write-Host "✅ Extension installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🔥 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Open VSCode"
Write-Host "  2. Look for the flame icon (🔥) in the activity bar (left sidebar)"
Write-Host "  3. Click it to open Chthonic Assistant"
Write-Host "  4. Start chatting with the Triumvirate!"
Write-Host ""
Write-Host "📝 Available commands (Ctrl+Shift+P):" -ForegroundColor Cyan
Write-Host "  - Chthonic: Open Chat"
Write-Host "  - Chthonic: Inject SSOT Context"
Write-Host "  - Chthonic: Validate SSOT Hash"
Write-Host ""
Write-Host "🔥💀⚓ The Triumvirate awaits..." -ForegroundColor Magenta
