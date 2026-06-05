#!/usr/bin/env pwsh
# @SID: SCRIPT_FORTIFY_TERMINAL_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: fortify_terminal.ps1
# ║ Module: Terminal hardening
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: INFRASTRUCTURE
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
$OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "   ✅ Output Encoding set to UTF-8" -ForegroundColor Gray
Write-Host "   ✅ Input Encoding set to UTF-8" -ForegroundColor Gray
Write-Host "   ✅ OutputEncoding set to UTF-8 (pwsh pipeline serialization)" -ForegroundColor Gray

# 2. Python UTF-8 mode (PEP 540 + PEP 597)
# Covers uv run, python3, and subprocesses that inherit this environment.
# PYTHONUTF8=1  → PEP 540: global UTF-8 mode (file I/O, stdio, locale)
# PYTHONIOENCODING → PEP 597: explicit stdin/stdout/stderr encoding for pipes/ttys
# Both are required for full coverage. Idempotent — safe if already set.
if (-not $env:PYTHONUTF8)       { $env:PYTHONUTF8       = "1" }
if (-not $env:PYTHONIOENCODING) { $env:PYTHONIOENCODING = "utf-8" }
Write-Host "   ✅ PYTHONUTF8=1 (PEP 540 — global UTF-8 mode)" -ForegroundColor Gray
Write-Host "   ✅ PYTHONIOENCODING=utf-8 (PEP 597 — stdin/stdout/stderr)" -ForegroundColor Gray

# 2. Disable QuickEdit Mode
# In QuickEdit mode, clicking in the console pauses output processing,
# which fills the stdout buffer and freezes the single-threaded Node/Bun process.
[System.Console]::TreatControlCAsInput = $false
Write-Host "   ✅ QuickEdit Mode mitigated (TreatControlCAsInput = false)" -ForegroundColor Gray

Write-Host "🚀 Terminal fortified. Ready for Bun + Playwright CDP operations." -ForegroundColor Cyan

