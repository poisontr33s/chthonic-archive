#!/usr/bin/env pwsh

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$bunExe = Join-Path $env:USERPROFILE '.bun\bin\bun.exe'
$server = Join-Path $repoRoot 'scripts\mcp_artisan_server.ts'

if (-not (Test-Path -LiteralPath $bunExe)) {
  throw "Bun not found at '$bunExe'."
}
if (-not (Test-Path -LiteralPath $server)) {
  throw "MCP artisan server not found at '$server'."
}

# Run in the current console (stdio).
& $bunExe $server

