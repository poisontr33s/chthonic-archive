#!/usr/bin/env pwsh

param(
  [string]$CodexRoot = ".codex/skills",
  [string]$ClaudeRoot = ".claude/skills"
)

$ErrorActionPreference = "Stop"

Write-Host "E2E Skill Matrix (Claude-side): start"

# 1) Four-way flavor/root matrix (Claude-side artifact paths)
uv run scripts/skill_audit.py --flavor codex --root $CodexRoot --json --json-path claude/mailbox/e2e_matrix_codex_on_codex.json
uv run scripts/skill_audit.py --flavor codex --root $ClaudeRoot --json --json-path claude/mailbox/e2e_matrix_codex_on_claude.json
uv run scripts/skill_audit.py --flavor claude --root $CodexRoot --json --json-path claude/mailbox/e2e_matrix_claude_on_codex.json
uv run scripts/skill_audit.py --flavor claude --root $ClaudeRoot --json --json-path claude/mailbox/e2e_matrix_claude_on_claude.json

# 2) Hook-level cross runs
./scripts/run_codex_polisher.ps1 -Root $CodexRoot
./scripts/run_claude_skill_polisher.ps1 -Root $ClaudeRoot
./scripts/run_claude_cross_polish.ps1 -CodexRoot $CodexRoot -ClaudeRoot $ClaudeRoot

# 3) Meta validators + policy/layout (Claude-side artifact paths where applicable)
uv run scripts/validate_meta_polishers.py
uv run scripts/validate_claude_meta.py
uv run scripts/check_python_policy.py
uv run scripts/check_mailbox_layout.py

Write-Host "E2E Skill Matrix (Claude-side): complete"
