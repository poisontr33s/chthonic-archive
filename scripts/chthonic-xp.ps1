#!/usr/bin/env pwsh
#-*- coding: utf-8 -*-
<#
.SYNOPSIS
Chthonic Archive XP Engine — derives XP and achievements from .chthonic/trail/ events.

@SID:    TOOL_CHTHONIC_XP_V1
@Type:   Gamification
@Output: Compact startup status line (level, XP bar, unlocked achievements)
#>

param(
    [string]$TrailDir = (Join-Path (Split-Path -Parent $PSScriptRoot) '.chthonic\trail'),
    [string]$StateFile = (Join-Path $env:USERPROFILE 'chthonic-archive\.chthonic\xp-state.json'),
    [switch]$Quiet,   # suppress output, just update state
    [switch]$XPDebug  # print event count and XP breakdown
)

Set-StrictMode -Off

# ── XP table: type → base XP (priority multiplier applied below) ──────────────
$XP_BASE = @{
    artifact   = 10
    decision   = 8
    diagnostic = 5
    memory     = 4
    recovery   = 15
    snapshot   = 3
    meta       = 5
}
$XP_KIND_BONUS = @{
    'epoch-close'     = 45   # stacks with meta base = 50 total
    git_commit        = 5    # stacks with artifact base = 15 total
    wiring            = 3    # stacks with diagnostic/decision
    redux             = 8    # alchemy/SSOT-promotion transforms — stacks with artifact/decision/meta
    roulette_steward  = 12   # roulette chain item completion — stacks with artifact/meta base
    bounty_hunt       = 20   # Bounty-Hunt-Sync metadata enrichment cycle
    pwsh_fullstack    = 15   # full-stack pwsh engineering: backend dispatch + frontend display
}
$PRIORITY_MULT = @{ 1 = 1.5; 2 = 1.0; 3 = 0.75 }

# ── Level titles ──────────────────────────────────────────────────────────────
$LEVELS = @(
    'Initiate', 'Apprentice', 'Adept', 'Journeyman', 'Craftsman',
    'Expert', 'Master', 'Archivist', 'Sage', 'Oracle', 'Sovereign'
)

# ── Achievements ──────────────────────────────────────────────────────────────
$ACHIEVEMENTS = @(
    @{ id = 'trail-keeper';   name = 'Trail Keeper';   icon = '[T]'; check = { param($ev) $ev.Count -ge 10 } }
    @{ id = 'centurion';      name = 'Centurion';      icon = '[C]'; check = { param($ev) $ev.Count -ge 100 } }
    @{ id = 'epoch-closer';   name = 'Epoch Closer';   icon = '[E]'; check = { param($ev) ($ev | Where-Object { $_.type -eq 'meta' -and $_.kind -eq 'epoch-close' }).Count -gt 0 } }
    @{ id = 'phantom-slayer'; name = 'Phantom Slayer'; icon = '[!]'; check = {
        param($ev) ($ev | Where-Object { $_.msg -match 'phantom|0-byte|System32|extensionless' }).Count -gt 0 }}
    @{ id = 'path-surgeon';   name = 'PATH Surgeon';   icon = '[P]'; check = {
        param($ev) ($ev | Where-Object { $_.msg -match 'msys64|usr.bin|PATH.*clean|HKLM|Python314' }).Count -gt 0 }}
    @{ id = 'type-detective'; name = 'Type Detective'; icon = '[D]'; check = {
        param($ev) ($ev | Where-Object { $_.msg -match 'Object\[\]|IVE|Invoke-Expression|join.*NewLine' }).Count -gt 0 }}
    @{ id = 'clean-room';     name = 'Clean Room';     icon = '[=]'; check = {
        param($ev) ($ev | Where-Object { $_.msg -match 'dedup|duplicate|unique|no dupl' }).Count -gt 0 }}
    @{ id = 'git-scribe';     name = 'Git Scribe';     icon = '[G]'; check = {
        param($ev) ($ev | Where-Object { $_.kind -eq 'git_commit' }).Count -ge 3 }}
    @{ id = 'recover-ward';   name = 'Recovery Ward';  icon = '[R]'; check = {
        param($ev) ($ev | Where-Object { $_.type -eq 'recovery' }).Count -gt 0 }}
    @{ id = 'alchemist';      name = 'Alchemist';       icon = '[A]'; check = {
        param($ev) ($ev | Where-Object { $_.kind -eq 'redux' }).Count -gt 0 }}
    @{ id = 'roulette-steward'; name = 'Roulette Steward'; icon = '[S]'; check = {
        param($ev) ($ev | Where-Object { $_.kind -eq 'roulette_steward' -or $_.msg -match 'roulette' }).Count -ge 1 }}
    @{ id = 'bounty-hunter';    name = 'Bounty Hunter';    icon = '[B]'; check = {
        param($ev) ($ev | Where-Object { $_.kind -eq 'bounty_hunt' -or $_.msg -match 'Bounty-Hunt' }).Count -ge 1 }}
    @{ id = 'shell-architect';  name = 'Shell Architect';  icon = '[F]'; check = {
        param($ev)
        $hasBackend  = ($ev | Where-Object { $_.msg -match 'chthonic\.ps1|dispatch|bridge.*service|Invoke-Chthonic' }).Count -gt 0
        $hasFrontend = ($ev | Where-Object { $_.msg -match 'chthonic-xp|cai\.exe|xp-state|XP.*bar|XP.*engine' }).Count -gt 0
        $hasBackend -and $hasFrontend }}
    @{ id = 'zjit-rider'; name = 'ZJIT Rider'; icon = '[Z]'; check = {
        param($ev)
        # ZJIT recorded in trail (legacy zjit-session marker OR session_start.zjit)
        # AND real work must exist — env presence alone does not unlock this
        $hasZjit = ($ev | Where-Object {
            ($_.kind -eq 'zjit-session') -or
            ($_.kind -eq 'session_start' -and $_.zjit -and ([string]$_.zjit -match 'zjit'))
        }).Count -gt 0
        if (-not $hasZjit) { return $false }
        ($ev | Where-Object {
            $_.type -in @('diagnostic','artifact','decision','recovery') -and
            $_.kind -notin @('zjit-session','msys2-session','session_start','session_end')
        }).Count -ge 3
    }}
    @{ id = 'forge-ready'; name = 'Forge Ready'; icon = '[M]'; check = {
        param($ev)
        # MSYS2 recorded in trail AND real work must exist
        $hasMsys2 = ($ev | Where-Object {
            ($_.kind -eq 'msys2-session') -or
            ($_.kind -eq 'session_start' -and $_.msys2 -eq $true)
        }).Count -gt 0
        if (-not $hasMsys2) { return $false }
        ($ev | Where-Object {
            $_.type -in @('diagnostic','artifact','decision','recovery') -and
            $_.kind -notin @('zjit-session','msys2-session','session_start','session_end')
        }).Count -ge 3
    }}
)

# ── Ingest trail ──────────────────────────────────────────────────────────────
function Read-TrailEvents {
    param([string]$Dir)
    $events = [System.Collections.Generic.List[object]]::new()
    if (-not (Test-Path $Dir)) { return $events }
    Get-ChildItem $Dir -Filter '*.hot.ndjson' | Sort-Object Name | ForEach-Object {
        Get-Content $_.FullName -ErrorAction SilentlyContinue | Where-Object { $_.Trim() } | ForEach-Object {
            try { $events.Add(($_ | ConvertFrom-Json)) } catch {}
        }
    }
    return $events
}

# ── Compute XP ────────────────────────────────────────────────────────────────
function Measure-XP {
    param($events)
    $total = 0
    # Metadata kinds — session bookkeeping and env markers; earn no XP (work earns, presence doesn't)
    $metaKinds = [System.Collections.Generic.HashSet[string]]@(
        'session_start', 'session_end', 'zjit-session', 'msys2-session'
    )
    foreach ($e in $events) {
        if ($e.kind -and $metaKinds.Contains([string]$e.kind)) { continue }
        $base = if ($XP_BASE.ContainsKey($e.type)) { $XP_BASE[$e.type] } else { 1 }
        $kind = if ($e.kind -and $XP_KIND_BONUS.ContainsKey($e.kind)) { $XP_KIND_BONUS[$e.kind] } else { 0 }
        $prio = if ($e.p -and $PRIORITY_MULT.ContainsKey([int]$e.p)) { $PRIORITY_MULT[[int]$e.p] } else { 1.0 }
        $total += [Math]::Round(($base + $kind) * $prio)
    }
    return $total
}

# ── Level from XP ─────────────────────────────────────────────────────────────
function Get-Level { param([int]$xp)
    [Math]::Floor([Math]::Sqrt($xp / 10))
}
function Get-XpThreshold { param([int]$level)
    $level * $level * 10
}

# ── XP bar (10 chars) ─────────────────────────────────────────────────────────
function Get-XpBar { param([int]$xp, [int]$level)
    $lo  = Get-XpThreshold $level
    $hi  = Get-XpThreshold ($level + 1)
    $pct = if ($hi -gt $lo) { ($xp - $lo) / ($hi - $lo) } else { 1.0 }
    $filled = [Math]::Round($pct * 10)
    $bar    = ([string][char]0x2588) * $filled + ([string][char]0x2591) * (10 - $filled)
    return "[${bar}]"
}

# ── Trail event date helper (handles both 'at' ISO and 'ts' epoch-ms fields) ──
function Get-TrailDay { param($e)
    if ($e.at)  { try { return ([datetime]$e.at).ToString('yyyy-MM-dd')  } catch {} }
    if ($e.ts)  { try { return ([DateTimeOffset]::FromUnixTimeMilliseconds([long]$e.ts)).ToString('yyyy-MM-dd') } catch {} }
    return $null
}

# ── Main ──────────────────────────────────────────────────────────────────────

# ── Env probe — path-check only, zero subprocess cost ────────────────────────
$rubyEnvTag  = $null
$zjitActive  = $false
$msys2Active = $false

try {
    $rubyExe = Get-Command ruby -ErrorAction SilentlyContinue
    if ($rubyExe -and $rubyExe.Source) {
        if ($rubyExe.Source -match '\\rubies\\ruby-([^\\]+)\\bin\\ruby') {
            $rubyEnvTag = $matches[1]           # e.g. "4.0.3-zjit" — from rv path
            $zjitActive = [bool]($rubyEnvTag -match 'zjit')
        }
    }
} catch {}

try {
    $msys2Root = if ($env:MSYS2_HOME) { $env:MSYS2_HOME } elseif ($env:RI_DEVKIT) { $env:RI_DEVKIT } else { $null }
    if ($msys2Root -and (Test-Path (Join-Path $msys2Root 'ucrt64\bin\gcc.exe'))) {
        $msys2Active = $true
    }
} catch {}

# Env display string — shown below XP bar, only when env is populated
$envParts = @()
if ($rubyEnvTag) { $envParts += "rb:$rubyEnvTag" }
if ($msys2Active) { $envParts += 'gcc/msys2' }
$envLine = if ($envParts -and -not $Quiet) { "       env: $($envParts -join ' | ')" } else { $null }

# Early-exit: if state was written today, emit cached line and stop — no trail I/O.
# Skip cache when -XPDebug is set so live trail data and event count are printed.
if (-not $Quiet -and -not $XPDebug -and (Test-Path $StateFile)) {
    try {
        $cached = Get-Content $StateFile -Raw -ErrorAction Stop | ConvertFrom-Json
        if ($cached.updated -and ([datetime]$cached.updated).Date -eq (Get-Date).Date) {
            $cachedLevel = $cached.level
            $cachedTitle = if ($cachedLevel -lt $LEVELS.Count) { $LEVELS[$cachedLevel] } else { 'Sovereign' }
            $cachedBar   = Get-XpBar -xp $cached.xp -level $cachedLevel
            $cachedNext  = ($cachedLevel * $cachedLevel * 10 + 2 * $cachedLevel * 10 + 10) - $cached.xp
            $cachedIcons = ($ACHIEVEMENTS | Where-Object { $_.id -in $cached.unlocked } | ForEach-Object { $_.icon }) -join ' '
            Write-Host ""
            Write-Host ("  [XP] Lv.{0} {1}  {2}  {3} XP  (+{4} -> Lv.{5})  {6}" -f `
                $cachedLevel, $cachedTitle, $cachedBar, $cached.xp, $cachedNext, ($cachedLevel + 1), $cachedIcons) -ForegroundColor Cyan
            if ($envLine) { Write-Host $envLine -ForegroundColor DarkGray }
            if ($cached.last_session_xp -and [int]$cached.last_session_xp -gt 0) {
                Write-Host ("       last session: +{0} XP  ({1})" -f [int]$cached.last_session_xp, $cached.last_session_date) -ForegroundColor DarkGray
            }
            exit 0
        }
    } catch {}
}

$events = Read-TrailEvents -Dir $TrailDir

# ── Last session delta — most recent session_end with positive XP ─────────────
$lastEndEv       = $events | Where-Object { $_.kind -eq 'session_end' -and $_.xp_delta -and [int]$_.xp_delta -gt 0 } | Select-Object -Last 1
$lastSessionXp   = if ($lastEndEv) { [int]$lastEndEv.xp_delta } else { $null }
$lastSessionDate = if ($lastEndEv) { Get-TrailDay $lastEndEv } else { $null }

$xp     = Measure-XP -events $events
$level  = Get-Level -xp $xp
$title  = if ($level -lt $LEVELS.Count) { $LEVELS[$level] } else { 'Sovereign' }
$bar    = Get-XpBar -xp $xp -level $level
$xpNext = (Get-XpThreshold ($level + 1)) - $xp

# Achievements
$prior = if (Test-Path $StateFile) {
    try { (Get-Content $StateFile -Raw | ConvertFrom-Json).unlocked } catch { @() }
} else { @() }

$unlocked = $ACHIEVEMENTS | Where-Object {
    $id = $_.id; $chk = $_.check
    try { & $chk $events } catch { $false }
} | ForEach-Object { $_.id }

$newUnlocks = $unlocked | Where-Object { $_ -notin $prior }

# Persist state
@{  xp = $xp; level = $level; unlocked = $unlocked; updated = (Get-Date -Format 'o')
    last_session_xp = $lastSessionXp; last_session_date = $lastSessionDate } |
    ConvertTo-Json -Depth 5 | Set-Content -Path $StateFile -Encoding UTF8 -ErrorAction SilentlyContinue

# ── Output ────────────────────────────────────────────────────────────────────
if (-not $Quiet) {
    $achieveStr = ($ACHIEVEMENTS | Where-Object { $_.id -in $unlocked } |
        ForEach-Object { $_.icon }) -join ' '

    $newStr = if ($newUnlocks) {
        $names = ($ACHIEVEMENTS | Where-Object { $_.id -in $newUnlocks } | ForEach-Object { $_.name }) -join ', '
        "  NEW: $names"
    } else { '' }

    Write-Host ""
    Write-Host ("  [XP] Lv.{0} {1}  {2}  {3} XP  (+{4} -> Lv.{5})  {6}" -f `
        $level, $title, $bar, $xp, $xpNext, ($level + 1), $achieveStr) -ForegroundColor Cyan
    if ($envLine) { Write-Host $envLine -ForegroundColor DarkGray }
    if ($lastSessionXp) {
        Write-Host ("       last session: +{0} XP  ({1})" -f $lastSessionXp, $lastSessionDate) -ForegroundColor DarkGray
    }
    if ($newStr) {
        Write-Host "  $newStr" -ForegroundColor Yellow
    }
    if ($XPDebug) {
        Write-Host ("  [XP Debug] Events: {0}  Raw XP: {1}  Level: {2}  To Next: {3}" -f `
            $events.Count, $xp, $level, $xpNext) -ForegroundColor DarkCyan
    }
}
