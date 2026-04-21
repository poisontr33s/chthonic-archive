#!/usr/bin/env pwsh
# @SID: SCRIPT_FORTIFY_TERMINAL_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: fortify_terminal.ps1
# ║ Module: Terminal hardening
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: INFRASTRUCTURE
# ║ Semantic ID: SCRIPT_FORTIFY_TERMINAL_V1
# ║ Purpose: Harden terminal for high-throughput automation
# ║ Exports: (none)
# ║ Flags/Modes: (none)
# ║ Cross-References: (none)
# ╚════════════════════════════════════════════════════════════════════════════

Write-Host "🛡️  Fortifying Terminal for High-Throughput Automation..." -ForegroundColor Cyan

# 1. Force UTF-8 Encoding
# Prevents character encoding mismatches that can sever pipes or crash the runner
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
Write-Host "   ✅ Output Encoding set to UTF-8" -ForegroundColor Gray
Write-Host "   ✅ Input Encoding set to UTF-8" -ForegroundColor Gray

# 2. Disable QuickEdit Mode
# In QuickEdit mode, clicking in the console pauses output processing,
# which fills the stdout buffer and freezes the single-threaded Node/Bun process.
[System.Console]::TreatControlCAsInput = $false
Write-Host "   ✅ QuickEdit Mode mitigated (TreatControlCAsInput = false)" -ForegroundColor Gray

Write-Host "🚀 Terminal fortified. Ready for Bun + Playwright CDP operations." -ForegroundColor Cyan

