# @SID: SKILL_API_MANAGER_V1

# API Manager (local tokens + auth drift doctor)
#
# Purpose:
# - Make token handling deterministic and non-performative:
#   - one local secrets file (outside git)
#   - one loader (process env injection)
#   - one doctor (precedence + missing signals)
#
# File:
# - $HOME\.chthonic\api_pool.json
#
# Schema:
# {
#   "env": {
#     "HUGGINGFACE_HUB_TOKEN": "hf_...",
#     "GITHUB_TOKEN": "ghp_...",
#     "OPENAI_API_KEY": "sk-...",
#     "GEMINI_API_KEY": "...",
#     "POE_API_KEY": "...",
#     "POE_API_KEY_1": "...",
#     "POE_API_KEY_2": "...",
#     "HF_TOKEN": ""  // avoid unless you want precedence override
#   }
# }
#
# Usage:
#   pwsh -NoProfile -File .codex/skills/api-manager/scripts/api_manager.ps1 -Doctor
#   pwsh -NoProfile -File .codex/skills/api-manager/scripts/api_manager.ps1 -Load
#   pwsh -NoProfile -File .codex/skills/api-manager/scripts/api_manager.ps1 -FixHF
#   pwsh -NoProfile -File .codex/skills/api-manager/scripts/api_manager.ps1 -VerifyHF

param(
  [switch]$Doctor,
  [switch]$Load,
  [switch]$FixHF,
  [switch]$VerifyHF
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-ApiPoolPath {
  $dir = Join-Path $HOME ".chthonic"
  $path = Join-Path $dir "api_pool.json"
  return @{ Dir = $dir; Path = $path }
}

function Ensure-Template([string]$Path, [string]$Dir) {
  if (Test-Path -LiteralPath $Path) { return $false }
  New-Item -ItemType Directory -Force -Path $Dir | Out-Null
  @'
{
  "env": {
    "HUGGINGFACE_HUB_TOKEN": "",
    "GITHUB_TOKEN": "",
    "OPENAI_API_KEY": "",
    "GEMINI_API_KEY": "",
    "POE_API_KEY": "",
    "POE_API_KEY_1": "",
    "POE_API_KEY_2": ""
  }
}
'@ | Out-File -FilePath $Path -Encoding utf8 -NoNewline
  return $true
}

function Has-Env([string]$Name) {
  $v = [System.Environment]::GetEnvironmentVariable($Name, "Process")
  if ([string]::IsNullOrWhiteSpace($v)) { return $false }
  return $true
}

function Set-EnvFromPool([pscustomobject]$EnvObj) {
  $count = 0
  foreach ($k in $EnvObj.PSObject.Properties.Name) {
    $v = [string]$EnvObj.$k
    if ([string]::IsNullOrWhiteSpace($v)) { continue }
    [System.Environment]::SetEnvironmentVariable($k, $v, "Process")
    $count++
  }
  return $count
}

function Print-Signals {
  $slotNames = @(Get-ChildItem Env: |
      Where-Object { $_.Name -match '^POE_API_KEY_[0-9]+$' } |
      Select-Object -ExpandProperty Name |
      Sort-Object)
  if (-not $slotNames -or $slotNames.Count -eq 0) {
    $slotNames = @("POE_API_KEY_1", "POE_API_KEY_2")
  }
  $names = @(
    "HF_TOKEN",
    "HUGGINGFACE_HUB_TOKEN",
    "GITHUB_TOKEN",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "POE_API_KEY",
    "POE_ACCOUNT_ACTIVE",
    "POE_BASE_URL",
    "POE_MODEL"
  )
  $names = @($names + $slotNames) | Select-Object -Unique
  Write-Host "Auth signals (process env, no secrets):"
  foreach ($n in $names) {
    Write-Host ("- " + $n + ": " + (Has-Env $n))
  }
  Write-Host ""
  if (Has-Env "HF_TOKEN") {
    Write-Host "HF note: HF_TOKEN is set and takes precedence over hf CLI login; stale HF_TOKEN breaks HF auth."
    Write-Host "Suggested: run -FixHF (clears HF_TOKEN in current shell)."
    Write-Host ""
  }
}

function Verify-HF {
  # Reuse the repo probe. It prints pass/fail only.
  $repoRoot = (Get-Location).Path
  $probe = Join-Path $repoRoot "scripts\\hf_probe.py"
  if (-not (Test-Path -LiteralPath $probe)) {
    throw "Missing probe script: $probe"
  }
  & uv run $probe
}

$p = Get-ApiPoolPath
$created = Ensure-Template -Path $p.Path -Dir $p.Dir
if ($created) {
  Write-Host "Created template: $($p.Path)"
  Write-Host "Fill values locally (never commit), then re-run with -Load."
  exit 3
}

if ($Doctor) {
  Print-Signals
  exit 0
}

if ($FixHF) {
  Remove-Item Env:HF_TOKEN -ErrorAction SilentlyContinue
  [System.Environment]::SetEnvironmentVariable("HF_TOKEN", $null, "Process")
  Write-Host "Cleared HF_TOKEN for current shell process."
  Print-Signals
  exit 0
}

if ($Load) {
  $json = Get-Content -LiteralPath $p.Path -Raw | ConvertFrom-Json
  if (-not $json.env) { throw "Invalid api_pool.json: missing env object" }
  $n = Set-EnvFromPool -EnvObj $json.env
  Write-Host "Loaded $n env var(s) into this shell process."
  Print-Signals
  exit 0
}

if ($VerifyHF) {
  Print-Signals
  Verify-HF
  exit $LASTEXITCODE
}

Write-Host "Usage:"
Write-Host "  pwsh -NoProfile -File .codex/skills/api-manager/scripts/api_manager.ps1 -Doctor"
Write-Host "  pwsh -NoProfile -File .codex/skills/api-manager/scripts/api_manager.ps1 -Load"
Write-Host "  pwsh -NoProfile -File .codex/skills/api-manager/scripts/api_manager.ps1 -FixHF"
Write-Host "  pwsh -NoProfile -File .codex/skills/api-manager/scripts/api_manager.ps1 -VerifyHF"
exit 2
