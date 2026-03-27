#!/usr/bin/env pwsh
#
# @SID: SCRIPT_RUN_GEM_POLISHER_V1
# @Type: RUNNER
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: [string]$Root = ".claude/skills"
#

param(
  [string]$Root = ".claude/skills"
)

.\scripts\run_claude_skill_polisher.ps1 -Root $Root

