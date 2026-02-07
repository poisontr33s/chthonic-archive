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
#     "OPENAI_API_KEY": "sk-..."
#   }
# }

param(
  [switch]$Load
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-ApiPoolPath {
  $dir = Join-Path $HOME ".chthonic"
  $path = Join-Path $dir "api_pool.json"
  return @{ Dir = $dir; Path = $path }
}

if (-not $Load) {
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
    "OPENAI_API_KEY": ""
  }
}
'@
  $template | Out-File -FilePath $p.Path -Encoding utf8 -NoNewline
  Write-Host "Created template: $($p.Path)"
  Write-Host "Fill values locally; never commit. Then re-run with -Load."
  exit 3
}

$json = Get-Content -LiteralPath $p.Path -Raw | ConvertFrom-Json
if (-not $json.env) {
  throw "Invalid api_pool.json: missing env object"
}

$count = 0
foreach ($k in $json.env.PSObject.Properties.Name) {
  $v = [string]$json.env.$k
  if ([string]::IsNullOrWhiteSpace($v)) { continue }
  # Set for current process only (safe and deterministic).
  [System.Environment]::SetEnvironmentVariable($k, $v, "Process")
  $count++
}

Write-Host "Loaded $count env var(s) into this shell process."

