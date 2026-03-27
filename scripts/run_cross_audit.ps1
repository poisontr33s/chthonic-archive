#!/usr/bin/env pwsh
#
# @SID: SCRIPT_RUN_CROSS_AUDIT_V1
# @Type: VALIDATION
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: [string]$CodexRoot = ".codex/skills",
#

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
$outJson = "codex/mailbox/cross_audit_$stamp.json"

$results = @()
$results += Run-Cmd -Label "skill_audit_codex" -Args @("uv","run","scripts/skill_audit.py","--flavor","codex","--root",$CodexRoot,"--json","--json-path","codex/mailbox/skill_audit_codex_$stamp.json")
$results += Run-Cmd -Label "skill_audit_claude" -Args @("uv","run","scripts/skill_audit.py","--flavor","claude","--root",$ClaudeRoot,"--json","--json-path","codex/mailbox/skill_audit_claude_$stamp.json")
$results += Run-Cmd -Label "check_python_policy" -Args @("uv","run","scripts/check_python_policy.py")
$results += Run-Cmd -Label "check_mailbox_layout" -Args @("uv","run","scripts/check_mailbox_layout.py")

$payload = [pscustomobject]@{
  schema_version = 1
  generated_on = (Get-Date).ToUniversalTime().ToString("o")
  codex_root = $CodexRoot
  claude_root = $ClaudeRoot
  results = $results
}
$payload | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 $outJson

$rc = 0
foreach ($r in $results) { if ($r.rc -ne 0) { $rc = $r.rc; break } }

$handoff = @(
  "---",
  "type: handoff",
  "from: codex",
  "to: codex",
  ("created: " + (Get-Date).ToString("yyyy-MM-dd")),
  "priority: inform",
  "scope: cross-audit",
  "---",
  "",
  "# Handoff: Cross Audit Report",
  "",
  "## Actions Taken",
  ('- Wrote: `' + $outJson + '`'),
  ('- Wrote: `codex/mailbox/skill_audit_codex_' + $stamp + '.json`'),
  ('- Wrote: `codex/mailbox/skill_audit_claude_' + $stamp + '.json`'),
  "",
  "## Result",
  ('- Exit code: `' + $rc + '`'),
  "",
  "## Next Actions",
  "- If failing: open the JSON above and fix the first non-zero `rc` step.",
  ""
) -join "`n"

$handoffPath = "codex/mailbox/SESSION_HANDOFF_$((Get-Date).ToString('yyyy_MM_dd'))_CROSS_AUDIT.md"
$handoff | Set-Content -Encoding utf8 $handoffPath

# Keep manifests/packet coherent (stable filenames; no file spam).
uv run scripts/mailbox_scribe.py --target codex --packet codex/mailbox/TETRAGRAMMATON_PACKET.md | Out-Null

exit $rc

