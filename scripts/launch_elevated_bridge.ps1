#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [string]$Root = (Join-Path $env:APPDATA 'rv\admin-bridge'),
    [int]$PollMilliseconds = 1000,
    [string]$PwshPath
)

$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $PSScriptRoot 'elevated_bridge.ps1'
if (-not $PwshPath) {
    $candidates = @(
        Get-ChildItem 'C:\Program Files\PowerShell' -Directory -ErrorAction SilentlyContinue |
            ForEach-Object { Join-Path $_.FullName 'pwsh.exe' } |
            Where-Object { Test-Path $_ }
    )

    if ($candidates.Count -gt 0) {
        $versionedCandidates = $candidates | ForEach-Object {
            $parentDir = Split-Path (Split-Path $_ -Parent) -Leaf
            $parsedVersion = $null
            if ([version]::TryParse($parentDir, [ref]$parsedVersion)) {
                [pscustomobject]@{
                    Path    = $_
                    Version = $parsedVersion
                }
            }
        } | Where-Object { $_ -ne $null }

        if ($versionedCandidates.Count -gt 0) {
            $PwshPath = $versionedCandidates |
                Sort-Object Version -Descending |
                Select-Object -First 1 -ExpandProperty Path
        } else {
            $PwshPath = (Get-Command pwsh).Source
        }
    } else {
        $PwshPath = (Get-Command pwsh).Source
    }
}

Start-Process -FilePath $PwshPath -Verb RunAs -WorkingDirectory (Get-Location).Path -ArgumentList @(
    '-NoExit',
    '-ExecutionPolicy', 'Bypass',
    '-File', $scriptPath,
    '-Root', $Root,
    '-PollMilliseconds', $PollMilliseconds
)
