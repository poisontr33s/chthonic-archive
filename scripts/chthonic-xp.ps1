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
    'epoch-close' = 45   # stacks with meta base = 50 total
    git_commit    = 5    # stacks with artifact base = 15 total
    wiring        = 3    # stacks with diagnostic/decision
    redux         = 8    # alchemy/SSOT-promotion transforms — stacks with artifact/decision/meta
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
    foreach ($e in $events) {
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

# ── Main ──────────────────────────────────────────────────────────────────────

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
            exit 0
        }
    } catch {}
}

$events = Read-TrailEvents -Dir $TrailDir
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
@{ xp = $xp; level = $level; unlocked = $unlocked; updated = (Get-Date -Format 'o') } |
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
    if ($newStr) {
        Write-Host "  $newStr" -ForegroundColor Yellow
    }
    if ($XPDebug) {
        Write-Host ("  [XP Debug] Events: {0}  Raw XP: {1}  Level: {2}  To Next: {3}" -f `
            $events.Count, $xp, $level, $xpNext) -ForegroundColor DarkCyan
    }
}
