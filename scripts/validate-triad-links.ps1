#!/usr/bin/env pwsh
#
# @SID: SCRIPT_VALIDATE_TRIAD_LINKS_V1
# @Type: VALIDATION
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: [string]$RepoRoot = "C:\Users\erdno\chthonic-archive"
#

param(
    [string]$RepoRoot = "C:\Users\erdno\chthonic-archive"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$targets = @(
    "AGENT_COMMON.md",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "codex/NEXT.md",
    "claude-codex-gemini/TRIAD_DOC_CONSOLIDATION_STRATEGY.md",
    "claude-codex-gemini/triadic-session-shared-0001.md",
    "claude-codex-gemini/triadic-session-shared-0002.md"
)

$linkPattern = [regex]'\[([^\]]+)\]\(([^)]+)\)'
$broken = New-Object System.Collections.Generic.List[object]
$checked = 0

foreach ($rel in $targets) {
    $path = Join-Path $RepoRoot $rel
    if (-not (Test-Path $path)) {
        $broken.Add([pscustomobject]@{
            File = $path
            Link = "(missing file)"
            Resolved = $path
        })
        continue
    }

    $content = Get-Content -Path $path -Raw
    $matches = $linkPattern.Matches($content)
    foreach ($m in $matches) {
        $target = $m.Groups[2].Value.Trim()
        if ($target -match '^(https?://|mailto:|#)') { continue }
        $target = $target.Split('#')[0]
        if ([string]::IsNullOrWhiteSpace($target)) { continue }

        $checked++
        $resolved = Resolve-Path -LiteralPath (Join-Path (Split-Path $path -Parent) $target) -ErrorAction SilentlyContinue
        if (-not $resolved) {
            $broken.Add([pscustomobject]@{
                File = $path
                Link = $target
                Resolved = (Join-Path (Split-Path $path -Parent) $target)
            })
        }
    }
}

Write-Host "agents link check" -ForegroundColor Cyan
Write-Host "Checked links: $checked"
Write-Host "Broken links: $($broken.Count)"

if ($broken.Count -gt 0) {
    Write-Host "`nBroken link list:" -ForegroundColor Yellow
    $broken | Format-Table -AutoSize
    exit 1
}

Write-Host "All agents links OK." -ForegroundColor Green
exit 0


