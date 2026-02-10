#!/usr/bin/env pwsh
<#
SYNOPSIS
  Self-heal Claude Code IDE integration after VS Code Insiders / Claude updates.

GOAL
  VS Code Insiders updates are frequent and can break:
  - Claude CLI IDE detection (needs code-insiders patch)
  - local MCP config presence/shape
  - plugin marketplace freshness + GitHub plugin enablement

DESIGN
  - Idempotent: safe to run every day.
  - Fast by default: avoids heavy installs unless you ask.
  - No secrets printed.

USAGE
  pwsh -NoProfile -File scripts/claude_insiders_selfheal.ps1
  pwsh -NoProfile -File scripts/claude_insiders_selfheal.ps1 -Full

CANON
  Prefer: pwsh -NoProfile -File scripts/claude_ide.ps1 heal
#>

param(
  [switch]$Full
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location (Split-Path -Parent $PSScriptRoot)
try {

function Try-Step {
  param(
    [Parameter(Mandatory = $true)][string]$Label,
    [Parameter(Mandatory = $true)][scriptblock]$Body
  )
  try {
    & $Body
    Write-Output "ok: $Label"
    return $true
  } catch {
    Write-Output "warn: $Label ($($_.Exception.Message))"
    return $false
  }
}

# 1) Patch Claude CLI to understand VS Code Insiders binary.
Try-Step -Label "patch claude-cli for code-insiders" -Body {
  pwsh -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot/patch-claude-insiders.ps1" | Out-Null
} | Out-Null

# 2) Load API pool and (re)write local .mcp.json (ignored by git).
Try-Step -Label "refresh local .mcp.json from api pool (copilot github mode)" -Body {
  . "$PSScriptRoot/api_pool.ps1" -Load | Out-Null
  $mode = [Environment]::GetEnvironmentVariable("CHTHONIC_GITHUB_MCP_MODE", "Process")
  if ([string]::IsNullOrWhiteSpace($mode)) { $mode = "copilot" }
  pwsh -NoProfile -File "$PSScriptRoot/mcp_write_local.ps1" -GitHubMode $mode | Out-Null
} | Out-Null

# 3) Marketplace refresh (only in -Full; avoids network chatter on every session start).
if ($Full) {
  Try-Step -Label "update plugin marketplaces" -Body {
    & claude plugin marketplace update | Out-Null
  } | Out-Null
}

# 4) Ensure GitHub plugin enabled (no noisy enable-no-op).
Try-Step -Label "ensure github plugin enabled" -Body {
  pwsh -NoProfile -File "$PSScriptRoot/claude_plugin_ensure.ps1" -Plugin "github@claude-plugins-official" -Scope project | Out-Null
} | Out-Null

# 4b) Ensure local chthonic-tools plugin enabled (commands: /selfheal, /postman).
Try-Step -Label "ensure chthonic-tools plugin enabled" -Body {
  pwsh -NoProfile -File "$PSScriptRoot/claude_plugin_ensure.ps1" -Plugin "chthonic-tools@chthonic-local" -Scope project | Out-Null
} | Out-Null

# 5) Quick MCP health check (non-fatal).
Try-Step -Label "mcp health" -Body {
  & claude mcp list | Out-Null
} | Out-Null

} finally {
  Pop-Location
}
