#!/usr/bin/env pwsh

# @SID: SCRIPT_RELAUNCH_VSCODE_INSIDERS_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: relaunch-vscode-insiders.ps1
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: GOLD
# ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Recovery utility for VS Code Insiders auto-update flicker)
# ║   └─◄ (Companion to .vscode/settings.json git.path shim wiring)
# ╚════════════════════════════════════════════════════════════════════════════

<#
.SYNOPSIS
    Closes running VS Code Insiders and relaunches via the conductor's
    flag-bearing desktop shortcut.

.DESCRIPTION
    VS Code Insiders auto-update workflow strips the GPU flags from the
    process command-line on restart. The desktop shortcut at
    "C:\Users\eldno\OneDrive\Desktop\Chthonic Archive Workspace.lnk"
    carries the canonical flag set:
        --ignore-gpu-blocklist
        --use-vulkan
        --enable-features=Vulkan
        --disable-gpu-compositing
        --enable-gpu-rasterization
        --enable-native-gpu-memory-buffers

    After an auto-update, the running instance comes up without these flags,
    causing visual flicker and (per conductor 2026-05-25) occasional session
    instability + missing session logs. This script restores the canonical
    launch path.

.PARAMETER DryRun
    Show what would be done without actually closing/relaunching anything.

.PARAMETER Force
    Skip the graceful close attempt and Stop-Process immediately. Use only
    if Code - Insiders has hung and won't respond to CloseMainWindow.

.NOTES
    CANNOT BE RUN FROM INSIDE VS CODE — it would kill the host terminal.
    Run from an external PowerShell window (Win+X → Windows PowerShell,
    or Start menu → PowerShell).

    Idempotent: safe to re-run if the relaunched instance also misbehaves.

.EXAMPLE
    pwsh -File C:\Users\eldno\chthonic-archive\scripts\relaunch-vscode-insiders.ps1

.EXAMPLE
    # Preview what would happen
    pwsh -File scripts\relaunch-vscode-insiders.ps1 -DryRun
#>
param(
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$shortcut = "C:\Users\eldno\OneDrive\Desktop\Chthonic Archive Workspace.lnk"

# Refuse to run from inside VS Code's integrated terminal (would self-kill)
if ($env:TERM_PROGRAM -eq "vscode" -or $env:VSCODE_PID) {
    Write-Host "[relaunch] DETECTED: running inside VS Code (TERM_PROGRAM=$env:TERM_PROGRAM, VSCODE_PID=$env:VSCODE_PID)" -ForegroundColor Red
    Write-Host "[relaunch] REFUSING to proceed — this script would kill VS Code while running inside it." -ForegroundColor Red
    Write-Host "[relaunch] Open an EXTERNAL PowerShell (Win+X → Terminal, or Start → PowerShell) and run from there." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $shortcut)) {
    Write-Host "[relaunch] ERROR: shortcut not found at $shortcut" -ForegroundColor Red
    Write-Host "[relaunch] Recreate the shortcut with these properties:" -ForegroundColor Yellow
    Write-Host "[relaunch]   Target:    `"C:\Users\eldno\AppData\Local\Programs\Microsoft VS Code Insiders\Code - Insiders.exe`" --ignore-gpu-blocklist --use-vulkan --enable-features=Vulkan --disable-gpu-compositing --enable-gpu-rasterization --enable-native-gpu-memory-buffers" -ForegroundColor Yellow
    Write-Host "[relaunch]   Start in:  `"C:\Users\eldno\AppData\Local\Programs\Microsoft VS Code Insiders`"" -ForegroundColor Yellow
    exit 1
}

$running = @(Get-Process -Name "Code - Insiders" -ErrorAction SilentlyContinue)
Write-Host "[relaunch] Found $($running.Count) running Code - Insiders process(es)" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "[relaunch] [DRY-RUN] would close $($running.Count) process(es) and relaunch $shortcut" -ForegroundColor Yellow
    foreach ($p in $running) {
        Write-Host "[relaunch] [DRY-RUN]   PID $($p.Id) — $($p.MainWindowTitle)" -ForegroundColor Yellow
    }
    exit 0
}

if ($running.Count -gt 0) {
    if ($Force) {
        Write-Host "[relaunch] -Force: Stop-Process immediately" -ForegroundColor Yellow
        $running | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    } else {
        # Try graceful close first
        Write-Host "[relaunch] Attempting graceful CloseMainWindow on $($running.Count) process(es)..." -ForegroundColor Cyan
        foreach ($p in $running) {
            try { $p.CloseMainWindow() | Out-Null } catch {}
        }
        Start-Sleep -Seconds 5

        # Force-kill any stragglers
        $straggle = @(Get-Process -Name "Code - Insiders" -ErrorAction SilentlyContinue)
        if ($straggle.Count -gt 0) {
            Write-Host "[relaunch] $($straggle.Count) straggler(s) — force-killing..." -ForegroundColor Yellow
            $straggle | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
    }
    # Verify all dead
    $final = @(Get-Process -Name "Code - Insiders" -ErrorAction SilentlyContinue)
    if ($final.Count -gt 0) {
        Write-Host "[relaunch] WARNING: $($final.Count) Code - Insiders process(es) still running. Manual intervention may be needed." -ForegroundColor Red
        exit 1
    }
    Write-Host "[relaunch] All Code - Insiders processes closed" -ForegroundColor Green
}

Write-Host "[relaunch] Launching $shortcut ..." -ForegroundColor Cyan
Invoke-Item $shortcut

Write-Host "[relaunch] Done. VS Code Insiders should be relaunching with canonical GPU flags." -ForegroundColor Green
Write-Host "[relaunch] After it loads, verify shim wiring:" -ForegroundColor Cyan
Write-Host "[relaunch]   1. bun run scripts/verify-rescue-shim.ts --reset-log" -ForegroundColor Cyan
Write-Host "[relaunch]   2. (do any git op in source-control panel)" -ForegroundColor Cyan
Write-Host "[relaunch]   3. bun run scripts/verify-rescue-shim.ts --live" -ForegroundColor Cyan
