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

:: Dynamic REAL_GIT lookup. PATH-based via `where`, excluding our own shim
:: (else infinite recursion). Falls back to standard Git-for-Windows path
:: if `where` finds nothing usable. This survives git upgrades, scoop
:: relocations, or any future install path drift without re-editing this file.
set "REAL_GIT="
for /f "delims=" %%i in ('where git.exe 2^>nul') do (
    echo %%i | findstr /i /v "git-chthonic" >nul && if not defined REAL_GIT set "REAL_GIT=%%i"
)
if not defined REAL_GIT set "REAL_GIT=C:\Program Files\Git\cmd\git.exe"

:: Dynamic BUN lookup. Same pattern as REAL_GIT — PATH first, hardcoded
:: fallback. If bun is missing entirely, rescue is silently skipped and
:: commit proceeds to real git (V1.4 hook-level rescue remains as backstop).
set "BUN="
for /f "delims=" %%i in ('where bun.exe 2^>nul') do if not defined BUN set "BUN=%%i"
if not defined BUN set "BUN=%USERPROFILE%\.bun\bin\bun.exe"

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
