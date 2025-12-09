#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Adds CUDA/cuDNN/TensorRT paths to system PATH permanently.
    
.DESCRIPTION
    This script must be run as Administrator.
    It adds the necessary DLL paths for GPU acceleration to the system PATH.
    
.NOTES
    After running, restart your terminal/VS Code to pick up the new PATH.
#>

Write-Host "🔥💀⚓ GPU PATH SETUP - PERMANENT SYSTEM CONFIGURATION" -ForegroundColor Magenta
Write-Host "=" * 70

$pathsToAdd = @(
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\bin\x64",
    "C:\Program Files\NVIDIA\CUDNN\v9.17\bin\13.1",
    "C:\Program Files\NVIDIA\TensorRT-10.14.1.48\bin"
)

# Verify paths exist
Write-Host "`nVerifying paths exist..." -ForegroundColor Cyan
$allExist = $true
foreach ($p in $pathsToAdd) {
    if (Test-Path $p) {
        Write-Host "  ✅ $p" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $p (NOT FOUND)" -ForegroundColor Red
        $allExist = $false
    }
}

if (-not $allExist) {
    Write-Host "`n❌ Some paths don't exist. Aborting." -ForegroundColor Red
    exit 1
}

# Get current system PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
Write-Host "`nCurrent system PATH has $($currentPath.Split(';').Count) entries"

# Check which paths need to be added
$pathsNeeded = @()
foreach ($p in $pathsToAdd) {
    if ($currentPath -notlike "*$p*") {
        $pathsNeeded += $p
    }
}

if ($pathsNeeded.Count -eq 0) {
    Write-Host "`n✅ All GPU paths already in system PATH!" -ForegroundColor Green
    exit 0
}

Write-Host "`nAdding $($pathsNeeded.Count) paths to system PATH:" -ForegroundColor Yellow
foreach ($p in $pathsNeeded) {
    Write-Host "  + $p" -ForegroundColor Yellow
}

# Add paths
$newPath = $currentPath + ";" + ($pathsNeeded -join ";")
[Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")

Write-Host "`n✅ System PATH updated successfully!" -ForegroundColor Green
Write-Host "`n⚠️  IMPORTANT: Restart your terminal/VS Code to use the new PATH." -ForegroundColor Yellow
Write-Host ""

# Verify
$verifyPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
Write-Host "Verification - new PATH has $($verifyPath.Split(';').Count) entries"
