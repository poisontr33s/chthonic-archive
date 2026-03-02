#!/usr/bin/env pwsh

param(
  [string]$Root = ".claude/skills"
)

uv run scripts/skill_audit.py --flavor claude --root $Root --json --json-path claude/mailbox/skill_audit_claude.json
uv run scripts/validate_claude_meta.py

