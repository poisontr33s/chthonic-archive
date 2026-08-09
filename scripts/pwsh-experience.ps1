#!/usr/bin/env pwsh
#-*- coding: utf-8 -*-
<#
.SYNOPSIS
pwsh-experience — a progression gate for PowerShell object-shell discipline.

@SID:    TOOL_PWSH_EXPERIENCE_V1
@Type:   Gamification / Gate
@Output: Rank line, findings, and a trail event consumed by chthonic-xp.ps1

.DESCRIPTION
Wraps — does not replace — the installed PowerShell. Two layers:

  BLOCKING  Syntax errors. Parsed with [Parser]::ParseFile, which never
            executes the file. Any error stops progression outright.

  SCORED    The object-shell rule set. These are the failures that produce
            *plausible wrong answers* rather than crashes, which is why they
            are worth points: an empty pipe reads as "nothing to do" when it
            may mean "the check never ran."

Unlike the surrounding XP engine, this one CAN TAKE POINTS AWAY. A reward
system that only ever adds turns effort and correctness into the same number.

KNOWN GAP — member enumeration. `$list.Prop` on an empty collection throws under
StrictMode Latest, and that is the bug this tool shipped with. It is NOT in the
rule set, because `$x.Prop` is textually identical whether $x is a collection or
a single object, and only type flow tells them apart. Catching it needs AST
analysis, not a line regex. Recorded rather than approximated: a rule that
guesses would fire on correct code, and the tool's only real asset is that a
finding means something.

.EXAMPLE
  ./pwsh-experience.ps1 -Path ./scripts
  ./pwsh-experience.ps1 -Path ./x.ps1 -Emit       # write the trail event
  ./pwsh-experience.ps1 -Path ./x.ps1 -Strict     # scored findings also block
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Path,
    [switch]$Emit,      # append a trail event (chthonic-xp.ps1 derives XP from it)
    [switch]$Strict,    # scored findings block too, not just syntax errors
    [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$TrailDir = Join-Path $env:USERPROFILE 'chthonic-archive\.chthonic\trail'

# ── Ranks: 0 is where everyone starts, and it is not an insult ───────────────
$RANKS = @(
    @{ n = 0; t = 'Textual'      ; d = 'thinks in bash; pipes strings' }
    @{ n = 1; t = 'Object-Aware' ; d = 'no syntax errors; still trusts .Count' }
    @{ n = 2; t = 'Wrapped'      ; d = 'collections wrapped; empties guarded' }
    @{ n = 3; t = 'Stream-Literate'; d = 'knows Write-Host is stream 6' }
    @{ n = 4; t = 'Controlled'   ; d = 'proves the search works before trusting a zero' }
)

# ── The rule set ────────────────────────────────────────────────────────────
# Each rule costs XP because each one produces a CONFIDENT WRONG ANSWER, not a
# crash. Ordered by how quietly they fail.
$RULES = @(
    # Measured on pwsh 7.6.3, not assumed. A no-match Where-Object really does
    # yield $null, but PowerShell synthesizes $null.Count = 0, so the whole
    # "$null -eq 0 is False" folklore never reaches this idiom — under
    # StrictMode -Off the unwrapped form answers correctly at 0, 1 and n.
    # Under StrictMode Latest the same expression THROWS instead. So the defect
    # is real but conditional, and the rule is scoped to the condition. A rule
    # that fires on working code is how a linter teaches people to ignore it.
    @{ id='unwrapped-count'; cost=6; strictOnly=$true
       rx='(?<!@)\((?!\@)[^()]*\|\s*Where-Object[^()]*\)\s*\.Count'
       why='under StrictMode Latest, .Count on the $null no-match result THROWS' }
    @{ id='pipe-into-replace'; cost=6; rx='\)\s*-replace'
       why='no match -> $null -replace -> ""; 2+ -> array, stringified space-joined' }
    @{ id='unguarded-sum'; cost=5; rx='Measure-Object[^\r\n]*-Sum[^\r\n]*\)\.Sum(?![^\r\n]*\?\?)'
       why='Measure-Object -Sum returns $null on empty; arithmetic then silently 0' }
    @{ id='bash-head-tail'; cost=4; rx='\|\s*(head|tail)\b'   # pwsh-xp:ignore bash-head-tail
       why='use Select-Object -First/-Last; head/tail are not PowerShell' }
    @{ id='selectstring-matches'; cost=5; rx='\(Select-String[^)]*\)\.Matches'
       why='throws when the result is not a collection; iterate MatchInfo instead' }
    # Narrow deliberately: `& $someExe ... 2>&1` is CORRECT — a native binary
    # writes to real stderr and merging it is the right move. The mistake only
    # exists when the target is a .ps1, whose Write-Host output goes to the
    # information stream (6) and is invisible to 2>&1. Flagging the native case
    # too would make this rule cry wolf, and a linter that cries wolf gets
    # muted, which is worse than not having it.
    @{ id='stderr-only-capture'; cost=5; rx='\.ps1[''"]?\s*\)?[^\r\n|]*2>&1'
       why='.ps1 reports via Write-Host on stream 6; 2>&1 captures none of it — use *>&1' } # pwsh-xp:ignore stderr-only-capture
    @{ id='unquoted-dash-d'; cost=3; rx='(?<![''"])-D[A-Za-z_][A-Za-z0-9_]*=[^\s''"]*\.[0-9]'
       why='a bare -DFOO=3.5 splits at the dot and passes ".5" as a stray path' } # pwsh-xp:ignore unquoted-dash-d
    @{ id='shadowed-matches'; cost=4; rx='\$matches\s*='
       why='$matches is an automatic variable — shadowing it corrupts -match' }
)

# ── Collect targets ─────────────────────────────────────────────────────────
if (-not (Test-Path -LiteralPath $Path)) { throw "path not found: $Path" }
$files = @(
    if ((Get-Item -LiteralPath $Path).PSIsContainer) {
        Get-ChildItem -LiteralPath $Path -Recurse -File -Filter *.ps1 -EA SilentlyContinue
    } else { Get-Item -LiteralPath $Path }
)

# An empty target set is UNKNOWN, not clean. Refuse to award a passing rank for
# having examined nothing — that is the exact failure this tool exists to catch.
if ($files.Count -eq 0) {
    Write-Host "pwsh-experience: no .ps1 files under '$Path' — nothing examined." -ForegroundColor Yellow
    Write-Host "  An empty result is not a pass. Exiting 2." -ForegroundColor Yellow
    exit 2
}

# ── Layer 1: syntax (blocking) ──────────────────────────────────────────────
$syntaxErrors = [System.Collections.Generic.List[object]]::new()
foreach ($f in $files) {
    $errs = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$null, [ref]$errs)
    foreach ($e in @($errs)) {
        $syntaxErrors.Add([pscustomobject]@{
            File = $f.Name; Line = $e.Extent.StartLineNumber; Msg = $e.Message
        })
    }
}

# ── Layer 2: object-shell rules (scored) ────────────────────────────────────
$findings = [System.Collections.Generic.List[object]]::new()
$muted    = [System.Collections.Generic.List[object]]::new()
foreach ($f in $files) {
    $lines = @(Get-Content -LiteralPath $f.FullName -EA SilentlyContinue)
    # Whether a rule applies can depend on the file's own strictness setting, so
    # establish it once per file rather than assuming the worst everywhere.
    $strictOn = @($lines | Where-Object { $_ -match '^\s*Set-StrictMode\s+-Version' }).Count -gt 0
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -match '^\s*#') { continue }        # comments are not code
        # A suppression must NAME the rule it silences. A blanket `ignore` would
        # let one marker mute rules added later, which is how suppression lists
        # rot into blindfolds. Every mute is also counted and printed — an
        # invisible suppression is indistinguishable from a passing check.
        $mutes = @(if ($line -match '#\s*pwsh-xp:ignore\s+([a-z0-9,\-\s]+)') {
                       $Matches[1] -split '[,\s]+' | Where-Object { $_ }
                   })
        foreach ($r in $RULES) {
            # ContainsKey, not $r.strictOnly — asking a hashtable for a key it
            # does not have is exactly the silent-$null habit this tool bills for.
            if ($r.ContainsKey('strictOnly') -and -not $strictOn) { continue }
            if ($line -match $r.rx) {
                $row = [pscustomobject]@{
                    File = $f.Name; Line = $i + 1; Rule = $r.id; Cost = $r.cost; Why = $r.why
                }
                if ($mutes -contains $r.id) { $muted.Add($row) } else { $findings.Add($row) }
            }
        }
    }
}

# ── Score ───────────────────────────────────────────────────────────────────
$penalty = 0
foreach ($x in $findings) { $penalty += $x.Cost }
# $findings.File is member enumeration over a List — it THROWS on an empty list
# under StrictMode Latest. This is the exact failure class this tool scores, and
# it shipped in the tool itself, surfacing only once a scan came back clean.
# The success path is the one nobody tests.
$dirty  = @(if ($findings.Count -gt 0) { $findings | ForEach-Object { $_.File } | Sort-Object -Unique })
# A file that is only quiet because it suppressed something is not clean, it is
# neutral. Paying the clean bonus for it would make muting profitable.
$mutedF = @(if ($muted.Count -gt 0) { $muted | ForEach-Object { $_.File } | Sort-Object -Unique })
# A file that does not parse produces no rule findings — not because it is clean
# but because the scanner never got to read it. Paying the bonus there rewards
# unparseable code, which is the inverse of the point.
$brokeF = @(if ($syntaxErrors.Count -gt 0) { $syntaxErrors | ForEach-Object { $_.File } | Sort-Object -Unique })
$clean  = $files.Count - @($dirty + $mutedF + $brokeF | Sort-Object -Unique).Count
$reward = $clean * 2
$delta  = $reward - $penalty
# Charged per unparseable FILE, not per reported error. One unclosed brace makes
# the parser emit three cascading errors; billing each one turns a single typo
# into a triple fine and makes the number say more than the mistake does.
$delta -= 10 * $brokeF.Count

$rank = if ($syntaxErrors.Count -gt 0) { 0 }
        elseif ($findings.Count -eq 0) { 4 }
        elseif ($penalty -le 6)        { 3 }
        elseif ($penalty -le 20)       { 2 }
        else                           { 1 }
$r = $RANKS[$rank]

# ── Report ──────────────────────────────────────────────────────────────────
if (-not $Quiet) {
    Write-Host ""
    Write-Host "pwsh-experience  —  $($files.Count) file(s)" -ForegroundColor Cyan
    if ($syntaxErrors.Count -gt 0) {
        Write-Host "`n  SYNTAX — BLOCKING" -ForegroundColor Red
        foreach ($e in $syntaxErrors) { Write-Host "    $($e.File):$($e.Line)  $($e.Msg)" -ForegroundColor Red }
    } else {
        Write-Host "  syntax: clean ($($files.Count) parsed, none executed)" -ForegroundColor Green
    }
    if ($findings.Count -gt 0) {
        Write-Host "`n  OBJECT-SHELL FINDINGS" -ForegroundColor Yellow
        foreach ($x in ($findings | Sort-Object Cost -Descending)) {
            Write-Host ("    -{0,-2} {1,-22} {2}:{3}" -f $x.Cost, $x.Rule, $x.File, $x.Line) -ForegroundColor Yellow
            Write-Host ("         {0}" -f $x.Why) -ForegroundColor DarkGray
        }
    }
    if ($muted.Count -gt 0) {
        Write-Host "`n  SUPPRESSED (declared, no bonus paid)" -ForegroundColor DarkCyan
        foreach ($x in $muted) {
            Write-Host ("     0  {0,-22} {1}:{2}" -f $x.Rule, $x.File, $x.Line) -ForegroundColor DarkCyan
        }
    }
    $sign = if ($delta -ge 0) { "+" } else { "" }
    Write-Host ""
    Write-Host ("  RANK $($r.n) — $($r.t)") -ForegroundColor $(if ($rank -ge 3) { 'Green' } elseif ($rank -ge 1) { 'Yellow' } else { 'Red' })
    Write-Host ("  $($r.d)") -ForegroundColor DarkGray
    Write-Host ("  XP $sign$delta   (clean +$reward / findings -$penalty)")
    if ($rank -lt 4) { Write-Host ("  next: $($RANKS[$rank + 1].t) — $($RANKS[$rank + 1].d)") -ForegroundColor DarkGray }
    Write-Host ""
}

# ── Emit a trail event the existing XP engine will pick up ──────────────────
if ($Emit) {
    # The trail is written by a profile hook that fires in every pwsh session in
    # every directory, so it is global but project-blind — no event in 22,804
    # carried any attribution. Without this, a Sol Foundry scan and a
    # chthonic-archive scan are the same row, and the XP means nothing per repo.
    $scanned = (Resolve-Path -LiteralPath $Path).Path
    $holder  = if (Test-Path -LiteralPath $scanned -PathType Container) { $scanned } else { Split-Path -Parent $scanned }
    $probe   = $holder
    $project = $null
    while ($probe -and -not $project) {
        if (Test-Path -LiteralPath (Join-Path $probe '.git')) { $project = Split-Path -Leaf $probe; break }
        $parent = Split-Path -Parent $probe
        if ($parent -eq $probe) { break }
        $probe = $parent
    }
    # No .git anywhere up the tree — Sol Foundry is currently such a case. Name it
    # after the directory actually scanned, not its parent: walking up one level
    # on a miss reports the containing folder as the project, which is wrong and
    # silently wrong (it still produces a plausible-looking name).
    if (-not $project) { $project = Split-Path -Leaf $holder }

    New-Item -ItemType Directory -Force $TrailDir | Out-Null
    $file = Join-Path $TrailDir ("{0}.hot.ndjson" -f (Get-Date -Format 'yyyy-MM-dd'))
    $stamp = [DateTimeOffset]::UtcNow
    $ev = [ordered]@{
        # Both stamps, deliberately. The PowerShell lane reads `ts` (unix ms);
        # ankh-forge's REM schema requires `at` as a non-Option RFC 3339 field
        # (event.rs:40) and cannot deserialize a row without it. 22,758 of 22,809
        # existing events lack `at`, so the whole hot->cold->.runestone pipeline
        # is blind to them. Emitting one stamp would have picked a side silently.
        # ONE clock read, both formats derived from it. Calling UtcNow twice put
        # ts and at a millisecond apart in a real event tonight — a provenance
        # record that disagrees with itself about when it happened.
        ts        = $stamp.ToUnixTimeMilliseconds()
        at        = $stamp.UtcDateTime.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
        type      = 'diagnostic'
        kind      = 'pwsh_experience'
        p         = 2
        sid       = (New-Guid).ToString('N').Substring(0, 8)
        msg       = "pwsh-experience rank $($r.n) ($($r.t)) — $($files.Count) file(s), $($findings.Count) finding(s), $($syntaxErrors.Count) syntax error(s)"
        xp_delta  = $delta
        project   = $project
        scanned   = $scanned
        rank      = $r.n
        findings  = $findings.Count
        suppressed= $muted.Count
        syntax    = $syntaxErrors.Count
    }
    ($ev | ConvertTo-Json -Compress) | Add-Content -LiteralPath $file -Encoding UTF8
    if (-not $Quiet) { Write-Host "  trail event -> $file" -ForegroundColor DarkGray }
}

# ── Gate ────────────────────────────────────────────────────────────────────
if ($syntaxErrors.Count -gt 0) { exit 1 }
if ($Strict -and $findings.Count -gt 0) { exit 1 }
exit 0
