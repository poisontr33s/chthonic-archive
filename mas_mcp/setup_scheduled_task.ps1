#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup Windows Task Scheduler for Genesis Engine v2.

.DESCRIPTION
    Creates a scheduled task that runs the Genesis Scheduler every 15 minutes.
    Task runs whether user is logged on or not and requires network availability.

.PARAMETER Interval
    Minutes between runs (default: 15)

.PARAMETER Target
    Target accepts per cycle (default: 25)

.PARAMETER TaskName
    Name for the scheduled task (default: "Genesis Scheduler v2")

.PARAMETER Uninstall
    Remove the scheduled task instead of creating it

.EXAMPLE
    .\setup_scheduled_task.ps1
    .\setup_scheduled_task.ps1 -Interval 30 -Target 10
    .\setup_scheduled_task.ps1 -Uninstall
#>

param(
    [int]$Interval = 15,
    [int]$Target = 25,
    [string]$TaskName = "Genesis Scheduler v2",
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

# Paths
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$SchedulerScript = Join-Path $PSScriptRoot "genesis_scheduler.py"

# Validate paths
if (-not (Test-Path $VenvPython)) {
    Write-Error "Python venv not found at: $VenvPython"
    exit 1
}

if (-not (Test-Path $SchedulerScript)) {
    Write-Error "Scheduler script not found at: $SchedulerScript"
    exit 1
}

if ($Uninstall) {
    Write-Host "🗑️  Removing scheduled task: $TaskName" -ForegroundColor Yellow
    
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✓ Task removed successfully" -ForegroundColor Green
    } else {
        Write-Host "⚠ Task not found" -ForegroundColor Yellow
    }
    exit 0
}

Write-Host @"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Genesis Scheduler v2 - Windows Task Setup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Task Name:     $TaskName
  Interval:      $Interval minutes
  Target:        $Target accepts/cycle
  Python:        $VenvPython
  Script:        $SchedulerScript
  Working Dir:   $PSScriptRoot

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"@ -ForegroundColor Cyan

# Create trigger (every N minutes, indefinitely)
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $Interval)

# Create action
$Arguments = "-u `"$SchedulerScript`" --once --target $Target"
$Action = New-ScheduledTaskAction -Execute $VenvPython -Argument $Arguments -WorkingDirectory $PSScriptRoot

# Task settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

# Principal (run whether logged in or not - requires elevation)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Limited

# Check if task exists
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "⚠ Task already exists, updating..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Register task
Write-Host "📅 Creating scheduled task..." -ForegroundColor Cyan

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Trigger $Trigger `
        -Action $Action `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Runs Genesis Engine v2 background synthesis every $Interval minutes. Target: $Target accepts/cycle."
    
    Write-Host @"

✓ Task created successfully!

  To view:    Get-ScheduledTask -TaskName '$TaskName'
  To run now: Start-ScheduledTask -TaskName '$TaskName'
  To remove:  .\setup_scheduled_task.ps1 -Uninstall

  Logs:       $PSScriptRoot\logs\genesis\
  Heartbeat:  $PSScriptRoot\logs\genesis\heartbeat.json

"@ -ForegroundColor Green

} catch {
    Write-Host @"

⚠ Failed to create task with LogonType S4U (run whether logged in or not).
  This requires elevated permissions.

  Alternative: Run in current session only:
"@ -ForegroundColor Yellow

    # Fallback: create with Interactive logon (only runs when logged in)
    $PrincipalFallback = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
    
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Trigger $Trigger `
        -Action $Action `
        -Settings $Settings `
        -Principal $PrincipalFallback `
        -Description "Runs Genesis Engine v2 background synthesis every $Interval minutes. Target: $Target accepts/cycle."
    
    Write-Host @"

✓ Task created (runs only when logged in).

  For background execution, run this script as Administrator.

"@ -ForegroundColor Green
}
