#!/usr/bin/env pwsh

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║ THE DECORATOR'S BLESSING: run_overnight_daemon.ps1                        ║
# ║ Module: Overnight Daemon Launcher                                         ║
# ╠════════════════════════════════════════════════════════════════════════════╣
# ║ Spectral Frequency: orchestration/automation                              ║
# ║ Architectural Role: PowerShell wrapper for TypeScript overnight daemon    ║
# ║ Semantic ID: SCRIPT_RUN_OVERNIGHT_DAEMON_V1                               ║
# ║ Purpose: Launch overnight_daemon.ts via Bun with configurable parameters  ║
# ║ Exports: None (launcher script)                                           ║
# ║ Flags/Modes: -Top <int>, -MaxTodo <int>, -Siphon                          ║
# ║ Cross-References: scripts/overnight_daemon.ts                             ║
# ╚════════════════════════════════════════════════════════════════════════════╝

[CmdletBinding()]
param(
  [int]$Top = 20,
  [int]$MaxTodo = 80,
  [switch]$Siphon
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$bunExe = Join-Path $env:USERPROFILE '.bun\bin\bun.exe'
$tsScript = Join-Path $repoRoot 'scripts\overnight_daemon.ts'

if (-not (Test-Path -LiteralPath $bunExe)) {
  throw "Bun not found at '$bunExe'. Install Bun or adjust this script to point to bun.exe."
}
if (-not (Test-Path -LiteralPath $tsScript)) {
  throw "Daemon script not found at '$tsScript'."
}

$argsList = @(
  $tsScript,
  '--top', $Top,
  '--maxTodo', $MaxTodo
)
if ($Siphon) {
  $argsList += '--siphon'
}

& $bunExe @argsList

