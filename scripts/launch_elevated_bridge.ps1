#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [string]$Root = (Join-Path $env:APPDATA 'rv\admin-bridge'),
    [int]$PollMilliseconds = 1000,
    [string]$PwshPath
)

$ErrorActionPreference = 'Stop'

function Get-PwshVersion {
    param([string]$Path)

    if (-not (Test-Path $Path)) { return $null }
    try {
        $raw = & $Path -NoLogo -NoProfile -Command '$PSVersionTable.PSVersion.ToString()' 2>$null
        if ($raw) {
            return [version]($raw | Select-Object -First 1).ToString().Trim()
        }
    } catch {}

    return $null
}

$scriptPath = Join-Path $PSScriptRoot 'elevated_bridge.ps1'
if (-not $PwshPath) {
    $candidates = @()

    foreach ($candidate in @(
        'C:\Program Files\PowerShell\7\pwsh.exe',
        (Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\pwsh.exe')
    )) {
        $version = Get-PwshVersion -Path $candidate
        if ($version) {
            $candidates += [pscustomobject]@{
                Path = $candidate
                Version = $version
            }
        }
    }

    if ($candidates.Count -gt 0) {
        $PwshPath = ($candidates | Sort-Object Version -Descending | Select-Object -First 1).Path
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
