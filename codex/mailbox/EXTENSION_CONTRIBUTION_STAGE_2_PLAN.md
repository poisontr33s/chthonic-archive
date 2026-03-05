---
type: plan
from: codex
to: user
created: 2026-03-04
priority: high
subject: Stage 2 Plan After Parts 0-4
in_response_to: codex/mailbox/EXTENSION_CONTRIBUTION_GRAPH_VALIDATOR_CHORE.md
---

# Stage 2 — Synthesized Verdict and Next Steps

## Synthesized Verdict

The Parts 0-4 chain is operational and materially delivered. The remaining hard blocker from the review is tracked generated output in `dumpster-dive/forge/furnace/csharp/bin/` and `dumpster-dive/forge/furnace/csharp/obj/`.

Validated review numbers:

- Tracked C# furnace build artifacts: `21` files.
- `audit-reports/orphaned_artifact_reconciliation.json`: `1,505,599` bytes, `41,234` lines.

## Stage 2 Execution Status

| Priority | Task | Status | Evidence |
|---|---|---|---|
| P0 | Untrack furnace C# build artifacts + add ignore guards | **Completed** | Commit `81ab7569`; `.gitignore` guards for `dumpster-dive/forge/furnace/csharp/bin/` and `obj/`; tracked artifact count now `0` |
| P0 | Push cleanup chain to remote | **Completed** | `main -> origin/main` push including `81ab7569` and later Stage 2 updates |
| P1 | Verify `dumpster-dive/intake/ankh-forge-salvage/` and remove if non-required | **Verified / Retained** | Directory contains nested git metadata salvage (`nested-git-2026-03-03`); retained as provenance payload, not empty |
| P1 | Regression sweep of delivered scripts | **Completed** | `uv run scripts/extension_universe_scanner.py`; `uv run scripts/wptg_filetype_census.py`; `uv run scripts/universal_forge.py`; `uv run scripts/extension_contribution_audit.py` |
| P2 | Decide furnace/tempered dedupe strategy | **Completed** | `codex/mailbox/STAGE2_FORGE_DECISIONS.md` (retain dual-lane policy in Stage 2) |
| P2 | Decide promotion disposition for six forge recommendations | **Completed** | `codex/mailbox/STAGE2_FORGE_DECISIONS.md` disposition table |
| P3 | Add `ankh-forge` to root Cargo workspace | **Completed** | Root `Cargo.toml` updated with `[workspace] members = ["tools/ankh-forge"]` |

## Stage 2 Decision Artifacts

- `codex/mailbox/STAGE2_FORGE_DECISIONS.md` — dedupe policy + promotion dispositions.
- `codex/mailbox/EXTENSION_CONTRIBUTION_STAGE_3_EXECUTION.md` — promotion execution and dedupe reassessment.

## Stage 3 Continuation Status

Stage 3 continuation was executed after Stage 2 closure:

- Three approved tempered artifacts promoted into active lanes under `scripts/`.
- Trigger-based dedupe reassessment completed; dual-lane furnace/tempered model retained in this pass.

## Stage 4 Continuation Status

Stage 4 converts the delivered chain into a repeatable cycle framework:

- `scripts/wptg_repeatable_cycle.py` orchestrates Phase 0 -> Part 4 in ordered replay.
- Cycle outputs now include `audit-reports/wptg_cycle_state.json` and `audit-reports/wptg_default_view.json`.
- Framework contract recorded in `codex/mailbox/WPTG_REPEATABLE_FRAMEWORK.md`.
- Baseline execution completed with `uv run scripts/wptg_repeatable_cycle.py --begin-anew` and report `codex/mailbox/WPTG_REPEATABLE_CYCLE_REPORT.md`.

## Stage 5 Continuation Status

Stage 5 applies reverse-rarity-first default perspective with sequential restart control:

- `scripts/wptg_repeatable_cycle.py --auto-restart` now handles readiness-driven sequencing.
- New output: `audit-reports/wptg_reverse_viability_queue.json`.
- Default view shifted to `renewal_loop_reverse_rarity_first` with `least_viable_first` selection principle.
- Legacy safeguard enforced: `scripts/wpth_repeatable_cycle_LEGACY` is tracked as a restart-readiness guard.

## Lane Constraint Reminder

Stage 2 must continue honoring the same absolute lane exclusions from the chore, especially the theme/icon/product chain paths under `extensions/chthonic-archive/themes/` and related icon/font pipelines.
