#!/usr/bin/env pwsh

# ╔════════════════════════════════════════════════════════════════════════════
# ║ Nightly Daemon Launcher
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Semantic ID: SCRIPT_RUN_NIGHTLY_V1
# ║ Purpose: Run local-only overnight analysis before sleep — zero API calls
# ║ Flags: -Background -WithLLM -WithHF -Local -LocalCoder -LocalHeavy -Genre
# ║ Cross-References:
# ║ scripts/overnight_daemon.ts        (debt/complexity scorer, local)
# ║ meta-ide/copilot-sdk/overnight-archaeology.ts  (file archaeology)
# ╚════════════════════════════════════════════════════════════════════════════

[CmdletBinding()]
param(
  [switch]$Background,    # Detach processes (run while you sleep)
  [switch]$WithLLM,       # Opt-in: Copilot SDK Loop 2 (costs ~14 haiku calls from YOUR quota)
  [switch]$WithHF,        # Opt-in: HuggingFace open-source LLM refinement (free, separate pool)
  [switch]$Local,         # Opt-in: Local GPU inference (Qwen3-30B-A3B abliterated, default)
  [switch]$LocalV2,       # Opt-in: Force v2 refiner (same as -Local, kept for compatibility)
  [switch]$LocalCoder,    # Opt-in: Qwen3-Coder-30B-A3B abliterated (code-focused)
  [switch]$LocalHeavy,    # Opt-in: GPT-OSS-20B dense model (Harmony parser)
  [switch]$Genre,          # Opt-in: Genre extraction on creative content (local GPU)
  [switch]$DryRun,        # Preview without writing
  [switch]$SkipDaemon,    # Skip the debt/complexity daemon
  [switch]$SkipArchaeology, # Skip the file archaeology scavenge
  [int]$Top = 20,         # Top N candidates for daemon
  [int]$MaxTodo = 80      # Max TODO hits for daemon
)

$ErrorActionPreference = 'Stop'

$repoRoot   = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$bunExe     = Join-Path $env:USERPROFILE '.bun\bin\bun.exe'
$stamp      = Get-Date -Format 'yyyy-MM-ddTHH-mm-ss'
$runFailures = [System.Collections.Generic.List[string]]::new()

if (-not (Test-Path -LiteralPath $bunExe)) {
  throw "Bun not found at '$bunExe'. Install Bun or adjust path."
}

$logDir = Join-Path $repoRoot "dumpster-dive\intake\overnight-intelligence"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

# ── Retention: keep last 7 runs, prune older ─────────────────────────────
function Invoke-RetentionPrune {
  param([string]$Dir, [int]$Keep = 7)
  if (-not (Test-Path $Dir)) { return }
  $dirs = Get-ChildItem -Path $Dir -Directory | Sort-Object Name -Descending
  if ($dirs.Count -le $Keep) { return }
  $stale = $dirs | Select-Object -Skip $Keep
  foreach ($d in $stale) {
    Remove-Item -LiteralPath $d.FullName -Recurse -Force -ErrorAction SilentlyContinue
  }
  Write-Host "  Pruned $($stale.Count) old runs from $(Split-Path $Dir -Leaf)" -ForegroundColor DarkGray
}

$daemonDir = Join-Path $repoRoot "dumpster-dive\intake\overnight-daemon"
if ($DryRun) {
  Write-Host '  ☥ Retention prune: skipped in dry-run mode.' -ForegroundColor DarkGray
} else {
  Invoke-RetentionPrune -Dir $daemonDir -Keep 7
  Invoke-RetentionPrune -Dir $logDir    -Keep 7
}

function Invoke-ExternalStep {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Label,

    [Parameter(Mandatory = $true)]
    [scriptblock]$Body
  )

  $global:LASTEXITCODE = 0
  try {
    & $Body
  } catch {
    $runFailures.Add("$Label failed: $($_.Exception.Message)")
    return
  }

  if ($LASTEXITCODE -ne 0) {
    $runFailures.Add("$Label failed with exit code $LASTEXITCODE")
  }
}

function Assert-UvModuleAvailable {
  param(
    [Parameter(Mandatory = $true)]
    [string]$UvExe,

    [Parameter(Mandatory = $true)]
    [string]$ModuleName,

    [Parameter(Mandatory = $true)]
    [string]$InstallHint
  )

  $global:LASTEXITCODE = 0
  & $UvExe run python -c "import $ModuleName" 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "Python module '$ModuleName' is missing. Install it with: $InstallHint"
  }
}

Write-Host '' -ForegroundColor DarkGray
Write-Host '╔══════════════════════════════════════════════════════╗' -ForegroundColor DarkYellow
Write-Host '║  ☥ NIGHTLY DAEMON — Local Computation, Zero API     ║' -ForegroundColor DarkYellow
Write-Host '╚══════════════════════════════════════════════════════╝' -ForegroundColor DarkYellow
Write-Host ''

# ── 1. Overnight Daemon (debt scores, complexity, patterns) ──────────────

if (-not $SkipDaemon) {
  if ($DryRun) {
    Write-Host '  ☥ Daemon: dry-run mode requested; skipping write-heavy daemon stage.' -ForegroundColor DarkYellow
    Write-Host '    (Use without -DryRun to generate daemon report artifacts.)' -ForegroundColor DarkGray
  } else {
  $daemonScript = Join-Path $repoRoot 'scripts\overnight_daemon.ts'
  if (-not (Test-Path -LiteralPath $daemonScript)) {
    Write-Host '  ⚠ overnight_daemon.ts not found — skipping' -ForegroundColor Yellow
  } else {
    $daemonArgs = @('run', $daemonScript, '--top', $Top, '--maxTodo', $MaxTodo)

    if ($Background) {
      $daemonLog = Join-Path $logDir "daemon-$stamp.log"
      Write-Host "  ☥ Daemon: debt scoring + complexity analysis (background)" -ForegroundColor Green
      Write-Host "    Log: $daemonLog" -ForegroundColor DarkGray
      Start-Process -FilePath $bunExe `
        -ArgumentList $daemonArgs `
        -WorkingDirectory $repoRoot `
        -RedirectStandardOutput $daemonLog `
        -RedirectStandardError ($daemonLog -replace '\.log$', '.err.log') `
        -WindowStyle Hidden
    } else {
      Write-Host '  ☥ Daemon: debt scoring + complexity analysis...' -ForegroundColor Green
      Invoke-ExternalStep -Label "Overnight daemon" -Body { & $bunExe @daemonArgs }
    }
  }
  }
}

# ── 2. Archaeology Scavenge (file walk + gold tier classification) ───────

if (-not $SkipArchaeology) {
  $archScript = Join-Path $repoRoot 'meta-ide\copilot-sdk\overnight-archaeology.ts'
  $archWork   = Join-Path $repoRoot 'meta-ide\copilot-sdk'
  if (-not (Test-Path -LiteralPath $archScript)) {
    Write-Host '  ⚠ overnight-archaeology.ts not found — skipping' -ForegroundColor Yellow
  } else {
    $archArgs = @('run', $archScript)

    if ($WithLLM) {
      Write-Host '  ☥ Archaeology: full run (Loop 1 + Loop 2 LLM refinement)' -ForegroundColor Magenta
      Write-Host '    ⚠ This uses ~14-22 Copilot API calls (claude-haiku-4.5)' -ForegroundColor Yellow
    } else {
      $archArgs += '--loop=1'
      Write-Host '  ☥ Archaeology: scavenge only (Loop 1, zero API)' -ForegroundColor Green
    }
    if ($DryRun) { $archArgs += '--dry-run' }

    if ($Background) {
      $archLog = Join-Path $logDir "archaeology-$stamp.log"
      Write-Host "    Log: $archLog" -ForegroundColor DarkGray
      Start-Process -FilePath $bunExe `
        -ArgumentList $archArgs `
        -WorkingDirectory $archWork `
        -RedirectStandardOutput $archLog `
        -RedirectStandardError ($archLog -replace '\.log$', '.err.log') `
        -WindowStyle Hidden
    } else {
      Push-Location $archWork
      try {
        Invoke-ExternalStep -Label "Archaeology scavenge" -Body { & $bunExe @archArgs }
      } finally {
        Pop-Location
      }
    }
  }
}

# ── 3. HF Refiner (open-source LLM, separate API pool) ──────────────────

if ($WithHF) {
  $hfScript = Join-Path $repoRoot 'scripts\hf_refiner.py'
  $uvExe    = Join-Path $env:USERPROFILE '.local\bin\uv.exe'
  if (-not (Test-Path -LiteralPath $uvExe)) {
    # Fallback: try uv on PATH
    $uvExe = 'uv'
  }
  if (-not (Test-Path -LiteralPath $hfScript)) {
    Write-Host '  ⚠ hf_refiner.py not found — skipping' -ForegroundColor Yellow
  } else {
    Write-Host '  ☥ HF Refiner: open-source LLM refinement (free API, not your quota)' -ForegroundColor Cyan
    $hfArgs = @('run', $hfScript)
    if ($DryRun) { $hfArgs += '--dry-run' }

    if ($Background) {
      $hfLog = Join-Path $logDir "hf-refiner-$stamp.log"
      Write-Host "    Log: $hfLog" -ForegroundColor DarkGray
      Start-Process -FilePath $uvExe `
        -ArgumentList $hfArgs `
        -WorkingDirectory $repoRoot `
        -RedirectStandardOutput $hfLog `
        -RedirectStandardError ($hfLog -replace '\.log$', '.err.log') `
        -WindowStyle Hidden
    } else {
      Push-Location $repoRoot
      try {
        Invoke-ExternalStep -Label "HF refiner" -Body { & $uvExe @hfArgs }
      } finally {
        Pop-Location
      }
    }
  }
}

# ── 4. Local Refiner (GPU inference, zero network) ──────────────────────

if ($Local -or $LocalV2 -or $LocalCoder -or $LocalHeavy) {
  $v2Script    = Join-Path $repoRoot 'scripts\local_refiner_v2.py'
  $uvExe       = Join-Path $env:USERPROFILE '.local\bin\uv.exe'
  if (-not (Test-Path -LiteralPath $uvExe)) { $uvExe = 'uv' }

  $localScript = $v2Script
  if ($LocalCoder) {
    $refinerLabel = 'Qwen3-Coder-30B-A3B abliterated (code-focused, uncensored)'
  } elseif ($LocalHeavy) {
    $refinerLabel = 'GPT-OSS-20B dense (Harmony parser, uncensored)'
  } else {
    $refinerLabel = 'Qwen3-30B-A3B Instruct abliterated (default, uncensored)'
  }

  if (-not (Test-Path -LiteralPath $localScript)) {
    Write-Host "  ⚠ $($localScript | Split-Path -Leaf) not found — skipping" -ForegroundColor Yellow
  } else {
    Write-Host "  ☥ Local Refiner: $refinerLabel (zero network, zero cost)" -ForegroundColor Green
    $localArgs = @('run', $localScript)
    if ($LocalCoder) { $localArgs += '--coder' }
    if ($LocalHeavy) { $localArgs += '--heavy' }
    if ($DryRun) { $localArgs += '--dry-run' }

    if ($Background) {
      $localLog = Join-Path $logDir "local-refiner-$stamp.log"
      Write-Host "    Log: $localLog" -ForegroundColor DarkGray
      Start-Process -FilePath $uvExe `
        -ArgumentList $localArgs `
        -WorkingDirectory $repoRoot `
        -RedirectStandardOutput $localLog `
        -RedirectStandardError ($localLog -replace '\.log$', '.err.log') `
        -WindowStyle Hidden
    } else {
      Push-Location $repoRoot
      $canRunLocal = $true
      $localScriptName = Split-Path -Leaf $localScript
      if ($localScriptName -eq 'local_refiner_v2.py') {
        try {
          Assert-UvModuleAvailable `
            -UvExe $uvExe `
            -ModuleName "llama_cpp" `
            -InstallHint "uv add --dev llama-cpp-python"
        } catch {
          $runFailures.Add("Local refiner preflight failed: $($_.Exception.Message)")
          $canRunLocal = $false
        }
      }

      try {
        if ($canRunLocal) {
          Invoke-ExternalStep -Label "Local refiner" -Body { & $uvExe @localArgs }
        }
      } finally {
        Pop-Location
      }
    }
  }
}

# ── 5. Genre Extractor (creative content analysis, local GPU) ────────────

if ($Genre) {
  $genreScript = Join-Path $repoRoot 'scripts\genre_extractor.py'
  $uvExe       = Join-Path $env:USERPROFILE '.local\bin\uv.exe'
  if (-not (Test-Path -LiteralPath $uvExe)) { $uvExe = 'uv' }

  if (-not (Test-Path -LiteralPath $genreScript)) {
    Write-Host '  ⚠ genre_extractor.py not found — skipping' -ForegroundColor Yellow
  } else {
    Write-Host '  ☥ Genre Extractor: creative content analysis (local GPU, uncensored)' -ForegroundColor Magenta
    $genreArgs = @('run', $genreScript)
    if ($LocalCoder) { $genreArgs += '--coder' }
    if ($DryRun)     { $genreArgs += '--dry-run' }

    Push-Location $repoRoot
    try {
      Invoke-ExternalStep -Label "Genre extractor" -Body { & $uvExe @genreArgs }
    } finally {
      Pop-Location
    }
  }
}

# ── Summary ──────────────────────────────────────────────────────────────

Write-Host ''
Write-Host '  ────────────────────────────────────────────────────' -ForegroundColor DarkGray
if (-not $Background -and $runFailures.Count -gt 0) {
  Write-Host '  ☥ Nightly run completed with errors:' -ForegroundColor Red
  foreach ($failure in $runFailures) {
    Write-Host "    - $failure" -ForegroundColor Yellow
  }
  Write-Host ''
  exit 1
}

if ($Background) {
  Write-Host '  ☥ Daemons detached. Check in the morning:' -ForegroundColor Green
  Write-Host '    Daemon reports:      dumpster-dive\intake\overnight-daemon\' -ForegroundColor DarkGray
  Write-Host '    Archaeology ore:     dumpster-dive\intake\overnight-intelligence\' -ForegroundColor DarkGray
  if ($WithLLM -or $WithHF -or $Local -or $LocalV2) {
    Write-Host '    LLM digest:          claude\mailbox\ARCHAEOLOGY_DIGEST_*.md' -ForegroundColor DarkGray
  }
  Write-Host ''
  exit 0
} else {
  Write-Host '  ☥ Nightly run complete.' -ForegroundColor Green
  Write-Host ''
  exit 0
}
