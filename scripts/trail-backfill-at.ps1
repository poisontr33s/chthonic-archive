#!/usr/bin/env pwsh
#-*- coding: utf-8 -*-
<#
.SYNOPSIS
Backfill the REM-required `at` timestamp onto trail events that only carry `ts`.

@SID:    TOOL_TRAIL_BACKFILL_AT_V1
@Type:   Data migration (additive, idempotent)
@Output: Per-file counts; with -Apply, rewritten .hot.ndjson + backups

.DESCRIPTION
`.chthonic/trail/*.hot.ndjson` is written and read by components that never
agreed on a timestamp field:

  - the PowerShell lane (profile.ps1 session hook, chthonic-xp.ps1) writes `ts`,
    unix milliseconds
  - REM / ankh-forge's `TrailEvent` (tools/ankh-forge/src/trail/event.rs) requires
    `at`, RFC 3339, as a NON-Option field

Measured 2026-08-09: 22,758 of 22,809 events carry `ts` and no `at`, so
`ankh-forge trail verify` fails to deserialize them and the entire
hot -> cold -> .runestone pipeline — including the Vulkan GPU decode path — has
never been able to read the trail it was built for. Confirmed with the real
binary, not by inference: "missing field `at`".

`at` is derived from `ts`, so this is recoverable arithmetic, not invention.

WHY STRING SURGERY AND NOT ConvertFrom-Json | ConvertTo-Json. Round-tripping
22k events through PowerShell's JSON would re-serialize every value: key order
changes, unicode escaping changes, and large integers can lose exactness. The
diff would then be enormous and unreviewable, and any corruption would hide
inside it. This inserts `,"at":"..."` immediately after the existing `"ts":<n>`
token and touches nothing else, so a diff shows exactly one insertion per line.

Idempotent: a line already containing `"at":` is left byte-identical. Safe to
re-run. Lines with neither `ts` nor `at` are reported, never guessed at.

.EXAMPLE
  ./trail-backfill-at.ps1                 # dry run, reports what would change
  ./trail-backfill-at.ps1 -Apply          # write, backing each file up first
  ./trail-backfill-at.ps1 -Apply -Date 2026-08-09
#>

[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$Date,                     # single YYYY-MM-DD, else every hot file
    [string]$TrailDir = (Join-Path $PSScriptRoot '..\.chthonic\trail')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$TrailDir = (Resolve-Path -LiteralPath $TrailDir).Path
$filter = if ($Date) { "$Date.hot.ndjson" } else { '*.hot.ndjson' }
$files = @(Get-ChildItem -LiteralPath $TrailDir -Filter $filter -File -EA SilentlyContinue | Sort-Object Name)

# An empty target set is unknown, not clean — refuse to report success on nothing.
if ($files.Count -eq 0) {
    Write-Host "no hot trail files matching '$filter' under $TrailDir" -ForegroundColor Yellow
    exit 2
}

# Deliberately a SIBLING of the trail, not a child. A backup of *.hot.ndjson
# living inside the directory those files are globbed from is a landmine: every
# reader here happens to be non-recursive today, and the day one isn't, the
# backup gets counted as real events and silently doubles the history.
$BackupDir = Join-Path (Split-Path -Parent $TrailDir) ("trail-backups\backfill-{0}" -f ([DateTimeOffset]::UtcNow.ToUnixTimeSeconds()))

$totAlready = 0; $totFixed = 0; $totUnfixable = 0; $totLines = 0
$changedFiles = [System.Collections.Generic.List[string]]::new()

foreach ($f in $files) {
    $lines = @(Get-Content -LiteralPath $f.FullName)
    $out = [System.Collections.Generic.List[string]]::new()
    $already = 0; $fixed = 0; $unfixable = 0

    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line)) { $out.Add($line); continue }
        $totLines++

        if ($line -match '"at"\s*:') { $already++; $out.Add($line); continue }

        if ($line -match '"ts"\s*:\s*(\d+)') {
            $ms = [long]$Matches[1]
            $iso = [DateTimeOffset]::FromUnixTimeMilliseconds($ms).UtcDateTime.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
            # Insert immediately after the matched ts token; nothing else is touched.
            $out.Add(($line -replace '("ts"\s*:\s*\d+)', ('$1,"at":"' + $iso + '"')))
            $fixed++
            continue
        }

        # Neither field. Not guessable — a fabricated timestamp is worse than a
        # rejected line, because REM would then accept it as real provenance.
        $unfixable++
        $out.Add($line)
    }

    $totAlready += $already; $totFixed += $fixed; $totUnfixable += $unfixable
    $flag = if ($fixed -gt 0) { '*' } else { ' ' }
    "{0} {1,-24} lines={2,6}  already={3,6}  backfill={4,6}  unfixable={5,4}" -f
        $flag, $f.Name, $lines.Count, $already, $fixed, $unfixable | Write-Host

    if ($fixed -gt 0) {
        $changedFiles.Add($f.Name)
        if ($Apply) {
            New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
            Copy-Item -LiteralPath $f.FullName -Destination (Join-Path $BackupDir $f.Name) -Force
            Set-Content -LiteralPath $f.FullName -Value $out -Encoding UTF8
        }
    }
}

Write-Host ""
Write-Host ("files={0}  lines={1}  already-valid={2}  backfilled={3}  unfixable={4}" -f
    $files.Count, $totLines, $totAlready, $totFixed, $totUnfixable) -ForegroundColor Cyan

if ($totUnfixable -gt 0) {
    Write-Host ("  {0} line(s) carry neither ts nor at — left untouched, never invented." -f $totUnfixable) -ForegroundColor Yellow
}

if ($Apply) {
    if ($changedFiles.Count -gt 0) {
        Write-Host ("  backups -> {0}" -f $BackupDir) -ForegroundColor DarkGray
    }
    Write-Host "  verify with: target\debug\ankh-forge.exe trail verify --date <YYYY-MM-DD>" -ForegroundColor DarkGray
} else {
    Write-Host "  DRY RUN — nothing written. Re-run with -Apply." -ForegroundColor Yellow
}

exit 0
