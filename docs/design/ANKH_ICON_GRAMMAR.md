---
sid: DOC_ANKH_ICON_GRAMMAR_V1
title: "ANKH Icon Grammar - Research Bridge for SFS and Descendant Themes"
type: methodology
status: active
priority: high
description: >
  Canonical bridge from the ANKH research corpus to VS Code icon execution.
  Defines silhouette grammar, palette inheritance, motif assignment, state
  behavior, and benchmark gates for file, folder, and product icon work.
created: 2026-02-28
authors:
  - Codex
applies_to:
  - extensions/chthonic-archive/themes/icons/
  - extensions/chthonic-archive/themes/chthonic-file-icon-theme.json
  - extensions/chthonic-archive/themes/chthonic-product-icon-theme.json
tags:
  - ankh
  - icon-grammar
  - sfs
  - wptg
  - design-system
---

<!--
@SID:           DOC_ANKH_ICON_GRAMMAR_V1
@Type:          Methodology
@Context:       ANKH icon execution bridge / SFS baseline / descendant-theme inheritance
-->

# ANKH Icon Grammar

## Why This Exists

The research corpus already establishes the 50/50 Egyptological x Andean
abstraction, the SFS 12-color baseline, and the WPTG icon-quality gates.
What was missing was the bridge between those research sources and the actual
16px SVG work inside the extension.

This document closes that gap.

It formalizes:

- what shape family each icon lane belongs to
- how SFS acts as the baseline for every later MILF/Sub-MILF theme
- which motifs and palette tokens belong to the new folder families
- what counts as a valid open/closed state
- what fails the lane outright

Without this bridge, icon work drifts into recolored prototypes, generic modern
glyphs, or audits that have to reconstruct the lineage from comments and dumps.

---

## Authority Chain

| Source | What It Governs |
|--------|-----------------|
| `docs/frameworks/ankh/ANKH_README.md` | 50/50 Egyptological x Andean abstraction |
| `docs/design/ANKH_THEME_REFERENCE.md` | Global SVG policy, color modulation doctrine, SFS palette baseline |
| `docs/design/SFS_WPTG_ITERATION_PLAN.md` | WPTG stage gates, icon-pipeline quality requirements |
| `claude/mailbox/SFA_CROSS_REFERENCE_SCAN.md` | Motif bank, axis balance, motif-to-palette lineage |
| `extensions/chthonic-archive/themes/icons/file-default.svg` | Canon file silhouette exemplar |
| `extensions/chthonic-archive/themes/icons/folder-temple.svg` | Canon folder silhouette exemplar |
| `extensions/chthonic-archive/themes/icons/folder-src.svg` | Early domain-specific folder exemplar |
| `extensions/chthonic-archive/themes/icons/folder-github.svg` | Early domain-specific folder exemplar |
| `extensions/chthonic-archive/themes/icons/folder-scripts.svg` | Early domain-specific folder exemplar |

This document is the execution bridge between those sources and every later icon
decision. If a future icon proposal conflicts with this file, this file is the
working contract until the research chain itself is deliberately revised.

---

## Baseline Doctrine

### SFS Is The First Full Theme Baseline

Sister Ferrum Scoriae is the first complete theme-extension baseline for the
theme / icons / product-icons loop.

That means later MILF/Sub-MILF themes inherit:

- the icon grammar
- the motif bank
- the silhouette family
- the benchmark gates

Later themes may modulate palette and emphasis. They do not get to silently
replace the grammar with unrelated modern icon tropes.

### Global Svg Rule

SVGs are not faction-local one-offs. They are global ANKHological artifacts.
The chromatic layer may vary by theme. The grammar layer stays stable unless a
new canon document explicitly replaces it.

### Substance Over Performance

Coverage is not success. Fast expansion that breaks lineage, legibility, or
motif provenance is a regression, even if more folders are technically mapped.

---

## Shape Families

### File Icons = Stele

Files inherit the stele grammar:

- individual record
- inscribed tablet
- contained artifact
- rounded-top memorial silhouette

Canonical exemplar: `file-default.svg`

The file lane succeeds when the file reads first as a distinct object, then as
its domain motif.

### Folder Icons = Pylon

Folders inherit the pylon grammar:

- gateway
- enclosure threshold
- domain chamber
- temple precinct entry

Canonical exemplar: `folder-temple.svg`

The folder lane succeeds when the folder reads first as a sacred container and
then as the domain-specific chamber within that gateway.

### Product Icons = Distilled Glyph

Product icons are not file icons and not folder icons. They are distilled,
single-channel glyphs for VS Code chrome.

They must:

- derive from the same ANKH motif bank
- survive monochrome font conversion
- remain legible at codicon scale

They are the narrowest lane and must be the most reduced.

---

## Inheritance Rules

### Rule 1 - Silhouette Before Detail

The silhouette family is the first identity signal. Motif detail is secondary.
If the icon only works when the interior detail is read, it is too weak for the
lane.

### Rule 2 - Palette Is Structural, Not Decorative

The SFS 12-color palette is the baseline token system. New icons must use those
tokens or documented derivations of those tokens.

Uniform recoloring across unrelated domain folders is forbidden when it erases
the semantic color lineage already established by the motif bank.

### Rule 3 - Motifs Must Come From The ANKH Bank

Folder and file interiors must derive from the Egyptological / Andean motif
vocabulary already present in the corpus.

Generic modern glyphs such as abstract bar charts, compass marks, or office-app
icons fail unless they can be explicitly traced to an ANKH motif mapping.

### Rule 4 - Descendant Themes Recolor, They Do Not Re-grammar

For later MILF/Sub-MILF themes:

- keep the silhouette family
- keep the motif provenance
- keep the domain mapping unless canon changes
- modulate palette and chromatic expression per theme

Any proposal to redraw the grammar itself requires a new bridge-level decision,
not an untracked SVG batch.

---

## Canonical Palette

The icon lane inherits the SFS baseline:

| Token | Hex | Role |
|-------|-----|------|
| `bg` | `#050505` | Void substrate |
| `stele` | `#0A0A0A` | Workbench panel background (reference only — not used in SVGs) |
| `stele-body` | `#2A2724` | SVG icon body fill (stele tablets, pylon walls). Lifted from `stele` for contrast. |
| `fg` | `#E8E2D2` | Primary text / aged papyrus |
| `gold` | `#F4C430` | Egyptian primary |
| `copper` | `#D4714E` | Andean earth |
| `amber` | `#D7B562` | Warm neutral |
| `rose-clay` | `#D4907A` | Organic warmth |
| `patina` | `#7AAAB2` | Cool contrast |
| `sandstone` | `#B9A37A` | Desert neutral |
| `weathered` | `#908672` | Subdued secondary |
| `kiln` | `#E05545` | Alert / conflict |
| `verdigris` | `#8CB87A` | Growth / truth / validation |

### Chamber Transparency Rule

Closed folder pylon chambers use `fill-opacity="0.55"` on the inner `<rect x="5" y="5" width="6" height="8">` element. This allows theme background color to bleed through the portal, creating per-theme chromatic tinting from one global SVG set. Outer pylon walls and file stele bodies remain fully opaque. Open folder variants already use accent-color opacity fills.

---

## Domain Folder Canon

The 10 domain folders below are the benchmark set for the current lane. Their
assignments preserve a 5 Egyptian / 5 Andean balance across the family.

| Folder | Palette Token | Hex | Motif | Axis | Meaning |
|--------|---------------|-----|-------|------|---------|
| `session-archives` | `copper` | `#D4714E` | Pachakuti | Andean | world-turning cycle / archive epochs |
| `checkpoints` | `amber` | `#D7B562` | Wedjat | Egyptian | verification / watchfulness |
| `reports` | `sandstone` | `#B9A37A` | Thoth tablet | Egyptian | inscribed record / account |
| `prompts` | `gold` | `#F4C430` | Hu | Egyptian | utterance / authoritative speech |
| `protocols` | `verdigris` | `#8CB87A` | Ma'at feather | Egyptian | order / truth / validation |
| `skills` | `rose-clay` | `#D4907A` | Tocapu | Andean | craft / encoded textile knowledge |
| `governance` | `weathered` | `#908672` | Shen ring | Egyptian | enclosure / continuity / authority |
| `architecture` | `patina` | `#7AAAB2` | Chakana | Andean | structure / cross-world framework |
| `methodology` | `copper` | `#D4714E` | Quipu | Andean | structured process / tied knowledge |
| `handoffs` | `amber` | `#D7B562` | Ayni arrows | Andean | reciprocity / exchange / transfer |

This table is now the benchmark for those folder families. If a redesign uses a
different motif or palette, it must justify the change against this table and
the SFA corpus rather than improvising a new mapping.

---

## 16px Execution Budget

Explorer icons live at a punishing scale. The lane only survives if the design
accepts that constraint instead of drawing desktop-logo detail into a stamp.

### Required Constraints

- One primary motif per icon.
- One supporting motif group at most.
- Inner chamber detail should read in 4-6 visible strokes or shapes, not a
  miniature illustration.
- Minimum visible stroke target: `0.4` for interior detail.
- Interior opacity may support depth, but not carry the only semantic signal.
- Filled shapes that merge into a blob at 16px fail.

### What This Means In Practice

- `folder-protocols` should read as feather/order first, not as a tiny policy UI.
- `folder-governance` should read as ring/enclosure first, not scales plus
  micro-detail.
- `folder-reports` should read as tablet/record first, not as office-document
  iconography.

---

## State Grammar For Folders

### Closed State

Closed folders are sealed pylons.

Required signals:

- stable gateway silhouette
- closed inner chamber
- domain motif visible inside the chamber

### Open State

Open folders must be structurally opened pylons, not the same icon with a mild
opacity bump.

At least one of the following structural deltas must occur:

- aperture clearly widens or reveals more chamber depth
- lintel or chamber geometry changes to read as opened access
- side pylons or chamber plane shift to imply entry

The domain motif stays the same. The state changes; the identity does not.

### Explicit Failure Case

The following is not sufficient as an open state:

- same closed silhouette
- same motif
- slightly brighter chamber fill
- a bottom underline

That is cosmetic variation, not state grammar.

---

## Anti-Regression Rules

The lane fails if any of the following happen:

- all new folder families collapse to one accent color without domain rationale
- ANKH motifs are replaced by generic modern symbols without source lineage
- open/closed variants differ only by opacity tweaks
- interior detail exceeds 16px legibility budget
- new work is justified by coverage alone instead of lineage plus readability

This rule exists because the real regression is not disagreement over taste. It
is drift away from the already-built epoch standard.

---

## Benchmark Gate

Any icon batch proposed for this lane must pass all of the following:

1. Research citation: name the source doc or motif-bank lineage it comes from.
2. Silhouette fit: identify whether it belongs to stele, pylon, or product-glyph
   grammar.
3. Palette fit: use SFS tokens or documented derivations only.
4. Motif provenance: map the domain to a named Egyptological or Andean motif.
5. State fit: open variants must have structural delta.
6. 16px fit: no micro-detail that only reads in an SVG viewer.
7. SFA fit: the set maintains overall balance rather than clustering one axis.

If a proposal cannot explain itself through those seven gates, it is not ready.

---

## Working Exemplars

Use these as the lineage baseline before inventing new folder families:

- `extensions/chthonic-archive/themes/icons/file-default.svg`
- `extensions/chthonic-archive/themes/icons/folder-temple.svg`
- `extensions/chthonic-archive/themes/icons/folder-src.svg`
- `extensions/chthonic-archive/themes/icons/folder-github.svg`
- `extensions/chthonic-archive/themes/icons/folder-scripts.svg`

The correct operation is inheritance and refinement, not replacement by a lower
fidelity batch.

---

## Consequence For Future Themes

For every later MILF/Sub-MILF theme:

- the icon lane starts from SFS, not from zero
- the ANKH glyph corpus remains shared
- the benchmark is quality inheritance, not rapid divergence

If a later theme wants a new icon language, that is a new architecture decision,
not a casual local variation.

---

## Cross-References

### Sibling Design Docs

| File | Relevance |
|------|-----------|
| [ANKH_THEME_REFERENCE.md](ANKH_THEME_REFERENCE.md) | Global SVG policy, SFS palette baseline, theme creation checklist |
| [SFS_WPTG_ITERATION_PLAN.md](SFS_WPTG_ITERATION_PLAN.md) | WPTG stage gates, icon-pipeline stages (0.0→3.0), KCP metadata |
| [SFS_SLABSTONE_BASELINE.md](SFS_SLABSTONE_BASELINE.md) | Generated reproducibility anchor linking canon prose to live SFS theme/icon assets |
| [ANKH_README.md (ankh)](../frameworks/ankh/ANKH_README.md) | 50/50 Egyptological × Andean abstraction, top-level ANKH bridge |
| [SFA_CROSS_REFERENCE_SCAN.md](../../claude/mailbox/SFA_CROSS_REFERENCE_SCAN.md) | Motif balance audit, motif-to-palette lineage |

### Methodology

| File | Relevance |
|------|-----------|
| [WET_PAPER_TO_GOLD_METHODOLOGY.md (repo-root)](../../WET_PAPER_TO_GOLD_METHODOLOGY.md) | Governs preservation-first icon/script refinement and the dry-lane contract for static script/skill audits |

### Canon Exemplars

| File | Lane | Role |
|------|------|------|
| [file-default.svg](../../extensions/chthonic-archive/themes/icons/file-default.svg) | Stele | Canon file silhouette |
| [folder-temple.svg](../../extensions/chthonic-archive/themes/icons/folder-temple.svg) | Pylon | Canon folder silhouette (gold/Ankh) |
| [folder-temple-open.svg](../../extensions/chthonic-archive/themes/icons/folder-temple-open.svg) | Pylon | Canon open-state exemplar |
| [folder-src.svg](../../extensions/chthonic-archive/themes/icons/folder-src.svg) | Pylon | Early domain exemplar (patina/scribal) |
| [folder-github.svg](../../extensions/chthonic-archive/themes/icons/folder-github.svg) | Pylon | Early domain exemplar |
| [folder-scripts.svg](../../extensions/chthonic-archive/themes/icons/folder-scripts.svg) | Pylon | Early domain exemplar |

### Domain Folder Canon SVGs (10 Families × 2 States)

| Closed | Open |
|--------|------|
| [folder-session-archives.svg](../../extensions/chthonic-archive/themes/icons/folder-session-archives.svg) | [folder-session-archives-open.svg](../../extensions/chthonic-archive/themes/icons/folder-session-archives-open.svg) |
| [folder-checkpoints.svg](../../extensions/chthonic-archive/themes/icons/folder-checkpoints.svg) | [folder-checkpoints-open.svg](../../extensions/chthonic-archive/themes/icons/folder-checkpoints-open.svg) |
| [folder-reports.svg](../../extensions/chthonic-archive/themes/icons/folder-reports.svg) | [folder-reports-open.svg](../../extensions/chthonic-archive/themes/icons/folder-reports-open.svg) |
| [folder-prompts.svg](../../extensions/chthonic-archive/themes/icons/folder-prompts.svg) | [folder-prompts-open.svg](../../extensions/chthonic-archive/themes/icons/folder-prompts-open.svg) |
| [folder-protocols.svg](../../extensions/chthonic-archive/themes/icons/folder-protocols.svg) | [folder-protocols-open.svg](../../extensions/chthonic-archive/themes/icons/folder-protocols-open.svg) |
| [folder-skills.svg](../../extensions/chthonic-archive/themes/icons/folder-skills.svg) | [folder-skills-open.svg](../../extensions/chthonic-archive/themes/icons/folder-skills-open.svg) |
| [folder-governance.svg](../../extensions/chthonic-archive/themes/icons/folder-governance.svg) | [folder-governance-open.svg](../../extensions/chthonic-archive/themes/icons/folder-governance-open.svg) |
| [folder-architecture.svg](../../extensions/chthonic-archive/themes/icons/folder-architecture.svg) | [folder-architecture-open.svg](../../extensions/chthonic-archive/themes/icons/folder-architecture-open.svg) |
| [folder-methodology.svg](../../extensions/chthonic-archive/themes/icons/folder-methodology.svg) | [folder-methodology-open.svg](../../extensions/chthonic-archive/themes/icons/folder-methodology-open.svg) |
| [folder-handoffs.svg](../../extensions/chthonic-archive/themes/icons/folder-handoffs.svg) | [folder-handoffs-open.svg](../../extensions/chthonic-archive/themes/icons/folder-handoffs-open.svg) |

### Theme / Icon JSON (Wiring Layer)

| File | Purpose |
|------|--------|
| [chthonic-file-icon-theme.json](../../extensions/chthonic-archive/themes/chthonic-file-icon-theme.json) | Maps SVG icon defs → file extensions, filenames, folder names |
| [chthonic-product-icon-theme.json](../../extensions/chthonic-archive/themes/chthonic-product-icon-theme.json) | Product icon font definitions |
| [chthonic-geology-color-theme.json](../../extensions/chthonic-archive/themes/chthonic-geology-color-theme.json) | SFS color theme (669 workbench / 83 token / 57 semantic) |
| [package.json (chthonic-archive)](../../extensions/chthonic-archive/package.json) | Extension manifest — theme, icon, language, command contributions |

### Pipeline Scripts (Icon Pillar)

| Script | WPTG Stage | Purpose |
|--------|------------|--------|
| [icon_filetype_census.py](../../scripts/icon_filetype_census.py) | 0.0–0.1 | Workspace filetype census + coverage gap mapping |
| [icon_svg_audit.py](../../scripts/icon_svg_audit.py) | 1.0–1.2 | Structural, WCAG, palette validation |
| [icon_svg_optimizer.py](../../scripts/icon_svg_optimizer.py) | 2.0 | SVG path optimization |
| [icon_distinctiveness_audit.py](../../scripts/icon_distinctiveness_audit.py) | 2.1 | Motif similarity / collision detection |
| [icon_surface_map.py](../../scripts/icon_surface_map.py) | (cross-cutting) | Deterministic surface mapping — where each icon renders |
| [sfa_cross_reference.py](../../scripts/sfa_cross_reference.py) | (cross-cutting) | 50/50 balance engine, motif assignment |
| [sfs_slabstone_baseline.py](../../scripts/sfs_slabstone_baseline.py) | (cross-cutting) | Generated anchor report tying icon canon prose to live SFS/theme asset state |
| [vscode_settings_live_audit.py](../../scripts/vscode_settings_live_audit.py) | (validation) | Settings/language drift detection |
