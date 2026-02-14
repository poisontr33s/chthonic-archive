#!/usr/bin/env pwsh

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: pause_agents.ps1
# ║ Module: Agent pause emergency switch
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: EMERGENCY
# ║ Semantic ID: SCRIPT_PAUSE_AGENTS_V1
# ║ Purpose: Pause all agent operations via VS Code settings
# ║ Exports: (none)
# ║ Flags/Modes: (none)
# ║ Cross-References: .vscode/settings.json
# ╚════════════════════════════════════════════════════════════════════════════

# ============================================================================
# PAUSE ALL AGENTS - Emergency Cognitive Relief
# Chthonic Archive - Information Sovereignty Protocol
# ============================================================================
# Purpose: Immediately halt ALL automated agents to restore clarity
# Usage:   .\scripts\pause_agents.ps1
# Recovery: Restart VS Code or manually set operationalMode back to "essential"
# ============================================================================

Write-Host ""
Write-Host "\ud83d\uded1 ============================================" -ForegroundColor Red
Write-Host "\ud83d\uded1  EMERGENCY PAUSE - ALL AGENTS DISABLED" -ForegroundColor Red
Write-Host "\ud83d\uded1 ============================================" -ForegroundColor Red
Write-Host ""

$REPO_ROOT = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$settingsPath = Join-Path $REPO_ROOT ".vscode\settings.json"

if (-not (Test-Path $settingsPath)) {
    Write-Host "\u274c ERROR: Settings file not found at: $settingsPath" -ForegroundColor Red
    exit 1
}

# Backup current settings
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = Join-Path (Split-Path $settingsPath) "settings_backup_$timestamp.json"
Copy-Item $settingsPath $backupPath -Force
Write-Host "\u2705 Settings backup created: $backupPath" -ForegroundColor Green

# Read and parse settings
try {
    $settingsContent = Get-Content $settingsPath -Raw

    # Update operational mode to paused (simple string replacement for JSONC)
    $settingsContent = $settingsContent -replace '"chthonic\.operationalMode"\s*:\s*"[^"]*"', '"chthonic.operationalMode": "paused"'
    $settingsContent = $settingsContent -replace '"chthonic\.allowCompetingAgents"\s*:\s*(true|false)', '"chthonic.allowCompetingAgents": false'
    $settingsContent = $settingsContent -replace '"chthonic\.sessionTargetOverride"\s*:\s*(true|false)', '"chthonic.sessionTargetOverride": false'

    # Add timestamp
    $now = (Get-Date).ToString("o")
    $settingsContent = $settingsContent -replace '"chthonic\.ssotLastVerified"\s*:\s*(null|"[^"]*")', "`"chthonic.ssotLastVerified`": `"$now (PAUSED)`""

    # Write back
    Set-Content $settingsPath -Value $settingsContent -NoNewline

    Write-Host ""
    Write-Host "\u2705 OPERATIONAL MODE: PAUSED" -ForegroundColor Green
    Write-Host "\u2705 Competing agents: BLOCKED" -ForegroundColor Green
    Write-Host "\u2705 Set Session Target: OVERRIDDEN" -ForegroundColor Green
    Write-Host ""
    Write-Host "\ud83d\udd36 ALL AGENTS NOW SILENT \ud83d\udd36" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To resume:" -ForegroundColor Cyan
    Write-Host "  1. Restart VS Code" -ForegroundColor Cyan
    Write-Host "  2. Or manually edit settings.json:" -ForegroundColor Cyan
    Write-Host "     Set 'chthonic.operationalMode' to 'essential' or 'development'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Backup location: $backupPath" -ForegroundColor DarkGray
    Write-Host ""

} catch {
    Write-Host "\u274c ERROR: Failed to update settings.json" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Backup preserved at: $backupPath" -ForegroundColor Yellow
    exit 1
}
