#!/usr/bin/env pwsh

<#
.SYNOPSIS
  Select active Poe API account for the current shell process.

.DESCRIPTION
  Loads local token pool via canonical api-manager, then maps:
    POE_API_KEY_<n> -> POE_API_KEY
  for the current process only.
#>

param(
  [ValidateSet("1", "2")]
  [string]$Account = "1",
  [switch]$MapOpenAICompat,
  [switch]$Doctor,
  [string]$Model
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Has-Env([string]$Name) {
  $v = [System.Environment]::GetEnvironmentVariable($Name, "Process")
  return -not [string]::IsNullOrWhiteSpace([string]$v)
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$apiManager = Join-Path $repoRoot ".codex/skills/api-manager/scripts/api_manager.ps1"
$legacyPool = Join-Path $repoRoot "scripts/api_pool.ps1"

if (Test-Path -LiteralPath $apiManager) {
  & $apiManager -Load | Out-Null
} elseif (Test-Path -LiteralPath $legacyPool) {
  . $legacyPool -Load -Quiet
} else {
  throw "No token loader found (.codex api-manager or scripts/api_pool.ps1)."
}

$slot = "POE_API_KEY_$Account"
$selected = [System.Environment]::GetEnvironmentVariable($slot, "Process")
if ([string]::IsNullOrWhiteSpace([string]$selected)) {
  throw "Missing $slot in current process. Populate ~/.chthonic/api_pool.json and load again."
}

[System.Environment]::SetEnvironmentVariable("POE_API_KEY", $selected, "Process")
[System.Environment]::SetEnvironmentVariable("POE_ACCOUNT_ACTIVE", $Account, "Process")

if (-not (Has-Env "POE_BASE_URL")) {
  [System.Environment]::SetEnvironmentVariable("POE_BASE_URL", "https://api.poe.com/v1", "Process")
}
if (-not [string]::IsNullOrWhiteSpace($Model)) {
  [System.Environment]::SetEnvironmentVariable("POE_MODEL", $Model.Trim(), "Process")
}

if ($MapOpenAICompat) {
  # Process-only mapping for OpenAI-compatible clients.
  [System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", $selected, "Process")
  [System.Environment]::SetEnvironmentVariable(
    "OPENAI_BASE_URL",
    ([System.Environment]::GetEnvironmentVariable("POE_BASE_URL", "Process")),
    "Process"
  )
}

Write-Host "Poe account lane selected (process-only)."
Write-Host ("- Active account: " + $Account)
Write-Host ("- " + $slot + " present: " + (Has-Env $slot))
Write-Host ("- POE_API_KEY present: " + (Has-Env "POE_API_KEY"))
Write-Host ("- POE_BASE_URL: " + ([System.Environment]::GetEnvironmentVariable("POE_BASE_URL", "Process")))
if ($MapOpenAICompat) {
  Write-Host "- OPENAI-compatible mapping: enabled"
}
if (Has-Env "POE_MODEL") {
  Write-Host ("- POE_MODEL: " + [System.Environment]::GetEnvironmentVariable("POE_MODEL", "Process"))
}

if ($Doctor) {
  foreach ($k in @("POE_API_KEY_1", "POE_API_KEY_2", "POE_API_KEY", "POE_ACCOUNT_ACTIVE", "OPENAI_API_KEY", "OPENAI_BASE_URL")) {
    Write-Host ("- " + $k + ": " + (Has-Env $k))
  }
}
