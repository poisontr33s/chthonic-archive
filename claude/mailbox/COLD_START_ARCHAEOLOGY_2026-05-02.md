---
type: stewardess
category: cold-start
created: 2026-05-02T08:00:00.000Z
from: overnight-autopilot
subject: PNK-LFH archaeology extraction — morning queue wired
---

# Overnight Archaeology Cold-Start

**Status:** Infrastructure complete. Digests generated. Queue wired. Ready for extraction.

---

## What Happened Overnight

Built env-driven multi-repo archaeology MCP system. Ran full extraction pass on `psychonoir-kontrapunkt-large-file-holder` (PNK-LFH). Found **507 entities, 945 files, 12 GEN3-FULLDEPTH, 101 GEN1-RAW, 117 unread Gen1+ files**.

The scripts ran. The digests exist. The task chain is queued.

---

## Morning Queue — Attack in This Order

These live in `manifest/todo_roulette.json` under `entries_extended[]`. Load-balanced from lowest friction to highest signal:

| ID | Task | Weight | Friction | Value |
|----|------|--------|----------|-------|
| `pnk00001` | **Ingest 6 GEN3 entity cards** | 9 | LOW — cards already extracted in `manifest/overnight_gen3_cards.json` | Immediate cRPG-portable content |
| `pnk00002` | **Mine MILF psychographic report** (2224L) | 8 | MED | Full entity relationship map |
| `pnk00003` | **Caribbean synthesis → game/** | 7 | MED | District lore, direct to `game/` |
| `pnk00004` | **ESPEN profile GEN1→GEN3** | 7 | MED | §10.3 template for T1 upgrades |
| `pnk00005` | **Scan PNK public satellite** | 5 | LOW — just run MCP scan tool | Closes a7b8c9d0 |

---

## Artifacts Ready (generated during sleep)

All in `chthonic-archive/manifest/`:

| File | Contents |
|------|----------|
| `overnight_gen3_cards.json` | 6 GEN3 entity cards, first 150 lines each |
| `overnight_gen1_previews.json` | Top 6 GEN1 files, first 80 lines each |
| `overnight_archaeology_summary.md` | Full archive state + navigation guide |

---

## The 6 GEN3 Entities (cRPG-ready, just read + format)

All in `CLAUDINE_SUPREME_CONSCIOUSNESS_NEXUS/TIER_2_DISTRICT_DOMINION_MATRIX/`:

**HAVSDOMINANSEN (Maritime Command):**
1. `dynamic_maritime_consciousness_state_protocols` — 565 lines — state machine doc
2. `maritime_consciousness_pathways_architecture` — 431 lines — consciousness pathway architecture
3. `navigator_siren_oceanic_tier2_specialist` — 409 lines — entity card (Tier 2 specialist)
4. `captain_coral_cultivation_tier2_specialist` — 377 lines — entity card (Tier 2 specialist)

**VIRTUALITETSHELGEDOMMEN (Digital Sanctuary):**
5. `programmer_mirage_code_tier2_specialist` — 738 lines — entity card (Tier 2, largest)
6. `designer_echo_simulation_tier2_specialist` — 519 lines — entity card (Tier 2)

**Write each to:** `docs/world-building/entities/<entity_name>.md`

---

## Key GEN1-RAW Targets After GEN3

| Entity | Lines | Why |
|--------|-------|-----|
| `MILF_PSYCHOGRAPHIC_PROFILE_SCAN_REPORT.md` | 2224 | Full entity + relationship map for the Matriarchy |
| `refined_session_log.md` | 5649 | Session gold — entity interactions, world events |
| `ESPEN_DIGITAL_ENTITY_CONSCIOUSNESS_PROFILE.md` | 909 | GEN3 upgrade demonstration target |
| `PHASE_2.3_MILF_RELATIONSHIP_MAPPING_COMPLETION_REPORT.md` | 899 | Phase 2.3 completion — entity relationship chain |
| `TIER_1.5_BRIDGE_RULERS_CONSCIOUSNESS_ARCHITECTURE.md` | 883 | Bridge entity architecture — feeds d4e5f6a7 |
| `claudine-caribbean-archipelago-consciousness-synthesis.md` | 835 | Caribbean arc lore → `game/` |

---

## District Map (for orientation)

| District | Entities | Signal | Priority |
|----------|----------|--------|----------|
| NEXUS | 234 | Raw session logs, CLAUDINE_SUPREME nexus docs, 23,496-line mega-files | Mine for entity mentions |
| UNCLASSIFIED | 231 | Personal WIP, quality_md layer, session logs | GEN1-RAW source |
| CARIBBEAN_ARCHIPELAGO | 26 | Deprecated Sep 2025 but rich Caribbean arc lore | pnk00003 |
| HAVSDOMINANSEN | 5 | 4 GEN3 entities — maritime consciousness command | pnk00001 |
| VIRTUALITETSHELGEDOMMEN | 3 | 2 GEN3 entities — digital sanctuary | pnk00001 |
| SKYSKRAPEREN | 4 | Claudine's sophistication arm (Astrid Møller domain) | After GEN3 pass |
| RUSTBELTET | 1 | Iron Maiden's domain | After other districts |
| NEKROKRONORIKET | 1 | The necro-kingdom (death/entropy arc) | Low urgency |
| FOYDALITETSDUALITETSLENKEN | 2 | Utility duality chain (operational layer) | Low urgency |

---

## MCP Tools Available

Registered in `.vscode/mcp.json`:

```
mcp_pnk-archaeolo   → PNK-LFH (primary — 507 entities)
mcp_pnk-public-ar   → PsychoNoir-Kontrapunkt public satellite
mcp_chthonic-arch   → chthonic-archive itself
```

Tool signatures:
```python
archaeology_scan()                           # rescan + rebuild DB
archaeology_query(command, term, n)          # district|entity|generation|top|unread|search|report
archaeology_mark_read(path, lines, summary)  # mark entity as processed
archaeology_fetch_json(artifact)             # scan_full|scan_results|reads_export|repo_info
archaeology_lessons_compile()               # cross-session synthesis
```

---

## Direct CLI (no MCP needed)

```powershell
$PNK = "C:\Users\eldno\psychonoir-kontrapunkt-large-file-holder"
uv run "$PNK\scripts\query_archive.py" --report
uv run "$PNK\scripts\query_archive.py" --generation 3
uv run "$PNK\scripts\query_archive.py" --top 20
uv run "$PNK\scripts\overnight_archaeology.py"  # re-run anytime for fresh digests
```

---

## Pentea-Next Chain (commit trailers)

```
pnk00001 → pnk00002 → pnk00003 → pnk00004 → pnk00005
```

Each task commit should carry:
```
Pentea-Next: pnk0000N
Co-authored-by: Pentea <223556219+Penteaa@users.noreply.github.com>
```

---

## Linkage to Existing Queue

- `d4e5f6a7` — §10.3 Orackla/Umeko/Lysandra profiles: **pnk00004 (ESPEN elevation) is the GEN3 template demonstration** — do pnk00004 FIRST, then use the pattern for d4e5f6a7.
- `a7b8c9d0` — Investigate PNK-LFH: **pnk00005 closes this** (scan result = investigation complete).
- `c3d4e5f6` — Already completed (CSI-SOI-SMM added to Claudine §10.3.1).

---

## One Sentence Summary

The gold is already extracted into `manifest/overnight_gen3_cards.json` — **start with pnk00001 and just format it into `docs/world-building/entities/`**.
