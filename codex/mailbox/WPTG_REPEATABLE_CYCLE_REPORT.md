# WPTG Repeatable Cycle Report

- Timestamp: `2026-03-05T16:04:36+00:00`
- Cycle ID: `1`
- Begin Anew Mode: `True`
- Execution Mode: `auto_restart_ready_now`
- Verdict: `WARN`

## Restart Readiness

- Ready for restart: `True`
- Notes:
  - Census anomalies exist; they are handled via reverse-rarity-first priority.
  - Validator warnings are currently lane-exclusion skips.

## Step Results

| Step | Toolchain | Exit | Status | Duration(s) |
|---|---|---:|---|---:|
| phase_0_universe | uv | 0 | pass | 2.760 |
| part_1_census | uv | 2 | warn | 119.182 |
| part_2_forge | uv | 0 | pass | 5.154 |
| part_3_ankh_scan | cargo | 0 | pass | 3.224 |
| part_3_ankh_census | cargo | 0 | pass | 0.607 |
| part_3_ankh_landscape | cargo | 0 | pass | 2.556 |
| part_3_ankh_eol | cargo | 0 | pass | 3.044 |
| part_3_bun_lane_pulse | bun | 0 | pass | 0.017 |
| part_4_validator | uv | 0 | pass | 0.162 |

## Metrics

- Extensions unique: `51`
- Tracked files: `2800`
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

- `11.46` | `tracked_bytecode` | `.codex/skills/artifact-upcycle/scripts/__pycache__/resolve_directory_relationships.cpython-313.pyc`
- `11.46` | `tracked_bytecode` | `.codex/skills/codekiller-remediation-gate/scripts/__pycache__/codekiller_remediation_gate.cpython-313.pyc`
- `11.46` | `tracked_bytecode` | `.codex/skills/mailbox-handoff/scripts/__pycache__/mailbox_check.cpython-313.pyc`
- `11.46` | `tracked_bytecode` | `.codex/skills/script-envelope/scripts/__pycache__/script_envelope.cpython-313.pyc`
- `11.46` | `tracked_bytecode` | `.codex/skills/skill-polisher/scripts/__pycache__/polish_skill.cpython-313.pyc`
- `11.46` | `tracked_bytecode` | `dumpster-dive/scripts/__pycache__/audit_deploy_integrity.cpython-313.pyc`
- `10.59` | `legacy_batch_in_pwsh_repo` | `dumpster-dive/intake/claude-ide-harden-2026-02-10/tier-1-direct/claude_process_wrapper.bat`
- `10.46` | `disabled_by_rename` | `.github/workflows/claude-code-review.yml.off`
- `10.46` | `disabled_by_rename` | `.github/workflows/claude.yml.off`
- `10.46` | `disabled_by_rename` | `.github/workflows/gemini-dispatch.yml.off`

## Learning Deltas

- `census_anomaly_count` delta: `0`
- `forge_tempered` delta: `0`
- `validator_errors` delta: `0`
- `validator_warnings` delta: `0`

## Guidance

- Baseline cycle established; use this snapshot as the default comparison anchor for future runs.
- Reverse-rarity queue is now the primary selection mode for high-effort nurturing.
- Validator warnings are lane-exclusion skips; treat current validator posture as operationally expected.

## Boon/Penalty

- Boon total: `11.5`
- Penalty total: `1.3`
- Net score: `10.2`
