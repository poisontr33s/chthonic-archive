#!/usr/bin/env pwsh

# Siphon selected repo files into dumpster-dive for local iteration.
#
# - Deterministic, explicit, repo-local.
# - Does not modify git state.
# - Copies a small, curated set of "interesting" files by default.

[CmdletBinding()]
param(
    # Source root (defaults to repo root).
    [string]$SourceRoot,

    # Destination root (defaults to dumpster-dive intake).
    [string]$DestRoot,

    # Repo-relative paths to siphon. If omitted, a small default set is used.
    [string[]]$Paths,

    # Optional glob patterns (repo-relative) to siphon (applied when -Paths is not provided).
    [string[]]$IncludeGlobs = @(
        '.github/instructions/*.instructions.md',
        '.github/tools/*.ps1',
        'scripts/*.ps1',
        '.vscode/settings.json',
        'Cargo.toml',
        'build.rs',
        'src/main.rs'
    ),

    # Exclude glob patterns.
    [string[]]$ExcludeGlobs = @(
        'dumpster-dive/**',
        'target/**',
        'build/**',
        '**/__pycache__/**'
    )
)

$ErrorActionPreference = 'Stop'

function Get-RepoRoot {
    $gitCandidates = @(
        "$env:ProgramFiles\Git\cmd\git.exe",
        "$env:ProgramFiles\Git\bin\git.exe",
        "$env:ProgramFiles(x86)\Git\cmd\git.exe",
        "$env:LocalAppData\Programs\Git\cmd\git.exe"
    ) | Where-Object { $_ -and (Test-Path $_) }

    $git = $null
    if ($gitCandidates.Count -gt 0) { $git = $gitCandidates[0] }

    if ($git) {
        try {
            $root = (& $git rev-parse --show-toplevel).Trim()
            if ($root) { return $root }
        }
        catch {
            # fall through
        }
    }

    # Fallback: assume script is in repo/scripts.
    return (Split-Path -Parent $PSScriptRoot)
}

function Convert-GlobToRegex {
    param([Parameter(Mandatory = $true)][string]$Glob)

    $g = $Glob.Trim()
    if (-not $g) { return $null }
    $g = $g -replace '\\', '/'

    $rx = [regex]::Escape($g)
    $rx = $rx -replace '\\\*\\\*', '.*'
    $rx = $rx -replace '\\\*', '[^/]*'
    $rx = $rx -replace '\\\?', '.'

    return "^$rx$"
}

$repoRoot = if ($SourceRoot) { [System.IO.Path]::GetFullPath($SourceRoot) } else { Get-RepoRoot }

$destBase = if ($DestRoot) {
    [System.IO.Path]::GetFullPath($DestRoot)
} else {
    Join-Path $repoRoot 'dumpster-dive\intake\overnight-siphon'
}

$stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$destRootFull = Join-Path $destBase $stamp
$null = New-Item -ItemType Directory -Force -Path $destRootFull

$excludeRegexes = @(
    foreach ($g in $ExcludeGlobs) {
        $r = Convert-GlobToRegex -Glob $g
        if ($r) { $r }
    }
)

function Is-Excluded([string]$rel) {
    foreach ($rx in $excludeRegexes) {
        if ($rel -match $rx) { return $true }
    }
    return $false
}

$selected = New-Object System.Collections.Generic.List[string]

if ($Paths -and $Paths.Count -gt 0) {
    foreach ($p in $Paths) {
        if (-not $p) { continue }
        $rel = ($p -replace '\\', '/').TrimStart('/')
        if (-not (Is-Excluded $rel)) {
            $selected.Add($rel)
        }
    }
} else {
    $includeRegexes = @(
        foreach ($g in $IncludeGlobs) {
            $r = Convert-GlobToRegex -Glob $g
            if ($r) { $r }
        }
    )

    # Enumerate repo files once, then match via regex for determinism and speed.
    Get-ChildItem -LiteralPath $repoRoot -Recurse -File -ErrorAction SilentlyContinue |
        ForEach-Object {
            $full = $_.FullName
            $rel = $full.Substring($repoRoot.Length).TrimStart('\','/') -replace '\\', '/'
            if (-not $rel) { return }
            if (Is-Excluded $rel) { return }

            foreach ($rx in $includeRegexes) {
                if ($rel -match $rx) {
                    $selected.Add($rel)
                    break
                }
            }
        }
}

$selected = @($selected | Select-Object -Unique | Sort-Object)

$manifest = @()
foreach ($rel in $selected) {
    $src = Join-Path $repoRoot ($rel -replace '/', '\')
    if (-not (Test-Path $src)) { continue }

    $dst = Join-Path $destRootFull ($rel -replace '/', '\')
    $dstDir = Split-Path -Parent $dst
    $null = New-Item -ItemType Directory -Force -Path $dstDir

    Copy-Item -LiteralPath $src -Destination $dst -Force

    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $src).Hash
    $manifest += [pscustomobject]@{
        relPath = $rel
        sha256 = $hash
        length = (Get-Item -LiteralPath $src).Length
    }
}

$manifestPath = Join-Path $destRootFull 'manifest.json'
$manifest | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 -LiteralPath $manifestPath

Write-Host "Siphoned files: $($manifest.Count)" -ForegroundColor Green
Write-Host "Dest: $destRootFull" -ForegroundColor DarkGray
Write-Host "Manifest: $manifestPath" -ForegroundColor DarkGray
