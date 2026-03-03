# @SID: FORGE_BATCH_TRANSLITERATION_V1
# Purpose: Faithful PowerShell transliteration of the tracked batch artifact.
# Source-Files: dumpster-dive/intake/claude-ide-harden-2026-02-10/tier-1-direct/claude_process_wrapper.bat
# Pathway: batch -> PowerShell transliteration
# Kept: Script intent, comments, and control flow markers.
# Discarded: cmd.exe-specific syntax.
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
