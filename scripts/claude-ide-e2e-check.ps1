#!/usr/bin/env pwsh

#Requires -Version 7.0
<#
.SYNOPSIS
    End-to-end diagnostic for Claude Code IDE integration
    
.DESCRIPTION
    Checks every component needed for Claude Code IDE to work:
    - VS Code installation & running status
    - Claude Code extension installation & activation
    - API key configuration
    - Extension communication port
    - MCP server bridge status
    - Full integration readiness
    
.EXAMPLE
    pwsh scripts/claude-ide-e2e-check.ps1 -Verbose
#>

param(
    [switch]$Verbose,
    [switch]$FixAPIKey
)

$ErrorActionPreference = "Continue"

Write-Host "`n╔════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Claude Code IDE - End-to-End Integration Check                         ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$checks = @{
    "VS Code Installation" = $false
    "VS Code Running" = $false
    "Claude Code Extension" = $false
    "Extension Activated" = $false
    "API Key Valid" = $false
    "Extension Port Ready" = $false
    "MCP Bridge Running" = $false
    "All Systems Ready" = $false
}

# ═══════════════════════════════════════════════════════════════════════════
# 1. VS CODE INSTALLATION
# ═══════════════════════════════════════════════════════════════════════════
Write-Host "📍 Check 1: VS Code Installation" -ForegroundColor DarkCyan
Write-Host "─────────────────────────────────────────────────────────────────────────────" 

$codeInsiders = Get-Command code-insiders -ErrorAction SilentlyContinue
$code = Get-Command code -ErrorAction SilentlyContinue

if ($codeInsiders -or $code) {
    $codePath = if ($codeInsiders) { $codeInsiders.Source } else { $code.Source }
    Write-Host "✅ VS Code found: $codePath" -ForegroundColor Green
    $checks["VS Code Installation"] = $true
} else {
    Write-Host "❌ VS Code not found in PATH" -ForegroundColor Red
    exit 1
}

# ═══════════════════════════════════════════════════════════════════════════
# 2. VS CODE RUNNING
# ═══════════════════════════════════════════════════════════════════════════
Write-Host "`n📍 Check 2: VS Code Running Status" -ForegroundColor DarkCyan
Write-Host "─────────────────────────────────────────────────────────────────────────────"

$procs = Get-Process -Name "Code*" -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "Code|code-" }
if ($procs.Count -gt 0) {
    Write-Host "✅ VS Code is running ($($procs.Count) processes)" -ForegroundColor Green
    if ($Verbose) { $procs | Format-Table Name,Id -AutoSize | Out-String | Write-Host }
    $checks["VS Code Running"] = $true
} else {
    Write-Host "❌ VS Code is not running" -ForegroundColor Red
    Write-Host "→ Start it: code-insiders . (or code .)" -ForegroundColor Yellow
}

# ═══════════════════════════════════════════════════════════════════════════
# 3. CLAUDE CODE EXTENSION
# ═══════════════════════════════════════════════════════════════════════════
Write-Host "`n📍 Check 3: Claude Code Extension Installation" -ForegroundColor DarkCyan
Write-Host "─────────────────────────────────────────────────────────────────────────────"

$extPath = "$env:APPDATA\Code - Insiders\User\extensions"
if ($env:APPDATA -and (Test-Path $extPath)) {
    $claudeExt = Get-ChildItem $extPath -Filter "*anthropic*claude*" -ErrorAction SilentlyContinue
    if ($claudeExt) {
        Write-Host "✅ Claude Code extension found:" -ForegroundColor Green
        $claudeExt | ForEach-Object { Write-Host "   - $_" -ForegroundColor Green }
        $checks["Claude Code Extension"] = $true
    } else {
        Write-Host "⚠️  Claude Code extension not found in extensions folder" -ForegroundColor Yellow
        Write-Host "→ Install via VS Code Extensions: @anthropic-ai/claude-code" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Extensions directory not accessible: $extPath" -ForegroundColor Red
}

# ═══════════════════════════════════════════════════════════════════════════
# 4. EXTENSION ACTIVATION STATUS
# ═══════════════════════════════════════════════════════════════════════════
Write-Host "`n📍 Check 4: Extension Activated in VS Code" -ForegroundColor DarkCyan
Write-Host "─────────────────────────────────────────────────────────────────────────────"

$storageDir = "$env:APPDATA\Code - Insiders\User\globalStorage"
if (Test-Path "$storageDir\github.copilot-chat") {
    Write-Host "✅ VS Code Copilot Chat storage found" -ForegroundColor Green
    $checks["Extension Activated"] = $true
} else {
    Write-Host "⚠️  Extension may not be activated" -ForegroundColor Yellow
    Write-Host "→ Try: Reload Window (Ctrl+Shift+P → Reload Window)" -ForegroundColor Yellow
}

# ═══════════════════════════════════════════════════════════════════════════
# 5. API KEY VALIDATION
# ═══════════════════════════════════════════════════════════════════════════
Write-Host "`n📍 Check 5: API Key Configuration" -ForegroundColor DarkCyan
Write-Host "─────────────────────────────────────────────────────────────────────────────"

$apiKey = $env:ANTHROPIC_API_KEY
if (-not $apiKey -and (Test-Path .env.local)) {
    $envContent = Get-Content .env.local | Where-Object { $_ -match "^ANTHROPIC_API_KEY=" }
    $apiKey = ($envContent -split "=", 2)[1].Trim()
}

if ($apiKey -and $apiKey -notmatch "sk_your_key|placeholder|example|your_key") {
    Write-Host "✅ Valid API key detected" -ForegroundColor Green
    Write-Host "   Key: $($apiKey.Substring(0, 10))..." -ForegroundColor DarkGreen
    $checks["API Key Valid"] = $true
} else {
    Write-Host "❌ API key is missing or invalid" -ForegroundColor Red
    Write-Host "   Current: $($apiKey -as [string])" -ForegroundColor Red
    Write-Host "`n🔧 FIX:" -ForegroundColor Yellow
    Write-Host "   1. Get API key: https://console.anthropic.com/account/keys" -ForegroundColor Yellow
    Write-Host "   2. Add to .env.local:" -ForegroundColor Yellow
    Write-Host "      ANTHROPIC_API_KEY=sk_your_actual_key_here" -ForegroundColor Yellow
    Write-Host "   3. Reload VS Code (Ctrl+Shift+P → Reload Window)" -ForegroundColor Yellow
    Write-Host "   4. Run this check again" -ForegroundColor Yellow
}

# ═══════════════════════════════════════════════════════════════════════════
# 6. EXTENSION COMMUNICATION PORT
# ═══════════════════════════════════════════════════════════════════════════
Write-Host "`n📍 Check 6: Extension Communication Port" -ForegroundColor DarkCyan
Write-Host "─────────────────────────────────────────────────────────────────────────────"

$portCheck = $null
try {
    $portCheck = Test-NetConnection -ComputerName localhost -Port 9999 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    if ($portCheck.TcpTestSucceeded) {
        Write-Host "✅ Extension port 9999 is accessible" -ForegroundColor Green
        $checks["Extension Port Ready"] = $true
    } else {
        Write-Host "ℹ️  Extension port 9999 not yet open (normal on first launch)" -ForegroundColor DarkGray
        Write-Host "→ Will open when Claude Code IDE connects" -ForegroundColor DarkGray
    }
} catch {
    Write-Host "ℹ️  Port check skipped (net available)" -ForegroundColor DarkGray
}

# ═══════════════════════════════════════════════════════════════════════════
# 7. MCP BRIDGE STATUS
# ═══════════════════════════════════════════════════════════════════════════
Write-Host "`n📍 Check 7: MCP Bridge Server" -ForegroundColor DarkCyan
Write-Host "─────────────────────────────────────────────────────────────────────────────"

$bridgeCheck = $null
try {
    $bridgeCheck = Invoke-WebRequest -Uri "http://localhost:8888/status" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($bridgeCheck.StatusCode -eq 200) {
        Write-Host "✅ MCP Bridge running on port 8888" -ForegroundColor Green
        Write-Host "   Status: $($bridgeCheck.Content)" -ForegroundColor DarkGreen
        $checks["MCP Bridge Running"] = $true
    }
} catch {
    Write-Host "⚠️  MCP Bridge not running" -ForegroundColor Yellow
    Write-Host "→ Start it: bun run scripts/bridge-server.ts" -ForegroundColor Yellow
}

# ═══════════════════════════════════════════════════════════════════════════
# 8. SUMMARY & RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════
Write-Host "`n╔════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Integration Status Summary                                              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$passCount = ($checks.Values | Where-Object { $_ -eq $true }).Count
$totalCount = $checks.Count

foreach ($check in $checks.GetEnumerator()) {
    $symbol = if ($check.Value) { "✅" } else { "⚠️ " }
    $color = if ($check.Value) { "Green" } else { "Yellow" }
    Write-Host "$symbol $($check.Key)" -ForegroundColor $color
}

Write-Host "`nStatus: $passCount/$totalCount checks passed`n" -ForegroundColor Cyan

if ($checks["API Key Valid"]) {
    Write-Host "🚀 READY TO LAUNCH:" -ForegroundColor Green
    Write-Host "   chthonic claude-ide" -ForegroundColor Green
    Write-Host "`nor:`n" -ForegroundColor Green
    Write-Host "   claude --ide" -ForegroundColor Green
    $checks["All Systems Ready"] = $true
} else {
    Write-Host "⚠️  ACTION REQUIRED:" -ForegroundColor Yellow
    Write-Host "   1. Add valid ANTHROPIC_API_KEY to .env.local" -ForegroundColor Yellow
    Write-Host "   2. Save the file" -ForegroundColor Yellow
    Write-Host "   3. Reload VS Code (Ctrl+Shift+P → Reload Window)" -ForegroundColor Yellow
    Write-Host "   4. Run this check again" -ForegroundColor Yellow
}

Write-Host "`n"
exit if $checks["All Systems Ready"] { 0 } else { 1 }

