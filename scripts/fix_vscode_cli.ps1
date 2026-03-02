#!/usr/bin/env pwsh

# fix_vscode_cli.ps1 — Ensure `code` CLI is available and Claude integrator can detect VS Code
# Idempotent script: creates a `code` shim if only `code-insiders` exists,
# adds user bin to PATH, installs Anthropic Claude extension if missing,
# and runs `claude /status` for a quick integration check.

Set-StrictMode -Version Latest

Write-Host "== Fix VS Code CLI & Claude Integrator Check ==" -ForegroundColor Cyan

$insiders = Get-Command code-insiders -ErrorAction SilentlyContinue
$stable = Get-Command code -ErrorAction SilentlyContinue

if ($stable) {
  Write-Host "Found 'code' at: $($stable.Source)" -ForegroundColor Green
} else {
  Write-Host "'code' not found." -ForegroundColor Yellow
}

if ($insiders) {
  Write-Host "Found 'code-insiders' at: $($insiders.Source)" -ForegroundColor Green
} else {
  Write-Host "'code-insiders' not found." -ForegroundColor Yellow
}

# Create shim if needed
if (-not $stable -and $insiders) {
  $userBin = Join-Path $env:USERPROFILE 'bin'
  if (-not (Test-Path $userBin)) {
    Write-Host "Creating user bin at: $userBin" -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $userBin -Force | Out-Null
  }

  $shimPath = Join-Path $userBin 'code.cmd'
   $shimContent = @'
@echo off
"%LocalAppData%\Programs\Microsoft VS Code Insiders\bin\code-insiders.cmd" %*
'@

  if (-not (Test-Path $shimPath) -or (Get-Content $shimPath -Raw) -ne $shimContent) {
    Write-Host "Writing shim: $shimPath" -ForegroundColor Cyan
    Set-Content -Path $shimPath -Value $shimContent -Encoding ASCII
  } else {
    Write-Host "Shim already up-to-date: $shimPath" -ForegroundColor Green
  }

  # Ensure user bin is in User PATH
  $currentUserPath = [Environment]::GetEnvironmentVariable('Path','User')
  if ($currentUserPath -notlike "*$userBin*") {
    Write-Host "Adding $userBin to user PATH (requires new terminals to pick up)" -ForegroundColor Cyan
    [Environment]::SetEnvironmentVariable('Path', "$currentUserPath;$userBin", 'User')
  } else {
    Write-Host "$userBin already in user PATH" -ForegroundColor Green
  }

  # Refresh session PATH for this run
  $env:Path = [System.Environment]::GetEnvironmentVariable('Path','User') + ';' + [System.Environment]::GetEnvironmentVariable('Path','Machine')
  Write-Host "Refreshed PATH for current session." -ForegroundColor Cyan
}

# Choose CLI to run extension commands
$cli = if (Get-Command code -ErrorAction SilentlyContinue) { 'code' } elseif (Get-Command code-insiders -ErrorAction SilentlyContinue) { 'code-insiders' } else { $null }

if (-not $cli) {
  Write-Error "No 'code' or 'code-insiders' CLI found. Aborting extension checks."
  exit 2
}

Write-Host "Using CLI: $cli" -ForegroundColor Cyan

# Check if Anthropic Claude extension is installed
$exts = & $cli --list-extensions 2>$null
if ($exts -match 'anthropic.claude-code') {
  Write-Host "Extension 'anthropic.claude-code' is already installed." -ForegroundColor Green
} else {
  Write-Host "Installing 'anthropic.claude-code' via $cli..." -ForegroundColor Cyan
  & $cli --install-extension anthropic.claude-code --force
  if ($LASTEXITCODE -eq 0) { Write-Host "Installed successfully." -ForegroundColor Green } else { Write-Warning "Installation returned non-zero exit code ($LASTEXITCODE)." }
}

# Run claude status if available
$claude = Get-Command claude -ErrorAction SilentlyContinue
if ($claude) {
  Write-Host "Running 'claude /status' to check integrator..." -ForegroundColor Cyan
  & claude /status
} else {
  Write-Host "'claude' command not found in PATH. Skipping integrator status check." -ForegroundColor Yellow
}

Write-Host "\nDone. Please restart VS Code (Insiders) and open a new terminal to ensure changes take effect." -ForegroundColor Cyan

