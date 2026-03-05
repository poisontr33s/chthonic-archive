# WPTG Repeatable Cycle Report

- Timestamp: `2026-03-05T16:30:05+00:00`
- Cycle ID: `2`
- Begin Anew Mode: `False`
- Execution Mode: `manual_continuation`
- Verdict: `WARN`

## Restart Readiness

- Ready for restart: `True`
- Notes:
  - Census anomalies exist; they are handled via reverse-rarity-first priority.
  - Validator warnings are currently lane-exclusion skips.
  - Legacy salvage guard preserved: scripts/wpth_repeatable_cycle_LEGACY (20113 bytes).

## Legacy Guard

- Path: [`scripts/wpth_repeatable_cycle_LEGACY`](../../scripts/wpth_repeatable_cycle_LEGACY)
- Present: `True`
- Size bytes: `20113`

## Step Results

| Step | Toolchain | Exit | Status | Duration(s) |
|---|---|---:|---|---:|
| phase_0_universe | uv | 0 | pass | 2.327 |
| part_1_census | uv | 2 | warn | 117.099 |
| part_2_forge | uv | 0 | pass | 4.584 |
| part_3_ankh_scan | cargo | 0 | pass | 2.841 |
| part_3_ankh_census | cargo | 0 | pass | 0.566 |
| part_3_ankh_landscape | cargo | 0 | pass | 2.951 |
| part_3_ankh_eol | cargo | 0 | pass | 2.769 |
| part_3_bun_lane_pulse | bun | 0 | pass | 0.025 |
| part_4_validator | uv | 0 | pass | 0.156 |

## Metrics

- Extensions unique: `51`
- Tracked files: `2801`
- Census verdict/anomalies: `FAIL` / `353`
- Forge tempered/rejected: `18` / `0`
- Validator verdict/errors/warnings: `WARN` / `0` / `3`

## Reverse-Rarity Priority (Top 10 Extensions)

| Rank | Ext | Count | Anomalies | Effort | Viability |
|---:|---|---:|---:|---:|---:|
| 1 | `.bat` | 1 | 1 | 8.99 | 0.1006 |
| 2 | `.cpython-313.pyc` | 6 | 6 | 8.96 | 0.1035 |
| 3 | `.off` | 7 | 7 | 8.96 | 0.1041 |
| 4 | `.sh` | 1 | 0 | 7.99 | 0.2006 |
| 5 | `.md"` | 3 | 3 | 7.98 | 0.2018 |
| 6 | `.env` | 4 | 3 | 7.23 | 0.2774 |
| 7 | `.bak` | 1 | 0 | 6.99 | 0.3006 |
| 8 | `.db` | 1 | 0 | 6.99 | 0.3006 |
| 9 | `.tsbuildinfo` | 1 | 0 | 6.99 | 0.3006 |
| 10 | `.woff` | 1 | 0 | 6.99 | 0.3006 |

## Reverse-Rarity Priority (Top 10 Files)

- `11.46` | `tracked_bytecode` | [`.codex/skills/artifact-upcycle/scripts/__pycache__/resolve_directory_relationships.cpython-313.pyc`](../../.codex/skills/artifact-upcycle/scripts/__pycache__/resolve_directory_relationships.cpython-313.pyc)
- `11.46` | `tracked_bytecode` | [`.codex/skills/codekiller-remediation-gate/scripts/__pycache__/codekiller_remediation_gate.cpython-313.pyc`](../../.codex/skills/codekiller-remediation-gate/scripts/__pycache__/codekiller_remediation_gate.cpython-313.pyc)
- `11.46` | `tracked_bytecode` | [`.codex/skills/mailbox-handoff/scripts/__pycache__/mailbox_check.cpython-313.pyc`](../../.codex/skills/mailbox-handoff/scripts/__pycache__/mailbox_check.cpython-313.pyc)
- `11.46` | `tracked_bytecode` | [`.codex/skills/script-envelope/scripts/__pycache__/script_envelope.cpython-313.pyc`](../../.codex/skills/script-envelope/scripts/__pycache__/script_envelope.cpython-313.pyc)
- `11.46` | `tracked_bytecode` | [`.codex/skills/skill-polisher/scripts/__pycache__/polish_skill.cpython-313.pyc`](../../.codex/skills/skill-polisher/scripts/__pycache__/polish_skill.cpython-313.pyc)
- `11.46` | `tracked_bytecode` | [`dumpster-dive/scripts/__pycache__/audit_deploy_integrity.cpython-313.pyc`](../../dumpster-dive/scripts/__pycache__/audit_deploy_integrity.cpython-313.pyc)
- `10.59` | `legacy_batch_in_pwsh_repo` | [`dumpster-dive/intake/claude-ide-harden-2026-02-10/tier-1-direct/claude_process_wrapper.bat`](../../dumpster-dive/intake/claude-ide-harden-2026-02-10/tier-1-direct/claude_process_wrapper.bat)
- `10.46` | `disabled_by_rename` | [`.github/workflows/claude-code-review.yml.off`](../../.github/workflows/claude-code-review.yml.off)
- `10.46` | `disabled_by_rename` | [`.github/workflows/claude.yml.off`](../../.github/workflows/claude.yml.off)
- `10.46` | `disabled_by_rename` | [`.github/workflows/gemini-dispatch.yml.off`](../../.github/workflows/gemini-dispatch.yml.off)

## Learning Deltas

- `census_anomaly_count` delta: `0`
- `forge_tempered` delta: `0`
- `validator_errors` delta: `0`
- `validator_warnings` delta: `0`

## Guidance

- Anomaly count stable; continue rarity-first nurturing focus.
- Forge yield remains above Tier 2 gate; maintain provenance lanes and promotion discipline.
- Validator warnings are lane-exclusion related; continue without treating them as hard blockers.

## Boon/Penalty

- Boon total: `11.5`
- Penalty total: `1.3`
- Net score: `10.2`
