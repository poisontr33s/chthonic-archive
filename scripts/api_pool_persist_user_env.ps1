#!/usr/bin/env pwsh
#
# @SID: SCRIPT_API_POOL_PERSIST_USER_ENV_V1
# @Type: UTILITY
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Persist API pool env vars into Windows *User* environment variables.
#

<#
.SYNOPSIS
  Persist API pool env vars into Windows *User* environment variables.

.WHY
  VS Code / Claude Code IDE launches processes that may not inherit your terminal's
  process environment. Persisting tokens at User-scope makes MCP/plugins stable
  across restarts and daily VS Code Insiders updates.

  This script writes ONLY to the user's environment variable store (registry-backed),
  not to repo files. It does not print secret values.

.USAGE
  pwsh -NoProfile -File scripts/api_pool_persist_user_env.ps1 -Apply
  pwsh -NoProfile -File scripts/api_pool_persist_user_env.ps1 -Apply -Force
  pwsh -NoProfile -File scripts/api_pool_persist_user_env.ps1 -Status
#>

param(
  [switch]$Apply,
  [switch]$Status,
  [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-ApiPoolPath {
  $dir = Join-Path $HOME ".chthonic"
  $path = Join-Path $dir "api_pool.json"
  return @{ Dir = $dir; Path = $path }
}

function Get-UserVar {
  param([Parameter(Mandatory=$true)][string]$Name)
  return [string]([Environment]::GetEnvironmentVariable($Name, "User"))
}

function Set-UserVar {
  param(
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][string]$Value
  )
  [Environment]::SetEnvironmentVariable($Name, $Value, "User")
}

function Normalize-Token {
  param([Parameter(Mandatory=$true)][string]$Value)
  $v = [string]$Value
  $v = $v.Trim()
  if ($v.StartsWith("<") -and $v.EndsWith(">") -and $v.Length -ge 3) {
    $v = $v.Substring(1, $v.Length - 2).Trim()
  }
  if ($v -match '^(?i)Bearer\s+') {
    $v = ($v -replace '^(?i)Bearer\s+', '').Trim()
  }
  return $v
}

function Get-WantedVarNames {
  param([Parameter(Mandatory=$true)][hashtable]$Map)
  $prefixes = @(
    "GITHUB_",
    "HF_",
    "HUGGINGFACE_",
    "OPENAI_",
    "GEMINI_",
    "GOOGLE_",
    "POE_",
    "ANTHROPIC_"
  )
  $wanted = @()
  foreach ($k in ($Map.Keys | Sort-Object)) {
    foreach ($pfx in $prefixes) {
      if ($k.StartsWith($pfx)) {
        $wanted += $k
        break
      }
    }
  }
  return ($wanted | Select-Object -Unique)
}

if (-not $Apply -and -not $Status) {
  Write-Output "Usage: pwsh -NoProfile -File scripts/api_pool_persist_user_env.ps1 -Apply [-Force] | -Status"
  exit 2
}

$p = Get-ApiPoolPath
if (-not (Test-Path -LiteralPath $p.Path)) {
  throw "Missing api_pool.json at $($p.Path). Create/fill it, then re-run."
}

$json = Get-Content -LiteralPath $p.Path -Raw | ConvertFrom-Json
if (-not $json.env) {
  throw "Invalid api_pool.json: missing env object"
}

# Canonical vars we care about for IDE-launched Codex/Claude/MCP processes:
# - GitHub/HF aliases used by plugins
# - OpenAI/Gemini/Google lanes
# - Poe direct + numbered account slots (POE_API_KEY_<n>)
# - Anthropic lanes when present
#
# We take values from api_pool.json if present; otherwise we do not touch.
$map = @{}
foreach ($k in $json.env.PSObject.Properties.Name) {
  $v = Normalize-Token -Value ([string]$json.env.$k)
  if ([string]::IsNullOrWhiteSpace($v)) { continue }
  $map[$k] = $v
}

if ($map.ContainsKey("GITHUB_TOKEN") -and -not $map.ContainsKey("GITHUB_PERSONAL_ACCESS_TOKEN")) {
  $map["GITHUB_PERSONAL_ACCESS_TOKEN"] = $map["GITHUB_TOKEN"]
}
if ($map.ContainsKey("HUGGINGFACE_HUB_TOKEN") -and -not $map.ContainsKey("HF_TOKEN")) {
  $map["HF_TOKEN"] = $map["HUGGINGFACE_HUB_TOKEN"]
}

$wanted = @(Get-WantedVarNames -Map $map)
if (-not $wanted -or $wanted.Count -eq 0) {
  throw "No supported API vars found in $($p.Path)."
}

if ($Status) {
  foreach ($k in $wanted) {
    $userVal = Get-UserVar -Name $k
    $poolVal = if ($map.ContainsKey($k)) { $map[$k] } else { $null }
    $present = -not [string]::IsNullOrWhiteSpace($userVal)
    $inPool  = -not [string]::IsNullOrWhiteSpace($poolVal)
    if ($inPool -and -not $present) {
      Write-Output ("{0}: MISSING (need -Apply)" -f $k)
    } elseif ($inPool -and $present -and $userVal -ne $poolVal) {
      Write-Output ("{0}: DRIFT (pool != user)" -f $k)
    } else {
      Write-Output ("{0}: {1}" -f $k, ($(if ($present) { "True" } else { "False" })))
    }
  }
  exit 0
}

$setCount = 0
$driftSkipped = @()
foreach ($k in $wanted) {
  if (-not $map.ContainsKey($k)) { continue }
  $new = [string]$map[$k]
  $old = Get-UserVar -Name $k
  if (-not [string]::IsNullOrWhiteSpace($old) -and $old -ne $new -and -not $Force) {
    $driftSkipped += $k
    continue
  }
  if ($old -ne $new) {
    Set-UserVar -Name $k -Value $new
    $setCount++
  }
}

Write-Output "ok: persisted $setCount user env var(s) (values not printed). Restart VS Code Insiders to take effect."
if ($driftSkipped.Count -gt 0) {
  Write-Output ("warn: skipped {0} drifted user env var(s): {1}" -f $driftSkipped.Count, ($driftSkipped -join ", "))
  Write-Output "warn: rerun with -Apply -Force only if the pool is definitely the source of truth."
}
