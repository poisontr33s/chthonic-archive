#!/usr/bin/env pwsh
# @SID: SCRIPT_VALIDATE_TRIAD_LINKS_V1
# @Type: SHIM
# @Purpose: Thin delegate — wraps link_audit.py scan for triad markdown files.
# Legacy callers preserved. Original triad-specific logic in .deprecated/validate-triad-links.ps1.
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)
$triadFiles = @(
    "AGENT_COMMON.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md",
    "codex/NEXT.md",
    "claude-codex-gemini/TRIAD_DOC_CONSOLIDATION_STRATEGY.md",
    "claude-codex-gemini/triadic-session-shared-0001.md",
    "claude-codex-gemini/triadic-session-shared-0002.md"
)
$existing = $triadFiles | Where-Object { Test-Path (Join-Path $RepoRoot $_) }
if ($existing.Count -eq 0) {
    Write-Warning "No triad files found under $RepoRoot"
    exit 1
}
$fileArgs = $existing | ForEach-Object { "--file", (Join-Path $RepoRoot $_) }
uv run "$PSScriptRoot/link_audit.py" scan @fileArgs
