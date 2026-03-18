---
type: mailbox-state
updated: 2026-03-18T00:13:16.123166+00:00
mailbox: claude/mailbox
---

# Mailbox Current State

## Root Summary
- Root files: `75`
- Root directories: `1`
- Archive file count: `37`
- Latest aliases at root: `24`
- Timestamped root files: `23`

## Protected Surfaces
- `MAILBOX_CURRENT_STATE.md`
- `mailbox_manifest.json`
- `ACTUAL-WORKING-HANDOFFS/`
- `archive/`

## Root Series Under Rotation Policy
- none

## Root Latest Aliases
- `CLAUDE_SKILL_POLISH_SUMMARY_LATEST.md`
- `CODEX_TO_CLAUDE_TASK_LATEST.md`
- `GIT_SNAPSHOT_LATEST.md`
- `HANDOFF_AUDIT_LATEST.json`
- `HANDOFF_AUDIT_LATEST.md`
- `LOCAL_AI_READINESS_LATEST.json`
- `LOCAL_AI_READINESS_LATEST.md`
- `MAILBOX_HANDOFF_VERIFICATION_LATEST.md`
- `POE_API_DUAL_DISCREPANCY_LATEST.json`
- `POE_API_DUAL_DISCREPANCY_LATEST.md`
- `POE_API_SETUP_PULL_LATEST.json`
- `POE_API_SETUP_PULL_LATEST.md`
- `POE_CALLABILITY_REGISTRY_LATEST.json`
- `POE_CALLABILITY_REGISTRY_LATEST.md`
- `POE_LANE_LATEST.json`
- `POE_LANE_LATEST.md`
- `POE_SDK_LATEST.json`
- `POE_SDK_LATEST.md`
- `POE_TRANSPORT_AUDIT_LATEST.json`
- `POE_TRANSPORT_AUDIT_LATEST.md`
- `SCM_TRIAGE_SNAPSHOT_LATEST.md`
- `VSCODE_ELECTRON_HARDENER_LATEST.md`
- `VSCODE_ERROR_AUTOPSY_LATEST.json`
- `VSCODE_ERROR_AUTOPSY_LATEST.md`

## Root Directory Series
- none

## Policy
- Root mailbox keeps current-cycle files, latest aliases, and protected working handoffs.
- Timestamped series with more than three members are rotation candidates.
- Rotation always archives; it never deletes.
- `.tmp_fixture_eval/` is temporary fixture output and should not be treated as a durable active handoff lane.
