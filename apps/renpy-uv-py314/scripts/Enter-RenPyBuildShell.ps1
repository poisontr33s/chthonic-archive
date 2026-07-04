#!/usr/bin/env pwsh
# Enter-RenPyBuildShell.ps1
#
# Drops the current pwsh session into a Ren'Py-on-Python-3.14 build shell:
#   - sources MSVC vcvars64 (VS 2022 BuildTools)
#   - sets VCPKG_ROOT to the user's existing vcpkg checkout
#   - prepends vcpkg's installed bin + pkgconf to PATH
#   - sets PKG_CONFIG_PATH so renpy's setup.py can locate sdl2/freetype/etc.
#
# Usage (from a fresh pwsh):
#   . .\scripts\Enter-RenPyBuildShell.ps1
#
# Use the dot-source form ('. .\') so env vars survive into your shell.

$ErrorActionPreference = "Stop"

# ----- Resolve paths -----
$LANE_ROOT = Split-Path -Parent $PSScriptRoot
$VCPKG_ROOT = if ($env:VCPKG_ROOT) { $env:VCPKG_ROOT } else { "C:\Users\eldno\vcpkg" }
$VCVARS = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
$TRIPLET = if ($env:VCPKG_DEFAULT_TRIPLET) { $env:VCPKG_DEFAULT_TRIPLET } else { "x64-windows" }

if (-not (Test-Path $VCPKG_ROOT)) {
    Write-Error "VCPKG_ROOT not found: $VCPKG_ROOT"
    return
}
if (-not (Test-Path $VCVARS)) {
    Write-Error "vcvars64.bat not found: $VCVARS"
    return
}

# ----- Source vcvars64 (MSVC) into pwsh -----
Write-Host "[Enter-RenPyBuildShell] sourcing $VCVARS"
$cmdOutput = & cmd.exe /c "`"$VCVARS`" && set" 2>&1
foreach ($line in $cmdOutput) {
    if ($line -match '^([^=]+)=(.*)$') {
        $name = $Matches[1]
        $value = $Matches[2]
        # Skip noisy diagnostic vars
        if ($name -in @("PROMPT", "_NT_SYMBOL_PATH", "ERRORLEVEL")) { continue }
        Set-Item "Env:$name" $value
    }
}

# ----- vcpkg env -----
$env:VCPKG_ROOT = $VCPKG_ROOT
$env:VCPKG_DEFAULT_TRIPLET = $TRIPLET

# Manifest-mode install dir lives under the lane root, not vcpkg root.
$installed = Join-Path $LANE_ROOT "vcpkg_installed\$TRIPLET"
if (Test-Path $installed) {
    $env:PATH = "$installed\bin;$installed\tools\pkgconf;$env:PATH"
    $env:PKG_CONFIG_PATH = "$installed\lib\pkgconfig"
    # Prepend vcpkg paths to MSVC's native INCLUDE/LIB env vars so cl.exe / link.exe
    # find vcpkg-installed headers and import libraries without per-Extension flags.
    # Ren'Py's setup.py doesn't parse CFLAGS on Windows; this is the path of least
    # patch surface area.
    # Ren'Py's pygame_sdl2-derived .pyx files use bare `#include "SDL.h"` (no SDL2/ prefix).
    # vcpkg installs SDL2 headers under include/SDL2/, so the subdir must also be on INCLUDE.
    $env:INCLUDE = "$installed\include;$installed\include\SDL2;$env:INCLUDE"
    $env:LIB = "$installed\lib;$env:LIB"
    # Renpy's __init__.py reads RENPY_DEPS_INSTALL on Windows and calls
    # os.add_dll_directory() so the cp314 .pyd files can locate vcpkg's SDL2.dll
    # and ffmpeg DLLs at load time (Python 3.8+ no longer searches PATH for
    # extension-module DLLs).
    $env:RENPY_DEPS_INSTALL = $installed
    Write-Host "[Enter-RenPyBuildShell] manifest install present at $installed"
} else {
    # Fallback: classic-mode global install layout
    $classic = Join-Path $VCPKG_ROOT "installed\$TRIPLET"
    $env:PATH = "$classic\bin;$classic\tools\pkgconf;$VCPKG_ROOT;$env:PATH"
    $env:PKG_CONFIG_PATH = "$classic\lib\pkgconfig"
    $env:INCLUDE = "$classic\include;$env:INCLUDE"
    $env:LIB = "$classic\lib;$env:LIB"
    Write-Host "[Enter-RenPyBuildShell] manifest not yet built; falling back to classic install"
}

# ----- Report -----
Write-Host ""
Write-Host "  VCPKG_ROOT       = $env:VCPKG_ROOT"
Write-Host "  VCPKG_DEFAULT_TRIPLET = $env:VCPKG_DEFAULT_TRIPLET"
Write-Host "  PKG_CONFIG_PATH  = $env:PKG_CONFIG_PATH"
Write-Host ""
$cl = Get-Command cl -ErrorAction SilentlyContinue
$pc = Get-Command pkg-config -ErrorAction SilentlyContinue
$pcf = Get-Command pkgconf -ErrorAction SilentlyContinue
Write-Host ("  cl         : " + $(if ($cl) { $cl.Source } else { "(not on PATH)" }))
Write-Host ("  pkg-config : " + $(if ($pc) { $pc.Source } else { "(not on PATH)" }))
Write-Host ("  pkgconf    : " + $(if ($pcf) { $pcf.Source } else { "(not on PATH)" }))
Write-Host ""
Write-Host "[Enter-RenPyBuildShell] ready."
