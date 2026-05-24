#!/usr/bin/env pwsh
# @SID: SCRIPT_ENSURE_PRECOMMIT_HOOK_V1
# Ensure the active Git pre-commit hook runs the local staged CI gate.

param(
    [switch]$Force,
    [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"

function Invoke-GitValue {
    param([string[]]$GitArgs)
    $value = & git @GitArgs 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $null
    }
    return ($value | Select-Object -First 1)
}

function Resolve-RepoPath {
    param([string]$Path)
    if ([System.IO.Path]::IsPathRooted($Path)) {
        return $Path
    }
    return Join-Path $repoRoot $Path
}

$repoRoot = Invoke-GitValue @("rev-parse", "--show-toplevel")
if (-not $repoRoot) {
    Write-Error "[hooks:precommit] not inside a git repository"
    exit 1
}

$source = Join-Path $repoRoot "scripts" "pre-commit-hook.sh"
if (-not (Test-Path $source)) {
    Write-Error "[hooks:precommit] missing source hook: $source"
    exit 1
}

$configuredHooksPath = Invoke-GitValue @("config", "--get", "core.hooksPath")
if ($configuredHooksPath) {
    $hooksRoot = Resolve-RepoPath $configuredHooksPath
} else {
    $hookPath = Invoke-GitValue @("rev-parse", "--git-path", "hooks/pre-commit")
    if (-not $hookPath) {
        Write-Error "[hooks:precommit] could not resolve .git/hooks/pre-commit"
        exit 1
    }
    $hookFile = Resolve-RepoPath $hookPath
    $hooksRoot = Split-Path $hookFile -Parent
}

$destination = Join-Path $hooksRoot "pre-commit"
$managedNeedles = @(
    "Chthonic Archive",
    "ci/run.ts",
    "--staged"
)

function Test-ManagedHook {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return $false
    }
    $content = Get-Content -Raw -Path $Path
    foreach ($needle in $managedNeedles) {
        if (-not $content.Contains($needle)) {
            return $false
        }
    }
    return $true
}

function Test-HookHealthy {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return $false
    }
    $content = Get-Content -Raw -Path $Path
    return $content.Contains("ci/run.ts") -and $content.Contains("--staged")
}

if ($VerifyOnly) {
    if (Test-HookHealthy $destination) {
        Write-Host "[hooks:precommit] ok: $destination runs ci/run.ts --staged"
        exit 0
    }
    Write-Error "[hooks:precommit] missing or stale: $destination"
    exit 1
}

if ((Test-Path $destination) -and -not $Force -and -not (Test-ManagedHook $destination)) {
    Write-Error "[hooks:precommit] refusing to overwrite unmanaged hook: $destination"
    Write-Error "[hooks:precommit] rerun with -Force after preserving any local hook content that matters"
    exit 1
}

if (-not (Test-Path $hooksRoot)) {
    New-Item -ItemType Directory -Path $hooksRoot | Out-Null
}

Copy-Item -Path $source -Destination $destination -Force
Write-Host "[hooks:precommit] installed: $destination"
exit 0
