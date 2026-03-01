# Icon Architecture Contract

**Status**: FROZEN  
**Scope**: `extensions/chthonic-archive/themes/`  
**Rule**: One stable file icon system. One stable product icon system. Four workbench skins. Nothing else.

---

## Three Channels, Three Lanes

| Channel | Controls | Does NOT Control |
|---|---|---|
| **Color Theme** (×4) | Workbench surfaces: editor bg, activity bar, sidebar, status bar, token colors | File icon appearance, product icon appearance |
| **File Icon Theme** (×1) | SVG file/folder icons: mapping, silhouette, fill | Per-theme recoloring (VS Code does not support this) |
| **Product Icon Theme** (×1) | Monochrome font glyphs via codicon/runtime IDs | Arbitrary icon slots, color, multi-tone rendering |

These three channels are **independent**. A change to a color theme never requires a change to either icon theme. A change to an icon SVG never requires a change to a color theme.

---

## File Icon Rules

1. **One global set.** All four color themes share the same `chthonic-file-icon-theme.json` and the same SVG files.
2. **Stele body fill: `#2A2724`.** This is the frozen baseline. It is visible on all four dark theme backgrounds. Do not lower it. Raise it only if visual review on the darkest background (`#09080E` ROGBIV activity bar) proves it insufficient.
3. **Chamber opacity: `fill-opacity="0.55"` on closed folder rects.** Frozen.
4. **No per-theme SVG variants.** VS Code provides no mechanism for a file icon theme to swap SVGs per color theme. Stop designing for this.
5. **Optimize for legibility and silhouette**, not compositing tricks. A file icon must be recognizable at 16×16 on any of the four backgrounds.
6. **50/50 Egyptological/Andean** lives in motif vocabulary (ankh, stele, textile weave, stepped fret) and silhouette grammar. It does not live in runtime color switching.

## Product Icon Rules

1. **One global font.** `chthonic-product-icons.woff` + `chthonic-product-icons.json`.
2. **Monochrome only.** Product icons inherit `currentColor` from the color theme. The font contains no color information.
3. **Valid IDs only.** Every glyph must map to a VS Code runtime icon ID (`codicon-*` namespace or extension-contributed ID). If the runtime doesn't know the ID, the glyph is dead weight.
4. **No overreach.** Don't create product icon glyphs for slots VS Code doesn't expose. Check the [product icon reference](https://code.visualstudio.com/api/references/icons-in-labels) before adding.

## Color Theme Rules

1. **SFS (Geological Core) is the canonical baseline.** New workbench keys are authored in SFS first, then propagated to the other three.
2. **Decorator, Mandala, ROGBIV are surface variants.** They change palette and workbench colors. They do not change icon systems.
3. **No foreground below 3:1 contrast on its background.** Catch this before packaging, not after.
4. **Dark-text-on-bright-button is correct** (e.g., `button.foreground` on `button.background`). Don't "fix" these.
5. **`#000000` as a background or border on a dark theme is fine.** `#000000` as a foreground on a dark background is not.

## What This Stops

- Regenerating SVGs when a color theme changes.
- Adding "theme-aware" logic to file icon definitions.
- Treating product icon slots as decorative art surfaces.
- Conflating workbench color work with icon work.
- Multi-day debugging loops caused by not setting `workbench.colorTheme` in settings.

---

## Research Anchor Chain

These files are the authoritative source pool for any future icon repair or
extension-visual refinement in this lane:

- `.github/copilot-instructions.archive.md`
  - ANKH middle-ground bridge protocol, heritage SSOT, lineage framing
- `docs/frameworks/ankh/ANKH_README.md`
  - 50/50 Egyptological × Andean abstraction, Alpha Directives, topology
- `docs/frameworks/ankh/ANKHOLOGY.md`
  - generative vs selection hygiene; use for phase discipline, not doctrine
- `docs/design/ANKH_ICON_GRAMMAR.md`
  - shape families, motif bank, palette inheritance, folder canon
- `docs/reference/ETS_ARCHAEOLOGICAL_TOOLFORM_BASELINE.md`
  - archaeology-first donor pool for tools, forge/build, strike and craft forms
- `.temple/session-archives/EPOCH_REFERENCE_2026-02-18_to_2026-02-28.md`
  - session lineage for what was built, what failed, and where the lane drifted

If a proposed icon change cannot be explained against this source chain, it is
not ready for direct mutation.

## Surgical Repair Order

When repairing the icon lane, use this order and stop as soon as the visible
problem is solved:

1. **Current Explorer surfaces first**
   - root folders and the domains the user actually stares at daily
   - `.temple`, `session-archives`, `prompts`, `protocols`, `reports`, `skills`, `scripts`, `docs`
2. **Frequent file types second**
   - `md`, `py`, `ts`, `json`, `toml`, `ps1`, `rs`, `yml`, `txt`
3. **Product icons only when a live consumer is wrong**
   - never redesign product glyphs in a vacuum
4. **Dormant mappings last**
   - only touch them if they become visible in the workspace

This lane is now fix-only:

- identify the visible defect
- patch the exact SVG or theme key
- verify the rendered result
- stop

No new theory loop, no global reinvention, no speculative recolor pass.

---

## Installed Extension Checklist

The installed extension at `~/.vscode-insiders/extensions/chthonic-archive.chthonic-archive-0.2.1/` must have:

```
settings.json (user):
  workbench.colorTheme    = one of the four theme labels
  workbench.iconTheme     = chthonic-file-icons
  workbench.productIconTheme = chthonic-product-icons

package.json contributes:
  themes[]           → 4 color themes (Geology, Mandala, Decorator, ROGBIV)
  iconThemes[]       → 1 file icon theme
  productIconThemes[] → 1 product icon theme
```

All three settings must be explicitly set. If `workbench.colorTheme` is empty, VS Code uses its built-in default and none of the chthonic workbench colors apply.
