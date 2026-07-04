#!/usr/bin/env pwsh
# SID: CHTHONIC_MICA_RENDERER_VISUAL_PROBE_PS1_V1
# scripts/mica-renderer-visual-probe.ps1
#
# Temporary visual truth probe for the Chthonic VS Code Insiders renderer.
# This exists so the human eye can verify renderer CSS without DevTools.
#
# Modes:
#   -Enable          Insert a visible banner and outlines into workbench.html.
#   -Enable -Stress  Also force exaggerated transparency for visual proof.
#   -Disable         Remove the visual probe.
#   -Status          Report whether the probe is present.
#
# Made by Claude. Corrected by Codex.

[CmdletBinding()]
param(
    [switch]$Enable,
    [switch]$Disable,
    [switch]$Status,
    [switch]$Stress,
    [switch]$SkipReconcile
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ProgramsRoot = Join-Path $env:LOCALAPPDATA 'Programs\Microsoft VS Code Insiders'
$BackupDir = Join-Path $RepoRoot 'CLAUDEBASE\hold\vscode-insiders-substrate\backups'

$ProbeStart = '<!-- chthonic.renderer.visual-probe.begin -->'
$ProbeEnd = '<!-- chthonic.renderer.visual-probe.end -->'
$ProbePattern = '(?s)\r?\n?\s*<!-- chthonic\.renderer\.visual-probe\.begin -->.*?<!-- chthonic\.renderer\.visual-probe\.end -->\s*\r?\n?'

function Find-AppRoot {
    $processRoots = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -eq 'Code - Insiders.exe' -and
            $_.CommandLine -match '--app-path="([^"]+\\resources\\app)"'
        } |
        ForEach-Object {
            if ($_.CommandLine -match '--app-path="([^"]+\\resources\\app)"') { $matches[1] }
        } |
        Sort-Object -Unique

    foreach ($root in $processRoots) {
        if (Test-Path (Join-Path $root 'out\vs\code\electron-browser\workbench\workbench.html')) {
            return $root
        }
    }

    $dirs = Get-ChildItem -LiteralPath $ProgramsRoot -Directory -ErrorAction Stop |
        Where-Object { $_.Name -match '^[0-9a-f]{10,}$' } |
        Sort-Object LastWriteTimeUtc -Descending

    foreach ($dir in $dirs) {
        $root = Join-Path $dir.FullName 'resources\app'
        if (Test-Path (Join-Path $root 'out\vs\code\electron-browser\workbench\workbench.html')) {
            return $root
        }
    }

    throw "No VS Code Insiders app root found under $ProgramsRoot"
}

function Read-AppMeta {
    param([string]$AppRoot)
    $productPath = Join-Path $AppRoot 'product.json'
    $raw = [System.IO.File]::ReadAllText($productPath, [System.Text.Encoding]::UTF8)
    $product = $raw | ConvertFrom-Json
    return @{
        ProductPath = $productPath
        Commit = $product.commit
        Version = $product.version
    }
}

function Get-WorkbenchHtmlPath {
    param([string]$AppRoot)
    $path = Join-Path $AppRoot 'out\vs\code\electron-browser\workbench\workbench.html'
    if (-not (Test-Path $path)) { throw "workbench.html not found at $path" }
    return $path
}

function New-ProbeCss {
    param([switch]$Stress)

    $stressCss = ''
    $mode = 'presence'
    if ($Stress) {
        $mode = 'stress'
        $stressCss = @'

body,
.monaco-workbench {
  background: transparent !important;
}

.monaco-workbench .part.sidebar,
.monaco-workbench .part.auxiliarybar {
  background: color-mix(in oklch, var(--vscode-sideBar-background) 52%, transparent) !important;
}

.monaco-workbench .part.activitybar,
.monaco-workbench .part.panel,
.monaco-workbench .part.statusbar,
.monaco-workbench .part.titlebar {
  background: color-mix(in oklch, currentColor 20%, transparent) !important;
}

.monaco-workbench .part.editor,
.monaco-workbench .editor-group-container,
.monaco-workbench .editor-instance,
.monaco-workbench .monaco-editor {
  background: color-mix(in oklch, var(--vscode-editor-background) 78%, transparent) !important;
}

.monaco-workbench .quick-input-widget {
  background: color-mix(in oklch, var(--vscode-quickInput-background, var(--vscode-editorWidget-background)) 42%, transparent) !important;
  backdrop-filter: saturate(220%) brightness(1.18) !important;
  -webkit-backdrop-filter: saturate(220%) brightness(1.18) !important;
}
'@
    }

    return @"
$ProbeStart
<style data-chthonic-renderer-visual-probe="true" data-mode="$mode">
/* Temporary visual renderer probe. Remove with scripts/mica-renderer-visual-probe.ps1 -Disable. Made by Claude. */
body::before {
  content: "CHTHONIC RENDERER PROBE LIVE ($mode)";
  position: fixed;
  top: 6px;
  right: 118px;
  z-index: 2147483647;
  padding: 4px 8px;
  font: 700 11px/1.2 system-ui, sans-serif;
  letter-spacing: 0;
  color: #050505;
  background: #f4c430;
  border: 1px solid #00e5ff;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, .65), 0 8px 24px rgba(0, 0, 0, .35);
  pointer-events: none;
}

body::after {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 2147483646;
  border: 3px solid #f4c430;
  pointer-events: none;
}

.monaco-workbench .part.sidebar {
  outline: 3px solid #00e5ff !important;
  outline-offset: -3px !important;
}

.monaco-workbench .part.editor {
  outline: 3px solid #f4c430 !important;
  outline-offset: -3px !important;
}

.monaco-workbench .quick-input-widget {
  outline: 4px solid #ff4d8d !important;
  outline-offset: -4px !important;
}
$stressCss
</style>
$ProbeEnd
"@
}

function Write-Backup {
    param(
        [string]$WorkbenchHtml,
        [string]$Commit
    )
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $dest = Join-Path $BackupDir "workbench.html.renderer-probe.$($Commit.Substring(0, 10)).$stamp.bak"
    Copy-Item -LiteralPath $WorkbenchHtml -Destination $dest -Force
    return $dest
}

function Invoke-Reconcile {
    if ($SkipReconcile) { return 'skipped' }
    $script = Join-Path $RepoRoot 'scripts\insiders-integrity-reconcile.ps1'
    if (-not (Test-Path $script)) { return 'missing' }
    & pwsh -NoProfile -File $script -Apply | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "insiders-integrity-reconcile.ps1 -Apply failed" }
    return 'applied'
}

function Get-State {
    $appRoot = Find-AppRoot
    $meta = Read-AppMeta -AppRoot $appRoot
    $htmlPath = Get-WorkbenchHtmlPath -AppRoot $appRoot
    $raw = [System.IO.File]::ReadAllText($htmlPath, [System.Text.Encoding]::UTF8)
    return @{
        AppRoot = $appRoot
        Version = $meta.Version
        Commit = $meta.Commit
        WorkbenchHtml = $htmlPath
        Present = $raw.Contains($ProbeStart) -and $raw.Contains($ProbeEnd)
        Raw = $raw
    }
}

function Invoke-Enable {
    $state = Get-State
    $backup = Write-Backup -WorkbenchHtml $state.WorkbenchHtml -Commit $state.Commit
    $clean = [regex]::Replace($state.Raw, $ProbePattern, "`r`n")
    $block = New-ProbeCss -Stress:$Stress
    $rx = [regex]'(?i)</head>'
    if (-not $rx.IsMatch($clean)) { throw "</head> not found in workbench.html" }
    $updated = $rx.Replace($clean, "$block`r`n`t</head>", 1)
    [System.IO.File]::WriteAllText($state.WorkbenchHtml, $updated, [System.Text.Encoding]::UTF8)
    $reconcile = Invoke-Reconcile
    [pscustomobject]@{
        Action = if ($Stress) { 'enabled-stress' } else { 'enabled' }
        RestartRequired = $true
        Backup = $backup
        Reconcile = $reconcile
        WorkbenchHtml = $state.WorkbenchHtml
    }
}

function Invoke-Disable {
    $state = Get-State
    $backup = Write-Backup -WorkbenchHtml $state.WorkbenchHtml -Commit $state.Commit
    $updated = [regex]::Replace($state.Raw, $ProbePattern, "`r`n")
    [System.IO.File]::WriteAllText($state.WorkbenchHtml, $updated, [System.Text.Encoding]::UTF8)
    $reconcile = Invoke-Reconcile
    [pscustomobject]@{
        Action = 'disabled'
        RestartRequired = $true
        Backup = $backup
        Reconcile = $reconcile
        WorkbenchHtml = $state.WorkbenchHtml
    }
}

function Invoke-Status {
    $state = Get-State
    [pscustomobject]@{
        Present = $state.Present
        Version = $state.Version
        Commit = $state.Commit
        AppRoot = $state.AppRoot
        WorkbenchHtml = $state.WorkbenchHtml
    }
}

if ($Enable -and $Disable) { throw "Use only one mode: -Enable or -Disable" }
if ($Enable) { Invoke-Enable; exit 0 }
if ($Disable) { Invoke-Disable; exit 0 }
Invoke-Status
