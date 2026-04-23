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
# rv spinel source + docs: https://rv.dev  (Software Version: 0.5.3)
# Ruby path resolution uses: rv ruby find [VERSION]  → canonical per-version path
#
# Ruby selection (same priority order as build_win32.ps1):
#   1. C:\ruby-zjit-build\ruby-4.0.3\ruby.exe  (custom ZJIT source build)
#   2. rv ruby find 4.0.3-zjit                  (rv spinel — canonical zjit path)
#   3. rv ruby find 4.0.3                        (rv spinel — canonical std path)
#   4. ruby (PATH fallback)
#
# -Bench mode: runs each test file twice (direct binary vs rv r ruby) and
#              prints a timing comparison table at the end.

[CmdletBinding()]
param(
    [string[]]$Ext     = @(),
    [switch]  $Verbose,
    [switch]  $List,
    [switch]  $Bench
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Paths ─────────────────────────────────────────────────────────────────────
$ProjectRoot = Split-Path -Parent $PSScriptRoot          # ruby-zjit/
$RepoRoot    = Split-Path -Parent $ProjectRoot           # chthonic-archive/
$TestDir     = Join-Path $ProjectRoot "tests"
$BuildDir    = Join-Path $RepoRoot "build\ruby-zjit-ext-win32"

# ── Ruby selection (rv spinel canonical path resolution — rv.dev) ─────────────
$_rvCmd          = Get-Command rv -ErrorAction SilentlyContinue
$RUBY_ZJIT_BUILD = "C:\ruby-zjit-build\ruby-4.0.3\ruby.exe"

function Find-RubyExe {
    # Tier 1: custom ZJIT source build
    if (Test-Path $RUBY_ZJIT_BUILD) { return $RUBY_ZJIT_BUILD }

    # Tier 2-3: rv ruby find — canonical rv path resolution (rv.dev)
    # rv ruby find <version>  →  installed path for that version label
    if ($_rvCmd) {
        foreach ($ver in @('4.0.3-zjit', '4.0.3')) {
            $p = & rv ruby find $ver 2>$null
            if ($LASTEXITCODE -eq 0 -and $p -and (Test-Path $p)) { return $p }
        }
    }

    # Tier 4: PATH fallback
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
if ($Bench) {
    Write-Host "Mode : -Bench (direct vs rv r ruby speed differential)" -ForegroundColor DarkYellow
}
Write-Host ""

$Pass = 0; $Fail = 0; $Total = 0

# -Bench: collect per-file timing rows
$benchRows = [System.Collections.Generic.List[PSCustomObject]]::new()

foreach ($tf in $AllTests) {
    Write-Host "── $($tf.Name)" -ForegroundColor Cyan

    $allArgs = $LoadArgs + @($tf.FullName)

    if ($Bench -and $_rvCmd) {
        # Direct binary
        $directTimer = [System.Diagnostics.Stopwatch]::StartNew()
        $output = & $RubyBin @allArgs 2>&1
        $directOk   = $LASTEXITCODE -eq 0
        $directTimer.Stop()
        $directMs = $directTimer.ElapsedMilliseconds

        # rv r ruby — rv spinel invocation path
        # rv run ruby <args> : sets PATH via pinned .ruby-version, then executes ruby
        $rvTimer = [System.Diagnostics.Stopwatch]::StartNew()
        $rvOut = & rv r ruby @allArgs 2>&1
        $rvOk   = $LASTEXITCODE -eq 0
        $rvTimer.Stop()
        $rvMs = $rvTimer.ElapsedMilliseconds

        $delta = $rvMs - $directMs
        $deltaStr = ($delta -ge 0 ? "+${delta}" : "$delta") + "ms"
        $benchRows.Add([PSCustomObject]@{
            Test    = $tf.Name
            DirectMs = $directMs
            RvMs     = $rvMs
            Delta    = $delta
            DeltaStr = $deltaStr
        })

        Write-Host ("  direct: {0}ms  rv r: {1}ms  Δ {2}" -f $directMs, $rvMs, $deltaStr) -ForegroundColor DarkYellow
        $output = if ($directOk) { $output } else { $rvOut }
        $ok = $directOk -or $rvOk
    } else {
        $output = & $RubyBin @allArgs 2>&1
        $ok     = $LASTEXITCODE -eq 0
    }

    if ($ok) {
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

# ── Bench Report ──────────────────────────────────────────────────────────────
if ($Bench -and $benchRows.Count -gt 0) {
    Write-Host ""
    Write-Host "── Speed Differential (direct binary vs rv r ruby) ──────────────────────────" -ForegroundColor DarkYellow
    $benchRows | Format-Table -Property Test,
        @{Label='Direct (ms)'; Expression={$_.DirectMs}; Align='Right'},
        @{Label='rv r (ms)';   Expression={$_.RvMs};     Align='Right'},
        @{Label='Delta';       Expression={$_.DeltaStr}; Align='Right'} -AutoSize
    $avgDelta = ($benchRows | Measure-Object -Property Delta -Average).Average
    Write-Host ("  avg rv overhead: {0:N1}ms per test file" -f $avgDelta) -ForegroundColor DarkYellow
    Write-Host "  (overhead = rv process startup + .ruby-version resolution + PATH injection)" -ForegroundColor DarkGray
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
$color = $Fail -gt 0 ? 'Red' : 'Green'
Write-Host "══ $Pass/$($Pass + $Fail) test files passed | ~$Total Minitest runs ══" -ForegroundColor $color
exit ($Fail -gt 0 ? 1 : 0)
