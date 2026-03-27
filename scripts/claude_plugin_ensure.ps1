#!/usr/bin/env pwsh
#
# @SID: SCRIPT_CLAUDE_PLUGIN_ENSURE_V1
# @Type: AGENT
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Idempotently ensure a Claude Code plugin is enabled (no false "Failed" noise).
#
<#
SYNOPSIS
  Idempotently ensure a Claude Code plugin is enabled (no false "Failed" noise).

WHY
  `claude plugin enable <plugin>` returns a scary error when the plugin is already enabled.
  This wrapper checks state first and only runs enable when needed.

USAGE
  pwsh -NoProfile -File scripts/claude_plugin_ensure.ps1 -Plugin "github@claude-plugins-official" -Scope project
#>

param(
  [Parameter(Mandatory = $true)][string]$Plugin,
  [ValidateSet("local","project","user")][string]$Scope = "project"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location (Split-Path -Parent $PSScriptRoot)
try {

function Get-PluginStatus {
  param([Parameter(Mandatory = $true)][string]$Name)
  $json = & claude plugin list --json 2>&1
  $text = if ($json -is [System.Array]) { $json -join "`n" } else { [string]$json }
  $items = $text | ConvertFrom-Json
  $hit = $items | Where-Object { $_.id -eq $Name } | Select-Object -First 1
  if (-not $hit) { return "missing" }
  if ($hit.enabled -eq $true) { return "enabled" }
  if ($hit.enabled -eq $false) { return "disabled" }
  return "unknown"
}

$status = Get-PluginStatus -Name $Plugin
switch ($status) {
  "enabled" { Write-Output "ok: plugin already enabled ($Plugin)"; exit 0 }
  "missing" { throw "Plugin not installed: $Plugin (install via: claude plugin install $Plugin)" }
  default {
    # Only call enable when it isn't already enabled to avoid the CLI's no-op error.
    & claude plugin enable $Plugin --scope $Scope | Out-Null
    Write-Output "ok: enabled plugin ($Plugin) scope=$Scope"
  }
}

} finally {
  Pop-Location
}
