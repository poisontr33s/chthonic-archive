---
type: handoff
from: claude
to: codex
created: 2026-02-18
priority: high
scope: claudine-archaeology-upcycle-classification
---

# SESSION_HANDOFF_2026_02_18_CLAUDINE_ARCHAEOLOGY_UPCYCLE_CLASSIFICATION

## Actions Taken
- Classified Claudine-era artifacts into deterministic upcycle classes: `KEEP`, `TRANSFORM`, `QUARANTINE`, `DROP`.
- Defined the unified target model where `scripts/chthonic.ps1` remains SSOT runtime and `scripts/claudine.ps1` remains thin compatibility facade.
- Produced phased implementation guidance for activation kernel extraction, facade registry, profile hygiene, and classifier automation.

## Files Changed
- No source files were modified by this handoff packet.
- Evidence/reference scope for the classification:
  - `dumpster-dive/intake/claudine-harvest/*`
  - `scripts/chthonic.ps1`
  - `scripts/claudine.ps1`

## How to verify
- Run: `chthonic doctor --origins`
- Run: `chthonic status --json`
- Run: `pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/claudine.ps1 status --json`
- Confirm the strata/classification guidance in this document matches the current wrapper/runtime relationship.

## Next Actions
- Implement Phase 1 activation kernel extraction in `scripts/chthonic.ps1`.
- Add facade metadata fields in status/origins outputs (`facade_claudine`, `facade_chthonic`).
- Add `doctor` guard for external profile alias leakage and extend harvest classification tags.

## Scope
- Domain: `TEMPLE` (structural/tooling upcycle)
- Objective: classify all Claudine-era artifacts and define a deterministic merge into unified `claudine` (not `claudineENV`) with `chthonic` as SSOT engine.

## Archaeology Strata

### Stratum A — Pre-era Global Hijack Layer
- Sources:
  - `dumpster-dive/intake/claudine-harvest/2919D506B1758C9B__Microsoft.PowerShell_profile.ps1`
  - `dumpster-dive/intake/claudine-harvest/556BBC05B819EB8F__profile.ps1`
- Signature:
  - Global `Set-Alias claudine ...` outside repo scope.
- Classification:
  - `QUARANTINE` (forensics only; never canonical runtime logic).

### Stratum B — Monolithic Activation Script Layer (`claudineENV`)
- Source:
  - `dumpster-dive/intake/claudine-harvest/2ED300C9669FC860__claudineENV.ps1`
- Signature:
  - Hardcoded tool paths by era, direct PATH front-loading, environment markers.
- Classification:
  - `TRANSFORM` (extract patterns, not file wholesale).

### Stratum C — Generated/Incidental Noise Layer
- Sources:
  - `dumpster-dive/intake/claudine-harvest/*__semver.ps1`, `*__mime.ps1`, `*__nodemon.ps1`, etc.
- Signature:
  - Package shims and low-signal wrappers.
- Classification:
  - `DROP` from runtime design; keep only as archive evidence.

### Stratum D — High-impact Sandbox Utilities Layer
- Sources:
  - `dumpster-dive/intake/claudine-harvest/DF47AE1F882232F3__CantorForge.ps1`
  - `dumpster-dive/intake/claudine-harvest/6CA77E28501F31BF__EnvVarManagerGUI.ps1`
- Signature:
  - Broad host mutation and installer orchestration.
- Classification:
  - `QUARANTINE` + selective pattern extraction only.

### Stratum E — Unified Router Layer (Current)
- Source:
  - `scripts/chthonic.ps1`
- Signature:
  - Multi-domain command routing, manager detection, origins/status diagnostics.
- Classification:
  - `KEEP` as SSOT runtime engine.

### Stratum F — Compatibility Facade Layer (Target)
- Source:
  - `scripts/claudine.ps1`
- Signature:
  - Thin command facade delegating to `chthonic.ps1`.
- Classification:
  - `KEEP` as compatibility shell, no business logic drift.

## Upcycle Classes (Deterministic)

### Class 1 — Canonical Runtime (`KEEP`)
- `scripts/chthonic.ps1`
- Rule:
  - Owns all runtime logic, detection, origin reporting, and manager handlers.

### Class 2 — Facade Compatibility (`KEEP`)
- `scripts/claudine.ps1`
- Rule:
  - Delegates 1:1 into `chthonic`.
  - No duplicate activation logic.

### Class 3 — Pattern Extraction (`TRANSFORM`)
- from `claudineENV` and safe portions of legacy scripts:
  - PATH ordering heuristics
  - env marker semantics
  - activation UX hints
- Rule:
  - Patterns only; never copy hardcoded era paths into canonical runtime.

### Class 4 — Forensics Reference (`QUARANTINE`)
- global profiles, CantorForge, EnvVarManagerGUI.
- Rule:
  - Keep archived and documented; do not execute in normal flow.

### Class 5 — Noise Archive (`DROP` from design)
- generated package shims.
- Rule:
  - Ignore for architecture decisions.

## Unified `claudine` Target Model

### Contract
- `claudine` is a stable facade, not an activation engine.
- Valid forms:
  - `claudine` -> `chthonic env`
  - `claudine status --json` -> `chthonic status --json`
  - `claudine doctor --origins` -> `chthonic doctor --origins`

### Non-negotiables
- No global alias hijack assumptions.
- No era-bound path constants.
- No logic fork between `claudine` and `chthonic`.

## What To Do With `chthonic` Next (Archaeological Upcycle Sequence)

### Phase 1 — Extract an Activation Kernel
- Move activation internals into a single callable kernel in `scripts/chthonic.ps1`:
  - PATH merge + de-dup
  - manager collision guards (`rv`/`rvar`)
  - environment marker population
- Outcome:
  - all entrypoints (`env`, `claudine`, wrapper) call same kernel.

### Phase 2 — Facade Registry
- Add explicit facade metadata in status/origins:
  - `facade_claudine: active|script|function|absent`
  - `facade_chthonic: script|function`
- Outcome:
  - wrapper drift becomes observable.

### Phase 3 — Profile Hygiene Guard
- Add optional `doctor` check for global alias leakage:
  - detect if external PowerShell profiles bind `claudine` away from repo facade.
- Outcome:
  - prevent Stratum A regressions.

### Phase 4 — Archeology Classifier Automation
- Extend `scripts/harvest_claudines.ps1` report classification tags:
  - `KEEP`, `TRANSFORM`, `QUARANTINE`, `DROP`
- Outcome:
  - future harvests become decision-ready without manual triage.

## Immediate Classification Verdict
- `claudineENV` should be **dethroned** to `TRANSFORM` source only.
- `claudine` should be the **single compatibility facade**.
- `chthonic` remains **sole logic authority**.

## How to Verify Current State
- `chthonic doctor --origins`
- `chthonic status --json`
- `pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/claudine.ps1 status --json`
