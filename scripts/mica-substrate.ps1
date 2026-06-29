#!/usr/bin/env pwsh
# SID: CHTHONIC_MICA_SUBSTRATE_PS1_V1
# Purpose: Own the local VS Code Insiders Mica substrate without delegating
# color authority to Vibrancy Continued's broad themeCSS patch.
# Made by Claude. Continued by Codex.

[CmdletBinding()]
param(
    [Alias('Enable')]
    [switch]$Apply,

    [switch]$Disable,

    [Alias('Reapply')]
    [switch]$ReapplyLatest,

    [switch]$Status,

    [Alias('RestoreLatestBackup')]
    [switch]$Restore,

    [switch]$Verify,

    [string]$BackupPath,

    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA 'Programs\Microsoft VS Code Insiders'),
    [string]$Material = 'mica'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$RuntimePath = Join-Path $RepoRoot 'designs\chthonic-mica.cjs'
$CssPath = Join-Path $RepoRoot 'designs\vibrancy-obsidian.css'
$BackupRoot = Join-Path $RepoRoot 'CLAUDEBASE\hold\vscode-insiders-substrate\backups'
$ChthonicStart = '/* !! CHTHONIC-MICA-START !! */'
$ChthonicEnd = '/* !! CHTHONIC-MICA-END !! */'
$VibrancyStart = '/* !! VSCODE-VIBRANCY-START !! */'
$SubstrateCssMarker = 'data-claude-design-substrate="vibrancy-obsidian"'

function ConvertTo-FileUri {
    param([Parameter(Mandatory)][string]$Path)
    return ([System.Uri](Resolve-Path -LiteralPath $Path).ProviderPath).AbsoluteUri
}

function Get-OptionalProperty {
    param(
        $Object,
        [Parameter(Mandatory)][string]$Name
    )

    if ($null -eq $Object) {
        return $null
    }

    $property = $Object.PSObject.Properties[$Name]
    if ($property) {
        return $property.Value
    }

    return $null
}

function Get-FileSha256 {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
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
    $runtimeUri = if (Test-Path -LiteralPath $RuntimePath) { ConvertTo-FileUri -Path $RuntimePath } else { $null }
    $cssUri = if (Test-Path -LiteralPath $CssPath) { ConvertTo-FileUri -Path $CssPath } else { $null }
    $version = if ($package) { Get-OptionalProperty -Object $package -Name 'version' } else { 'unknown' }
    $commit = if ($product) { Get-OptionalProperty -Object $product -Name 'commit' } else { 'unknown' }
    $devDependencies = if ($package) { Get-OptionalProperty -Object $package -Name 'devDependencies' } else { $null }
    $electron = Get-OptionalProperty -Object $devDependencies -Name 'electron'
    if (-not $electron) { $electron = 'unknown' }
    $agentSdks = if ($product) { Get-OptionalProperty -Object $product -Name 'agentSdks' } else { $null }
    $claude = Get-OptionalProperty -Object $agentSdks -Name 'claude'
    $claudeAgentSdk = Get-OptionalProperty -Object $claude -Name 'version'
    if (-not $claudeAgentSdk) { $claudeAgentSdk = 'unknown' }
    $codex = Get-OptionalProperty -Object $agentSdks -Name 'codex'
    $codexAgentSdk = Get-OptionalProperty -Object $codex -Name 'version'
    if (-not $codexAgentSdk) { $codexAgentSdk = 'unknown' }
    $hasRuntimeUri = if ($runtimeUri) { $main.Contains($runtimeUri) } else { $false }
    $hasCssUri = if ($cssUri) { $html.Contains($cssUri) } else { $false }
    $latestBackup = Get-LatestBackup -StateCommit $commit
    $latestCleanBackup = Get-LatestBackup -StateCommit $commit -RequireClean
    $latestBackupPath = if ($latestBackup) { $latestBackup.FullName } else { $null }
    $latestCleanBackupPath = if ($latestCleanBackup) { $latestCleanBackup.FullName } else { $null }
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
        Version = $version
        Commit = $commit
        Electron = $electron
        ClaudeAgentSdk = $claudeAgentSdk
        CodexAgentSdk = $codexAgentSdk
        AgentSdks = $agentSdks
        MainJs = $mainJs
        WorkbenchHtml = $workbenchHtml
        RuntimePath = $RuntimePath
        CssPath = $CssPath
        RuntimeUri = $runtimeUri
        CssUri = $cssUri
        RuntimeHash = Get-FileSha256 -Path $RuntimePath
        CssHash = Get-FileSha256 -Path $CssPath
        MainJsHash = Get-FileSha256 -Path $mainJs
        WorkbenchHtmlHash = Get-FileSha256 -Path $workbenchHtml
        HasVibrancyBlock = $main.Contains($VibrancyStart)
        HasChthonicBlock = $main.Contains($ChthonicStart)
        ChthonicBlockCount = ([regex]::Matches($main, [regex]::Escape($ChthonicStart))).Count
        HasRuntimeUri = $hasRuntimeUri
        HasSubstrateCss = $html.Contains($SubstrateCssMarker)
        SubstrateCssLinkCount = ([regex]::Matches($html, [regex]::Escape($SubstrateCssMarker))).Count
        HasCssUri = $hasCssUri
        IsPatched = $main.Contains($ChthonicStart) -and $html.Contains($SubstrateCssMarker)
        IsClean = (-not $main.Contains($ChthonicStart)) -and (-not $main.Contains($VibrancyStart)) -and (-not $html.Contains($SubstrateCssMarker))
        LatestBackup = $latestBackupPath
        LatestCleanBackup = $latestCleanBackupPath
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
        mainJsHash = $State.MainJsHash
        workbenchHtmlHash = $State.WorkbenchHtmlHash
        hadVibrancyBlock = $State.HasVibrancyBlock
        hadChthonicBlock = $State.HasChthonicBlock
        hadSubstrateCss = $State.HasSubstrateCss
    } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $backupDir 'metadata.json') -Encoding utf8

    return $backupDir
}

function Get-BackupMetadata {
    param([Parameter(Mandatory)][string]$Directory)

    $metadataPath = Join-Path $Directory 'metadata.json'
    if (-not (Test-Path -LiteralPath $metadataPath)) {
        return $null
    }

    try {
        return Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Test-CleanBackupMetadata {
    param($Metadata)

    if ($null -eq $Metadata) {
        return $false
    }

    return (-not [bool](Get-OptionalProperty -Object $Metadata -Name 'hadVibrancyBlock')) -and
        (-not [bool](Get-OptionalProperty -Object $Metadata -Name 'hadChthonicBlock')) -and
        (-not [bool](Get-OptionalProperty -Object $Metadata -Name 'hadSubstrateCss'))
}

function Get-LatestBackup {
    param(
        [string]$StateCommit,
        [switch]$RequireClean
    )

    if (-not (Test-Path -LiteralPath $BackupRoot)) {
        return $null
    }

    $backups = Get-ChildItem -LiteralPath $BackupRoot -Directory |
        Sort-Object LastWriteTimeUtc -Descending

    foreach ($backup in $backups) {
        $metadata = Get-BackupMetadata -Directory $backup.FullName
        $metadataCommit = Get-OptionalProperty -Object $metadata -Name 'commit'
        if ($StateCommit -and $StateCommit -ne 'unknown' -and $metadataCommit -and $metadataCommit -ne $StateCommit) {
            continue
        }
        if ($RequireClean -and -not (Test-CleanBackupMetadata -Metadata $metadata)) {
            continue
        }
        return $backup
    }

    return $null
}

function Resolve-BackupPath {
    param([string]$Path)

    if ($Path) {
        $resolved = Resolve-Path -LiteralPath $Path -ErrorAction Stop
        return $resolved.ProviderPath
    }

    $state = Get-SubstrateState
    $latest = Get-LatestBackup -StateCommit $state.Commit
    if (-not $latest) {
        throw "No substrate backups found under: $BackupRoot"
    }

    return $latest.FullName
}

function Assert-BackupUsable {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        throw "Backup path is not a directory: $Path"
    }

    $mainBackup = Join-Path $Path 'main.js'
    $htmlBackup = Join-Path $Path 'workbench.html'
    if (-not (Test-Path -LiteralPath $mainBackup)) {
        throw "Backup is missing main.js: $mainBackup"
    }
    if (-not (Test-Path -LiteralPath $htmlBackup)) {
        throw "Backup is missing workbench.html: $htmlBackup"
    }
}

function Test-Substrate {
    $state = Get-SubstrateState
    $checks = @(
        [pscustomobject]@{ Name = 'runtime-file'; Ok = [bool](Test-Path -LiteralPath $RuntimePath); Detail = $RuntimePath },
        [pscustomobject]@{ Name = 'css-file'; Ok = [bool](Test-Path -LiteralPath $CssPath); Detail = $CssPath },
        [pscustomobject]@{ Name = 'chthonic-main-block'; Ok = [bool]$state.HasChthonicBlock; Detail = $state.MainJs },
        [pscustomobject]@{ Name = 'single-chthonic-main-block'; Ok = ($state.ChthonicBlockCount -eq 1); Detail = "count=$($state.ChthonicBlockCount)" },
        [pscustomobject]@{ Name = 'no-vibrancy-block'; Ok = (-not $state.HasVibrancyBlock); Detail = $state.MainJs },
        [pscustomobject]@{ Name = 'runtime-uri-current'; Ok = [bool]$state.HasRuntimeUri; Detail = $state.RuntimeUri },
        [pscustomobject]@{ Name = 'workbench-css-link'; Ok = [bool]$state.HasSubstrateCss; Detail = $state.WorkbenchHtml },
        [pscustomobject]@{ Name = 'single-workbench-css-link'; Ok = ($state.SubstrateCssLinkCount -eq 1); Detail = "count=$($state.SubstrateCssLinkCount)" },
        [pscustomobject]@{ Name = 'css-uri-current'; Ok = [bool]$state.HasCssUri; Detail = $state.CssUri }
    )
    $failed = @($checks | Where-Object { -not $_.Ok })

    [pscustomobject]@{
        Ok = ($failed.Count -eq 0)
        FailedCount = $failed.Count
        Version = $state.Version
        Commit = $state.Commit
        Electron = $state.Electron
        AppRoot = $state.AppRoot
        MainJs = $state.MainJs
        WorkbenchHtml = $state.WorkbenchHtml
        Checks = $checks
    }
}

function Verify-Substrate {
    $report = Test-Substrate
    $report
    if (-not $report.Ok) {
        $failed = ($report.Checks | Where-Object { -not $_.Ok } | ForEach-Object { $_.Name }) -join ', '
        throw "Substrate verification failed: $failed"
    }
}

function Apply-Substrate {
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
$ChthonicStart
process.env.CHTHONIC_MICA_MATERIAL = "$Material";
import("$runtimeUri").catch(err => console.error("[chthonic-mica] import failed:", err));
$ChthonicEnd

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

    $result = [pscustomobject]@{
        action = 'applied'
        material = $Material
        backup = $backupDir
        appRoot = $state.AppRoot
        mainJs = $state.MainJs
        workbenchHtml = $state.WorkbenchHtml
    }

    if ($Quiet) {
        return $result
    }

    $result
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

function Restore-Substrate {
    param([string]$Path)

    $restorePath = Resolve-BackupPath -Path $Path
    Assert-BackupUsable -Path $restorePath
    $state = Get-SubstrateState
    $safetyBackup = New-SubstrateBackup -State $state

    Copy-Item -LiteralPath (Join-Path $restorePath 'main.js') -Destination $state.MainJs -Force
    Copy-Item -LiteralPath (Join-Path $restorePath 'workbench.html') -Destination $state.WorkbenchHtml -Force

    [pscustomobject]@{
        action = 'restored'
        restoredFrom = $restorePath
        safetyBackup = $safetyBackup
        appRoot = $state.AppRoot
        mainJs = $state.MainJs
        workbenchHtml = $state.WorkbenchHtml
    }
}

function Reapply-LatestSubstrate {
    $state = Get-SubstrateState
    $clean = Get-LatestBackup -StateCommit $state.Commit -RequireClean
    $restoredFrom = $null
    $safetyBackup = $null

    if ($clean) {
        Assert-BackupUsable -Path $clean.FullName
        $safetyBackup = New-SubstrateBackup -State $state
        Copy-Item -LiteralPath (Join-Path $clean.FullName 'main.js') -Destination $state.MainJs -Force
        Copy-Item -LiteralPath (Join-Path $clean.FullName 'workbench.html') -Destination $state.WorkbenchHtml -Force
        $restoredFrom = $clean.FullName
    }

    $applyResult = Apply-Substrate -Quiet
    [pscustomobject]@{
        action = 'reapplied-latest'
        restoredFrom = $restoredFrom
        safetyBackup = $safetyBackup
        applyBackup = $applyResult.backup
        appRoot = $state.AppRoot
        mainJs = $state.MainJs
        workbenchHtml = $state.WorkbenchHtml
    }
}

$actions = @(@($Apply, $Disable, $ReapplyLatest, $Status, $Restore, $Verify) | Where-Object { $_.IsPresent })
if ($actions.Count -gt 1) {
    throw "Choose exactly one action: -Status, -Apply, -Verify, -Restore, -ReapplyLatest, or -Disable."
}
if ($BackupPath -and -not $Restore) {
    throw "-BackupPath is only valid with -Restore."
}

if ($Apply) {
    Apply-Substrate
} elseif ($ReapplyLatest) {
    Reapply-LatestSubstrate
} elseif ($Disable) {
    Disable-Substrate
} elseif ($Restore) {
    Restore-Substrate -Path $BackupPath
} elseif ($Verify) {
    Verify-Substrate
} else {
    Get-SubstrateState
}
