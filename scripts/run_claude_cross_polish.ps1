#!/usr/bin/env pwsh

param(
  [string]$CodexRoot = ".codex/skills",
  [string]$ClaudeRoot = ".claude/skills"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-Stamp {
  return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH-mm-ssZ")
}

function Run-Cmd {
  param(
    [Parameter(Mandatory=$true)][string]$Label,
    [Parameter(Mandatory=$true)][string[]]$Args
  )
  $start = Get-Date
  $p = Start-Process -FilePath $Args[0] -ArgumentList $Args[1..($Args.Count-1)] -NoNewWindow -Wait -PassThru
  $end = Get-Date
  return [pscustomobject]@{
    label = $Label
    rc = $p.ExitCode
    seconds = [math]::Round(($end - $start).TotalSeconds, 3)
    cmd = $Args
  }
}

$stamp = New-Stamp
$codexJson = "codex/mailbox/skill_audit_codex_$stamp.json"
$claudeJson = "codex/mailbox/skill_audit_claude_$stamp.json"

$results = @()
$results += Run-Cmd -Label "skill_audit_codex" -Args @("uv","run","scripts/skill_audit.py","--flavor","codex","--root",$CodexRoot,"--json","--json-path",$codexJson)
$results += Run-Cmd -Label "skill_audit_claude" -Args @("uv","run","scripts/skill_audit.py","--flavor","claude","--root",$ClaudeRoot,"--json","--json-path",$claudeJson)

$rc = 0
foreach ($r in $results) { if ($r.rc -ne 0) { $rc = $r.rc; break } }

$handoff = @(
  "---",
  "type: handoff",
  "from: codex",
  "to: codex",
  ("created: " + (Get-Date).ToString("yyyy-MM-dd")),
  "priority: inform",
  "scope: cross-polish",
  "---",
  "",
  "# Handoff: Cross Skill Audit",
  "",
  "## Actions Taken",
  ('- Wrote: `' + $codexJson + '`'),
  ('- Wrote: `' + $claudeJson + '`'),
  "",
  "## Result",
  ('- Exit code: `' + $rc + '`'),
  "",
  "## Next Actions",
  "- If failing: open the JSON above and address the first reported violation.",
  ""
) -join "`n"

$handoffPath = "codex/mailbox/SESSION_HANDOFF_$((Get-Date).ToString('yyyy_MM_dd'))_CROSS_SKILL_AUDIT.md"
$handoff | Set-Content -Encoding utf8 $handoffPath

uv run scripts/mailbox_scribe.py --target codex --packet codex/mailbox/TETRAGRAMMATON_PACKET.md | Out-Null

exit $rc

