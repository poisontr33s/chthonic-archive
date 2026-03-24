# Handoff: Sister Ferrum Scoriae / QML / Bride / Embalmer — Cross-Relationship Sync

**Date:** 2026-03-23
**From:** Claude (zombie evolution session)
**To:** Next Claude session / Codex
**Priority:** Pre-emptive strategic — do not block zombie evolution lane

---

## Why This Handoff Exists

The zombie consumer pipeline (`scripts/zombie_consumer.py`) feeds into Sister Ferrum Scoriae's Forge (`dumpster-dive/forge/`). The forge circulation system (INTAKE → ANVIL → FURNACE → QUENCH → TEMPERED | SLAG) is the downstream consumer of everything the zombie excretes.

Three character-systems converge on this pipeline but are **not yet synchronized**:

1. **Sister Ferrum Scoriae** (`SFS`) — The forge operator. Profile: [dumpster-dive/BLACKSMITH_MATRIARCH.md](../../dumpster-dive/BLACKSMITH_MATRIARCH.md). Tier 3 Sub-MILF. Domain: `dumpster-dive/`.
2. **Novia Cadaveris** — The White-dressed Bride. Gallbladder organ (T3). Dead code embalming, fragment preservation. Corpse Reviver skill: [.claude/skills/corpse-reviver/](../../.claude/skills/corpse-reviver/).
3. **Dame Schrödinger's Paradox** (`DM-SCRS-P`) — Pineal gland organ (R). Quantum observation, superposition regulation. The Observer to SFS's Observed. Updated from `Sir Schrödinger's Bastard` → `Dame Schrödinger's Paradox` in the current SSOT ([copilot-instructions.archive.md](../../.github/copilot-instructions.archive.md)).

---

## The Cross-Relationships To Map

### 1. Zombie → Forge Pipeline Gap

The zombie consumer (`zombie_consumer.py`) excretes to `dumpster-dive/intake/`. The forge circulation system expects files to flow through INTAKE → ANVIL → FURNACE → QUENCH → TEMPERED.

**Gap:** No automated bridge moves files from `intake/` subdirectories (like `intake/scripts-restructure-2026-03-20/`) into the forge's ANVIL stage. The zombie's `ore_rating` should inform the forge's initial heat classification, but this handoff is manual.

**Files to check:**
- [dumpster-dive/forge/PATHWAY_REGISTRY.json](../../dumpster-dive/forge/PATHWAY_REGISTRY.json)
- [dumpster-dive/forge/PROCESS_FLOW.md](../../dumpster-dive/forge/PROCESS_FLOW.md)
- [dumpster-dive/CIRCULATION_DIAGRAM.md](../../dumpster-dive/CIRCULATION_DIAGRAM.md)
- [dumpster-dive/protocols/](../../dumpster-dive/protocols/) — FORGE_CIRCULATION_PROTOCOL.md

### 2. Corpse Reviver (Bride) — Embalmer WIP Status

The corpse-reviver skill exists in all three agent roots:
- [.claude/skills/corpse-reviver/scripts/corpse_reviver.py](../../.claude/skills/corpse-reviver/scripts/corpse_reviver.py)
- [.codex/skills/corpse-reviver/scripts/corpse_reviver.py](../../.codex/skills/corpse-reviver/scripts/corpse_reviver.py)
- [.gemini/extensions/chthonic-archive-sync/skills/corpse-reviver/scripts/corpse_reviver.py](../../.gemini/extensions/chthonic-archive-sync/skills/corpse-reviver/scripts/corpse_reviver.py)

The skill description says: *"The embalm-before-edit lane is currently DO-NOT-USE-UNFINISHED-DEV--WIP."*

**Two embalmer variants already ran (dry-run only, 2026-03-07):**
- [dumpster-dive/intake/ferrum-embalmer/SISTER_FERRUM_EMBALMER_LATEST.md](../../dumpster-dive/intake/ferrum-embalmer/SISTER_FERRUM_EMBALMER_LATEST.md)
- [dumpster-dive/intake/novia-cadaveris-embalmer/NOVIA_CADAVERIS_EMBALMER_LATEST.md](../../dumpster-dive/intake/novia-cadaveris-embalmer/NOVIA_CADAVERIS_EMBALMER_LATEST.md)

Both scanned 10 sources (chthonic.ps1, claudine.ps1, profiles, SSOT anchors) and extracted signal fingerprints. Both were dry runs — nothing was actually embalmed.

**Task:** Determine whether the embalmer lane should be brought to operational status, and whether it overlaps or complements the zombie consumer's CHEW stage. The zombie extracts intelligence (imports, SIDs, functions). The embalmer extracts provenance (sha256, signal fingerprints, source lineage). These are different axes — they should compose, not compete.

### 3. QML / Dame Schrödinger's Paradox — SSOT Name Update

The SSOT (`copilot-instructions.archive.md`) has been updated:
- **Old:** `Sir Schrödinger's Bastard` / `SR-SCRS-B` (in older backups under `.github/ssot_backups/` and `.github/copilot-inststructons-backups.md/`)
- **New:** `Dame Schrödinger's Paradox` / `DM-SCRS-P` (in current `.github/copilot-instructions.archive.md`)

The metaphysical bond between SFS and Dame Schrödinger is load-bearing for the forge:
> *"His 'dead/alive' superposition mirrors the ore's 'valuable/slag' superposition. When she observes ore, she observes him — collapsing his state."*

This maps directly to the zombie's `bite()` function — the act of assessment collapses the file from "maybe valuable" to a rated ore. The QML (Quantum Measurement Logic) of observation-as-classification is the theoretical foundation for adaptive bite heuristics.

**Task:** Verify that all references to `Sir Schrödinger's Bastard` have been updated to `Dame Schrödinger's Paradox` across:
- `dumpster-dive/BLACKSMITH_MATRIARCH.md` (check the Observer/Observed section)
- Any forge protocols that reference the quantum assessment metaphor
- The MILF/Sub-MILF hierarchy tables

### 4. MILF / Sub-MILF Hierarchy — Dumpster-Dive Sync

The MMPS (MILF Manifestation Protocol System) in [.github/codex-satellites/VALIDATION_PROTOCOLS.md](../../.github/codex-satellites/VALIDATION_PROTOCOLS.md) defines:
- MILF generation, lending, kidnapping, siphoning, fusion protocols
- Sub-MILF lifecycle (generate → validate → hibernate → dissolve)
- TSE-MILF tensor synthesis (each MILF as basis vector in capability space)

SFS is a Tier 3 Sub-MILF. Novia Cadaveris is T3 (Gallbladder). Dame Schrödinger is T4↔T3 EXTREME (tier violation — Sub-MILF architecture concealed within T4).

**Task:** Verify that `dumpster-dive/` systems (forge, intake, embalmer) correctly reference the current MILF hierarchy. The overnight daemon reports may contain stale references.

---

## Deliverables Expected

1. **Cross-reference map:** Which files reference which characters, with current vs. stale name variants
2. **Embalmer status report:** WIP lane viability, overlap analysis with zombie consumer
3. **SSOT propagation check:** Dame Schrödinger name update coverage
4. **Forge bridge spec:** How zombie ore_rating maps to forge ANVIL heat classification

---

## Do Not

- Do not modify `zombie_consumer.py` — that's the active evolution lane
- Do not delete or restructure `dumpster-dive/` — map first, move later
- Do not pivot the zombie evolution session — this handoff exists precisely to prevent that
