# @SID: ruby-podman-build
# PURPOSE: Build Ruby 4.0.3 ZJIT+YJIT+Prism+ via Podman (Linux native lane)
# PLATFORM: Win11 → WSL2 podman-machine-default
# STATUS: Podman lane — Linux native, no Win32 ABI constraints
#
# Project root: ruby-zjit/ (self-contained — ext/, scripts/, REGISTRY.yaml, WIN32_PROFILE.yaml)
# Registry    : ruby-zjit/REGISTRY.yaml
# Profile     : ruby-zjit/WIN32_PROFILE.yaml
#
# Usage:
#   pwsh -NoProfile -File ruby-zjit/scripts/build_podman.ps1 [-Build] [-Run] [-Verify] [-Export <path>]
#
# Flags:
#   -Build   : Build the container image from scratch (slow — compiles Ruby from source)
#   -Run     : Start an interactive shell in the built image
#   -Verify  : Run the build-verify.sh script inside the container
#   -Export  : Export the /opt/ruby-zjit prefix to <path> on the Windows host
#   -Pull    : Skip build, pull existing image if available
#
# Source files:
#   ruby-zjit/Containerfile     — build definition (all layers incl. GPU exts)
#   ruby-zjit/build-verify.sh   — post-build verification (graceful GPU probe)
#   ruby-zjit/ext/              — C/C++ extension sources (REGISTRY.yaml is the index)
#
# Context: rv manages Win32 rubies (ruby-4.0.3, ruby-4.0.3-zjit stub)
#   The Podman lane provides a Linux-native ZJIT+Prism build for:
#   - Benchmarking ZJIT without Win32 shape-system bugs
#   - Full devkit (Prism, YJIT, ZJIT all functional under Linux)
#   - Podman container as portable ZJIT devkit

[CmdletBinding()]
param(
    [switch]$Build,
    [switch]$Run,
    [switch]$Verify,
    [string]$Export,
    [switch]$Pull
)

$ErrorActionPreference = 'Stop'

$IMAGE_NAME = "chthonic-ruby-zjit"
$IMAGE_TAG  = "4.0.3"
$WSL_DISTRO = "podman-machine-default"
$CONTAINERFILE = Join-Path $PSScriptRoot ".." "Containerfile"
$VERIFY_SCRIPT = Join-Path $PSScriptRoot ".." "build-verify.sh"

function Invoke-Podman {
    param([string[]]$Args)
    wsl -d $WSL_DISTRO -- podman @Args
    if ($LASTEXITCODE -ne 0) { throw "podman exited $LASTEXITCODE" }
}

function Get-WslPath([string]$WinPath) {
    # Convert Windows path to WSL path
    $drive = $WinPath.Substring(0, 1).ToLower()
    $rest  = $WinPath.Substring(2) -replace '\\', '/'
    return "/mnt/$drive$rest"
}

# Check Podman is available
try {
    $ver = wsl -d $WSL_DISTRO -- podman --version 2>&1
    Write-Host "[ruby-podman] Podman: $ver"
} catch {
    Write-Error "Podman machine '$WSL_DISTRO' is not running. Start with: wsl --distribution $WSL_DISTRO"
    exit 1
}

if ($Build) {
    Write-Host "[ruby-podman] Building $IMAGE_NAME`:$IMAGE_TAG from Containerfile..."
    Write-Host "[ruby-podman] NOTE: This compiles Ruby from source — expect 5-15 minutes."
    $cfWsl = Get-WslPath (Resolve-Path $CONTAINERFILE).Path
    $ctxWsl = Get-WslPath (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    wsl -d $WSL_DISTRO -- podman build -t "${IMAGE_NAME}:${IMAGE_TAG}" -f $cfWsl $ctxWsl
    if ($LASTEXITCODE -ne 0) { Write-Error "Build failed"; exit 1 }
    Write-Host "[ruby-podman] Build complete: ${IMAGE_NAME}:${IMAGE_TAG}"
}

if ($Verify) {
    Write-Host "[ruby-podman] Running build verification..."
    $vsWsl = Get-WslPath (Resolve-Path $VERIFY_SCRIPT).Path
    wsl -d $WSL_DISTRO -- podman run --rm -v "${vsWsl}:/verify.sh:ro" "${IMAGE_NAME}:${IMAGE_TAG}" bash /verify.sh
    Write-Host "[ruby-podman] Verification complete."
}

if ($Export) {
    Write-Host "[ruby-podman] Exporting /opt/ruby-zjit to $Export..."
    $expWsl = Get-WslPath $Export
    wsl -d $WSL_DISTRO -- podman run --rm -v "${expWsl}:/export:rw" "${IMAGE_NAME}:${IMAGE_TAG}" bash -c "cp -r /opt/ruby-zjit/* /export/"
    Write-Host "[ruby-podman] Export complete: $Export"
}

if ($Run) {
    Write-Host "[ruby-podman] Starting interactive shell in ${IMAGE_NAME}:${IMAGE_TAG}..."
    wsl -d $WSL_DISTRO -- podman run --rm -it "${IMAGE_NAME}:${IMAGE_TAG}" bash
}

if (-not ($Build -or $Run -or $Verify -or $Export -or $Pull)) {
    Write-Host @"
[ruby-podman] Ruby 4.0.3 ZJIT+YJIT+Prism Podman Build Lane

  -Build   Build image from source (~5-15 min)
  -Verify  Run verification suite in built image
  -Run     Interactive shell
  -Export  <path>  Copy /opt/ruby-zjit to Windows path

Quick start:
  pwsh -File ruby-zjit/scripts/build_podman.ps1 -Build
  pwsh -File ruby-zjit/scripts/build_podman.ps1 -Verify

Image: ${IMAGE_NAME}:${IMAGE_TAG}
Distro: $WSL_DISTRO
"@
}
