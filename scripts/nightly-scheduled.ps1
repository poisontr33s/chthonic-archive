#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Wrapper for Windows Task Scheduler — runs the nightly archaeology daemon.
  
  @SID:   SCRIPT_NIGHTLY_SCHEDULED_V1
  @Type:  Launcher

.DESCRIPTION
  Called by Task Scheduler at 04:00 CET. Runs the focused local pipeline:
  daemon + genre extraction (markdown-first), with archaeology/classification
  stage skipped by default to reduce JSON artifact churn.
  
  Logs to: dumpster-dive/intake/overnight-daemon/
  Digest:  claude/mailbox/ARCHAEOLOGY_DIGEST_*.md

.NOTES
  Register with (hidden window, no popup):
    schtasks /Create /TN "ChthonicNightly" /TR "pwsh -NoProfile -WindowStyle Hidden -File C:\Users\erdno\chthonic-archive\scripts\nightly-scheduled.ps1" /SC DAILY /ST 03:00 /F

  03:00 UTC = 04:00 CET (Norway winter) / 05:00 CEST (Norway summer)
#>

$ErrorActionPreference = 'Stop'

# Timestamped log
$logDir  = Join-Path $PSScriptRoot '..\dumpster-dive\intake\overnight-daemon'
$logFile = Join-Path $logDir "nightly-scheduled-$(Get-Date -Format 'yyyy-MM-dd_HHmmss').log"

if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

# Run the launcher in focused mode:
# - Keep daemon analysis
# - Run genre extractor
# - Skip archaeology stage (largest JSON artifact producer)
$launcher = Join-Path $PSScriptRoot 'run_archaeology.ps1'

$exitCode = 1
try {
  & pwsh -NoProfile -File $launcher -Genre -SkipArchaeology 2>&1 | Tee-Object -FilePath $logFile
  $exitCode = $LASTEXITCODE
} catch {
  $_ | Tee-Object -FilePath $logFile -Append | Out-Null
  $exitCode = if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { $LASTEXITCODE } else { 1 }
}

if ($exitCode -ne 0) {
  Write-Host "Nightly run failed (exit code $exitCode). See log: $logFile" -ForegroundColor Red
} else {
  $resumptionScript = Join-Path $PSScriptRoot 'session_resumption_high_coverage.py'
  if (Test-Path -LiteralPath $resumptionScript) {
    try {
      & uv run $resumptionScript --quiet --latest-only --no-json 2>&1 | Tee-Object -FilePath $logFile -Append | Out-Null
      if ($LASTEXITCODE -ne 0) {
        Write-Host "Session resumption packet generation failed (exit code $LASTEXITCODE). See log: $logFile" -ForegroundColor Yellow
      }
    } catch {
      $_ | Tee-Object -FilePath $logFile -Append | Out-Null
      Write-Host "Session resumption packet generation failed. See log: $logFile" -ForegroundColor Yellow
    }
  }
}

exit $exitCode
