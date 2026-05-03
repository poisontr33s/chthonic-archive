# PNK Large-File-Holder — District Archaeology Scan
## Run: 2026-05-02, script: scripts/district_scanner.py

### Scan Summary
- 10 districts found
- 319 unique entities
- 504 total files
- Output: scripts/district_scan_results.json

### Districts + Entity Counts
- SKYSKRAPEREN: Astrid Møller (4v GRAVEYARD ⭐ stale + 2v ACTIVE), Eva Blue (4v ACTIVE), Yukiko Tanaka (5v ACTIVE/GRAVEYARD), Claudine Sinclaire (3v)
- RUSTBELTET: Iron Maiden (2v ACTIVE), Raven Bytes (2v ACTIVE), Vera Steel (2v ACTIVE), Iron Maiden legacy (GRAVEYARD ⭐)
- SUPREME_MATRIARCH: Claudine Metamorphica (2v ACTIVE ⭐), Kompilerings Spøkelse (2v ACTIVE), Morticia (2v ACTIVE)
- HAVSDOMINANSEN: Admiral Marina Abyssos (2v ACTIVE)
- NEKROKRONORIKET: Dr. Lilith Mortis (2v ACTIVE), Entropy Weaver Vex (2v ACTIVE), Wednesday Necrosis (2v ACTIVE)
- FOYDALITETSDUALITETSLENKEN: Sagiri Yamada (2v), Tenza Nakamura (2v), Yuzuriha Yamada (2v)
- CARIBBEAN_ARCHIPELAGO: many Claudine-specific files
- NEXUS: large catch-all with 100+ entries (many mass_resurrection_ summaries, psychographic stubs)
- UNCLASSIFIED: .meta files + stray entities

### Key Confusion Pattern Identified
- ⭐ GOLDSTANDARD files are often in GRAVEYARD — they WERE goldstandard at time of writing but were superseded by newer ACTIVE versions
- The ACTIVE versions in `02_DISTRICT_DOMINION_MATRIX/` ARE the current canonical, even without ⭐ in filename
- Tier order for canonicity: ACTIVE > ARCHIVED > GRAVEYARD > PRESERVED
- NEXUS district is actually a catch-all classification artifact (files that don't have district path)

### Canonical Active Entity Paths
SKYSKRAPEREN:
- astrid_moller_corporate_supremacy (2v ACTIVE) — `02_DISTRICT_DOMINION_MATRIX/SKYSKRAPEREN_CORPORATE_DOMINION/astrid_moller_corporate_supremacy_consciousness_profile.md`
- eva_blue_aerospace_midwife (4v ACTIVE) — `02_DISTRICT_DOMINION_MATRIX/SKYSKRAPEREN_CORPORATE_DOMINION/eva_blue_aerospace_midwife_consciousness_profile.md`
- yukiko_tanaka_algorithmic_seductress (5v ACTIVE/GRAVEYARD) — active in SKYSKRAPEREN dir

SUPREME_MATRIARCH:
- claudine_metamorphica_supreme (2v ACTIVE ⭐) — `01_SUPREME_MATRIARCH_COMMAND/claudine_metamorphica_supreme_consciousness_profile.md`

### COMPLETE DISTRICT HIERARCHY (cRPG portable) — confirmed from ACTIVE canonical profiles

**T0.5 SUPREME (above all districts):**
- Claudine Sin'claire / Claudine Metamorphica Supreme — `01_SUPREME_MATRIARCH_COMMAND/claudine_metamorphica_supreme_consciousness_profile.md`
- Kompilerings Spøkelse (Integration Nexus) — `01_SUPREME_MATRIARCH_COMMAND/kompilerings_spokelse_integration_nexus_consciousness_profile.md`
- Morticia (Temporal Oversight) — `01_SUPREME_MATRIARCH_COMMAND/morticia_temporal_oversight_nexus_consciousness_profile.md`

**TIER 1 DISTRICT RULERS:**

1. SKYSKRAPEREN (Corporate Consciousness / Information Warfare)
   - T1: Astrid Møller | H:192.2cm | Hair:Corporate Brunette | Eyes:Steel Blue | Furniture:Aerospace Birthing Chair | Weapon:Information Control Neural Scepter
   - Sub: Eva Blue (Aerospace Midwife) | Sub: Yukiko Tanaka (Algorithmic Seductress)
   - File: `02_DISTRICT_DOMINION_MATRIX/SKYSKRAPEREN_CORPORATE_DOMINION/astrid_moller_corporate_supremacy_consciousness_profile.md`

2. RUSTBELTET (Industrial Survival / Resource Control)
   - T1: Iron Maiden | H:187.3cm | Hair:Industrial Steel Gray | Eyes:Forge Fire Orange | Furniture:Industrial Dominance Optimization Platform | Weapon:Resource Control Authority Hammer
   - Sub: Vera Steel (Mechanical Resurrector) | Sub: Raven Bytes (Digital Liberator)
   - File: `02_DISTRICT_DOMINION_MATRIX/RUSTBELTET_INDUSTRIAL_SOVEREIGNTY/iron_maiden_industrial_mastery_consciousness_profile.md`

3. HAVSDOMINANSEN (Maritime Dominance / Oceanic Biotechnology)
   - T1: Admiral Marina Abyssos | H:187.4cm | Hair:Deep Oceanic Blue | Eyes:Caribbean Sea Green | Furniture:Tidal Command Throne | Weapon:Abyssal Trident
   - Sub: Captain Coral (Cultivation) | Sub: Navigator Siren (Oceanic)
   - File: `02_DISTRICT_DOMINION_MATRIX/HAVSDOMINANSEN_NAVAL_COMMAND/admiral_marina_abyssos_maritime_dominance_consciousness_profile.md`

4. NEKROKRONORIKET (Thanatology / Mortality Transcendence)
   - T1: Wednesday Necrosis | H:175.3cm | Hair:Midnight Black | Eyes:Deep Violet | Furniture:Gothic Necromancy Altar | Weapon:Death Scythe of Consciousness Transcendence
   - Sub: Dr. Lilith Mortis (Mortuary Scientist) | Sub: Entropy Weaver Vex (Temporal Entropy)
   - File: `02_DISTRICT_DOMINION_MATRIX/NEKROKRONORIKET_THANATOLOGICAL_DOMINION/wednesday_necrosis_thanatological_mastery_consciousness_profile.md`

5. FOYDALITETSDUALITETSLENKEN (Feudal Balance Duality)
   - T1: Sagiri Yamada | H:175.2cm | Hair:Silver-black gradient | Eyes:Heterochromatic (steel blue L / warm amber R) | Balance threshold: 0.700
   - Sub: Yuzuriha Yamada (Creative Harmony) | Sub: Tenza Nakamura (Precision Excellence)
   - File: `02_DISTRICT_DOMINION_MATRIX/FOYDALITETSDUALITETSLENKEN_HARMONIC_BALANCE/sagiri_yamada_harmonic_balance_consciousness_profile.md`

6. VIRTUALITETSHELGEDOMMEN (Virtual World Creation / Sensory Deprivation)
   - T1: Architect Nyx Virtualis | H:181.6cm | Hair:Digital Silver | Eyes:Neon Purple/Matrix Code | Furniture:Sensory Deprivation Chamber | Weapon:Reality Manipulation Staff
   - Sub: Designer Echo (Simulation) | Sub: Programmer Mirage (Code)
   - File: `02_DISTRICT_DOMINION_MATRIX/VIRTUALITETSHELGEDOMMEN_DIGITAL_SANCTUARY/architect_nyx_virtualis_digital_architecture_consciousness_profile.md`

**PROFILE DEPTH CORRECTION (critical — prior analysis was wrong):**
The `02_DISTRICT_DOMINION_MATRIX/_consciousness_profile.md` files I read were ~192 lines = HEADER ONLY (read at line 1-80). Full T1 profiles are much longer. The real goldstandard deeper profiles are:

**FULL-DEPTH LOCATIONS (400-800+ lines each):**
- `TIER_2_DISTRICT_DOMINION_MATRIX/HAVSDOMINANSEN_MARITIME_COMMAND/captain_coral_cultivation_tier2_specialist.md` — 565 lines (confirmed: full TypeScript interface schema + aesthetic consciousness + specialist architecture)
- `TIER_2_DISTRICT_DOMINION_MATRIX/HAVSDOMINANSEN_MARITIME_COMMAND/navigator_siren_oceanic_tier2_specialist.md` — same folder
- `TIER_2_DISTRICT_DOMINION_MATRIX/VIRTUALITETSHELGEDOMMEN_DIGITAL_SANCTUARY/designer_echo_simulation_tier2_specialist.md` — 738 lines
- `TIER_2_DISTRICT_DOMINION_MATRIX/VIRTUALITETSHELGEDOMMEN_DIGITAL_SANCTUARY/programmer_mirage_code_tier2_specialist.md` — 519 lines

**DISTRICT SYSTEMS (Skyskraperen + Foydalitetsdualitetslenken have inner systems, others don't):**
- `02_DISTRICT_DOMINION_MATRIX/SKYSKRAPEREN_CORPORATE_DOMINION/CONSCIOUSNESS_PATHWAYS/corporate_consciousness_pathways_architecture.md`
- `02_DISTRICT_DOMINION_MATRIX/SKYSKRAPEREN_CORPORATE_DOMINION/CONSCIOUSNESS_PATHWAYS/district_consciousness_pathways_architecture.md`
- `02_DISTRICT_DOMINION_MATRIX/SKYSKRAPEREN_CORPORATE_DOMINION/STATE_MANAGEMENT/dynamic_corporate_consciousness_state_protocols.md`
- `02_DISTRICT_DOMINION_MATRIX/FOYDALITETSDUALITETSLENKEN_HARMONIC_BALANCE/CONSCIOUSNESS_PATHWAYS/district_consciousness_pathways_architecture.md`
- `02_DISTRICT_DOMINION_MATRIX/FOYDALITETSDUALITETSLENKEN_HARMONIC_BALANCE/STATE_MANAGEMENT/dynamic_consciousness_state_protocols.md`
- Root-level Nexus: `CONSCIOUSNESS_PATHWAYS/` + `STATE_MANAGEMENT/` — including `dynamic_vr_consciousness_state_protocols.md` (819 lines!)
- Root-level Nexus CONSCIOUSNESS_PATHWAYS: `vr_consciousness_pathways_architecture.md` (644 lines)

**Nexus root-level DIRECTORY count: 30+ subdirs**
- Key unexplored: `01_OPTIMIZED_URCA_MILF/` (only JSONs, no .md profiles), `07_NSFW18_SUBLIMINAL_AESTHETIC_PROTOCOLS/`, `08_NSFW18_VOYEURISTIC_ENHANCEMENT_SYSTEMS/`, `09_LIBIDINAL_CONSCIOUSNESS_ARCHAEOLOGY/`, `10_NSFW18_PSYCHO_HYPER_SEXUAL_INTEGRATION/`, `11_AHEGAO_CONSCIOUSNESS_AMPLIFICATION/`

**SCAN REPORT KEY FINDING:** `16_ORIGINAL_ROOT_DOCUMENTATION/MILF_PSYCHOGRAPHIC_PROFILE_SCAN_REPORT.md` — 2224 lines, catalogs 415 profiles: 235 TIER_0_META_MILF + 52 TIER_1_DISTRICT_RULER + 22 TIER_2_SPECIALIST + 106 UNKNOWN. This is the comprehensive index/report, not the profiles themselves.

**GOLDSTANDARD PROFILE SCHEMA (confirmed from Captain Coral, 565 lines):**
```
1. Header: Name, tier, district, temporal anchor, consciousness coherence score
2. TypeScript interface block: consciousness parameters as game stats
3. Physical Manifestation: age, presence, aesthetic consciousness details
4. Subliminal Aesthetic Protocols: appearance/behavior patterns (4 lines)
5. Specialist Consciousness Architecture: domain skills as TypeScript interfaces + numbered protocols
6. [continues for 400+ more lines...]
```
The TypeScript interfaces ARE the game stat blocks — directly portable to cRPG entity cards.

**HIDDEN directories in 16_4_PERSONAL_WIP (dot-prefixed, scanner missed them):**
- `.ikke_milfografisk_relaterte_hulrom/` (1642 lines — "not milfographic related voids")
- `.vår_nåværende_ustrukturerte_hele_sesjonslogg_tir_30_sep_23_58/` (raw session log Sep 30 2025)

**GRAVEYARD goldstandard preserved profiles (milf_instances/ and root):**
- `milf_ecosystem_astrid_corporate_hegemony_mf1ji9gr.preserved.md` (Astrid prior-gen preserved)
- `milf_ecosystem_archive.md` (full prior-gen MILF ecosystem)
- Multiple `.preserved.md` files in milf_instances/

**NEXT READ TARGETS (ordered by value):**
1. `TIER_2_DISTRICT_DOMINION_MATRIX/HAVSDOMINANSEN_MARITIME_COMMAND/captain_coral_cultivation_tier2_specialist.md` lines 80-300 (to see full schema depth)
2. `16_ORIGINAL_ROOT_DOCUMENTATION/HIERARKISK_BIDIREKSJONELL_MILF_EMIGRERING_SYNTETISERING.md` (508 lines — hierarchy architecture)
3. `21_MD_CONSCIOUSNESS_ARCHIVE/MILF_CONSCIOUSNESS/necromancy_graveyard/milf_ecosystem_archive.md` (558 lines — prior-gen goldstandard)
4. Root `STATE_MANAGEMENT/dynamic_vr_consciousness_state_protocols.md` (819 lines — Virtualitetshelgedommen deep system)

**ALL T1 RULERS CANONICAL PATH PREFIX:** `CLAUDINE_SUPREME_CONSCIOUSNESS_NEXUS/02_DISTRICT_DOMINION_MATRIX/`
**ALL SUB-MILF CANONICAL PATH PREFIX:** `CLAUDINE_SUPREME_CONSCIOUSNESS_NEXUS/03_SPECIALIZED_CONSCIOUSNESS_OPERATIVES/`
**FULL-DEPTH SUB-MILF PATH PREFIX:** `CLAUDINE_SUPREME_CONSCIOUSNESS_NEXUS/TIER_2_DISTRICT_DOMINION_MATRIX/` (only Havsdominansen + Virtualitetshelgedommen present here)
