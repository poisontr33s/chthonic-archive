#!/usr/bin/env pwsh

#Requires -Version 7
# scripts/nvidia-stack-probe.ps1
# Probes the full NVIDIA/CUDA/Vulkan software stack from env vars and DLL VersionInfo.
# Read-only — no admin required. Output: .chthonic/cache/nvidia_stack.json
#
# Usage:
#   pwsh -NoProfile -File scripts/nvidia-stack-probe.ps1
#   pwsh -NoProfile -File scripts/nvidia-stack-probe.ps1 -OutPath custom/path.json
#   mise run nvidia-probe   (via slab mise.toml task)

param([string]$OutPath = '')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'SilentlyContinue'

$repoRoot = Split-Path $PSScriptRoot -Parent
if (-not $OutPath) { $OutPath = Join-Path $repoRoot '.chthonic\cache\nvidia_stack.json' }
New-Item -ItemType Directory -Force -Path (Split-Path $OutPath) | Out-Null

function Get-DllInfo([string]$path) {
    if (-not (Test-Path $path)) { return $null }
    $item = Get-Item $path
    [ordered]@{
        version = $item.VersionInfo.FileVersion
        size_mb = [math]::Round($item.Length / 1MB, 2)
        path    = $path
    }
}

function Invoke-Safe([string]$bin, [string[]]$args_) {
    try { & $bin @args_ 2>$null | Out-String } catch { '' }
}

# ── 1. DRIVER ──────────────────────────────────────────────────────────────────
# nvidia-smi --version deprecated fields in 600+ series; bare nvidia-smi header is authoritative
$smiOutput = Invoke-Safe 'nvidia-smi'
$driverVer = if ($smiOutput -match 'KMD Version:\s*([\d.]+)')      { $Matches[1] } else { $null }
$cudaUmd   = if ($smiOutput -match 'CUDA UMD Version:\s*([\d.]+)') { $Matches[1] } else { $null }

# ── 2. CUDA TOOLKIT ───────────────────────────────────────────────────────────
$nvccRaw = Invoke-Safe 'nvcc' '--version'
$nvccVer = if ($nvccRaw -match 'release (\S+),') { $Matches[1].TrimEnd(',') } else { $null }
$nvccPath = (Get-Command 'nvcc' -ErrorAction SilentlyContinue)?.Source

$cudaEnvVars = [ordered]@{}
foreach ($v in @('CUDA_PATH','CUDA_PATH_V12_8','CUDA_PATH_V12_9','CUDA_PATH_V13_2','CUDA_PATH_V13_3')) {
    $val = [Environment]::GetEnvironmentVariable($v, 'Machine')
    $cudaEnvVars[$v] = [ordered]@{
        value   = $val
        exists  = if ($val) { Test-Path $val } else { $false }
        has_nvcc = if ($val) { Test-Path (Join-Path $val 'bin\nvcc.exe') } else { $false }
        has_cudart_lib = if ($val) { Test-Path (Join-Path $val 'lib\x64\cudart.lib') } else { $false }
        has_cudart_dll = if ($val) { (Get-ChildItem (Join-Path $val 'bin') -Filter 'cudart64_*.dll' -ErrorAction SilentlyContinue | Select-Object -First 1)?.Name } else { $null }
    }
}

$cudaToolkitDlls = [ordered]@{}
$v128 = [Environment]::GetEnvironmentVariable('CUDA_PATH_V12_8', 'Machine')
if ($v128) {
    foreach ($dll in @('cudart64_12.dll','cublas64_12.dll','cublasLt64_12.dll','curand64_10.dll')) {
        $p = Join-Path $v128 "bin\$dll"
        $cudaToolkitDlls[$dll] = Get-DllInfo $p
    }
}

# ── 3. VULKAN ─────────────────────────────────────────────────────────────────
$vulkanSdkPath = [Environment]::GetEnvironmentVariable('VULKAN_SDK', 'Machine')
if (-not $vulkanSdkPath) { $vulkanSdkPath = $env:VULKAN_SDK }

$glslcRaw = Invoke-Safe (Join-Path $vulkanSdkPath 'Bin\glslc.exe') '--version'
$glslcVer = if ($glslcRaw -match 'v(\S+)') { $Matches[1] } else { $null }

$vkinfoRaw = Invoke-Safe (Join-Path $vulkanSdkPath 'Bin\vulkaninfoSDK.exe') '--version'
$vkinfoVer = if ($vkinfoRaw -match 'Vulkan Instance Version: (\S+)') { $Matches[1] } else { $null }

# ── 4. SYSTEM32 DRIVER DLLs ───────────────────────────────────────────────────
$sys32 = 'C:\Windows\System32'
$driverDlls = [ordered]@{}
foreach ($dll in @('nvapi64.dll','nvcuda.dll','nvcuvid.dll','nvEncodeAPI64.dll',
                   'nvml.dll','nvofapi64.dll','NvFBC64.dll','NvIFR64.dll')) {
    $driverDlls[$dll] = Get-DllInfo (Join-Path $sys32 $dll)
}

# ── 5. NGX / DLSS ─────────────────────────────────────────────────────────────
$dlssCandidates = @(
    (Join-Path $repoRoot 'CLAUDEBASE\The-Savant-High-Bounties\streamline-sdk-v2.12.0\bin\x64\nvngx_dlss.dll'),
    'C:\Program Files (x86)\World of Warcraft\_retail_\nvngx_dlss.dll',
    'C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Bin\Win64Shared\nvngx_dlss.dll',
    'C:\Program Files (x86)\Steam\steamapps\common\Path of Exile 2\Streamline\nvngx_dlss.dll'
)
$dlssFound = [System.Collections.Generic.List[object]]::new()
foreach ($p in $dlssCandidates) {
    $info = Get-DllInfo $p
    if ($info) { $dlssFound.Add($info) }
}
# FileVersion uses commas on Windows — normalise to dots for version sort
$dlssNewest = if ($dlssFound.Count -gt 0) {
    ($dlssFound | Sort-Object { [version](($_.version -replace ',','.' )) } -Descending)[0]
} else { $null }

$dlisr = Get-DllInfo 'C:\Program Files\NVIDIA Corporation\NVIDIA App\NvBackend\nvngx_dlisr.dll'

# ── 6. cuDNN ──────────────────────────────────────────────────────────────────
$cudnnBase = 'C:\Program Files\NVIDIA\CUDNN'
$cudnnInfo = $null
if (Test-Path $cudnnBase) {
    $latest = Get-ChildItem $cudnnBase -Directory | Sort-Object Name -Descending | Select-Object -First 1
    if ($latest) {
        $cudnnDll = Get-ChildItem $latest.FullName -Recurse -Filter 'cudnn_adv64_9.dll' -ErrorAction SilentlyContinue | Select-Object -First 1
        $cudnnInfo = if ($cudnnDll) {
            [ordered]@{
                version   = (Get-Item $cudnnDll.FullName).VersionInfo.FileVersion
                sdk_path  = $latest.FullName
                dll_path  = $cudnnDll.FullName
            }
        }
    }
}

# ── 7. ASSEMBLE ───────────────────────────────────────────────────────────────
$snapshot = [ordered]@{
    meta = [ordered]@{
        snapshot_date   = (Get-Date -Format 'yyyy-MM-dd')
        probe_script    = 'scripts/nvidia-stack-probe.ps1'
    }
    driver = [ordered]@{
        version          = $driverVer
        cuda_umd_max     = $cudaUmd
        nvapi64_dll_ver  = $driverDlls['nvapi64.dll']?.version
    }
    cuda = [ordered]@{
        nvcc_version    = $nvccVer
        nvcc_path       = $nvccPath
        cuda_path_env   = $cudaEnvVars
        toolkit_dlls    = $cudaToolkitDlls
    }
    vulkan = [ordered]@{
        sdk_path        = $vulkanSdkPath
        glslc_version   = $glslcVer
        instance_version = $vkinfoVer
        sdk_accessible  = if ($vulkanSdkPath) { Test-Path "$vulkanSdkPath\Bin\glslc.exe" } else { $false }
    }
    ngx = [ordered]@{
        dlss_newest     = $dlssNewest
        dlss_candidates = @($dlssFound)
        dlisr           = $dlisr
        ngx_loader_system32 = (Test-Path 'C:\Windows\System32\nvngx.dll')
    }
    cudnn = $cudnnInfo
    system32_dlls = $driverDlls
}

# ── 8. WRITE ──────────────────────────────────────────────────────────────────
$json = $snapshot | ConvertTo-Json -Depth 8
Set-Content -Path $OutPath -Value $json -Encoding utf8
$dlssVerDisplay   = if ($dlssNewest)  { $dlssNewest['version']  } else { 'not found' }
$dlssPathDisplay  = if ($dlssNewest)  { $dlssNewest['path']     } else { '' }
$cudnnVerDisplay  = if ($cudnnInfo)   { $cudnnInfo['version']   } else { 'not found' }
$cudnnPathDisplay = if ($cudnnInfo)   { $cudnnInfo['sdk_path']  } else { '' }

Write-Host "nvidia-stack-probe: wrote $OutPath"
Write-Host "  driver        : $driverVer  (CUDA UMD max $cudaUmd)"
Write-Host "  nvcc          : $nvccVer  @ $nvccPath"
Write-Host "  Vulkan SDK    : $($snapshot.vulkan.sdk_path)"
Write-Host "  DLSS newest   : $dlssVerDisplay  @ $dlssPathDisplay"
Write-Host "  cuDNN         : $cudnnVerDisplay  @ $cudnnPathDisplay"
