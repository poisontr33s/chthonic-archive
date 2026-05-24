#!/usr/bin/env pwsh
# @SID: SCRIPT_POSTINSTALL_V1
# Local postinstall maintenance. Must not block dependency installation.

$ErrorActionPreference = "Continue"
$scriptRoot = $PSScriptRoot

& pwsh -NoProfile -File (Join-Path $scriptRoot "gemini-cli-wrapper.ps1") -v
if ($LASTEXITCODE -ne 0) {
    Write-Warning "[postinstall] gemini version probe failed; continuing"
}

& pwsh -NoProfile -File (Join-Path $scriptRoot "ensure-precommit-hook.ps1") -Force
if ($LASTEXITCODE -ne 0) {
    Write-Warning "[postinstall] pre-commit hook install failed; run 'bun run hooks:precommit' to repair"
}

exit 0
