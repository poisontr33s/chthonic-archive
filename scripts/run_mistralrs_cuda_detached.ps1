#!/usr/bin/env pwsh
#
# Detached launcher for long-running mistralrs CUDA installs.
#
# @SID: TOOL_MISTRALRS_CUDA_DETACHED_LAUNCHER_V1
# @Type: Utility
# @Spectrum: WHITE
# @Zone: THE GARDEN

param(
    [ValidateSet("insiders", "vs2022", "auto")]
    [string]$Toolchain = "insiders",

    [switch]$NoFlashAttn,
    [switch]$NoForce,

    [ValidateRange(1, 64)]
    [int]$Jobs = 0,

    [ValidateRange(1, 64)]
    [int]$NvccThreads = 0,

    [string]$CargoTargetDir = "$env:LOCALAPPDATA\chthonic\cargo-target\mistralrs-cuda",
    [string]$LogRoot = "codex/mailbox"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Optional global defaults (persist via User env vars):
#   CHTHONIC_MISTRAL_JOBS
#   CHTHONIC_MISTRAL_NVCC_THREADS
if ($Jobs -eq 0 -and $env:CHTHONIC_MISTRAL_JOBS) {
    $parsedJobs = 0
    if ([int]::TryParse($env:CHTHONIC_MISTRAL_JOBS, [ref]$parsedJobs) -and $parsedJobs -ge 1 -and $parsedJobs -le 64) {
        $Jobs = $parsedJobs
    }
}
if ($NvccThreads -eq 0 -and $env:CHTHONIC_MISTRAL_NVCC_THREADS) {
    $parsedThreads = 0
    if ([int]::TryParse($env:CHTHONIC_MISTRAL_NVCC_THREADS, [ref]$parsedThreads) -and $parsedThreads -ge 1 -and $parsedThreads -le 64) {
        $NvccThreads = $parsedThreads
    }
}
if ($Jobs -eq 0) { $Jobs = 4 }
if ($NvccThreads -eq 0) { $NvccThreads = 2 }

function Get-RepoRoot {
    $dir = (Get-Location).Path
    while ($true) {
        if ((Test-Path (Join-Path $dir "pyproject.toml")) -and (Test-Path (Join-Path $dir "AGENTS.md"))) {
            return $dir
        }
        $parent = Split-Path -Parent $dir
        if ($parent -eq $dir) {
            throw "Could not locate repo root from current directory."
        }
        $dir = $parent
    }
}

$repoRoot = Get-RepoRoot
$logDir = Join-Path $repoRoot $LogRoot
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$stdoutLog = Join-Path $logDir "MISTRALRS_CUDA_BUILD_${stamp}.out.log"
$stderrLog = Join-Path $logDir "MISTRALRS_CUDA_BUILD_${stamp}.err.log"
$installScript = Join-Path $repoRoot "scripts\install_mistralrs_cuda.ps1"

if (-not (Test-Path $installScript)) {
    throw "Installer script not found: $installScript"
}

$argList = @(
    "-NoProfile",
    "-File", $installScript,
    "-Toolchain", $Toolchain,
    "-Jobs", "$Jobs",
    "-NvccThreads", "$NvccThreads",
    "-CargoTargetDir", $CargoTargetDir
)

if ($NoFlashAttn) { $argList += "-NoFlashAttn" }
if ($NoForce) { $argList += "-NoForce" }

$proc = Start-Process `
    -FilePath "pwsh" `
    -ArgumentList $argList `
    -WorkingDirectory $repoRoot `
    -PassThru `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog

Write-Host "Started detached mistralrs CUDA build." -ForegroundColor Green
Write-Host "  PID:        $($proc.Id)"
Write-Host "  Stdout log: $stdoutLog"
Write-Host "  Stderr log: $stderrLog"
Write-Host ""
Write-Host "Tail logs with:"
Write-Host "  Get-Content -Path `"$stdoutLog`" -Wait"
