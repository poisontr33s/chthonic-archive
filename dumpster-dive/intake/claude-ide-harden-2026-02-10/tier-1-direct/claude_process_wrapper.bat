@echo off
setlocal

REM Claude Code VS Code process wrapper shim.
REM The extension only accepts an executable path for claudeCode.claudeProcessWrapper.
REM This shim launches PowerShell and forwards all args to scripts/claude_process_wrapper.ps1.

set "REPO_ROOT=%~dp0.."
set "PWSH=C:\Program Files\PowerShell\7\pwsh.exe"

"%PWSH%" -NoProfile -ExecutionPolicy Bypass -File "%REPO_ROOT%\scripts\claude_process_wrapper.ps1" %*
exit /b %ERRORLEVEL%

