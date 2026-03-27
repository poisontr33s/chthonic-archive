#!/usr/bin/env pwsh
#
# @SID: SCRIPT_ROBOCOPY_PAUSE_RESUME_V1
# @Type: UTILITY
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Pause, resume, or inspect a running robocopy process.
#

<#
.SYNOPSIS
  Pause, resume, or inspect a running robocopy process.

.USAGE
  pwsh -NoProfile -File scripts/robocopy_pause_resume.ps1 -Action status
  pwsh -NoProfile -File scripts/robocopy_pause_resume.ps1 -Action pause
  pwsh -NoProfile -File scripts/robocopy_pause_resume.ps1 -Action resume
  pwsh -NoProfile -File scripts/robocopy_pause_resume.ps1 -Action status -Id 1234
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("pause", "resume", "status")]
    [string]$Action,

    [int]$Id,

    [string]$Name = "robocopy"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not ("ProcessSuspendNative" -as [type])) {
    Add-Type @"
using System;
using System.Runtime.InteropServices;

public static class ProcessSuspendNative
{
    [DllImport("ntdll.dll", SetLastError = true)]
    public static extern int NtSuspendProcess(IntPtr processHandle);

    [DllImport("ntdll.dll", SetLastError = true)]
    public static extern int NtResumeProcess(IntPtr processHandle);
}
"@
}

function Get-Targets {
    if ($Id -gt 0) {
        return @(Get-Process -Id $Id -ErrorAction Stop)
    }

    $targets = @(Get-Process -Name $Name -ErrorAction SilentlyContinue)
    if ($targets.Count -eq 0) {
        throw "No process found for name '$Name'."
    }

    return $targets
}

function Get-ThreadSnapshot {
    param(
        [Parameter(Mandatory = $true)]
        [System.Diagnostics.Process]$Process
    )

    $threads = @($Process.Threads)
    $suspended = @(
        $threads | Where-Object {
            $_.ThreadState -eq [System.Diagnostics.ThreadState]::Wait -and
            $_.WaitReason -eq [System.Diagnostics.ThreadWaitReason]::Suspended
        }
    ).Count

    [pscustomobject]@{
        Id = $Process.Id
        Name = $Process.ProcessName
        StartTime = $Process.StartTime
        TotalThreads = $threads.Count
        SuspendedThreads = $suspended
        FullySuspended = ($threads.Count -gt 0 -and $suspended -eq $threads.Count)
    }
}

function Invoke-ProcessAction {
    param(
        [Parameter(Mandatory = $true)]
        [System.Diagnostics.Process]$Process,

        [Parameter(Mandatory = $true)]
        [ValidateSet("pause", "resume")]
        [string]$Mode
    )

    $result = if ($Mode -eq "pause") {
        [ProcessSuspendNative]::NtSuspendProcess($Process.Handle)
    } else {
        [ProcessSuspendNative]::NtResumeProcess($Process.Handle)
    }

    if ($result -ne 0) {
        throw "$Mode failed for PID $($Process.Id) with NTSTATUS $result."
    }
}

$targets = Get-Targets

switch ($Action) {
    "status" {
        $targets | ForEach-Object { Get-ThreadSnapshot -Process $_ } | Format-Table -AutoSize
    }
    "pause" {
        foreach ($target in $targets) {
            Invoke-ProcessAction -Process $target -Mode "pause"
        }
        $targets | ForEach-Object { Get-ThreadSnapshot -Process $_ } | Format-Table -AutoSize
    }
    "resume" {
        foreach ($target in $targets) {
            Invoke-ProcessAction -Process $target -Mode "resume"
        }
        $targets | ForEach-Object { Get-ThreadSnapshot -Process $_ } | Format-Table -AutoSize
    }
}
