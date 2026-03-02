#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Launch Claude Code with a profile override for this repository.

.DESCRIPTION
  Profiles are additive settings passed via `claude --settings <file>`.
  - default: uses .claude/settings.json as-is
  - research-high: keeps Opus with high effort
  - opus-1m: probes long-context support first; falls back to research-high when unavailable

.USAGE
  pwsh -NoProfile -File scripts/claude_profile.ps1 -Profile research-high
  pwsh -NoProfile -File scripts/claude_profile.ps1 -Profile opus-1m
  pwsh -NoProfile -File scripts/claude_profile.ps1 -Profile check-opus-1m
#>

[CmdletBinding()]
param(
  [ValidateSet("default", "lean", "research-high", "opus-1m", "check-opus-1m")]
  [string]$Profile = "default",

  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$ClaudeArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$defaultSettings = Join-Path $repoRoot ".claude/settings.json"
$researchSettings = Join-Path $repoRoot ".claude/profiles/research-high.json"
$opus1mSettings = Join-Path $repoRoot ".claude/profiles/opus-1m.json"
$extraArgs = @()

function Parse-ClaudeResult {
  param([Parameter(Mandatory = $true)][string]$RawText)
  $idx = $RawText.IndexOf("{")
  if ($idx -lt 0) { return $null }
  $jsonText = $RawText.Substring($idx)
  try { return ($jsonText | ConvertFrom-Json) } catch { return $null }
}

function Test-LongContextModel {
  param([Parameter(Mandatory = $true)][string]$ModelAlias)

  $probe = & claude -p --output-format json --model $ModelAlias "Reply with exactly: LONG_CONTEXT_OK" 2>&1
  $raw = if ($probe -is [Array]) { $probe -join "`n" } else { [string]$probe }
  $result = Parse-ClaudeResult -RawText $raw

  if ($null -eq $result) {
    return [pscustomobject]@{
      Supported = $false
      Reason    = "Could not parse probe response."
    }
  }

  if ($result.is_error) {
    return [pscustomobject]@{
      Supported = $false
      Reason    = [string]$result.result
    }
  }

  if (([string]$result.result).Trim() -eq "LONG_CONTEXT_OK") {
    return [pscustomobject]@{
      Supported = $true
      Reason    = "Probe succeeded."
    }
  }

  return [pscustomobject]@{
    Supported = $false
    Reason    = "Probe did not return expected marker."
  }
}

if ($Profile -eq "check-opus-1m") {
  $check = Test-LongContextModel -ModelAlias "opus[1m]"
  if ($check.Supported) {
    Write-Host "Opus 1M check: AVAILABLE for this auth/session." -ForegroundColor Green
    exit 0
  }

  Write-Host "Opus 1M check: NOT available for this auth/session." -ForegroundColor Yellow
  Write-Host $check.Reason
  exit 1
}

$settingsFile = switch ($Profile) {
  "default" { $defaultSettings }
  "lean" {
    # Note: --disable-slash-commands was removed in CLI 2.1.42.
    # Lean mode now just uses the default settings overlay.
    $defaultSettings
  }
  "research-high" { $researchSettings }
  "opus-1m" {
    $check = Test-LongContextModel -ModelAlias "opus[1m]"
    if ($check.Supported) {
      Write-Host "Opus 1M available. Launching with opus-1m profile." -ForegroundColor Green
      $opus1mSettings
    } else {
      Write-Host "Opus 1M unavailable. Falling back to research-high profile." -ForegroundColor Yellow
      Write-Host $check.Reason
      $researchSettings
    }
  }
  default { throw "Unknown profile: $Profile" }
}

if (-not (Test-Path $settingsFile)) {
  throw "Profile settings file not found: $settingsFile"
}

Write-Host ("Launching Claude with profile '{0}' using {1}" -f $Profile, $settingsFile) -ForegroundColor Cyan
& claude @extraArgs --settings $settingsFile @ClaudeArgs
exit $LASTEXITCODE
