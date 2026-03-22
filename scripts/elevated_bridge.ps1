#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [string]$Root = (Join-Path $env:APPDATA 'rv\admin-bridge'),
    [int]$PollMilliseconds = 1000
)

$ErrorActionPreference = 'Stop'

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Ensure-Directory {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Write-BridgeStatus {
    param(
        [string]$StatusPath,
        [bool]$Elevated,
        [string]$RootPath,
        [string]$State = 'idle',
        [string]$CurrentJobId = $null,
        [string]$CurrentJobPath = $null,
        [string]$CurrentJobStartedAt = $null,
        [string]$LastCompletedJobId = $null,
        [int]$LastExitCode = 0
    )

    $status = [pscustomobject]@{
        pid = $PID
        elevated = $Elevated
        started_at = (Get-Date).ToString('o')
        last_heartbeat = (Get-Date).ToString('o')
        root = $RootPath
        user = [Environment]::UserName
        host = $env:COMPUTERNAME
        state = $State
        current_job_id = $CurrentJobId
        current_job_path = $CurrentJobPath
        current_job_started_at = $CurrentJobStartedAt
        last_completed_job_id = $LastCompletedJobId
        last_exit_code = $LastExitCode
    }

    $status | ConvertTo-Json -Depth 4 | Set-Content -Path $StatusPath -Encoding utf8
}

function Complete-BridgeJob {
    param(
        [string]$JobPath,
        [string]$ResultDir,
        [string]$LogDir,
        [hashtable]$Result
    )

    $resultPath = Join-Path $ResultDir ($Result.id + '.json')
    $logPath = Join-Path $LogDir ($Result.id + '.log')

    @($Result.output) | Set-Content -Path $logPath -Encoding utf8
    $Result | ConvertTo-Json -Depth 8 | Set-Content -Path $resultPath -Encoding utf8
    Remove-Item -LiteralPath $JobPath -Force -ErrorAction SilentlyContinue
}

function Invoke-BridgeCommand {
    param(
        [string]$Workdir,
        [string]$Command
    )

    $output = [System.Collections.Generic.List[string]]::new()
    $exitCode = 0
    $startedAt = Get-Date

    Push-Location -LiteralPath $Workdir
    try {
        $script = [scriptblock]::Create($Command)
        $result = & $script 2>&1
        foreach ($line in @($result)) {
            if ($null -ne $line) {
                $output.Add($line.ToString()) | Out-Null
            }
        }

        if ($null -ne $LASTEXITCODE) {
            $exitCode = [int]$LASTEXITCODE
        }
    } catch {
        $exitCode = 1
        $output.Add($_.ToString()) | Out-Null
        if ($_.InvocationInfo.PositionMessage) {
            $output.Add($_.InvocationInfo.PositionMessage) | Out-Null
        }
    } finally {
        Pop-Location
    }

    return [pscustomobject]@{
        started_at = $startedAt.ToString('o')
        completed_at = (Get-Date).ToString('o')
        exit_code = $exitCode
        output = @($output)
    }
}

$isAdmin = Test-IsAdmin
$inboxDir = Join-Path $Root 'inbox'
$processingDir = Join-Path $Root 'processing'
$doneDir = Join-Path $Root 'done'
$failedDir = Join-Path $Root 'failed'
$logsDir = Join-Path $Root 'logs'
$statusPath = Join-Path $Root 'status.json'
$stopPath = Join-Path $Root 'STOP'

foreach ($dir in @($Root, $inboxDir, $processingDir, $doneDir, $failedDir, $logsDir)) {
    Ensure-Directory -Path $dir
}

Write-BridgeStatus -StatusPath $statusPath -Elevated $isAdmin -RootPath $Root -State 'idle'

Write-Host "Elevated bridge root: $Root" -ForegroundColor Cyan
Write-Host "Elevated: $isAdmin" -ForegroundColor Cyan
Write-Host "Polling: $PollMilliseconds ms" -ForegroundColor Cyan
Write-Host "Create .json jobs in $inboxDir or use scripts/elevated_bridge_send.ps1" -ForegroundColor DarkGray

while ($true) {
    Write-BridgeStatus -StatusPath $statusPath -Elevated $isAdmin -RootPath $Root -State 'idle'

    if (Test-Path $stopPath) {
        Remove-Item -LiteralPath $stopPath -Force -ErrorAction SilentlyContinue
        break
    }

    $jobs = @(Get-ChildItem $inboxDir -Filter *.json -File -ErrorAction SilentlyContinue | Sort-Object Name)
    if ($jobs.Count -eq 0) {
        Start-Sleep -Milliseconds $PollMilliseconds
        continue
    }

    foreach ($jobFile in $jobs) {
        $processingPath = Join-Path $processingDir $jobFile.Name
        Move-Item -LiteralPath $jobFile.FullName -Destination $processingPath -Force

        try {
            $job = Get-Content $processingPath -Raw | ConvertFrom-Json
            $id = [string]$job.id
            if (-not $id) {
                $id = [IO.Path]::GetFileNameWithoutExtension($jobFile.Name)
            }

            $command = [string]$job.command
            $workdir = if ($job.workdir -and (Test-Path $job.workdir)) { [string]$job.workdir } else { $PWD.Path }
            $currentJobStartedAt = (Get-Date).ToString('o')

            Write-BridgeStatus -StatusPath $statusPath -Elevated $isAdmin -RootPath $Root -State 'running' -CurrentJobId $id -CurrentJobPath $processingPath -CurrentJobStartedAt $currentJobStartedAt

            if ($command -eq '__STOP__') {
                Complete-BridgeJob -JobPath $processingPath -ResultDir $doneDir -LogDir $logsDir -Result @{
                    id = $id
                    workdir = $workdir
                    command = $command
                    elevated = $isAdmin
                    started_at = (Get-Date).ToString('o')
                    completed_at = (Get-Date).ToString('o')
                    exit_code = 0
                    output = @('Bridge stop requested.')
                }
                break 2
            }

            $firstLine = ($command -split "`r?`n" | Select-Object -First 1).Trim()
            if ($firstLine.Length -gt 120) {
                $firstLine = $firstLine.Substring(0, 117) + '...'
            }
            Write-Host ("[{0}] running in {1}" -f $id, $workdir) -ForegroundColor Yellow
            Write-Host ("[{0}] {1}" -f $id, $firstLine) -ForegroundColor DarkGray
            $run = Invoke-BridgeCommand -Workdir $workdir -Command $command
            $resultDir = if ($run.exit_code -eq 0) { $doneDir } else { $failedDir }

            Complete-BridgeJob -JobPath $processingPath -ResultDir $resultDir -LogDir $logsDir -Result @{
                id = $id
                workdir = $workdir
                command = $command
                elevated = $isAdmin
                started_at = $run.started_at
                completed_at = $run.completed_at
                exit_code = $run.exit_code
                output = $run.output
            }
            Write-BridgeStatus -StatusPath $statusPath -Elevated $isAdmin -RootPath $Root -State 'idle' -LastCompletedJobId $id -LastExitCode $run.exit_code
            Write-Host ("[{0}] completed with exit {1}" -f $id, $run.exit_code) -ForegroundColor Cyan
        } catch {
            Complete-BridgeJob -JobPath $processingPath -ResultDir $failedDir -LogDir $logsDir -Result @{
                id = [IO.Path]::GetFileNameWithoutExtension($jobFile.Name)
                workdir = $PWD.Path
                command = '<job parse failure>'
                elevated = $isAdmin
                started_at = (Get-Date).ToString('o')
                completed_at = (Get-Date).ToString('o')
                exit_code = 1
                output = @($_.ToString())
            }
            Write-BridgeStatus -StatusPath $statusPath -Elevated $isAdmin -RootPath $Root -State 'idle' -LastCompletedJobId ([IO.Path]::GetFileNameWithoutExtension($jobFile.Name)) -LastExitCode 1
        }
    }
}

Write-Host 'Elevated bridge stopped.' -ForegroundColor Cyan
