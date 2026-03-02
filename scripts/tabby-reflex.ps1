#!/usr/bin/env pwsh

# Starts/stops/checks the local TabbyAPI reflex service used by the triad lane.

param(
    [ValidateSet("start", "stop", "status", "restart")]
    [string]$Action = "status",
    [int]$Port = 5000,
    [int]$StartupTimeoutSec = 60
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$tabbyDir = Join-Path $repoRoot "extensions/tabbyAPI"
$pythonExe = Join-Path $tabbyDir ".venv/Scripts/python.exe"
$configPath = Join-Path $tabbyDir "config.yml"
$baseUrl = "http://127.0.0.1:$Port"

function Get-TabbyProcesses {
    $listenerPids = @(
        Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess -Unique
    )

    Get-CimInstance Win32_Process |
        Where-Object {
            ($_.Name -match "python(.exe)?$" -or $_.Name -match "pythonw(.exe)?$") -and
            $_.CommandLine -and
            (
                (
                    $_.CommandLine -match [regex]::Escape("extensions\\tabbyAPI\\") -and
                    $_.CommandLine -match '(^|\s)main\.py(\s|$)'
                ) -or
                (
                    $listenerPids -contains $_.ProcessId -and
                    $_.CommandLine -match '(^|\s)main\.py(\s|$)'
                )
            )
        }
}

function Test-TabbyHealth {
    param([string]$Url)
    try {
        $health = Invoke-RestMethod -Uri "$Url/health" -Method Get -TimeoutSec 3
        return ($health.status -eq "healthy")
    } catch {
        return $false
    }
}

function Stop-Tabby {
    $procs = Get-TabbyProcesses
    if (-not $procs) {
        Write-Host "[tabby-reflex] no running Tabby process found."
        return
    }
    foreach ($proc in $procs) {
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "[tabby-reflex] stopped PID $($proc.ProcessId)"
    }
}

function Show-Status {
    $procs = Get-TabbyProcesses
    $healthy = Test-TabbyHealth -Url $baseUrl
    if ($procs) {
        Write-Host "[tabby-reflex] process: running"
        foreach ($proc in $procs) {
            Write-Host "  pid=$($proc.ProcessId)"
        }
    } else {
        Write-Host "[tabby-reflex] process: stopped"
    }
    $healthState = if ($healthy) { "healthy" } else { "unreachable" }
    Write-Host "[tabby-reflex] health: $healthState"
    if ($healthy) {
        try {
            $models = Invoke-RestMethod -Uri "$baseUrl/v1/models" -Method Get -TimeoutSec 3
            $count = if ($models.data) { $models.data.Count } else { 0 }
            Write-Host "[tabby-reflex] models: $count"
        } catch {
            Write-Host "[tabby-reflex] models: endpoint reachable but model query failed"
        }
    }
}

if (-not (Test-Path $tabbyDir)) {
    throw "Tabby directory not found: $tabbyDir"
}
if (-not (Test-Path $pythonExe)) {
    throw "Tabby venv python not found: $pythonExe"
}
if (-not (Test-Path $configPath)) {
    throw "Tabby config not found: $configPath"
}

switch ($Action) {
    "stop" {
        Stop-Tabby
        Show-Status
        exit 0
    }
    "status" {
        Show-Status
        exit 0
    }
    "restart" {
        Stop-Tabby
    }
    "start" {
        # no-op, continue
    }
}

if (Test-TabbyHealth -Url $baseUrl) {
    Write-Host "[tabby-reflex] already healthy on $baseUrl"
    Show-Status
    exit 0
}

$proc = Start-Process -FilePath $pythonExe `
    -ArgumentList @("main.py", "--config", "config.yml") `
    -WorkingDirectory $tabbyDir `
    -PassThru

Write-Host "[tabby-reflex] started PID $($proc.Id), waiting for health..."

$deadline = (Get-Date).AddSeconds($StartupTimeoutSec)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 1200
    if (Test-TabbyHealth -Url $baseUrl) {
        Write-Host "[tabby-reflex] healthy on $baseUrl"
        Show-Status
        exit 0
    }
}

Write-Host "[tabby-reflex] failed to become healthy within $StartupTimeoutSec seconds."
Show-Status
exit 1
