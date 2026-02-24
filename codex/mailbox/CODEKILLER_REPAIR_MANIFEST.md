# CODEKILLER Structural Repair Manifest

Generated: 2026-02-24
Mode: Read-only findings only (no auto-fixes)

## Severity-Ordered Findings

### CRITICAL

1. Broken evidence link in primary packet
- Location: `anti-patterns/codekiller.md:46`
- Reference: `file:///C:/Users/erdno/chthonic-archive/anti-patterns/codekiller/Readme.md`
- Current state: target path does not exist (`anti-patterns/codekiller/Readme.md`)
- Why broken: packet claims a detailed sibling README exists in a `codekiller/` subdirectory, but that subdirectory is absent.
- Impact: fails evidence-link integrity gate and blocks `codekiller-remediation-gate` readiness.

2. Tribunal recovery arithmetic mismatch (governance chain inconsistency)
- POINTS_ECONOMY states:
  - `recovery_required: 20` (`.temple/governance/POINTS_ECONOMY.md:239`)
  - `recovery_earned: 0` (`.temple/governance/POINTS_ECONOMY.md:240`)
  - `recovery_remaining: 20` (`.temple/governance/POINTS_ECONOMY.md:241`)
- PRECEDENTS states:
  - `required: 20`, `earned: 0` (`.temple/governance/ledger/PRECEDENTS.yaml:45-46`)
- LEDGER active case states:
  - `recovery_remaining: 10` (`.temple/governance/ledger/LEDGER.yaml:37`)
- Why broken: remaining value in LEDGER conflicts with both canonical case docs (20 expected if earned is 0).
- Impact: governance-consistency gate fails; tribunal chain cannot be treated as canonical.

### HIGH

1. Policy-basis line anchors drifted from quoted statements
- `anti-patterns/codekiller.md` frontmatter points to `.github/copilot-instructions.archive.md:5670` and `:5676`.
- Actual content:
  - `:5670` is blank.
  - `:5676` is `→ TIER: ΔEXIST`.
  - Closest "governance substrate annihilation" anchor is `:5675`.
- Why broken: line-number anchored evidence no longer resolves to the claimed quoted text.
- Impact: provenance precision degraded; audit confidence reduced.

2. Evidence completeness gap for `9 files changed / +298 / -1931`
- Packet includes `9 files changed +298 -1931` at `anti-patterns/codekiller.md:50-52`.
- Packet currently contains 8 named fenced file snippets (`anti-patterns/codekiller.md`, named fence headers count = 8).
- Why broken: preserved packet does not provide an unambiguous full 9-file listing or diff hash to fully verify the `-1931` claim.
- Impact: historical scale claim is plausible but not fully reproducible from packet alone.

### MEDIUM

1. Ambiguous policy_basis README entry
- Entry: `readme.md (in this folder-DIR-structure)` (`anti-patterns/codekiller.md:13`)
- Why broken: ambiguous target; could refer to `anti-patterns/README.md` while in-body link points elsewhere and fails.
- Impact: inconsistent documentation intent and cross-reference ambiguity.

2. Telemetry anomaly residue still present
- Source: `dumpster-dive/intake/overnight-daemon/nightly-scheduled-2026-02-24_030002.log`
- Evidence: `parsed 0` seen twice (lines 22 and 34).
- Impact: keeps remediation gate in `BLOCKED` due operational anomaly condition.

### LOW

1. Remediation gate self-scope gap (not a runtime failure)
- Gate script validates local markdown links and governance counters, but does not validate frontmatter policy-basis line-level drift.
- Impact: manual crossref audit still required for quote-anchored references.

## YAML Frontmatter Status (`anti-patterns/codekiller.md`)

- Structural syntax: no obvious delimiter/indentation break detected in frontmatter block.
- Semantic issues found:
  - ambiguous README policy_basis pointer
  - drifted archive line anchors (`5670`, `5676`)

## Tribunal Governance Chain Verification

- All governance documents referenced by `anti-patterns/README.md` exist:
  - `TRIBUNAL_SPEC.md`, `ROLES.md`, `CRIME_CLASSIFICATION.md`, `POINTS_ECONOMY.md`, `PROCEEDINGS.md`, `TEMPORAL_MECHANICS.md`, `FRACTAL_GOVERNANCE.md`, `ledger/LEDGER.yaml`, `ledger/PRECEDENTS.yaml`.
- What is broken is not presence; it is internal numeric consistency for Codekiller recovery state.

## Gate Self-Validation Result

- `uv run .codex/skills/codekiller-remediation-gate/scripts/codekiller_remediation_gate.py --selftest` => OK
- `uv run .codex/skills/codekiller-remediation-gate/scripts/codekiller_remediation_gate.py --emit-json codex/mailbox/CODEKILLER_GATE_STATUS.json --emit-md codex/mailbox/CODEKILLER_GATE_STATUS.md` => readiness `BLOCKED`
- Blockers confirmed by direct audit:
  - governance mismatch
  - broken evidence link (`anti-patterns/codekiller/Readme.md`)
  - telemetry `parsed_zero` anomalies

## Repair Order (Savant-Adjudicated)

1. Resolve broken `Readme.md` evidence reference (link target or canonical replacement).
2. Reconcile Codekiller `recovery_remaining` across POINTS_ECONOMY, PRECEDENTS, and LEDGER.
3. Re-anchor archive policy_basis references to current authoritative lines.
4. Add explicit 9-file evidence index or commit hash/provenance anchor to substantiate `-1931` claim.
5. Reduce overnight `parsed 0` anomalies and re-run gate.
