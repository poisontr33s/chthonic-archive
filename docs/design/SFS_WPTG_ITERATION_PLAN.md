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

## Dry Lane Contract (Scripts + Skills)

When the SFS lane audits its supporting automation in `scripts/` and
`.codex/skills/`, and execution would intersect live extension work, the audit
stays in **dry lane** mode.

Dry lane obligations:
- inspect script/skill contracts statically before running anything
- classify each surface as `preserve`, `refactor`, `re-scope`, or `demote`
- treat redirect/stashed skills as provenance artifacts, not active runtime guidance
- reserve salvage/embalming for destructive or provenance-critical edits only
- do not generate reports, refresh manifests, or churn mailbox artifacts during overlapping lanes

Authoritative method: [WET_PAPER_TO_GOLD_METHODOLOGY.md](../../WET_PAPER_TO_GOLD_METHODOLOGY.md)

---

## Three Pillars

| Pillar | Artifact | Current State |
|--------|----------|---------------|
| **Color Theme** | `chthonic-geology-color-theme.json` | 669 workbench, 149 tokens, 57 semantic |
| **File/Folder Icons** | `chthonic-file-icon-theme.json` + 96 SVGs | 76 defs, 91 ext, 34 filenames, 33 langs, 35 folders. Gold 10.10: 26 closed folder chambers at `fill-opacity="0.55"` |
| **Product Icons** | `chthonic-product-icon-theme.json` + 43 SVGs | 46 overrides (43 glyphs), Tier 1: 39/39 (100%), overall: 46/535 (8.6%) |

---

## SFS Palette (Forge Colors)

| Token | Hex | Role |
|-------|-----|------|
| bg | `#050505` | Void substrate |
| stele | `#0A0A0A` | Panel background |
| stele-body | `#2A2724` | SVG icon body fill (stele tablets, pylon chambers). Lifted from `stele` for contrast against dark surfaces. |
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
| **1.1** | WCAG / Contrast Audit | 76/76 pass, plus 49/49 workbench secondary-lane pairs ≥ 4.5:1 across all 4 themes | ✅ Pass |
| **1.2** | Palette Coherence | 76/76 on-palette (0 off-palette colors) | ✅ Pass |

### Completed Stages (cont.)

| Stage | Name | Gate | Status |
|-------|------|------|--------|
| **2.0** | Structural Refinement | SVGO / path optimization / file size | ✅ Pass — 103 SVGs, 10 optimized (364B saved) |
| **2.1** | Motif Distinctiveness | All pairs below 0.85 similarity | ✅ 0 collisions — 3 rounds: 11→6→3→0 |
| **3.0** | Gold Standard | All gates pass, ready for packaging | ✅ GOLD — 96/96 structural, 96/96 WCAG, 96/96 palette, 0 collisions |
| **1.3** | Chamber Transparency | Closed folder SVGs have `fill-opacity="0.55"` inner chamber | ✅ 26/26 pass — audit enforced via `icon_svg_audit.py` Stage 1.3 |

### Canonical Execution Bridge

Icon work in this pillar is governed by `docs/design/ANKH_ICON_GRAMMAR.md`.
That document bridges the ANKH research corpus to the actual SVG lane and is
the prerequisite for:

- file and folder silhouette decisions
- folder open/closed state behavior
- palette inheritance across new domain families
- descendant-theme reuse for every later MILF/Sub-MILF theme

If a proposed icon batch cannot explain itself against that bridge document, it
is not ready for WPTG advancement.

### Stage 2.1 — Collision Resolution Record

Original: 24 pairs reduced to 11 (commit `7a544db0`), then resolved to 0 across 3 rounds.

**Round 1 — Color Redistribution** (7 recolors):
- file-go: patina→verdigris (`#7AAAB2`→`#8CB87A`)
- file-proto: patina→copper (`#7AAAB2`→`#D4714E`)
- file-font: rose-clay→amber (`#D4907A`→`#D7B562`)
- file-cpp: rose-clay→kiln (`#D4907A`→`#E05545`)
- file-img: kiln→gold (`#E05545`→`#F4C430`)
- file-ps1: kiln→sandstone (`#E05545`→`#B9A37A`)
- file-rst: sandstone→amber (`#B9A37A`→`#D7B562`)
- Result: 11→6 pairs (new collisions from populated color groups)

**Round 2 — Element Type Diversification** (5 ellipse additions):
- Added `<ellipse>` to: file-go, file-rb, file-img, file-ps1, file-proto
- Result: 6→3 pairs (cfg↔go, img↔lock, default↔ps1 — partners already had ellipses)

**Round 3 — Unique Element Injection** (3 polygon+polyline additions):
- Added `<polygon>` + `<polyline>` to: file-go, file-img, file-ps1
- These element types are unique across all 103 SVGs, diversifying type Jaccard to ~0.5
- Result: 3→0 pairs ✅

**Final Color Distribution** (post-resolution):

| Color | Hex | Count | Icons |
|-------|-----|-------|-------|
| amber | `#D7B562` | 8 | c, csv, env, font, js, jsx, rst, sql |
| copper | `#D4714E` | 7 | bat, docker, git, html, map, proto, py |
| sandstone | `#B9A37A` | 6 | default, json, md, ps1, rst, toml |
| gold | `#F4C430` | 6 | cmake, img, lock, rs, rust-toml, tsx |
| verdigris | `#8CB87A` | 5 | audio, cfg, claude, go, sh |
| rose-clay | `#D4907A` | 4 | css, svg, wasm, xml |
| kiln | `#E05545` | 4 | cpp, h, rb, txt |
| patina | `#7AAAB2` | 3 | copilot, ts, yml |
| bg | `#050505` | 1 | html (dual) |

### Pipeline Scripts (Icon Pillar)

| Script | Lines | WPTG Stage | Purpose |
|--------|-------|------------|---------|
| [icon_filetype_census.py](../../scripts/icon_filetype_census.py) | 415 | 0.0 / 0.1 | Workspace filetype census + coverage gap mapping |
| [icon_svg_audit.py](../../scripts/icon_svg_audit.py) | ~430 | 1.0 / 1.1 / 1.2 / 1.3 | Structural, WCAG, palette, chamber transparency validation |
| [icon_svg_optimizer.py](../../scripts/icon_svg_optimizer.py) | 228 | 2.0 | SVG path optimization (SVGO equiv) |
| [icon_distinctiveness_audit.py](../../scripts/icon_distinctiveness_audit.py) | 293 | 2.1 | Motif similarity / collision detection |
| [icon_scaffold_contract_audit.py](../../scripts/icon_scaffold_contract_audit.py) | ~430 | (cross-cutting) | Scaffold matrix: runtime IDs, unique glyphs, aliases, consumers, spillover |
| [sfa_cross_reference.py](../../scripts/sfa_cross_reference.py) | 800 | (cross-cutting) | 50/50 balance engine, motif assignment |
| [link_audit.py](../../scripts/link_audit.py) | ~408 | (cross-cutting) | Markdown `[label](path)` validation + auto-fix; collision index |
| [theme_artcop.py](../../scripts/theme_artcop.py) | 245 | (visual QA) | Screenshot-based quality assessment |
| [vscode-art-cop.ts](../../scripts/vscode-art-cop.ts) | — | (visual QA) | Screenshot automation for Art Cop |

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

### Pipeline Scripts (Color Pillar)

| Script | Purpose | Exists? |
|--------|---------|---------|
| [theme_token_coverage.py](../../scripts/theme_token_coverage.py) | Audit token scope vs full TextMate grammar | ✅ Created |
| `theme_workbench_completeness.py` | Diff workbench keys vs VS Code schema | ❌ Create |
| `theme_palette_discipline.py` | Trace all hex values to palette derivations | ❌ Create |
| [theme_parity.py](../../scripts/theme_parity.py) | Cross-theme comparison (existing) | ✅ 141L |
| [theme_contrast_audit.py](../../scripts/theme_contrast_audit.py) | Workbench contrast gate: 3.0 UI floor + 4.5 secondary-text floor | ✅ Expanded |

---

## Pillar III — Product Icons (Stages 6.0→7.0)

46 product icon overrides (6 original + 39 Tier 1 + 1 remap). Tier 1 coverage: 100%. Font: 43-glyph WOFF (2.1 KB).

### Planned Stages

| Stage | Name | Description | Status |
|-------|------|-------------|--------|
| **6.0** | Product Icon Census | Map all VS Code product icon IDs in active use (activity bar, status bar, editor widgets, debug, SCM, testing, etc.) against current 7. | ✅ 6/535 (1.1%) — 39 Tier 1 gaps identified, `hammer` remapped → `tools` (valid codicon EB6D) |
| **6.1** | Priority Expansion | Design and implement icons for highest-visibility product icon slots (activity bar, editor actions, debug controls). | ✅ 39/39 Tier 1 — 36 new SVGs, 43-glyph WOFF, 46 codicon mappings. Signature: scarab (debug), Eye of Horus (copilot). |
| **6.2** | Product Palette + Motif Audit | Verify product SVGs use SFS palette and maintain Egypto-Andean motif vocabulary. | ✅ BCE Redesign — 28 SVGs rewritten with ANKH motif bank provenance. Modern motifs eliminated. Papyrus scroll (files), Wedjat eye (search), ashlar masonry (extensions), kheper scarab (debug), khopesh (debug-alt), Djed pillar (remote), broken ankh (error), pyramid+eye (warning), obelisk (info), Inti sun disc (settings), Nemes headdress (account), ouroboros (sync), Nile delta (git-branch×4), sistrum (bell×4), cartouche tablets (comment), pigment mortar (paintcan), Ka arms (pulse), ox-hide shield (shield), sedimentary strata (layers). Font rebuilt: 43 glyphs, 2.1 KB. E2E 3/3 PASS. |
| **7.0** | Product Icon Gold Standard | All high-visibility slots covered. Palette and motif compliant. Visual coherence with file icons. | ⬜ Not started |

### Runtime Icon ID Contract

A source motif name (e.g., `adze-tupu`) ≠ a runtime icon ID (e.g., `tools`). Product icon themes can **only** override valid codicon IDs.

**Two legal paths for non-codicon names:**
1. **Remap** archaeology art → existing codicon ID (workbench-wide scope)
2. **Contribute** custom icon via `contributes.icons` (extension-local scope only)

**Required 4-field model for every product icon:**

| Field | Description |
|-------|-------------|
| `runtime_id` | Valid codicon or contributed custom icon ID |
| `source_svg` | Actual SVG file |
| `provenance_name` | Archaeology name from research |
| `consumer_scope` | `product-icon-theme` or `extension-local` |

Question gate for future icon passes: "Is this a real codicon ID?" If no → remap or contribute. Never assume a name exists.

### Pipeline Scripts Needed (Product Pillar)

| Script | Purpose | Exists? |
|--------|---------|---------|
| [product_icon_census.py](../../scripts/product_icon_census.py) | Map VS Code product icon IDs vs coverage | ✅ Created |
| [icon_scaffold_contract_audit.py](../../scripts/icon_scaffold_contract_audit.py) | Classify `46` runtime IDs vs `43` unique glyphs vs `3` aliases; record consumers and dormant-valid coverage | ✅ Created |
| Product SVG audit | Reuse [icon_svg_audit.py](../../scripts/icon_svg_audit.py) (extend to product/ path) | ✅ Extend |

---

## Pillar IV — Extension Integration (Stages 8.0→9.0)

The extension manifest, commands, tree view, and build pipeline must be cohesive.

### Two Development Loops

| Loop | Command | When to Use | What Changes |
|------|---------|-------------|--------------|
| **Dev Host** | `bun run insiders:run` | Fast iteration on TS source, commands, UI. Opens a **separate** VS Code window reading directly from workspace source. | TypeScript, commands, webview panels |
| **VSIX Repackage** | Package → Install → Reload | Final verification in your **real workspace**. The installed extension is a snapshot — it does not track source. | SVGs, theme JSONs, icon-theme JSON, product-icon font, any visual change |

**Rule of thumb:** If you changed anything under `themes/` or `icons/`, you must repackage. If you only changed `.ts` source, the dev host is faster.

### VSIX Repackage Loop (Canonical Build→Verify Cycle)

Edits to SVGs, theme JSONs, or extension source in `extensions/chthonic-archive/`
do **not** appear in VS Code until the extension is repackaged and reinstalled.
The installed extension lives at `%USERPROFILE%\.vscode-insiders\extensions\chthonic-archive.chthonic-archive-<version>\`
and is a **snapshot** — it does not track workspace source.

```powershell
# 0. Link audit — resolve broken refs from any file gen/move/rename
uv run scripts/link_audit.py check docs/design/ANKH_THEME_REFERENCE.md --fix
uv run scripts/link_audit.py check docs/design/ANKH_ICON_GRAMMAR.md --fix
uv run scripts/link_audit.py check docs/design/SFS_WPTG_ITERATION_PLAN.md --fix

# 1. Package (runs compile via prepublish automatically)
cd extensions/chthonic-archive
bunx @vscode/vsce package --pre-release --no-dependencies --out chthonic-archive-insiders.vsix --skip-license

# 2. Install
code-insiders --install-extension chthonic-archive-insiders.vsix --force

# 3. Reload VS Code Insiders (Ctrl+Shift+P → "Developer: Reload Window")
```

**Step 0 rationale:** When files are generated, replaced, or moved during a WPTG stage, cross-references in the three canon design docs can break silently. `link_audit.py check <file> --fix` resolves fixable broken paths in-place (unique basename match → auto-rewrite) and flags ambiguous or missing targets. Run it before packaging so the VSIX ships with clean docs.

Shortcut: `bun run insiders:package` runs step 1 (requires interactive `y` for missing LICENSE unless `--skip-license` is passed to vsce).

**Verification after install:**
- `code-insiders --list-extensions | Select-String chthonic` → confirms installed
- Check `%USERPROFILE%\.vscode-insiders\extensions\chthonic-archive.chthonic-archive-<version>\themes\icons\` → SVGs match source
- Settings must have `workbench.iconTheme: chthonic-file-icons` and `workbench.productIconTheme: chthonic-product-icons`

### Planned Stages

| Stage | Name | Description | Status |
|-------|------|-------------|--------|
| **8.0** | Manifest Validation | Verify `package.json` contributes (themes, icons, commands) are wired correctly. All theme files referenced. | ✅ Done (commit 1e3a880e) |
| **8.1** | Build Pipeline Health | `bun run compile` succeeds. `dist/extension.js` < 200KB. No dead imports. | ✅ Current: 101.1KB |
| **8.2** | Visual Regression Baseline | Capture Art Cop screenshots of SFS in active workspace. Store as baseline for future regression comparison. | ⬜ Not started |
| **9.0** | Release Readiness | Marketplace metadata (README, CHANGELOG, screenshots, gallery images) prepared. Version bumped. | ⬜ Not started |

---

## Gold 10.10 — Cross-Theme Icon Modulation (Cross-Pillar Gate)

**Binds:** Pillar I (Icons) + Pillar II (Color Theme) + Pillar IV (Integration)

**Definition:** "If SVG icon backgrounds can be theme-modulated, that is the gold 10.10 achievement — the highest WPTG milestone for theme integration." — [ANKH_THEME_REFERENCE.md](ANKH_THEME_REFERENCE.md)

### Architecture Trace

```
Color Theme (user selects 1 of 4)
  → chthonic-{geology|mandala|rogbiv|decorator}-color-theme.json
  → sidebar.background, editor.background, etc. (DIFFERENT per theme)
      ↓
File Icon Theme (shared — ONE icon theme across all 4 color themes)
  → chthonic-file-icon-theme.json → 100 iconDefinitions (iconPath only)
      ↓
96 SVGs — stele (files) + pylon (folders), opaque #2A2724 body fills
  → VS Code renders as <img> / CSS background-image
  → NO CSS variable inheritance, NO currentColor cascade for SVG iconPaths
```

### VS Code API Constraints

The official [file icon theme contract](https://code.visualstudio.com/api/extension-guides/file-icon-theme) provides:

| Feature | Scope | Usable? |
|---------|-------|---------|
| `iconPath` | SVG/PNG path per definition | ✅ In use |
| `fontCharacter` + `fontColor` | Font-based icons only | ❌ N/A for SVGs |
| `light` | Binary override for light themes | ❌ All 4 themes are dark |
| `highContrast` | Binary override for high-contrast | ❌ Not relevant |
| Per-color-theme overrides | Not in API | ❌ Does not exist |

**Conclusion:** VS Code provides no per-dark-theme icon variation mechanism for SVG-based file icons. Product icons (font-based) already inherit theme color automatically via `currentColor`.

### Validated Mechanism: Inner Chamber Transparency

SVGs rendered as images DO support alpha transparency. Background composites through.

**Strategy:** Apply `fill-opacity` only to **inner chamber planes** in closed folder pylons. Outer pylon walls and file stele bodies remain opaque. This preserves structural mass while allowing theme background to bleed through the portal.

**SVG Anatomy (175 `#2A2724` fills across 96 SVGs):**

| Plane | Count | Treatment |
|-------|-------|-----------|
| File stele body | 44 (1 per file) | **Opaque** — single monolithic fill, no separable inner plane |
| Folder pylon walls | 52 (2 per folder) | **Opaque** — structural mass, must read as stone |
| Folder inner chamber | 26 (1 per closed folder) | **`fill-opacity="0.55"`** — portal reads as recessed depth, theme bleeds through |
| Folder open variants | 0 | Already use accent-color opacity fills (`opacity="0.15"`) |

### Contrast Validation

**Outer wall (opaque `#2A2724`) vs sidebar backgrounds:**

| Theme | Sidebar BG | Contrast |
|-------|------------|----------|
| Geology | `#100D0A` | 1.305:1 |
| Mandala | `#171210` | 1.251:1 |
| Decorator | `#141110` | 1.266:1 |
| ROGBIV | `#100E18` | 1.288:1 |

**Inner chamber composited (alpha=0.55) — accent motif legibility IMPROVES:**

| Accent | On Opaque Chamber | On Translucent Chamber | Delta |
|--------|-------------------|------------------------|-------|
| Gold (`#F4C430`) | 9.04:1 | 10.1–10.4:1 | +12% |
| Copper (`#D4714E`) | 4.44:1 | 5.0–5.1:1 | +12% |
| Patina (`#7AAAB2`) | 5.81:1 | 6.5–6.7:1 | +12% |
| Sandstone (`#B9A37A`) | 6.07:1 | 6.8–7.0:1 | +12% |

**Wall-to-chamber depth contrast:** ~1.12–1.15:1 (subtle dimensional depth, not a legibility target)

### A/B Phase (Current)

Applied `fill-opacity="0.55"` to inner chamber rects in 3 canonical closed folders:

| Icon | Status | Chamber Element |
|------|--------|-----------------|
| `folder-default.svg` | ✅ Applied | `<rect x="6" y="6" width="4" height="6.5">` |
| `folder-temple.svg` | ✅ Applied | `<rect x="5" y="5" width="6" height="8">` |
| `folder-session-archives.svg` | ✅ Applied | `<rect x="5" y="5" width="6" height="8">` |
| `file-default.svg` | — | No separable inner plane (single stele body) |

Pending visual validation before rollout to remaining 23 closed folders.

### Rollout Gate

| Step | Description | Status |
|------|-------------|--------|
| A/B-1 | Apply to 3 canonical folders | ✅ Done |
| A/B-2 | Visual inspection across all 4 themes | ✅ Done |
| A/B-3 | Roll out to remaining 23 closed folders | ✅ Done — 26/26 verified |
| A/B-4 | Audit pipeline enforcement (Stage 1.3) | ✅ Done — `icon_svg_audit.py` validates chamber opacity |
| **10.10** | **Gold** | ✅ GOLD — All 26 closed folder chambers translucent, 4 themes auto-tint via alpha compositing. File steles opaque. Audit enforced. |

### What 10.10 Does NOT Cover

- File stele body modulation (single monolithic fill — would require adding a new inner rect to all 44 SVGs)
- Product icon modulation (already handled — font-based icons inherit `currentColor` from workbench theme)
- Light theme variants (all 4 themes are dark; `light` override exists in API but is unused)

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

Pillar I complete — Icon Pipeline at Gold Standard. KCP integration is the critical path.

```
┌─ COMPLETED ───────────────────────────────┐
│ Stage S.B: Box normalization        ✅     │
│ Stage S.0: Python #-*- tight format ✅     │
│ STD_V2: Metadata ratification       ✅     │
│ KCP-0.0→KCP-2.0: Protocol specs    ✅     │
│ Pillar I: Icon Pipeline GOLD        ✅     │
│   0.0→1.2: Baseline + validation           │
│   2.0: SVG optimization (103 SVGs)         │
│   2.1: Collision resolution (3 rounds)     │
│   3.0: Gold Standard achieved              │
└────────────────────────────────────────────┘
         │
         ▼
┌─ CURRENT / PARALLEL ──────────────────────┐
│ [Color]  4.1: Semantic token expansion     │
│ [Color]  4.2: Workbench key completeness   │
│ [Color]  4.3: Palette discipline audit     │
│ [Prod]   6.1: Product icon expansion       │
│ [Meta]   KCP-3.0→6.0: Per-language batch   │
└────────────────────────────────────────────┘
         │
         ▼
┌─ INTEGRATION ─────────────────────────────┐
│ Stage 5.0: Color Theme Gold Standard       │
│ Stage 7.0: Product Icon Gold Standard      │
│ KCP-7.0→10.0: Tooling + Ascension          │
└────────────────────────────────────────────┘
         │
         ▼
┌─ FINAL ───────────────────────────────────┐
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
  1. KCP-3.0 — Python consolidation         ← CRITICAL PATH
  2. 4.1–4.3 — Color theme stages           ← PARALLEL
  3. 6.1   — Product icon expansion          ← PARALLEL
  4. D.0   — Daemon-Forge Bridge            ← QUEUED
  5. S.3   — Rust @SID tags
  6. KCP-4.0→6.0 — TS/PS1/Rust metadata
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

### Sibling Design Docs

| File | Relevance |
|------|-----------|
| [ANKH_ICON_GRAMMAR.md](ANKH_ICON_GRAMMAR.md) | Canon icon execution bridge — 7-gate benchmark, state grammar, domain folder canon |
| [ANKH_THEME_REFERENCE.md](ANKH_THEME_REFERENCE.md) | Global SVG policy, SFS palette baseline, theme creation checklist, tier hierarchy |
| [SFS_SLABSTONE_BASELINE.md](SFS_SLABSTONE_BASELINE.md) | Generated reproducibility anchor linking the plan to live SFS/theme/icon assets |
| [KCP_SESSION_CHECKPOINT.md](KCP_SESSION_CHECKPOINT.md) | Crash-resilient KCP progress tracker |

### Research Sources

| File | Relevance |
|------|-----------|
| [WET_PAPER_TO_GOLD_METHODOLOGY.md (.)](../../WET_PAPER_TO_GOLD_METHODOLOGY.md) | WPTG foundational axioms plus the dry-lane contract for script/skill dumpster-diving |
| [ETS_ARCHAEOLOGICAL_TOOLFORM_BASELINE.md](../reference/ETS_ARCHAEOLOGICAL_TOOLFORM_BASELINE.md) | Codex ET-S research: BCE toolform archaeology for `tools` glyph (adze-tupu hybrid, Direction B) |
| [ANKH_README.md (ankh)](../frameworks/ankh/ANKH_README.md) | 50/50 Egyptological × Andean abstraction |
| [SFA_CROSS_REFERENCE_SCAN.md](../../claude/mailbox/SFA_CROSS_REFERENCE_SCAN.md) | Motif balance audit, motif-to-palette lineage |
| [ANKH_UNIFYING_REPOSITORY_METADATA_STANDARDS.md](../../claude-codex-gemini/ANKH_EGYPTOLOGY_SOUTH_AMERICAN/ANKH_UNIFYING_REPOSITORY_METADATA_STANDARDS.md) | Gemini research: Khipu-Cartouche Protocol |

### Skills

| File | Relevance |
|------|-----------|
| [.claude/skills/sfa/SKILL.md](../../.claude/skills/sfa/SKILL.md) | SFA engine specification |
| [.claude/skills/theme-system/SKILL.md](../../.claude/skills/theme-system/SKILL.md) | Theme design automation skill |

### Theme / Icon / Language Artifacts

| File | Pillar | Purpose |
|------|--------|--------|
| [package.json (chthonic-archive)](../../extensions/chthonic-archive/package.json) | Integration | Extension manifest — themes, icons, languages, commands |
| [chthonic-geology-color-theme.json](../../extensions/chthonic-archive/themes/chthonic-geology-color-theme.json) | Color | SFS color theme (669 workbench / 83 token / 57 semantic) |
| [chthonic-file-icon-theme.json](../../extensions/chthonic-archive/themes/chthonic-file-icon-theme.json) | Icon | File/folder icon defs → SVGs |
| [chthonic-product-icon-theme.json](../../extensions/chthonic-archive/themes/chthonic-product-icon-theme.json) | Icon | Product icon font definitions |
| [chthonic-mandala-color-theme.json (themes)](../../extensions/chthonic-archive/themes/chthonic-mandala-color-theme.json) | Color | Decorator theme (Flesh & Earth) |
| [chthonic-rogbiv-color-theme.json (themes)](../../extensions/chthonic-archive/themes/chthonic-rogbiv-color-theme.json) | Color | Spectra Chroma ROGBIV theme |
| [chthonic-decorator-color-theme.json](../../extensions/chthonic-archive/themes/chthonic-decorator-color-theme.json) | Color | The Decorator theme |
| [language-configuration-glsl.json](../../extensions/chthonic-archive/language-configuration-glsl.json) | Language | GLSL language config (Vulkan SDK backing) |
| [language-configuration-toml.json](../../extensions/chthonic-archive/language-configuration-toml.json) | Language | TOML language config (Cargo/Python/Bun/Go backing) |
| [glsl.tmLanguage.json](../../extensions/chthonic-archive/syntaxes/glsl.tmLanguage.json) | Language | GLSL TextMate grammar |
| [toml.tmLanguage.json](../../extensions/chthonic-archive/syntaxes/toml.tmLanguage.json) | Language | TOML TextMate grammar |

### Pipeline Scripts

| Script | Stage | Purpose |
|--------|-------|--------|
| [icon_filetype_census.py](../../scripts/icon_filetype_census.py) | 0.0–0.1 | Workspace filetype census + coverage gap mapping |
| [icon_svg_audit.py](../../scripts/icon_svg_audit.py) | 1.0–1.2 | Structural, WCAG, palette validation |
| [icon_svg_optimizer.py](../../scripts/icon_svg_optimizer.py) | 2.0 | SVG path optimization |
| [icon_distinctiveness_audit.py](../../scripts/icon_distinctiveness_audit.py) | 2.1 | Motif similarity / collision detection |
| [icon_surface_map.py](../../scripts/icon_surface_map.py) | (cross-cutting) | Deterministic surface mapping |
| [icon_scaffold_contract_audit.py](../../scripts/icon_scaffold_contract_audit.py) | (cross-cutting) | Runtime IDs vs unique glyphs vs aliases; authored substrate / spillover matrix |
| [sfa_cross_reference.py](../../scripts/sfa_cross_reference.py) | (cross-cutting) | 50/50 balance engine, motif assignment |
| [product_icon_census.py](../../scripts/product_icon_census.py) | 6.0 | Product icon ID coverage mapping |
| [theme_token_coverage.py](../../scripts/theme_token_coverage.py) | 4.0 | Token scope vs TextMate grammar audit |
| [theme_parity.py](../../scripts/theme_parity.py) | (cross-cutting) | Cross-theme comparison |
| [theme_artcop.py](../../scripts/theme_artcop.py) | (visual QA) | Screenshot-based quality assessment |
| [vscode-art-cop.ts](../../scripts/vscode-art-cop.ts) | (visual QA) | Screenshot automation |
| [sfs_slabstone_baseline.py](../../scripts/sfs_slabstone_baseline.py) | (cross-cutting) | Generated anchor report for canon-doc linkage and live SFS asset reproducibility |
| [link_audit.py](../../scripts/link_audit.py) | (cross-cutting) | Markdown link validation + auto-fix; runs as Step 0 of VSIX Repackage Loop |
| [normalize_blessing_box.py](../../scripts/normalize_blessing_box.py) | S.B | Blessing envelope normalization |
| [vscode_settings_live_audit.py](../../scripts/vscode_settings_live_audit.py) | (validation) | Settings/language drift detection |

### Validation / E2E

| File | Purpose |
|------|--------|
| [e2e-extension-host.ts](../../extensions/chthonic-archive/scripts/e2e-extension-host.ts) | Extension host smoke runner (3/3 gate) |
| [e2e-smoke-runner.cjs](../../extensions/chthonic-archive/scripts/e2e-smoke-runner.cjs) | Smoke test — registration + command execution |
| [SETTINGS_LIVE_AUDIT.md](../../.vscode/SETTINGS_LIVE_AUDIT.md) | Generated audit report (strict pass/fail) |
| [SFS_SLABSTONE_BASELINE.md](SFS_SLABSTONE_BASELINE.md) | Generated anchor report for canon linkage, asset presence, and reproduction commands |

### Standards

| File | Relevance |
|------|-----------|
| [SCRIPT_METADATA_STANDARD.md](../standards/SCRIPT_METADATA_STANDARD.md) | Universal metadata standard V2 |
| [python-scripting.instructions.md](../../.github/instructions/python-scripting.instructions.md) | PMS-v3 Python canonical |
