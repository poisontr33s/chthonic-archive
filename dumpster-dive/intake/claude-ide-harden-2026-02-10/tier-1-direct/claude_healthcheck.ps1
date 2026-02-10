#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Deterministic healthcheck for Claude Code IDE integration (Windows/Insiders).

.GOAL
  Convert "random" daily breakage into a small set of stable invariants with
  machine-readable artifacts for debugging and regression tracking.

.OUTPUTS
  - codex/mailbox/CLAUDE_IDE_HEALTH_LATEST.json

.SECURITY
  - Never prints or writes secret values.
  - Only boolean presence checks for tokens.

.USAGE
  pwsh -NoProfile -File scripts/claude_healthcheck.ps1
  pwsh -NoProfile -File scripts/claude_healthcheck.ps1 -OutPath codex/mailbox/CLAUDE_IDE_HEALTH_LATEST.json

CANON
  Prefer: pwsh -NoProfile -File scripts/claude_ide.ps1 health
#>

param(
  [string]$OutPath = "codex/mailbox/CLAUDE_IDE_HEALTH_LATEST.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Now-IsoUtc {
  return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
}

function Get-EnvPresent {
  param([Parameter(Mandatory=$true)][string]$Name)
  $v = [Environment]::GetEnvironmentVariable($Name, "Process")
  return -not [string]::IsNullOrWhiteSpace([string]$v)
}

function Read-JsonFile {
  param([Parameter(Mandatory=$true)][string]$Path)
  $raw = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop
  return $raw | ConvertFrom-Json -ErrorAction Stop
}

function Try-Run {
  param(
    [Parameter(Mandatory=$true)][string]$Label,
    [Parameter(Mandatory=$true)][scriptblock]$Body
  )
  $t0 = Get-Date
  try {
    $out = & $Body
    return @{
      ok = $true
      label = $Label
      ms = [int]((Get-Date) - $t0).TotalMilliseconds
      detail = $out
      error = $null
    }
  } catch {
    return @{
      ok = $false
      label = $Label
      ms = [int]((Get-Date) - $t0).TotalMilliseconds
      detail = $null
      error = ($_.Exception.Message)
    }
  }
}

Push-Location (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
try {
  $repoRoot = (Get-Location).Path

  # Ensure this healthcheck is self-contained when run from the IDE wrapper.
  # It is safe/idempotent: it only sets process env vars.
  try {
    . "$repoRoot/scripts/api_pool.ps1" -Load | Out-Null
  } catch {
    # Don't throw; record via env presence + downstream failures.
  }

  $mcpPath = Join-Path $repoRoot ".mcp.json"
  $mcpExists = Test-Path -LiteralPath $mcpPath

  $checks = @()

  $checks += Try-Run -Label "parse .mcp.json" -Body {
    if (-not (Test-Path -LiteralPath $mcpPath)) { return @{ exists = $false } }
    $obj = Read-JsonFile -Path $mcpPath
    # Minimal shape check.
    $servers = $obj.mcpServers
    $hasGithub = $false
    $hasHf = $false
    if ($servers) {
      $hasGithub = $servers.PSObject.Properties.Name -contains "github"
      $hasHf = $servers.PSObject.Properties.Name -contains "huggingface"
    }
    return @{
      exists = $true
      hasGithub = $hasGithub
      hasHuggingface = $hasHf
    }
  }

  $checks += Try-Run -Label "claude mcp list" -Body {
    $txt = & claude mcp list 2>&1
    $s = if ($txt -is [Array]) { $txt -join "`n" } else { [string]$txt }
    # Don't over-parse; keep a compact excerpt for debugging.
    $lines = $s -split "`r?`n"
    $head = ($lines | Select-Object -First 40) -join "`n"
    return @{ head = $head }
  }

  $checks += Try-Run -Label "claude plugin list --json" -Body {
    $txt = & claude plugin list --json 2>&1
    $s = if ($txt -is [Array]) { $txt -join "`n" } else { [string]$txt }
    $obj = $s | ConvertFrom-Json
    # This command returns an array of installed plugins.
    $ids = @()
    foreach ($p in $obj) {
      if ($p.id) { $ids += [string]$p.id }
    }
    return @{
      count = $ids.Count
      hasGithubPlugin = ($ids -contains "github@claude-plugins-official")
      hasChthonicTools = ($ids -contains "chthonic-tools@chthonic-local")
    }
  }

  $result = @{
    schema_version = 1
    generated_at_utc = Now-IsoUtc
    repo_root = $repoRoot
    invariants = @{
      env = @{
        GITHUB_PERSONAL_ACCESS_TOKEN_present = (Get-EnvPresent -Name "GITHUB_PERSONAL_ACCESS_TOKEN")
        HUGGINGFACE_HUB_TOKEN_present = (Get-EnvPresent -Name "HUGGINGFACE_HUB_TOKEN")
        HF_TOKEN_present = (Get-EnvPresent -Name "HF_TOKEN")
      }
      mcp_json = @{
        path = ".mcp.json"
        exists = $mcpExists
      }
    }
    checks = $checks
    ok = ($checks | Where-Object { -not $_.ok } | Measure-Object).Count -eq 0
  }

  $outFile = Join-Path $repoRoot $OutPath
  $outDir = Split-Path -Parent $outFile
  New-Item -ItemType Directory -Force -Path $outDir | Out-Null
  ($result | ConvertTo-Json -Depth 8) | Out-File -FilePath $outFile -Encoding utf8
  Write-Output ("ok: wrote {0}" -f $OutPath)
  if (-not $result.ok) { exit 1 }
  exit 0
} finally {
  Pop-Location
}
