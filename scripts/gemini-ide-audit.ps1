#!/usr/bin/env pwsh
# Purpose: Audit Gemini CLI IDE integration prerequisites after VS Code Insiders or Gemini updates.

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Check {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [bool]$Passed,
        [Parameter(Mandatory = $true)]
        [string]$Detail
    )

    $status = if ($Passed) { 'PASS' } else { 'FAIL' }
    $color = if ($Passed) { 'Green' } else { 'Red' }
    Write-Host ("[{0}] {1}" -f $status, $Name) -ForegroundColor $color
    Write-Host ("       {0}" -f $Detail)
}

function Get-JsonValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Pattern
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    $match = Select-String -Path $Path -Pattern $Pattern -SimpleMatch
    if ($match) {
        return $match.Line.Trim()
    }

    return $null
}

$issues = New-Object System.Collections.Generic.List[string]

$settingsPath = Join-Path $env:APPDATA 'Code - Insiders\User\settings.json'
$argvPath = Join-Path $env:USERPROFILE '.vscode-insiders\argv.json'
$expectedExtension = 'google.gemini-cli-vscode-ide-companion'

Write-Host 'Gemini IDE Audit'
Write-Host ("Date: {0}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'))
Write-Host

$codeCommand = $null
try {
    $codeCommand = Get-Command code -ErrorAction Stop
    Write-Check -Name 'code shim / VS Code CLI' -Passed $true -Detail ("Resolved to {0}" -f $codeCommand.Source)
} catch {
    $issues.Add("`'code`' does not resolve on PATH.")
    Write-Check -Name 'code shim / VS Code CLI' -Passed $false -Detail "Gemini /ide install expects 'code' on PATH on Windows."
}

$extensionInstalled = $false
if ($codeCommand) {
    try {
        $extensions = & $codeCommand.Source --list-extensions --show-versions 2>$null
        $extensionLine = $extensions | Where-Object { $_ -match "^$([regex]::Escape($expectedExtension))@" } | Select-Object -First 1
        if ($extensionLine) {
            $extensionInstalled = $true
            Write-Check -Name 'Gemini companion extension' -Passed $true -Detail ("Installed: {0}" -f $extensionLine)
        } else {
            $issues.Add("Gemini companion extension is not installed in VS Code Insiders.")
            Write-Check -Name 'Gemini companion extension' -Passed $false -Detail ("Missing extension id '{0}'." -f $expectedExtension)
        }
    } catch {
        $issues.Add("Failed to query installed extensions through 'code'.")
        Write-Check -Name 'Gemini companion extension' -Passed $false -Detail $_.Exception.Message
    }
} else {
    Write-Check -Name 'Gemini companion extension' -Passed $false -Detail "Skipped because 'code' is unavailable."
}

$envRelaunchLine = Get-JsonValue -Path $settingsPath -Pattern '"terminal.integrated.environmentChangesRelaunch": true'
if ($envRelaunchLine) {
    Write-Check -Name 'Terminal env relaunch setting' -Passed $true -Detail ("Found in {0}" -f $settingsPath)
} else {
    $issues.Add("`"terminal.integrated.environmentChangesRelaunch`" is not set to true in Insiders settings.")
    Write-Check -Name 'Terminal env relaunch setting' -Passed $false -Detail ("Expected in {0}" -f $settingsPath)
}

$gpuArgLine = Get-JsonValue -Path $argvPath -Pattern '"disable-hardware-acceleration": true'
if ($gpuArgLine) {
    Write-Check -Name 'Insiders GPU workaround' -Passed $true -Detail ("Found in {0}" -f $argvPath)
} else {
    $issues.Add("`"disable-hardware-acceleration`" is not set to true in Insiders argv.json.")
    Write-Check -Name 'Insiders GPU workaround' -Passed $false -Detail ("Expected in {0}" -f $argvPath)
}

$ideVars = Get-ChildItem Env:GEMINI_CLI_IDE_* -ErrorAction SilentlyContinue | Sort-Object Name
$isVsCodeTerminal = [bool]($env:TERM_PROGRAM -eq 'vscode' -or $env:VSCODE_IPC_HOOK_CLI)

if ($ideVars) {
    $names = ($ideVars | Select-Object -ExpandProperty Name) -join ', '
    Write-Check -Name 'Gemini IDE environment variables' -Passed $true -Detail ("Present in current shell: {0}" -f $names)
} elseif ($isVsCodeTerminal) {
    $issues.Add('No GEMINI_CLI_IDE_* variables are present in this VS Code terminal.')
    Write-Check -Name 'Gemini IDE environment variables' -Passed $false -Detail 'Open a brand new integrated terminal in Insiders and rerun this script.'
} else {
    Write-Check -Name 'Gemini IDE environment variables' -Passed $false -Detail 'This shell is not a VS Code integrated terminal. Run the script from a fresh Insiders terminal to verify env injection.'
}

Write-Host
if ($issues.Count -eq 0 -and $ideVars) {
    Write-Host 'Overall: PASS' -ForegroundColor Green
    Write-Host 'Gemini IDE integration prerequisites are in place for this terminal session.'
    exit 0
}

if ($issues.Count -eq 0) {
    Write-Host 'Overall: PARTIAL' -ForegroundColor Yellow
    Write-Host 'Static prerequisites pass. The live IDE env check still needs a fresh VS Code Insiders terminal.'
    exit 0
}

Write-Host 'Overall: FAIL' -ForegroundColor Red
foreach ($issue in $issues) {
    Write-Host ("- {0}" -f $issue)
}
exit 1
