#!/usr/bin/env pwsh
# SID: CHTHONIC_CLAUDE_DESIGN_QUARANTINE_PS1_V1
# Purpose: Quarantine stale installed Claude Design edges that collide with
# The Extreme Haute Couture Movement 1 substrate lane.

[CmdletBinding()]
param(
    [switch]$Apply,
    [switch]$Verify,
    [switch]$Status,

    [string]$ExtensionRoot = (Join-Path $env:USERPROFILE '.vscode-insiders\extensions\claude-design.claude-design-0.1.0'),
    [string]$ReportPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $ReportPath) {
    $ReportPath = Join-Path $RepoRoot 'manifest\claude-design-quarantine.json'
}

$BackupRoot = Join-Path $RepoRoot 'CLAUDEBASE\hold\claude-design-quarantine\backups'
$PatchNeedle = 'vscode15.commands.registerCommand("claudeDesign.enableSubstrate", async () => {'
$PatchReplacement = @'
vscode15.commands.registerCommand("claudeDesign.runeAction", async () => {
    return vscode15.commands.executeCommand("claudeDesign.openBestiary");
  }), vscode15.commands.registerCommand("claudeDesign.enableSubstrate", async () => {
'@

function Get-QuarantineState {
    param([Parameter(Mandatory)][string]$Root)

    $packageJsonPath = Join-Path $Root 'package.json'
    $distPath = Join-Path $Root 'dist\extension.js'
    $installed = Test-Path -LiteralPath $Root
    $package = $null
    $dist = $null

    if ($installed -and (Test-Path -LiteralPath $packageJsonPath)) {
        $package = Get-Content -LiteralPath $packageJsonPath -Raw | ConvertFrom-Json
    }

    if ($installed -and (Test-Path -LiteralPath $distPath)) {
        $dist = Get-Content -LiteralPath $distPath -Raw
    }

    $name = if ($package) { $package.name } else { $null }
    $publisher = if ($package) { $package.publisher } else { $null }
    $version = if ($package) { $package.version } else { $null }
    $expectedPackage = $installed -and $name -eq 'claude-design' -and $publisher -eq 'claude-design' -and $version -eq '0.1.0'
    $hasRuneAssignment = [bool]($dist -and $dist.Contains('claudeDesign.runeAction'))
    $hasRuneRegistration = [bool]($dist -and $dist.Contains('registerCommand("claudeDesign.runeAction"'))
    $hasBestiaryRegistration = [bool]($dist -and $dist.Contains('registerCommand("claudeDesign.openBestiary"'))
    $hasPatchNeedle = [bool]($dist -and $dist.Contains($PatchNeedle))

    $ok = -not $installed -or (
        $expectedPackage -and
        (-not $hasRuneAssignment -or ($hasRuneRegistration -and $hasBestiaryRegistration))
    )

    return [pscustomobject]@{
        Schema = 'chthonic/claude-design-quarantine/v1'
        GeneratedAt = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
        ExtensionRoot = $Root
        Installed = $installed
        PackageJson = $packageJsonPath
        Dist = $distPath
        Name = $name
        Publisher = $publisher
        Version = $version
        ExpectedPackage = $expectedPackage
        HasRuneAssignment = $hasRuneAssignment
        HasRuneRegistration = $hasRuneRegistration
        HasBestiaryRegistration = $hasBestiaryRegistration
        HasPatchNeedle = $hasPatchNeedle
        Ok = $ok
    }
}

function Write-QuarantineReport {
    param(
        [Parameter(Mandatory)]$State,
        [string]$BackupPath,
        [string]$Action
    )

    $report = [pscustomobject]@{
        Schema = $State.Schema
        GeneratedAt = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
        Action = $Action
        BackupPath = $BackupPath
        State = $State
    }

    $reportDir = Split-Path -Parent $ReportPath
    if (-not (Test-Path -LiteralPath $reportDir)) {
        New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
    }
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
}

if (-not $Apply -and -not $Verify -and -not $Status) {
    $Status = $true
}

$state = Get-QuarantineState -Root $ExtensionRoot
$backupPath = $null
$action = 'status'

if ($Apply) {
    if (-not $state.Installed) {
        $action = 'not-installed'
    } elseif (-not $state.ExpectedPackage) {
        throw "Refusing to patch unexpected extension at $ExtensionRoot (name=$($state.Name), publisher=$($state.Publisher), version=$($state.Version))."
    } elseif ($state.HasRuneRegistration) {
        $action = 'already-patched'
    } elseif (-not $state.HasPatchNeedle) {
        throw "Patch anchor not found in installed Claude Design bundle: $($state.Dist)"
    } else {
        $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
        $backupDir = Join-Path $BackupRoot $stamp
        New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

        $backupPath = Join-Path $backupDir 'extension.js'
        Copy-Item -LiteralPath $state.Dist -Destination $backupPath -Force

        $dist = Get-Content -LiteralPath $state.Dist -Raw
        $patched = $dist.Replace($PatchNeedle, $PatchReplacement.TrimEnd())
        Set-Content -LiteralPath $state.Dist -Value $patched -Encoding UTF8
        $action = 'patched'
        $state = Get-QuarantineState -Root $ExtensionRoot
    }

    Write-QuarantineReport -State $state -BackupPath $backupPath -Action $action
}

$state | ConvertTo-Json -Depth 8

if ($Verify -and -not $state.Ok) {
    exit 1
}
