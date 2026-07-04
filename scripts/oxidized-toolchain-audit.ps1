#!/usr/bin/env pwsh
# SID: CHTHONIC_OXIDIZED_TOOLCHAIN_AUDIT_PS1_V1
# scripts/oxidized-toolchain-audit.ps1
#
# Non-mutating audit for curated oxidized tool managers:
#   bun, uv, rvw/rv Ruby, rv-r R packages, goup-rs, zv, brush, rustup
#
# This script does not update, install, remove, prune, or self-update anything.
# It reports current versions, latest known stable versions where queryable,
# and the exact commands that would be mutating if the user approves later.
#
# Tool boundary:
#   Python: uv
#   Ruby:   rvw/rv run ("rv r --no-install ...")
#   R lang: rv-r wrapper for A2-ai/rv; root rv.lock belongs to this lane
#   Zig:    zv
#   Go:     goup
#   Shell:  brush
#
# Made by Claude. Corrected by Codex.

[CmdletBinding()]
param(
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

function Get-CommandPath {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $cmd) { return $null }
    if ($cmd.Path) { return $cmd.Path }
    return $cmd.Definition
}

function Invoke-Capture {
    param(
        [Parameter(Mandatory)][string]$Command,
        [string[]]$Args = @()
    )
    try {
        $output = & $Command @Args 2>&1
        return @{
            ok = ($LASTEXITCODE -eq 0)
            exit = $LASTEXITCODE
            text = (($output | Out-String).Trim())
        }
    } catch {
        return @{
            ok = $false
            exit = $null
            text = $_.Exception.Message
        }
    }
}

function Get-GitHubLatest {
    param([string]$Repo)
    try {
        $r = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" -Headers @{ 'User-Agent' = 'chthonic-oxidized-toolchain-audit' }
        return @{
            tag = [string]$r.tag_name
            prerelease = [bool]$r.prerelease
            published = [string]$r.published_at
            url = [string]$r.html_url
        }
    } catch {
        return @{ error = $_.Exception.Message }
    }
}

function Get-CratesLatest {
    param([string]$Crate)
    try {
        $r = Invoke-RestMethod -Uri "https://crates.io/api/v1/crates/$Crate" -Headers @{ 'User-Agent' = 'chthonic-oxidized-toolchain-audit' }
        return @{
            max_stable = [string]$r.crate.max_stable_version
            newest = [string]$r.crate.newest_version
            repository = [string]$r.crate.repository
        }
    } catch {
        return @{ error = $_.Exception.Message }
    }
}

function Get-GoLatest {
    try {
        $r = Invoke-RestMethod -Uri 'https://go.dev/dl/?mode=json' -Headers @{ 'User-Agent' = 'chthonic-oxidized-toolchain-audit' }
        $stable = $r | Where-Object { $_.stable } | Select-Object -First 1
        return @{ version = [string]$stable.version; stable = [bool]$stable.stable }
    } catch {
        return @{ error = $_.Exception.Message }
    }
}

function Get-ZigLatest {
    try {
        $z = Invoke-RestMethod -Uri 'https://ziglang.org/download/index.json' -Headers @{ 'User-Agent' = 'chthonic-oxidized-toolchain-audit' }
        $stable = $z.PSObject.Properties.Name |
            Where-Object { $_ -match '^\d+\.\d+\.\d+$' } |
            Sort-Object { [version]$_ } -Descending |
            Select-Object -First 1
        return @{ version = [string]$stable }
    } catch {
        return @{ error = $_.Exception.Message }
    }
}

$rvCommand = Get-CommandPath 'rvw'
if (-not $rvCommand) { $rvCommand = Get-CommandPath 'rv' }

$report = [ordered]@{
    generated = (Get-Date).ToUniversalTime().ToString('o')
    non_mutating = $true
    notes = @(
        'Root rv.lock is R language package state for A2-ai/rv, not Ruby rv manager state.',
        'PowerShell rv may be an alias; scripts should call rvw on Windows and use rv semantics.',
        'Installed goup.exe is thinkgos/goup-rs; lpar/goup is a separate Go updater project.',
        'No mutating updater was run by this audit.'
    )
    tools = [ordered]@{}
    suggested_mutating_commands = [ordered]@{}
}

$bunPath = Get-CommandPath 'bun'
$uvPath = Get-CommandPath 'uv'
$goupPath = Get-CommandPath 'goup'
$zvPath = Get-CommandPath 'zv'
$zigPath = Get-CommandPath 'zig'
$rustupPath = Get-CommandPath 'rustup'
$rscriptPath = Get-CommandPath 'Rscript'
$rvRScript = Join-Path $PSScriptRoot 'rv-r.ps1'
$brushPath = Get-CommandPath 'brush'

$report.tools.bun = @{
    path = $bunPath
    current = if ($bunPath) { (Invoke-Capture $bunPath @('--version')).text } else { 'missing' }
    latest = Get-GitHubLatest 'oven-sh/bun'
    dry_run = 'none advertised by bun upgrade --help'
}
$report.suggested_mutating_commands.bun = 'bun upgrade'

$report.tools.uv = @{
    path = $uvPath
    current = if ($uvPath) { (Invoke-Capture $uvPath @('--version')).text } else { 'missing' }
    latest = Get-GitHubLatest 'astral-sh/uv'
    dry_run = if ($uvPath) { (Invoke-Capture $uvPath @('self', 'update', '--dry-run')).text } else { 'missing' }
}
$report.suggested_mutating_commands.uv = 'uv self update'

$report.tools.ruby_rv = @{
    path = $rvCommand
    current_manager = if ($rvCommand) { (Invoke-Capture $rvCommand @('--version')).text } else { 'missing' }
    current_ruby = if ($rvCommand) { (Invoke-Capture $rvCommand @('r', '--no-install', 'ruby', '--version')).text } else { 'missing' }
    latest_manager = Get-GitHubLatest 'spinel-coop/rv'
    pin = if (Test-Path '.ruby-version') { (Get-Content -LiteralPath '.ruby-version' -Raw).Trim() } else { 'missing' }
    root_rv_lock_lane = if (Test-Path 'rv.lock') { 'R language, not Ruby' } else { 'absent' }
}
$report.suggested_mutating_commands.ruby_rv = 'rvw self update; rvw ruby install <version>; rvw ruby pin <version>'

$report.tools.r_rv = @{
    wrapper = if (Test-Path $rvRScript) { $rvRScript } else { 'missing' }
    current_manager = if (Test-Path $rvRScript) { (Invoke-Capture 'pwsh' @('-NoProfile', '-File', $rvRScript, '--version')).text } else { 'missing' }
    latest_manager = Get-GitHubLatest 'A2-ai/rv'
    root_rv_lock_lane = if (Test-Path 'rv.lock') { 'R language package lockfile' } else { 'missing' }
    root_rv_lock_r_version = if (Test-Path 'rv.lock') {
        $line = Select-String -LiteralPath 'rv.lock' -Pattern '^r_version\s*=' | Select-Object -First 1
        if ($line -and $line.Line -match '"([^"]+)"') { $matches[1] } else { 'unknown' }
    } else { 'missing' }
    rscript_path = $rscriptPath
    rscript_version = if ($rscriptPath) { (Invoke-Capture $rscriptPath @('--version')).text } else { 'missing' }
    dry_run_plan = if (Test-Path $rvRScript) { (Invoke-Capture 'pwsh' @('-NoProfile', '-File', $rvRScript, 'plan')).text } else { 'missing' }
}
$report.suggested_mutating_commands.r_rv = 'Install/update A2-ai/rv only in isolated .r-rv lane; then use scripts\rv-r.ps1 plan before scripts\rv-r.ps1 sync'

$report.tools.goup = @{
    path = $goupPath
    installed_upstream = 'thinkgos/goup-rs'
    different_project_not_installed = Get-GitHubLatest 'lpar/goup'
    current = if ($goupPath) { (Invoke-Capture $goupPath @('--version')).text } else { 'missing' }
    installed = if ($goupPath) { (Invoke-Capture $goupPath @('list')).text } else { 'missing' }
    latest_manager = Get-GitHubLatest 'thinkgos/goup-rs'
    latest_go = Get-GoLatest
    dry_run = 'none advertised by goup self update --help'
}
$report.suggested_mutating_commands.goup = 'goup self update; goup install stable; goup default <version>'

$report.tools.zv = @{
    path = $zvPath
    current = if ($zvPath) { (Invoke-Capture $zvPath @('--version')).text } else { 'missing' }
    installed = if ($zvPath) { (Invoke-Capture $zvPath @('list')).text } else { 'missing' }
    latest_manager = Get-CratesLatest 'zv'
    latest_zig = Get-ZigLatest
    active_zig = if ($zigPath) { (Invoke-Capture $zigPath @('version')).text } else { 'missing' }
    dry_run = 'none advertised by zv update/sync/install --help'
}
$report.suggested_mutating_commands.zv = 'zv update; zv sync; zv install stable --zls; zv use stable --zls'

$report.tools.brush = @{
    path = $brushPath
    current = if ($brushPath) { (Invoke-Capture $brushPath @('--version')).text } else { 'missing' }
    latest = Get-GitHubLatest 'reubeno/brush'
    dry_run = 'version/help only; shell execution is explicit and separate'
}
$report.suggested_mutating_commands.brush = 'cargo install --locked brush-shell --force (or release asset install after review)'

$report.tools.rustup = @{
    path = $rustupPath
    current = if ($rustupPath) { (Invoke-Capture $rustupPath @('--version')).text } else { 'missing' }
    check = if ($rustupPath) { (Invoke-Capture $rustupPath @('check')).text } else { 'missing' }
    dry_run = 'rustup check only; rustup update is mutating'
}
$report.suggested_mutating_commands.rustup = 'rustup update'

if ($Json) {
    $report | ConvertTo-Json -Depth 8
    exit 0
}

Write-Host "# Oxidized Toolchain Audit"
Write-Host "Generated: $($report.generated)"
Write-Host ""
foreach ($name in $report.tools.Keys) {
    Write-Host "## $name"
    ($report.tools[$name] | ConvertTo-Json -Depth 8)
    Write-Host ""
}
Write-Host "## Suggested Mutating Commands (not run)"
foreach ($name in $report.suggested_mutating_commands.Keys) {
    Write-Host "${name}: $($report.suggested_mutating_commands[$name])"
}
