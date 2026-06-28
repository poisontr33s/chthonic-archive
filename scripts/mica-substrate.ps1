#!/usr/bin/env pwsh
# SID: CHTHONIC_MICA_SUBSTRATE_PS1_V1
# Purpose: Own the local VS Code Insiders Mica substrate without delegating
# color authority to Vibrancy Continued's broad themeCSS patch.
# Made by Claude. Continued by Codex.

[CmdletBinding(DefaultParameterSetName = 'Status')]
param(
    [Parameter(ParameterSetName = 'Enable')]
    [switch]$Enable,

    [Parameter(ParameterSetName = 'Disable')]
    [switch]$Disable,

    [Parameter(ParameterSetName = 'Reapply')]
    [switch]$Reapply,

    [Parameter(ParameterSetName = 'Status')]
    [switch]$Status,

    [Parameter(ParameterSetName = 'RestoreLatestBackup')]
    [switch]$RestoreLatestBackup,

    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA 'Programs\Microsoft VS Code Insiders'),
    [string]$Material = 'mica'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$RuntimePath = Join-Path $RepoRoot 'designs\chthonic-mica.cjs'
$CssPath = Join-Path $RepoRoot 'designs\vibrancy-obsidian.css'
$BackupRoot = Join-Path $RepoRoot 'CLAUDEBASE\hold\vscode-insiders-substrate\backups'

function ConvertTo-FileUri {
    param([Parameter(Mandatory)][string]$Path)
    return ([System.Uri](Resolve-Path -LiteralPath $Path).ProviderPath).AbsoluteUri
}

function Get-InsidersAppRoot {
    param([Parameter(Mandatory)][string]$Root)

    if (-not (Test-Path -LiteralPath $Root)) {
        throw "VS Code Insiders install root not found: $Root"
    }

    $candidates = New-Object System.Collections.Generic.List[object]
    $directApp = Join-Path $Root 'resources\app'
    $directMain = Join-Path $directApp 'out\main.js'
    if (Test-Path -LiteralPath $directMain) {
        $candidates.Add([pscustomobject]@{
            AppRoot = $directApp
            MainJs = $directMain
            Stamp = (Get-Item -LiteralPath $directMain).LastWriteTimeUtc
        })
    }

    Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $app = Join-Path $_.FullName 'resources\app'
        $main = Join-Path $app 'out\main.js'
        if (Test-Path -LiteralPath $main) {
            $candidates.Add([pscustomobject]@{
                AppRoot = $app
                MainJs = $main
                Stamp = (Get-Item -LiteralPath $main).LastWriteTimeUtc
            })
        }
    }

    $chosen = $candidates | Sort-Object Stamp -Descending | Select-Object -First 1
    if (-not $chosen) {
        throw "No VS Code Insiders app root containing out\main.js found under: $Root"
    }
    return $chosen.AppRoot
}

function Get-WorkbenchHtml {
    param([Parameter(Mandatory)][string]$AppRoot)

    $known = Join-Path $AppRoot 'out\vs\code\electron-browser\workbench\workbench.html'
    if (Test-Path -LiteralPath $known) {
        return $known
    }

    $searchRoot = Join-Path $AppRoot 'out\vs\code'
    $found = Get-ChildItem -LiteralPath $searchRoot -Recurse -Filter 'workbench.html' -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($found) {
        return $found.FullName
    }

    throw "workbench.html not found below: $searchRoot"
}

function Get-SubstrateState {
    $appRoot = Get-InsidersAppRoot -Root $InstallRoot
    $mainJs = Join-Path $appRoot 'out\main.js'
    $workbenchHtml = Get-WorkbenchHtml -AppRoot $appRoot
    $packageJson = Join-Path $appRoot 'package.json'
    $productJson = Join-Path $appRoot 'product.json'

    $package = if (Test-Path -LiteralPath $packageJson) {
        Get-Content -LiteralPath $packageJson -Raw | ConvertFrom-Json
    } else {
        $null
    }
    $product = if (Test-Path -LiteralPath $productJson) {
        Get-Content -LiteralPath $productJson -Raw | ConvertFrom-Json
    } else {
        $null
    }
    $main = Get-Content -LiteralPath $mainJs -Raw
    $html = Get-Content -LiteralPath $workbenchHtml -Raw
    $running = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
        try {
            $_.Path -and $_.Path.StartsWith($InstallRoot, [System.StringComparison]::OrdinalIgnoreCase)
        } catch {
            $false
        }
    }).Count

    [pscustomobject]@{
        InstallRoot = $InstallRoot
        AppRoot = $appRoot
        Version = if ($package) { $package.version } else { 'unknown' }
        Commit = if ($product) { $product.commit } else { 'unknown' }
        Electron = if ($package -and $package.devDependencies.electron) { $package.devDependencies.electron } else { 'unknown' }
        ClaudeAgentSdk = if ($product -and $product.agentSdks -and $product.agentSdks.claude) { $product.agentSdks.claude.version } else { 'unknown' }
        CodexAgentSdk = if ($product -and $product.agentSdks -and $product.agentSdks.codex) { $product.agentSdks.codex.version } else { 'unknown' }
        AgentSdks = if ($product -and $product.agentSdks) { $product.agentSdks } else { $null }
        MainJs = $mainJs
        WorkbenchHtml = $workbenchHtml
        RuntimePath = $RuntimePath
        CssPath = $CssPath
        HasVibrancyBlock = $main.Contains('VSCODE-VIBRANCY-START')
        HasChthonicBlock = $main.Contains('CHTHONIC-MICA-START')
        HasSubstrateCss = $html.Contains('data-claude-design-substrate="vibrancy-obsidian"')
        RunningProcessCount = $running
    }
}

function Remove-SubstrateBlocks {
    param([Parameter(Mandatory)][string]$Text)

    $patterns = @(
        '(?s)\r?\n?/\* !! VSCODE-VIBRANCY-START !! \*/.*?/\* !! VSCODE-VIBRANCY-END !! \*/\r?\n?',
        '(?s)\r?\n?/\* !! CHTHONIC-MICA-START !! \*/.*?/\* !! CHTHONIC-MICA-END !! \*/\r?\n?'
    )

    foreach ($pattern in $patterns) {
        $Text = [regex]::Replace($Text, $pattern, "`r`n")
    }
    return $Text.TrimStart([char[]]"`r`n")
}

function Remove-SubstrateCssLink {
    param([Parameter(Mandatory)][string]$Html)

    return [regex]::Replace(
        $Html,
        '(?m)^\s*<link rel="stylesheet" data-claude-design-substrate="vibrancy-obsidian"[^>]*>\s*\r?\n?',
        ''
    )
}

function New-SubstrateBackup {
    param([Parameter(Mandatory)]$State)

    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
    $safeVersion = ($State.Version -replace '[^a-zA-Z0-9_.-]', '_')
    $safeCommit = if ($State.Commit -and $State.Commit -ne 'unknown') {
        $State.Commit.Substring(0, [Math]::Min(10, $State.Commit.Length))
    } else {
        'unknown'
    }
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backupDir = Join-Path $BackupRoot "$safeVersion-$safeCommit-$stamp"
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

    Copy-Item -LiteralPath $State.MainJs -Destination (Join-Path $backupDir 'main.js') -Force
    Copy-Item -LiteralPath $State.WorkbenchHtml -Destination (Join-Path $backupDir 'workbench.html') -Force

    [ordered]@{
        createdAt = (Get-Date).ToString('o')
        installRoot = $State.InstallRoot
        appRoot = $State.AppRoot
        version = $State.Version
        commit = $State.Commit
        electron = $State.Electron
        mainJs = $State.MainJs
        workbenchHtml = $State.WorkbenchHtml
        hadVibrancyBlock = $State.HasVibrancyBlock
        hadChthonicBlock = $State.HasChthonicBlock
        hadSubstrateCss = $State.HasSubstrateCss
    } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $backupDir 'metadata.json') -Encoding utf8

    return $backupDir
}

function Enable-Substrate {
    param([switch]$Quiet)

    if (-not (Test-Path -LiteralPath $RuntimePath)) {
        throw "Mica runtime not found: $RuntimePath"
    }
    if (-not (Test-Path -LiteralPath $CssPath)) {
        throw "Workbench substrate CSS not found: $CssPath"
    }

    $state = Get-SubstrateState
    $backupDir = New-SubstrateBackup -State $state
    $runtimeUri = ConvertTo-FileUri -Path $RuntimePath
    $cssUri = ConvertTo-FileUri -Path $CssPath

    $main = Get-Content -LiteralPath $state.MainJs -Raw
    $main = Remove-SubstrateBlocks -Text $main
    $block = @"
/* !! CHTHONIC-MICA-START !! */
process.env.CHTHONIC_MICA_MATERIAL = "$Material";
import("$runtimeUri").catch(err => console.error("[chthonic-mica] import failed:", err));
/* !! CHTHONIC-MICA-END !! */

"@
    Set-Content -LiteralPath $state.MainJs -Value ($block + $main) -NoNewline -Encoding utf8

    $html = Get-Content -LiteralPath $state.WorkbenchHtml -Raw
    $html = Remove-SubstrateCssLink -Html $html
    $cssLine = "`t`t<link rel=""stylesheet"" data-claude-design-substrate=""vibrancy-obsidian"" href=""$cssUri"">"
    $anchor = '<link rel="stylesheet" href="../../../workbench/workbench.desktop.main.css">'
    if ($html.Contains($anchor)) {
        $html = $html.Replace($anchor, "$anchor`r`n$cssLine")
    } else {
        $html = $html.Replace('</head>', "$cssLine`r`n`t</head>")
    }
    Set-Content -LiteralPath $state.WorkbenchHtml -Value $html -NoNewline -Encoding utf8

    if (-not $Quiet) {
        [pscustomobject]@{
            action = 'enabled'
            material = $Material
            backup = $backupDir
            appRoot = $state.AppRoot
            mainJs = $state.MainJs
            workbenchHtml = $state.WorkbenchHtml
        }
    }
}

function Disable-Substrate {
    $state = Get-SubstrateState
    $backupDir = New-SubstrateBackup -State $state

    $main = Get-Content -LiteralPath $state.MainJs -Raw
    $main = Remove-SubstrateBlocks -Text $main
    Set-Content -LiteralPath $state.MainJs -Value $main -NoNewline -Encoding utf8

    $html = Get-Content -LiteralPath $state.WorkbenchHtml -Raw
    $html = Remove-SubstrateCssLink -Html $html
    Set-Content -LiteralPath $state.WorkbenchHtml -Value $html -NoNewline -Encoding utf8

    [pscustomobject]@{
        action = 'disabled'
        backup = $backupDir
        appRoot = $state.AppRoot
        mainJs = $state.MainJs
        workbenchHtml = $state.WorkbenchHtml
    }
}

function Restore-LatestBackup {
    if (-not (Test-Path -LiteralPath $BackupRoot)) {
        throw "No backup root found: $BackupRoot"
    }

    $latest = Get-ChildItem -LiteralPath $BackupRoot -Directory |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 1
    if (-not $latest) {
        throw "No substrate backups found under: $BackupRoot"
    }

    $state = Get-SubstrateState
    Copy-Item -LiteralPath (Join-Path $latest.FullName 'main.js') -Destination $state.MainJs -Force
    Copy-Item -LiteralPath (Join-Path $latest.FullName 'workbench.html') -Destination $state.WorkbenchHtml -Force

    [pscustomobject]@{
        action = 'restored-latest-backup'
        restoredFrom = $latest.FullName
        appRoot = $state.AppRoot
        mainJs = $state.MainJs
        workbenchHtml = $state.WorkbenchHtml
    }
}

if ($Enable) {
    Enable-Substrate
} elseif ($Reapply) {
    Enable-Substrate
} elseif ($Disable) {
    Disable-Substrate
} elseif ($RestoreLatestBackup) {
    Restore-LatestBackup
} else {
    Get-SubstrateState
}
