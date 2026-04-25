# @SID: TABBY_PODMAN_BUILD_V1
# PURPOSE: Build + run tabby-modern GPU stack via Podman (Linux/CUDA lane)
# PLATFORM: Win11 → WSL2 Fedora (NVIDIA Workbench) or podman-machine-default
# STATUS: GPU probe lane — resolves G5/G6/G7 without Win32 MSVC surface
#
# FAF: docs/reference/FAF_TABBYAPI_PY314_GPU_INFERENCE_HOST.md
#
# Usage:
#   pwsh -NoProfile -File scripts/tabby_podman_build.ps1 [-Build] [-Probe] [-Run] [-Shell] [-Distro <name>]
#
# Flags:
#   -Build          Build the container image (flash_attn source compile ~10-20 min on Linux GCC)
#   -Probe          Run the full probe ladder (P-07 formatron + P-02 torch CUDA) in built image
#   -ProbeFormatron Run P-07 (formatron cessation gate) only
#   -Run            Run the default CMD (P-07) and stream output
#   -Shell          Interactive shell in built image
#   -Distro <name>  WSL2 distro name (default: podman-machine-default)
#   -NoWsl          Invoke podman directly (native Linux or Podman Desktop on Windows)
#   -ManifestOut    Copy /workspace/manifest/ results back to ./manifest/ after probe run
#
# Gate coverage:
#   G5  exllamav3 cp314 linux_x86_64 — L4 (direct wheel, no source build)
#   G6  flash_attn 2.8.3 source build — GCC path (no MSVC quoting hell)
#   G7  formatron escape-sequence cessation — patched in-container via patch-formatron-escape.py
#   G4  exllamav2 cp314 — still impossible_currently (no turboderp cp314 release as of 2026-04-25)
#
# Image: chthonic-tabby-modern-gpu:latest
# Containerfile: build/tabby-modern-gpu/Containerfile

[CmdletBinding()]
param(
    [switch]$Build,
    [switch]$Probe,
    [switch]$ProbeFormatron,
    [switch]$Run,
    [switch]$Shell,
    [string]$Distro = "podman-machine-default",
    [switch]$NoWsl,
    [switch]$ManifestOut
)

$ErrorActionPreference = 'Stop'

$IMAGE_NAME     = "chthonic-tabby-modern-gpu"
$IMAGE_TAG      = "latest"
$REPO_ROOT      = Resolve-Path (Join-Path $PSScriptRoot "..")
$CONTAINERFILE  = Join-Path $REPO_ROOT "build" "tabby-modern-gpu" "Containerfile"

function Get-WslPath([string]$WinPath) {
    $drive = $WinPath.Substring(0, 1).ToLower()
    $rest  = $WinPath.Substring(2) -replace '\\', '/'
    "/mnt/$drive$rest"
}

function Invoke-Podman {
    param([string[]]$PodmanArgs)
    if ($NoWsl) {
        podman @PodmanArgs
    } else {
        wsl -d $Distro -- podman @PodmanArgs
    }
    if ($LASTEXITCODE -ne 0) { throw "podman exited $LASTEXITCODE" }
}

function ConvertTo-PodmanPath([string]$WinPath) {
    if ($NoWsl) { return $WinPath }
    Get-WslPath $WinPath
}

# --- Preflight: verify podman available ---
try {
    if ($NoWsl) {
        $ver = podman --version 2>&1
    } else {
        $ver = wsl -d $Distro -- podman --version 2>&1
    }
    Write-Host "[tabby-podman] Podman: $ver"
} catch {
    if ($NoWsl) {
        Write-Error "podman not found. Ensure Podman Desktop is installed and in PATH."
    } else {
        Write-Error "WSL2 distro '$Distro' not running or podman not found.`nStart with: wsl --distribution $Distro"
    }
    exit 1
}

# --- Build ---
if ($Build) {
    Write-Host "[tabby-podman] Building ${IMAGE_NAME}:${IMAGE_TAG}..."
    Write-Host "[tabby-podman] Base: nvcr.io/nvidia/cuda:12.8.0-devel-ubi9"
    Write-Host "[tabby-podman] flash_attn source build will take ~10-20 min (GCC, MAX_JOBS=4)"
    Write-Host ""

    $cfPath  = ConvertTo-PodmanPath $CONTAINERFILE
    $ctxPath = ConvertTo-PodmanPath $REPO_ROOT.Path

    if ($NoWsl) {
        podman build --tag "${IMAGE_NAME}:${IMAGE_TAG}" -f $cfPath $ctxPath
    } else {
        wsl -d $Distro -- podman build --tag "${IMAGE_NAME}:${IMAGE_TAG}" -f $cfPath $ctxPath
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Error "[tabby-podman] Build FAILED (exit $LASTEXITCODE)"
        exit 1
    }
    Write-Host "[tabby-podman] Build complete: ${IMAGE_NAME}:${IMAGE_TAG}"
}

# --- Probe ladder (all probes) ---
if ($Probe) {
    Write-Host "[tabby-podman] Running full probe ladder..."

    $probeScript = @"
set -e
echo '=== P-07: formatron cessation gate ==='
python /workspace/probes/python/P-07.py
echo '=== P-02: torch CUDA gate ==='
python /workspace/probes/python/torch_cuda_probe.py
echo '=== P-01: python host identity ==='
python /workspace/probes/python/python_host_probe.py
echo '=== PROBE LADDER COMPLETE ==='
"@

    $gpuFlag = "--device=nvidia.com/gpu=all"

    if ($NoWsl) {
        $result = podman run --rm $gpuFlag "${IMAGE_NAME}:${IMAGE_TAG}" bash -c $probeScript
    } else {
        $result = wsl -d $Distro -- podman run --rm $gpuFlag "${IMAGE_NAME}:${IMAGE_TAG}" bash -c $probeScript
    }

    Write-Host $result

    if ($ManifestOut) {
        Write-Host "[tabby-podman] Copying manifest results from container..."
        $manifestWin = Join-Path $REPO_ROOT "manifest"
        $manifestPod = ConvertTo-PodmanPath $manifestWin

        if ($NoWsl) {
            podman run --rm $gpuFlag -v "${manifestPod}:/workspace/manifest:rw" "${IMAGE_NAME}:${IMAGE_TAG}" bash -c $probeScript
        } else {
            wsl -d $Distro -- podman run --rm $gpuFlag -v "${manifestPod}:/workspace/manifest:rw" "${IMAGE_NAME}:${IMAGE_TAG}" bash -c $probeScript
        }
        Write-Host "[tabby-podman] Manifest results written to: $manifestWin"
        Write-Host "[tabby-podman]   manifest/formatron_cessation_gate.json"
        Write-Host "[tabby-podman]   manifest/cuda_gate.jsonl (if P-02 runs)"
    }
}

# --- Probe: formatron only (P-07) ---
if ($ProbeFormatron) {
    Write-Host "[tabby-podman] Running P-07: formatron cessation gate..."
    $gpuFlag = "--device=nvidia.com/gpu=all"

    if ($ManifestOut) {
        $manifestWin = Join-Path $REPO_ROOT "manifest"
        $manifestPod = ConvertTo-PodmanPath $manifestWin
        if ($NoWsl) {
            podman run --rm -v "${manifestPod}:/workspace/manifest:rw" "${IMAGE_NAME}:${IMAGE_TAG}" `
                python /workspace/probes/python/P-07.py
        } else {
            wsl -d $Distro -- podman run --rm -v "${manifestPod}:/workspace/manifest:rw" `
                "${IMAGE_NAME}:${IMAGE_TAG}" python /workspace/probes/python/P-07.py
        }
    } else {
        if ($NoWsl) {
            podman run --rm "${IMAGE_NAME}:${IMAGE_TAG}" python /workspace/probes/python/P-07.py
        } else {
            wsl -d $Distro -- podman run --rm "${IMAGE_NAME}:${IMAGE_TAG}" python /workspace/probes/python/P-07.py
        }
    }
}

# --- Run default CMD ---
if ($Run) {
    $gpuFlag = "--device=nvidia.com/gpu=all"
    if ($NoWsl) {
        podman run --rm $gpuFlag "${IMAGE_NAME}:${IMAGE_TAG}"
    } else {
        wsl -d $Distro -- podman run --rm $gpuFlag "${IMAGE_NAME}:${IMAGE_TAG}"
    }
}

# --- Interactive shell ---
if ($Shell) {
    $gpuFlag = "--device=nvidia.com/gpu=all"
    Write-Host "[tabby-podman] Starting interactive shell in ${IMAGE_NAME}:${IMAGE_TAG}..."
    if ($NoWsl) {
        podman run --rm -it $gpuFlag "${IMAGE_NAME}:${IMAGE_TAG}" bash
    } else {
        wsl -d $Distro -- podman run --rm -it $gpuFlag "${IMAGE_NAME}:${IMAGE_TAG}" bash
    }
}

# --- Usage (no flags) ---
if (-not ($Build -or $Probe -or $ProbeFormatron -or $Run -or $Shell)) {
    Write-Host @"
[tabby-podman] tabby-modern GPU stack — Podman lane
FAF: docs/reference/FAF_TABBYAPI_PY314_GPU_INFERENCE_HOST.md

  -Build              Build image (flash_attn source compile ~10-20 min)
  -Probe              Run full probe ladder (P-01, P-02, P-07) in image
  -ProbeFormatron     Run P-07 (formatron cessation gate) only
  -Run                Run default CMD (P-07) and stream output
  -Shell              Interactive shell in image
  -ManifestOut        Mount manifest/ volume; copy probe results to host
  -Distro <name>      WSL2 distro (default: $Distro)
  -NoWsl              Skip WSL2 — invoke podman directly (native Fedora)

Gate coverage:
  G5  exllamav3 cp314 linux_x86_64  — L4 (wheel install)
  G6  flash_attn 2.8.3               — L1 (source build, GCC path)
  G7  formatron cessation            — patched by patch-formatron-escape.py
  G4  exllamav2 cp314                — impossible_currently (no cp314 wheel)

Quick start:
  pwsh -File scripts/tabby_podman_build.ps1 -Build
  pwsh -File scripts/tabby_podman_build.ps1 -Probe -ManifestOut
  pwsh -File scripts/tabby_podman_build.ps1 -ProbeFormatron -ManifestOut

Image: ${IMAGE_NAME}:${IMAGE_TAG}
"@
}
