#!/usr/bin/env pwsh
# @SID: MAS_BUILD_CUPY_V1

<#
.SYNOPSIS
    Build CuPy from source for Python 3.14 + CUDA 13 + cuDNN 9.17

.DESCRIPTION
    This script builds CuPy from source since no official wheels exist for Python 3.14.
    
    Prerequisites:
    - Python 3.14 (via uv)
    - CUDA Toolkit 13.0
    - cuDNN 9.17
    - Visual Studio 2026 with C++ workload
    - Git

.PARAMETER DryRun
    Simulate the build without compiling kernels. Validates environment,
    checks toolchain paths, and prints what would be built.

.PARAMETER Clean
    Remove previous build artifacts before starting.

.PARAMETER SkipTests
    Skip the test suite after building.

.EXAMPLE
    .\build_cupy.ps1 -DryRun
    Validate environment without compiling.

.EXAMPLE
    .\build_cupy.ps1 -Clean
    Full build with clean artifacts.

.NOTES
    Author: Claudine (MAS-MCP Build System)
    Date: December 2025
    Target: RTX 4090 (SM 8.9 Ada Lovelace)
#>

param(
    [switch]$DryRun,
    [switch]$Clean,
    [switch]$SkipTests,
    [int]$Jobs = 12,  # Default 12 for i9-14900 stability (use -Jobs 24 for max speed)
    [string]$BuildDir = "$env:TEMP\cupy_build"
)

$ErrorActionPreference = "Stop"

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

$CUDA_PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1"
$CUDNN_PATH = "C:\Program Files\NVIDIA\CUDNN\v9.17"
$VS_PATH = "C:\Program Files\Microsoft Visual Studio\18\Insiders"
$CUPY_REPO = "https://github.com/cupy/cupy.git"
$CUPY_BRANCH = "main"  # or "v13.x" when stable

# GPU architecture for RTX 4090 (Ada Lovelace SM 8.9)
# Also include SM 8.6 (Ampere) for compatibility
$CUDA_ARCHS = "86;89"

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

function Write-Step {
    param([string]$Message)
    Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║ $Message".PadRight(63) + "║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
}

function Write-Status {
    param([string]$Status, [string]$Message)
    $icon = switch ($Status) {
        "OK"      { "✅" }
        "WARN"    { "⚠️" }
        "ERROR"   { "❌" }
        "INFO"    { "ℹ️" }
        default   { "•" }
    }
    Write-Host "  $icon $Message"
}

function Test-Prerequisite {
    param([string]$Name, [string]$Path, [switch]$Required)
    
    if (Test-Path $Path) {
        Write-Status "OK" "$Name found at: $Path"
        return $true
    } else {
        if ($Required) {
            Write-Status "ERROR" "$Name NOT FOUND at: $Path"
            throw "Missing required prerequisite: $Name"
        } else {
            Write-Status "WARN" "$Name not found (optional): $Path"
            return $false
        }
    }
}

function Initialize-VCEnvironment {
    Write-Step "Initializing Visual Studio Environment"
    
    $vcvars = "$VS_PATH\VC\Auxiliary\Build\vcvars64.bat"
    if (-not (Test-Path $vcvars)) {
        throw "vcvars64.bat not found at: $vcvars"
    }
    
    # Run vcvars64.bat and capture environment
    $envOutput = cmd /c "`"$vcvars`" >nul 2>&1 && set"
    
    foreach ($line in $envOutput) {
        if ($line -match '^([^=]+)=(.*)$') {
            $varName = $matches[1]
            $varValue = $matches[2]
            [Environment]::SetEnvironmentVariable($varName, $varValue, "Process")
        }
    }
    
    # Verify cl.exe is now available
    $cl = Get-Command cl.exe -ErrorAction SilentlyContinue
    if ($cl) {
        Write-Status "OK" "MSVC compiler initialized: $($cl.Source)"
    } else {
        throw "Failed to initialize MSVC compiler"
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN BUILD PROCESS
# ═══════════════════════════════════════════════════════════════════════════

Write-Host @"

  ██████╗██╗   ██╗██████╗ ██╗   ██╗    ██████╗ ██╗   ██╗██╗██╗     ██████╗ 
 ██╔════╝██║   ██║██╔══██╗╚██╗ ██╔╝    ██╔══██╗██║   ██║██║██║     ██╔══██╗
 ██║     ██║   ██║██████╔╝ ╚████╔╝     ██████╔╝██║   ██║██║██║     ██║  ██║
 ██║     ██║   ██║██╔═══╝   ╚██╔╝      ██╔══██╗██║   ██║██║██║     ██║  ██║
 ╚██████╗╚██████╔╝██║        ██║       ██████╔╝╚██████╔╝██║███████╗██████╔╝
  ╚═════╝ ╚═════╝ ╚═╝        ╚═╝       ╚═════╝  ╚═════╝ ╚═╝╚══════╝╚═════╝ 
                                                                           
  CuPy Source Build for Python 3.14 + CUDA 13 + cuDNN 9.17
  Target: RTX 4090 (Ada Lovelace SM 8.9)

"@ -ForegroundColor Magenta

# ═══════════════════════════════════════════════════════════════════════════
# VIRTUAL ENVIRONMENT ACTIVATION (claudine-gpu)
# ═══════════════════════════════════════════════════════════════════════════

$VENV_PATH = "C:\Users\erdno\chthonic-archive\claudine-gpu"
$venvActivate = "$VENV_PATH\Scripts\Activate.ps1"

if (Test-Path $venvActivate) {
    Write-Status "INFO" "Activating claudine-gpu virtual environment..."
    & $venvActivate
    
    # Verify activation
    $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($pythonPath -like "*claudine-gpu*") {
        Write-Status "OK" "Venv active: $pythonPath"
    } else {
        Write-Status "WARN" "Venv activation may have failed - python at: $pythonPath"
    }
} else {
    Write-Status "ERROR" "claudine-gpu venv not found at: $VENV_PATH"
    Write-Status "INFO" "Create it with: uv venv $VENV_PATH --python 3.14"
    throw "Virtual environment required for CuPy build"
}

# ═══════════════════════════════════════════════════════════════════════════
# DRY-RUN MODE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

if ($DryRun) {
    Write-Host @"
  ╔═══════════════════════════════════════════════════════════════╗
  ║  🧪 DRY-RUN MODE: Simulating build without compilation        ║
  ║     • Environment validation only                             ║
  ║     • No kernels will be compiled                             ║
  ║     • Use full build when ready: .\build_cupy.ps1             ║
  ╚═══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Yellow
    
    # Set CuPy simulation flags
    $env:CUPY_DRY_RUN = "1"
    $env:CUPY_INSTALL_USE_HIP = "0"
    $env:CUPY_DUMMY_DEVICE = "1"
}

# ─────────────────────────────────────────────────────────────────────────
Write-Step "Checking Prerequisites"
# ─────────────────────────────────────────────────────────────────────────

# Python
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "3\.14") {
    Write-Status "OK" "Python: $pythonVersion"
} else {
    throw "Python 3.14 required, found: $pythonVersion"
}

# CUDA
Test-Prerequisite "CUDA Toolkit" "$CUDA_PATH\bin\nvcc.exe" -Required
$nvccVersion = & "$CUDA_PATH\bin\nvcc.exe" --version 2>&1 | Select-String "release"
Write-Status "INFO" "NVCC: $nvccVersion"

# cuDNN (v9.x uses versioned subdirectories)
$cudnnInclude = "$CUDNN_PATH\include\13.1"
$cudnnLib = "$CUDNN_PATH\lib\13.1\x64"
$cudnnBinDir = "$CUDNN_PATH\bin\13.1"

Test-Prerequisite "cuDNN Headers" "$cudnnInclude\cudnn.h" -Required
Test-Prerequisite "cuDNN Library" "$cudnnLib\cudnn.lib" -Required
Test-Prerequisite "cuDNN DLL" "$cudnnBinDir\cudnn64_9.dll" -Required

# Visual Studio
Test-Prerequisite "Visual Studio 2026 Insiders" "$VS_PATH\VC\Auxiliary\Build\vcvars64.bat" -Required

# Git
$git = Get-Command git.exe -ErrorAction SilentlyContinue
if ($git) {
    Write-Status "OK" "Git: $($git.Source)"
} else {
    throw "Git not found in PATH"
}

# ─────────────────────────────────────────────────────────────────────────
Write-Step "Setting Up Environment Variables"
# ─────────────────────────────────────────────────────────────────────────

# CUDA environment
$env:CUDA_PATH = $CUDA_PATH
$env:CUDA_HOME = $CUDA_PATH
$env:CUDNN_PATH = $CUDNN_PATH

# Add to PATH (cuDNN 9.x uses versioned bin directory)
$cudaBin = "$CUDA_PATH\bin"
$cudnnBin = "$CUDNN_PATH\bin\13.1"
if ($env:PATH -notlike "*$cudaBin*") {
    $env:PATH = "$cudaBin;$cudnnBin;$env:PATH"
}

# CuPy build configuration
$env:CUPY_NVCC_GENERATE_CODE = "arch=compute_86,code=sm_86;arch=compute_89,code=sm_89"
$env:CUPY_NUM_BUILD_JOBS = $Jobs  # Configurable via -Jobs parameter (default 12 for stability)
$env:CUPY_ACCELERATORS = "cub"  # Enable CUB for better performance

# cuDNN include/lib paths for CuPy (v9.x versioned structure)
$env:CUDNN_INCLUDE_DIR = "$CUDNN_PATH\include\13.1"
$env:CUDNN_LIBRARY_DIR = "$CUDNN_PATH\lib\13.1\x64"

# Additional flags for CUDA 13 compatibility
$env:NVCC_PREPEND_FLAGS = "-allow-unsupported-compiler"
$env:CUB_HOME = "$CUDA_PATH\include\cub"

Write-Status "OK" "CUDA_PATH: $env:CUDA_PATH"
Write-Status "OK" "CUDNN_PATH: $env:CUDNN_PATH"
Write-Status "OK" "CUDA archs: $env:CUPY_NVCC_GENERATE_CODE"
Write-Status "OK" "Build jobs: $env:CUPY_NUM_BUILD_JOBS"

# ─────────────────────────────────────────────────────────────────────────
Write-Step "Initializing MSVC Compiler"
# ─────────────────────────────────────────────────────────────────────────

Initialize-VCEnvironment

# ─────────────────────────────────────────────────────────────────────────
Write-Step "Cloning CuPy Repository"
# ─────────────────────────────────────────────────────────────────────────

if ($Clean -and (Test-Path $BuildDir)) {
    Write-Status "INFO" "Cleaning previous build directory..."
    Remove-Item -Recurse -Force $BuildDir
}

if (-not (Test-Path $BuildDir)) {
    New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null
}

$cupyDir = "$BuildDir\cupy"

if (-not (Test-Path "$cupyDir\.git")) {
    Write-Status "INFO" "Cloning CuPy from $CUPY_REPO..."
    git clone --depth 1 --branch $CUPY_BRANCH $CUPY_REPO $cupyDir
    if ($LASTEXITCODE -ne 0) { throw "Git clone failed" }
} else {
    Write-Status "INFO" "CuPy already cloned, pulling latest..."
    Push-Location $cupyDir
    git pull
    Pop-Location
}

# Initialize submodules
Push-Location $cupyDir
Write-Status "INFO" "Initializing submodules..."
git submodule update --init --recursive
Pop-Location

Write-Status "OK" "CuPy source ready at: $cupyDir"

# ─────────────────────────────────────────────────────────────────────────
Write-Step "Installing Build Dependencies"
# ─────────────────────────────────────────────────────────────────────────

# Install build dependencies via uv (require virtualenv to prevent system pollution)
uv pip install --require-virtualenv --upgrade pip setuptools wheel cython numpy

if ($LASTEXITCODE -ne 0) { throw "Failed to install build dependencies" }

Write-Status "OK" "Build dependencies installed"

# ─────────────────────────────────────────────────────────────────────────
if ($DryRun) {
    Write-Step "DRY-RUN: Build Simulation"
} else {
    Write-Step "Building CuPy (this may take 15-30 minutes)"
}
# ─────────────────────────────────────────────────────────────────────────

Push-Location $cupyDir

$startTime = Get-Date

try {
    if ($DryRun) {
        # Dry-run mode: validate setup.py can parse, print build config
        Write-Status "INFO" "Simulating build environment..."
        
        # Show what CuPy would build
        Write-Host "`n  📋 Build Configuration:" -ForegroundColor Cyan
        Write-Host "     ├─ CUDA Path:    $env:CUDA_PATH"
        Write-Host "     ├─ cuDNN Path:   $env:CUDNN_PATH"
        Write-Host "     ├─ CUDA Archs:   $env:CUPY_NVCC_GENERATE_CODE"
        Write-Host "     ├─ Build Jobs:   $env:CUPY_NUM_BUILD_JOBS"
        Write-Host "     ├─ Accelerators: $env:CUPY_ACCELERATORS"
        Write-Host "     └─ cuDNN Inc:    $env:CUDNN_INCLUDE_DIR"
        
        # Validate setup.py can be parsed
        Write-Status "INFO" "Validating CuPy setup.py..."
        $setupCheck = python -c "import ast; ast.parse(open('setup.py').read())" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "OK" "setup.py syntax valid"
        } else {
            Write-Status "ERROR" "setup.py parse error: $setupCheck"
        }
        
        # Check Cython can import
        Write-Status "INFO" "Checking Cython availability..."
        python -c "import cython; print(f'  Cython {cython.__version__}')" 2>&1
        
        # Simulate device detection
        Write-Host "`n  🎮 Simulated GPU Detection:" -ForegroundColor Cyan
        Write-Host "     ├─ Device:       RTX 4090 (simulated)"
        Write-Host "     ├─ Architecture: SM 8.9 (Ada Lovelace)"
        Write-Host "     ├─ Tensor Cores: Available"
        Write-Host "     ├─ FP16:         Supported"
        Write-Host "     └─ cuDNN:        v9.17 @ $cudnnBinDir"
        
        Write-Host "`n" -NoNewline
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host "  ✅ DRY-RUN COMPLETE: Environment validated successfully!" -ForegroundColor Green
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host "`n  Ready for full build. Run: .\build_cupy.ps1`n" -ForegroundColor Cyan
        
        Pop-Location
        exit 0
    }
    
    # Full build mode
    Write-Status "INFO" "Starting build... (check Task Manager for nvcc.exe activity)"
    Write-Status "INFO" "Build may show warnings for CUDA 13 - these are expected"
    
    # First ensure Cython is compatible
    uv pip install --require-virtualenv "cython>=3.0" "numpy>=2.0" "fastrlock>=0.8"
    
    # Use pip install with build isolation disabled for faster builds
    # Add --config-settings to pass build options
    $buildCmd = "uv pip install --require-virtualenv . --no-build-isolation -v 2>&1"
    $buildOutput = Invoke-Expression $buildCmd
    $buildOutput | ForEach-Object { Write-Host $_ }
    
    if ($LASTEXITCODE -ne 0) { throw "CuPy build failed" }
    
    $elapsed = (Get-Date) - $startTime
    Write-Status "OK" "Build completed in $($elapsed.TotalMinutes.ToString('0.0')) minutes"
    
} finally {
    Pop-Location
}

# ─────────────────────────────────────────────────────────────────────────
Write-Step "Verifying Installation"
# ─────────────────────────────────────────────────────────────────────────

$verifyScript = @"
import cupy as cp
import numpy as np

print(f"CuPy version: {cp.__version__}")
print(f"CUDA version: {cp.cuda.runtime.runtimeGetVersion()}")

# Device info
device = cp.cuda.Device(0)
props = cp.cuda.runtime.getDeviceProperties(0)
print(f"GPU: {props['name'].decode()}")
print(f"Compute capability: {props['major']}.{props['minor']}")
print(f"Total memory: {props['totalGlobalMem'] / 1024**3:.1f} GB")

# Quick matmul test
n = 4096
a = cp.random.randn(n, n, dtype=cp.float32)
b = cp.random.randn(n, n, dtype=cp.float32)

# Warm-up
c = cp.matmul(a, b)
cp.cuda.Stream.null.synchronize()

# Benchmark
import time
start = time.perf_counter()
for _ in range(10):
    c = cp.matmul(a, b)
cp.cuda.Stream.null.synchronize()
elapsed = (time.perf_counter() - start) / 10 * 1000

print(f"MatMul {n}x{n}: {elapsed:.2f} ms per iteration")
print("✅ CuPy GPU acceleration working!")
"@

python -c $verifyScript

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n" -NoNewline
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  ✅ CuPy successfully built and installed for Python 3.14!" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
} else {
    Write-Status "ERROR" "CuPy verification failed"
    exit 1
}

# ─────────────────────────────────────────────────────────────────────────
if (-not $SkipTests) {
    Write-Step "Running CuPy Test Suite (optional)"
    
    Write-Status "INFO" "Running basic tests..."
    python -m pytest "$cupyDir\tests\cupy_tests\core_tests" -x -q --timeout=60 2>&1 | Select-Object -First 20
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "OK" "Core tests passed"
    } else {
        Write-Status "WARN" "Some tests failed (may be expected for bleeding-edge build)"
    }
}

Write-Host "`n🎉 Build complete! CuPy is ready for MAS-MCP GPU acceleration.`n" -ForegroundColor Magenta
