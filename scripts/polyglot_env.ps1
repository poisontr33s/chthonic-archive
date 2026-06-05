#!/usr/bin/env pwsh
# @SID: SCRIPT_POLYGLOT_ENV_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: polyglot_env.ps1
# ║ Module: Polyglot Environment Manager
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: configuration/environment
# ║ Architectural Role: Deterministic PATH and toolchain environment setup
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
  [switch]$Show,

  # Validate toolchain health via sfs.ps1 --verify.
  [switch]$Verify
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$probe = Join-Path $repoRoot 'scripts\probe_toolchain_path.ps1'

if (-not (Test-Path -LiteralPath $probe)) {
  throw "Missing probe script: $probe"
}

$probeRoot = Join-Path $repoRoot 'dumpster-dive\intake\toolchain-probe'
$latestExisting = if (Test-Path -LiteralPath $probeRoot) {
  Get-ChildItem -LiteralPath $probeRoot -Directory | Sort-Object Name -Descending | Select-Object -First 1
} else { $null }

$doApply = [bool]$Apply -or (-not $Show -and -not $Verify)
if ($doApply) {
  $probeFresh = $latestExisting -and ((Get-Date) - $latestExisting.LastWriteTime).TotalHours -lt 24 -and -not $Apply
  if ($probeFresh) {
    Write-Host "polyglot_env: probe output fresh (< 24h), skipping re-run" -ForegroundColor DarkGray
    $cachedPathFile = Get-ChildItem -LiteralPath $latestExisting.FullName -Filter 'probed_path_*.txt' -EA SilentlyContinue | Select-Object -First 1
    if ($cachedPathFile) {
      $env:Path = (Get-Content -LiteralPath $cachedPathFile.FullName -Raw).Trim()
    }
  } else {
    & $probe -ApplyToSession | Out-Null
  }
  Write-Host "polyglot_env: Applied — PATH updated for this session." -ForegroundColor Green
}

if ($Verify) {
  $sfsScript = Join-Path $PSScriptRoot 'sfs.ps1'
  if (Test-Path -LiteralPath $sfsScript) {
    & $sfsScript --verify
  } else {
    Write-Warning "polyglot_env: sfs.ps1 not found — skipping verify"
  }
}

if (-not (Test-Path -LiteralPath $probeRoot)) {
  throw "Missing probe output root: $probeRoot"
}

$latest = if ($latestExisting) { $latestExisting } else {
  Get-ChildItem -LiteralPath $probeRoot -Directory | Sort-Object Name -Descending | Select-Object -First 1
}
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

