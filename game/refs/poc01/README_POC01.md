---
lifecycle: poc-form-vector
series: poc01
axis: form
source_register: disco-elysium-class
landed_at: 2026-05-26
cross_ref_ssot: .github/copilot-instructions.archive.md
cross_ref_content_vector: game/lore/characters/_deferred_organ/T1.5/the_sourcer.json
tool: TOOL_POC_COLLAGE_V3
---

<!--
@SID: REF_POC01_FORM_VECTOR_INTAKE_V1
@Type: Reference
@Series: POCNN (pattern-anchor at poc01)
@Axis: Form (cRPG chassis), orthogonal to the SSOT's Content axis
@Context: First art-and-style anchor for game/; landed 2026-05-26 to push past
  meta-documentation stalemate. High-fidelity PNGs preserved in LFS so the
  collage derivative can be regenerated at different parameters later.
-->

# (`POC01-Form-Vector`/`FORM-VEC-POC01`): → cRPG Chassis Reference

This directory is the first **form-vector anchor** for the [game/](../../) workspace — twenty *Disco Elysium*-class screenshots that name the genre/aesthetic skeleton the chthonic-archive's cRPG content is gesturing toward.

It is **not** content-vector canon. The Andean|Egyptologic Milfological / Ankhological skin declared in [the SSOT canonical register](../../../.github/copilot-instructions.archive.md) is applied **OVER** this chassis, not derived **FROM** it.

## (`Axis-Declaration`): → (`FORM-VS-CONTENT`)

| Axis | What it carries | Where it lives |
|---|---|---|
| **Form** *(here)* | painterly-isometric cRPG chassis, faculty-driven internal mechanics, skill-check grammar, dialogue-first encounter design, ornamental HUD chrome | `game/refs/pocNN/` |
| **Content** *(SSOT-side)* | Andean|Egyptologic mythology, Milfological/Ankhological protocol, K-CUP Trinity governance, Triumvirate (Orackla/Umeko/Lysandra), WHR:MAX tri-axis | [`.github/copilot-instructions.archive.md`](../../../.github/copilot-instructions.archive.md), [`game/lore/characters/_deferred_organ/T1.5/the_sourcer.json`](../../lore/characters/hypothalamus/T1.5/the_sourcer.json) |

The two axes are **orthogonal, not contradictory**. The chassis carries the skin; the skin does not specify a chassis.

## (`What-These-POCs-Reference-Well`): → (`FORM-VEC-AFFIRMATIVE`)

- **Painterly density** — `Example_POC00001.png`, `Example_POC00012.png`, `Example_POC00015.png`. Vertical slum/temple verticality, moss-and-lichen substrate aesthetic, layered urban decay. Maps onto chthonic-archive's preservation-of-rot register.
- **Faculty-trinity grammar** — `Example_POC00003.png`. **(`Gift-Surface`/`SSOT-MAPPING`):** FACULTY OF ACTION / RELATION / INTELLECT, each with five skills. This is a near-wrapped UX template for displaying the K-CUP Triumvirate (T1: Orackla / Umeko / Lysandra) as a player-facing faculty system. The mechanical UI from the screenshot becomes the diegetic surface of the Trinity. Content-vector counterpart: [`the_sourcer.json`](../../lore/characters/hypothalamus/T1.5/the_sourcer.json).
- **Internal-state-as-mechanic** — `Example_POC00017.png`. Thought Cabinet equivalent ("REINFORCED THOUGHT: PRIMITIVE ACCUMULATION", with reinforced effects + violations) matches the Lysandra Truth Chain register: thoughts as committed positions with measurable consequence.
- **Skill-check UI grammar** — `Example_POC00018.png`. Dice-card with modifiers (`Cocaine jitters [+1]`, `Ball knower [+1]`) + percentage (`LEANING PASS [58%]`). Composable with any mythological skin.
- **Journal / task cards** — `Example_POC00008.png`. Tarot-card task system. Fits chthonic-archive's archival/dossier register.
- **Hard genre tonality** — `Example_POC00010.png`, `Example_POC00020.png`. Confrontational set pieces, red-coated figure against grey-painted faces. Psycho-noir register territory.

## (`What-These-POCs-Do-NOT-Reference`): → (`ANTI-DRIFT-CONTRACT`)

Explicit anti-drift list. The POCs **do not** authorize any of the following onto the content-vector axis:

- Andean step-pyramid iconography
- Egyptian temple / hieroglyphic / ANKH-MGBP symbology
- Matriarchal-command-structure visual language (K-CUP Supremacy, T-DECOR)
- WHR:MAX tri-axis sonic geometry (Bayonetta / Eva Green / Chun-Li)
- Any character archetypes, factions, or species named in `game/lore/`

These remain SSOT-side. The POCs supply the **shape of the frame**, not the **painting inside it**.

## (`Series-Anchor`): → (`POCNN-PATTERN-CONTRACT`)

This is `poc01/`. Future drops (`poc02/`, `poc03/`, …) inherit this directory shape and this README's section structure. To add a `pocNN/`:

1. Create `game/refs/pocNN/`.
2. Drop source PNGs as `Example_POCnnnnn.png` (or other suitable filename pattern — the collage tool sorts lexically, so any stable name works).
3. Copy this `README_POC01.md` to `README_POCNN.md`, update the frontmatter (`series:`, `landed_at:`, `source_register:` if different), and rewrite the **affirmative** and **anti-drift** sections to match the new POC's actual content. Keep the section headers and the form-vs-content axis declaration verbatim — they're the contract.
4. Run the collage tool: `uv run scripts/build_poc_collage.py game/refs/pocNN/`.
5. Commit. The LFS lane in [`.gitattributes`](../../../.gitattributes) and the allowlist in [`.gitignore`](../../../.gitignore) already cover `game/refs/poc**/`.

## (`Collage-Derivative`): → (`WALLPAPER-GRADE-ARTIFACT`)

High-fidelity originals (~4.5 MB each, 91 MB total for poc01) stay in Git LFS. The collage is the wallpaper-grade derivative — a single 2560×1440 image whose cell topology is a **Centroidal Voronoi Tessellation** (non-rectangular by construction), suitable as a desktop background AND agent-readable in one [`Read`](../../../scripts/build_poc_collage.py) tool call. Emitted in four lossless formats from the same pixel data:

- `POC01_collage.png` — lossless PNG (reference; largest)
- `POC01_collage.webp` — lossless WebP (~80% of PNG size, identical pixels)
- `POC01_collage.qoi` — Quite OK Image format (fast-encode staging buffer; ~115% of PNG size, prioritizes encode/decode speed over ratio)
- `POC01_collage.jxl` — JPEG XL lossless (smallest, ~78% of PNG size; archival)
- `POC01_collage.manifest.json` — auditable cell-by-cell record: seed positions before/after Lloyd's relaxation, cell polygon vertices, source assignments, per-format sha256

Regenerate at will:

```powershell
uv run scripts/build_poc_collage.py game/refs/poc01/
```

### (`Algorithm`): → (`VORONOI-CVT-SALIENCE-AWARE`)

1. **Per-source salience scoring** via global Shannon entropy on grayscale 64×64 thumbnail: `S_i = -Σ p(g) log₂ p(g)`. Higher score = more visual information density.
2. **Source ordering** (default: descending salience). Most-information-dense sources land first, assigned to centroids closer to canvas center after Lloyd's relaxation.
3. **Halton(2,3) seed distribution** — deterministic low-discrepancy quasi-random `n` seeds within the canvas.
4. **Lloyd's relaxation** (40 iterations default) — iteratively moves each seed to the centroid of its Voronoi cell. Boundary cells bounded by mirroring seeds across canvas edges; final cells clipped to canvas via shapely intersection. Result: cells approximate equal-area hyperuniform distribution.
5. **Cell rendering** — each source scaled to fit cell bounding box (fill mode), center-cropped, masked to cell polygon shape.
6. **Adaptive unsharp-mask** post-downscale, strength scaled by downscale ratio.

### (`Defaults`): → (`WALLPAPER-FIRST-CONTRACT`)

| Knob | Default | Notes |
|---|---|---|
| `--canvas` | `2560x1440` | 2K QHD. Cells fill the canvas; no letterboxing. |
| `--lloyd-iters` | `40` | Lloyd's relaxation iterations. 30-50 is the standard range. |
| `--order` | `salience` | Sources sorted by descending Shannon-entropy score. Alternatives: `lex`, `brightness`, `hue`. |
| `--format` | `all` | PNG + WebP + QOI + JXL. Alternatives: any single one. |
| `--bg` | `#000000` | OLED-friendly. Visible only at canvas boundaries where cells curve away. |
| sharpening | adaptive, on | Post-downscale unsharp-mask. Disable with `--no-sharpen`. |
| determinism | always | Halton seeds + Lloyd's iterates + fixed encoder params = byte-identical re-runs across all 4 output formats. |

### (`Tweaking-For-Other-Targets`): → (`CANVAS-NEGOTIATION`)

- **4K wallpaper (3840×2160)**: `--canvas 3840x2160`. Cells scale proportionally; salience-ordering and Lloyd's relaxation unchanged.
- **Ultrawide (3440×1440)**: `--canvas 3440x1440`. Cells auto-adapt to the wider aspect.
- **More sources**: drop more PNGs into `pocNN/` — seed count = source count; Lloyd's relaxation distributes them evenly.
- **Tighter relaxation**: `--lloyd-iters 80` for more uniform cell areas (diminishing returns past ~50).
- **Different ordering aesthetic**: `--order brightness` for dark-anchored dusk-arc; `--order hue` for warm→cool sweep; `--order lex` for filename order (audit baseline).
- **Single archival format**: `--format jxl` for the smallest lossless output (~78% of PNG size).
- **Fast staging buffer**: `--format qoi` when encode speed matters more than file size.

## (`Source-Provenance`): → (`PRE-INTAKE-LOCATION`)

- Originally landed at repo root as `Game_POCS_/` (draft-zone shape), 2026-05-26.
- Moved here under the gitignore-allowlist-discipline + LFS-lane contract in the same change.
- Source register: *Disco Elysium*-class painterly-isometric cRPG. Likely from a ZA/UM successor or genre cohort. Provenance beyond that is unverified and not load-bearing — these are *reference materia*, not authorized canon art.
