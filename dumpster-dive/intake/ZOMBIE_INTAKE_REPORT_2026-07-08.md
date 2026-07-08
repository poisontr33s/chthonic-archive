# Zombie Intake Report — 2026-07-08

Generated from 171 consumed files with a known forge outcome (see `_scan_forge_outcomes()`). Read-only — SFS reads this to prioritize forge work without manual queue inspection (docs/zombie/CONVERGENCE_PLAN.md Tier C1).

## Ore histogram by community

| Community | Ore 1 | Ore 2 | Ore 3 | Ore 4 | Ore 5 | Total |
|---|---|---|---|---|---|---|
| unknown (-1) | 73 | 0 | 97 | 0 | 1 | 171 |

_No real Louvain communities detected — the import graph currently has fewer than 3 nodes (see `detect_communities()`'s own threshold). Every row falls into the `unknown (-1)` bucket above until the graph grows._

## Provenance age distribution

Total files: 171 | Orphaned (>90d since last touch): 131

| Age bucket | Count |
|---|---|
| 0-7d | 33 |
| 7-30d | 0 |
| 30-90d | 7 |
| 90d+ (orphaned) | 130 |
| unknown (no git history) | 1 |

## ML confidence distribution

Scored 171/171 rows against the trained GBT model.

| Confidence | Count |
|---|---|
| >90% | 145 |
| 70-90% | 17 |
| 50-70% | 9 |
| <50% | 0 |

## Top semantic clusters awaiting SFS attention

"Awaiting attention" = at least one cluster member has not reached the `tempered` forge stage yet (SFS's own terminal/reviewed state). Files with no forge outcome yet show as `unrouted`.

None found — the semantic index has 0 entries, too few to compare. Run `zombie digest` on more files (A1's embedding step) to populate it.
