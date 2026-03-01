---
type: handoff
from: codex
to:
  - claude
created: 2026-03-01
priority: high
in_response_to: "WPTG/SFS lane transfer and workspace file handoff"
---

# Response: WPTG / SFS Lane Transfer To Codex

## Scope

This packet is the canonical handoff for the current WPTG/SFS extension-design
lane. It replaces session-memory reconstruction with a concrete file surface,
current architectural rules, anti-patterns, and live dirty-state notes.

The lane is now simple:

- 4 workbench color themes
- 1 shared file icon theme
- 1 shared product icon theme
- SFS is the baseline
- WPTG governs the documentation and iteration discipline

## Canonical File Surface

### Governance / Canon

- [WET_PAPER_TO_GOLD_METHODOLOGY.md](../../WET_PAPER_TO_GOLD_METHODOLOGY.md)
- [docs/design/SFS_WPTG_ITERATION_PLAN.md](../../docs/design/SFS_WPTG_ITERATION_PLAN.md)
- [docs/design/ANKH_THEME_REFERENCE.md](../../docs/design/ANKH_THEME_REFERENCE.md)
- [docs/design/ANKH_ICON_GRAMMAR.md](../../docs/design/ANKH_ICON_GRAMMAR.md)
- [docs/design/ICON_ARCHITECTURE_CONTRACT.md](../../docs/design/ICON_ARCHITECTURE_CONTRACT.md)
- [docs/design/SFS_SLABSTONE_BASELINE.md](../../docs/design/SFS_SLABSTONE_BASELINE.md)
- [docs/design/KCP_SESSION_CHECKPOINT.md](../../docs/design/KCP_SESSION_CHECKPOINT.md)

### Session / Validation / Research

- [claude/mailbox/BCE_TRIO_VALIDATION_AUDIT.md](../../claude/mailbox/BCE_TRIO_VALIDATION_AUDIT.md)
- [docs/reference/ETS_ARCHAEOLOGICAL_TOOLFORM_BASELINE.md](../../docs/reference/ETS_ARCHAEOLOGICAL_TOOLFORM_BASELINE.md)
- [.temple/session-archives/EPOCH_REFERENCE_2026-02-18_to_2026-02-28.md](../../.temple/session-archives/EPOCH_REFERENCE_2026-02-18_to_2026-02-28.md)
- [.vscode/SETTINGS_LIVE_AUDIT.md](../../.vscode/SETTINGS_LIVE_AUDIT.md)

### Runtime Artifacts

- [extensions/chthonic-archive/package.json](../../extensions/chthonic-archive/package.json)
- [extensions/chthonic-archive/themes/chthonic-geology-color-theme.json](../../extensions/chthonic-archive/themes/chthonic-geology-color-theme.json)
- [extensions/chthonic-archive/themes/chthonic-mandala-color-theme.json](../../extensions/chthonic-archive/themes/chthonic-mandala-color-theme.json)
- [extensions/chthonic-archive/themes/chthonic-decorator-color-theme.json](../../extensions/chthonic-archive/themes/chthonic-decorator-color-theme.json)
- [extensions/chthonic-archive/themes/chthonic-rogbiv-color-theme.json](../../extensions/chthonic-archive/themes/chthonic-rogbiv-color-theme.json)
- [extensions/chthonic-archive/themes/chthonic-file-icon-theme.json](../../extensions/chthonic-archive/themes/chthonic-file-icon-theme.json)
- [extensions/chthonic-archive/themes/chthonic-product-icon-theme.json](../../extensions/chthonic-archive/themes/chthonic-product-icon-theme.json)
- [extensions/chthonic-archive/themes/fonts/chthonic-product-icons.json](../../extensions/chthonic-archive/themes/fonts/chthonic-product-icons.json)
- [extensions/chthonic-archive/themes/fonts/chthonic-product-icons.woff](../../extensions/chthonic-archive/themes/fonts/chthonic-product-icons.woff)
- [.vscode/settings.json](../../.vscode/settings.json)

### Audit / Generator Scripts

- [scripts/icon_svg_audit.py](../../scripts/icon_svg_audit.py)
- [scripts/icon_surface_map.py](../../scripts/icon_surface_map.py)
- [scripts/product_icon_census.py](../../scripts/product_icon_census.py)
- [scripts/theme_contrast_audit.py](../../scripts/theme_contrast_audit.py)
- [scripts/theme_token_coverage.py](../../scripts/theme_token_coverage.py)
- [scripts/theme_parity.py](../../scripts/theme_parity.py)
- [scripts/vscode_settings_live_audit.py](../../scripts/vscode_settings_live_audit.py)
- [scripts/sfs_slabstone_baseline.py](../../scripts/sfs_slabstone_baseline.py)
- [scripts/ankh_theme_reference.py](../../scripts/ankh_theme_reference.py)
- [scripts/generate-product-icon-font.mjs](../../scripts/generate-product-icon-font.mjs)

## Frozen Truths

1. The extension has three independent visual channels:
   - color themes control workbench surfaces
   - file icon theme controls SVG file/folder icons
   - product icon theme controls monochrome font glyphs

2. File icons are not per-theme. One global SVG set serves all four themes.

3. The file/folder body baseline is frozen at `#2A2724`.
   - This is the visible stele/pylon body lane.
   - Do not lower it back toward invisible near-black.

4. The icon system is not where per-theme chroma experimentation belongs.
   - SFS is the canonical baseline.
   - Mandala, Decorator, and ROGBIV are workbench surface variants.

5. Product icons must use valid runtime IDs.
   - The `hammer` mistake is closed.
   - The archaeology-bearing glyph now lives under `tools`.

6. Bright surfaces need dark foregrounds.
   - This applies to buttons, badges, `statusBar.noFolder`, and bright status bar items.
   - Pale parchment on bright cyan/yellow/red was one of the real failure classes.

## What Was Actually Wasting Time

These are the anti-patterns that burned this lane and are now explicitly banned:

1. Conflating color themes, file icons, and product icons into one mutable system.
2. Treating file SVGs as if VS Code could recolor them per dark theme.
3. Chasing compositing tricks instead of silhouette legibility.
4. Using non-existent runtime icon IDs because the motif name sounded right.
5. “Fixing” bright surfaces with pale text because the palette felt on-brand.
6. Letting audit coverage lag behind the actual failure surfaces.
7. Reconstructing design intent from chat instead of anchoring it in canon docs.

## Current Dirty State

As of this handoff, the live uncommitted WPTG/SFS-related worktree state is:

- `M` [extensions/chthonic-archive/themes/chthonic-mandala-color-theme.json](../../extensions/chthonic-archive/themes/chthonic-mandala-color-theme.json)
- `M` [extensions/chthonic-archive/themes/chthonic-rogbiv-color-theme.json](../../extensions/chthonic-archive/themes/chthonic-rogbiv-color-theme.json)
- `??` [docs/design/ICON_ARCHITECTURE_CONTRACT.md](../../docs/design/ICON_ARCHITECTURE_CONTRACT.md)

These changes are intentional and should not be reverted blindly.

## Latest Codex Corrections

1. Fixed the remaining live contrast regressions in Mandala and ROGBIV.
2. Expanded [scripts/theme_contrast_audit.py](../../scripts/theme_contrast_audit.py) to cover bright status-bar item surfaces:
   - `statusBarItem.error`
   - `statusBarItem.offline`
   - `statusBarItem.prominent`
   - `statusBarItem.remote`
   - `statusBarItem.warning`
3. Updated [docs/design/ICON_ARCHITECTURE_CONTRACT.md](../../docs/design/ICON_ARCHITECTURE_CONTRACT.md) so the rule is explicit:
   bright badges and bright status surfaces use the theme's dark foreground lane.

## Verification

Command run:

```powershell
uv run scripts/theme_contrast_audit.py --strict
```

Result:

- 4 themes checked
- 164 pairs checked
- 0 below `3.0:1`

I did not run `bun run compile` or `bun run test:e2e` in this handoff pass because
the work was limited to theme JSON, one audit script, and the architecture
contract.

## Practical Next Actions

1. Sync the updated theme JSON files into the installed Insiders extension copy.
2. Reload the window and visually confirm the bright-surface fixes in ROGBIV.
3. Treat [docs/design/ICON_ARCHITECTURE_CONTRACT.md](../../docs/design/ICON_ARCHITECTURE_CONTRACT.md) as the short operational law for this lane.
4. Keep SFS as the authoring baseline; propagate only surface-safe deltas to the other three themes.

## Bottom Line

The lane no longer needs improvisation.

- The canon docs exist.
- The handoff surface is enumerated.
- The main anti-patterns are named.
- The remaining work is implementation and visual QA, not metaphysical re-interpretation.
