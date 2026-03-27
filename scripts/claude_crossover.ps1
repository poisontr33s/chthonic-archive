#!/usr/bin/env pwsh
#
# @SID: SCRIPT_CLAUDE_CROSSOVER_V1
# @Type: AGENT
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Codex -> Claude Code IDE crossover: emit a deterministic task + continuation art
#

<#
.SYNOPSIS
  Codex -> Claude Code IDE crossover: emit a deterministic task + continuation artifacts into claude/mailbox.

.WHY
  "Check your mail" is supposed to mean continuity, not file spam.
  This script creates a single, well-structured task packet for Claude Code to pick up in the IDE,
  referencing the most relevant artifacts (trainstop, healthcheck, etc.).

.OUTPUTS
  - claude/mailbox/CODEX_TO_CLAUDE_TASK_LATEST.md
  - codex/mailbox/CODEX_TO_CLAUDE_TASK_LATEST.json

.USAGE
  pwsh -NoProfile -File scripts/claude_crossover.ps1 -Topic "Fix MCP auth drift"
  pwsh -NoProfile -File scripts/claude_crossover.ps1 -Topic "Review bridge scripts" -Files ".mcp.json",".claude/settings.json"
#>

param(
  [Parameter(Mandatory=$true)][string]$Topic,
  [string[]]$Files = @(),
  [string]$OutMd = "claude/mailbox/CODEX_TO_CLAUDE_TASK_LATEST.md",
  [string]$OutJson = "codex/mailbox/CODEX_TO_CLAUDE_TASK_LATEST.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Now-IsoUtc {
  return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
}

function ExistingOrNull {
  param([Parameter(Mandatory=$true)][string]$Path)
  if (Test-Path -LiteralPath $Path) { return $Path }
  return $null
}

Push-Location (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
try {
  $repoRoot = (Get-Location).Path
  $stamp = Now-IsoUtc

  $refs = @()
  foreach ($p in $Files) {
    $pp = $p
    if (-not [System.IO.Path]::IsPathRooted($pp)) {
      $pp = Join-Path $repoRoot $pp
    }
    if (Test-Path -LiteralPath $pp) {
      $rel = (Resolve-Path -LiteralPath $pp).Path.Substring($repoRoot.Length).TrimStart("\","/")
      $refs += $rel
    }
  }

  # Known "high signal" artifacts if present.
  $maybe = @(
    "codex/mailbox/CLAUDE_IDE_HEALTH_LATEST.json",
    "codex/mailbox/TRAINSTOP_ORCHESTRATOR_LATEST.json",
    "codex/mailbox/HF_PREP_LATEST.json",
    "codex/mailbox/HF_PREP_LATEST.md",
    ".claude/settings.json",
    ".vscode/settings.json",
    ".mcp.json"
  )
  foreach ($p in $maybe) {
    $hit = ExistingOrNull -Path (Join-Path $repoRoot $p)
    if ($hit) { $refs += $p }
  }

  $refs = $refs | Select-Object -Unique
  $refLines = @()
  if ($refs.Count -gt 0) {
    foreach ($r in $refs) {
      # Avoid PowerShell backtick parsing issues by constructing explicitly.
      $refLines += ('- `' + $r + '`')
    }
  } else {
    $refLines += "- (none provided)"
  }

  $md = @(
    "---",
    "type: task",
    "from: codex",
    "to: claude",
    ("created_at_utc: " + $stamp),
    "priority: high",
    "scope: crossover",
    "---",
    "",
    ("# Task: " + $Topic),
    "",
    "## Intent",
    "- Continue the active workstream from Codex inside Claude Code IDE.",
    "- Prefer producing continuation artifacts (mailbox handoffs, health JSON) over silent audits.",
    "",
    "## What Codex Already Did",
    "- Implemented an IDE launch wrapper (`claudeCode.claudeProcessWrapper`) so VS Code-launched Claude always loads tokens + self-heals.",
    "- Added deterministic health artifact: `codex/mailbox/CLAUDE_IDE_HEALTH_LATEST.json`.",
    "- Added local plugin marketplace `chthonic-local` with plugin `chthonic-tools` (commands: `/selfheal`, `/postman`).",
    "",
    "## Required Outputs (Claude)",
    "- One handoff note describing what you changed and why (no spam).",
    "- If you touch IDE/MCP: update/verify `codex/mailbox/CLAUDE_IDE_HEALTH_LATEST.json` and cite failures by signature.",
    "",
    "## High-Signal References",
    ($refLines -join "`n"),
    "",
    "## Execution Notes",
    "- If running from VS Code integrated terminal, the wrapper should already normalize env + rewrite `.mcp.json`.",
    "- If you see an already-enabled plugin enable failure: use idempotent enable (or ignore) and proceed.",
    ""
  ) -join "`n"

  $outMdAbs = Join-Path $repoRoot $OutMd
  $outJsonAbs = Join-Path $repoRoot $OutJson
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outMdAbs) | Out-Null
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outJsonAbs) | Out-Null

  $md | Out-File -FilePath $outMdAbs -Encoding utf8

  $payload = @{
    schema_version = 1
    created_at_utc = $stamp
    topic = $Topic
    references = $refs
    out_md = $OutMd
  }
  ($payload | ConvertTo-Json -Depth 6) | Out-File -FilePath $outJsonAbs -Encoding utf8

  Write-Output ("ok: wrote {0}" -f $OutMd)
  Write-Output ("ok: wrote {0}" -f $OutJson)
} finally {
  Pop-Location
}
