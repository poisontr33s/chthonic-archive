#!/usr/bin/env pwsh
#Requires -Version 7.0
# @SID: ruby-zjit-test-win32
# E2E Minitest runner for ruby-zjit native GPU extensions on Win32.
# Runs tests against extensions built by build_win32.ps1 in build/ruby-zjit-ext-win32/.
#
# Project root: ruby-zjit/ (self-contained — tests/, ext/, scripts/)
# Registry    : ruby-zjit/REGISTRY.yaml
# Profile     : ruby-zjit/WIN32_PROFILE.yaml
#
# Usage:
#   .\ruby-zjit\scripts\test_win32.ps1              # Run all extension tests
#   .\ruby-zjit\scripts\test_win32.ps1 -Ext cuda_rb # Run specific extension(s)
#   .\ruby-zjit\scripts\test_win32.ps1 -Verbose     # Show full Minitest output
#   .\ruby-zjit\scripts\test_win32.ps1 -List        # List available test files
#
# Ruby selection (same priority order as build_win32.ps1):
#   1. C:\ruby-zjit-build\ruby-4.0.3\ruby.exe  (custom ZJIT source build)
#   2. %APPDATA%\rv\rubies\ruby-4.0.3-zjit\bin\ruby.exe
#   3. %APPDATA%\rv\rubies\ruby-4.0.3\bin\ruby.exe   ← safest (no ZJIT+Prism crash)
#   4. ruby (PATH fallback)

[CmdletBinding()]
param(
    [string[]]$Ext     = @(),
    [switch]  $Verbose,
    [switch]  $List
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Paths ─────────────────────────────────────────────────────────────────────
$ProjectRoot = Split-Path -Parent $PSScriptRoot          # ruby-zjit/
$RepoRoot    = Split-Path -Parent $ProjectRoot           # chthonic-archive/
$TestDir     = Join-Path $ProjectRoot "tests"
$BuildDir    = Join-Path $RepoRoot "build\ruby-zjit-ext-win32"

# ── Ruby selection (mirrors build_win32.ps1 Find-RubyExe priority) ────────────
function Find-RubyExe {
    $candidates = @(
        "C:\ruby-zjit-build\ruby-4.0.3\ruby.exe",
        (Join-Path $env:APPDATA "rv\rubies\ruby-4.0.3-zjit\bin\ruby.exe"),
        (Join-Path $env:APPDATA "rv\rubies\ruby-4.0.3\bin\ruby.exe")
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }
    # PATH fallback
    $r = Get-Command ruby -ErrorAction SilentlyContinue
    return $r ? $r.Source : $null
}

$RubyBin = Find-RubyExe
if (-not $RubyBin) {
    Write-Host "✗ No ruby.exe found. Run build_win32.ps1 first, or install rv." -ForegroundColor Red
    exit 1
}

# ── Load paths from built extension directories ────────────────────────────────
$LoadArgs = @()
if (Test-Path $BuildDir) {
    foreach ($dir in (Get-ChildItem -Path $BuildDir -Directory)) {
        $LoadArgs += "-I"
        $LoadArgs += $dir.FullName
    }
}

if ($LoadArgs.Count -eq 0) {
    Write-Host "! No built extensions found at $BuildDir" -ForegroundColor Yellow
    Write-Host "  Run .\ruby-zjit\scripts\build_win32.ps1 first." -ForegroundColor Yellow
    # Do not exit — tests may still run if extensions are on the system gem path
}

# ── Select test files ─────────────────────────────────────────────────────────
if (-not (Test-Path $TestDir)) {
    Write-Host "✗ Test directory not found: $TestDir" -ForegroundColor Red
    exit 1
}

$AllTests = Get-ChildItem -Path $TestDir -Filter "test_*.rb" | Sort-Object Name

if ($Ext.Count -gt 0) {
    $AllTests = $AllTests | Where-Object {
        $basename = $_.BaseName  # e.g. "test_cuda_rb"
        $Ext | Where-Object { $basename -eq "test_${_}" -or $basename -like "test_${_}_*" } |
               Select-Object -First 1
    }
}

if ($List) {
    Write-Host "`nAvailable test files:" -ForegroundColor Cyan
    $AllTests | ForEach-Object { Write-Host "  $($_.Name)" }
    Write-Host ""
    exit 0
}

if (-not $AllTests) {
    Write-Host "No test files matched." -ForegroundColor Yellow
    exit 0
}

# ── Run ───────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Ruby : $RubyBin" -ForegroundColor DarkGray
Write-Host "Build: $BuildDir" -ForegroundColor DarkGray
Write-Host "Tests: $TestDir" -ForegroundColor DarkGray
Write-Host ""

$Pass = 0; $Fail = 0; $Total = 0

foreach ($tf in $AllTests) {
    Write-Host "── $($tf.Name)" -ForegroundColor Cyan

    $allArgs = $LoadArgs + @($tf.FullName)
    $output  = & $RubyBin @allArgs 2>&1

    if ($LASTEXITCODE -eq 0) {
        $Pass++
        $summary = ($output | Select-String '^\d+ runs' | Select-Object -Last 1)
        if ($summary) {
            Write-Host "  ✓ $($summary.Line.Trim())" -ForegroundColor Green
        } else {
            Write-Host "  ✓ passed" -ForegroundColor Green
        }
        if ($Verbose) {
            $output | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
        }
    } else {
        $Fail++
        Write-Host "  ✗ FAILED" -ForegroundColor Red
        $output | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
    }

    # Count total runs/assertions from Minitest output
    $runLine = $output | Select-String '(\d+) runs, (\d+) assertions' | Select-Object -Last 1
    if ($runLine) {
        $m = $runLine.Line | Select-String '(\d+) runs'
        $Total += [int]$m.Matches[0].Groups[1].Value
    }
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
$color = $Fail -gt 0 ? 'Red' : 'Green'
Write-Host "══ $Pass/$($Pass + $Fail) test files passed | ~$Total Minitest runs ══" -ForegroundColor $color
exit ($Fail -gt 0 ? 1 : 0)
