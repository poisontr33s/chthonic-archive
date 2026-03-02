#!/usr/bin/env pwsh

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: polyglot_env.ps1
# ║ Module: Polyglot Environment Manager
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: configuration/environment
# ║ Architectural Role: Deterministic PATH and toolchain environment setup
# ║ Semantic ID: SCRIPT_POLYGLOT_ENV_V1
# ║ Purpose: Apply or display resolved toolchain paths from probe output
# ║ Exports: Session PATH modifications, resolved tool locations display
# ║ Flags/Modes: -Apply (set PATH), -Show (display only)
# ║ Cross-References: probe_toolchain_path.ps1, shell_capabilities.ps1
# ╚════════════════════════════════════════════════════════════════════════════

[CmdletBinding()]
param(
  # Apply deterministic PATH into the current session.
  [switch]$Apply,

  # Print resolved tool locations (from the probe output on disk).
  [switch]$Show
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$probe = Join-Path $repoRoot 'scripts\probe_toolchain_path.ps1'

if (-not (Test-Path -LiteralPath $probe)) {
  throw "Missing probe script: $probe"
}

$doApply = [bool]$Apply -or (-not $Show)
if ($doApply) {
  & $probe -ApplyToSession | Out-Null
}

$probeRoot = Join-Path $repoRoot 'dumpster-dive\intake\toolchain-probe'
if (-not (Test-Path -LiteralPath $probeRoot)) {
  throw "Missing probe output root: $probeRoot"
}

$latest = Get-ChildItem -LiteralPath $probeRoot -Directory | Sort-Object Name -Descending | Select-Object -First 1
if (-not $latest) {
  throw "No probe runs found under: $probeRoot"
}

$resolvedTxt = Join-Path $latest.FullName 'resolved.txt'
$toolchainJson = Join-Path $latest.FullName 'toolchain.json'

Write-Host "polyglot_env: $(Split-Path -Leaf $latest.FullName)"
Write-Host "resolved:     $resolvedTxt"
Write-Host "manifest:     $toolchainJson"

if (Test-Path -LiteralPath $resolvedTxt) {
  Get-Content -LiteralPath $resolvedTxt -TotalCount 200
}

