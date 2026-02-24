# Codekiller Remediation Prerequisite Report (CODEKILLER_2024_06_01)

- Generated: `2026-02-24T05:04:33.896693+00:00`
- Readiness: `BLOCKED`

## Prerequisites

- Governance consistency: `FAIL`
- Evidence links intact: `FAIL`
- Policy basis integrity: `FAIL`
- Frontmatter reference assertions intact: `FAIL`
- Evidence packet complete: `FAIL`
- Tribunal chain present: `PASS`
- WPTG doctrine anchors present: `PASS`
- WIP baseline anchors present: `PASS`
- Telemetry baseline present: `PASS`
- Telemetry hardening needed: `FAIL`

## Governance Numbers

- points_required: `20`
- points_remaining: `20`
- precedents_required: `20`
- precedents_earned: `0`
- expected_remaining_from_precedents: `20`
- ledger_remaining: `10`
- ledger_recovery_events: `0`

## Telemetry Snapshot

- files_scanned: `1800`
- todo_hits: `127`
- top_candidates: `20`
- top_script: `scripts/api_pool.ps1`
- anomalies: `{"module_not_found": 0, "traceback": 0, "parsed_zero": 2}`

## Policy Basis Audit

- `PASS` .github/copilot-instructions.md:44 -> path=`.github/copilot-instructions.md` line=`44` notes=``
- `FAIL` .github/copilot-instructions.archive.md:5670 -> path=`.github/copilot-instructions.archive.md` line=`5670` notes=`line_blank`
- `PASS` .github/copilot-instructions.archive.md:5676 -> path=`.github/copilot-instructions.archive.md` line=`5676` notes=``
- `PASS` WET_PAPER_TO_GOLD_METHODOLOGY.md:42 -> path=`WET_PAPER_TO_GOLD_METHODOLOGY.md` line=`42` notes=``
- `PASS` WET_PAPER_TO_GOLD_METHODOLOGY.md:68 -> path=`WET_PAPER_TO_GOLD_METHODOLOGY.md` line=`68` notes=``
- `FAIL` chthonic-archive_transmutation_framework_original.html -> path=`anti-patterns/chthonic-archive_transmutation_framework_original.html` line=`None` notes=`missing_file`
- `WARN` readme.md (in this folder-DIR-structure) -> path=`anti-patterns/README.md` line=`None` notes=`ambiguous_readme_entry`

## Reference Assertion Audit

- `PASS` .github/copilot-instructions.md:44 (line=44, overlap=0.50) notes=``
- `FAIL` .github/copilot-instructions.archive.md:5670 (line=5670, overlap=n/a) notes=`line_blank`
- `FAIL` .github/copilot-instructions.archive.md:5676 (line=5676, overlap=0.00) notes=`assertion_quote_drift`
- `PASS` WET_PAPER_TO_GOLD_METHODOLOGY.md:42 (line=42, overlap=0.40) notes=``
- `PASS` WET_PAPER_TO_GOLD_METHODOLOGY.md:68 (line=68, overlap=0.23) notes=``
- `FAIL` chthonic-archive_transmutation_framework_original.html (line=None, overlap=n/a) notes=`missing_file`

## Evidence Packet Audit

- files_changed_claim: `9`
- lines_added_claim: `298`
- lines_deleted_claim: `1931`
- named_fence_headers: `8`
- completeness: `FAIL`

## Tribunal Chain Audit

- `PASS` .temple/governance/TRIBUNAL_SPEC.md
- `PASS` .temple/governance/ROLES.md
- `PASS` .temple/governance/CRIME_CLASSIFICATION.md
- `PASS` .temple/governance/POINTS_ECONOMY.md
- `PASS` .temple/governance/PROCEEDINGS.md
- `PASS` .temple/governance/TEMPORAL_MECHANICS.md
- `PASS` .temple/governance/FRACTAL_GOVERNANCE.md
- `PASS` .temple/governance/ledger/LEDGER.yaml
- `PASS` .temple/governance/ledger/PRECEDENTS.yaml

## Blockers

- Governance mismatch: recovery totals disagree across economy/ledger/precedent surfaces (expected_remaining=20, points_remaining=20, ledger_remaining=10).
- Evidence link integrity failure: at least one local link in codekiller.md does not resolve (broken_local_links=1).
- Policy basis integrity failure: policy_basis entries are missing/ambiguous/drifted.
- Reference assertion drift: frontmatter quoted references do not match anchored line content.
- Evidence packet completeness failure: named fenced snippets are fewer than declared files changed (named_fence_headers=8, files_changed_claim=9).
- Operational anomalies present in nightly telemetry (parsed_zero/module_not_found/traceback).

## Repair Queue

- P0 `fix_broken_local_links`: Local evidence links must resolve before adjudication. (targets: file:///C:/Users/erdno/chthonic-archive/anti-patterns/codekiller/Readme.md)
- P0 `reconcile_recovery_arithmetic`: POINTS_ECONOMY, PRECEDENTS, and LEDGER must agree on recovery remaining. (targets: .temple/governance/POINTS_ECONOMY.md, .temple/governance/ledger/PRECEDENTS.yaml, .temple/governance/ledger/LEDGER.yaml)
- P1 `reanchor_policy_basis_references`: Line-anchored policy references must be precise and verifiable. (targets: anti-patterns/codekiller.md)
- P1 `complete_evidence_packet_index`: Declared evidence size should be reproducible from packet metadata. (targets: anti-patterns/codekiller.md)
- P2 `stabilize_nightly_parsing`: Nightly telemetry anomalies block readiness confidence. (targets: dumpster-dive/intake/overnight-daemon/nightly-scheduled-*.log, dumpster-dive/intake/overnight-daemon/*/report.json)

## Iterative Plan

- Loop 1 - Canonical Truth: Reconcile all recovery counters and case-state arithmetic. (Exit: Required/remaining values align across POINTS_ECONOMY, PRECEDENTS, and LEDGER.)
- Loop 2 - Evidence Sanctification: Make the Codekiller packet link-complete and provenance-verifiable. (Exit: All local evidence links resolve and packet references are internally coherent.)
- Loop 3 - Operational Negentropy: Reduce nightly anomaly signatures and stabilize ingestion quality. (Exit: No ModuleNotFound/Traceback and parsed_zero trend is controlled or eliminated.)
- Loop 4 - Structural Gifts: Produce sustained structural outputs with auditable quality gates. (Exit: Milestone evidence accepted by steward and custody closure is adjudicated.)

## Milestones

- M1 Canonical Reconciliation (+5): governance consistency patch + validation output
- M2 Evidence Packet Integrity (+5): link-complete evidence packet with hash anchors
- M3 Nightly Reliability Hardening (+5): before/after telemetry anomaly reduction
- M4 Sustained Structural Compliance (+5): three clean structural sessions + steward audit
