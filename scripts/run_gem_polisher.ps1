#!/usr/bin/env pwsh

param(
  [string]$Root = ".claude/skills"
)

.\scripts\run_claude_skill_polisher.ps1 -Root $Root

