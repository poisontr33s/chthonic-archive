#!/usr/bin/env pwsh
#
# @SID: SCRIPT_DESKTOP_WARMUP_V1
# @Type: UTILITY
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Post-pull desktop environment warmup for the Chthonic Archive.
#
<#
.SYNOPSIS
  Post-pull desktop environment warmup for the Chthonic Archive.

.WHY
  After git-pull on the desktop (4090 / 25GB VRAM / 64GB RAM), the environment
  needs uv sync, API pool loading, MCP config regeneration, and verification.
  This script automates that sequence as a single idempotent command.

.USAGE
  pwsh -NoProfile -File scripts/desktop-warmup.ps1
  pwsh -NoProfile -File scripts/desktop-warmup.ps1 -SkipPull
  pwsh -NoProfile -File scripts/desktop-warmup.ps1 -SkipVerify
  pwsh -NoProfile -File scripts/desktop-warmup.ps1 -DryRun

.STEPS
  1. git pull (unless -SkipPull)
  2. uv sync --extra poe --extra openai --extra hf --extra analysis
  3. Load API pool into process env
  4. Persist API pool to Windows User env (registry-backed)
  5. Regenerate .mcp.json from pool
  6. Verify: Poe auth, HF auth (unless -SkipVerify)
#>

param(
  [switch]$SkipPull,
  [switch]$SkipVerify,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repoRoot
$stepNum = 0

function Write-Step {
  param([string]$Message)
  $script:stepNum++
  Write-Host -ForegroundColor Cyan "[$script:stepNum] $Message"
}

function Write-Ok {
  param([string]$Message)
  Write-Host -ForegroundColor Green "    OK: $Message"
}

function Write-Fail {
  param([string]$Message)
  Write-Host -ForegroundColor Red "    FAIL: $Message"
}

function Write-Skip {
  param([string]$Message)
  Write-Host -ForegroundColor Yellow "    SKIP: $Message"
}

$errors = @()

try {
  Write-Host ""
  Write-Host -ForegroundColor Magenta "=== Chthonic Desktop Warmup ==="
  Write-Host ""

  # --- Step 1: git pull ---
  Write-Step "git pull"
  if ($SkipPull) {
    Write-Skip "SkipPull flag set"
  } elseif ($DryRun) {
    Write-Skip "DryRun — would run: git pull"
  } else {
    $pullOut = git pull 2>&1
    if ($LASTEXITCODE -eq 0) {
      Write-Ok ($pullOut | Select-Object -First 2 | Out-String).Trim()
    } else {
      Write-Fail "git pull failed: $pullOut"
      $errors += "git pull"
    }
  }

  # --- Step 2: uv sync ---
  Write-Step "uv sync --extra poe --extra openai --extra hf --extra analysis"
  if ($DryRun) {
    Write-Skip "DryRun — would run: uv sync --extra poe --extra openai --extra hf --extra analysis"
  } else {
    $syncOut = uv sync --extra poe --extra openai --extra hf --extra analysis 2>&1
    if ($LASTEXITCODE -eq 0) {
      Write-Ok "uv sync complete"
    } else {
      Write-Fail "uv sync failed"
      $errors += "uv sync"
      Write-Host ($syncOut | Out-String)
    }
  }

  # --- Step 3: Load API pool ---
  Write-Step "Load API pool into process env"
  if ($DryRun) {
    Write-Skip "DryRun — would source: scripts/api_pool.ps1 -Load -Quiet"
  } else {
    try {
      . "$repoRoot/scripts/api_pool.ps1" -Load -Quiet
      Write-Ok "API pool loaded"
    } catch {
      Write-Fail "api_pool.ps1 failed: $_"
      $errors += "api_pool"
    }
  }

  # --- Step 4: Persist to User env ---
  Write-Step "Persist API pool to Windows User environment"
  if ($DryRun) {
    Write-Skip "DryRun — would run: api_pool_persist_user_env.ps1 -Apply"
  } else {
    try {
      pwsh -NoProfile -File "$repoRoot/scripts/api_pool_persist_user_env.ps1" -Apply
      Write-Ok "User env persisted"
    } catch {
      Write-Fail "persist failed: $_"
      $errors += "persist_env"
    }
  }

  # --- Step 5: Regenerate .mcp.json ---
  Write-Step "Regenerate .mcp.json from API pool"
  if ($DryRun) {
    Write-Skip "DryRun — would run: claude_ide.ps1 write-mcp"
  } else {
    try {
      pwsh -NoProfile -File "$repoRoot/scripts/claude_ide.ps1" write-mcp -GitHubMode copilot
      Write-Ok ".mcp.json regenerated (copilot mode)"
    } catch {
      Write-Fail "write-mcp failed: $_"
      $errors += "write_mcp"
    }
  }

  # --- Step 6: Verify lanes ---
  Write-Step "Verify: Poe auth + HF auth"
  if ($SkipVerify) {
    Write-Skip "SkipVerify flag set"
  } elseif ($DryRun) {
    Write-Skip "DryRun — would verify Poe and HF auth"
  } else {
    # Poe verification
    try {
      $poeOut = uv run scripts/poe_lane.py --mode auth 2>&1
      if ($LASTEXITCODE -eq 0) {
        Write-Ok "Poe auth verified"
      } else {
        Write-Fail "Poe auth: $poeOut"
        $errors += "poe_auth"
      }
    } catch {
      Write-Fail "Poe auth check threw: $_"
      $errors += "poe_auth"
    }

    # HF verification
    try {
      $hfOut = uv run scripts/hf_probe.py 2>&1
      if ($LASTEXITCODE -eq 0) {
        Write-Ok "HF auth verified"
      } else {
        Write-Fail "HF auth: $hfOut"
        $errors += "hf_auth"
      }
    } catch {
      Write-Fail "HF auth check threw: $_"
      $errors += "hf_auth"
    }
  }

  # --- Summary ---
  Write-Host ""
  if ($errors.Count -eq 0) {
    Write-Host -ForegroundColor Green "=== Warmup complete — all steps passed ==="
  } else {
    Write-Host -ForegroundColor Red "=== Warmup complete — $($errors.Count) step(s) failed: $($errors -join ', ') ==="
  }
  Write-Host ""

} finally {
  Pop-Location
}

exit $errors.Count
