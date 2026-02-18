# Oversight Upcycle (Latest)

- Generated UTC: `2026-02-18T04:18:18.041209+00:00`
- Source report: `C:/Users/erdno/chthonic-archive/dumpster-dive/intake/overnight-daemon/20260218_030002/report.json`
- Files scanned: `1310`
- TODO hits total: `81`
- Actionable TODO hits: `15`
- Noise TODO hits: `64`
- Monolith hotspots: `7`

## TIER-0
1. `Stabilize TODO signal quality`
target: `scripts/overnight_daemon.ts + error-classifier/ingest.ts`
why: Noise TODO hits (64) are >= actionable code TODO hits (15). Current telemetry is polluting prioritization.
do: Restrict scored TODO extraction to actionable code prefixes and keep docs/research TODOs informational.

2. `Decompose primary monolith`
target: `scripts/chthonic.ps1`
why: Highest structural complexity hotspot (score=2083, derived=2083). This file dominates systemic change risk.
do: Extract bounded modules by responsibility and keep CLI surface unchanged; add regression checks.

## TIER-1
1. `Decompose secondary monolith`
target: `scripts/overnight_daemon.ts`
why: High complexity hotspot (score=902, derived=1082).
do: Split analyzer/core/output concerns into separate units with deterministic interfaces.

2. `Decompose secondary monolith`
target: `scripts/decorator_cross_ref_production.py`
why: High complexity hotspot (score=1040, derived=1040).
do: Split analyzer/core/output concerns into separate units with deterministic interfaces.

3. `Decompose secondary monolith`
target: `scripts/decorator_cross_ref_maximum.py`
why: High complexity hotspot (score=1416, derived=1416).
do: Split analyzer/core/output concerns into separate units with deterministic interfaces.

## TIER-2
1. `Close actionable TODO cluster`
target: `scripts/overnight_daemon.ts`
why: 6 actionable TODO/FIXME/HACK markers in code path.
do: Convert TODOs to either implemented behavior or explicit deferred issue references.

2. `Close actionable TODO cluster`
target: `src/data/procedural.rs`
why: 2 actionable TODO/FIXME/HACK markers in code path.
do: Convert TODOs to either implemented behavior or explicit deferred issue references.

3. `Close actionable TODO cluster`
target: `error-classifier/ingest.ts`
why: 2 actionable TODO/FIXME/HACK markers in code path.
do: Convert TODOs to either implemented behavior or explicit deferred issue references.
