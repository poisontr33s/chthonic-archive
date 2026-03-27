#!/usr/bin/env pwsh
#
# @SID: SCRIPT_RUN_CLAUDE_LOCAL_AUDIT_V1
# @Type: VALIDATION
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: [string]$Root = ".claude/skills"
#

param(
  [string]$Root = ".claude/skills"
)

uv run scripts/skill_audit.py --flavor claude --root $Root --json --json-path claude/mailbox/skill_audit_claude.json
uv run scripts/validate_claude_meta.py

