#!/usr/bin/env pwsh
# uv-python-install.ps1
# Installs a uv-managed Python by FULL patch version with no junction alias
# and no .local/bin shim.
#
# Usage:
#   .\scripts\uv-python-install.ps1 3.14.4
#   .\scripts\uv-python-install.ps1 cpython-3.14.4-windows-x86_64-none
#
# Why uv creates extras by design (not bugs):
#   1. Junction alias  (cpython-3.14-windows-x86_64-none -> real dir)
#      PURPOSE: lets venvs transparently upgrade patch versions.
#      SUPPRESSION: none — uv hardcodes this. Cleaned up post-install.
#   2. PATH shim  (~/.local/bin/python3.14.exe, ~46KB launcher)
#      PURPOSE: makes python3.14 usable as a bare shell command.
#      SUPPRESSION: UV_PYTHON_INSTALL_BIN=0 — prevents creation entirely.
#      (env-var only; no uv.toml key yet as of uv PR #8458)
#
# Neither artifact is needed for `uv run` or `uv sync` — those resolve
# Python through the managed install dir directly.

param(
    [Parameter(Mandatory)][string]$Version
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Normalise: strip leading "cpython-" and trailing platform suffix if present
# Accept either "3.14.4" or "cpython-3.14.4-windows-x86_64-none"
$bare = $Version -replace '^cpython-', '' -replace '-windows-x86_64-none$', ''

# Validate it looks like a full patch version (X.Y.Z)
if ($bare -notmatch '^\d+\.\d+\.\d+$') {
    Write-Error "Provide a full patch version like 3.14.4 (got: $bare). Partial versions (e.g. '3.14') recreate the junction alias — use the full patch."
    exit 1
}

$minorParts = $bare -split '\.'
$major = $minorParts[0]
$minor = $minorParts[1]
$minorVersion = "$major.$minor"   # e.g. "3.14"

$uvPythonDir = "$env:APPDATA\uv\python"
$junctionPath = Join-Path $uvPythonDir "cpython-$minorVersion-windows-x86_64-none"
$shimPath     = "$env:USERPROFILE\.local\bin\python$minorVersion.exe"

# Suppress shim creation at source — UV_PYTHON_INSTALL_BIN=0 tells uv not to
# write the python3.x.exe launcher into UV_PYTHON_BIN_DIR (~/.local/bin).
$env:UV_PYTHON_INSTALL_BIN = "0"

Write-Host "Installing cpython-$bare (shim suppressed via UV_PYTHON_INSTALL_BIN=0) ..." -ForegroundColor Cyan
uv python install "cpython-$bare-windows-x86_64-none"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Remove minor-version junction — no config suppresses this; uv always creates it.
# [Directory]::Delete on a junction removes only the junction point, never contents.
if (Test-Path $junctionPath) {
    $item = Get-Item $junctionPath -Force
    if ($item.LinkType -eq 'Junction') {
        [System.IO.Directory]::Delete($junctionPath)
        Write-Host "Removed junction: $junctionPath" -ForegroundColor Yellow
    } else {
        Write-Warning "Expected a junction at $junctionPath but found $($item.LinkType) — skipping."
    }
} else {
    Write-Host "Junction not present: $junctionPath" -ForegroundColor DarkGray
}

# Shim cleanup — belt-and-suspenders in case UV_PYTHON_INSTALL_BIN was ignored
if (Test-Path $shimPath) {
    Remove-Item $shimPath -Force
    Write-Host "Removed residual shim: $shimPath" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "uv python list (installed only):" -ForegroundColor Cyan
uv python list --only-installed
