#!/usr/bin/env pwsh
#
# @SID: SCRIPT_FLUX_FORGE_PREFLIGHT_V1
# @Type: UTILITY
# @Spectrum: WHITE
# @Zone: FLUX_FORGE
# @Purpose: Strict env preflight for the FLUX engine forge (CUDA 12.x, SM89, scratch >= 60 GB).
#
# Run before kicking off the 30-minute AOT compile so we fail fast on
# missing toolchain rather than mid-build.
#
# Usage:
#   pwsh -NoProfile -File .\apps\flux-engine-forge\scripts\preflight.ps1
#   pwsh -NoProfile -File .\apps\flux-engine-forge\scripts\preflight.ps1 -ScratchDir 'D:\flux-scratch'

[CmdletBinding()]
param(
    [string]$ScratchDir = (Join-Path $PSScriptRoot '..\scratch'),
    [int]$MinFreeGB = 60
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Log([string]$m)  { Write-Host "[forge-preflight] $m" }
function Warn([string]$m) { Write-Warning "[forge-preflight] $m" }
function Fail([string]$m) { Write-Error "[forge-preflight] $m"; exit 1 }

# --- CUDA Toolkit 12.x ------------------------------------------------------

$nvcc = Get-Command nvcc -ErrorAction SilentlyContinue
if (-not $nvcc) {
    Fail "nvcc not on PATH. Install CUDA Toolkit 12.x: https://developer.nvidia.com/cuda-downloads"
}
$nvccVer = (& nvcc --version) -join "`n"
if ($nvccVer -match 'release\s+(\d+)\.(\d+)') {
    $major = [int]$matches[1]
    if ($major -lt 12) {
        Fail "CUDA >= 12.0 required. nvcc reports major version $major.`n$nvccVer"
    }
    Log "CUDA OK (release $major.$($matches[2]); requirement >= 12.0)"
} else {
    Fail "Could not parse CUDA version from nvcc output:`n$nvccVer"
}

# --- NVML driver bridge -----------------------------------------------------

$nvml = Join-Path $env:SystemRoot 'System32\nvml.dll'
if (-not (Test-Path $nvml)) {
    Fail "nvml.dll not at $nvml. Install or repair the NVIDIA driver."
}
Log "nvml.dll OK ($nvml)"

# --- nvidia-smi + SM89 ------------------------------------------------------

$smi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if (-not $smi) {
    Fail "nvidia-smi not on PATH. Install or repair the NVIDIA driver."
}
$gpuInfo = & nvidia-smi --query-gpu=name,compute_cap,memory.total --format=csv,noheader,nounits | Select-Object -First 1
if (-not $gpuInfo) {
    Fail "nvidia-smi returned no GPU rows."
}
$parts = $gpuInfo -split ',' | ForEach-Object { $_.Trim() }
$gpuName = $parts[0]
$gpuCap  = $parts[1]
$gpuVram = [int]$parts[2]
if ($gpuCap -ne '8.9') {
    Fail "GPU 0 compute capability is '$gpuCap'; require '8.9' (RTX 4000 series Ada). Detected: $gpuName"
}
if ($gpuVram -lt 22000) {
    Warn "GPU has $gpuVram MB total VRAM; FLUX.1-dev expects ~24 GB. Continue at your own risk."
}
Log "GPU 0 OK: $gpuName (SM $gpuCap, $gpuVram MB)"

# --- Scratch disk capacity --------------------------------------------------

$scratch = (Resolve-Path -Path $ScratchDir -ErrorAction SilentlyContinue)
if (-not $scratch) {
    Log "scratch dir does not exist; creating: $ScratchDir"
    New-Item -ItemType Directory -Path $ScratchDir -Force | Out-Null
    $scratch = Resolve-Path -Path $ScratchDir
}
$drive = ($scratch.Path -split '\\')[0].TrimEnd(':')
$volume = Get-PSDrive -Name $drive -ErrorAction Stop
$freeGB = [math]::Floor($volume.Free / 1GB)
if ($freeGB -lt $MinFreeGB) {
    Fail "scratch volume $drive has $freeGB GB free; require >= $MinFreeGB GB."
}
Log "scratch OK: $($scratch.Path) on $drive`: ($freeGB GB free)"

# --- Python / uv ------------------------------------------------------------

$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    Fail "uv not on PATH. Install via 'winget install --id astral-sh.uv' or follow PWSH_RULES.md."
}
Log "uv OK ($($uv.Source))"

Log "PREFLIGHT PASSED — env is ready for forge."
exit 0
