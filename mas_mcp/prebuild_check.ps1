#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Pre-build validation for CuPy source build environment

.DESCRIPTION
    Checks all prerequisites before starting the 15-30 minute CuPy build.
    Run this first to catch any missing components.
#>

$ErrorActionPreference = "Stop"

Write-Host @"

  ╔═══════════════════════════════════════════════════════════════
  ║     CuPy Build Environment Pre-Check                         ║
  ║     Python 3.14 + CUDA 13 + cuDNN 9.17 + MSVC 2022           ║
  ╚═══════════════════════════════════════════════════════════════

"@ -ForegroundColor Cyan

$allPassed = $true

function Check-Item {
    param([string]$Name, [string]$Path, [switch]$Required)

    $exists = Test-Path $Path
    $icon = if ($exists) { "✅" } elseif ($Required) { "❌" } else { "⚠️" }
    $status = if ($exists) { "Found" } else { "MISSING" }

    Write-Host "  $icon $Name : $status"
    if ($exists) {
        Write-Host "     └─ $Path" -ForegroundColor DarkGray
    }

    if (-not $exists -and $Required) {
        $script:allPassed = $false
    }
    return $exists
}

# ─────────────────────────────────────────────────────────────────────────
Write-Host "`n📦 Python Environment" -ForegroundColor Yellow
# ─────────────────────────────────────────────────────────────────────────

$pyVersion = python --version 2>&1
if ($pyVersion -match "3\.14") {
    Write-Host "  ✅ Python: $pyVersion"
} else {
    Write-Host "  ❌ Python 3.14 required, found: $pyVersion"
    $allPassed = $false
}

# Check uv
$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) {
    $uvVersion = uv --version
    Write-Host "  ✅ uv: $uvVersion"
} else {
    Write-Host "  ❌ uv not found in PATH"
    $allPassed = $false
}

# ─────────────────────────────────────────────────────────────────────────
Write-Host "`n🔧 CUDA Toolkit 13" -ForegroundColor Yellow
# ─────────────────────────────────────────────────────────────────────────

$cudaPath = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0"
Check-Item "CUDA nvcc.exe" "$cudaPath\bin\nvcc.exe" -Required
Check-Item "CUDA include" "$cudaPath\include\cuda.h" -Required
Check-Item "CUDA lib" "$cudaPath\lib\x64\cudart.lib" -Required

if (Test-Path "$cudaPath\bin\nvcc.exe") {
    $nvccVer = & "$cudaPath\bin\nvcc.exe" --version 2>&1 | Select-String "release"
    Write-Host "     └─ $nvccVer" -ForegroundColor DarkGray
}

# ─────────────────────────────────────────────────────────────────────────
Write-Host "`n🧠 cuDNN 9.17" -ForegroundColor Yellow
# ─────────────────────────────────────────────────────────────────────────

$cudnnPath = "C:\Program Files\NVIDIA\CUDNN\v9.17"
Check-Item "cuDNN headers" "$cudnnPath\include\13.1\cudnn.h" -Required
Check-Item "cuDNN lib" "$cudnnPath\lib\13.1\x64\cudnn.lib" -Required
Check-Item "cuDNN DLL" "$cudnnPath\bin\13.1\cudnn64_9.dll" -Required

# ─────────────────────────────────────────────────────────────────────────
Write-Host "`n🛠️ Visual Studio 2022" -ForegroundColor Yellow
# ─────────────────────────────────────────────────────────────────────────

$vsPath = "C:\Program Files\Microsoft Visual Studio\2022\Community"
Check-Item "VS2022 vcvars64.bat" "$vsPath\VC\Auxiliary\Build\vcvars64.bat" -Required
Check-Item "MSVC cl.exe" "$vsPath\VC\Tools\MSVC" -Required

# Test MSVC initialization
Write-Host "`n  Testing MSVC environment initialization..."
$vcvars = "$vsPath\VC\Auxiliary\Build\vcvars64.bat"
if (Test-Path $vcvars) {
    $testCmd = cmd /c "`"$vcvars`" >nul 2>&1 && where cl.exe 2>nul"
    if ($testCmd) {
        Write-Host "  ✅ MSVC compiler can be initialized"
        Write-Host "     └─ $($testCmd | Select-Object -First 1)" -ForegroundColor DarkGray
    } else {
        Write-Host "  ❌ MSVC initialization failed"
        $allPassed = $false
    }
}

# ─────────────────────────────────────────────────────────────────────────
Write-Host "`n📚 Git" -ForegroundColor Yellow
# ─────────────────────────────────────────────────────────────────────────

$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
    Write-Host "  ✅ Git: $(git --version)"
} else {
    Write-Host "  ❌ Git not found in PATH"
    $allPassed = $false
}

# ─────────────────────────────────────────────────────────────────────────
Write-Host "`n🎮 GPU Information" -ForegroundColor Yellow
# ─────────────────────────────────────────────────────────────────────────

$nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvidiaSmi) {
    $gpuInfo = nvidia-smi --query-gpu=name,compute_cap,memory.total --format=csv,noheader 2>$null
    if ($gpuInfo) {
        Write-Host "  ✅ GPU detected:"
        Write-Host "     └─ $gpuInfo" -ForegroundColor DarkGray

        # Check for Ada Lovelace (SM 8.9)
        if ($gpuInfo -match "4090|4080|4070|Ada") {
            Write-Host "  ✅ Ada Lovelace architecture (SM 8.9) - optimal for build" -ForegroundColor Green
        }
    }
} else {
    Write-Host "  ⚠️ nvidia-smi not found (GPU check skipped)"
}

# ─────────────────────────────────────────────────────────────────────────
Write-Host "`n📊 Build Dependencies" -ForegroundColor Yellow
# ─────────────────────────────────────────────────────────────────────────

$deps = @("cython", "numpy", "setuptools", "wheel")
foreach ($dep in $deps) {
    $installed = python -c "import $dep; print($dep.__version__)" 2>$null
    if ($installed) {
        Write-Host "  ✅ $dep : $installed"
    } else {
        Write-Host "  ⚠️ $dep : not installed (will be installed during build)"
    }
}

# ─────────────────────────────────────────────────────────────────────────
Write-Host "`n" -NoNewline
if ($allPassed) {
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  ✅ All prerequisites satisfied! Ready to build CuPy." -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "`n  Run: .\build_cupy.ps1`n" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "  ❌ Some prerequisites are missing. Please fix before building." -ForegroundColor Red
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "`n  See above for missing components.`n" -ForegroundColor Yellow
    exit 1
}
