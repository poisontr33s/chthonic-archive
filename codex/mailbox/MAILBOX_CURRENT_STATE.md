---
type: mailbox-state
updated: 2026-03-08T04:49:18Z
mailbox: codex/mailbox
---

# Mailbox Current State

## Root Summary

- Root files: `175`
- Root directories: `24`
- Archive files: `113`
- Protected files:
  - `MAILBOX_CURRENT_STATE.md`
  - `mailbox_manifest.json`
- Protected directories:
  - `ACTUAL-WORKING-HANDOFFS/`
  - `archive/`

## Current Working Queue

- `ACTUAL-WORKING-HANDOFFS/CHORE_CODEBASE_HYGIENE_2026_03_09.md`
- `ACTUAL-WORKING-HANDOFFS/CONTEXT_SURGERY_2026_02_10.md`

## Stable Latest Aliases

- `ART_COP_REPORT_LATEST.md`
- `CLAUDE_IDE_HEALTH_LATEST.json`
- `HF_MODEL_RANKING_LATEST.md`
- `HF_PREP_LATEST.json`
- `HF_PREP_LATEST.md`
- `LOCAL_AI_READINESS_LATEST.json`
- `LOCAL_AI_READINESS_LATEST.md`
- `OVERSIGHT_UPCYCLE_LATEST.json`
- `OVERSIGHT_UPCYCLE_LATEST.md`
- `POE_LANE_LATEST.json`
- `POE_LANE_LATEST.md`
- `POE_SDK_LATEST.json`
- `POE_SDK_LATEST.md`
- `POE_TRANSPORT_AUDIT_LATEST.json`
- `POE_TRANSPORT_AUDIT_LATEST.md`
- `RUSTIFICATION_TREND_LATEST.json`
- `RUSTIFICATION_TREND_LATEST.md`
- `TOOLCHAIN_DOCTOR_LATEST.md`
- `TRAINSTOP_ORCHESTRATOR_LATEST.json`
- `VS2026_ELEVATED_VALIDATION_LATEST.json`
- `VS2026_ELEVATED_VALIDATION_LATEST.md`

## Root Series Under Rotation Policy

- `TOOLCHAIN_DOCTOR_REPORT` (`15` root files)
- `SESSION_HANDOFF` (`6` root files)
- `SCM_TRIAGE_SNAPSHOT` (`2` root files)
- `SESSION_COMPACT` (`2` root files)
- `SKILL_COMPARATIVE_REVIEW` (`2` root files)
- `VSCODE_TERMINAL_TRIAGE` (`14` root directories)
- `VSCODE_INSIDERS_MATRIX` (`6` root directories)

## Temporary / Non-Durable Surfaces

- `.tmp_fixture_eval/` is fixture output, not a durable mailbox lane.
- Timestamped VS Code triage and matrix directories are historical diagnostic bursts and should rotate to archive on a series basis.

## Policy

- Root mailbox keeps the current-cycle files, `*_LATEST.*` aliases, protected manifests, and the active working handoff queue.
- Historical series should move to `archive/series/` or `archive/directories/` instead of piling up at root.
- Rotation is archive-only; nothing is destroyed.
