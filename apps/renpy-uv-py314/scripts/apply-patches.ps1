#!/usr/bin/env pwsh
# apply-patches.ps1
#
# Resets vendor/renpy to its tagged commit and applies every *.patch in
# patches/ in lexical order. Idempotent — safe to re-run.
#
# Usage:
#   .\scripts\apply-patches.ps1                # apply all
#   .\scripts\apply-patches.ps1 -Reset         # reset only, no apply
#   .\scripts\apply-patches.ps1 -ListOnly      # show what would happen

[CmdletBinding()]
param(
    [switch]$Reset,
    [switch]$ListOnly
)

$ErrorActionPreference = "Stop"

$LANE_ROOT = Split-Path -Parent $PSScriptRoot
$VENDOR    = Join-Path $LANE_ROOT "vendor\renpy"
$PATCHES   = Join-Path $LANE_ROOT "patches"
$PIN_TAG   = "8.5.3.26051504"

if (-not (Test-Path $VENDOR)) {
    Write-Error "vendor/renpy not found at $VENDOR. Clone it first:`n  cd vendor && git clone --depth 50 --branch $PIN_TAG https://github.com/renpy/renpy.git"
    exit 1
}

# 1) Reset to clean tagged state.
Write-Host "=== Resetting vendor/renpy to $PIN_TAG ==="
Push-Location $VENDOR
try {
    if ($ListOnly) {
        Write-Host "  would: git reset --hard $PIN_TAG"
    } else {
        git fetch --tags --depth 50 origin 2>&1 | Out-Null
        git reset --hard "tags/$PIN_TAG" 2>&1 | Tee-Object -Variable resetOut | Out-Null
        Write-Host "  $($resetOut[0])"
    }
} finally {
    Pop-Location
}

if ($Reset) { return }

# 2) Apply patches in lexical order.
$patchFiles = @(Get-ChildItem $PATCHES -Filter "*.patch" -ErrorAction SilentlyContinue | Sort-Object Name)
if ($patchFiles.Count -eq 0) {
    Write-Host "INFO: no patches in $PATCHES"
    return
}

Write-Host "`n=== Applying $($patchFiles.Count) patch(es) ==="
Push-Location $VENDOR
try {
    foreach ($p in $patchFiles) {
        Write-Host "  -> $($p.Name)"
        if ($ListOnly) {
            Write-Host "     would: git apply --check --3way $($p.FullName)"
            continue
        }
        # Validate cleanly first, then apply.
        & git apply --check --3way $p.FullName 2>&1 | Tee-Object -Variable checkOut | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Patch validation failed for $($p.Name):`n$($checkOut -join "`n")"
            exit 2
        }
        & git apply --3way $p.FullName 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Patch apply failed for $($p.Name) (validate passed but apply did not — git state may need cleanup)"
            exit 3
        }
    }
} finally {
    Pop-Location
}

Write-Host "`n=== All patches applied ==="
Push-Location $VENDOR
try {
    Write-Host "Modified files in vendor/renpy:"
    & git status --short
} finally {
    Pop-Location
}
