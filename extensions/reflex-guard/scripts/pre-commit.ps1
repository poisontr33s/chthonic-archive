#!/usr/bin/env pwsh

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
$guard = Join-Path $repoRoot "extensions/reflex-guard/.chthonic/reflex_guard.py"

if (-not (Test-Path $guard)) {
    Write-Host "[REFLEX-GUARD] Guard script not found at $guard"
    exit 0
}

uv run $guard --staged
exit $LASTEXITCODE

