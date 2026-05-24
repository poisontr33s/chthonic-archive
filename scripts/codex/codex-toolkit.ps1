#!/usr/bin/env pwsh
#
# @SID: SCRIPT_CODEX_TOOLKIT_V1
# @Type: AGENT
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: codex-toolkit.ps1 — Single entry point for all Codex extension operations
#
# codex-toolkit.ps1 — Single entry point for all Codex extension operations
#
# Usage:
#   .\scripts\codex\codex-toolkit.ps1 patch [-DryRun]
#   .\scripts\codex\codex-toolkit.ps1 restore
#   .\scripts\codex\codex-toolkit.ps1 audit [-Deep]
#   .\scripts\codex\codex-toolkit.ps1 parity
#   .\scripts\codex\codex-toolkit.ps1 status

param(
    [Parameter(Position = 0)]
    [ValidateSet("patch", "restore", "audit", "parity", "status")]
    [string]$Action = "status",

    [switch]$DryRun,
    [switch]$Deep
)

$scriptDir = $PSScriptRoot

switch ($Action) {
    "patch" {
        if ($DryRun) {
            & "$scriptDir\patch-slash-parity.ps1" -DryRun
        } else {
            & "$scriptDir\patch-slash-parity.ps1"
        }
    }
    "restore" {
        & "$scriptDir\patch-slash-parity.ps1" -Restore
    }
    "audit" {
        if ($Deep) {
            & "$scriptDir\audit-bundle.ps1" -Deep
        } else {
            & "$scriptDir\audit-bundle.ps1"
        }
    }
    "parity" {
        & "$scriptDir\audit-bundle.ps1" -Parity
    }
    "status" {
        $bundlePath = "$env:USERPROFILE\.vscode-insiders\extensions\openai.chatgpt-26.5313.41514-win32-x64\webview\assets\index-B5Tvu0Eq.js"
        $backupPath = "$bundlePath.bak"

        if (!(Test-Path $bundlePath)) {
            Write-Host "Bundle not found. Extension may have updated." -ForegroundColor Red
            return
        }

        $size = (Get-Item $bundlePath).Length
        $hasBackup = Test-Path $backupPath
        $c = [System.IO.File]::ReadAllText($bundlePath)
        $isV2 = $c.Contains('I.dispatchMessage')
        $hasOriginal = $c.Contains('a(``agent``,``subagents``,``Subagents``')
        $hasV2Marker = $c.Contains('Toggle plan mode')

        Write-Host "=== Codex Slash Parity Status ===" -ForegroundColor Cyan
        Write-Host "  Bundle:  $size bytes"
        Write-Host "  Backup:  $(if ($hasBackup) { 'Yes' } else { 'No' })"
        Write-Host "  State:   $(if ($hasV2Marker -and $isV2) { 'v2 patched' } elseif ($hasV2Marker) { 'v1 patched (dead)' } elseif ($hasOriginal) { 'Original (unpatched)' } else { 'Unknown' })" -ForegroundColor $(if ($hasV2Marker -and $isV2) { 'Green' } elseif ($hasOriginal) { 'Yellow' } else { 'Red' })
        Write-Host ""
        Write-Host "Commands:"
        Write-Host "  .\scripts\codex\codex-toolkit.ps1 patch [-DryRun]"
        Write-Host "  .\scripts\codex\codex-toolkit.ps1 restore"
        Write-Host "  .\scripts\codex\codex-toolkit.ps1 audit [-Deep]"
        Write-Host "  .\scripts\codex\codex-toolkit.ps1 parity"
    }
}
