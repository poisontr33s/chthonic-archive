#!/usr/bin/env pwsh

param(
  [string]$Root = ".codex/skills"
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
$stampsJson = "codex/mailbox/tatragrammatron_stamps_$stamp.json"
$summaryMd = "codex/mailbox/TATRAGRAMMATRON_SUMMARY_$stamp.md"

$args = @(
  "uv","run",
  ".codex/skills/skill-polisher/scripts/polish_skill.py",
  $Root,
  "--all",
  "--mode","verify",
  "--subprocess-fix",
  "--target-flavor","codex",
  "--emit-stamps-json",$stampsJson,
  "--emit-summary-md",$summaryMd
)
$result = Run-Cmd -Label "codex_skill_polisher" -Args $args

$payload = [pscustomobject]@{
  schema_version = 1
  generated_on = (Get-Date).ToUniversalTime().ToString("o")
  root = $Root
  result = $result
  artifacts = @($stampsJson,$summaryMd)
}
$outJson = "codex/mailbox/codex_skill_polisher_$stamp.json"
$payload | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 $outJson

$handoff = @(
  "---",
  "type: handoff",
  "from: codex",
  "to: codex",
  ("created: " + (Get-Date).ToString("yyyy-MM-dd")),
  "priority: inform",
  "scope: codex-skill-polisher",
  "---",
  "",
  "# Handoff: Codex Skill Polisher",
  "",
  "## Actions Taken",
  ('- Wrote: `' + $outJson + '`'),
  ('- Wrote: `' + $stampsJson + '`'),
  ('- Wrote: `' + $summaryMd + '`'),
  "",
  "## Result",
  ('- Exit code: `' + $result.rc + '`'),
  "",
  "## Next Actions",
  "- If failing: open the summary MD and fix the first critical entropy item.",
  ""
) -join "`n"

$handoffPath = "codex/mailbox/SESSION_HANDOFF_$((Get-Date).ToString('yyyy_MM_dd'))_CODEX_SKILL_POLISH.md"
$handoff | Set-Content -Encoding utf8 $handoffPath

uv run scripts/mailbox_scribe.py --target codex --packet codex/mailbox/TETRAGRAMMATON_PACKET.md | Out-Null

exit $result.rc

