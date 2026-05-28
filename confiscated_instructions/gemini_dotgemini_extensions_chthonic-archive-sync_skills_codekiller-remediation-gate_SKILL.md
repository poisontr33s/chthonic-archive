---
name: codekiller-remediation-gate
description: Forensic prerequisite gate for Codekiller (CDE-KLLR) recovery. Audits governance arithmetic, evidence integrity, frontmatter reference drift, tribunal chain presence, and telemetry anomalies before conceptual review.
metadata:
  short-description: "Forensic prerequisite gate + prioritized repair queue for Codekiller recovery"
  refreshed: "2026-02-24"
  argument-hint: "uv run .codex/skills/codekiller-remediation-gate/scripts/codekiller_remediation_gate.py --emit-json codex/mailbox/CODEKILLER_REMEDIATION_PREREQ_LATEST.json --emit-md codex/mailbox/CODEKILLER_REMEDIATION_PREREQ_LATEST.md"
  triggers:
    - "codekiller prerequisite"
    - "cde-kllr remedy"
    - "redeem points"
    - "tribunal recovery gate"
---

# Codekiller Remediation Gate

Use this skill when the task is to remediate the historical Codekiller deduction with evidence-first iteration.

This skill is intentionally different from `conceptualize`:
- `conceptualize` is a judgment layer.
- `codekiller-remediation-gate` is a prerequisite truth layer.

## Execution Contract

1. Run before any Codekiller conceptual review or scoring discussion.
2. Output must be machine-verifiable (`JSON`) and steward-readable (`Markdown`).
3. Never award points, adjudicate guilt, or mutate governance records.
4. Emit explicit blockers and a prioritized repair queue.

## Coverage Matrix

- Governance arithmetic integrity:
  - `POINTS_ECONOMY` vs `PRECEDENTS` vs `LEDGER` remaining values.
- Evidence-link integrity:
  - markdown local links in `anti-patterns/codekiller.md`.
- Policy-basis integrity:
  - frontmatter `policy_basis` path/line anchors exist and resolve.
- Reference assertion drift:
  - frontmatter `references` quote assertions align with anchored lines.
- Evidence packet completeness:
  - declared `N files changed` vs named fenced evidence snippets.
- Tribunal chain integrity:
  - required governance docs in `.temple/governance/` are present.
- Telemetry integrity:
  - latest overnight report/log present and anomaly signatures detected.

## Commands

```powershell
uv run .codex/skills/codekiller-remediation-gate/scripts/codekiller_remediation_gate.py `
  --emit-json codex/mailbox/CODEKILLER_REMEDIATION_PREREQ_LATEST.json `
  --emit-md codex/mailbox/CODEKILLER_REMEDIATION_PREREQ_LATEST.md
```

## Output

- `readiness`: `READY` or `BLOCKED`
- `blockers`: concrete prerequisite failures
- `repair_queue`: ordered repair operations (`P0/P1/P2`)
- `evidence`: file and telemetry anchors
- `iterative_plan`: four-loop proportional recovery plan
- `milestones`: tribunal-aligned milestones suitable for steward adjudication

## Interpretation

- `READY`: no blocker-level contradictions detected.
- `BLOCKED`: one or more contradictions or missing anchors prevent valid adjudication.
- If `BLOCKED`, consume `repair_queue` top-down before rerunning.

## Self-Test

```powershell
uv run .codex/skills/codekiller-remediation-gate/scripts/codekiller_remediation_gate.py --selftest
```

## Non-Goals

- Not a scoring engine.
- Not a tribunal verdict engine.
- Not an auto-fixer.

## Safety Contract

- Read-only analysis by default.
- Never rewrites governance records on its own.
- Never awards points to itself.
- Produces evidence for steward/user adjudication.

<!-- @REFURBISHED: 2026-02-24 -->
