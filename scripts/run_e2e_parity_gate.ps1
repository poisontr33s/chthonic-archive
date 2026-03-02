#!/usr/bin/env pwsh

param(
  [string]$CodexRoot = ".codex/skills",
  [string]$ClaudeRoot = ".claude/skills"
)

$ErrorActionPreference = "Stop"

Write-Host "E2E Parity Gate: start"

./scripts/run_e2e_skill_matrix.ps1 -CodexRoot $CodexRoot -ClaudeRoot $ClaudeRoot
./scripts/run_e2e_skill_matrix_claude.ps1 -CodexRoot $CodexRoot -ClaudeRoot $ClaudeRoot
uv run scripts/compare_e2e_matrices.py --codex-dir codex/mailbox --claude-dir claude/mailbox --json-out codex/mailbox/e2e_matrix_compare_summary.json

Write-Host "E2E Parity Gate: complete"
