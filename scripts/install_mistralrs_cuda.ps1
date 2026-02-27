#!/usr/bin/env pwsh
#
# Deterministic mistralrs CUDA installer for Windows toolchain control.
#
# @SID: TOOL_MISTRALRS_CUDA_INSTALLER_V1
# @Type: Utility
# @Spectrum: WHITE
# @Zone: THE GARDEN

param(
    [ValidateSet("insiders", "vs2022", "auto")]
    [string]$Toolchain = "insiders",

    [switch]$NoFlashAttn,
    [switch]$DryRun,

    [string]$CargoTargetDir = "$env:LOCALAPPDATA\Temp\cargo-mistralrs-cuda"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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
    $vs2022 = @($Instances | Where-Object {
        $_.installationVersion -like "17.*"
    })

    switch ($Selection) {
        "insiders" {
            if (-not $insiders) {
                throw "VS 18 Insiders with C++ tools not found. Use -Toolchain vs2022 or install Insiders Build Tools."
            }
            return ($insiders | Sort-Object installationVersion -Descending | Select-Object -First 1)
        }
        "vs2022" {
            if (-not $vs2022) {
                throw "VS 2022 Build Tools with C++ tools not found."
            }
            return ($vs2022 | Sort-Object installationVersion -Descending | Select-Object -First 1)
        }
        "auto" {
            if ($insiders) {
                return ($insiders | Sort-Object installationVersion -Descending | Select-Object -First 1)
            }
            if ($vs2022) {
                return ($vs2022 | Sort-Object installationVersion -Descending | Select-Object -First 1)
            }
            throw "No supported VS toolchain detected (insiders or vs2022)."
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
        [string[]]$RequiredFlags
    )

    $existing = @()
    if ($env:NVCC_PREPEND_FLAGS) {
        $existing = @($env:NVCC_PREPEND_FLAGS -split "\s+" | Where-Object { $_ -ne "" })
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
$env:NVCC_PREPEND_FLAGS = Merge-NvccFlags -RequiredFlags $requiredFlags

$featureList = if ($NoFlashAttn) { "cuda" } else { "cuda,flash-attn" }

if (-not (Test-Path $CargoTargetDir)) {
    New-Item -ItemType Directory -Path $CargoTargetDir -Force | Out-Null
}
$env:CARGO_TARGET_DIR = $CargoTargetDir

Write-Host ""
Write-Host "Resolved build environment:" -ForegroundColor Green
Write-Host "  nvcc version:         $(Get-NvccVersion)"
Write-Host "  cl.exe:               $($cl.Source)"
Write-Host "  CUDAHOSTCXX:          $env:CUDAHOSTCXX"
Write-Host "  NVCC_CCBIN:           $env:NVCC_CCBIN"
Write-Host "  NVCC_PREPEND_FLAGS:   $env:NVCC_PREPEND_FLAGS"
Write-Host "  CARGO_TARGET_DIR:     $env:CARGO_TARGET_DIR"
Write-Host "  Cargo features:       $featureList"

$installArgs = @(
    "install",
    "mistralrs-cli",
    "--locked",
    "--force",
    "--features",
    $featureList
)

if ($DryRun) {
    Write-Host ""
    Write-Host "Dry-run only. Command not executed:" -ForegroundColor Yellow
    Write-Host "cargo $($installArgs -join ' ')"
    exit 0
}

Write-Host ""
Write-Host "Running cargo install..." -ForegroundColor Cyan
& cargo @installArgs
