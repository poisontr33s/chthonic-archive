#!/usr/bin/env pwsh

# @SID: SCRIPT_COPERNICUS_CREDS_SETUP_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: setup-copernicus-creds.ps1
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ scripts/cm_sdb_fetch.py (consumes CMEMS_USER/CMEMS_PASS this sets)
# ╚════════════════════════════════════════════════════════════════════════════

<#
.SYNOPSIS
One-time interactive setup for Copernicus Marine (CMEMS) credentials.

.DESCRIPTION
Prompts for your Copernicus Marine username and password (password input is
masked, never echoed to the screen or written to any log) and persists both
as CMEMS_USER / CMEMS_PASS user-scope environment variables. Run this once,
after registering a free account at marine.copernicus.eu. A fresh terminal —
or the next command run by any tool, including Claude Code — will pick the
credentials up automatically; nothing else needs to be restarted.

Usage:
    .\scripts\setup-copernicus-creds.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "`nCopernicus Marine credential setup" -ForegroundColor Cyan
Write-Host "Your password is masked as you type and is never displayed, logged, or stored in plain text on screen.`n" -ForegroundColor DarkGray

$username = Read-Host "Copernicus Marine username"
$securePassword = Read-Host "Copernicus Marine password" -AsSecureString
$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
try {
    $plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
} finally {
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

[System.Environment]::SetEnvironmentVariable("CMEMS_USER", $username, "User")
[System.Environment]::SetEnvironmentVariable("CMEMS_PASS", $plainPassword, "User")

$plainPassword = $null
$securePassword = $null
[System.GC]::Collect()

Write-Host "`nDone — CMEMS_USER / CMEMS_PASS are persisted to your Windows user profile." -ForegroundColor Green
Write-Host "You don't need to do anything else; the next command that reads them will just find them." -ForegroundColor Green
