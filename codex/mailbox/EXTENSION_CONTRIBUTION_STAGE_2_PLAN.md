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

## Stage 2 (Post-Parts 0-4) Sequence

1. **P0 complete in this pass**: untrack the 21 tracked C# build artifacts and guard against re-tracking with explicit `.gitignore` rules.
2. **P0 complete in this pass**: push the cleanup commit so remote reflects the corrected furnace index state.
3. **P1 next**: remove `dumpster-dive/intake/ankh-forge-salvage/` only after confirming there is no needed provenance in that quarantine path.
4. **P1 next**: run a quick regression sweep of the delivered scripts:
   - `uv run scripts/extension_universe_scanner.py`
   - `uv run scripts/wptg_filetype_census.py`
   - `uv run scripts/universal_forge.py`
   - `uv run scripts/extension_contribution_audit.py`
5. **P2 next**: decide furnace/tempered duplication strategy (keep both lanes vs. dedupe one lane with preserved manifests).
6. **P2 next**: decide promotion disposition for the six forge recommendations (PowerShell transliteration, Python utility module, shell recipe book, Go CLI, C# contracts, C FFI header).
7. **P3 optional**: add `tools/ankh-forge` as a workspace member to root `Cargo.toml` for root-level build ergonomics.

## Lane Constraint Reminder

Stage 2 must continue honoring the same absolute lane exclusions from the chore, especially the theme/icon/product chain paths under `extensions/chthonic-archive/themes/` and related icon/font pipelines.
