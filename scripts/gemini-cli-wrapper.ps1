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
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# Disable MCP discovery to prevent Bun crash during startup
$env:GEMINI_DISABLE_MCP = "1"

# Execute via Bun (drop-in Node replacement)
# Use dynamic path relative to User Profile
$geminiCliPath = Join-Path $env:USERPROFILE ".bun\install\global\node_modules\@google\gemini-cli\dist\index.js"

if (-not (Test-Path $geminiCliPath)) {
    Write-Error "Gemini CLI not found at: $geminiCliPath"
    Write-Host "Reinstall with: bun install -g @google/gemini-cli" -ForegroundColor Yellow
    exit 1
}

& bun $geminiCliPath @Arguments
