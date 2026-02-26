#!/usr/bin/env pwsh
# @ankh: heritage-continuity — Apply Chthonic Golden patches to upstream VS Code
# SID: chthonic-golden-patch
# Usage: .\patch.ps1 -UpstreamPath .\upstream-vscode [-DryRun]

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$UpstreamPath,

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$PatchDir = Join-Path ($PSScriptRoot | Split-Path) 'patches'

Write-Host "`n[CHTHONIC-GOLDEN] Patch Application" -ForegroundColor Cyan

if (-not (Test-Path (Join-Path $UpstreamPath '.git'))) {
    Write-Error "Upstream path is not a git repository: $UpstreamPath"
    exit 1
}

$patches = Get-ChildItem $PatchDir -Filter '*.patch' | Sort-Object Name

if ($patches.Count -eq 0) {
    Write-Host "  No patch files in $PatchDir" -ForegroundColor Yellow
    Write-Host "  This is expected for initial setup. Patches will be generated after first manual configuration." -ForegroundColor DarkGray
    exit 0
}

Write-Host "  Found $($patches.Count) patch(es)" -ForegroundColor DarkGray

$results = @()

foreach ($patch in $patches) {
    Write-Host "  [$($patch.BaseName)]" -NoNewline -ForegroundColor White

    Push-Location $UpstreamPath
    try {
        if ($DryRun) {
            $output = git apply --check $patch.FullName 2>&1
            $success = $LASTEXITCODE -eq 0
            $status = if ($success) { 'WOULD-APPLY' } else { 'CONFLICT' }
        } else {
            $output = git apply $patch.FullName 2>&1
            $success = $LASTEXITCODE -eq 0
            $status = if ($success) { 'APPLIED' } else { 'FAILED' }
        }

        $color = if ($success) { 'Green' } else { 'Red' }
        Write-Host " $status" -ForegroundColor $color

        if (-not $success) {
            Write-Host "    $output" -ForegroundColor DarkRed
        }

        $results += [PSCustomObject]@{
            Patch = $patch.Name
            Status = $status
        }
    } finally {
        Pop-Location
    }
}

Write-Host "`nPatch Summary:" -ForegroundColor Cyan
$results | Format-Table -AutoSize

$failed = @($results | Where-Object Status -in 'FAILED','CONFLICT')
if ($failed.Count -gt 0) {
    Write-Warning "$($failed.Count) patch(es) need manual resolution"
    exit 1
}
