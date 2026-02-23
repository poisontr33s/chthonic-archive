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
| **2.1** | Motif Distinctiveness | All pairs below 0.85 similarity | ❌ **BLOCKED**: 24 collision pairs above threshold |
| **3.0** | Gold Standard | All gates pass, ready for packaging | ❌ Blocked by 2.1 |

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
| **4.0** | Token Scope Coverage Audit | Compare 83 token scopes against VS Code's full TextMate grammar universe. Identify syntax contexts with no assigned color. | ⬜ Not started |
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
| **6.0** | Product Icon Census | Map all VS Code product icon IDs in active use (activity bar, status bar, editor widgets, debug, SCM, testing, etc.) against current 7. | ⬜ Not started |
| **6.1** | Priority Expansion | Design and implement icons for highest-visibility product icon slots (activity bar, editor actions, debug controls). | ⬜ Not started |
| **6.2** | Product Palette + Motif Audit | Verify product SVGs use SFS palette and maintain Egypto-Andean motif vocabulary. | ⬜ Not started |
| **7.0** | Product Icon Gold Standard | All high-visibility slots covered. Palette and motif compliant. Visual coherence with file icons. | ⬜ Not started |

### Pipeline Scripts Needed (Product Pillar)

| Script | Purpose | Exists? |
|--------|---------|---------|
| `product_icon_census.py` | Map VS Code product icon IDs vs coverage | ❌ Create |
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

Header/metadata conventions across all authored file types. Governed by `STD_SCRIPT_METADATA_V2` (canonical) and PMS-v3 (Python-specific).

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
| **S.0** | Python Header Canon | Fix 92 scripts with spaced `# -*-` to tight `#-*-` per PMS-v3. | ⬜ Batch tooling target |
| **S.1** | @SID Expansion | Raise @SID coverage from 19% to ≥60% across all languages. | ⬜ Incremental |
| **S.2** | TypeScript Shebang Sweep | Add `#!/usr/bin/env bun` to CLI-oriented `.ts` scripts missing it. | ⬜ Not started |
| **S.3** | Rust @SID Tags | Add `@SID` to all 15 Rust files within their existing Blessing envelopes. | ⬜ Not started |

### Reference

- [docs/standards/SCRIPT_METADATA_STANDARD.md](../standards/SCRIPT_METADATA_STANDARD.md) — Universal standard (V2, canonical)
- [.github/instructions/python-scripting.instructions.md](../../.github/instructions/python-scripting.instructions.md) — PMS-v3 (Python canonical)

---

## Iteration Sequence (Recommended)

The 24 collisions in Stage 2.1 are the **current critical path blocker**. Everything else is downstream.

```
┌─ CURRENT ─────────────────────────────────┐
│ Stage 2.0: Run optimizer gate formally     │
│ Stage 2.1: Resolve 24 collision pairs      │ ← CRITICAL PATH
│ Stage 3.0: Icon Gold Standard gate         │
└────────────────────────────────────────────┘
         │
         ▼
┌─ NEXT ────────────────────────────────────┐
│ Stage 4.0: Token scope coverage audit      │
│ Stage 4.1: Semantic token expansion        │
│ Stage 4.2: Workbench key completeness      │
│ Stage 4.3: Palette discipline audit        │
│ Stage 5.0: Color Theme Gold Standard       │
└────────────────────────────────────────────┘
         │
         ▼
┌─ THEN ────────────────────────────────────┐
│ Stage 6.0: Product icon census             │
│ Stage 6.1: Priority expansion              │
│ Stage 6.2: Product palette audit           │
│ Stage 7.0: Product Icon Gold Standard      │
└────────────────────────────────────────────┘
         │
         ▼
┌─ FINAL ───────────────────────────────────┐
│ Stage 8.2: Visual regression baseline      │
│ Stage 9.0: Release readiness               │
└────────────────────────────────────────────┘
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
