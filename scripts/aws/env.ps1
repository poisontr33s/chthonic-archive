#!/usr/bin/env pwsh
#
# @SID: SCRIPT_ENV_V1
# @Type: UTILITY
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: . .\scripts\aws\env.ps1
#

# Usage:
#   . .\scripts\aws\env.ps1
#   aws --version
#   aws configure sso --profile my-sso
#
# Makes aws callable in this repo's shell session even if VS Code PATH is stale.

$repoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
$shimDir = Join-Path $repoRoot "scripts\bin"
if ($env:Path -notlike "${shimDir}*") {
  $env:Path = "$shimDir;" + $env:Path
}

# Convenience defaults used by the Python scripts.
if (-not $env:AWS_REGION) { $env:AWS_REGION = "us-east-1" }
if (-not $env:AWS_PROFILE) { $env:AWS_PROFILE = "my-sso" }
if (-not $env:BEDROCK_MODEL_ID) { $env:BEDROCK_MODEL_ID = "us.anthropic.claude-opus-4-6-v1" }

Write-Host "AWS env loaded:" -ForegroundColor Cyan
Write-Host "  AWS_PROFILE=$env:AWS_PROFILE"
Write-Host "  AWS_REGION=$env:AWS_REGION"
Write-Host "  BEDROCK_MODEL_ID=$env:BEDROCK_MODEL_ID"
