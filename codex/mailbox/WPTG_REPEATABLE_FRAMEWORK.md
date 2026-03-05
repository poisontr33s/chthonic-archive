---
type: framework
from: codex
to: user
created: 2026-03-05
priority: high
subject: WPTG Repeatable Cycle Framework
in_response_to: codex/mailbox/EXTENSION_CONTRIBUTION_GRAPH_VALIDATOR_CHORE.md
---

# WPTG Repeatable Cycle Framework

## Purpose

Convert the one-pass Phase 0 -> Part 4 execution into a reusable learning loop that can be rerun from current lane state without reinventing the process.

## Execution Contract

Run:

```powershell
uv run scripts/wptg_repeatable_cycle.py --begin-anew
```

Or run sequential auto-mode:

```powershell
uv run scripts/wptg_repeatable_cycle.py --auto-restart
```

`--auto-restart` behavior:

1. Check restart readiness from current cycle state.
2. If ready, restart immediately (`begin_anew` path).
3. If not ready, execute continuation cycle first, then restart only when readiness turns green.

The orchestrator executes, in order:

1. Phase 0 (`extension_universe_scanner.py`) via `uv`.
2. Part 1 (`wptg_filetype_census.py`) via `uv`.
3. Part 2 (`universal_forge.py`) via `uv`.
4. Part 3 (`ankh-forge` scan/census/landscape/eol) via `cargo`.
5. TypeScript lane pulse (`bun --version`) via `bun`.
6. Part 4 (`extension_contribution_audit.py`) via `uv`.

## Persistent Artifacts

- `audit-reports/wptg_cycle_state.json`:
  - Per-step execution outcomes.
  - Metrics snapshot.
  - Learning deltas against previous cycle.
  - Boon/penalty score ledger.
- `audit-reports/wptg_default_view.json`:
  - New default WPTG posture for the next loop.
  - Focus guidance distilled from current lane status.
- `audit-reports/wptg_reverse_viability_queue.json`:
  - Reverse-rarity-first extension and file priority queue.
  - Least-viable artifacts ranked as highest-effort nurturing targets.
- `codex/mailbox/WPTG_REPEATABLE_CYCLE_REPORT.md`:
  - Human-readable execution and scoring report.

## Learning Mechanics

Each run computes deltas from previous cycle state:

- anomaly drift,
- forge yield drift,
- validator risk drift.

These deltas produce concrete next-cycle guidance and a refreshed default-view baseline.

Default perspective is now:

- `reverse_rarity_first`
- Selection principle: `least_viable_first`
- Priority assignment ignores filetype prestige; rare/weak viability artifacts are targeted first.

## Governance Boundary

- Lane exclusion table remains immutable.
- No destructive operations are introduced by the framework.
- Promotion and dedupe decisions remain explicit governance actions, not implicit side effects.
- Legacy preservation guard is mandatory:
  - `scripts/wpth_repeatable_cycle_LEGACY` is checked during readiness.
  - Missing legacy guard blocks restart in `--auto-restart` mode until restored.
