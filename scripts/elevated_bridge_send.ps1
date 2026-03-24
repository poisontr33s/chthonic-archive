#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Command,

    [string]$Root = (Join-Path $env:APPDATA 'rv\admin-bridge'),
    [string]$Workdir = (Get-Location).Path,
    [switch]$Wait,
    [int]$TimeoutSeconds = 120
)

$ErrorActionPreference = 'Stop'

function Ensure-Directory {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

$inboxDir = Join-Path $Root 'inbox'
$doneDir = Join-Path $Root 'done'
$failedDir = Join-Path $Root 'failed'
Ensure-Directory -Path $Root
Ensure-Directory -Path $inboxDir
Ensure-Directory -Path $doneDir
Ensure-Directory -Path $failedDir

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$id = '{0}_{1}' -f $timestamp, ([guid]::NewGuid().ToString('N'))
$jobPath = Join-Path $inboxDir ($id + '.json')

$job = [pscustomobject]@{
    id = $id
    command = $Command
    workdir = $Workdir
    created_at = (Get-Date).ToString('o')
}

$job | ConvertTo-Json -Depth 4 | Set-Content -Path $jobPath -Encoding utf8

if (-not $Wait) {
    Write-Output $jobPath
    return
}

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $deadline) {
    foreach ($dir in @($doneDir, $failedDir)) {
        $resultPath = Join-Path $dir ($id + '.json')
        if (Test-Path $resultPath) {
            Get-Content $resultPath -Raw
            return
        }
    }
    Start-Sleep -Milliseconds 500
}

throw "Timed out waiting for elevated bridge job $id"
