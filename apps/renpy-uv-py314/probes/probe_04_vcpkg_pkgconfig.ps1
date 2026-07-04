#!/usr/bin/env pwsh
# Probe 04 — Phase 1 acceptance gate.
#
# Verifies that after install-native-deps.ps1 runs, every native dep that
# Ren'Py setup.py wants via pkg-config is resolvable through the lane's
# vcpkg-managed pkgconf.
#
# Pre-req:  . .\scripts\Enter-RenPyBuildShell.ps1
# Run:      pwsh -NoProfile -File probes/probe_04_vcpkg_pkgconfig.ps1

$ErrorActionPreference = "Continue"

# Phase 1 acceptance set. ffmpeg's 5 .pc files (libav*) are intentionally
# under a waiver -- vcpkg port at baseline 821100d96 cannot bootstrap its
# MSYS2 toolchain because msys2-file-5.45-1 was delisted from mirrors.
# Phase 2 handles renpy.audio.renpysound separately (skip-if-missing patch).
$pkgs = @(
    "sdl2", "SDL2_image", "libpng", "libjpeg",
    "freetype2", "harfbuzz", "fribidi",
    "openssl", "assimp"
)
# Optional set, not part of the acceptance gate -- reported but not gated.
$ffmpegPkgs = @("libavformat", "libavcodec", "libavutil", "libswresample", "libswscale")

# pkgconf is the binary; pkg-config is the alias. Try both.
$pc = Get-Command pkg-config -ErrorAction SilentlyContinue
if (-not $pc) { $pc = Get-Command pkgconf -ErrorAction SilentlyContinue }

if (-not $pc) {
    Write-Host "FAIL: neither pkg-config nor pkgconf on PATH"
    Write-Host "      Did you dot-source scripts/Enter-RenPyBuildShell.ps1?"
    exit 2
}

Write-Host "=== Probe 04: vcpkg pkg-config resolution ==="
Write-Host "pkg-config tool : $($pc.Source)"
Write-Host "PKG_CONFIG_PATH : $env:PKG_CONFIG_PATH"
Write-Host ""

$pass = 0
$fail = 0
$missing = @()

foreach ($p in $pkgs) {
    $exists = & $pc.Source --exists $p 2>$null
    if ($LASTEXITCODE -eq 0) {
        $version = & $pc.Source --modversion $p 2>$null
        Write-Host ("OK     {0,-18} {1}" -f $p, $version)
        $pass++
    } else {
        Write-Host ("MISS   {0}" -f $p)
        $fail++
        $missing += $p
    }
}

Write-Host ""
Write-Host "--- ffmpeg (waiver, not gated) ---"
$ffmpegPresent = 0
foreach ($p in $ffmpegPkgs) {
    $exists = & $pc.Source --exists $p 2>$null
    if ($LASTEXITCODE -eq 0) {
        $version = & $pc.Source --modversion $p 2>$null
        Write-Host ("OK     {0,-18} {1}" -f $p, $version)
        $ffmpegPresent++
    } else {
        Write-Host ("WAIVE  {0}" -f $p)
    }
}

Write-Host ""
Write-Host "=== Summary ==="
Write-Host "Phase 1 gate    : $pass / $($pkgs.Count) required"
Write-Host "ffmpeg (waiver) : $ffmpegPresent / $($ffmpegPkgs.Count) optional"
if ($fail -gt 0) {
    Write-Host "Missing : $($missing -join ', ')"
    exit 1
}

Write-Host "PASS: all 9 Ren'Py non-audio native deps resolve via vcpkg pkg-config"
exit 0
