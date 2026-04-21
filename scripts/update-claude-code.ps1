#!/usr/bin/env pwsh
# @SID: SCRIPT_UPDATE_CLAUDE_CODE_V1

<#
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: update-claude-code.ps1
# ║ Module: Claude Code updater
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: UTILITY
# ║ Semantic ID: SCRIPT_UPDATE_CLAUDE_CODE_V1
# ║ Purpose: Update Claude Code to latest, capture version before/after, print diff
# ║ Exports: (none)
# ║ Flags/Modes: (none)
# ║ Cross-References: (none)
# ╚════════════════════════════════════════════════════════════════════════════
#>

<#
.SYNOPSIS
    Updates Claude Code to latest and prints before/after version diff.
.DESCRIPTION
    Uses bun to install @anthropic-ai/claude-code@latest (npm registry).
    The native installer (irm | iex) installs the 'stable' tag which lags behind.
.EXAMPLE
    .\scripts\update-claude-code.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Capture version before update
$verBefore = (& claude --version 2>$null) | Select-Object -First 1
if ($LASTEXITCODE -ne 0 -or -not $verBefore) { $verBefore = "(not installed)" }

Write-Host "Updating Claude Code via bun..." -ForegroundColor Cyan
bun add -g @anthropic-ai/claude-code@latest

# Capture version after update
$verAfter = (& claude --version 2>$null) | Select-Object -First 1
if ($LASTEXITCODE -ne 0 -or -not $verAfter) { $verAfter = "(not found)" }

Write-Host "`nVersion diff:" -ForegroundColor Cyan
Write-Host "  Before: $verBefore" -ForegroundColor DarkGray
Write-Host "  After:  $verAfter" -ForegroundColor Green

Write-Host "`nDone. Restart Claude Code." -ForegroundColor Green

