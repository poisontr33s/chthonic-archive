#!/usr/bin/env pwsh
# @SID: SCRIPT_PROFILE_DIAG_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: profile-diag.ps1
# ║ Module: Profile timing diagnostics
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: DIAGNOSTIC
# ║ Purpose: Diagnose profile startup timing and OneDrive impact
# ║ Exports: (none)
# ║ Flags/Modes: (none)
# ║ Cross-References: scripts/chthonic.ps1
# ╚════════════════════════════════════════════════════════════════════════════

# Profile diagnostic script
Write-Host "=== Profile Component Timing ===" -ForegroundColor Cyan

Write-Host "`n1. UTF-8 encoding..."
$t1 = Measure-Command {
    [Console]::InputEncoding = [Console]::OutputEncoding = $OutputEncoding = [System.Text.Encoding]::UTF8
}
Write-Host "   $($t1.TotalMilliseconds)ms" -ForegroundColor Green

Write-Host "`n2. Test-Path chthonic.ps1..."
$t2 = Measure-Command {
    Test-Path "C:\Users\erdno\chthonic-archive\scripts\chthonic.ps1"
}
Write-Host "   $($t2.TotalMilliseconds)ms" -ForegroundColor Green

Write-Host "`n3. Chthonic env -Quiet (THE SLOW ONE?)..."
$t3 = Measure-Command {
    & "C:\Users\erdno\chthonic-archive\scripts\chthonic.ps1" env -Quiet
}
Write-Host "   $($t3.TotalSeconds) seconds" -ForegroundColor $(if ($t3.TotalSeconds -gt 5) { "Red" } else { "Green" })

Write-Host "`n4. Set-Alias..."
$t4 = Measure-Command {
    Set-Alias -Name diagcode -Value code-insiders -Scope Global
}
Write-Host "   $($t4.TotalMilliseconds)ms" -ForegroundColor Green

Write-Host "`n=== TOTAL ===" -ForegroundColor Cyan
$total = $t1.TotalSeconds + $t2.TotalSeconds + $t3.TotalSeconds + $t4.TotalSeconds
Write-Host "   $total seconds" -ForegroundColor $(if ($total -gt 10) { "Red" } else { "Green" })

# Also check if OneDrive might be the issue
Write-Host "`n=== Profile Location ===" -ForegroundColor Cyan
Write-Host "   $PROFILE"
if ($PROFILE -like "*OneDrive*") {
    Write-Host "   WARNING: Profile is in OneDrive - may cause delays!" -ForegroundColor Yellow
}

