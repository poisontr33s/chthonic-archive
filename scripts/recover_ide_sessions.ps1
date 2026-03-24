#!/usr/bin/env pwsh

<#
.SYNOPSIS
  Recover path-bound Copilot and Claude IDE sessions after a user-profile rename during migration.

.DESCRIPTION
  Run this on the desktop-local machine after the desktop clone package has been copied locally.
  This script remaps:
  - the Copilot chat session "Understanding Machine Learning Algorithms"
  - the Claude Code project bucket tied to C:\Users\erdno\chthonic-archive

  It must not be run from the remote laptop tunnel session.

.USAGE
  pwsh -NoProfile -File scripts/recover_ide_sessions.ps1
  pwsh -NoProfile -File scripts/recover_ide_sessions.ps1 -PackageRoot "C:\Users\eldno\Desktop\chthonic-desktop-clone"
#>

param(
    [string]$PackageRoot = "",
    [string]$RepoName = "chthonic-archive",
    [string]$OldUser = "erdno",
    [string]$CopilotSessionId = "de3fec44-4ae5-4c7e-bafe-2abbc4f10178",
    [string]$OldWorkspaceHash = "ef54bace47120bf8bda2a555aef41825"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Section {
    param([Parameter(Mandatory = $true)][string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Info {
    param([Parameter(Mandatory = $true)][string]$Message)
    Write-Host "  $Message" -ForegroundColor DarkGray
}

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Resolve-NormalizedPath {
    param([Parameter(Mandatory = $true)][string]$Path)
    return [System.IO.Path]::GetFullPath($Path)
}

function Invoke-RobocopyTransfer {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    Ensure-Directory -Path $Destination

    $args = @(
        $Source,
        $Destination,
        "/E",
        "/COPY:DAT",
        "/DCOPY:DAT",
        "/R:1",
        "/W:1",
        "/XJ",
        "/FFT",
        "/NP",
        "/NFL",
        "/NDL",
        "/NJH",
        "/NJS"
    )

    & robocopy @args | Out-Null
    if ($LASTEXITCODE -gt 7) {
        throw "robocopy failed for `"$Source`" -> `"$Destination`" with exit code $LASTEXITCODE"
    }
}

if ([string]::IsNullOrWhiteSpace($PackageRoot)) {
    $PackageRoot = Join-Path $HOME "Desktop\chthonic-desktop-clone"
}

$PackageRoot = Resolve-NormalizedPath -Path $PackageRoot
$NewUser = $env:USERNAME

$oldRepoPathUpper = "C:\Users\$OldUser\$RepoName"
$oldRepoPathLower = $oldRepoPathUpper.ToLower()
$newRepoPathUpper = Join-Path $HOME $RepoName
$newRepoPathLower = $newRepoPathUpper.ToLower()

$oldProjectSlug = "C--Users-$OldUser-$RepoName"
$newProjectSlug = "C--Users-$NewUser-$RepoName"

$desktopProcesses = @(Get-Process -Name "Code - Insiders","code-tunnel-insiders" -ErrorAction SilentlyContinue)
if ($desktopProcesses.Count -gt 0) {
    Write-Host "warning: close local VS Code Insiders windows before recovery for the cleanest result." -ForegroundColor Yellow
    foreach ($proc in $desktopProcesses) {
        Write-Host ("  {0} ({1})" -f $proc.ProcessName, $proc.Id) -ForegroundColor Yellow
    }
}

$packageWorkspaceStorage = Join-Path $PackageRoot "payload\appdata\Code - Insiders\User\workspaceStorage"
$localWorkspaceStorage = Join-Path $env:APPDATA "Code - Insiders\User\workspaceStorage"

if (-not (Test-Path -LiteralPath $packageWorkspaceStorage)) {
    throw "Package workspaceStorage not found: $packageWorkspaceStorage"
}

if (-not (Test-Path -LiteralPath $localWorkspaceStorage)) {
    throw "Local workspaceStorage not found: $localWorkspaceStorage"
}

Write-Section "Locate Desktop Workspace Hash"
$targetWorkspace = Get-ChildItem $localWorkspaceStorage -Directory | Where-Object {
    $workspaceJson = Join-Path $_.FullName "workspace.json"
    if (-not (Test-Path -LiteralPath $workspaceJson)) { return $false }

    $content = Get-Content -LiteralPath $workspaceJson -Raw
    $content -match [regex]::Escape(("file:///" + $newRepoPathUpper.Replace("\", "/").Replace(":", "%3A")))
} | Select-Object -First 1

if (-not $targetWorkspace) {
    throw "No desktop workspaceStorage folder found for $newRepoPathUpper. Open the local repo once in local VS Code Insiders, close it, and rerun."
}

Write-Info ("desktop workspace hash: {0}" -f $targetWorkspace.Name)

Write-Section "Recover Copilot Session"
$srcChat = Join-Path $packageWorkspaceStorage "$OldWorkspaceHash\chatSessions\$CopilotSessionId.jsonl"
if (-not (Test-Path -LiteralPath $srcChat)) {
    throw "Missing source Copilot session in package: $srcChat"
}

$dstChatDir = Join-Path $targetWorkspace.FullName "chatSessions"
Ensure-Directory -Path $dstChatDir
Copy-Item -LiteralPath $srcChat -Destination $dstChatDir -Force
Write-Info ("copied chat session: {0}" -f $CopilotSessionId)

$srcCopilotDebug = Join-Path $packageWorkspaceStorage "$OldWorkspaceHash\GitHub.copilot-chat\debug-logs\$CopilotSessionId"
if (Test-Path -LiteralPath $srcCopilotDebug) {
    $dstCopilotDebugRoot = Join-Path $targetWorkspace.FullName "GitHub.copilot-chat\debug-logs"
    Ensure-Directory -Path $dstCopilotDebugRoot
    Invoke-RobocopyTransfer -Source $srcCopilotDebug -Destination (Join-Path $dstCopilotDebugRoot $CopilotSessionId)
    Write-Info "copied Copilot debug logs"
}

$srcCopilotResources = Join-Path $packageWorkspaceStorage "$OldWorkspaceHash\GitHub.copilot-chat\chat-session-resources\$CopilotSessionId"
if (Test-Path -LiteralPath $srcCopilotResources) {
    $dstCopilotResourcesRoot = Join-Path $targetWorkspace.FullName "GitHub.copilot-chat\chat-session-resources"
    Ensure-Directory -Path $dstCopilotResourcesRoot
    Invoke-RobocopyTransfer -Source $srcCopilotResources -Destination (Join-Path $dstCopilotResourcesRoot $CopilotSessionId)
    Write-Info "copied Copilot session resources"
}

$srcEditSession = Join-Path $packageWorkspaceStorage "$OldWorkspaceHash\chatEditingSessions\$CopilotSessionId"
if (Test-Path -LiteralPath $srcEditSession) {
    $dstEditRoot = Join-Path $targetWorkspace.FullName "chatEditingSessions"
    Ensure-Directory -Path $dstEditRoot
    Invoke-RobocopyTransfer -Source $srcEditSession -Destination (Join-Path $dstEditRoot $CopilotSessionId)
    Write-Info "copied Copilot chat editing session"
}

Write-Section "Recover Claude Project Sessions"
$srcClaudeProject = Join-Path $PackageRoot "payload\home\.claude\projects\$oldProjectSlug"
$dstClaudeProjectsRoot = Join-Path $HOME ".claude\projects"
$dstClaudeProject = Join-Path $dstClaudeProjectsRoot $newProjectSlug

if (-not (Test-Path -LiteralPath $srcClaudeProject)) {
    throw "Missing source Claude project bucket in package: $srcClaudeProject"
}

Ensure-Directory -Path $dstClaudeProjectsRoot
Invoke-RobocopyTransfer -Source $srcClaudeProject -Destination $dstClaudeProject
Write-Info ("copied Claude project bucket: {0}" -f $newProjectSlug)

$oldClaudeProjectRootUpper = "C:\Users\$OldUser\.claude\projects\$oldProjectSlug"
$oldClaudeProjectRootLower = $oldClaudeProjectRootUpper.ToLower()
$newClaudeProjectRootUpper = Join-Path $HOME ".claude\projects\$newProjectSlug"
$newClaudeProjectRootLower = $newClaudeProjectRootUpper.ToLower()

Get-ChildItem $dstClaudeProject -Recurse -File | Where-Object {
    $_.Extension -in ".json", ".jsonl"
} | ForEach-Object {
    $raw = Get-Content -LiteralPath $_.FullName -Raw
    $new = $raw
    $new = $new.Replace($oldClaudeProjectRootUpper, $newClaudeProjectRootUpper)
    $new = $new.Replace($oldClaudeProjectRootLower, $newClaudeProjectRootLower)
    $new = $new.Replace($oldRepoPathUpper, $newRepoPathUpper)
    $new = $new.Replace($oldRepoPathLower, $newRepoPathLower)
    $new = $new.Replace($oldProjectSlug, $newProjectSlug)

    if ($new -ne $raw) {
        Set-Content -LiteralPath $_.FullName -Value $new -Encoding utf8NoBOM
    }
}

Write-Section "Done"
Write-Host "Recovery complete. Reopen local VS Code Insiders and the local repo." -ForegroundColor Green
Write-Info ("Copilot session ID: {0}" -f $CopilotSessionId)
Write-Info ("Claude project bucket: {0}" -f $newProjectSlug)
