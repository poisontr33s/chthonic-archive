#!/usr/bin/env pwsh

[CmdletBinding()]
param(
  # Sentry access token (recommended: pass via env var instead).
  [string]$SentryAccessToken = $env:SENTRY_ACCESS_TOKEN,

  # Sentry org slug (optional depending on server behavior).
  [string]$SentryOrg = $env:SENTRY_ORG,

  # Comma-separated projects (optional).
  [string]$SentryProjects = $env:SENTRY_PROJECTS
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$bunExe = Join-Path $env:USERPROFILE '.bun\bin\bun.exe'

if (-not (Test-Path -LiteralPath $bunExe)) {
  throw "Bun not found at '$bunExe'."
}

if ([string]::IsNullOrWhiteSpace($SentryAccessToken)) {
  throw "SENTRY_ACCESS_TOKEN is required (set env var or pass -SentryAccessToken)."
}

# Preserve deterministic env lane: only add env vars the server expects.
$env:SENTRY_ACCESS_TOKEN = $SentryAccessToken
if (-not [string]::IsNullOrWhiteSpace($SentryOrg)) { $env:SENTRY_ORG = $SentryOrg }
if (-not [string]::IsNullOrWhiteSpace($SentryProjects)) { $env:SENTRY_PROJECTS = $SentryProjects }

Push-Location $repoRoot
try {
  # Prefer bun's package runner (no global install required).
  # If you want to pin a version, replace @latest with an explicit version.
  & $bunExe x -y @sentry/mcp-server@latest
}
finally {
  Pop-Location
}

