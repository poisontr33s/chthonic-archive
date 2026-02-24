---
sid: DOC_SFS_WPTG_ITERATION_PLAN_V1
title: "SFS WPTG Iteration Plan — Sister Ferrum Scoriae Theme Pipeline"
type: methodology
status: active
priority: high
description: >
  Structured iteration plan for the SFS (Sister Ferrum Scoriae) theme,
  covering all three pillars: color theme, file/folder icons, and product icons.
  This is the WPTG baseline from which all other MILF/Sub-MILF themes descend.
created: 2026-02-24
authors:
  - Claude Code Opus 4.6
applies_to:
  - extensions/chthonic-archive/
tags:
  - wptg
  - sfs
  - theme-pipeline
  - iteration-plan
  - icon-pipeline
  - color-theme
---

<!--
@SID:           DOC_SFS_WPTG_ITERATION_PLAN_V1
@Type:          Methodology
@Context:       WPTG Theme Pipeline / SFS Baseline
-->

# SFS WPTG Iteration Plan

**Sister Ferrum Scoriae** — the Forge's own theme. The baseline from which all MILF/Sub-MILF themes descend.

> *"Ore enters; gold or slag exits. There is no middle state."*

---

## Scope Constraint

This plan covers **SFS only**. No Mandala, ROGBIV, or Decorator work.
Each MILF/Sub-MILF receives its own WPTG pass, using SFS as the structural template.

---

## Three Pillars

| Pillar | Artifact | Current State |
|--------|----------|---------------|
| **Color Theme** | `chthonic-geology-color-theme.json` | 669 workbench, 83 tokens, 57 semantic |
| **File/Folder Icons** | `chthonic-file-icon-theme.json` + 76 SVGs | 76 defs, 91 ext, 34 filenames, 33 langs, 35 folders |
| **Product Icons** | `chthonic-product-icon-theme.json` + 7 SVGs | 7 icons: pulse, shield, paintcan, layers, comment-discussion, hammer, flame |

---

## SFS Palette (Forge Colors)

| Token | Hex | Role |
|-------|-----|------|
| bg | `#050505` | Void substrate |
| stele | `#0A0A0A` | Panel background |
| fg | `#E8E2D2` | Primary text (aged papyrus) |
| gold | `#F4C430` | Accent / Egyptian primary |
| copper | `#D4714E` | Andean earth accent |
| amber | `#D7B562` | Warm neutral |
| rose-clay | `#D4907A` | Organic warmth |
| patina | `#7AAAB2` | Cool contrast |
| sandstone | `#B9A37A` | Desert neutral |
| weathered | `#908672` | Subdued secondary |
| kiln | `#E05545` | Alert / Andean fire |
| verdigris | `#8CB87A` | Growth / success |

---

## SFA Equilibrium

**Mandate**: 50/50 Egyptological × Andean balance across all design decisions.

- Egyptian Vertical Axis: 12 motifs (Ankh, Tyet, Wedjat, Djed, Ma'at, Scarab, Shen, Uraeus, Peseshkef, Heh, Ibis, Canopic Jar)
- Andean Horizontal Axis: 12 motifs (Quipu, Chakana, Tocapu, Cusco-as-Puma, Chumpi, Tinku, Pachakuti, Huaca, 12-Angled, Nazca, Inti, Pacha)
- Current Balance: **45.8% E / 54.2% A — BALANCED ✅**
- Engine: `scripts/sfa_cross_reference.py` (5 commands: scan, balance-audit, assign, extract, forge-digest)

---

## Pillar I — Icon Pipeline (Stages 0.0→3.0)

### Completed Stages

| Stage | Name | Gate | Status |
|-------|------|------|--------|
| **0.0** | Baseline Wet-Paper | 44 file + 32 folder + 7 product SVGs | ✅ Pass |
| **0.1** | Coverage Audit | Census mapped all workspace filetypes | ✅ Pass |
| **0.2** | Gap Fill — Bespoke Motifs | High-frequency uncovered types filled | ✅ Pass |
| **1.0** | Rendering Validation | 76/76 viewBox `0 0 16 16` | ✅ Pass |
| **1.1** | WCAG / Contrast Audit | 76/76 pass | ✅ Pass |
| **1.2** | Palette Coherence | 76/76 on-palette (0 off-palette colors) | ✅ Pass |

### Active Stages

| Stage | Name | Gate | Status |
|-------|------|------|--------|
| **2.0** | Structural Refinement | SVGO / path optimization / file size | ⚠️ Tooling exists (`icon_svg_optimizer.py`), no formal gate run |
| **2.1** | Motif Distinctiveness | All pairs below 0.85 similarity | ✅ 24→11 pairs resolved (commit `7a544db0`) |
| **3.0** | Gold Standard | All gates pass, ready for packaging | ⬜ Needs 11 remaining pairs (motif redesign) |

### Stage 2.1 — Collision Analysis

24 pairs above 0.85 threshold. Root cause: **color family over-concentration**.

| Color | Hex | Icons Using It | Collision Contribution |
|-------|-----|----------------|----------------------|
| patina | `#7AAAB2` | go, h, proto, ps1, ts, tsx | 10 collision pairs |
| rose-clay | `#D4907A` | cpp, css, cfg, svg, wasm, xml, yml | 6 pairs |
| gold | `#F4C430` | cmake, img, default, lock, rs, rust-toml | 4 pairs |
| sandstone | `#B9A37A` | font, json, md, rst, txt | 3 pairs |
| copper | `#D4714E` | map, py, toml | 1 pair |

**Resolution strategy**: Redistribute color assignments + differentiate motif silhouettes within same-color families. Icons that share a color MUST differ by ≥3 path elements and have distinct silhouette profiles.

### Pipeline Scripts (Icon Pillar)

| Script | Lines | WPTG Stage | Purpose |
|--------|-------|------------|---------|
| `icon_filetype_census.py` | 415 | 0.0 / 0.1 | Workspace filetype census + coverage gap mapping |
| `icon_svg_audit.py` | 392 | 1.0 / 1.1 / 1.2 | Structural, WCAG, palette validation |
| `icon_svg_optimizer.py` | 228 | 2.0 | SVG path optimization (SVGO equiv) |
| `icon_distinctiveness_audit.py` | 293 | 2.1 | Motif similarity / collision detection |
| `sfa_cross_reference.py` | 800 | (cross-cutting) | 50/50 balance engine, motif assignment |
| `theme_artcop.py` | 245 | (visual QA) | Screenshot-based quality assessment |
| `vscode-art-cop.ts` | — | (visual QA) | Screenshot automation for Art Cop |

---

## Pillar II — Color Theme (Stages 4.0→5.0)

The color theme is at 669/83/57 — a strong foundation. These stages refine and validate.

### Planned Stages

| Stage | Name | Description | Status |
|-------|------|-------------|--------|
| **4.0** | Token Scope Coverage Audit | Compare 83 token scopes against VS Code's full TextMate grammar universe. Identify syntax contexts with no assigned color. | ✅ 12/13 TM categories covered, 25/52 LSP types, 4/22 LSP modifiers + 15 custom SFS modifiers |
| **4.1** | Semantic Token Expansion | Validate 57 semantic keys cover all LSP semantic token types + modifiers used by major language servers (TS, Python, Rust, Go, C++). | ⬜ Not started |
| **4.2** | Workbench Key Completeness | Diff 669 workbench keys against VS Code's full `workbench.colorCustomizations` schema. Identify missing UI surfaces. | ⬜ Not started |
| **4.3** | Palette Discipline Audit | Verify every hex value in the theme is either from the SFS 12-color palette or a derivation (alpha, lighten, darken) with documented relationship. | ⬜ Not started |
| **5.0** | Color Theme Gold Standard | All syntax categories colored. All workbench surfaces covered. Every hex traceable to palette. Zero orphan colors. | ⬜ Not started |

### Pipeline Scripts Needed (Color Pillar)

| Script | Purpose | Exists? |
|--------|---------|---------|
| `theme_token_coverage.py` | Audit token scope vs full TextMate grammar | ❌ Create |
| `theme_workbench_completeness.py` | Diff workbench keys vs VS Code schema | ❌ Create |
| `theme_palette_discipline.py` | Trace all hex values to palette derivations | ❌ Create |
| `theme_parity.py` | Cross-theme comparison (existing) | ✅ 141L |

---

## Pillar III — Product Icons (Stages 6.0→7.0)

7 product icons exist. VS Code's product icon theme supports 400+ icon IDs. This pillar expands coverage.

### Planned Stages

| Stage | Name | Description | Status |
|-------|------|-------------|--------|
| **6.0** | Product Icon Census | Map all VS Code product icon IDs in active use (activity bar, status bar, editor widgets, debug, SCM, testing, etc.) against current 7. | ✅ 6/534 (1.1%) — 39 Tier 1 gaps, `hammer` invalid |
| **6.1** | Priority Expansion | Design and implement icons for highest-visibility product icon slots (activity bar, editor actions, debug controls). | ⬜ Not started |
| **6.2** | Product Palette + Motif Audit | Verify product SVGs use SFS palette and maintain Egypto-Andean motif vocabulary. | ⬜ Not started |
| **7.0** | Product Icon Gold Standard | All high-visibility slots covered. Palette and motif compliant. Visual coherence with file icons. | ⬜ Not started |

### Pipeline Scripts Needed (Product Pillar)

| Script | Purpose | Exists? |
|--------|---------|---------|
| `product_icon_census.py` | Map VS Code product icon IDs vs coverage | ✅ Created |
| Product SVG audit | Reuse `icon_svg_audit.py` (extend to product/ path) | ✅ Extend |

---

## Pillar IV — Extension Integration (Stages 8.0→9.0)

The extension manifest, commands, tree view, and build pipeline must be cohesive.

### Planned Stages

| Stage | Name | Description | Status |
|-------|------|-------------|--------|
| **8.0** | Manifest Validation | Verify `package.json` contributes (themes, icons, commands) are wired correctly. All theme files referenced. | ✅ Done (commit 1e3a880e) |
| **8.1** | Build Pipeline Health | `bun run compile` succeeds. `dist/extension.js` < 200KB. No dead imports. | ✅ Current: 100.33KB |
| **8.2** | Visual Regression Baseline | Capture Art Cop screenshots of SFS in active workspace. Store as baseline for future regression comparison. | ⬜ Not started |
| **9.0** | Release Readiness | Marketplace metadata (README, CHANGELOG, screenshots, gallery images) prepared. Version bumped. | ⬜ Not started |

---

## Pillar V — Metadata Standardization (Cross-Cutting)

Header/metadata conventions across all authored file types.

### Khipu-Cartouche Protocol (KCP) — Supersedes STD_V2 / PMS-v3

**Research Source:** `claude-codex-gemini/ANKH_EGYPTOLOGY_SOUTH_AMERICAN/ANKH_UNIFYING_REPOSITORY_METADATA_STANDARDS.md`
**Architecture:** Approach C — Stratified Metadata (Visual/Semantic Split)
**Hierarchy:** KCP > PMS-v3 > STD_SCRIPT_METADATA_V2 > Decorator's Blessing > per-framework

The KCP divides metadata into two ontologically distinct layers:

| Layer | Name | Content | Width |
|-------|------|---------|-------|
| Stratum 1 | **Cartouche** (Visual Envelope) | Artifact Name, Wedjat-Quipu Spectrum, Temple-Ayllu Zone, Ogdoad-Ceque Radiance | 80 chars, enumeration only |
| Stratum 2 | **Khipu** (Semantic Docstring) | @SID, @Shabti, @Heka-Ayni, @Ankh-Tinku, @Purpose | Unbounded, language-native |

**Key invariant:** @SID exists ONLY in the Khipu layer. Purpose exists ONLY in the Khipu layer. Zero duplication.

### KCP Phase Gates (KCP-0.0 → KCP-10.0)

| Phase | Name | Gate | Status |
|-------|------|------|--------|
| KCP-0.0 | Protocol Ontology Spec | 100% legacy fields mapped, 0 data loss | ✅ |
| KCP-1.0 | Architecture Ratification | Approach C locked, rejections documented | ✅ |
| KCP-2.0 | Template Canonization | 4 language templates pass native parser | ✅ DONE |
| KCP-3.0 | Python Consolidation | 0 duplicate @SIDs in 97 .py files (audit: 11L/2K/11H/73N) | ⬜ NEXT |
| KCP-4.0 | TypeScript Injection | `bun run compile` clean with JSDoc @tags | ⬜ |
| KCP-5.0 | PowerShell Encapsulation | `Get-Help` returns synopsis for 82 scripts | ⬜ |
| KCP-6.0 | Rust Alignment | `cargo doc --no-deps` clean for 15 files | ⬜ |
| KCP-7.0 | Tooling Refactor | Knowledge graph indexes all @SIDs | ⬜ |
| KCP-8.0 | SFA Equilibrium Audit | 50/50 balance on KCP ontology | ⬜ |
| KCP-9.0 | Legacy Purge Verification | 0 instances of `║ Purpose:` in envelopes | ⬜ |
| KCP-10.0 | Protocol Ascension | GOLD: 0% duplication, 100% coverage | ⬜ |

**Crash-Resilient Tracker:** [`docs/design/KCP_SESSION_CHECKPOINT.md`](KCP_SESSION_CHECKPOINT.md) — read this FIRST on session recovery.

### Legacy Stages (Pre-KCP)

### Compliance Matrix (2026-02-24)

| Language | Files | Shebang | Decorator's Blessing | @SID |
|----------|-------|---------|---------------------|------|
| Python | 120 | 100% | 48% | 39% |
| PowerShell | 82 | 100% | 39% | 2% |
| TypeScript | 62 | 16% | 42% | 5% |
| Rust | 15 | N/A | 100% | 0% |

### Planned Stages

| Stage | Name | Description | Status |
|-------|------|-------------|--------|
| **S.B** | Box Normalization | Normalize all Decorator's Blessing envelopes to open-sided (no right border). 145 files, 1422 lines. | ✅ Complete |
| **S.0** | Python Header Canon | Fix 92 scripts with spaced `# -*-` to tight `#-*-` per PMS-v3. | ✅ 143 files fixed, 0 spaced remaining |
| **S.1** | @SID Expansion | Raise @SID coverage from 19% to ≥60% across all languages. | ⬜ Incremental |
| **S.2** | TypeScript Shebang Sweep | Add `#!/usr/bin/env bun` to CLI-oriented `.ts` scripts missing it. | ⬜ Not started |
| **S.3** | Rust @SID Tags | Add `@SID` to all 15 Rust files within their existing Blessing envelopes. | ⬜ Not started |

### S.B Completion Record

- **Script:** `scripts/normalize_blessing_box.py` (`TOOL_NORMALIZE_BLESSING_BOX_V1`)
- **Scope:** All `.py`, `.ps1`, `.ts`, `.tsx`, `.rs`, `.js` files with closed-box envelopes
- **Transform:** Strip right-border chars (`╗`, `╣`, `╝`), normalize `║  ` → `║ ` (double→single space), strip trailing whitespace
- **Result:** 145 files normalized, 1422 lines changed, 0 remaining closed boxes
- **Validation:** `cargo build` ✅, `bun run compile` ✅, zero closed boxes verified

### Reference

- [docs/standards/SCRIPT_METADATA_STANDARD.md](../standards/SCRIPT_METADATA_STANDARD.md) — Universal standard (V2, canonical)
- [.github/instructions/python-scripting.instructions.md](../../.github/instructions/python-scripting.instructions.md) — PMS-v3 (Python canonical)

---

## Iteration Sequence (Recommended)

Stage 2.1 resolved (24→11 pairs). KCP integration is the new critical path.

```
┌─ COMPLETED ───────────────────────────────┐
│ Stage S.B: Box normalization        ✅     │
│ Stage 2.1: Collision resolution     ✅     │
│ STD_V2: Metadata ratification       ✅     │
└────────────────────────────────────────────┘
         │
         ▼
┌─ CURRENT ─────────────────────────────────┐
│ Stage S.0: Python #-*- tight format        │ ← QUICKEST WIN
│ KCP-0.0:  Protocol Ontology Spec           │ ← CRITICAL PATH
│ KCP-1.0:  Architecture Ratification        │
│ KCP-2.0:  Template Canonization             │
└────────────────────────────────────────────┘
         │
         ▼
┌─ PARALLEL TRACKS ─────────────────────────┐
│ [Icons]  4.0: Token scope coverage         │
│ [Icons]  2.1+: Remaining 11 pairs (3.0)    │
│ [Icons]  6.0: Product icon census          │
│ [Meta]   KCP-3.0→6.0: Per-language batch   │
└────────────────────────────────────────────┘
         │
         ▼
┌─ INTEGRATION ─────────────────────────────┐
│ KCP-7.0: Tooling refactor                  │
│ KCP-8.0: SFA equilibrium audit             │
│ KCP-9.0: Legacy purge verification         │
│ KCP-10.0: Protocol Ascension — GOLD        │
└────────────────────────────────────────────┘
         │
         ▼
┌─ FINAL ───────────────────────────────────┐
│ Stage 5.0: Color Theme Gold Standard       │
│ Stage 7.0: Product Icon Gold Standard      │
│ Stage 8.2: Visual regression baseline      │
│ Stage 9.0: Release readiness               │
└────────────────────────────────────────────┘
```

### Session Recovery

**On crash/disruption:** Read `docs/design/KCP_SESSION_CHECKPOINT.md` FIRST.
Each completed phase commits an atomic checkpoint update. The error is always the same,
the recovery point is always deterministic.

---

## Queued Signals — SFS Forge × Nightly Daemon Convergence

> **Signal Origin:** Session insight — SFS's dumpster-dive WIP system and the
> overnight daemon are structurally adjacent but operationally disconnected.
> Per SSOT canon, Sister Ferrum Scoriae governs `dumpster-dive/` as the
> Blacksmith Matriarch. The daemon already siphons ore candidates into
> `dumpster-dive/intake/overnight-siphon`. The forge pipeline
> (INTAKE → ANVIL → FURNACE → QUENCH → TEMPERED) exists but doesn't
> auto-consume daemon output.

### What Exists

| Component | Location | State |
|-----------|----------|-------|
| Overnight Daemon | `scripts/overnight_daemon.ts` | Operational — debt scoring, classification, siphon |
| Siphon Output | `dumpster-dive/intake/overnight-siphon/` | Written by daemon, not consumed |
| Forge Pipeline | `dumpster-dive/forge/PROCESS_FLOW.md` | Defined — INTAKE→ANVIL→FURNACE→QUENCH→TEMPERED |
| Ore Manifest | `dumpster-dive/ORE_MANIFEST.json` | 96 files, static ratings |
| SFS Profile | `dumpster-dive/BLACKSMITH_MATRIARCH.md` | Canon persona, domain = `dumpster-dive/` |

### The Convergence

The daemon's debt-scored candidates should flow through the forge pipeline per
the SSOT's SFS governance model. Currently the daemon writes reports and the
forge has a defined process — but there is no bridge script that:

1. Reads daemon output → classifies as ore rating (1-5 scale)
2. Routes candidates into the correct forge stage (ANVIL for analysis, FURNACE for refinement, SLAG for rejection)
3. Updates `ORE_MANIFEST.json` with daemon-derived entries
4. Produces a nightly digest that SFS "signs off on" (canon simulation)

### Priority Assessment

| Factor | Assessment |
|--------|------------|
| **Blocks KCP?** | No — fully independent lane |
| **Blocks Icon Pipeline?** | No — separate domain |
| **Dependencies** | Overnight daemon must be operational (it is) |
| **Risk if deferred** | Low — ore accumulates but doesn't rot |
| **SSOT alignment** | High — directly implements SFS's declared domain authority |
| **Estimated phases** | 2-3 (bridge script + manifest update + digest format) |

### Disposition

**QUEUED** — Execute after S.0 + KCP-0.0→KCP-2.0 template canonization.
Slot into the plan as **Stage D.0** (Daemon-Forge Bridge) when the active
lane reaches a natural pause point. Does NOT disrupt the critical path.

```
Priority Stack (current):
  1. S.0   — Python #-*- tight format      ← ACTIVE LANE
  2. KCP-0.0 → KCP-2.0 — Protocol specs    ← CRITICAL PATH
  3. D.0   — Daemon-Forge Bridge            ← QUEUED HERE
  4. 4.0   — Token scope coverage
  5. S.3   — Rust @SID tags
  6. 6.0   — Product icon census
```

---

## Codex Lane (Supplementary Context)

Codex sessions have contributed:
- WPTG WIP HTML benchmark (3 variants: original, transmutation, chthonic-archive) — gitignored
- Poe API lane scripts (`poe_lane.py`, `poe_sdk_lane.py`, `poe_transport_audit.py`)
- Cross-lane skill parity enforcement (Codex=24, Claude=23 skills, 20 shared)
- Art Cop iterative mode concept (screenshot → analysis → refinement loop)

Codex's structural enforcement role supports the WPTG by validating that:
- Icon mappings in `chthonic-file-icon-theme.json` match actual SVG files
- Theme JSON structure is schema-compliant
- Build output is deterministic

---

## Cross-References

| File | Relevance |
|------|-----------|
| [WET_PAPER_TO_GOLD_METHODOLOGY.md](../../WET_PAPER_TO_GOLD_METHODOLOGY.md) | WPTG foundational axioms |
| [.claude/skills/sfa/SKILL.md](../../.claude/skills/sfa/SKILL.md) | SFA engine specification |
| [.claude/skills/theme-system/SKILL.md](../../.claude/skills/theme-system/SKILL.md) | Theme design automation skill |
| [scripts/sfa_cross_reference.py](../../scripts/sfa_cross_reference.py) | SFA engine implementation |
| [extensions/chthonic-archive/themes/](../../extensions/chthonic-archive/themes/) | Theme files (color, file icon, product icon) |
| [docs/design/KCP_SESSION_CHECKPOINT.md](KCP_SESSION_CHECKPOINT.md) | Crash-resilient KCP progress tracker |
| [claude-codex-gemini/ANKH_EGYPTOLOGY_SOUTH_AMERICAN/ANKH_UNIFYING_REPOSITORY_METADATA_STANDARDS.md](../../claude-codex-gemini/ANKH_EGYPTOLOGY_SOUTH_AMERICAN/ANKH_UNIFYING_REPOSITORY_METADATA_STANDARDS.md) | Gemini research: Khipu-Cartouche Protocol |
