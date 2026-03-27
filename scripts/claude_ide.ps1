#!/usr/bin/env pwsh
#
# @SID: SCRIPT_CLAUDE_IDE_V1
# @Type: AGENT
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Canonical entrypoint for Claude Code IDE hardening on Windows/VS Code Insiders.
#
<#
.SYNOPSIS
  Canonical entrypoint for Claude Code IDE hardening on Windows/VS Code Insiders.

.WHY
  We previously accumulated multiple patch/selfheal/health scripts. This file is the
  single choke point that learns from failures. Other scripts should be thin shims.

.COMMANDS
  - heal        : patch CLI for code-insiders + (re)write .mcp.json + ensure plugins + mcp list
  - health      : write codex/mailbox/CLAUDE_IDE_HEALTH_LATEST.json (and exit non-zero if failing)
  - write-mcp   : rewrite .mcp.json from api pool (GitHub mode: copilot|official)
  - persist-env : persist required tokens as Windows User env vars (no values printed)
  - crossover   : emit claude/mailbox task packet (Codex -> Claude continuation)

.USAGE
  pwsh -NoProfile -File scripts/claude_ide.ps1 heal
  pwsh -NoProfile -File scripts/claude_ide.ps1 health
  pwsh -NoProfile -File scripts/claude_ide.ps1 write-mcp -GitHubMode copilot
  pwsh -NoProfile -File scripts/claude_ide.ps1 persist-env
  pwsh -NoProfile -File scripts/claude_ide.ps1 crossover -Topic "..."
#>

param(
  [Parameter(Position=0)][ValidateSet("heal","health","write-mcp","persist-env","crossover")][string]$Cmd = "heal",
  [ValidateSet("official","copilot")][string]$GitHubMode = "copilot",
  [switch]$Full,
  [string]$Topic,
  [string[]]$Files = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
try {
  switch ($Cmd) {
    "heal" {
      pwsh -NoProfile -File "scripts/claude_insiders_selfheal.ps1" @(
        $(if ($Full) { "-Full" } else { $null })
      ) | Out-Null
      exit 0
    }
    "health" {
      pwsh -NoProfile -File "scripts/claude_healthcheck.ps1" | Out-Null
      exit $LASTEXITCODE
    }
    "write-mcp" {
      . "scripts/api_pool.ps1" -Load | Out-Null
      pwsh -NoProfile -File "scripts/mcp_write_local.ps1" -GitHubMode $GitHubMode | Out-Null
      exit 0
    }
    "persist-env" {
      pwsh -NoProfile -File "scripts/api_pool_persist_user_env.ps1" -Apply | Out-Null
      exit 0
    }
    "crossover" {
      if ([string]::IsNullOrWhiteSpace($Topic)) {
        throw "crossover requires -Topic"
      }
      pwsh -NoProfile -File "scripts/claude_crossover.ps1" -Topic $Topic -Files $Files | Out-Null
      exit 0
    }
  }
} finally {
  Pop-Location
}

