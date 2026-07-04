#!/usr/bin/env pwsh
# install-native-deps.ps1
#
# Installs the native deps Ren'Py setup.py needs (sdl2, ffmpeg, freetype,
# harfbuzz, fribidi, openssl, libpng, libjpeg-turbo, sdl2-image, assimp,
# zlib) plus pkgconf for the build chain. Manifest-mode only.
#
# Why manifest-only: the global vcpkg root has its own vcpkg.json so vcpkg
# auto-engages manifest mode whenever the binary runs. Mixing classic-mode
# port specs into our lane fights that. Lane manifest at vcpkg.json is the
# single source of truth; output lands in vcpkg_installed/${TRIPLET}/.
#
# Usage:
#   .\scripts\install-native-deps.ps1                # full install
#   .\scripts\install-native-deps.ps1 -DryRun        # plan only, no build
#   .\scripts\install-native-deps.ps1 -OnlyDownloads # download sources, skip build
#   .\scripts\install-native-deps.ps1 -KeepGoing     # don't stop on first failure

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$OnlyDownloads,
    [switch]$KeepGoing
)

$ErrorActionPreference = "Stop"

$LANE_ROOT = Split-Path -Parent $PSScriptRoot
$VCPKG_ROOT = if ($env:VCPKG_ROOT) { $env:VCPKG_ROOT } else { "C:\Users\eldno\vcpkg" }
$VCPKG_EXE = Join-Path $VCPKG_ROOT "vcpkg.exe"
$TRIPLET = if ($env:VCPKG_DEFAULT_TRIPLET) { $env:VCPKG_DEFAULT_TRIPLET } else { "x64-windows" }
$INSTALL_ROOT = Join-Path $LANE_ROOT "vcpkg_installed"

if (-not (Test-Path $VCPKG_EXE)) {
    Write-Error "vcpkg.exe missing: $VCPKG_EXE"
    exit 1
}

$OVERLAY_PORTS = Join-Path $LANE_ROOT "vcpkg-overlay-ports"

$cmd = @(
    $VCPKG_EXE,
    "install",
    "--triplet", $TRIPLET,
    "--x-manifest-root=$LANE_ROOT",
    "--x-install-root=$INSTALL_ROOT"
)
if (Test-Path $OVERLAY_PORTS) {
    $cmd += "--overlay-ports=$OVERLAY_PORTS"
    Write-Host "  overlay ports : $OVERLAY_PORTS"
}
if ($DryRun)        { $cmd += "--dry-run" }
if ($OnlyDownloads) { $cmd += "--only-downloads" }
if ($KeepGoing)     { $cmd += "--keep-going" }

Write-Host "=== Manifest install (lane vcpkg.json) ==="
Write-Host "  manifest root : $LANE_ROOT"
Write-Host "  install root  : $INSTALL_ROOT"
Write-Host "  triplet       : $TRIPLET"
Write-Host ""
Write-Host ">> $($cmd -join ' ')"
Write-Host ""

& $cmd[0] $cmd[1..($cmd.Length - 1)]
$exit = $LASTEXITCODE

Write-Host "`n=== Result ==="
if (Test-Path "$INSTALL_ROOT\$TRIPLET") {
    $pc = Join-Path "$INSTALL_ROOT\$TRIPLET" "lib\pkgconfig"
    if (Test-Path $pc) {
        $pcs = @(Get-ChildItem $pc -Filter *.pc | ForEach-Object { $_.BaseName })
        Write-Host "  .pc files installed ($($pcs.Count)):"
        $pcs | ForEach-Object { Write-Host "    $_" }
    }
    $tools = Join-Path "$INSTALL_ROOT\$TRIPLET" "tools"
    if (Test-Path $tools) {
        $td = @(Get-ChildItem $tools -Directory | ForEach-Object { $_.Name })
        Write-Host "  tools dirs ($($td.Count)): $($td -join ', ')"
    }
}

if ($exit -ne 0) {
    Write-Warning "vcpkg exited with $exit"
}
exit $exit
