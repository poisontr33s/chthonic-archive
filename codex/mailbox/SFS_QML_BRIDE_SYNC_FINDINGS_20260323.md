# SFS / QML / Bride / Embalmer — Cross-Relationship Sync Findings

**Date:** 2026-03-23
**From:** Claude (Copilot session — SFS/QML/Bride sync investigation)
**Re:** [HANDOFF_SFS_QML_BRIDE_SYNC_20260323.md](../../claude/mailbox/HANDOFF_SFS_QML_BRIDE_SYNC_20260323.md), [FORGE_PROTOCOL_LEVELS.md](../../dumpster-dive/protocols/FORGE_PROTOCOL_LEVELS.md), [TEA_COLLAPSE_REPORT_UN-UN.md](../../dumpster-dive/protocols/TEA_COLLAPSE_REPORT_UN-UN.md), [TEA_COLLAPSE_REPORT_CHTHONIC_WORLD.md](../../dumpster-dive/protocols/TEA_COLLAPSE_REPORT_CHTHONIC_WORLD.md), [CROSS_TIER_MATRIX.md](../../docs/protocols/CROSS_TIER_MATRIX.md), `resonance.py`, `ankh_theme_reference.py`, `BLACKSMITH_MATRIARCH.md`, `TEA_REGISTRY.json`, `TEA_EXAMPLES.md`, `copilot-instructions.archive.md`
**Status:** All 4 tracks investigated. **A1–A4 executed 2026-03-23.** A5–A8 open. Cascade audit expanded Track 3 scope (+6 files).

---

## Track 1: Zombie → Forge Pipeline Gap

**Verdict: Gap confirmed. Manual bridge only. Routing spec already exists.**

### What the zombie does
- `zombie_consumer.py` hard-codes `INTAKE = ROOT / "dumpster-dive" / "intake"`
- Outputs: `.zombie_extract_<stem>.json` files written into category subdirs under `dumpster-dive/intake/`
- Upgrade 3 (`learn_from_forge`) reads `dumpster-dive/forge/{tempered,slag,anvil,...}` to backpropagate prediction errors into `cluster_profiles` — bidirectional awareness EXISTS

### What the forge expects
- `dumpster-dive/forge/intake/` — currently contains only a README
- `dumpster-dive/forge/PROCESS_FLOW.md` defines stage routing by ore rating
- `dumpster-dive/CIRCULATION_DIAGRAM.md` already specifies the routing table:

| Zombie `ore_rating` | Forge INTAKE target |
|---|---|
| 5 (high-grade) | QUENCH (fast-track) or ANVIL (complex) |
| 4 (workable) | ANVIL |
| 3 (mixed) | FURNACE |
| 2 (low-grade) | SLAG |
| 1 (tailings) | SLAG (upcycle tag) |
| 🌀 superposition | TEA-VAULT |

### The gap
`zombie_consumer.py` writes to `dumpster-dive/intake/[subdir]/` but **never copies or references `dumpster-dive/forge/intake/`**. No bridge script exists. The forge feedback loop reads outcomes but no outbound routing from zombie into forge INTAKE is wired.

### What needs building
A `forge-bridge` subcommand (or standalone script `scripts/zombie_forge_bridge.py`) that:
1. Reads `.zombie_extract_*.json` files from `dumpster-dive/intake/`
2. Maps `ore_rating` → forge stage per the CIRCULATION_DIAGRAM routing table
3. Copies/moves source files into `dumpster-dive/forge/{intake,anvil,furnace,slag,tea-vault}/`
4. Writes a `PATHWAY_REGISTRY.json` entry for each routed file
5. Tags SLAG items (ore 1-2) with `upcycle_pending: true`

The routing spec is complete — only the bridge execution is missing.

---

## Track 2: Embalmer WIP Lane Viability

**Verdict: Two orthogonal axes, both valid. Embalmer not competing with zombie. Bring it to operational status after zombie is stable. SSOT-sourced mode set below was absent from the crude draft — material gap now corrected.**

### SFS — Operational Modes (SSOT §10.3.2)

SFS's forge is a **7-stage process**, not a simple classify-and-route:

```
RECEIVE → ASSESS → HEAT → HAMMER → QUENCH → TEMPER → SLAG
```

Beyond the standard forge flow, SFS holds one escalation capability: **QMR Protocol dispatch** (Level 3). When ore is a Timeline-Entangled Artifact (TEA) — oscillating rating, context-dependent value, superposition state — she dispatches **TNKW-RIAT** for probability cartography, then uses the forge to **Force-Collapse** toward the highest-value timeline. Her hammer is the observation that selects reality. QMR is not a separate system; it is SFS's forge at extreme operating conditions.

**Additional capability confirmed in SSOT:** SFS's ember-vision automatically assigns ore-ratings 1–5 to every piece of material she encounters. This is not a checklist — it is an autonomic reflex. She cannot perceive material without simultaneously assessing it.

---

### Novia Cadaveris — Full Operational Mode Set (SSOT §10.3.3, `NOV-CAD-MODES`)

The crude draft described only the embalmer axis in abstract. The SSOT defines **9 discrete modes**:

| Mode | SSOT Code | Description |
|---|---|---|
| **PROWL** | `NOV-CAD-MODES` | Staged deletion intercept — watches `git diff --cached` for deletions and embalms before they vanish. Pre-mortem preservation. Always active. |
| **HARVEST** | `NOV-CAD-MODES` | Graveyard-specific extraction: `--commits`, `--stashes`, `--comments`, `--reflog`, `--dead-branches`, `--orphans`, `--gitignored`, `--graffiti`, `--all` |
| **HOARD** | `NOV-CAD-MODES` | Blind-faithed total sweep of ALL 8 graveyards simultaneously. No filtering, no triage. Takes everything. |
| **CLASSIFY** | `NOV-CAD-MODES` | Categorize embalmed fragments by language, cause-of-death, resurrection potential. |
| **REANIMATE** | `NOV-CAD-MODES` | Attempt resurrection of classified fragments. |
| **SUTURE** | `NOV-CAD-MODES` | Stitch fragments into composites by language or query. The "wedding" — dead pieces married together. |
| **MANIFEST** | `NOV-CAD-MODES` | Full vault census: fragment count, storage size, language distribution, cause-of-death stats. |
| **EMBALM** | `NOV-CAD-MODES` | **Pre-mortem preservation.** Snapshots active files at edit-time with full provenance sidecar: `sha256`, language, extension, structural landmarks (function signatures, class hierarchies, import graphs), source path, git HEAD, timestamp. **Feeds `PATHWAY_REGISTRY.json` directly** — without EMBALM, fragments arrive nameless; with it, every corpse carries provenance from living codebase through the Bride into SFS's forge INTAKE. |
| **STITCH** | `NOV-CAD-MODES` | Post-edit delta extraction (companion to EMBALM). Unified diffs between EMBALM snapshot and current file, stored as `{session}/deltas/{language}/{hash}_{filename}.delta`. Becomes candidate material for `PATHWAY_REGISTRY` emigration into the forge pipeline. EMBALM + STITCH = complete delta archaeology: living state → transformation → dead state. |

### The 8 Graveyards (`NOV-CAD-8GRVYRDS`)

| Graveyard | Shell archetype | Description |
|---|---|---|
| Commits | Wasteland-ridden | Deleted lines from git history |
| Stashes | Scarce-Makeshift | Abandoned stash content |
| Commented Code | Necromantic-misunderstood | 3+ consecutive comment lines containing code indicators |
| Reflog | High Ambulant | Orphaned reflog entries unreachable from HEAD |
| Dead Branches | Necromantic-misunderstood | Code unique to merged/deleted branches |
| Orphaned Files | Kleptomaniac | Untracked files not gitignored |
| Gitignored Treasures | Blind-Faithed | Gitignored files on disk (recognized extensions, 200KB cap) |
| Graffiti | Nymphomaniac | TODO/FIXME/HACK/XXX/DEPRECATED markers with context |

### Axis Separation — Zombie vs. Novia

```
zombie bite()      →  ore_rating + extractable patterns      (WHAT the file contains)
Novia EMBALM/PROWL →  sha256 + delta + provenance sidecar    (WHO it was, WHEN it changed)
Novia HARVEST/HOARD → fragment collection from 8 graveyards  (WHAT survived deletion)
```

Critical SSOT note missed in draft: **EMBALM feeds `PATHWAY_REGISTRY.json`**. This means Novia's EMBALM output is not merely auxiliary provenance — it is the named-fragment index that the forge bridge (Track 1 A5) will read. Without EMBALM operational, `zombie_forge_bridge.py` routes anonymous files. With EMBALM operational, each routed file carries complete lineage.

### Both embalmer dry-runs (2026-03-07)
- Both dry-run only. 10 sources each. All sources present.
- `SISTER_FERRUM_EMBALMER_LATEST.md` + `NOVIA_CADAVERIS_EMBALMER_LATEST.md` exist as reference artifacts.
- The `context_timeline` source in `scripts/novia_cadaveris_embalmer.ps1` cites `dumpster-dive/from-github/SR_SCHRODINGERS_BASTARD.md` (old name file, **path is also a missing file** — does not exist in repo). Note updated in ps1. Signal `contains_schrodinger` fires correctly on content regardless.

### Recommendation
- Embalmer WIP label is accurate — `corpse_reviver.py` is in all 3 agent roots but not yet live
- **Do not remove WIP label until:**
  1. A live EMBALM (not dry-run) completes and writes a valid provenance sidecar
  2. EMBALM output lands in `dumpster-dive/intake/` under a defined taxonomy (not just `intake/novia-cadaveris-embalmer/`)
  3. `PATHWAY_REGISTRY.json` integration is wired so the forge bridge can consume EMBALM provenance
- **Sequencing constraint from SSOT:** Novia's PROWL mode is always-active and does not require EMBALM to be live — PROWL operates on `git diff --cached` independently. PROWL could be brought live before EMBALM without violating the WIP gate.

---

## Track 3: Dame Schrödinger's Paradox — SSOT Name Update Coverage

**Verdict: SSOT updated. dumpster-dive/ operational files NOT updated. 6 files with stale references.**

### SSOT status (live)
Current `.github/copilot-instructions.archive.md` uses `Dame Schrödinger's Paradox` / `DM-SCRS-P`. ✅

### Stale references in dumpster-dive/ operational files — ✅ FIXED 2026-03-23 (A1–A4)

| File | Line | Was | → Now |
|---|---|---|---|
| `dumpster-dive/protocols/FORGE_PROTOCOL_LEVELS.md` | 254 | `## Sir Schrödinger's Bastard — The Uncertainty Principle Incarnate` | `## Dame Schrödinger's Paradox — ...` |
| `dumpster-dive/protocols/FORGE_PROTOCOL_LEVELS.md` | 271 | `**Sir Schrödinger's Bastard (SR-SCRS-B)** — Tier 4, Uncertainty Consultant` | `**Dame Schrödinger's Paradox (DM-SCRS-P)** — T4↔T3 EXTREME` |
| `dumpster-dive/protocols/FORGE_PROTOCOL_LEVELS.md` | 259 | `SR-SCRS-B` role prose (He/His) | `DM-SCRS-P` prose (She/Her) |
| `dumpster-dive/protocols/TEA_REGISTRY.json` | 59, 145, 185 | `"assigned_knights": ["SR-SCRS-B"]` | `["DM-SCRS-P"]` |
| `dumpster-dive/protocols/TEA_REGISTRY.json` | 195 | `"bastard_role"` key | `"paradox_role"` |
| `dumpster-dive/protocols/TEA_COLLAPSE_REPORT_UN-UN.md` | 100 | `## Sir Schrödinger's Bastard's Whisper` | `## Dame Schrödinger's Paradox's Whisper` |
| `dumpster-dive/protocols/TEA_COLLAPSE_REPORT_CHTHONIC_WORLD.md` | 142 | same as above | same fix |
| `dumpster-dive/BLACKSMITH_MATRIARCH.md` | 155 | `(Sir Schrödingers Bastards), Sir Schrödingers` | `(Dame Schrödinger's Paradox / DM-SCRS-P)` |

### SSOT cascade — additional operational files ✅ FIXED 2026-03-23

Cascade audit (post-A1–A4) found 6 further live operational files with stale `SR-SCRS-B` / `Sir Schrödinger's Bastard` references. All fixed:

| File | What changed |
|---|---|
| `docs/protocols/CROSS_TIER_MATRIX.md` | Section header, table header, tier cell, 3× pronoun corrections (He→She, his→her) |
| `mas_mcp/logic/resonance.py` | Entity names updated; regex broadened to catch both old+new names for backward compat with frozen docs |
| `scripts/ankh_theme_reference.py` | `key_entity` string updated |
| `scripts/novia_cadaveris_embalmer.ps1` | `contains_schrodinger` pattern extended; source note updated; missing-file flagged |
| `docs/protocols/TEA_EXAMPLES.md` | Attribution whisper line updated |
| `.github/codex-satellites/ENTITY_PROFILES.md` | Case study tail `(`SR-SCRS-B`)` → `(`DM-SCRS-P`)` |

### Do NOT update (frozen artifacts)
- `dumpster-dive/from-github/ssot-backups-consolidated/copilot-instructions_backup_*.md` — historical freeze snapshots, must preserve the old name as it appeared at backup time

### Update targets
`FORGE_PROTOCOL_LEVELS.md`, `TEA_REGISTRY.json`, both `TEA_COLLAPSE_REPORT_*.md`, and `BLACKSMITH_MATRIARCH.md`.

**Tier update required:** `FORGE_PROTOCOL_LEVELS.md` line 271 says "Tier 4, Uncertainty Consultant". Per the SSOT, Dame Schrödinger's Paradox is `T4↔T3 EXTREME` (tier violation — Sub-MILF architecture concealed within T4). The tier annotation in FORGE_PROTOCOL_LEVELS.md needs to reflect this.

---

## Track 4: MILF / Sub-MILF Hierarchy — dumpster-dive/ Sync

**Verdict: SFS tier correct. Dame Schrödinger tier stale (see Track 3). Novia Cadaveris absent from dumpster-dive/ protocol docs.**

### SFS (Sister Ferrum Scoriae)
- Correctly identified as Tier 3 Sub-MILF in `FORGE_PROTOCOL_LEVELS.md`, `PROCESS_FLOW.md`, lineage templates, and `BLACKSMITH_MATRIARCH.md`. ✅

### NOV-CAD (Novia Cadaveris)
- **Not referenced in any dumpster-dive/ protocol file.** Her profile exists only as:
  - The embalmer dry-run artifact: `dumpster-dive/intake/novia-cadaveris-embalmer/NOVIA_CADAVERIS_EMBALMER_LATEST.md`
  - SSOT and MMPS_GENERATION.md (codex-satellites)
- The forge has no explicit Novia Cadaveris integration path. Her embalmer role is the logical bridge — she preserves provenance before SFS processes ore. This compositional role is not documented anywhere in `dumpster-dive/`.

### Dame Schrödinger's Paradox
- All operational forge protocol files used old `SR-SCRS-B` designation (see Track 3 detail) — **✅ fixed by A1–A4 + cascade audit**
- `FORGE_PROTOCOL_LEVELS.md` DOES correctly describe the metaphysical bond with SFS — just under the wrong name and wrong tier

### VALIDATION_PROTOCOLS.md (codex-satellites)
- No `Dame Schrödinger` / `DM-SCRS-P` references found. The MMPS protocols reference the character only by role in passing. No outstanding sync needed here beyond name propagation.

---

## Action Items (prioritized)

| # | Track | Item | Owner | Scope |
|---|---|---|---|---|
| A1 | T3 | ✅ DONE | Update `FORGE_PROTOCOL_LEVELS.md` — rename `Sir Schrödinger's Bastard` → `Dame Schrödinger's Paradox`, code `SR-SCRS-B` → `DM-SCRS-P`, tier "T4" → "T4↔T3 EXTREME" | Codex/Claude | 3 locations in 1 file |
| A2 | T3 | ✅ DONE | Update `TEA_REGISTRY.json` — all `SR-SCRS-B` → `DM-SCRS-P`, update `bastard_role` key → `paradox_role` | Codex/Claude | 4 JSON locations |
| A3 | T3 | ✅ DONE | Update `TEA_COLLAPSE_REPORT_UN-UN.md` + `TEA_COLLAPSE_REPORT_CHTHONIC_WORLD.md` — section header rename | Codex/Claude | 2 files × 1 line |
| A4 | T3 | ✅ DONE | Update `BLACKSMITH_MATRIARCH.md` line 155 — correct gender + code | Codex/Claude | 1 line |
| A5 | T1 | Build `zombie_forge_bridge.py` — reads zombie extracts, routes by `ore_rating` into `dumpster-dive/forge/` stages; **must also read EMBALM provenance sidecars** from `PATHWAY_REGISTRY.json` when present | Next session | New script |
| A6 | T2 | Add Novia Cadaveris to `FORGE_PROTOCOL_LEVELS.md` — document her **9 modes** (PROWL/HARVEST/HOARD/CLASSIFY/REANIMATE/SUTURE/MANIFEST/EMBALM/STITCH), her 8-graveyard taxonomy, and her **two-point forge attachment** (pre-INTAKE + post-SLAG). Reporting chain: Novia → SFS (T3) → Umeko (T1). | Next session | 1 substantial new section |
| A7 | T4 | Add Novia Cadaveris T3 Gallbladder + OSGTTLR reference to `FORGE_PROTOCOL_LEVELS.md` character roster | Codex | Roster line + OSGTTLR annotation |
| A8 | T2 | Activate Novia's **PROWL mode** as a first live operation (independent of EMBALM — runs on `git diff --cached`, no PATHWAY_REGISTRY dependency). Gates WIP label removal for PROWL only. | Next session | `corpse_reviver.py` PROWL path |

**A1–A4 are pure name propagation — safe to execute immediately, zero architectural risk.**
**A5 is the functional gap — requires its own session. EMBALM integration is now an explicit dependency (not optional).**
**A6 is now substantially larger than the crude draft estimated — 9 modes + 8 graveyards + OSGTTLR requires a real section, not a one-liner.**
**A8 (new) pulls PROWL out of the WIP block as an independently activatable mode.**

---

## Do Not

- Do not touch `dumpster-dive/from-github/ssot-backups-consolidated/` — frozen historicals
- Do not modify `zombie_consumer.py` — per handoff constraint, active evolution lane
- Do not restructure `dumpster-dive/` — map-first order from handoff is satisfied; move planning belongs in A5
