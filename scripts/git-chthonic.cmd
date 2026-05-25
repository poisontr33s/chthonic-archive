@echo off
:: ============================================================================
:: git-chthonic.cmd — VS Code git.path shim for one-attempt commits
:: ============================================================================
:: Wedjat-Quipu Spectrum: GOLD
:: Temple-Ayllu Zone: THE OBSERVATORY
:: SID: SHIM_GIT_CHTHONIC_V1
::
:: Intercepts `git commit` invocations from VS Code. Runs chthonic-rescue.ts
:: BEFORE forwarding to real git so the rescue is in the index when git takes
:: its commit-content snapshot. Solves the V1.4 two-attempt structural flaw.
::
:: All other git subcommands pass through unchanged.
::
:: Wired via .vscode/settings.json: "git.path": "${workspaceFolder}/scripts/git-chthonic.cmd"
:: ============================================================================
setlocal enabledelayedexpansion

set "REAL_GIT=C:\Program Files\Git\cmd\git.exe"
set "BUN=%USERPROFILE%\.bun\bin\bun.exe"
set "REPO_ROOT=%~dp0.."

:: Scan all args for `commit` subcommand. VS Code invokes with leading -c
:: flags (e.g., `-c user.useConfigOnly=true commit ...`), so `commit` is
:: NOT always %1 — must scan.
set "IS_COMMIT="
for %%a in (%*) do (
    if /i "%%~a"=="commit" set "IS_COMMIT=1"
)

if defined IS_COMMIT (
    if exist "%BUN%" (
        "%BUN%" run "%~dp0chthonic-rescue.ts" --silent 2>nul
    )
)

"%REAL_GIT%" %*
exit /b %errorlevel%
