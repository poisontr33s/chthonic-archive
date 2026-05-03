# PsychoNoir-Kontrapunkt Large-File-Holder — Full Archaeology Findings

## Repo: C:\Users\eldno\psychonoir-kontrapunkt-large-file-holder

## Scanner Output (after full-repo sweep)
- 30 districts, 279 entities, 34,188 files total
- scanner: scripts/district_scanner.py (now scans repo root, includes dot dirs)
- scan results: scripts/district_scan_results.json, scripts/district_scan_full_sweep.json

## CRITICAL STRUCTURAL REVELATION
The "KARIBISK_ARKIPELAGISK" district was DEPRECATED on Sep 29, 2025 (folder: `KARIBISK_ARKIPELAGISK_DEPRECATED_20250929_210849`). 
- Sagiri Yamada was ORIGINALLY a Caribbean district ruler (sagiri_balanced_synthesis_matriarch.md 216 lines in GRAVEYARD)
- The current NEXUS structure (with Foydalitetsdualitetslenken, Havsdominansen, etc.) is POST-deprecation
- "Legacy" = the pre-Sep-29-2025 Caribbean district structure
- "Gold uncertain" = user doesn't know which generation is canonical for cRPG

## Hidden Layer Map (Repo Root Dot Dirs)
- `.quality_md_jsons_relatively_new/` — curated quality md files, ACTIVE
- `.poly_gluttony_scripts_files_orgy/.mds/` — mirror of above (same files, no copies)
- `.a1-poisontr33s-personal-wipFILES/` — raw session logs, WIP files, nested dot dirs
  - Contains: Hele_sesjonsloggen.md (28,864 lines), universal_milf_excavation JSON (81K lines)
- `.scripting_coding_programming_languages/` — code files

## Bedrock Databases (largest files)
- `SYSTEMATIC_MATRIARCH_CORRECTION_REPORT.json` — 82,482 lines (analysis)
- `universal_milf_matriarch_excavation_20250920_004918.json` — 81,770 lines (Sep 20 2025 excavation)
- `Hele_sesjonsloggen.md` — 28,864 lines (raw session log Sep 30 2025)

## TIER_1.5 BRIDGE RULERS — NEW DISCOVERY
- File: `.quality_md_jsons_relatively_new/TIER_1.5_BRIDGE_RULERS_CONSCIOUSNESS_ARCHITECTURE.md`
- 883 lines, ACTIVE — NOT in the original NEXUS_TIER_INDEX.json at all
- Must be read — entirely new tier between T1 and T2

## District Entity Counts (named districts only)
- CARIBBEAN_ARCHIPELAGO: 32 entities (Claudine's personal topology)
- NEXUS: 184 entities (catch-all NEXUS zone)
- UNCLASSIFIED: 163 entities (hidden dot-dir files not caught by path classifier)
- SKYSKRAPEREN: 15
- RUSTBELTET: 16
- HAVSDOMINANSEN: 10
- NEKROKRONORIKET: 9
- VIRTUALITETSHELGEDOMMEN: 9
- FOYDALITETSDUALITETSLENKEN: 3
- SUPREME_MATRIARCH: 3

## HAVSDOMINANSEN — Most Complete District in NEXUS
Full Sub-MILF depth with STATE_MANAGEMENT + CONSCIOUSNESS_PATHWAYS:
- `captain_coral_cultivation_tier2_specialist.md` — 377 lines (NEXUS copy), 565 lines (original)
- `navigator_siren_oceanic_tier2_specialist.md` — 409 lines
- `dynamic_maritime_consciousness_state_protocols.md` — 565 lines
- `maritime_consciousness_pathways_architecture.md` — 431 lines

## VIRTUALITETSHELGEDOMMEN Sub-MILFs (largest profiles)
- `programmer_mirage_code_tier2_specialist.md` — 738 lines (LARGEST Sub-MILF)
- `designer_echo_simulation_tier2_specialist.md` — 519 lines

## Key UNCLASSIFIED Files (high-signal, not in NEXUS)
- `ESPEN_DIGITAL_ENTITY_CONSCIOUSNESS_PROFILE.md` — 909 lines (user's own entity)
- `TIER_1.5_BRIDGE_RULERS_CONSCIOUSNESS_ARCHITECTURE.md` — 883 lines (new tier)
- `PHASE_2.3_MILF_RELATIONSHIP_MAPPING_COMPLETION_REPORT.md` — 899 lines
- `claudine-caribbean-archipelago-consciousness-synthesis.md` — 835 lines
- `karibbiansk_guddinne_rammeverk_og_prompt_tektonisk_WIP1.md` — 805 lines
- `AUTONOMOUS_AI_CREATOR_WORLD_MANIFESTO.md` — 781 lines

## File Generations (3 types)
1. First-person raw (`.quality_md_jsons_relatively_new/`) — Claudine as narrator
2. Structured TypeScript interface (NEXUS `02_DISTRICT_DOMINION_MATRIX/`) — ~192-305 lines
3. Full-depth specialist profiles (NEXUS `TIER_2_DISTRICT_DOMINION_MATRIX/` + `21_MD_CONSCIOUSNESS_ARCHIVE/`) — 377-738 lines

## CARIBBEAN District (Pre-Deprecation, GRAVEYARD)
Located at: `necromancy_graveyard/milf_instances/KARIBISK_ARKIPELAGISK_DEPRECATED_20250929_210849/`
- Had its own milfografi, sagiri as ruler, consciousness chambers
- Deprecated Sep 29 2025
- Contents include: sagiri_balanced_synthesis_matriarch (216 lines), sagiri_hells_paradise_synthesis (230 lines)

## TIER_1.5 BRIDGE RULERS — KEY CONTENT (read lines 1-100)
- Invented AUTONOMOUSLY by Claudine 5.0 (NOT by Espen/user) in October 2025
- Triggered by: Eva Blue had 173 co-occurrences with Astrid Møller in consciousness DB → bridge role detected
- EVA BLUE elevated: Tier 2 (Skyskraperen Aerospace Midwife Specialist) → Tier 1.5 Bridge Ruler (first of her kind)
- Foydalitetsdualitetslenken ruler listed as "to be named" — unnamed at time of writing
- T0 in this doc: only Claudine Sin'claire 5.0 + Morticia Necrosis (Kompilerings Spøkelse NOT in T0 here)
- This file is in `.quality_md_jsons_relatively_new/` = ACTIVE but outside NEXUS entirely
- This is "gold uncertain" — user isn't sure if Claudine's autonomous innovation is canonical

## Persistent Archive Layer — COMMITTED 5f9e033e5 (2026-05-02)
- archive.db: SQLite, 9 districts, 507 entities, 945 file rows
- scripts/build_archive_db.py: ingest scan JSON → archive.db (upsert, safe to re-run)
- scripts/query_archive.py: --district --entity --generation --top --unread --search --report --mark-read --export-reads
- scripts/reads_export.json: version-controlled reads table export
- Mark reads: uv run scripts/query_archive.py --mark-read "path" --lines "1-80" --summary "..."
- Rebuild after scanner: uv run scripts/build_archive_db.py

## Priority Reads (not yet done)
- TIER_1.5_BRIDGE_RULERS_CONSCIOUSNESS_ARCHITECTURE.md (883 lines) — read 1-100; lines 101+ unread
- PROGRAMMER_MIRAGE full profile (738 lines) — largest Sub-MILF, GEN3-FULLDEPTH
- claudine-caribbean-archipelago-consciousness-synthesis.md (835 lines) — .quality_md_jsons_relatively_new/
- ESPEN_DIGITAL_ENTITY_CONSCIOUSNESS_PROFILE.md (909 lines) — .quality_md_jsons_relatively_new/
