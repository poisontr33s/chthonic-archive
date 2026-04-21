#!/usr/bin/env pwsh
#
# @SID: SCRIPT_POE_ACCOUNT_V1
# @Type: UTILITY
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Select active Poe API account for the current shell process.
#

<#
.SYNOPSIS
  Select active Poe API account for the current shell process.

.DESCRIPTION
  Loads local token pool via canonical api-manager, then maps:
    POE_API_KEY_<n> -> POE_API_KEY
  for the current process only.
#>

param(
  [string]$Account = "1",
  [switch]$MapOpenAICompat,
  [switch]$Doctor,
  [switch]$List,
  [string]$Model
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Account) -or ($Account -notmatch '^[0-9]+$')) {
  throw "Account must be numeric (example: 1, 2, 3)."
}
$Account = ([int]$Account).ToString()

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

if ($List) {
  $slots = Get-ChildItem Env: |
    Where-Object { $_.Name -match '^POE_API_KEY_[0-9]+$' } |
    Sort-Object Name
  if (-not $slots -or $slots.Count -eq 0) {
    Write-Host "No POE_API_KEY_N slots found in current process."
    exit 0
  }
  Write-Host "Available Poe API account slots:"
  foreach ($s in $slots) {
    $n = $s.Name -replace '^POE_API_KEY_', ''
    $v = $s.Value
    $masked = if ($v.Length -gt 8) { $v.Substring(0, 4) + '...' + $v.Substring($v.Length - 4) } else { '****' }
    $active = if ($n -eq $Account) { ' (active)' } else { '' }
    Write-Host "  account $n — key: $masked$active"
  }
  exit 0
}

$slot = "POE_API_KEY_$Account"
$selected = [System.Environment]::GetEnvironmentVariable($slot, "Process")
if ([string]::IsNullOrWhiteSpace([string]$selected)) {
  throw "Missing $slot in current process. Populate ~/.chthonic/api_pool.json and load again."
}

[System.Environment]::SetEnvironmentVariable("POE_API_KEY", $selected, "Process")
# Explicit post-set validation.
$keyAfter = [System.Environment]::GetEnvironmentVariable("POE_API_KEY", "Process")
if ([string]::IsNullOrWhiteSpace([string]$keyAfter)) {
  throw "POE_API_KEY is empty after assignment — SetEnvironmentVariable failed or key value is blank."
}
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
  $slotKeys = @(Get-ChildItem Env: |
      Where-Object { $_.Name -match '^POE_API_KEY_[0-9]+$' } |
      Select-Object -ExpandProperty Name |
      Sort-Object)
  if (-not $slotKeys -or $slotKeys.Count -eq 0) {
    $slotKeys = @("POE_API_KEY_$Account")
  }
  $keys = @($slotKeys + @(
      "POE_API_KEY",
      "POE_ACCOUNT_ACTIVE",
      "POE_BASE_URL",
      "POE_MODEL",
      "OPENAI_API_KEY",
      "OPENAI_BASE_URL"
    )) | Select-Object -Unique
  foreach ($k in $keys) {
    Write-Host ("- " + $k + ": " + (Has-Env $k))
  }
}
