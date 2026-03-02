#!/usr/bin/env pwsh

# Hugging Face auth doctor (local, non-secret).
#
# Purpose:
# - Diagnose why Hugging Face auth fails (env var precedence, stale tokens).
# - Provide deterministic next steps without printing secrets.
#
# Usage:
#   pwsh -NoProfile -File .\scripts\hf_auth_doctor.ps1
#   pwsh -NoProfile -File .\scripts\hf_auth_doctor.ps1 -UnsetProcessHFToken
#
# Notes:
# - `HF_TOKEN` takes precedence over `huggingface-cli login` in huggingface_hub.
# - Prefer using the API pool loader to set `HUGGINGFACE_HUB_TOKEN` for the current process:
#     .\scripts\api_pool.ps1 -Load

param(
  [switch]$UnsetProcessHFToken
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Has-Env([string]$Name) {
  $v = [System.Environment]::GetEnvironmentVariable($Name, "Process")
  if ([string]::IsNullOrWhiteSpace($v)) { return $false }
  return $true
}

if ($UnsetProcessHFToken) {
  [System.Environment]::SetEnvironmentVariable("HF_TOKEN", $null, "Process")
  Write-Host "Unset HF_TOKEN for current process."
}

$hasHFToken = Has-Env "HF_TOKEN"
$hasHubToken = Has-Env "HUGGINGFACE_HUB_TOKEN"

Write-Host "HF auth signal (no secrets):"
Write-Host ("- HF_TOKEN (process): " + ($hasHFToken))
Write-Host ("- HUGGINGFACE_HUB_TOKEN (process): " + ($hasHubToken))
Write-Host ""

if ($hasHFToken) {
  Write-Host "Important: HF_TOKEN is set in this process and takes precedence over hf CLI login."
  Write-Host "If hf_probe reports 'Invalid user token' it usually means HF_TOKEN is stale/rotated."
  Write-Host ""
  Write-Host "Fast fix (current shell only):"
  Write-Host "  Remove-Item Env:HF_TOKEN -ErrorAction SilentlyContinue"
  Write-Host ""
  Write-Host "If HF_TOKEN keeps coming back, it is probably persisted at the user level."
  Write-Host "Clear the user-level variable (then open a new terminal):"
  Write-Host "  setx HF_TOKEN \"\""
  Write-Host ""
}

Write-Host "Stable setups (recommended order):"
Write-Host "1) Use Hugging Face CLI login (stores token outside repo):"
Write-Host "   huggingface-cli login"
Write-Host "2) Or use API pool (process-only env injection, stable across VS Code updates):"
Write-Host "   .\\scripts\\api_pool.ps1 -Load"
Write-Host "   (then run) uv run scripts\\hf_probe.py"
Write-Host ""

Write-Host "Verify (no secrets printed):"
Write-Host "  uv run scripts\\hf_probe.py"
