---
type: mailbox-state
updated: 2026-03-18T00:12:45.193503+00:00
mailbox: codex/mailbox
---

# Mailbox Current State

## Root Summary
- Root files: `161`
- Root directories: `7`
- Archive file count: `449`
- Latest aliases at root: `42`
- Timestamped root files: `18`

## Protected Surfaces
- `MAILBOX_CURRENT_STATE.md`
- `mailbox_manifest.json`
- `ACTUAL-WORKING-HANDOFFS/`
- `archive/`

## Root Series Under Rotation Policy
- none

## Root Latest Aliases
- `ART_COP_HISTORY_LATEST.json`
- `ART_COP_REPORT_LATEST.md`
- `CLAUDE_IDE_HEALTH_LATEST.json`
- `CODEKILLER_REMEDIATION_PREREQ_LATEST.json`
- `CODEKILLER_REMEDIATION_PREREQ_LATEST.md`
- `HANDOFF_AUDIT_LATEST.json`
- `HANDOFF_AUDIT_LATEST.md`
- `HF_MCP_TOOLS_LATEST.json`
- `HF_MODEL_RANKING_LATEST.md`
- `HF_PREP_LATEST.json`
- `HF_PREP_LATEST.md`
- `LOCAL_AI_READINESS_LATEST.json`
- `LOCAL_AI_READINESS_LATEST.md`
- `MAILBOX_HANDOFF_VERIFICATION_LATEST.md`
- `OVERSIGHT_UPCYCLE_LATEST.json`
- `OVERSIGHT_UPCYCLE_LATEST.md`
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
- `RELATIONSHIP_AUDIT_CODEBASE_LATEST.json`
- `RELATIONSHIP_AUDIT_LATEST.json`
- `RELATIONSHIP_AUDIT_LATEST_APPLY_CHECK.json`
- `RUSTIFICATION_TREND_LATEST.json`
- `RUSTIFICATION_TREND_LATEST.md`
- `SCM_TRIAGE_SNAPSHOT_LATEST.md`
- `SKILL_FRESHNESS_LATEST.json`
- `SKILL_FRESHNESS_LATEST.md`
- `TATRAGRAMMATRON_SUMMARY_LATEST_CODEX.md`
- `TOOLCHAIN_DOCTOR_LATEST.md`
- `TRAINSTOP_ORCHESTRATOR_LATEST.json`
- `VS2026_ELEVATED_VALIDATION_LATEST.json`
- `VS2026_ELEVATED_VALIDATION_LATEST.md`
- `VSCODE_ERROR_AUTOPSY_LATEST.md`

## Root Directory Series
- none

## Policy
- Root mailbox keeps current-cycle files, latest aliases, and protected working handoffs.
- Timestamped series with more than three members are rotation candidates.
- Rotation always archives; it never deletes.
- `.tmp_fixture_eval/` is temporary fixture output and should not be treated as a durable active handoff lane.
