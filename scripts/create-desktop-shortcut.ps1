#!/usr/bin/env pwsh
# @SID: CREATE_DESKTOP_SHORTCUT_V1
#
# Creates a Windows desktop shortcut (.lnk) that launches VS Code Insiders
# with the chthonic-archive workspace AND the anti-flicker GPU flags.
#
# Idempotent: re-running overwrites the existing shortcut if any. Safe to
# re-run after VS Code Insiders updates (path stays the same on Windows).
#
# Usage:
#   .\scripts\create-desktop-shortcut.ps1
#
# Result:
#   <Desktop>\Chthonic Archive Workspace.lnk
#   Double-click to launch VS Code Insiders with all GPU flags + workspace.

$ErrorActionPreference = 'Stop'

$CodeExe = "$env:LOCALAPPDATA\Programs\Microsoft VS Code Insiders\Code - Insiders.exe"
$Workspace = (Join-Path $PSScriptRoot '..\chthonic-archive.code-workspace' | Resolve-Path).Path
$RepoRoot = (Join-Path $PSScriptRoot '..' | Resolve-Path).Path
$DesktopDir = [System.Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $DesktopDir 'Chthonic Archive Workspace.lnk'

if (-not (Test-Path $CodeExe)) {
    Write-Error "Code - Insiders.exe not found at: $CodeExe"
    exit 1
}
if (-not (Test-Path $Workspace)) {
    Write-Error "Workspace file not found: $Workspace"
    exit 1
}

# Anti-flicker GPU flags (matches user's existing manual shortcut) + workspace.
# Quote the workspace path so spaces in the path are preserved as one argument.
$Arguments = '--ignore-gpu-blocklist --use-vulkan --enable-features=Vulkan --disable-gpu-compositing --enable-gpu-rasterization --enable-native-gpu-memory-buffers "' + $Workspace + '"'

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $CodeExe
$Shortcut.Arguments = $Arguments
$Shortcut.WorkingDirectory = $RepoRoot
$Shortcut.IconLocation = "$CodeExe,0"
$Shortcut.Description = 'Launch VS Code Insiders with the chthonic-archive workspace and anti-flicker GPU flags.'
$Shortcut.Save()

Write-Host "Created desktop shortcut:"
Write-Host "  Path:      $ShortcutPath"
Write-Host "  Target:    $CodeExe"
Write-Host "  Arguments: $Arguments"
Write-Host "  WorkDir:   $RepoRoot"
Write-Host ""
Write-Host "Double-click the new shortcut on your desktop to launch."
