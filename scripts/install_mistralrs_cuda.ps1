#!/usr/bin/env pwsh
#
# Deterministic mistralrs CUDA installer for Windows toolchain control.
#
# @SID: TOOL_MISTRALRS_CUDA_INSTALLER_V1
# @Type: Utility
# @Spectrum: WHITE
# @Zone: THE GARDEN

param(
    [ValidateSet("insiders", "vs2026", "auto")]
    [string]$Toolchain = "insiders",

    [switch]$NoFlashAttn,
    [switch]$DryRun,
    [switch]$NoForce,
    [ValidateRange(1, 64)]
    [int]$Jobs = 0,
    [ValidateRange(1, 64)]
    [int]$NvccThreads = 0,

    [string]$CargoTargetDir = "$env:LOCALAPPDATA\chthonic\cargo-target\mistralrs-cuda"
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

function Get-VSWherePath {
    $candidates = @(
        "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe",
        "C:\Program Files\Microsoft Visual Studio\Installer\vswhere.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    throw "vswhere.exe not found. Install Visual Studio Installer."
}

function Get-VSInstances {
    $vswhere = Get-VSWherePath
    $json = & $vswhere -all -prerelease -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -format json
    if (-not $json) {
        throw "No Visual Studio instances with C++ tools were found."
    }
    return ($json | ConvertFrom-Json)
}

function Select-VSInstance {
    param(
        [Parameter(Mandatory = $true)]
        [Object[]]$Instances,

        [Parameter(Mandatory = $true)]
        [string]$Selection
    )

    $insiders = @($Instances | Where-Object {
        $_.isPrerelease -eq $true -and $_.installationVersion -like "18.*"
    })
    $vs2026 = @($Instances | Where-Object {
        $_.installationVersion -like "18.*"
    })

    switch ($Selection) {
        "insiders" {
            if (-not $insiders) {
                throw "VS 18 Insiders with C++ tools not found. Use -Toolchain vs2026 or install Insiders Build Tools."
            }
            return ($insiders | Sort-Object installationVersion -Descending | Select-Object -First 1)
        }
        "vs2026" {
            if (-not $vs2026) {
                throw "VS 2026 Build Tools with C++ tools not found."
            }
            return ($vs2026 | Sort-Object installationVersion -Descending | Select-Object -First 1)
        }
        "auto" {
            if ($insiders) {
                return ($insiders | Sort-Object installationVersion -Descending | Select-Object -First 1)
            }
            if ($vs2026) {
                return ($vs2026 | Sort-Object installationVersion -Descending | Select-Object -First 1)
            }
            throw "No supported VS toolchain detected (insiders or vs2026)."
        }
        default {
            throw "Unsupported toolchain selection: $Selection"
        }
    }
}

function Enter-SelectedDevShell {
    param(
        [Parameter(Mandatory = $true)]
        [string]$VsInstallPath
    )

    $devShellDll = Join-Path $VsInstallPath "Common7\Tools\Microsoft.VisualStudio.DevShell.dll"
    if (-not (Test-Path $devShellDll)) {
        throw "Microsoft.VisualStudio.DevShell.dll not found at $devShellDll"
    }

    if (Get-Module Microsoft.VisualStudio.DevShell -ErrorAction SilentlyContinue) {
        Remove-Module Microsoft.VisualStudio.DevShell -Force -ErrorAction SilentlyContinue
    }
    Import-Module $devShellDll -Force

    Enter-VsDevShell -VsInstallPath $VsInstallPath -SkipAutomaticLocation -Arch amd64 -HostArch amd64 | Out-Null
}

function Get-NvccVersion {
    $output = & nvcc --version
    $match = ($output | Select-String -Pattern "release\s+([0-9]+\.[0-9]+)" | Select-Object -First 1)
    if (-not $match) {
        return "unknown"
    }
    return $match.Matches[0].Groups[1].Value
}

function Merge-NvccFlags {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$RequiredFlags,

        [int]$ThreadCount = 0
    )

    $existing = @()
    if ($env:NVCC_PREPEND_FLAGS) {
        $existing = @($env:NVCC_PREPEND_FLAGS -split "\s+" | Where-Object { $_ -ne "" })
    }

    if ($ThreadCount -gt 0) {
        $existing = @($existing | Where-Object {
            $_ -notmatch "^-t\d+$" -and $_ -ne "--threads"
        })
        $RequiredFlags += "-t$ThreadCount"
    }

    return (($RequiredFlags + $existing | Select-Object -Unique) -join " ").Trim()
}

if (-not (Get-Command nvcc -ErrorAction SilentlyContinue)) {
    throw "nvcc not found on PATH. Install CUDA Toolkit first."
}
if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    throw "cargo not found on PATH. Install Rust toolchain first."
}

$instances = Get-VSInstances
$selected = Select-VSInstance -Instances $instances -Selection $Toolchain

Write-Host "Using Visual Studio toolchain:" -ForegroundColor Cyan
Write-Host "  Path:    $($selected.installationPath)"
Write-Host "  Version: $($selected.installationVersion)"
Write-Host "  Product: $($selected.productId)"

Enter-SelectedDevShell -VsInstallPath $selected.installationPath

$cl = Get-Command cl.exe -ErrorAction Stop
$env:CUDAHOSTCXX = $cl.Source
$env:NVCC_CCBIN = Split-Path -Parent $cl.Source

$requiredFlags = @("--use-local-env")
if ($selected.installationVersion -like "18.*") {
    # CUDA 12.x does not officially support VS 18 yet.
    $requiredFlags += "--allow-unsupported-compiler"
}
$env:NVCC_PREPEND_FLAGS = Merge-NvccFlags -RequiredFlags $requiredFlags -ThreadCount $NvccThreads

$featureList = if ($NoFlashAttn) { "cuda" } else { "cuda,flash-attn" }

if (-not (Test-Path $CargoTargetDir)) {
    New-Item -ItemType Directory -Path $CargoTargetDir -Force | Out-Null
}
$env:CARGO_TARGET_DIR = $CargoTargetDir

if ($Jobs -gt 0) {
    $env:CARGO_BUILD_JOBS = [string]$Jobs
}

Write-Host ""
Write-Host "Resolved build environment:" -ForegroundColor Green
Write-Host "  nvcc version:         $(Get-NvccVersion)"
Write-Host "  cl.exe:               $($cl.Source)"
Write-Host "  CUDAHOSTCXX:          $env:CUDAHOSTCXX"
Write-Host "  NVCC_CCBIN:           $env:NVCC_CCBIN"
Write-Host "  NVCC_PREPEND_FLAGS:   $env:NVCC_PREPEND_FLAGS"
Write-Host "  CARGO_TARGET_DIR:     $env:CARGO_TARGET_DIR"
if ($Jobs -gt 0) {
    Write-Host "  CARGO_BUILD_JOBS:     $env:CARGO_BUILD_JOBS"
}
Write-Host "  Cargo features:       $featureList"

$installArgs = @(
    "install",
    "mistralrs-cli",
    "--locked",
    "--features",
    $featureList
)
if (-not $NoForce) {
    $installArgs += "--force"
}

if ($DryRun) {
    Write-Host ""
    Write-Host "Dry-run only. Command not executed:" -ForegroundColor Yellow
    Write-Host "cargo $($installArgs -join ' ')"
    exit 0
}

Write-Host ""
Write-Host "Running cargo install..." -ForegroundColor Cyan
& cargo @installArgs
