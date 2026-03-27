#!/usr/bin/env pwsh
# @SID: SCRIPT_CHECK_SOLANA_VERSION_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: check-solana-version.ps1
# ║ Module: Solana/Agave governance version gate
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: GOVERNANCE
# ║ Semantic ID: SCRIPT_CHECK_SOLANA_VERSION_V1
# ║ Purpose: Enforce max-version-drift policy for local Solana CLI
# ║ Exports: (none)
# ║ Flags/Modes: -MaxMinorBehind -Json -CliCommand
# ║ Cross-References: scripts/chthonic.ps1
# ╚════════════════════════════════════════════════════════════════════════════

param(
    [int]$MaxMinorBehind = 2,
    [string]$CliCommand = "solana",
    [switch]$Json
)

$ErrorActionPreference = "Stop"

function Parse-SemVer {
    param([string]$Text)
    if (-not $Text) { return $null }
    if ($Text -match "(\d+)\.(\d+)\.(\d+)") {
        return [version]::new([int]$Matches[1], [int]$Matches[2], [int]$Matches[3])
    }
    return $null
}

function Get-LocalSolanaVersion {
    param([string]$CommandName)
    try {
        $raw = & $CommandName --version 2>$null
    } catch {
        return $null
    }
    $line = ($raw | Select-Object -First 1)
    if (-not $line) { return $null }
    return Parse-SemVer $line
}

function Get-RemoteRelease {
    param([string]$Repo)
    $url = "https://api.github.com/repos/$Repo/releases/latest"
    try {
        $release = Invoke-RestMethod -Uri $url -Headers @{ "User-Agent" = "chthonic-solana-governor" } -Method Get
    } catch {
        return $null
    }
    if (-not $release -or -not $release.tag_name) { return $null }
    $tag = "$($release.tag_name)".Trim()
    $ver = Parse-SemVer $tag.TrimStart("v")
    if (-not $ver) { return $null }
    return [pscustomobject]@{
        repo = $Repo
        tag = $tag
        version = $ver
        url = "$($release.html_url)"
        published_at = "$($release.published_at)"
    }
}

function Compare-Drift {
    param(
        [version]$Local,
        [version]$Remote,
        [int]$MaxBehind
    )
    if ($Remote.Major -gt $Local.Major) {
        return [pscustomobject]@{
            ok = $false
            reason = "major-behind"
            minor_diff = [int]::MaxValue
        }
    }
    if ($Remote.Major -lt $Local.Major) {
        return [pscustomobject]@{
            ok = $true
            reason = "local-ahead-major"
            minor_diff = -1
        }
    }

    $minorDiff = $Remote.Minor - $Local.Minor
    if ($minorDiff -gt $MaxBehind) {
        return [pscustomobject]@{
            ok = $false
            reason = "minor-drift-exceeded"
            minor_diff = $minorDiff
        }
    }

    return [pscustomobject]@{
        ok = $true
        reason = if ($minorDiff -le 0) { "up-to-date-or-ahead" } else { "within-policy-window" }
        minor_diff = $minorDiff
    }
}

$repos = @(
    "anza-xyz/agave",
    "solana-labs/solana"
)

$localVersion = Get-LocalSolanaVersion -CommandName $CliCommand
if (-not $localVersion) {
    $msg = "Solana CLI not found on PATH (command: $CliCommand)."
    if ($Json) {
        [pscustomobject]@{
            ok = $false
            error = "missing-local-cli"
            message = $msg
        } | ConvertTo-Json -Depth 4
    } else {
        Write-Error $msg
    }
    exit 2
}

$remote = $null
foreach ($repo in $repos) {
    $candidate = Get-RemoteRelease -Repo $repo
    if ($candidate) {
        $remote = $candidate
        break
    }
}

if (-not $remote) {
    $msg = "Unable to query remote release from GitHub for repos: $($repos -join ', ')."
    if ($Json) {
        [pscustomobject]@{
            ok = $false
            error = "remote-query-failed"
            message = $msg
            local_version = "$localVersion"
        } | ConvertTo-Json -Depth 4
    } else {
        Write-Warning $msg
        Write-Host "Local Solana CLI: $localVersion" -ForegroundColor Yellow
    }
    exit 3
}

$drift = Compare-Drift -Local $localVersion -Remote $remote.version -MaxBehind $MaxMinorBehind
$result = [pscustomobject]@{
    ok = $drift.ok
    policy = [pscustomobject]@{
        max_minor_behind = $MaxMinorBehind
    }
    local_version = "$localVersion"
    remote = [pscustomobject]@{
        repo = $remote.repo
        tag = $remote.tag
        version = "$($remote.version)"
        url = $remote.url
        published_at = $remote.published_at
    }
    drift = [pscustomobject]@{
        reason = $drift.reason
        minor_diff = $drift.minor_diff
    }
}

if ($Json) {
    $result | ConvertTo-Json -Depth 5
} else {
    if ($result.ok) {
        Write-Host "Solana Governance: OK" -ForegroundColor Green
        Write-Host "  local=$($result.local_version)" -ForegroundColor DarkGray
        Write-Host "  remote=$($result.remote.version) ($($result.remote.repo))" -ForegroundColor DarkGray
        Write-Host "  drift.reason=$($result.drift.reason), drift.minor_diff=$($result.drift.minor_diff)" -ForegroundColor DarkGray
    } else {
        Write-Error "CRITICAL: Solana CLI version drift exceeded policy."
        Write-Host "  local=$($result.local_version)" -ForegroundColor Red
        Write-Host "  remote=$($result.remote.version) ($($result.remote.repo))" -ForegroundColor Red
        Write-Host "  drift.reason=$($result.drift.reason), drift.minor_diff=$($result.drift.minor_diff), max=$MaxMinorBehind" -ForegroundColor Red
        Write-Host "  release=$($result.remote.url)" -ForegroundColor DarkGray
    }
}

if ($result.ok) {
    exit 0
}
exit 1

