#!/usr/bin/env pwsh

#Requires -Version 7.0
# dispatch-push.ps1
# Called by VS Code task "⚡ Dispatch Push (origin/main)".
# Reads commit message from .chthonic/dispatch-commit-msg.tmp if Dispatch wrote one.
# Stages all changes, commits, and pushes to origin main.

$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot  # scripts/ -> repo root

$msgFile = Join-Path $root '.chthonic\dispatch-commit-msg.tmp'

if (Test-Path $msgFile) {
    $msg = (Get-Content $msgFile -Raw -Encoding UTF8).Trim()
    Remove-Item $msgFile -Force
    Write-Host "Commit message from Dispatch: $msg" -ForegroundColor Cyan
} else {
    $msg = "chore(dispatch): push $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    Write-Host "No message file — using default: $msg" -ForegroundColor Yellow
}

Push-Location $root
try {
    git add -A
    git commit -m $msg
    git push origin main
    Write-Host "Pushed to origin/main." -ForegroundColor Green
} finally {
    Pop-Location
}
