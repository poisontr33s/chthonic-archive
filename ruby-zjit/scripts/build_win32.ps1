#!/usr/bin/env pwsh
#Requires -Version 7.0
# @SID: ruby-zjit-ext-build-win32
# Build CUDA + Vulkan + TensorRT Ruby C extensions on Win32
# against the custom ZJIT binary at C:\ruby-zjit-build\ruby-4.0.3\ruby.exe
# Uses MSYS2 UCRT64 toolchain from rv's ruby-4.0.3 devkit.
#
# Project root: ruby-zjit/ (self-contained — ext/, scripts/, REGISTRY.yaml, WIN32_PROFILE.yaml)
# Registry    : ruby-zjit/REGISTRY.yaml  — add new extension dirs to ext/ + update registry
# Profile     : ruby-zjit/WIN32_PROFILE.yaml — pinned SDK + machine baseline
#
# Usage:
#   .\ruby-zjit\scripts\build_win32.ps1             # Build all extensions
#   .\ruby-zjit\scripts\build_win32.ps1 -Ext cuda_rb # Build specific extension
#   .\ruby-zjit\scripts\build_win32.ps1 -Probe       # SDK detection only (dry-run)
#   .\ruby-zjit\scripts\build_win32.ps1 -Clean       # Remove build artifacts
#
# SDK auto-detection: version-agnostic glob (latest installed wins).
# Override via env vars: CUDA_PATH, VULKAN_SDK, TRT_PATH, CUDNN_PATH

[CmdletBinding()]
param(
    [string]$Ext    = "all",
    [switch]$Probe,
    [switch]$Clean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── SDK Paths (version-agnostic: picks latest installed unless overridden) ────
# Override any of these by setting the corresponding env var before running.
# See: build/ruby-zjit-podman/WIN32_PROFILE.yaml for the canonical pinned state.
function Find-LatestSdkDir([string]$parent, [string]$filter) {
    if (-not (Test-Path $parent)) { return $null }
    Get-ChildItem $parent -Directory -Filter $filter -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        Select-Object -First 1 -ExpandProperty FullName
}

$CUDA_PATH   = $env:CUDA_PATH  ??
    (Find-LatestSdkDir "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA" "v*") ??
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2"

$VULKAN_SDK  = $env:VULKAN_SDK ??
    (Find-LatestSdkDir "C:\VulkanSDK" "*") ??
    "C:\VulkanSDK\1.4.341.1"

$TRT_PATH    = $env:TRT_PATH   ??
    (Find-LatestSdkDir "C:\Program Files\NVIDIA" "TensorRT-*") ??
    ""

$CUDNN_PATH  = $env:CUDNN_PATH ??
    (Find-LatestSdkDir "C:\Program Files\NVIDIA\CUDNN" "v*") ??
    ""

# ── Ruby Targets ─────────────────────────────────────────────────────────────
# Primary: the ZJIT-patched binary from C:\ruby-zjit-build (custom source build)
# Fallback: rv-installed zjit binary
$RUBY_ZJIT_BUILD = "C:\ruby-zjit-build\ruby-4.0.3\ruby.exe"
$RUBY_RV_ZJIT    = Join-Path $env:APPDATA "rv\rubies\ruby-4.0.3-zjit\bin\ruby.exe"
$RUBY_RV_STD     = Join-Path $env:APPDATA "rv\rubies\ruby-4.0.3\bin\ruby.exe"

# ── MSYS2 UCRT64 Toolchain (from rv devkit) ──────────────────────────────────
$MSYS2_ROOT = Join-Path $env:APPDATA "rv\rubies\ruby-4.0.3\msys64"
$UCRT64_BIN = Join-Path $MSYS2_ROOT  "ucrt64\bin"
$GCC        = Join-Path $UCRT64_BIN  "gcc.exe"
$GPP        = Join-Path $UCRT64_BIN  "g++.exe"
$MAKE       = Join-Path $UCRT64_BIN  "mingw32-make.exe"

# ── Ext source root ───────────────────────────────────────────────────────────
$EXT_SRC    = Join-Path $PSScriptRoot "..\ext"
$BUILD_DIR  = Join-Path $PSScriptRoot "..\..\build\ruby-zjit-ext-win32"

# ── Helpers ───────────────────────────────────────────────────────────────────
function Write-Step([string]$msg) {
    Write-Host "`n── $msg" -ForegroundColor Cyan
}
function Write-Ok([string]$msg) {
    Write-Host "  ✓ $msg" -ForegroundColor Green
}
function Write-Warn([string]$msg) {
    Write-Host "  ! $msg" -ForegroundColor Yellow
}
function Write-Fail([string]$msg) {
    Write-Host "  ✗ $msg" -ForegroundColor Red
}

function Find-RubyExe {
    foreach ($candidate in @($RUBY_ZJIT_BUILD, $RUBY_RV_ZJIT, $RUBY_RV_STD)) {
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

function Probe-SDKs {
    Write-Step "SDK Detection"

    $cuda_ok = Test-Path (Join-Path $CUDA_PATH "include\cuda_runtime_api.h")
    Write-Host ("  CUDA_PATH   : $CUDA_PATH " + $(if ($cuda_ok) {"[OK]"} else {"[MISSING]"}))

    $vk_ok = Test-Path (Join-Path $VULKAN_SDK "include\vulkan\vulkan.h")
    Write-Host ("  VULKAN_SDK  : $VULKAN_SDK " + $(if ($vk_ok) {"[OK]"} else {"[MISSING]"}))

    $trt_ok = Test-Path (Join-Path $TRT_PATH "include\NvInfer.h")
    Write-Host ("  TRT_PATH    : $TRT_PATH " + $(if ($trt_ok) {"[OK]"} else {"[MISSING]"}))

    # cuDNN v9.x stores headers under include\<cuda-ver>\cudnn.h
    $cudnn_ok = (Test-Path (Join-Path $CUDNN_PATH "include\cudnn.h")) -or
                (Get-ChildItem (Join-Path $CUDNN_PATH "include") -Recurse -Filter "cudnn.h" -ErrorAction SilentlyContinue | Select-Object -First 1)
    Write-Host ("  CUDNN_PATH  : $CUDNN_PATH " + $(if ($cudnn_ok) {"[OK]"} else {"[MISSING]"}))

    $ruby = Find-RubyExe
    Write-Host "  Ruby target : $(if ($ruby) {$ruby} else {'[NOT FOUND]'})"

    $gcc_ok = Test-Path $GCC
    Write-Host ("  GCC (UCRT64): $GCC " + $(if ($gcc_ok) {"[OK]"} else {"[MISSING]"}))

    Write-Host ""
    Write-Host "  Shader tools (in PATH via Vulkan SDK):"
    foreach ($tool in @("glslc", "dxc", "spirv-cross", "slangc")) {
        $path = Get-Command $tool -ErrorAction SilentlyContinue
        Write-Host ("    $tool : " + $(if ($path) {$path.Source} else {"[not in PATH]"}))
    }

    return @{
        cuda   = $cuda_ok
        vulkan = $vk_ok
        trt    = $trt_ok
        cudnn  = $cudnn_ok
        ruby   = ($null -ne $ruby)
        gcc    = $gcc_ok
    }
}

function Build-Extension([string]$extName) {
    $src = Join-Path $EXT_SRC $extName
    if (-not (Test-Path $src)) {
        Write-Fail "${extName}: source dir not found at $src"
        return $false
    }

    $dst = Join-Path $BUILD_DIR $extName
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    Copy-Item -Path "$src\*" -Destination $dst -Recurse -Force

    $ruby = Find-RubyExe
    if (-not $ruby) {
        Write-Fail "${extName}: no Ruby executable found"
        return $false
    }

    Write-Step "Building $extName"
    Write-Host "  Ruby: $ruby"
    Write-Host "  Src : $dst"

    # Set env so extconf.rb can locate the SDKs
    $env:CUDA_PATH  = $CUDA_PATH
    $env:VULKAN_SDK = $VULKAN_SDK
    $env:TRT_PATH   = $TRT_PATH
    $env:CUDNN_PATH = $CUDNN_PATH

    # Detect rv — use ridk exec for MSYS2/UCRT64 environment activation when available.
    # rv r ridk exec sets MSYSTEM=UCRT64, injects UCRT64 bin (gcc/g++/mingw32-make) into PATH,
    # and handles devkit versioning automatically. Falls back to manual PATH injection.
    $rvCmd = Get-Command rv -ErrorAction SilentlyContinue
    $useRv = $null -ne $rvCmd

    if (-not $useRv) {
        # Manual fallback: inject UCRT64 bin into PATH directly
        $env:PATH = "${UCRT64_BIN};$($env:PATH)"
    }

    Push-Location $dst
    try {
        # Run extconf.rb
        if ($useRv) {
            Write-Host "  (rv r ridk exec)"
            rv r ridk exec -- $ruby extconf.rb 2>&1
        } else {
            & $ruby extconf.rb 2>&1
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "${extName}: extconf.rb failed (exit $LASTEXITCODE)"
            return $false
        }

        # Run make (always via ridk exec when rv is present — ridk owns the MSYS2 make)
        if ($useRv) {
            rv r ridk exec -- mingw32-make 2>&1
        } else {
            & $MAKE 2>&1
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "${extName}: make failed"
            return $false
        }

        # Locate built .so / .dll
        $dll = Get-ChildItem -Path $dst -Filter "*.so","*.dll" |
               Where-Object { $_.Name -notlike "libgcc*" } |
               Select-Object -First 1
        if ($dll) {
            Write-Ok "${extName}: ${$dll.Name} built at $($dll.FullName)"
        } else {
            Write-Warn "${extName}: make succeeded but no .so/.dll found — check Makefile output"
        }
        return $true
    }
    catch {
        Write-Fail "${extName}: exception — $_"
        return $false
    }
    finally {
        Pop-Location
    }
}

function Clean-Build {
    Write-Step "Cleaning ext-win32-build"
    if (Test-Path $BUILD_DIR) {
        Remove-Item -Recurse -Force $BUILD_DIR
        Write-Ok "Removed $BUILD_DIR"
    } else {
        Write-Warn "Nothing to clean at $BUILD_DIR"
    }
}

# ── Main ──────────────────────────────────────────────────────────────────────
Write-Host "`nchthonic ruby-zjit Win32 extension builder" -ForegroundColor Magenta
Write-Host "Registry : ruby-zjit/REGISTRY.yaml"
Write-Host "Profile  : ruby-zjit/WIN32_PROFILE.yaml`n"

if ($Clean) {
    Clean-Build
    exit 0
}

# Discover extensions dynamically — any ext/ subdir containing extconf.rb is a target.
# To add a new extension: create ext/<name>/extconf.rb + source, then update REGISTRY.yaml.
$targets = if ($Ext -eq "all") {
    Get-ChildItem -Path $EXT_SRC -Directory -ErrorAction SilentlyContinue |
        Where-Object { Test-Path (Join-Path $_.FullName "extconf.rb") } |
        Select-Object -ExpandProperty Name |
        Sort-Object
} else {
    @($Ext)
}

if ($targets.Count -eq 0 -and $Ext -eq "all") {
    Write-Warn "No ext/ subdirs with extconf.rb found under $EXT_SRC"
}
Write-Host ("Extensions ($($targets.Count)): " + ($targets -join " | ")) + "`n"

$probeResult = Probe-SDKs

if ($Probe) {
    exit 0
}

New-Item -ItemType Directory -Force -Path $BUILD_DIR | Out-Null

$results = @{}
foreach ($t in $targets) {
    $results[$t] = Build-Extension $t
}

Write-Step "Summary"
foreach ($t in $targets) {
    if ($results[$t]) { Write-Ok $t } else { Write-Fail $t }
}

# Exit non-zero if any extension failed
if ($results.Values -contains $false) { exit 1 }
exit 0
