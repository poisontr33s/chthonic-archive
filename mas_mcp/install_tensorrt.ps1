#!/usr/bin/env pwsh
# @SID: MAS_INSTALL_TENSORRT_V1
<#
.SYNOPSIS
    Install and configure TensorRT SDK for CUDA 13 + cuDNN 9.17

.DESCRIPTION
    This script validates TensorRT installation, configures PATH, and verifies
    ONNXRuntime can use TensorRT as an execution provider.
    
    Prerequisites:
    - CUDA Toolkit 13.0
    - cuDNN 9.17
    - TensorRT SDK 10.x (must be downloaded manually from NVIDIA)

.PARAMETER TensorRTPath
    Path to TensorRT installation directory.

.PARAMETER Validate
    Only validate existing installation, don't modify PATH.

.PARAMETER AddToProfile
    Add TensorRT to PowerShell profile for persistent PATH.

.EXAMPLE
    .\install_tensorrt.ps1 -Validate
    Check if TensorRT is already installed and working.

.EXAMPLE
    .\install_tensorrt.ps1 -TensorRTPath "C:\Program Files\NVIDIA\TensorRT-10.8.0.43"
    Configure TensorRT at the specified path.

.NOTES
    Author: Claudine (MAS-MCP Build System)
    Date: December 2025
    Target: CUDA 13 + cuDNN 9.17 + TensorRT 10.x
#>

param(
    [string]$TensorRTPath = "",
    [switch]$Validate,
    [switch]$AddToProfile
)

$ErrorActionPreference = "Stop"

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

$CUDA_PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0"
$CUDNN_PATH = "C:\Program Files\NVIDIA\CUDNN\v9.17"

# Common TensorRT installation locations to search
$TENSORRT_SEARCH_PATHS = @(
    "C:\Program Files\NVIDIA\TensorRT-10*",
    "C:\TensorRT-10*",
    "$env:USERPROFILE\TensorRT-10*",
    "D:\TensorRT-10*"
)

# Required DLLs for TensorRT 10.x
$REQUIRED_DLLS = @(
    "nvinfer_10.dll",
    "nvinfer_plugin_10.dll",
    "nvonnxparser_10.dll"
)

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

function Write-Step {
    param([string]$Message)
    Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║ $($Message.PadRight(62))║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
}

function Write-Status {
    param([string]$Status, [string]$Message)
    $icon = switch ($Status) {
        "OK"      { "✅" }
        "WARN"    { "⚠️" }
        "ERROR"   { "❌" }
        "INFO"    { "ℹ️" }
        "SEARCH"  { "🔍" }
        default   { "•" }
    }
    Write-Host "  $icon $Message"
}

function Find-TensorRT {
    Write-Step "Searching for TensorRT Installation"
    
    # First check if already in PATH
    $nvinfer = Get-Command nvinfer_10.dll -ErrorAction SilentlyContinue
    if ($nvinfer) {
        $libPath = Split-Path $nvinfer.Source -Parent
        $rootPath = Split-Path $libPath -Parent
        Write-Status "OK" "TensorRT found in PATH: $rootPath"
        return $rootPath
    }
    
    # Search common locations
    foreach ($pattern in $TENSORRT_SEARCH_PATHS) {
        Write-Status "SEARCH" "Checking: $pattern"
        # Resolve wildcard patterns to actual directories
        $parentDir = Split-Path $pattern -Parent
        $searchPattern = Split-Path $pattern -Leaf
        if (Test-Path $parentDir) {
            $found = Get-ChildItem -Path $parentDir -Filter $searchPattern -ErrorAction SilentlyContinue | 
                     Where-Object { $_.PSIsContainer } |
                     Sort-Object Name -Descending | 
                     Select-Object -First 1
            
            if ($found -and (Test-Path "$($found.FullName)\lib\nvinfer_10.dll")) {
                Write-Status "OK" "TensorRT found: $($found.FullName)"
                return $found.FullName
            }
        }
    }
    
    Write-Status "WARN" "TensorRT not found in common locations"
    return $null
}

function Test-TensorRTInstallation {
    param([string]$Path)
    
    Write-Step "Validating TensorRT Installation"
    
    $valid = $true
    $libPath = "$Path\lib"
    $includePath = "$Path\include"
    
    # Check lib directory
    if (-not (Test-Path $libPath)) {
        Write-Status "ERROR" "lib directory not found: $libPath"
        return $false
    }
    
    # Check required DLLs
    foreach ($dll in $REQUIRED_DLLS) {
        $dllPath = "$libPath\$dll"
        if (Test-Path $dllPath) {
            $version = (Get-Item $dllPath).VersionInfo.FileVersion
            Write-Status "OK" "$dll (v$version)"
        } else {
            Write-Status "ERROR" "$dll NOT FOUND"
            $valid = $false
        }
    }
    
    # Check include directory
    if (Test-Path "$includePath\NvInfer.h") {
        Write-Status "OK" "NvInfer.h header found"
    } else {
        Write-Status "WARN" "NvInfer.h not found (may affect compilation)"
    }
    
    # Check CUDA compatibility
    Write-Status "INFO" "Checking CUDA compatibility..."
    if (Test-Path "$CUDA_PATH\bin\nvcc.exe") {
        $nvccVersion = & "$CUDA_PATH\bin\nvcc.exe" --version 2>&1 | Select-String "release"
        Write-Status "OK" "CUDA: $nvccVersion"
    }
    
    # Check cuDNN compatibility
    if (Test-Path "$CUDNN_PATH\bin\13.1\cudnn64_9.dll") {
        Write-Status "OK" "cuDNN 9.17 found"
    }
    
    return $valid
}

function Add-TensorRTToPath {
    param([string]$Path)
    
    $libPath = "$Path\lib"
    
    # Add to current session
    if ($env:PATH -notlike "*$libPath*") {
        $env:PATH = "$libPath;$env:PATH"
        Write-Status "OK" "Added to current session PATH"
    } else {
        Write-Status "INFO" "Already in current PATH"
    }
    
    # Verify DLL is now findable
    $nvinfer = Get-Command nvinfer_10.dll -ErrorAction SilentlyContinue
    if ($nvinfer) {
        Write-Status "OK" "nvinfer_10.dll now accessible"
    } else {
        Write-Status "ERROR" "nvinfer_10.dll still not accessible after PATH update"
        return $false
    }
    
    return $true
}

function Add-TensorRTToProfile {
    param([string]$Path)
    
    Write-Step "Adding TensorRT to PowerShell Profile"
    
    $libPath = "$Path\lib"
    $profilePath = $PROFILE.CurrentUserAllHosts
    $profileDir = Split-Path $profilePath -Parent
    
    # Create profile directory if needed
    if (-not (Test-Path $profileDir)) {
        New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    }
    
    # Check if already in profile
    if (Test-Path $profilePath) {
        $content = Get-Content $profilePath -Raw
        if ($content -match "TensorRT") {
            Write-Status "INFO" "TensorRT already configured in profile"
            return
        }
    }
    
    # Add to profile
    $snippet = @"

# ═══════════════════════════════════════════════════════════════════════════
# TensorRT SDK Configuration (Added by install_tensorrt.ps1)
# ═══════════════════════════════════════════════════════════════════════════
`$env:TENSORRT_PATH = "$Path"
`$env:PATH = "`$env:TENSORRT_PATH\lib;`$env:PATH"
"@
    
    Add-Content -Path $profilePath -Value $snippet
    Write-Status "OK" "Added to profile: $profilePath"
    Write-Status "INFO" "Restart PowerShell or run: . `$PROFILE"
}

function Test-ONNXRuntimeProviders {
    Write-Step "Testing ONNXRuntime Execution Providers"
    
    $pythonScript = @"
import sys
try:
    import onnxruntime as ort
    providers = ort.get_available_providers()
    print("Available providers:")
    for p in providers:
        status = "✅" if p in ['TensorrtExecutionProvider', 'CUDAExecutionProvider'] else "•"
        print(f"  {status} {p}")
    
    if 'TensorrtExecutionProvider' in providers:
        print("\n🚀 TensorRT provider available!")
        sys.exit(0)
    elif 'CUDAExecutionProvider' in providers:
        print("\n⚠️ CUDA available but TensorRT not detected")
        sys.exit(1)
    else:
        print("\n❌ No GPU providers available")
        sys.exit(2)
except ImportError as e:
    print(f"❌ ONNXRuntime not installed: {e}")
    sys.exit(3)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(4)
"@
    
    $result = python -c $pythonScript 2>&1
    $result | ForEach-Object { Write-Host "  $_" }
    
    return $LASTEXITCODE -eq 0
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

Write-Host @"

 ████████╗███████╗███╗   ██╗███████╗ ██████╗ ██████╗ ██████╗ ████████╗
 ╚══██╔══╝██╔════╝████╗  ██║██╔════╝██╔═══██╗██╔══██╗██╔══██╗╚══██╔══╝
    ██║   █████╗  ██╔██╗ ██║███████╗██║   ██║██████╔╝██████╔╝   ██║   
    ██║   ██╔══╝  ██║╚██╗██║╚════██║██║   ██║██╔══██╗██╔══██╗   ██║   
    ██║   ███████╗██║ ╚████║███████║╚██████╔╝██║  ██║██║  ██║   ██║   
    ╚═╝   ╚══════╝╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   
                                                                       
  TensorRT SDK Installation & Validation
  Target: CUDA 13.0 + cuDNN 9.17 + TensorRT 10.x

"@ -ForegroundColor Magenta

# Find or use provided TensorRT path
$tensorrtPath = $TensorRTPath
if (-not $tensorrtPath) {
    $tensorrtPath = Find-TensorRT
}

if (-not $tensorrtPath) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "  ❌ TensorRT SDK Not Found" -ForegroundColor Red
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host ""
    Write-Host "  TensorRT must be downloaded manually from NVIDIA:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. Go to: https://developer.nvidia.com/tensorrt" -ForegroundColor Cyan
    Write-Host "  2. Download TensorRT 10.x for Windows (CUDA 12.x compatible)" -ForegroundColor Cyan
    Write-Host "  3. Extract to: C:\Program Files\NVIDIA\TensorRT-10.x.x.x" -ForegroundColor Cyan
    Write-Host "  4. Re-run: .\install_tensorrt.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Or specify path directly:" -ForegroundColor Yellow
    Write-Host "  .\install_tensorrt.ps1 -TensorRTPath 'C:\path\to\TensorRT'" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

# Validate installation
$isValid = Test-TensorRTInstallation -Path $tensorrtPath

if (-not $isValid) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "  ❌ TensorRT Installation Invalid" -ForegroundColor Red
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
    exit 1
}

if ($Validate) {
    # Just validate, don't modify anything
    Write-Step "Validation Complete"
    
    # Test if already in PATH
    $nvinfer = Get-Command nvinfer_10.dll -ErrorAction SilentlyContinue
    if ($nvinfer) {
        Write-Status "OK" "TensorRT already in PATH"
        Test-ONNXRuntimeProviders
    } else {
        Write-Status "WARN" "TensorRT found but not in PATH"
        Write-Host ""
        Write-Host "  Run without -Validate to configure PATH:" -ForegroundColor Yellow
        Write-Host "  .\install_tensorrt.ps1 -TensorRTPath '$tensorrtPath'" -ForegroundColor Cyan
    }
    exit 0
}

# Add to PATH
Write-Step "Configuring PATH"
$pathOk = Add-TensorRTToPath -Path $tensorrtPath

if (-not $pathOk) {
    exit 1
}

# Add to profile if requested
if ($AddToProfile) {
    Add-TensorRTToProfile -Path $tensorrtPath
}

# Test ONNXRuntime
$onnxOk = Test-ONNXRuntimeProviders

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ TensorRT Configuration Complete!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  TensorRT Path: $tensorrtPath" -ForegroundColor Cyan
Write-Host ""

if (-not $AddToProfile) {
    Write-Host "  ⚠️ PATH changes are session-only. To persist:" -ForegroundColor Yellow
    Write-Host "  .\install_tensorrt.ps1 -TensorRTPath '$tensorrtPath' -AddToProfile" -ForegroundColor Cyan
    Write-Host ""
}

if (-not $onnxOk) {
    Write-Host "  ⚠️ ONNXRuntime TensorRT provider not yet available." -ForegroundColor Yellow
    Write-Host "  You may need to install onnxruntime-gpu with TensorRT support:" -ForegroundColor Yellow
    Write-Host "  uv pip install onnxruntime-gpu" -ForegroundColor Cyan
    Write-Host ""
}
