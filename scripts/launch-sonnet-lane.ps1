#!/usr/bin/env pwsh
# @SID: TOOL_LAUNCH_SONNET_LANE_V1
<#
.SYNOPSIS
  Spin up the parallel Sonnet Claude Code session, pre-scoped to its lane -- one command.
.DESCRIPTION
  Compresses the manual dance (new session -> pick model -> set max thinking -> brief it on its lane)
  into a single invocation. Roots the session at the repo so it shares this project's memory (which
  already carries the lane split), then launches Sonnet on max effort with a system prompt that
  reinforces the boundary: Python embedding/clustering only, hands off the Rust daemon (the Opus lane).
  Run it in the IDE's integrated terminal for side-by-side with the Opus panel.

  Default -Model 'sonnet' draws the plan's weekly Sonnet allowance (the idle quota that was the whole
  reason for the lane). Pass the 1M metered model id only if you specifically want the giant-context
  variant ($3/$15 per Mtok -- usage credits, not the weekly bucket).
.EXAMPLE
  ./scripts/launch-sonnet-lane.ps1
.EXAMPLE
  ./scripts/launch-sonnet-lane.ps1 -Effort xhigh
#>
param(
    [string]$Model  = "sonnet",   # 'sonnet' = plan weekly quota; swap for the 1M metered id if wanted
    [string]$Effort = "max"       # max thinking (low | medium | high | xhigh | max)
)

$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo

$lane = @'
You are the SONNET PARALLEL LANE, working alongside a separate Opus session on the chthonic-archive
sonic project. YOUR lane is the PYTHON side: the texture-index work -- the PANNs CNN14 embeddings
(scripts/sonic_vocal_probe.py output), reading manifest/sonic_window_history.ndjson, clustering /
k-means of the texture vectors once volume accrues, plus exploration in probes/python/.
DO NOT edit the Rust sonic-daemon (extensions/chthonic-archive/native/sonic-daemon/, capture.rs) or
scripts/mcp-sonic.ts -- that daemon->model bridge is the Opus lane, and co-editing it on main (no
branches) clobbers. Stay Python-side, keep files disjoint from the Rust daemon, and leave git to the
conductor. The shared project memory carries the rest of the context.
'@

Write-Host "Launching Sonnet lane -- model '$Model', effort '$Effort', root $repo" -ForegroundColor Cyan
claude --model $Model --effort $Effort --name sonnet-lane --append-system-prompt $lane
