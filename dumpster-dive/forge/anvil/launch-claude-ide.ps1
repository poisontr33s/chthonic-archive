#!/usr/bin/env pwsh
# @SID: FORGE_LAUNCH_CLAUDE_IDE_V1

#Requires -Version 7.0
<#
.SYNOPSIS
    Claude Code IDE Launcher - Workaround for Bun 1.3.6 Windows segfault
    
.DESCRIPTION
    Launches Claude Code IDE with proper TTY and environment handling
    Automatically retries with fallback mechanisms if primary launch fails
    
.PARAMETER command
    Command to run (default: "ide")
    
.PARAMETER debug
    Enable debug output
    
.EXAMPLE
    ./launch-claude-ide.ps1
    ./launch-claude-ide.ps1 -command "." -debug
#>

param(
    [string]$command = "ide",
    [switch]$debug
)

$ErrorActionPreference = "Continue"
$CliPath = "C:\Users\erdno\.bun\install\global\node_modules\@anthropic-ai\claude-code\cli.js"

if ($debug) { Write-Host "🔍 Claude Code IDE Launcher v1.0" -ForegroundColor Cyan }

# Verify installation
if (-not (Test-Path $CliPath)) {
    Write-Host "❌ Claude Code CLI not found at: $CliPath" -ForegroundColor Red
    Write-Host "Install with: bun install -g @anthropic-ai/claude-code" -ForegroundColor Yellow
    exit 1
}

if ($debug) { Write-Host "✅ Claude Code found at: $CliPath" -ForegroundColor Green }

# Check for required API keys
$keys = @{}
if (Test-Path .env.local) {
    $envContent = Get-Content .env.local | Where-Object { $_ -match "^ANTHROPIC_API_KEY|^GOOGLE_API_KEY" }
    foreach ($line in $envContent) {
        $parts = $line -split "=", 2
        if ($parts.Count -eq 2) {
            $keys[$parts[0].Trim()] = $parts[1].Trim()
        }
    }
}

if (-not $env:ANTHROPIC_API_KEY -and $keys["ANTHROPIC_API_KEY"]) {
    $env:ANTHROPIC_API_KEY = $keys["ANTHROPIC_API_KEY"]
    if ($debug) { Write-Host "📝 Loaded ANTHROPIC_API_KEY from .env.local" -ForegroundColor Blue }
}

if (-not $env:ANTHROPIC_API_KEY) {
    Write-Host "⚠️  ANTHROPIC_API_KEY not set" -ForegroundColor Yellow
    Write-Host "Set it in .env.local or as an environment variable" -ForegroundColor Yellow
}

# Find available IDEs
$vsCodePath = Get-Command code -ErrorAction SilentlyContinue
$vsCodeInsidersPath = Get-Command code-insiders -ErrorAction SilentlyContinue
$ideArg = @()

if ($vsCodeInsidersPath) {
    $ideCmd = "code-insiders"
    $ideExe = $vsCodeInsidersPath.Source
    if ($debug) { Write-Host "✅ Found VS Code Insiders: $ideExe" -ForegroundColor Green }
}
elseif ($vsCodePath) {
    $ideCmd = "code"
    $ideExe = $vsCodePath.Source
    if ($debug) { Write-Host "✅ Found VS Code: $ideExe" -ForegroundColor Green }
}
else {
    Write-Host "❌ Error: VS Code not found in PATH" -ForegroundColor Red
    Write-Host "Install from: https://code.visualstudio.com" -ForegroundColor Yellow
    Write-Host "Or run diagnostic: pwsh scripts/ide-detection.ps1" -ForegroundColor Yellow
    exit 1
}

# Ensure we're in the workspace directory
Push-Location (Split-Path $PSScriptRoot -Parent)

# Check if VS Code is running
$isRunning = Get-Process $($ideCmd -replace "-insiders", "") -ErrorAction SilentlyContinue
if (-not $isRunning) {
    Write-Host "⚠️  $ideCmd is not currently running" -ForegroundColor Yellow
    Write-Host "Starting $ideCmd in workspace..." -ForegroundColor DarkCyan
    & $ideCmd . 2>$null &
    Start-Sleep -Seconds 3
}

# Strategy 1: Try bun with proper stdio setup
if ($debug) { Write-Host "🚀 Attempt 1: Launching Claude Code in workspace..." -ForegroundColor Cyan }

try {
    $workspacePath = (Get-Location).Path
    $cliArgs = @($CliPath, "--$command", $workspacePath)
    
    $process = Start-Process -FilePath (Get-Command bun).Source `
        -ArgumentList $cliArgs `
        -WorkingDirectory $workspacePath `
        -NoNewWindow `
        -PassThru `
        -ErrorAction Stop
    
    if ($debug) { Write-Host "✅ Process started (PID: $($process.Id)) - waiting for completion" -ForegroundColor Green }
    $process.WaitForExit()
    $exitCode = $process.ExitCode
    
    Pop-Location
    if ($exitCode -eq 0 -or $exitCode -eq 1) {
        exit $exitCode
    }
}
catch {
    if ($debug) { Write-Host "⚠️  Bun launch attempt failed: $_" -ForegroundColor Yellow }
}

# Strategy 2: Try direct Node.js if available
if ($debug) { Write-Host "🚀 Attempt 2: Trying Node.js directly..." -ForegroundColor Cyan }

$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCmd) {
    try {
        $workspacePath = (Get-Location).Path
        $process = Start-Process -FilePath $nodeCmd.Source `
            -ArgumentList @($CliPath, "--$command", $workspacePath) `
            -WorkingDirectory $workspacePath `
            -NoNewWindow `
            -PassThru `
            -ErrorAction Stop
        
        if ($debug) { Write-Host "✅ Node.js process started (PID: $($process.Id))" -ForegroundColor Green }
        $process.WaitForExit()
        Pop-Location
        exit $process.ExitCode
    }
    catch {
        if ($debug) { Write-Host "⚠️  Node.js launch attempt failed: $_" -ForegroundColor Yellow }
    }
}

# Strategy 3: Use chthonic.ps1 to find a runtime
if ($debug) { Write-Host "🚀 Attempt 3: Using chthonic polyglot runtime..." -ForegroundColor Cyan }

$chthonic = if (Test-Path ./scripts/chthonic.ps1) { ./scripts/chthonic.ps1 } else { . "$PSScriptRoot/chthonic.ps1" }

# Fallback fallback: Interactive prompt
Write-Host "`n🎯 Claude Code IDE Setup" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n"

Write-Host "If Claude Code IDE didn't launch, try:

1️⃣  Make sure you're in the workspace directory:
    cd c:\Users\erdno\chthonic-archive

2️⃣  Launch from workspace root:
    claude --ide

3️⃣  Or use chthonic from workspace:
    chthonic claude-ide

Status:" -ForegroundColor White

Write-Host "IDE Command: $ideCmd" -ForegroundColor DarkCyan
Write-Host "IDE Executable: $ideExe" -ForegroundColor DarkCyan
Write-Host "Claude Code CLI: $CliPath" -ForegroundColor DarkCyan

if ($env:ANTHROPIC_API_KEY) {
    Write-Host "  ✅ ANTHROPIC_API_KEY is set" -ForegroundColor Green
} else {
    Write-Host "  ❌ ANTHROPIC_API_KEY not set - add to .env.local" -ForegroundColor Red
}

if ($env:GOOGLE_API_KEY) {
    Write-Host "  ✅ GOOGLE_API_KEY is set" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  GOOGLE_API_KEY not set (optional for Gemini)" -ForegroundColor Yellow
}

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n"

exit 1

