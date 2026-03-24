# @SID: FORGE_BATCH_TRANSLITERATION_PROMOTED_V1
# Purpose: Active-lane PowerShell promotion of the recovered batch wrapper semantics.
# Source-Files: dumpster-dive/forge/tempered/powershell/batch_transliteration.ps1
# Pathway: tempered/powershell -> scripts promotion lane
# Kept: Script intent, batch transcript fidelity, and wrapper dispatch behavior.
# Discarded: cmd.exe-specific execution model.

$script:RecoveredBatchLines = @(
    '@echo off',
    'setlocal',
    '',
    'REM Claude Code VS Code process wrapper shim.',
    'REM The extension only accepts an executable path for claudeCode.claudeProcessWrapper.',
    'REM This shim launches PowerShell and forwards all args to scripts/claude_process_wrapper.ps1.',
    '',
    'set "REPO_ROOT=%~dp0.."',
    'set "PWSH=C:\Program Files\PowerShell\7\pwsh.exe"',
    '',
    '"%PWSH%" -NoProfile -ExecutionPolicy Bypass -File "%REPO_ROOT%\scripts\claude_process_wrapper.ps1" %*',
    'exit /b %ERRORLEVEL%',
    ''
)

function Get-RecoveredBatchTranscript {
    [CmdletBinding()]
    param()

    return $script:RecoveredBatchLines
}

function Show-RecoveredBatchTranscript {
    [CmdletBinding()]
    param()

    $script:RecoveredBatchLines | ForEach-Object { Write-Host $_ }
}

function Invoke-RecoveredBatchWrapper {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments,
        [string]$PowerShellPath = "C:\Program Files\PowerShell\7\pwsh.exe",
        [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    )

    $wrapperScript = Join-Path $RepoRoot "scripts/claude_process_wrapper.ps1"
    if (-not (Test-Path -LiteralPath $wrapperScript)) {
        throw "Recovered wrapper target not found: $wrapperScript"
    }

    & $PowerShellPath -NoProfile -ExecutionPolicy Bypass -File $wrapperScript @Arguments
    return $LASTEXITCODE
}
