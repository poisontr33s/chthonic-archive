#!/usr/bin/env pwsh
# Probe 03 — native dependency presence on this Windows host.
#
# Ren'Py setup.py requires these via pkg-config (extracted directly from
# renpy/renpy@master setup.py at audit time):
#   sdl2, SDL2_image, libpng, libjpeg
#   freetype2, harfbuzz, fribidi
#   libavformat, libavcodec, libavutil, libswresample, libswscale
#   openssl, assimp
#
# Plus build tools: pkg-config, cython, a working C/C++ compiler.

$ErrorActionPreference = "Continue"

function Test-Tool {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) {
        try {
            $version = & $Name --version 2>&1 | Select-Object -First 1
            return "OK     $Name  ->  $($cmd.Source)  ($version)"
        } catch {
            return "OK     $Name  ->  $($cmd.Source)  (no --version)"
        }
    }
    return "MISS   $Name"
}

function Test-PkgConfig {
    param([string]$Pkg)
    if (-not (Get-Command pkg-config -ErrorAction SilentlyContinue)) {
        return "SKIP   $Pkg  (pkg-config not on PATH)"
    }
    & pkg-config --exists $Pkg 2>$null
    if ($LASTEXITCODE -eq 0) {
        $version = & pkg-config --modversion $Pkg 2>$null
        return "OK     $Pkg  ($version)"
    }
    return "MISS   $Pkg"
}

Write-Host "=== Probe 03: native deps on this host ==="
Write-Host ""
Write-Host "-- Build tools --"
Test-Tool "pkg-config"
Test-Tool "cl"           # MSVC compiler
Test-Tool "clang"
Test-Tool "gcc"
Test-Tool "ninja"
Test-Tool "cmake"
Test-Tool "git"
Test-Tool "uv"

Write-Host ""
Write-Host "-- Ren'Py native deps via pkg-config --"
$pkgs = @(
    "sdl2", "SDL2_image", "libpng", "libjpeg",
    "freetype2", "harfbuzz", "fribidi",
    "libavformat", "libavcodec", "libavutil",
    "libswresample", "libswscale",
    "openssl", "assimp"
)
foreach ($p in $pkgs) { Test-PkgConfig $p }

Write-Host ""
Write-Host "-- Vulkan SDK / NVIDIA toolchain (Phase 3 only) --"
if ($env:VULKAN_SDK) { Write-Host "OK     VULKAN_SDK = $env:VULKAN_SDK" } else { Write-Host "MISS   VULKAN_SDK env var" }
Test-Tool "glslc"
Test-Tool "vulkaninfo"
if ($env:CUDA_PATH) { Write-Host "OK     CUDA_PATH = $env:CUDA_PATH" } else { Write-Host "MISS   CUDA_PATH env var" }
if (Test-Path "$env:ProgramFiles\NVIDIA Corporation\NVIDIA App") {
    Write-Host "OK     NVIDIA App present"
} else { Write-Host "INFO   NVIDIA App path not found (not required for build)" }
