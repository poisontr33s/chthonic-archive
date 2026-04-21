#!/usr/bin/env pwsh
#
# @SID: SCRIPT_API_POOL_V1
# @Type: UTILITY
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: API Pool helper (local only).
#

# API Pool helper (local only).
#
# Purpose:
# - Provide a stable "one command" way to load tokens into the current shell
#   without ever storing secrets in the repo.
#
# Usage:
# - .\scripts\api_pool.ps1 -Load
#
# Data file:
# - $HOME\.chthonic\api_pool.json (user profile, not repo)
#
# Schema (example):
# {
#   "env": {
#     "HUGGINGFACE_HUB_TOKEN": "hf_...",
#     "GITHUB_TOKEN": "ghp_...",
#     "OPENAI_API_KEY": "sk-..."
#   }
# }

param(
  [switch]$Load,
  [switch]$Verify,
  [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-ApiPoolPath {
  $dir = Join-Path $HOME ".chthonic"
  $path = Join-Path $dir "api_pool.json"
  return @{ Dir = $dir; Path = $path }
}

function Has-EnvVar {
  param([Parameter(Mandatory=$true)][string]$Name)
  $v = [System.Environment]::GetEnvironmentVariable($Name, "Process")
  return -not [string]::IsNullOrWhiteSpace([string]$v)
}

function Get-EnvVar {
  param([Parameter(Mandatory=$true)][string]$Name)
  return [string]([System.Environment]::GetEnvironmentVariable($Name, "Process"))
}

function Normalize-Token {
  param([AllowEmptyString()][string]$Value = "")
  $v = [string]$Value
  $v = $v.Trim()
  # Some configs/logs wrap tokens like <ghp_...>. Strip safely.
  if ($v.StartsWith("<") -and $v.EndsWith(">") -and $v.Length -ge 3) {
    $v = $v.Substring(1, $v.Length - 2).Trim()
  }
  # Avoid double-"Bearer " in downstream headers.
  if ($v -match '^(?i)Bearer\\s+') {
    $v = ($v -replace '^(?i)Bearer\\s+', '').Trim()
  }
  return $v
}

if (-not $Load) {
  if ($Quiet) { exit 2 }
  Write-Host "Usage: .\\scripts\\api_pool.ps1 -Load"
  exit 2
}

$p = Get-ApiPoolPath
if (-not (Test-Path -LiteralPath $p.Path)) {
  New-Item -ItemType Directory -Force -Path $p.Dir | Out-Null
  $template = @'
{
  "env": {
    "HUGGINGFACE_HUB_TOKEN": "",
    "GITHUB_TOKEN": "",
    "OPENAI_API_KEY": ""
  }
}
'@
  $template | Out-File -FilePath $p.Path -Encoding utf8 -NoNewline
  if (-not $Quiet) {
    Write-Host "Created template: $($p.Path)"
    Write-Host "Fill values locally; never commit. Then re-run with -Load."
  }
  exit 3
}

$json = Get-Content -LiteralPath $p.Path -Raw | ConvertFrom-Json
if (-not $json.env) {
  throw "Invalid api_pool.json: missing env object"
}

$count = 0
foreach ($k in $json.env.PSObject.Properties.Name) {
  $v = Normalize-Token -Value ([string]$json.env.$k)
  if ([string]::IsNullOrWhiteSpace($v)) { continue }
  # Set for current process only (safe and deterministic).
  [System.Environment]::SetEnvironmentVariable($k, $v, "Process")
  $count++
}

# Compatibility: some libraries/tools read `HF_TOKEN` only.
# If the pool provides `HUGGINGFACE_HUB_TOKEN`, map/override `HF_TOKEN` for this process.
if (Has-EnvVar -Name "HUGGINGFACE_HUB_TOKEN") {
  $v = [System.Environment]::GetEnvironmentVariable("HUGGINGFACE_HUB_TOKEN", "Process")
  $v = Normalize-Token -Value $v
  if (-not [string]::IsNullOrWhiteSpace($v)) {
    $prior = [System.Environment]::GetEnvironmentVariable("HF_TOKEN", "Process")
    if ($prior -ne $v) {
      [System.Environment]::SetEnvironmentVariable("HF_TOKEN", $v, "Process")
      $count++
    }
  }
}

# Compatibility: Claude official GitHub plugin expects `GITHUB_PERSONAL_ACCESS_TOKEN`.
# Map from `GITHUB_TOKEN` in the pool into the expected variable for this process.
if (Has-EnvVar -Name "GITHUB_TOKEN") {
  $v = Normalize-Token -Value (Get-EnvVar -Name "GITHUB_TOKEN")
  if (-not [string]::IsNullOrWhiteSpace($v)) {
    foreach ($alias in @("GITHUB_PERSONAL_ACCESS_TOKEN","GITHUB_PAT","GITHUB_MCP_PAT","GITHUB_MCP_PAT_TOKEN")) {
      $prior = Get-EnvVar -Name $alias
      if ($prior -ne $v) {
        [System.Environment]::SetEnvironmentVariable($alias, $v, "Process")
        $count++
      }
    }
  }
}

if (-not $Quiet) {
  Write-Host "Loaded $count env var(s) into this shell process."
}

if ($Verify) {
  $missing = @()
  foreach ($k in $json.env.PSObject.Properties.Name) {
    $v = [System.Environment]::GetEnvironmentVariable($k, "Process")
    if ([string]::IsNullOrWhiteSpace($v)) { $missing += $k }
  }
  if ($missing.Count -gt 0) {
    Write-Warning "api_pool -Verify: $($missing.Count) key(s) empty after load: $($missing -join ', ')"
    exit 4
  }
  if (-not $Quiet) { Write-Host "Verify: all $($json.env.PSObject.Properties.Name.Count) key(s) non-empty." }
}
