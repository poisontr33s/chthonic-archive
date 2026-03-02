#!/usr/bin/env pwsh
# ═══════════════════════════════════════════════════════════════════════════════
# purge-claude-bun.ps1 - Remove bun/npm Claude Code artifacts, install native
# Run this OUTSIDE of Claude Code (from a fresh pwsh terminal)
# ═══════════════════════════════════════════════════════════════════════════════

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Test-ClaudeShim {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )
    if (-not (Test-Path $Path)) { return $false }
    try {
        $item = Get-Item -LiteralPath $Path
        # Bun/npm shim executables are tiny stubs; native installer binary is ~hundreds of MB.
        return $item.Length -lt 1MB
    } catch {
        return $false
    }
}

Write-Host "`n=== Claude Code: Bun/npm Purge & Native Install ===" -ForegroundColor Cyan

# ─── Step 1: Kill any running claude processes ───
Write-Host "`n[1/6] Stopping claude processes..." -ForegroundColor Yellow
Get-Process -Name 'claude*' -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  Killing: $($_.ProcessName) (PID $($_.Id))"
    Stop-Process -Id $_.Id -Force
}

# ─── Step 2: Remove shim claude.exe from ~/.local/bin (if present) ───
Write-Host "`n[2/6] Removing shim claude.exe from ~/.local/bin (if present)..." -ForegroundColor Yellow
$localClaude = Join-Path $env:USERPROFILE ".local\bin\claude.exe"
if (Test-Path $localClaude) {
    $item = Get-Item -LiteralPath $localClaude
    if (Test-ClaudeShim -Path $localClaude) {
        Remove-Item $localClaude -Force
        Write-Host "  Removed shim: $localClaude ($($item.Length) bytes)" -ForegroundColor Green
    } else {
        Write-Host "  SKIP: $localClaude looks like native binary ($([math]::Round($item.Length/1MB,2)) MB)" -ForegroundColor Green
    }
} else {
    Write-Host "  Not found, skipping" -ForegroundColor DarkGray
}

# ─── Step 3: Remove stale npm shims + package ───
Write-Host "`n[3/6] Removing npm claude shims and package..." -ForegroundColor Yellow
$npmDir = Join-Path $env:APPDATA "npm"
@("claude", "claude.cmd", "claude.ps1") | ForEach-Object {
    $p = Join-Path $npmDir $_
    if (Test-Path $p) {
        Remove-Item $p -Force
        Write-Host "  Removed: $p" -ForegroundColor Green
    }
}
$npmPkg = Join-Path $npmDir "node_modules\@anthropic-ai\claude-code"
if (Test-Path $npmPkg) {
    Remove-Item $npmPkg -Recurse -Force
    Write-Host "  Removed: $npmPkg (~94MB)" -ForegroundColor Green
    # Clean up empty parent if @anthropic-ai is now empty
    $parentDir = Split-Path $npmPkg
    if ((Test-Path $parentDir) -and @(Get-ChildItem $parentDir).Count -eq 0) {
        Remove-Item $parentDir -Force
        Write-Host "  Removed empty: $parentDir" -ForegroundColor Green
    }
}

# ─── Step 4: Remove bun global claude install (if any) ───
Write-Host "`n[4/6] Checking bun global installs for claude..." -ForegroundColor Yellow
$bunGlobal = Join-Path $env:USERPROFILE ".bun\install\global"
if (Test-Path $bunGlobal) {
    $bunClaudeLinks = Get-ChildItem $bunGlobal -Recurse -Filter "*claude*" -ErrorAction SilentlyContinue
    foreach ($f in $bunClaudeLinks) {
        Write-Host "  Found bun global artifact: $($f.FullName)"
    }
    # Check for claude in bun's global node_modules
    $bunClaudePkg = Join-Path $bunGlobal "node_modules\@anthropic-ai\claude-code"
    if (Test-Path $bunClaudePkg) {
        Remove-Item $bunClaudePkg -Recurse -Force
        Write-Host "  Removed: $bunClaudePkg" -ForegroundColor Green
    }
} else {
    Write-Host "  No bun global dir found" -ForegroundColor DarkGray
}

# ─── Step 5: Install native Claude Code ───
Write-Host "`n[5/6] Installing native Claude Code via irm..." -ForegroundColor Yellow
Write-Host "  Running: irm https://claude.ai/install.ps1 | iex" -ForegroundColor Cyan
try {
    irm https://claude.ai/install.ps1 | iex
    Write-Host "  Native install complete" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Native install failed: $_" -ForegroundColor Red
    Write-Host "  Try manually: irm https://claude.ai/install.ps1 | iex" -ForegroundColor Yellow
}

# ─── Step 6: Verify ───
Write-Host "`n[6/6] Verifying installation..." -ForegroundColor Yellow
$claudePath = Join-Path $env:USERPROFILE ".local\bin\claude.exe"
if (Test-Path $claudePath) {
    $item = Get-Item -LiteralPath $claudePath
    $info = (Get-Command $claudePath).FileVersionInfo
    $version = & $claudePath --version 2>&1
    Write-Host "  Path:         $claudePath" -ForegroundColor Green
    Write-Host "  Version:      $version" -ForegroundColor Green
    Write-Host "  Size:         $([math]::Round($item.Length/1MB,2)) MB" -ForegroundColor Green
    Write-Host "  InternalName: $($info.InternalName)" -ForegroundColor Green
    if (Test-ClaudeShim -Path $claudePath) {
        Write-Host "  WARNING: claude.exe still looks like a shim (tiny binary)." -ForegroundColor Red
        Write-Host "  Re-run this script, then verify: where.exe claude" -ForegroundColor Yellow
    } else {
        Write-Host "  SUCCESS: Native self-contained binary confirmed (embedded runtime is expected)." -ForegroundColor Green
    }
} else {
    Write-Host "  WARNING: claude.exe not found at $claudePath" -ForegroundColor Red
    Write-Host "  The installer may have placed it elsewhere. Check:" -ForegroundColor Yellow
    Write-Host "    where.exe claude" -ForegroundColor Yellow
}

Write-Host "`n=== Done. Restart your terminal before using claude. ===" -ForegroundColor Cyan
Write-Host "  If PATH is missing, run:" -ForegroundColor DarkGray
Write-Host '  [Environment]::SetEnvironmentVariable("PATH", "$([Environment]::GetEnvironmentVariable(''PATH'', ''User''));$env:USERPROFILE\.local\bin", "User")' -ForegroundColor DarkGray
Write-Host ""
