#!/usr/bin/env pwsh
# check-install-status.ps1
#
# Inspects the lane's vcpkg_installed/ tree and reports which of the 14
# Ren'Py native deps are present. Use while a long install is running
# (or after the fact) to track progress without re-running vcpkg.
#
# Usage:
#   .\scripts\check-install-status.ps1
#   .\scripts\check-install-status.ps1 -Tail 40       # also tail vcpkg-install.log

[CmdletBinding()]
param(
    [int]$Tail = 0
)

$LANE_ROOT = Split-Path -Parent $PSScriptRoot
$TRIPLET = if ($env:VCPKG_DEFAULT_TRIPLET) { $env:VCPKG_DEFAULT_TRIPLET } else { "x64-windows" }
$INSTALL_ROOT = Join-Path $LANE_ROOT "vcpkg_installed\$TRIPLET"
$LOG = Join-Path $LANE_ROOT "vcpkg-install.log"

# Native-dep checklist mirrors what Ren'Py setup.py asks for via pkg-config.
$expected = @{
    "pkgconf"        = @{ pc = $null;            tool = "pkgconf" }
    "zlib"           = @{ pc = "zlib";           tool = $null }
    "libpng"         = @{ pc = "libpng";         tool = $null }
    "libjpeg-turbo"  = @{ pc = "libjpeg";        tool = $null }
    "freetype"       = @{ pc = "freetype2";      tool = $null }
    "fribidi"        = @{ pc = "fribidi";        tool = $null }
    "openssl"        = @{ pc = "openssl";        tool = $null }
    "harfbuzz"       = @{ pc = "harfbuzz";       tool = $null }
    "sdl2"           = @{ pc = "sdl2";           tool = $null }
    "sdl2-image"     = @{ pc = "SDL2_image";     tool = $null }
    "assimp"         = @{ pc = "assimp";         tool = $null }
    "ffmpeg-fmt"     = @{ pc = "libavformat";    tool = $null }
    "ffmpeg-codec"   = @{ pc = "libavcodec";     tool = $null }
    "ffmpeg-util"    = @{ pc = "libavutil";      tool = $null }
    "ffmpeg-swr"     = @{ pc = "libswresample";  tool = $null }
    "ffmpeg-sws"     = @{ pc = "libswscale";     tool = $null }
}

Write-Host "=== Lane install status ==="
Write-Host "  install root : $INSTALL_ROOT"
Write-Host ""

if (-not (Test-Path $INSTALL_ROOT)) {
    Write-Host "INFO   no vcpkg_installed/ yet. Install hasn't reached lockfile commit."
    if (Test-Path $LOG) {
        $lines = (Get-Content $LOG | Measure-Object -Line).Lines
        Write-Host "       log : $LOG ($lines lines)"
    }
    return
}

$pcDir   = Join-Path $INSTALL_ROOT "lib\pkgconfig"
$toolDir = Join-Path $INSTALL_ROOT "tools"

$pcsOnDisk   = @()
$toolsOnDisk = @()
if (Test-Path $pcDir)   { $pcsOnDisk   = @(Get-ChildItem $pcDir -Filter *.pc | ForEach-Object { $_.BaseName }) }
if (Test-Path $toolDir) { $toolsOnDisk = @(Get-ChildItem $toolDir -Directory  | ForEach-Object { $_.Name }) }

$present = 0
foreach ($name in ($expected.Keys | Sort-Object)) {
    $spec = $expected[$name]
    $ok = $false
    if ($spec.pc -and $pcsOnDisk -contains $spec.pc) { $ok = $true }
    if ($spec.tool -and $toolsOnDisk -contains $spec.tool) { $ok = $true }
    $marker = if ($ok) { "OK   " } else { "wait " }
    Write-Host ("  {0} {1,-15}  pc={2,-14} tool={3}" -f $marker, $name, ($spec.pc ?? "-"), ($spec.tool ?? "-"))
    if ($ok) { $present++ }
}

Write-Host ""
Write-Host "Resolved: $present / $($expected.Count)"

if ($Tail -gt 0 -and (Test-Path $LOG)) {
    Write-Host ""
    Write-Host "--- last $Tail lines of vcpkg-install.log ---"
    Get-Content $LOG -Tail $Tail
}
