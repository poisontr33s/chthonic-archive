#!/usr/bin/env pwsh
# @SID: SCRIPT_CHECK_PROFILES_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: check-profiles.ps1
# ║ Module: PowerShell profile locations
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: DIAGNOSTIC
# ║ Purpose: Print PowerShell profile paths and existence checks
# ║ Exports: (none)
# ║ Flags/Modes: (none)
# ║ Cross-References: (none)
# ╚════════════════════════════════════════════════════════════════════════════

# Show all profile locations
Write-Host "=== PowerShell Profile Locations ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "AllUsersAllHosts:" -ForegroundColor Yellow
Write-Host "  $($PROFILE.AllUsersAllHosts)"
Write-Host ""
Write-Host "AllUsersCurrentHost:" -ForegroundColor Yellow
Write-Host "  $($PROFILE.AllUsersCurrentHost)"
Write-Host ""
Write-Host "CurrentUserAllHosts:" -ForegroundColor Yellow
Write-Host "  $($PROFILE.CurrentUserAllHosts)"
Write-Host ""
Write-Host "CurrentUserCurrentHost (default):" -ForegroundColor Yellow
Write-Host "  $($PROFILE.CurrentUserCurrentHost)"
Write-Host ""
Write-Host "=== Which exist? ===" -ForegroundColor Cyan
Write-Host "AllUsersAllHosts: $(Test-Path $PROFILE.AllUsersAllHosts)"
Write-Host "AllUsersCurrentHost: $(Test-Path $PROFILE.AllUsersCurrentHost)"
Write-Host "CurrentUserAllHosts: $(Test-Path $PROFILE.CurrentUserAllHosts)"
Write-Host "CurrentUserCurrentHost: $(Test-Path $PROFILE.CurrentUserCurrentHost)"
Write-Host ""
Write-Host "Local copy exists: $(Test-Path (Join-Path $env:USERPROFILE 'Documents\PowerShell\Microsoft.PowerShell_profile.ps1'))"

