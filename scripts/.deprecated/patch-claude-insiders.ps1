#!/usr/bin/env pwsh
# @SID: SCRIPT_PATCH_CLAUDE_INSIDERS_V1

<#
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: patch-claude-insiders.ps1
# ║ Module: Claude Code VS Code Insiders patcher
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: UTILITY
# ║ Purpose: Patch Claude Code CLI to use code-insiders on Windows
# ║ Exports: (none)
# ║ Flags/Modes: (none)
# ║ Cross-References: (none)
# ╚════════════════════════════════════════════════════════════════════════════
#>

<#
.SYNOPSIS
    Patches Claude Code CLI to support VS Code Insiders on Windows.
.DESCRIPTION
    Claude Code hardcodes "code" as the VS Code binary. VS Code Insiders uses
    "code-insiders". This script patches cli.js so the startup IDE check finds
    and installs the extension via code-insiders instead.

    Run after every Claude Code update.
.EXAMPLE
    .\scripts\patch-claude-insiders.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- RETIRED ---
# Claude Code is now a compiled Bun binary at ~/.local/bin/claude.exe.
# The npm-based cli.js patching is obsolete since v2.1.x.
# VS Code Insiders detection is handled natively by the extension.
Write-Host "RETIRED: Claude Code no longer uses npm cli.js. No patch needed." -ForegroundColor Yellow
exit 0

# --- Legacy code below (kept for reference) ---
$npmBase = Join-Path $env:USERPROFILE '.npm\@anthropic-ai'
if (-not (Test-Path $npmBase)) {
    Write-Error "Claude Code npm directory not found at $npmBase"
    exit 1
}

$cliFile = Get-ChildItem -Path $npmBase -Recurse -Filter 'cli.js' |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $cliFile) {
    Write-Error "cli.js not found under $npmBase"
    exit 1
}

$path = $cliFile.FullName
Write-Host "Found: $path" -ForegroundColor Cyan

# --- Check if already patched ---
$content = [System.IO.File]::ReadAllText($path)

if ($content.Contains('case"vscode":return"code-insiders"')) {
    Write-Host "Already patched. Nothing to do." -ForegroundColor Green
    exit 0
}

if (-not $content.Contains('case"vscode":return"code"')) {
    Write-Error "Unexpected cli.js format - cannot find vscode case statement. Claude Code version may have changed structure."
    exit 1
}

# --- Backup ---
$backup = "$path.bak"
if (-not (Test-Path $backup)) {
    Copy-Item $path $backup
    Write-Host "Backup: $backup" -ForegroundColor DarkGray
}

# --- Patch 1: CLI resolver (SW7) ---
$content = $content.Replace(
    'case"vscode":return"code"',
    'case"vscode":return"code-insiders"'
)

# --- Patch 2: VS Code detection (xW7) ---
$content = $content.Replace(
    'await L6("code",["--help"])',
    'await L6("code-insiders",["--help"])'
)

# --- Write ---
[System.IO.File]::WriteAllText($path, $content)

Write-Host "Patched successfully. Restart Claude Code." -ForegroundColor Green

