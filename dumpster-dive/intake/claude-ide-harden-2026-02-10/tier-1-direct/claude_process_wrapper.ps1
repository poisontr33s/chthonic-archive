#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Claude Code VS Code process wrapper (Windows/Insiders hardening).

.WHY
  VS Code-launched processes do not inherit your terminal's process env.
  This wrapper ensures:
  - api_pool is loaded (tokens available to IDE-launched Claude)
  - Insiders self-heal is applied (CLI patch + .mcp.json refresh)
  before spawning the real Claude binary.

.CONTRACT (as implemented by the VS Code extension)
  When `claudeCode.claudeProcessWrapper` is set, the extension executes:
    <wrapper> <originalClaudeBinary> [originalArgs...]
  See extension.js:getClaudeBinary().

.SECURITY
  - Never prints secret values.

.USAGE (manual)
  pwsh -NoProfile -File scripts/claude_process_wrapper.ps1 <binary> [args...]
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Try-Step {
  param([Parameter(Mandatory=$true)][string]$Label, [Parameter(Mandatory=$true)][scriptblock]$Body)
  try { & $Body | Out-Null } catch { }
}

if ($args.Count -lt 1) {
  Write-Error "Missing target binary. Expected: <wrapper> <originalClaudeBinary> [args...]"
  exit 2
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $repoRoot
try {
  # 1) Load tokens into this process (and normalize aliases).
  Try-Step -Label "api_pool" -Body { . "$repoRoot/scripts/api_pool.ps1" -Load }

  # 2) Apply self-heal (fast mode).
  Try-Step -Label "selfheal" -Body { pwsh -NoProfile -File "$repoRoot/scripts/claude_insiders_selfheal.ps1" }

  # 3) Emit health artifact (do not print secrets). If this fails, it should
  # fail fast so we stop "mystery broken" sessions early.
  $hc = & pwsh -NoProfile -File "$repoRoot/scripts/claude_healthcheck.ps1" 2>&1
  if ($LASTEXITCODE -ne 0) {
    $s = if ($hc -is [Array]) { $hc -join "`n" } else { [string]$hc }
    Write-Error ("Claude IDE healthcheck failed. See codex/mailbox/CLAUDE_IDE_HEALTH_LATEST.json. {0}" -f $s.Trim())
    exit 1
  }

  # 4) Spawn the original process. Preserve exit code.
  $target = [string]$args[0]
  $pass = @()
  if ($args.Count -gt 1) { $pass = $args[1..($args.Count-1)] }

  # If the extension provided: node <cli.js> ... then use node explicitly.
  if ($target -ieq "node" -and $pass.Count -ge 1) {
    $nodeArgs = $pass
    $p = Start-Process -FilePath "node" -ArgumentList $nodeArgs -NoNewWindow -Wait -PassThru
    exit $p.ExitCode
  }

  $p = Start-Process -FilePath $target -ArgumentList $pass -NoNewWindow -Wait -PassThru
  exit $p.ExitCode
} finally {
  Pop-Location
}
