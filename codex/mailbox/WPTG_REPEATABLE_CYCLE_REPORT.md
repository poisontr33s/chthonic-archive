# WPTG Repeatable Cycle Report

- Timestamp: `2026-03-04T23:30:21+00:00`
- Cycle ID: `1`
- Begin Anew Mode: `True`
- Verdict: `WARN`

## Step Results

| Step | Toolchain | Exit | Status | Duration(s) |
|---|---|---:|---|---:|
| phase_0_universe | uv | 0 | pass | 2.400 |
| part_1_census | uv | 2 | warn | 128.159 |
| part_2_forge | uv | 0 | pass | 3.381 |
| part_3_ankh_scan | cargo | 0 | pass | 2.377 |
| part_3_ankh_census | cargo | 0 | pass | 0.542 |
| part_3_ankh_landscape | cargo | 0 | pass | 2.576 |
| part_3_ankh_eol | cargo | 0 | pass | 2.883 |
| part_3_bun_lane_pulse | bun | 0 | pass | 0.020 |
| part_4_validator | uv | 0 | pass | 0.162 |

## Metrics

- Extensions unique: `51`
- Tracked files: `2794`
- Census verdict/anomalies: `FAIL` / `353`
- Forge tempered/rejected: `18` / `0`
- Validator verdict/errors/warnings: `WARN` / `0` / `3`

## Learning Deltas

- `census_anomaly_count` delta: `0`
- `forge_tempered` delta: `0`
- `validator_errors` delta: `0`
- `validator_warnings` delta: `0`

## Guidance

- Baseline cycle established; use this snapshot as the default comparison anchor for future runs.
- Forge yield is currently above Tier 2 gate; maintain provenance lanes and promotion discipline.
- Validator warnings are lane-exclusion skips; treat current validator posture as operationally expected.

## Boon/Penalty

- Boon total: `11.5`
- Penalty total: `1.3`
- Net score: `10.2`
