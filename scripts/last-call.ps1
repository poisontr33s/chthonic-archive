#!/usr/bin/env pwsh
#-*- coding: utf-8 -*-
<#
.SYNOPSIS
last-call — reap MCP server trees whose client is gone.

@SID:    TOOL_LAST_CALL_V1
@Type:   Housekeeping / Reaper
@Output: Table of live and orphaned trees, and a trail event when it reaps

.DESCRIPTION
The first AHA law made executable. `CLAUDEBASE/dev/null/salt-trial/AHA_MANIFEST.md`
states it in prose:

    Forgetting what you don't carry is free; forgetting what you left running
    is not. [...] So when music stops the procession walks the deck once with
    hand out. What shakes back, stays.

That is a specification, and this is the implementation. An MCP server is a
stdio process parented to its client. When the client dies the server does not:
its pipes are severed, nothing can reach it, and it goes on holding whatever it
held. Measured 2026-08-09 on this box, one `cocoindex-code` tree orphaned sixteen
hours earlier was still resident at 2,486 MB — larger than every live MCP server
combined. Reaped by hand; the OS reported +2.55 GB free.

By hand is the wrong place for it, hence this.

.PARAMETER Reap
Actually stop the orphaned trees. Omitted, the script only reports — read-only by
default, the same posture as the CI gates.

.PARAMETER Client
Process names treated as MCP clients. A tree whose root is parented to one of
these is live; anything else is an orphan. Defaults cover the Claude and VS Code
lanes.

.PARAMETER MinMB
Ignore orphan trees below this size. Default 0 — report everything, because a
small orphan is still a severed process and the count matters more than the size.

.EXAMPLE
  .\scripts\last-call.ps1
  .\scripts\last-call.ps1 -Reap
  .\scripts\last-call.ps1 -Reap -MinMB 100

.NOTES
Measure by walking process trees, never by matching names. The launcher is what
carries the server's name; the memory sits in a grandchild whose command line
does not mention it. That is exactly how the 2.4 GB stayed invisible through a
first pass built on a name regex.
#>

[CmdletBinding()]
param(
    [switch]$Reap,
    [string[]]$Client = @('claude.exe', 'Code.exe', 'Code - Insiders.exe', 'cursor.exe', 'zed.exe'),
    [double]$MinMB = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Launcher signatures. Deliberately broad: a false positive costs a line of
# output, a false negative costs gigabytes that stay invisible.
$ServerPattern = 'mcp-|mcp_|corpus-mcp|ccc\.exe\s+mcp|chthonic-mcp-server|vulkan-mcp-server|' +
                 'bevy-mcp-server|chthonic-hw-mcp-server|server-memory|sequential-thinking|' +
                 'chrome-devtools-mcp|mas_mcp|modelcontextprotocol'

# Measure-Object -Sum returns $null on an empty collection, and $null in
# arithmetic silently becomes 0 — so an empty result and a zero-sized result
# read identically. Every sum in this file goes through here.
function Get-SumOrZero {
    param($Items, [Parameter(Mandatory = $true)][string]$Property)
    $wrapped = @($Items)
    if ($wrapped.Count -eq 0) { return 0 }
    # The rule matches the expression, not the block, so it fires on the one
    # place the pattern is correct — the null check is the very next line.
    $sum = ($wrapped | Measure-Object -Property $Property -Sum).Sum  # pwsh-xp:ignore unguarded-sum
    if ($null -eq $sum) { return 0 }
    return $sum
}

$all = @(Get-CimInstance Win32_Process)
$byId = @{}
foreach ($p in $all) { $byId[[int]$p.ProcessId] = $p }

$childrenOf = @{}
foreach ($p in $all) {
    $pp = [int]$p.ParentProcessId
    if (-not $childrenOf.ContainsKey($pp)) { $childrenOf[$pp] = [System.Collections.Generic.List[object]]::new() }
    $childrenOf[$pp].Add($p)
}

function Get-Tree {
    param([int]$RootPid)
    $out = [System.Collections.Generic.List[object]]::new()
    $queue = [System.Collections.Generic.Queue[int]]::new()
    $queue.Enqueue($RootPid)
    $seen = [System.Collections.Generic.HashSet[int]]::new()
    while ($queue.Count -gt 0) {
        $cur = $queue.Dequeue()
        if (-not $seen.Add($cur)) { continue }   # cycle guard; pids get reused
        $proc = $byId[$cur]
        if ($null -eq $proc) { continue }
        $out.Add($proc)
        if ($childrenOf.ContainsKey($cur)) {
            foreach ($c in $childrenOf[$cur]) { $queue.Enqueue([int]$c.ProcessId) }
        }
    }
    return $out
}

$liveClients = @($all | Where-Object { $Client -contains $_.Name } | ForEach-Object { [int]$_.ProcessId })

# Candidate servers, then keep only tree ROOTS — a candidate whose parent is also
# a candidate is an inner link of the launcher chain, not a tree of its own.
$candidates = @($all | Where-Object {
    $_.CommandLine -and $_.CommandLine -match $ServerPattern -and $Client -notcontains $_.Name
})
$candidateIds = @($candidates | ForEach-Object { [int]$_.ProcessId })
$roots = @($candidates | Where-Object { $candidateIds -notcontains [int]$_.ParentProcessId })

$live = [System.Collections.Generic.List[object]]::new()
$orphans = [System.Collections.Generic.List[object]]::new()

foreach ($r in $roots) {
    $tree = Get-Tree -RootPid ([int]$r.ProcessId)
    $mb = [math]::Round((Get-SumOrZero -Items $tree -Property 'WorkingSetSize') / 1MB, 1)
    $parentAlive = $liveClients -contains [int]$r.ParentProcessId
    $row = [pscustomobject]@{
        RootPID = [int]$r.ProcessId
        Launcher = $r.Name
        Procs = $tree.Count
        MB = $mb
        Started = $r.CreationDate.ToString('MM-dd HH:mm')
        Tree = $tree
    }
    if ($parentAlive) { $live.Add($row) } else { $orphans.Add($row) }
}

$keep = @($orphans | Where-Object { $_.MB -ge $MinMB })
$liveMB = [math]::Round((Get-SumOrZero -Items $live -Property 'MB'), 1)
$orphMB = [math]::Round((Get-SumOrZero -Items $keep -Property 'MB'), 1)

Write-Host ''
Write-Host ("  live      {0,3} tree(s)  {1,9:N1} MB" -f $live.Count, $liveMB)
Write-Host ("  orphaned  {0,3} tree(s)  {1,9:N1} MB" -f $keep.Count, $orphMB)

if ($keep.Count -eq 0) {
    Write-Host ''
    Write-Host '  nothing left drinking. deck is clear.'
    Write-Host ''
    exit 0
}

Write-Host ''
$keep | Sort-Object MB -Descending |
    Select-Object RootPID, Launcher, Procs, MB, Started |
    Format-Table -AutoSize | Out-String | Write-Host

if (-not $Reap) {
    Write-Host '  read-only. re-run with -Reap to stop them.'
    Write-Host ''
    exit 0
}

$reaped = 0
$freed = 0.0
foreach ($o in ($keep | Sort-Object MB -Descending)) {
    # Children first: stopping a parent can orphan its children onto the system
    # tree, which is how a reap creates the thing it was sent to remove.
    foreach ($proc in ($o.Tree | Sort-Object ProcessId -Descending)) {
        try { Stop-Process -Id ([int]$proc.ProcessId) -Force -ErrorAction Stop } catch { }
    }
    $reaped++
    $freed += $o.MB
    Write-Host ("  reaped PID {0} ({1}) — {2:N1} MB" -f $o.RootPID, $o.Launcher, $o.MB)
}

# Trail event: reaping is work, and work that leaves no record earns nothing.
# Same contract as the pwsh emitter — one clock read feeding both stamps.
try {
    $repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
    $trailDir = Join-Path $repoRoot '.chthonic\trail'
    if (Test-Path -LiteralPath $trailDir) {
        $stamp = [DateTimeOffset]::UtcNow
        $event = [ordered]@{
            ts   = $stamp.ToUnixTimeMilliseconds()
            at   = $stamp.UtcDateTime.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
            type = 'artifact'
            kind = 'last_call'
            p    = 2
            msg  = "last-call reaped $reaped orphaned MCP tree(s), $([math]::Round($freed,1)) MB"
            data = [ordered]@{ trees = $reaped; freed_mb = [math]::Round($freed, 1) }
        }
        $line = $event | ConvertTo-Json -Compress -Depth 5
        Add-Content -LiteralPath (Join-Path $trailDir "$((Get-Date -Format 'yyyy-MM-dd')).hot.ndjson") `
            -Value $line -Encoding utf8
    }
} catch {
    # A failed trail write must never turn a successful reap into an error.
}

Write-Host ''
Write-Host ("  {0} tree(s) over the side. {1:N1} MB." -f $reaped, $freed)
Write-Host ''
exit 0
