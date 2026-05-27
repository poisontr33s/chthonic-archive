#!/usr/bin/env pwsh
# @SID: MAS_INVOKE_VCVARS_FIXTURE_V1
<#
.SYNOPSIS
    Shared fixture for vcvarsall / vcvars64 invocation — bypasses Windows file-
    association "Open with" trap caused by bare `cmd /c` on Win11.

.DESCRIPTION
    Win11 associates the bare token `cmd` with a file-open handler on some
    configurations; `cmd /c "..."` then opens a dialog instead of executing.
    Using $env:ComSpec (always the full path: C:\Windows\System32\cmd.exe)
    bypasses the association entirely.

    This module provides two functions:
      Invoke-VcVars64   — sources vcvars64.bat, sets env vars in current process
      Test-VcVarsInit   — returns the first cl.exe path after sourcing, or $null

    Both scripts that previously used `cmd /c` inline (build_cupy.ps1,
    prebuild_check.ps1) dot-source this file and call these functions.
#>

function Invoke-VcVars64 {
    <#
    .SYNOPSIS
        Source vcvars64.bat and apply resulting env vars to the current process.
    .PARAMETER VcVarsPath
        Full path to vcvars64.bat.
    .OUTPUTS
        $true on success. Throws on failure.
    #>
    param([Parameter(Mandatory)][string]$VcVarsPath)

    if (-not (Test-Path $VcVarsPath)) {
        throw "vcvars64.bat not found at: $VcVarsPath"
    }

    # Write a temp batch that sources vcvars64 then dumps env — no quoting issues
    $tmpBat = [System.IO.Path]::ChangeExtension(
        [System.IO.Path]::GetTempFileName(), ".bat"
    )
    try {
        Set-Content -Path $tmpBat -Encoding ASCII -Value @"
@echo off
call "$VcVarsPath" >nul 2>&1
set
"@
        $envLines = & $env:ComSpec /c $tmpBat 2>&1
        foreach ($line in $envLines) {
            if ($line -match '^([^=]+)=(.*)$') {
                [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], "Process")
            }
        }
    }
    finally {
        Remove-Item $tmpBat -ErrorAction SilentlyContinue
    }

    return $true
}

function Test-VcVarsInit {
    <#
    .SYNOPSIS
        Source vcvars64.bat and return the first resolved cl.exe path, or $null.
    .PARAMETER VcVarsPath
        Full path to vcvars64.bat.
    #>
    param([Parameter(Mandatory)][string]$VcVarsPath)

    if (-not (Test-Path $VcVarsPath)) { return $null }

    $tmpBat = [System.IO.Path]::ChangeExtension(
        [System.IO.Path]::GetTempFileName(), ".bat"
    )
    try {
        Set-Content -Path $tmpBat -Encoding ASCII -Value @"
@echo off
call "$VcVarsPath" >nul 2>&1
where cl.exe 2>nul
"@
        $result = & $env:ComSpec /c $tmpBat 2>&1
        return ($result | Select-Object -First 1)
    }
    finally {
        Remove-Item $tmpBat -ErrorAction SilentlyContinue
    }
}
