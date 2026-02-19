#!/usr/bin/env pwsh

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: gemini-cli-wrapper.ps1
# ║ Module: Gemini CLI wrapper
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: UTILITY
# ║ Semantic ID: SCRIPT_GEMINI_CLI_WRAPPER_V1
# ║ Purpose: Wrap Gemini CLI to disable MCP discovery during Bun startup
# ║ Exports: (none)
# ║ Flags/Modes: -Arguments
# ║ Cross-References: (none)
# ╚════════════════════════════════════════════════════════════════════════════

# Gemini CLI Wrapper - Disable MCP crash on startup
# Bun is drop-in Node replacement with node_modules support
# Issue: Gemini CLI MCP discovery fails on startup → crash
# Fix: Set GEMINI_DISABLE_MCP env var before execution

param(
    [Alias("m")]
    [string]$Model,

    [Alias("p")]
    [string]$Prompt,

    [Alias("i")]
    [string]$PromptInteractive,

    [Alias("y")]
    [switch]$Yolo,

    [Alias("h")]
    [switch]$Help,

    [Alias("v")]
    [switch]$Version,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

# Disable MCP discovery to prevent Bun crash during startup
$env:GEMINI_DISABLE_MCP = "1"

$cliArgs = @()

if ($PSBoundParameters.ContainsKey("Model")) {
    $cliArgs += @("-m", $Model)
}
if ($PSBoundParameters.ContainsKey("Prompt")) {
    $cliArgs += @("--prompt", $Prompt)
}
if ($PSBoundParameters.ContainsKey("PromptInteractive")) {
    $cliArgs += @("--prompt-interactive", $PromptInteractive)
}
if ($Yolo) {
    $cliArgs += "--yolo"
}
if ($Help) {
    $cliArgs += "--help"
}
if ($Version) {
    $cliArgs += "--version"
}
if ($Arguments) {
    $cliArgs += $Arguments
}

$geminiCmd = Get-Command gemini -ErrorAction SilentlyContinue
if ($geminiCmd -and $geminiCmd.Source) {
    & $geminiCmd.Source @cliArgs
    exit $LASTEXITCODE
}

# Fallback execution via Bun global package path.
$geminiCliPath = Join-Path $env:USERPROFILE ".bun\install\global\node_modules\@google\gemini-cli\dist\index.js"
if (-not (Test-Path $geminiCliPath)) {
    Write-Error "Gemini CLI not found. Checked: gemini.exe on PATH and $geminiCliPath"
    Write-Host "Reinstall with: bun install -g @google/gemini-cli" -ForegroundColor Yellow
    exit 1
}

& bun $geminiCliPath @cliArgs
