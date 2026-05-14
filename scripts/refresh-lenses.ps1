#!/usr/bin/env pwsh
# @SID: REFRESH_LENSES_V1
#
# Refresh all data-plane lenses. One-stop wrapper around the ci/run.ts
# lens-refresh check. Use this when you want fresh manifests without
# running a full CI sweep.
#
# Methodology: "Gitological Noise As Structured Data — Lens per noise class."
#
# Usage:
#   .\scripts\refresh-lenses.ps1            # refresh all registered lenses
#   .\scripts\refresh-lenses.ps1 -Lens rot  # just the git_rot_index
#   .\scripts\refresh-lenses.ps1 -Lens dep  # just the dependabot_index
#
# Wired lenses live in ci/checks/lens-refresh.ts. To add a new one, edit
# that file's LENSES array — do NOT add scripts here.

[CmdletBinding()]
param(
    [ValidateSet('all', 'rot', 'dep', 'activity', 'method', 'route')]
    [string]$Lens = 'all'
)

$repo = Split-Path -Parent $PSScriptRoot
Push-Location $repo
try {
    switch ($Lens) {
        'rot' {
            Write-Host "[refresh-lenses] git_rot_index only"
            uv run scripts/git_rot_index.py
        }
        'dep' {
            Write-Host "[refresh-lenses] dependabot_index only"
            uv run scripts/dependabot_index.py
        }
        'activity' {
            Write-Host "[refresh-lenses] github_activity_index only"
            uv run scripts/github_activity_index.py
        }
        'method' {
            Write-Host "[refresh-lenses] method_index only"
            uv run scripts/method_index.py
        }
        'route' {
            Write-Host "[refresh-lenses] route_index only"
            uv run scripts/route_index.py
        }
        default {
            Write-Host "[refresh-lenses] firing all lenses via ci/run.ts orchestrator"
            bun run ci/run.ts --check lens-refresh
        }
    }
}
finally {
    Pop-Location
}
