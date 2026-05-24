#!/usr/bin/env pwsh
#
# @SID: SCRIPT_RESTRUCTURE_CODEX_V1
# @Type: AGENT
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Restructure codex folder
#

# Restructure codex folder
$codexRoot = Join-Path $PSScriptRoot "..\..\codex"

# Move protocols
if (Test-Path "$codexRoot\SLEEPERS_HOLD_PROTOCOL.md") {
    Move-Item "$codexRoot\SLEEPERS_HOLD_PROTOCOL.md" "$codexRoot\protocols\" -Force
    Write-Host "Moved: SLEEPERS_HOLD_PROTOCOL.md -> protocols/"
}

# Move handoffs
Get-ChildItem "$codexRoot\SESSION_HANDOFF_*.md" -ErrorAction SilentlyContinue | ForEach-Object {
    Move-Item $_.FullName "$codexRoot\handoffs\" -Force
    Write-Host "Moved: $($_.Name) -> handoffs/"
}

# Move checkpoints
Get-ChildItem "$codexRoot\SESSION_CHECKPOINT_*.md" -ErrorAction SilentlyContinue | ForEach-Object {
    Move-Item $_.FullName "$codexRoot\checkpoints\" -Force
    Write-Host "Moved: $($_.Name) -> checkpoints/"
}
Get-ChildItem "$codexRoot\REFINEMENT_PASS_*.md" -ErrorAction SilentlyContinue | ForEach-Object {
    Move-Item $_.FullName "$codexRoot\checkpoints\" -Force
    Write-Host "Moved: $($_.Name) -> checkpoints/"
}

# Move reports
if (Test-Path "$codexRoot\gemini_mcp_status_report.md") {
    Move-Item "$codexRoot\gemini_mcp_status_report.md" "$codexRoot\reports\" -Force
    Write-Host "Moved: gemini_mcp_status_report.md -> reports/"
}
Get-ChildItem "$codexRoot\CREATIVE_PRIMING_*.md" -ErrorAction SilentlyContinue | ForEach-Object {
    Move-Item $_.FullName "$codexRoot\reports\" -Force
    Write-Host "Moved: $($_.Name) -> reports/"
}

Write-Host "`nRestructure complete!"

