#!/usr/bin/env pwsh
# build-renpy.ps1
#
# Orchestrates the Ren'Py 8.5.2 source build against uv-managed Python 3.14.
# Verifies prerequisites, applies patches, runs setup.py via uv pip install -e,
# and confirms the resulting renpy package imports + Cython modules load.
#
# Pre-req: dot-source scripts/Enter-RenPyBuildShell.ps1 first.
#
# Usage:
#   .\scripts\build-renpy.ps1               # full build
#   .\scripts\build-renpy.ps1 -SkipPatches  # use whatever state vendor/renpy is in
#   .\scripts\build-renpy.ps1 -Generate     # only run setup.py generate (no compile)

[CmdletBinding()]
param(
    [switch]$SkipPatches,
    [switch]$Generate
)

$ErrorActionPreference = "Stop"

$LANE_ROOT = Split-Path -Parent $PSScriptRoot
$VENDOR    = Join-Path $LANE_ROOT "vendor\renpy"
$INSTALLED = Join-Path $LANE_ROOT "vcpkg_installed\x64-windows"

# 0) Sanity checks.
Write-Host "=== Build prerequisites ==="

$cl = Get-Command cl -ErrorAction SilentlyContinue
if (-not $cl) {
    Write-Error "cl.exe not on PATH. Did you dot-source scripts/Enter-RenPyBuildShell.ps1?"
    exit 1
}
Write-Host "  cl              : $($cl.Source)"

$pkgconf = Get-Command pkgconf -ErrorAction SilentlyContinue
if (-not $pkgconf) { $pkgconf = Get-Command pkg-config -ErrorAction SilentlyContinue }
if (-not $pkgconf) {
    Write-Error "pkgconf not on PATH. Re-source scripts/Enter-RenPyBuildShell.ps1."
    exit 1
}
Write-Host "  pkgconf         : $($pkgconf.Source)"
Write-Host "  PKG_CONFIG_PATH : $env:PKG_CONFIG_PATH"

if (-not (Test-Path $VENDOR)) {
    Write-Error "vendor/renpy missing. Clone first."
    exit 1
}

# 1) Reset + apply patches.
if (-not $SkipPatches) {
    & "$PSScriptRoot\apply-patches.ps1"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# 2) Hand off pkg-config-resolvable include / lib paths to setup.py via env.
#    Ren'Py's setuplib.parse_cflags / parse_libs invoke pkg-config; we just
#    need PKG_CONFIG_PATH (set) and the pkg-config binary on PATH (set).
#    Set RENPY_DEPS_INSTALL pointing at the vcpkg-installed prefix as well so
#    its setuplib can locate vendored DLLs at link time.
$env:RENPY_DEPS_INSTALL = $INSTALLED
Write-Host "  RENPY_DEPS_INSTALL = $env:RENPY_DEPS_INSTALL"

# Ren'Py's setup.py uses sys.platform-style branching; on Windows it expects
# a pkg-config-style toolchain. The cython binary ships in our uv venv.
$env:RENPY_CYTHON = (Join-Path $LANE_ROOT ".venv\Scripts\cython.exe")
if (-not (Test-Path $env:RENPY_CYTHON)) {
    Write-Error "cython.exe not found in lane .venv. Run: uv sync --group build"
    exit 1
}
Write-Host "  RENPY_CYTHON    = $env:RENPY_CYTHON"

# Pre-compute CFLAGS/LDFLAGS via pkgconf and pass them as RENPY_* env vars.
# Ren'Py setup.py invokes literal `pkg-config` which doesn't exist on Windows;
# vcpkg ships `pkgconf` instead. setuplib.env() honors RENPY_CFLAGS / RENPY_LDFLAGS
# and skips its pkg-config call when those are set.
$pkgconfigPackages = @(
    "libavformat", "libavcodec", "libavutil", "libswresample", "libswscale",
    "harfbuzz", "freetype2", "fribidi", "sdl2"
)
$env:RENPY_CFLAGS  = (& $pkgconf.Source --cflags @pkgconfigPackages 2>&1) -join " "
$env:RENPY_LDFLAGS = (& $pkgconf.Source --libs   @pkgconfigPackages 2>&1) -join " "
Write-Host "  RENPY_CFLAGS    = $($env:RENPY_CFLAGS.Substring(0, [Math]::Min(120, $env:RENPY_CFLAGS.Length)))..."
Write-Host "  RENPY_LDFLAGS   = $($env:RENPY_LDFLAGS.Substring(0, [Math]::Min(120, $env:RENPY_LDFLAGS.Length)))..."

# 3) Run the build.
Push-Location $VENDOR
try {
    if ($Generate) {
        Write-Host "`n=== Running setup.py generate (cython codegen only) ==="
        & uv run --project $LANE_ROOT python setup.py generate
    } else {
        Write-Host "`n=== uv pip install -e (full build) ==="
        & uv pip install -e . --no-build-isolation --project $LANE_ROOT
    }
    $exit = $LASTEXITCODE
} finally {
    Pop-Location
}

Write-Host ""
if ($exit -ne 0) {
    Write-Warning "Build exited with $exit. Check output above."
    exit $exit
}

# 4) Smoke test the install.
Write-Host "`n=== Smoke test ==="
$smokeScript = @'
import sys
print(f"Python: {sys.version.splitlines()[0]}")
import renpy
print(f"renpy version: {renpy.__version__ if hasattr(renpy, '__version__') else '(no __version__ attr)'}")
print(f"renpy package : {renpy.__file__}")

# Try loading a few Cython modules to confirm the build linked correctly.
modules = [
    "renpy.astsupport",
    "renpy.style",
    "renpy.display.matrix",
    "renpy.gl2.gl2draw",
    "renpy.text.textsupport",
]
ok = []
fail = []
for m in modules:
    try:
        __import__(m)
        ok.append(m)
    except Exception as e:
        fail.append((m, type(e).__name__, str(e)[:120]))

print(f"OK   {len(ok)}/{len(modules)} cython modules loaded:")
for m in ok: print(f"    {m}")
if fail:
    print(f"FAIL {len(fail)} cython modules failed to import:")
    for m, et, msg in fail: print(f"    {m}: {et}: {msg}")
    sys.exit(1)
print("PASS: smoke test")
'@

$tempPy = New-TemporaryFile
$tempPy = [System.IO.Path]::ChangeExtension($tempPy, ".py")
Set-Content -Path $tempPy -Value $smokeScript -Encoding UTF8
try {
    & uv run --project $LANE_ROOT python $tempPy
    $exit = $LASTEXITCODE
} finally {
    Remove-Item $tempPy -ErrorAction SilentlyContinue
}

exit $exit
