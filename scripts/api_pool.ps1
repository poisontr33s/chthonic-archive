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
# - .\scripts\api_pool.ps1 -VerifyPool
# - .\scripts\api_pool.ps1 -SetHFToken
# - .\scripts\api_pool.ps1 -VerifyHF
# - .\scripts\api_pool.ps1 -SyncGitHubFromGh
# - .\scripts\api_pool.ps1 -VerifyGitHub
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
  [switch]$VerifyPool,
  [switch]$SetHFToken,
  [switch]$VerifyHF,
  [switch]$SyncGitHubFromGh,
  [switch]$VerifyGitHub,
  [switch]$SetSpotify,
  [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$InvocationLine = [string]$MyInvocation.Line
$WantLoad = $PSBoundParameters.ContainsKey("Load") -or ($InvocationLine -match '(?i)(^|\s)-Load(\s|$)')
$WantVerifyPool = $PSBoundParameters.ContainsKey("VerifyPool") -or ($InvocationLine -match '(?i)(^|\s)-VerifyPool(\s|$)')
$WantSetHFToken = $PSBoundParameters.ContainsKey("SetHFToken") -or ($InvocationLine -match '(?i)(^|\s)-SetHFToken(\s|$)')
$WantVerifyHF = $PSBoundParameters.ContainsKey("VerifyHF") -or ($InvocationLine -match '(?i)(^|\s)-VerifyHF(\s|$)')
$WantSyncGitHubFromGh = $PSBoundParameters.ContainsKey("SyncGitHubFromGh") -or ($InvocationLine -match '(?i)(^|\s)-SyncGitHubFromGh(\s|$)')
$WantVerifyGitHub = $PSBoundParameters.ContainsKey("VerifyGitHub") -or ($InvocationLine -match '(?i)(^|\s)-VerifyGitHub(\s|$)')
$WantSetSpotify = $PSBoundParameters.ContainsKey("SetSpotify") -or ($InvocationLine -match '(?i)(^|\s)-SetSpotify(\s|$)')

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

function Set-GitHubAliases {
  param([Parameter(Mandatory=$true)][string]$Token)
  $v = Normalize-Token -Value $Token
  if ([string]::IsNullOrWhiteSpace($v)) { return 0 }
  $names = @(
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "GITHUB_PAT",
    "GITHUB_MCP_PAT",
    "GITHUB_MCP_PAT_TOKEN"
  )
  $count = 0
  foreach ($n in $names) {
    $prior = Get-EnvVar -Name $n
    if ($prior -ne $v) {
      [System.Environment]::SetEnvironmentVariable($n, $v, "Process")
      $count++
    }
  }
  return $count
}

function Set-HFAliases {
  param([Parameter(Mandatory=$true)][string]$Token)
  $v = Normalize-Token -Value $Token
  if ([string]::IsNullOrWhiteSpace($v)) { return 0 }
  $count = 0
  foreach ($n in @("HUGGINGFACE_HUB_TOKEN", "HF_TOKEN")) {
    $prior = Get-EnvVar -Name $n
    if ($prior -ne $v) {
      [System.Environment]::SetEnvironmentVariable($n, $v, "Process")
      $count++
    }
  }
  return $count
}

function Read-SecretPlainText {
  param([Parameter(Mandatory=$true)][string]$Prompt)
  $secure = Read-Host -Prompt $Prompt -AsSecureString
  $ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try {
    return [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
  } finally {
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
  }
}

function Set-PoolEnvValue {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][string]$Value
  )
  $json = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
  if (-not $json.env) {
    $json | Add-Member -MemberType NoteProperty -Name env -Value ([pscustomobject]@{})
  }
  $props = $json.env.PSObject.Properties.Name
  if ($props -contains $Name) {
    $json.env.$Name = $Value
  } else {
    $json.env | Add-Member -MemberType NoteProperty -Name $Name -Value $Value
  }
  $json | ConvertTo-Json -Depth 8 | Out-File -FilePath $Path -Encoding utf8 -NoNewline
}

function Invoke-GhKeyringToken {
  $names = @("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN", "GITHUB_PAT")
  $saved = @{}
  foreach ($n in $names) {
    $saved[$n] = [System.Environment]::GetEnvironmentVariable($n, "Process")
    Remove-Item ("Env:" + $n) -ErrorAction SilentlyContinue
    [System.Environment]::SetEnvironmentVariable($n, $null, "Process")
  }
  try {
    $token = (& gh auth token 2>$null)
    if ($LASTEXITCODE -ne 0) { throw "gh auth token failed; run gh auth login first." }
    $token = Normalize-Token -Value ([string]$token)
    if ([string]::IsNullOrWhiteSpace($token)) { throw "gh auth token returned no token." }
    return $token
  } finally {
    foreach ($n in $names) {
      [System.Environment]::SetEnvironmentVariable($n, $saved[$n], "Process")
    }
  }
}

function Verify-GitHub {
  $login = (& gh api user --jq ".login" 2>$null)
  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace([string]$login)) {
    if (-not $Quiet) { Write-Host "fail: GitHub token rejected" }
    return 2
  }
  if (-not $Quiet) { Write-Host ("ok: " + [string]$login) }
  return 0
}

function Verify-HF {
  $probe = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")).Path "scripts\hf_probe.py"
  $output = & uv run $probe 2>&1
  $rc = $LASTEXITCODE
  foreach ($line in @($output)) {
    if (-not [string]::IsNullOrWhiteSpace([string]$line)) {
      Write-Host ([string]$line)
    }
  }
  return $rc
}

if (-not (
    $WantLoad -or
    $WantVerifyPool -or
    $WantSetHFToken -or
    $WantVerifyHF -or
    $WantSyncGitHubFromGh -or
    $WantVerifyGitHub -or
    $WantSetSpotify
  )) {
  if ($Quiet) { exit 2 }
  Write-Host "Usage:"
  Write-Host "  .\\scripts\\api_pool.ps1 -Load"
  Write-Host "  .\\scripts\\api_pool.ps1 -VerifyPool"
  Write-Host "  .\\scripts\\api_pool.ps1 -SetHFToken"
  Write-Host "  .\\scripts\\api_pool.ps1 -VerifyHF"
  Write-Host "  .\\scripts\\api_pool.ps1 -SyncGitHubFromGh"
  Write-Host "  .\\scripts\\api_pool.ps1 -VerifyGitHub"
  Write-Host "  .\\scripts\\api_pool.ps1 -SetSpotify"
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
    "OPENAI_API_KEY": "",
    "SPOTIFY_CLIENT_ID": "",
    "SPOTIFY_CLIENT_SECRET": "",
    "SPOTIFY_REFRESH_TOKEN": ""
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

if ($WantSyncGitHubFromGh) {
  $token = Invoke-GhKeyringToken
  Set-PoolEnvValue -Path $p.Path -Name "GITHUB_TOKEN" -Value $token
  $mapped = Set-GitHubAliases -Token $token
  if (-not $Quiet) {
    Write-Host "Synced GitHub token from gh keyring into local API pool (token not printed)."
    Write-Host "Updated current-process GitHub aliases: $mapped"
  }
  exit (Verify-GitHub)
}

if ($WantSetSpotify) {
  $existingId = ""
  $existingSecret = ""
  if (Test-Path -LiteralPath $p.Path) {
    $existing = Get-Content -LiteralPath $p.Path -Raw | ConvertFrom-Json
    $existingId     = if ($null -ne $existing.env.PSObject.Properties["SPOTIFY_CLIENT_ID"])     { [string]$existing.env.SPOTIFY_CLIENT_ID }     else { "" }
    $existingSecret = if ($null -ne $existing.env.PSObject.Properties["SPOTIFY_CLIENT_SECRET"]) { [string]$existing.env.SPOTIFY_CLIENT_SECRET } else { "" }
  }
  $idHint = if ($existingId) { " [existing: $($existingId.Substring(0,8))... — press Enter to keep]" } else { "" }
  $clientId = Normalize-Token -Value (Read-SecretPlainText -Prompt "Spotify CLIENT_ID$idHint")
  if ([string]::IsNullOrWhiteSpace($clientId)) { $clientId = $existingId }
  if ([string]::IsNullOrWhiteSpace($clientId)) { throw "No CLIENT_ID provided or stored." }

  $secretHint = if ($existingSecret) { " [existing set — press Enter to keep]" } else { "" }
  $clientSecret = Normalize-Token -Value (Read-SecretPlainText -Prompt "Spotify CLIENT_SECRET$secretHint")
  if ([string]::IsNullOrWhiteSpace($clientSecret)) { $clientSecret = $existingSecret }
  if ([string]::IsNullOrWhiteSpace($clientSecret)) { throw "No CLIENT_SECRET provided or stored." }

  $refreshToken = Normalize-Token -Value (Read-SecretPlainText -Prompt "Spotify REFRESH_TOKEN (press Enter to skip)")

  Set-PoolEnvValue -Path $p.Path -Name "SPOTIFY_CLIENT_ID" -Value $clientId
  Set-PoolEnvValue -Path $p.Path -Name "SPOTIFY_CLIENT_SECRET" -Value $clientSecret
  if (-not [string]::IsNullOrWhiteSpace($refreshToken)) {
    Set-PoolEnvValue -Path $p.Path -Name "SPOTIFY_REFRESH_TOKEN" -Value $refreshToken
  }
  if (-not $Quiet) {
    Write-Host "Spotify credentials written to local API pool (values not printed)."
    if ([string]::IsNullOrWhiteSpace($refreshToken)) {
      Write-Host "SPOTIFY_REFRESH_TOKEN skipped — run spotify_auth.ts to obtain it, then re-run -SetSpotify."
    }
  }
  exit 0
}

if ($WantSetHFToken) {
  $token = Normalize-Token -Value (Read-SecretPlainText -Prompt "Paste Hugging Face token")
  if ([string]::IsNullOrWhiteSpace($token)) { throw "Empty Hugging Face token." }
  Set-PoolEnvValue -Path $p.Path -Name "HUGGINGFACE_HUB_TOKEN" -Value $token
  Set-PoolEnvValue -Path $p.Path -Name "HF_TOKEN" -Value $token
  $mapped = Set-HFAliases -Token $token
  if (-not $Quiet) {
    Write-Host "Synced Hugging Face token into local API pool (token not printed)."
    Write-Host "Updated current-process Hugging Face aliases: $mapped"
  }
  exit (Verify-HF)
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
    $count += Set-HFAliases -Token $v
  }
}

# Compatibility: Claude official GitHub plugin expects `GITHUB_PERSONAL_ACCESS_TOKEN`.
# Map from `GITHUB_TOKEN` in the pool into the expected variable for this process.
if (Has-EnvVar -Name "GITHUB_TOKEN") {
  $v = Normalize-Token -Value (Get-EnvVar -Name "GITHUB_TOKEN")
  if (-not [string]::IsNullOrWhiteSpace($v)) {
    $count += Set-GitHubAliases -Token $v
  }
}

if (-not $Quiet) {
  Write-Host "Loaded $count env var(s) into this shell process."
}

if ($WantVerifyPool) {
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

if ($WantVerifyGitHub) {
  exit (Verify-GitHub)
}

if ($WantVerifyHF) {
  exit (Verify-HF)
}
