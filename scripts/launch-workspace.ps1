#!/usr/bin/env pwsh
# @SID: LAUNCH_WORKSPACE_V1
#
# Launches VS Code Insiders with the workspace AND the GPU flags that
# prevent flickering on this machine. Combines both into one invocation
# so the workspace opens fresh (new extension-host session, workspace
# settings re-read) without sacrificing the anti-flicker render config.
#
# Use this whenever you need a TRUE restart of VS Code with the
# workspace loaded — for example, after changing workspace-level
# settings that don't take effect until a full restart.
#
# Usage:
#   .\scripts\launch-workspace.ps1
#
# If multiple Code - Insiders windows are already open, this opens a
# new window. To force-close the previous one first, use --reuse-window
# in the args below (currently NOT enabled to avoid accidentally killing
# unsaved state).

$ErrorActionPreference = 'Stop'

$CodeExe = "$env:LOCALAPPDATA\Programs\Microsoft VS Code Insiders\Code - Insiders.exe"
$Workspace = (Join-Path $PSScriptRoot '..\chthonic-archive.code-workspace' | Resolve-Path).Path

if (-not (Test-Path $CodeExe)) {
    Write-Error "Code - Insiders.exe not found at expected path: $CodeExe"
    exit 1
}

if (-not (Test-Path $Workspace)) {
    Write-Error "Workspace file not found: $Workspace"
    exit 1
}

# Anti-flicker GPU flags matching the user's preferred shortcut config.
$Flags = @(
    '--ignore-gpu-blocklist'
    '--use-vulkan'
    '--enable-features=Vulkan'
    '--disable-gpu-compositing'
    '--enable-gpu-rasterization'
    '--enable-native-gpu-memory-buffers'
)

Write-Host "Launching VS Code Insiders with chthonic-archive workspace ..."
Write-Host "  Exe:       $CodeExe"
Write-Host "  Workspace: $Workspace"
Write-Host "  Flags:     $($Flags -join ' ')"

& $CodeExe @Flags $Workspace
