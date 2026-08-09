#!/usr/bin/env pwsh
#-*- coding: utf-8 -*-
<#
.SYNOPSIS
xp-parity — proves the XP family agrees, instead of asserting it in a comment.

@SID:    TOOL_XP_PARITY_V1
@Type:   Contract check
@Output: per-implementation XP over one shared trail, plus drift causes

.DESCRIPTION
Four things in this repo compute or emit XP from the same trail:

  1. scripts/chthonic-xp.ps1        the engine the prompt actually renders
  2. ~/.config/powershell/profile.ps1  an INLINE MIRROR of the tables, needed
                                    because parent funcs are absent in that runspace
  3. tools/chthonic-cai/src/xp.rs   Rust, comment says "must stay in sync"
  4. scripts/pwsh-experience.ps1    emits scored events with explicit xp_delta

Nothing ever checked (2) and (3) against (1). "Must stay in sync" is a wish
unless something fails when it isn't, so this is that something.

The canonical implementation is chthonic-xp.ps1: it is what the prompt shows,
it carries the complete kind table, and it deliberately excludes session
bookkeeping on the grounds that work earns XP and presence does not.

.EXAMPLE
  ./xp-parity.ps1
  ./xp-parity.ps1 -Emit     # record the drift as a trail diagnostic
#>

[CmdletBinding()]
param([switch]$Emit, [switch]$Quiet)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root     = Split-Path -Parent $PSScriptRoot
$TrailDir = Join-Path $Root '.chthonic\trail'
$Engine   = Join-Path $PSScriptRoot 'chthonic-xp.ps1'
$CaiSrc   = Join-Path $Root 'tools\chthonic-cai\src\xp.rs'

# ── Load the trail once; every implementation scores the SAME events ─────────
$files = @(Get-ChildItem -LiteralPath $TrailDir -Filter '*.hot.ndjson' -EA SilentlyContinue | Sort-Object Name)
if ($files.Count -eq 0) { throw "no trail files under $TrailDir — refusing to report parity on nothing" }

$events = @($files | ForEach-Object {
    @(Get-Content -LiteralPath $_.FullName) |
        Where-Object { $_.Trim() } |
        ForEach-Object { try { $_ | ConvertFrom-Json } catch { } }
})
if ($events.Count -eq 0) { throw "trail files exist but parsed to zero events — that is unknown, not clean" }

# ── The tables, stated once, as data ────────────────────────────────────────
$BASE     = @{ artifact=10; decision=8; diagnostic=5; memory=4; recovery=15; snapshot=3; meta=5 }
$KIND_PS  = @{ 'epoch-close'=45; git_commit=5; wiring=3; redux=8; roulette_steward=12; bounty_hunt=20; pwsh_fullstack=15 }
$META     = @('session_start','session_end','zjit-session','msys2-session')

# cai is INVOKED, not transcribed. An earlier version of this script re-implemented
# xp.rs's rules here in PowerShell; the moment xp.rs was fixed, that copy started
# reporting a drift that no longer existed — a checker lying about the thing it
# checks. Running the real binary cannot go stale, which is the whole point.
$CaiExe = Join-Path $Root 'target\debug\cai.exe'

# Trail events are heterogeneous JSON — `type`, `kind` and `p` are each absent on
# some rows. Under StrictMode Latest a bare $e.p on a row without it THROWS, and
# that is the failure this whole family keeps producing. Ask before reading.
function Get-Field {
    param($obj, [string]$name)
    $prop = $obj.PSObject.Properties[$name]
    if ($null -ne $prop) { return $prop.Value }
    return $null
}

function Measure-Variant {
    param($events, $kindTable, [switch]$SkipMeta, [switch]$HonorDelta, [double]$DefaultPrio)
    $total = 0.0
    foreach ($e in $events) {
        $kind = Get-Field $e 'kind'
        if ($SkipMeta -and $kind -and $META -contains [string]$kind) { continue }
        if ($HonorDelta) {
            $d = Get-Field $e 'xp_delta'
            if ($null -ne $d) { $total += [int]$d; continue }
        }
        $type = Get-Field $e 'type'
        $prio = Get-Field $e 'p'
        $b = if ($type -and $BASE.ContainsKey([string]$type)) { $BASE[[string]$type] } else { 1 }
        $k = if ($kind -and $kindTable.ContainsKey([string]$kind)) { $kindTable[[string]$kind] } else { 0 }
        $p = if ($null -ne $prio -and @(1,2,3) -contains [int]$prio) { @{1=1.5;2=1.0;3=0.75}[[int]$prio] } else { $DefaultPrio }
        $total += [Math]::Round(($b + $k) * $p)
    }
    return [int]$total
}

$psXp  = Measure-Variant -events $events -kindTable $KIND_PS  -SkipMeta -HonorDelta -DefaultPrio 1.0

# Ask the real binary. Empty stdin makes cai print its XP banner and exit at EOF.
$caiXp = $null; $caiNote = ''
if (Test-Path -LiteralPath $CaiExe) {
    $caiOut = ("" | & $CaiExe 2>&1 | Out-String)
    $m = [regex]::Match($caiOut, '\[XP\]\s+Lv\.\d+\s+\S+\s+\[[^\]]*\]\s+(\d+)\s+XP')
    if ($m.Success) { $caiXp = [int]$m.Groups[1].Value }
    else { $caiNote = 'binary ran but printed no parseable XP line' }
} else {
    $caiNote = "not built — cargo build -p chthonic-cai"
}

# ── Positive control: the transcription above must reproduce the REAL engine ─
# Comparing two of my own reimplementations would prove nothing. Ask the engine.
$engineRaw = @(& $Engine -XPDebug *>&1 | Out-String -Width 300) -split "`r?`n"
$dbgLine   = @($engineRaw | Where-Object { $_ -match 'Raw XP:\s*(\d+)' })
$engineXp  = if ($dbgLine.Count -gt 0 -and $dbgLine[0] -match 'Raw XP:\s*(\d+)') { [int]$Matches[1] } else { $null }
$faithful  = ($null -ne $engineXp) -and ($engineXp -eq $psXp)

# ── Context for interpreting a drift, derived rather than asserted ───────────
# Deliberately NOT a list of cai's known bugs: those were fixed on 2026-08-09 and
# a hardcoded cause list would have started lying the moment they were. These are
# standing properties of the trail that make a divergence legible whatever caused it.
$metaEvents = @($events | Where-Object { $k = Get-Field $_ 'kind'; $k -and $META -contains [string]$k })
$deltaEvents= @($events | Where-Object { $null -ne (Get-Field $_ 'xp_delta') })
$noPrio     = @($events | Where-Object { $null -eq (Get-Field $_ 'p') })

$level = { param($x) [Math]::Floor([Math]::Sqrt($x / 10)) }

if (-not $Quiet) {
    Write-Host ""
    Write-Host "xp-parity  —  $($events.Count) events across $($files.Count) trail file(s)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host ("  {0,-34} {1,10} {2,8}" -f 'implementation', 'xp', 'level') -ForegroundColor DarkGray
    Write-Host ("  {0,-34} {1,10} {2,8}   canonical" -f 'chthonic-xp.ps1', $psXp,  (& $level $psXp)) -ForegroundColor Green
    if ($null -eq $caiXp) {
        Write-Host ("  {0,-34} {1,10} {2,8}   {3}" -f 'cai (target\debug\cai.exe)', '—', '—', $caiNote) -ForegroundColor Yellow
    } else {
        Write-Host ("  {0,-34} {1,10} {2,8}" -f 'cai (target\debug\cai.exe)', $caiXp, (& $level $caiXp)) -ForegroundColor $(if ($caiXp -eq $psXp) { 'Green' } else { 'Red' })
    }
    Write-Host ""
    if ($faithful) {
        Write-Host "  control: transcription reproduces the live engine exactly ($engineXp)" -ForegroundColor Green
    } else {
        Write-Host "  control: FAILED — transcription $psXp vs live engine $engineXp." -ForegroundColor Red
        Write-Host "           Every number below is therefore untrustworthy." -ForegroundColor Red
    }
    if ($null -eq $caiXp) {
        Write-Host ""
        Write-Host "  cai NOT COMPARED — $caiNote" -ForegroundColor Yellow
        Write-Host "  An uncomparable lane is unknown, not agreeing. Exiting 2." -ForegroundColor Yellow
    } elseif ($caiXp -ne $psXp) {
        Write-Host ""
        Write-Host "  DRIFT  $([Math]::Abs($caiXp - $psXp)) XP" -ForegroundColor Red
        Write-Host "  Standing properties of this trail, to locate the cause:" -ForegroundColor DarkGray
        Write-Host "    - $($metaEvents.Count) of $($events.Count) events are session bookkeeping (skipped by the engine)" -ForegroundColor Yellow
        Write-Host "    - $($deltaEvents.Count) event(s) carry an explicit xp_delta that must outrank the type table" -ForegroundColor Yellow
        Write-Host "    - $($noPrio.Count) event(s) carry no priority; the engine defaults those to 1.0, not 0.75" -ForegroundColor Yellow
        Write-Host "    - a BOM'd first line deserialises in PowerShell but not in Rust unless stripped" -ForegroundColor Yellow
        Write-Host "      (tools/chthonic-cai/src/xp.rs read_trail; ankh-forge event.rs:23 does the same)" -ForegroundColor DarkGray
    }
    Write-Host ""
}

if ($Emit) {
    $file = Join-Path $TrailDir ("{0}.hot.ndjson" -f (Get-Date -Format 'yyyy-MM-dd'))
    $stamp = [DateTimeOffset]::UtcNow
    ([ordered]@{
        # `at` satisfies ankh-forge's REM schema, `ts` the PowerShell lane. See
        # the note in pwsh-experience.ps1 — the two lanes never agreed on a stamp.
        # One clock read, both formats derived: two UtcNow calls drift a
        # millisecond apart and the event then contradicts its own timestamp.
        ts = $stamp.ToUnixTimeMilliseconds()
        at = $stamp.UtcDateTime.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
        type = 'diagnostic'; kind = 'xp_parity'; p = 2
        sid = (New-Guid).ToString('N').Substring(0,8)
        msg = "xp-parity: engine $psXp vs cai $caiXp over $($events.Count) events"
        xp_delta = 0; engine_xp = $psXp
        cai_xp = $caiXp                                              # $null when the binary is absent/unparseable
        drift = $(if ($null -eq $caiXp) { $null } else { $caiXp - $psXp })
        cai_note = $caiNote; control_ok = $faithful
    } | ConvertTo-Json -Compress) | Add-Content -LiteralPath $file -Encoding UTF8
}

if (-not $faithful)   { exit 2 }   # cannot trust the comparison at all
if ($null -eq $caiXp) { exit 2 }   # cai uncomparable — unknown, NOT agreeing
if ($caiXp -ne $psXp) { exit 1 }   # family is out of sync
exit 0
