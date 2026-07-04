#!/usr/bin/env pwsh
# SID: CHTHONIC_SOURCE_TEMP_PS1_V1
# scripts/chthonic-source-temp.ps1
#
# Local source-code study lane for upstream contenders.
# Keeps cloned/read-only source outside the repo and Git index.
# Durable notes belong in CLAUDEBASE; volatile source belongs in %TEMP%.
#
# Made by Claude. Corrected by Codex.

[CmdletBinding()]
param(
    [switch]$Init,
    [switch]$Status,
    [string]$CloneUrl,
    [string]$Name
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-SourceTempRoot {
    if ($env:CHTHONIC_TEMP_SOURCE_CODE) {
        return $env:CHTHONIC_TEMP_SOURCE_CODE
    }
    return (Join-Path $env:TEMP 'chthonic-source-code')
}

function ConvertTo-SafeName {
    param([string]$Value)
    if (-not $Value) { return $null }
    $leaf = $Value.TrimEnd('/') -replace '^.*[/:]', ''
    $leaf = $leaf -replace '\.git$', ''
    $leaf = $leaf -replace '[^A-Za-z0-9._-]+', '-'
    $leaf = $leaf.Trim('-')
    if (-not $leaf) { return $null }
    return $leaf
}

function Write-LaneReadme {
    param([string]$Root)
    $readme = Join-Path $Root 'README.md'
    if (Test-Path -LiteralPath $readme) { return }

    $content = @'
# Chthonic Temp Source Code Lane

This directory is for volatile upstream source-code studies.

Rules:

- Source checkouts live here, not in `chthonic-archive`.
- Do not commit this directory.
- Clone shallow unless a full history is explicitly needed.
- Durable notes, comparisons, and harvested patterns go to `CLAUDEBASE/harbor/`.
- The source is evidence, not authority.

Suggested variables:

- `CHTHONIC_TEMP_SOURCE_CODE`: absolute path to this directory.
- `CHTHONIC_SOURCE_STUDY_ROOT`: optional alias for tools that prefer a semantic name.
'@
    Set-Content -LiteralPath $readme -Value $content -Encoding UTF8
}

function Invoke-Init {
    param([string]$Root)
    New-Item -ItemType Directory -Path $Root -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $Root '_incoming') -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $Root '_notes') -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $Root '_archives') -Force | Out-Null
    Write-LaneReadme -Root $Root
}

function Invoke-Status {
    param([string]$Root)
    $repos = @()
    if (Test-Path -LiteralPath $Root) {
        $repos = Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch '^_' } |
            Select-Object -ExpandProperty Name
    }

    [pscustomobject]@{
        Root = $Root
        Exists = (Test-Path -LiteralPath $Root)
        EnvName = 'CHTHONIC_TEMP_SOURCE_CODE'
        EnvValue = $env:CHTHONIC_TEMP_SOURCE_CODE
        RepoCount = @($repos).Count
        Repos = @($repos)
    }
}

function Invoke-Clone {
    param(
        [string]$Root,
        [string]$Url,
        [string]$RequestedName
    )

    if (-not $Url) { throw '-CloneUrl requires a URL.' }
    Invoke-Init -Root $Root

    $safeName = ConvertTo-SafeName -Value $RequestedName
    if (-not $safeName) { $safeName = ConvertTo-SafeName -Value $Url }
    if (-not $safeName) { throw 'Could not derive a safe checkout name.' }

    $dest = Join-Path $Root $safeName
    if (Test-Path -LiteralPath $dest) {
        throw "Destination already exists: $dest"
    }

    git clone --depth 1 -- $Url $dest
    if ($LASTEXITCODE -ne 0) { throw "git clone failed with exit code $LASTEXITCODE" }

    [pscustomobject]@{
        Action = 'cloned'
        Url = $Url
        Destination = $dest
    }
}

$root = Resolve-SourceTempRoot

if ($CloneUrl) {
    Invoke-Clone -Root $root -Url $CloneUrl -RequestedName $Name
    exit 0
}

if ($Init) {
    Invoke-Init -Root $root
}

if ($Status -or $Init -or (-not $CloneUrl)) {
    Invoke-Status -Root $root
}
