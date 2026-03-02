#!/usr/bin/env pwsh

<#
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: update-claude-code.ps1
# ║ Module: Claude Code updater
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: UTILITY
# ║ Semantic ID: SCRIPT_UPDATE_CLAUDE_CODE_V1
# ║ Purpose: Update Claude Code and reapply VS Code Insiders patch
# ║ Exports: (none)
# ║ Flags/Modes: (none)
# ║ Cross-References: scripts/patch-claude-insiders.ps1
# ╚════════════════════════════════════════════════════════════════════════════
#>

<#
.SYNOPSIS
    Updates Claude Code to latest and re-applies the VS Code Insiders patch.
.DESCRIPTION
    Uses bun to install @anthropic-ai/claude-code@latest (npm registry).
    The native installer (irm | iex) installs the 'stable' tag which lags behind.
.EXAMPLE
    .\scripts\update-claude-code.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "Updating Claude Code via bun..." -ForegroundColor Cyan
bun add -g @anthropic-ai/claude-code@latest

Write-Host "`nApplying VS Code Insiders patch..." -ForegroundColor Cyan
& "$PSScriptRoot\patch-claude-insiders.ps1"

Write-Host "`nDone. Restart Claude Code." -ForegroundColor Green

