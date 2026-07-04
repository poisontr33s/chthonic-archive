#!/usr/bin/env pwsh

#@SID: SYNC_THEMES_V1

# scripts/sync-themes.ps1

# Syncs themes/ from chthonic-archive into chthonic-themes.
# Uses $PSScriptRoot so paths are always resolved from the script location,
# regardless of the cwd the caller uses.

$ErrorActionPreference = "Stop"

$repo   = Resolve-Path (Join-Path $PSScriptRoot "..")
$src    = Join-Path $repo "extensions\chthonic-archive\themes"
$dst    = Join-Path $repo "extensions\chthonic-themes\themes"

if (-not (Test-Path $src)) {
    Write-Error "[sync-themes] Source not found: $src"
    exit 1
}

New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item -Recurse -Force "$src\*" "$dst\"

$count = (Get-ChildItem $dst -Recurse -File).Count
if ($count -eq 0) {
    Write-Error "[sync-themes] Sync produced empty themes/ — aborting"
    exit 1
}

Write-Host "[sync-themes] synced $count files  $src -> $dst"
