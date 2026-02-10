#!/usr/bin/env pwsh
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: copilot_clean.ps1
# ║ Module: Copilot CLI launcher profile
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: integration/copilot
# ║ Architectural Role: CLI profile shim (non-destructive)
# ║ Semantic ID: SCRIPT_COPILOT_CLEAN_V1
# ║ Purpose: Launch Copilot CLI with explicit flags/env (no hidden sabotage)
# ║ Exports: None (launcher script)
# ║ Flags/Modes: -DisableCustomAgents, -DisableBuiltinMcps, -DisableMcpServer, -NoCustomInstructions
# ║ Cross-References: .github/copilot-instructions.md, .github/pathstofiles.md
# ╚════════════════════════════════════════════════════════════════════════════

<#
.SYNOPSIS
  Launch GitHub Copilot CLI with explicit profile switches.

.DESCRIPTION
  Copilot CLI can discover custom agents from:
  - [repo]/.github/agents/*.md
  - [repo]/.claude/agents/*.md
  - ~/.claude/agents/*.md

  This repo intentionally contains `.claude/agents/` for Claude-lane workflows.
  By default, this launcher does NOT disable anything. Use switches to opt-out.

.USAGE
  pwsh -NoProfile -File scripts/copilot_clean.ps1 [switches...] [-- <copilot args...>]
#>

[CmdletBinding(PositionalBinding = $false)]
param(
  [switch]$DisableCustomAgents,
  [switch]$DisableBuiltinMcps,
  [string[]]$DisableMcpServer,
  [switch]$NoCustomInstructions,
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$CopilotArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($DisableCustomAgents) {
  $env:CUSTOM_AGENTS = "false"
}

$argsList = @()

if ($DisableBuiltinMcps) {
  $argsList += "--disable-builtin-mcps"
}

if ($DisableMcpServer) {
  foreach ($name in $DisableMcpServer) {
    if ($null -ne $name -and $name.Trim().Length -gt 0) {
      $argsList += "--disable-mcp-server"
      $argsList += $name
    }
  }
}

if ($NoCustomInstructions) {
  $argsList += "--no-custom-instructions"
}

if ($CopilotArgs) {
  $argsList += $CopilotArgs
}

& copilot @argsList
exit $LASTEXITCODE
